from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, load_source_text, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_mobile, pytest.mark.novapay, pytest.mark.business]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_business_approval_payroll_and_reports_are_simulated() -> None:
    client = TestClient(app)
    business_token = _token(client, "business")
    operator_token = _token(client, "operator")
    charge_key = f"cp-business-{uuid4().hex[:8]}"
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(business_token), json={"device_id": "device-036"}).status_code == 200

    charge = client.post(
        "/v1/payments/charges",
        headers={**auth_header(operator_token), "Idempotency-Key": charge_key},
        json={
            "payer_id": "business-001",
            "amount_minor": 100000,
            "currency": "AUD",
            "method": "split",
            "provider": "wallet",
            "ride_id": None,
            "driver_id": None,
        },
    )
    assert charge.status_code == 200
    assert charge.json().get("data", charge.json())["simulated_payment"] is True

    report = client.get("/v1/payments/reporting", headers=auth_header(operator_token))
    assert report.status_code == 200
    assert report.json()["gross_minor"] > 0

    source = load_source_text("novapay_business")
    assert "Approvals" in source
    assert "Payroll" in source
    assert "Reports" in source
