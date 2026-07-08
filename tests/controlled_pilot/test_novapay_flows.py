from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.novapay]


def test_controlled_pilot_novapay_core_flows() -> None:
    client = TestClient(app)
    consumer_token = client.post("/auth/token", json=token_payload(*PILOT_ACCOUNTS["consumer"][:2])).json()["token"]
    agent_token = client.post("/auth/token", json=token_payload(*PILOT_ACCOUNTS["agent"][:2])).json()["token"]
    merchant_token = client.post("/auth/token", json=token_payload(*PILOT_ACCOUNTS["merchant"][:2])).json()["token"]
    business_token = client.post("/auth/token", json=token_payload(*PILOT_ACCOUNTS["business"][:2])).json()["token"]
    operator_token = client.post("/auth/token", json=token_payload(*PILOT_ACCOUNTS["operator"][:2])).json()["token"]
    key = f"cp-pay-{uuid4().hex[:8]}"

    assert client.post("/v1/pilot/devices/bind", headers=auth_header(consumer_token), json={"device_id": "device-012"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(agent_token), json={"device_id": "device-033"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(merchant_token), json={"device_id": "device-031"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(business_token), json={"device_id": "device-036"}).status_code == 200

    charge = client.post(
        "/v1/payments/charges",
        headers={**auth_header(consumer_token), "Idempotency-Key": key},
        json={"payer_id": "rider-002", "amount_minor": 2500, "currency": "AUD", "method": "wallet", "provider": "wallet", "ride_id": None, "driver_id": None},
    )
    assert charge.status_code == 200
    assert charge.json().get("data", charge.json())["simulated_payment"] is True

    cash = client.post(
        "/v1/payments/charges",
        headers={**auth_header(agent_token), "Idempotency-Key": f"{key}-cash"},
        json={"payer_id": "rider-002", "amount_minor": 1000, "currency": "AUD", "method": "cash", "provider": "cash", "ride_id": None, "driver_id": None},
    )
    assert cash.status_code == 200

    assert client.get("/v1/payments/reporting", headers=auth_header(operator_token)).status_code == 200
    assert client.post(f"/v1/payments/transactions/{charge.json()['transaction_id']}/refunds", headers=auth_header(operator_token), json={"amount_minor": 500}).status_code == 200
