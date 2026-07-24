from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_access_control, pytest.mark.approved_users_only]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_approved_users_devices_and_roles_are_enforced() -> None:
    client = TestClient(app)

    rider_token = _token(client, "rider")
    driver_token = _token(client, "driver")
    operator_token = _token(client, "operator")
    merchant_token = _token(client, "merchant")

    assert client.post("/v1/pilot/devices/bind", headers=auth_header(rider_token), json={"device_id": "device-011"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(driver_token), json={"device_id": "device-001"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(operator_token), json={"device_id": "device-038"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(merchant_token), json={"device_id": "device-031"}).status_code == 200

    rider_access = client.post(
        "/v1/pilot/access/check",
        headers=auth_header(rider_token),
        json={"device_id": "device-011", "surface": "rider"},
    )
    assert rider_access.status_code == 200
    assert rider_access.json()["allowed"] is True

    driver_access = client.post(
        "/v1/pilot/access/check",
        headers=auth_header(driver_token),
        json={"device_id": "device-001", "surface": "driver"},
    )
    assert driver_access.status_code == 200
    assert driver_access.json()["allowed"] is True

    operator_access = client.post(
        "/v1/pilot/access/check",
        headers=auth_header(operator_token),
        json={"device_id": "device-038", "surface": "operator"},
    )
    assert operator_access.status_code == 200
    assert operator_access.json()["allowed"] is True

    unauthorized = client.post(
        "/v1/pilot/access/check",
        headers=auth_header(rider_token),
        json={"device_id": "device-011", "surface": "driver"},
    )
    assert unauthorized.status_code == 200
    assert unauthorized.json()["allowed"] is False
    assert unauthorized.json()["reason"] == "role_not_authorized"

    unapproved = client.post(
        "/v1/pilot/access/check",
        headers=auth_header(JWT.create_token("intruder-1", role="CUSTOMER")),
        json={"device_id": "device-011", "surface": "rider"},
    )
    assert unapproved.status_code == 200
    assert unapproved.json()["allowed"] is False
    assert unapproved.json()["reason"] == "user_not_approved"
