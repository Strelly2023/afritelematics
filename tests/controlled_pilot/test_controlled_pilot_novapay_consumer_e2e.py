from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, load_source_text, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_mobile, pytest.mark.novapay, pytest.mark.consumer]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_consumer_wallet_transfer_and_receipt_are_simulated() -> None:
    client = TestClient(app)
    consumer_token = _token(client, "consumer")
    operator_token = _token(client, "operator")
    idempotency_key = f"cp-consumer-{uuid4().hex[:8]}"
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(consumer_token), json={"device_id": "device-consumer-1"}).status_code == 200

    wallet = client.get("/v1/payments/wallets/rider/pilot-consumer-1/AUD", headers=auth_header(consumer_token))
    assert wallet.status_code == 200

    charge = client.post(
        "/v1/payments/charges",
        headers={**auth_header(consumer_token), "Idempotency-Key": idempotency_key},
        json={
            "payer_id": "pilot-consumer-1",
            "amount_minor": 5000,
            "currency": "AUD",
            "method": "wallet",
            "provider": "wallet",
            "ride_id": None,
            "driver_id": None,
        },
    )
    assert charge.status_code == 200
    payload = charge.json().get("data", charge.json())
    assert payload["simulated_payment"] is True
    assert payload["status"] == "captured"

    refund = client.post(f"/v1/payments/transactions/{payload['transaction_id']}/refunds", headers=auth_header(consumer_token), json={"amount_minor": 1000})
    assert refund.status_code == 200
    assert refund.json().get("data", refund.json())["simulated_payment"] is True

    dispute = client.post(
        f"/v1/payments/transactions/{payload['transaction_id']}/disputes",
        headers=auth_header(consumer_token),
        json={"opened_by": "pilot-consumer-1", "reason": "pilot dispute"},
    )
    assert dispute.status_code == 200

    history = client.get("/v1/payments/reporting", headers=auth_header(operator_token))
    assert history.status_code == 200
    assert history.json()["gross_minor"] > 0
    assert history.json()["driver_minor"] >= 0

    source = load_source_text("novapay_consumer")
    assert "Send money" in source
    assert "Receive money" in source
    assert "Pay with QR" in source
