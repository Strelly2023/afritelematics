from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_security]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_monitoring_support_and_health_endpoints_are_available() -> None:
    client = TestClient(app)
    operator_token = _token(client, "operator")
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/v1/architecture/signature", headers=auth_header(operator_token)).status_code == 200
    assert client.get("/v1/corridors", headers=auth_header(operator_token)).status_code == 200
    assert client.get("/v1/treasury/snapshot", headers=auth_header(operator_token)).status_code == 200
    assert client.get("/v1/operations/dashboard", headers=auth_header(operator_token)).status_code == 200
    assert client.get("/v1/operations/launch-readiness", headers=auth_header(operator_token)).status_code == 200
    assert client.get("/v1/operations/safety/incidents", headers=auth_header(operator_token)).status_code == 200
    assert client.post("/v1/pilot/support/tickets", headers=auth_header(operator_token), json={"summary": "pilot support"}).status_code == 200
    assert client.post("/v1/pilot/safety/sos", headers=auth_header(operator_token), json={"ride_id": "pilot-ride-001"}).status_code == 200
