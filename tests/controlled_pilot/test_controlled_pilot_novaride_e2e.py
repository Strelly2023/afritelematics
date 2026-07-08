from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.controlled_pilot._helpers import PILOT_ACCOUNTS, auth_header, load_source_text, token_payload


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_mobile, pytest.mark.novaride, pytest.mark.rider, pytest.mark.driver, pytest.mark.operator]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _ = PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def test_rider_driver_operator_pilot_flow_is_available() -> None:
    client = TestClient(app)
    rider_token = _token(client, "rider")
    driver_token = _token(client, "driver")
    operator_token = _token(client, "operator")
    ride_id = f"pilot-ride-{uuid4().hex[:8]}"

    assert client.post("/v1/pilot/devices/bind", headers=auth_header(rider_token), json={"device_id": "device-rider-1"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(driver_token), json={"device_id": "device-rider-1"}).status_code == 200
    assert client.post("/v1/pilot/devices/bind", headers=auth_header(operator_token), json={"device_id": "device-business-1"}).status_code == 200

    request = client.post(
        "/passenger/request-ride",
        headers=auth_header(rider_token),
        json={"passenger_id": "pilot-rider-1", "pickup": "Melbourne CBD", "destination": "Docklands", "ride_id": ride_id},
    )
    assert request.status_code == 200
    ride = request.json()["data"]
    assert ride["ride_id"] == ride_id
    assert ride["status"] == "REQUESTED"

    online = client.post("/driver/status", headers=auth_header(driver_token), json={"driver_id": "driver-pilot-1", "online": True})
    assert online.status_code == 200

    requests = client.get("/driver/requests/driver-pilot-1", headers=auth_header(driver_token))
    assert requests.status_code == 200
    assert any(item["ride_id"] == ride_id for item in requests.json()["data"])

    accepted = client.post("/driver/accept", headers=auth_header(driver_token), json={"driver_id": "driver-pilot-1", "ride_id": ride_id})
    assert accepted.status_code == 200
    assert accepted.json()["data"]["status"] == "DRIVER_ASSIGNED"

    arrived = client.post("/driver/arrive", headers=auth_header(driver_token), json={"driver_id": "driver-pilot-1", "ride_id": ride_id})
    started = client.post("/driver/start", headers=auth_header(driver_token), json={"driver_id": "driver-pilot-1", "ride_id": ride_id})
    completed = client.post("/driver/complete", headers=auth_header(driver_token), json={"driver_id": "driver-pilot-1", "ride_id": ride_id})
    assert arrived.status_code == 200
    assert started.status_code == 200
    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "COMPLETED"

    receipt = client.get(f"/ride/{ride_id}/receipt", headers=auth_header(rider_token))
    replay = client.get(f"/ride/{ride_id}/replay", headers=auth_header(rider_token))
    evidence = client.get(f"/ride/{ride_id}/evidence", headers=auth_header(rider_token))
    ledger = client.get(f"/ride/{ride_id}/ledger-receipt", headers=auth_header(rider_token))
    for response in (receipt, replay, evidence, ledger):
        assert response.status_code == 200

    operations = client.get("/v1/operations/dashboard", headers=auth_header(operator_token))
    assert operations.status_code == 200
    assert "active" in str(operations.json()).lower()

    support = client.post("/v1/pilot/support/tickets", headers=auth_header(operator_token), json={"ride_id": ride_id, "category": "ride_support"})
    sos = client.post("/v1/pilot/safety/sos", headers=auth_header(rider_token), json={"ride_id": ride_id, "reason": "pilot test"})
    assert support.status_code == 200
    assert sos.status_code == 200

    source = load_source_text("novaride_rider")
    assert "Request Ride" in source
    assert "SOS" in source
