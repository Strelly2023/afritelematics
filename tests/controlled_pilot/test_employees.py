from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.main import app
from tests.controlled_pilot._helpers import auth_header, read_json, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.identity]


def test_controlled_pilot_employee_population_and_access() -> None:
    registry = read_json("docs/pilot/approved_pilot_registry.json")
    assert len(registry["approved_employees"]) == 10
    assert "employee-001" in registry["approved_employees"]

    client = TestClient(app)
    token = JWT.create_token("employee-003", role="OBSERVER")
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(token), json={"device_id": "device-040"}).status_code == 200
    access = client.post("/v1/pilot/access/check", headers=auth_header(token), json={"device_id": "device-040", "surface": "identity"})
    assert access.status_code == 200
    assert access.json()["allowed"] is True
