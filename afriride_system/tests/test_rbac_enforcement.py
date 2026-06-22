from __future__ import annotations

from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app


def auth(role: str, user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {JWT.create_token(user_id, role)}"}


def setup_function() -> None:
    reset_gateway()


def _complete_ride(client: TestClient, ride_id: str) -> None:
    client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers={"Idempotency-Key": f"{ride_id}-driver-online", **auth("DRIVER", "driver-1")},
    )
    client.post(
        "/passenger/request-ride",
        json={
            "passenger_id": "rider-1",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": ride_id,
        },
        headers={"Idempotency-Key": f"{ride_id}-request", **auth("RIDER", "rider-1")},
    )
    for action in ("accept", "arrive", "start", "complete"):
        client.post(
            f"/ride/{ride_id}/{action}",
            json={"driver_id": "driver-1"},
            headers={"Idempotency-Key": f"{ride_id}-{action}", **auth("DRIVER", "driver-1")},
        )


def test_dispatcher_and_fleet_owner_can_read_but_not_execute_driver_actions() -> None:
    client = TestClient(app)
    ride_id = "ride-rbac-enforcement-1"
    _complete_ride(client, ride_id)

    dispatcher_headers = auth("DISPATCHER", "dispatcher-1")
    fleet_owner_headers = auth("FLEET_OWNER", "fleet-owner-1")

    ride_status = client.get(f"/passenger/status/{ride_id}", headers=dispatcher_headers)
    assert ride_status.status_code == 200
    assert ride_status.json()["data"]["ride_id"] == ride_id

    receipt = client.get(f"/ride/{ride_id}/receipt", headers=dispatcher_headers)
    assert receipt.status_code == 200
    assert receipt.json()["ride_id"] == ride_id

    earnings = client.get("/driver/driver-1/earnings", headers=fleet_owner_headers)
    assert earnings.status_code == 200
    assert earnings.json()["driver_id"] == "driver-1"

    driver_status = client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": False},
        headers={"Idempotency-Key": "fleet-owner-status", **fleet_owner_headers},
    )
    assert driver_status.status_code == 200

    blocked = client.post(
        f"/ride/{ride_id}/start",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "dispatcher-start", **dispatcher_headers},
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "INSUFFICIENT_ROLE"
