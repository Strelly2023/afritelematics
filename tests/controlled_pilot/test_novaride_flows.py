from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.novaride]


def test_controlled_pilot_novaride_core_flow() -> None:
    client = TestClient(app)
    rider_token = client.post("/auth/token", json=token_payload(*PILOT_ACCOUNTS["rider"][:2])).json()["token"]
    driver_token = client.post("/auth/token", json=token_payload(*PILOT_ACCOUNTS["driver"][:2])).json()["token"]
    operator_token = client.post("/auth/token", json=token_payload(*PILOT_ACCOUNTS["operator"][:2])).json()["token"]
    ride_id = f"cp-ride-{uuid4().hex[:8]}"

    assert client.post("/v1/pilot/devices/bind", headers=auth_header(rider_token), json={"device_id": "device-011"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(driver_token), json={"device_id": "device-001"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(operator_token), json={"device_id": "device-038"}).status_code == 200

    request = client.post("/passenger/request-ride", headers=auth_header(rider_token), json={"passenger_id": "rider-001", "pickup": "Melbourne CBD", "destination": "Docklands", "ride_id": ride_id})
    assert request.status_code == 200
    assert request.json()["data"]["ride_id"] == ride_id

    assert client.post("/driver/status", headers=auth_header(driver_token), json={"driver_id": "driver-001", "online": True}).status_code == 200
    assert client.post("/driver/accept", headers=auth_header(driver_token), json={"driver_id": "driver-001", "ride_id": ride_id}).status_code == 200
    assert client.post("/driver/arrive", headers=auth_header(driver_token), json={"driver_id": "driver-001", "ride_id": ride_id}).status_code == 200
    assert client.post("/driver/start", headers=auth_header(driver_token), json={"driver_id": "driver-001", "ride_id": ride_id}).status_code == 200
    assert client.post("/driver/complete", headers=auth_header(driver_token), json={"driver_id": "driver-001", "ride_id": ride_id}).status_code == 200

    for path in [
        f"/ride/{ride_id}/receipt",
        f"/ride/{ride_id}/replay",
        f"/ride/{ride_id}/evidence",
        f"/ride/{ride_id}/ledger-receipt",
    ]:
        assert client.get(path, headers=auth_header(rider_token)).status_code == 200

    assert client.get("/v1/operations/dashboard", headers=auth_header(operator_token)).status_code == 200
