from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, load_source_text, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_mobile, pytest.mark.novaid, pytest.mark.identity]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_novaid_pilot_identity_flows_are_visible_in_app_surfaces() -> None:
    client = TestClient(app)
    personal_token = client.post("/auth/token", json=token_payload("pilot-consumer-1", "OBSERVER")).json()["token"]
    business_token = client.post("/auth/token", json=token_payload("pilot-business-1", "OBSERVER")).json()["token"]
    employee_token = client.post("/auth/token", json=token_payload("pilot-business-1", "OBSERVER")).json()["token"]
    partner_token = client.post("/auth/token", json=token_payload("pilot-agent-1", "PARTNER")).json()["token"]
    inspector_token = client.post("/auth/token", json=token_payload("pilot-business-1", "VERIFIER")).json()["token"]

    for token, device in [
        (personal_token, "device-consumer-1"),
        (business_token, "device-business-1"),
        (employee_token, "device-business-1"),
            (partner_token, "device-agent-1"),
        (inspector_token, "device-business-1"),
    ]:
        assert client.post("/v1/pilot/devices/bind", headers=auth_header(token), json={"device_id": device}).status_code == 200

    registry = client.get("/v1/pilot/registry", headers=auth_header(personal_token))
    assert registry.status_code == 200
    assert registry.json()["config"]["environment"] == "CONTROLLED_PILOT"

    assert client.post("/v1/pilot/access/check", headers=auth_header(personal_token), json={"device_id": "device-consumer-1", "surface": "identity"}).json()["allowed"] is True
    assert client.post("/v1/pilot/access/check", headers=auth_header(business_token), json={"device_id": "device-business-1", "surface": "identity"}).json()["allowed"] is True
    assert client.post("/v1/pilot/access/check", headers=auth_header(inspector_token), json={"device_id": "device-business-1", "surface": "identity"}).json()["allowed"] is True

    personal_source = load_source_text("novaid_personal")
    business_source = load_source_text("novaid_business")
    employee_source = load_source_text("novaid_employee")
    partner_source = load_source_text("novaid_partner")
    inspector_source = load_source_text("novaid_inspector")

    assert "Verify phone number" in personal_source
    assert "Business Verify" in business_source
    assert "Employment" in employee_source
    assert "Integrations" in partner_source
    assert "Inspections" in inspector_source
