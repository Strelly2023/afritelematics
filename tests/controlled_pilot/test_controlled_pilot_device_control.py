from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_device_control, pytest.mark.approved_devices_only]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_device_binding_revoke_and_audit_log_work() -> None:
    client = TestClient(app)
    rider_token = _token(client, "rider")
    bind = client.post("/v1/pilot/devices/bind", headers=auth_header(rider_token), json={"device_id": "device-rider-1"})
    assert bind.status_code == 200
    assert bind.json()["status"] == "bound"

    audit = client.get("/v1/pilot/audit", headers=auth_header(rider_token))
    assert audit.status_code == 200
    assert audit.json()["environment"] == "CONTROLLED_PILOT"
    assert any(item["action"] == "bind_device" for item in audit.json()["items"])

    revoke = client.post("/v1/pilot/devices/revoke", headers=auth_header(rider_token), json={"device_id": "device-rider-1"})
    assert revoke.status_code == 200
    assert revoke.json()["revoked"] is True

    blocked = client.post(
        "/v1/pilot/access/check",
        headers=auth_header(rider_token),
        json={"device_id": "device-rider-1", "surface": "rider"},
    )
    assert blocked.status_code == 200
    assert blocked.json()["allowed"] is False
    assert blocked.json()["reason"] == "device_not_approved"

    device_rebind = client.post("/v1/pilot/devices/bind", headers=auth_header(rider_token), json={"device_id": "device-rider-1"})
    assert device_rebind.status_code == 200

    unapproved = client.post("/v1/pilot/devices/bind", headers=auth_header(rider_token), json={"device_id": "device-unknown"})
    assert unapproved.status_code == 403
