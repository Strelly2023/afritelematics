from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import auth_header, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.identity]


def test_controlled_pilot_novaid_identity_flows() -> None:
    client = TestClient(app)
    personal_token = client.post("/auth/token", json=token_payload("rider-002", "OBSERVER")).json()["token"]
    business_token = client.post("/auth/token", json=token_payload("business-001", "OBSERVER")).json()["token"]
    employee_token = client.post("/auth/token", json=token_payload("employee-003", "OBSERVER")).json()["token"]
    partner_token = client.post("/auth/token", json=token_payload("merchant-002", "PARTNER")).json()["token"]
    inspector_token = client.post("/auth/token", json=token_payload("employee-002", "VERIFIER")).json()["token"]

    for token, device_id in [
        (personal_token, "device-012"),
        (business_token, "device-036"),
        (employee_token, "device-040"),
        (partner_token, "device-032"),
        (inspector_token, "device-039"),
    ]:
        assert client.post("/v1/pilot/devices/bind", headers=auth_header(token), json={"device_id": device_id}).status_code == 200
        assert client.post("/v1/pilot/access/check", headers=auth_header(token), json={"device_id": device_id, "surface": "identity"}).json()["allowed"] is True

    registry = client.get("/v1/pilot/registry", headers=auth_header(personal_token))
    assert registry.status_code == 200
    assert registry.json()["config"]["environment"] == "CONTROLLED_PILOT"

