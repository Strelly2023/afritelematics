from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, load_source_text, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_mobile, pytest.mark.novapay, pytest.mark.agent]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_agent_cash_in_cash_out_and_reconciliation_are_simulated() -> None:
    client = TestClient(app)
    agent_token = _token(client, "agent")
    operator_token = _token(client, "operator")
    cash_in_key = f"cp-agent-cash-in-{uuid4().hex[:8]}"
    cash_out_key = f"cp-agent-cash-out-{uuid4().hex[:8]}"
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(agent_token), json={"device_id": "device-agent-1"}).status_code == 200

    cash_in = client.post(
        "/v1/payments/charges",
        headers={**auth_header(agent_token), "Idempotency-Key": cash_in_key},
        json={
            "payer_id": "pilot-consumer-1",
            "amount_minor": 10000,
            "currency": "AUD",
            "method": "cash",
            "provider": "cash",
            "ride_id": None,
            "driver_id": None,
        },
    )
    assert cash_in.status_code == 200
    assert cash_in.json().get("data", cash_in.json())["simulated_payment"] is True

    cash_out = client.post(
        "/v1/payments/charges",
        headers={**auth_header(agent_token), "Idempotency-Key": cash_out_key},
        json={
            "payer_id": "pilot-consumer-1",
            "amount_minor": 5000,
            "currency": "AUD",
            "method": "cash",
            "provider": "cash",
            "ride_id": None,
            "driver_id": None,
        },
    )
    assert cash_out.status_code == 200
    assert cash_out.json().get("data", cash_out.json())["simulated_payment"] is True

    wallet = client.get("/v1/payments/wallets/driver/driver-pilot-1/AUD", headers=auth_header(agent_token))
    assert wallet.status_code == 200

    report = client.get("/v1/payments/reporting", headers=auth_header(operator_token))
    assert report.status_code == 200
    assert report.json()["gross_minor"] > 0

    source = load_source_text("novapay_agent")
    assert "Cash In" in source
    assert "Cash Out" in source
    assert "Float" in source
