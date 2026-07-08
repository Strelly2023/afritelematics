from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from afriride_system.pilot import public_pilot
from afriride_system.pilot.public_pilot import PublicPilotError, bind_device, mark_public_pilot_payment, public_pilot_payment_guard, reconciliation_report
from tests.public_pilot._helpers import PUBLIC_PILOT_ACCOUNTS, auth_header, load_source_text, public_pilot_approval_payload, token_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.novapay, pytest.mark.consumer, pytest.mark.agent, pytest.mark.merchant, pytest.mark.business]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _, _ = PUBLIC_PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def _install_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    path.write_text(json.dumps(public_pilot_approval_payload(), indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_novapay_consumer_agent_merchant_business_flow(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    client = TestClient(app)
    consumer_token = _token(client, "consumer")
    agent_token = _token(client, "agent")
    merchant_token = _token(client, "merchant")
    business_token = _token(client, "business")
    operator_token = _token(client, "operator")

    assert bind_device("public-consumer-1", "public-device-consumer-1")["status"] == "bound"
    assert bind_device("public-agent-1", "public-device-agent-1")["status"] == "bound"
    assert bind_device("public-merchant-1", "public-device-merchant-1")["status"] == "bound"
    assert bind_device("public-business-1", "public-device-business-1")["status"] == "bound"

    consumer_access = client.post(
        "/v1/public-pilot/access/check",
        headers=auth_header(consumer_token),
        json={"device_id": "public-device-consumer-1", "region": "Melbourne", "surface": "consumer"},
    )
    assert consumer_access.status_code == 200
    assert consumer_access.json()["allowed"] is True

    public_pilot_payment_guard(provider="wallet", method="wallet", amount_aud=25, region="Melbourne")
    with pytest.raises(PublicPilotError):
        public_pilot_payment_guard(provider="wallet", method="wallet", amount_aud=51, region="Melbourne")
    simulated = mark_public_pilot_payment({"transaction_id": "pp-pay-001", "status": "captured"})
    assert simulated["public_pilot"] is True

    limits = client.post(
        "/v1/public-pilot/limits/check",
        headers=auth_header(operator_token),
        json={"provider": "wallet", "method": "wallet", "amount_aud": 50, "region": "Melbourne"},
    )
    assert limits.status_code == 200
    assert limits.json()["allowed"] is True

    reconciliation = reconciliation_report(recorded_aud=100, ledger_aud=100, transactions=2)
    assert reconciliation["balanced"] is True

    for key, expected in {
        "novapay_consumer": "Profile",
        "novapay_agent": "Profile",
        "novapay_merchant": "Profile",
        "novapay_business": "Settings",
    }.items():
        source = load_source_text(key)
        assert expected in source

    assert client.get("/v1/payments/health", headers=auth_header(operator_token)).status_code == 200
