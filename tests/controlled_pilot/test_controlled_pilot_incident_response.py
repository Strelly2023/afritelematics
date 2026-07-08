from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, read_text, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_security, pytest.mark.pilot_smoke]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_incident_response_and_support_cases_are_available() -> None:
    client = TestClient(app)
    rider_token = _token(client, "rider")
    operator_token = _token(client, "operator")
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(rider_token), json={"device_id": "device-rider-1"}).status_code == 200
    assert client.post("/v1/pilot/support/tickets", headers=auth_header(operator_token), json={"summary": "broken route"}).status_code == 200
    assert client.post("/v1/pilot/safety/sos", headers=auth_header(rider_token), json={"ride_id": "pilot-ride-incident"}).status_code == 200
    audit = client.get("/v1/pilot/audit", headers=auth_header(operator_token))
    assert audit.status_code == 200
    assert any(item["action"] in {"support_ticket", "sos"} for item in audit.json()["items"])

    doc = read_text("docs/pilot/CONTROLLED_PILOT_INCIDENT_RESPONSE.md")
    assert "Preserve evidence" in doc
    assert "rollback" in doc.lower()
