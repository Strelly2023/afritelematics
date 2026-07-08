from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from afriride_system.pilot import public_pilot
from afriride_system.pilot.public_pilot import bind_device
from tests.public_pilot._helpers import PUBLIC_PILOT_ACCOUNTS, auth_header, load_source_text, public_pilot_approval_payload, token_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.novaride, pytest.mark.rider, pytest.mark.driver, pytest.mark.operator]


def _token(client: TestClient, user_key: str) -> str:
    user_id, role, _, _ = PUBLIC_PILOT_ACCOUNTS[user_key]
    response = client.post("/auth/token", json=token_payload(user_id, role))
    assert response.status_code == 200
    return response.json()["token"]


def _install_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    path.write_text(json.dumps(public_pilot_approval_payload(), indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_novaride_rider_driver_operator_flow(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    client = TestClient(app)
    rider_token = _token(client, "rider")
    driver_token = _token(client, "driver")
    operator_token = _token(client, "operator")
    ride_id = f"public-pilot-ride-{uuid4().hex[:8]}"
    rider_id, _, rider_device, rider_region = PUBLIC_PILOT_ACCOUNTS["rider"]
    driver_id, _, driver_device, _ = PUBLIC_PILOT_ACCOUNTS["driver"]
    operator_id, _, operator_device, _ = PUBLIC_PILOT_ACCOUNTS["operator"]

    assert bind_device(rider_id, rider_device)["status"] == "bound"
    assert bind_device(driver_id, driver_device)["status"] == "bound"
    assert bind_device(operator_id, operator_device)["status"] == "bound"

    access = client.post(
        "/v1/public-pilot/access/check",
        headers=auth_header(rider_token),
        json={"device_id": rider_device, "region": rider_region, "surface": "rider"},
    )
    assert access.status_code == 200
    assert access.json()["allowed"] is True

    request = client.post(
        "/passenger/request-ride",
        headers=auth_header(rider_token),
        json={"passenger_id": rider_id, "pickup": "Melbourne CBD", "destination": "Docklands", "ride_id": ride_id},
    )
    assert request.status_code == 200

    online = client.post("/driver/status", headers=auth_header(driver_token), json={"driver_id": driver_id, "online": True})
    assert online.status_code == 200
    assert client.get(f"/driver/requests/{driver_id}", headers=auth_header(driver_token)).status_code == 200
    assert client.post("/driver/accept", headers=auth_header(driver_token), json={"driver_id": driver_id, "ride_id": ride_id}).status_code == 200
    assert client.post("/driver/arrive", headers=auth_header(driver_token), json={"driver_id": driver_id, "ride_id": ride_id}).status_code == 200
    assert client.post("/driver/start", headers=auth_header(driver_token), json={"driver_id": driver_id, "ride_id": ride_id}).status_code == 200
    complete = client.post("/driver/complete", headers=auth_header(driver_token), json={"driver_id": driver_id, "ride_id": ride_id})
    assert complete.status_code == 200

    for path in (
        f"/ride/{ride_id}/receipt",
        f"/ride/{ride_id}/replay",
        f"/ride/{ride_id}/evidence",
        f"/ride/{ride_id}/ledger-receipt",
    ):
        assert client.get(path, headers=auth_header(rider_token)).status_code == 200

    assert client.get("/v1/operations/dashboard", headers=auth_header(operator_token)).status_code == 200
    assert client.post("/v1/pilot/support/tickets", headers=auth_header(operator_token), json={"ride_id": ride_id, "category": "public_pilot_support"}).status_code == 200
    assert client.post("/v1/pilot/safety/sos", headers=auth_header(rider_token), json={"ride_id": ride_id, "reason": "public pilot test"}).status_code == 200

    source = load_source_text("novaride_rider")
    assert "Book Ride" in source
    assert "Safety" in source
    assert "Profile" in source
