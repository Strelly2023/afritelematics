from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_api, pytest.mark.pilot_security]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_controlled_pilot_server_validation_and_protected_endpoints_work() -> None:
    client = TestClient(app)
    operator_token = _token(client, "operator")

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    architecture = client.get("/v1/architecture/signature", headers=auth_header(operator_token))
    corridors = client.get("/v1/corridors", headers=auth_header(operator_token))
    treasury = client.get("/v1/treasury/snapshot", headers=auth_header(operator_token))
    registry = client.get("/v1/pilot/registry", headers=auth_header(operator_token))
    assert architecture.status_code == 200
    assert corridors.status_code == 200
    assert treasury.status_code == 200
    assert registry.status_code == 200
    assert registry.json()["config"]["environment"] == "CONTROLLED_PILOT"

    assert client.get("/v1/architecture/signature").status_code == 401
    assert client.get("/v1/corridors").status_code == 401
    assert client.get("/v1/treasury/snapshot").status_code == 401
    assert client.get("/v1/pilot/registry").status_code == 401

    payload = treasury.json()
    assert "secret" not in str(payload).lower()
    assert payload["mode"] == "SIMULATED"
    assert payload["simulated"] is True
