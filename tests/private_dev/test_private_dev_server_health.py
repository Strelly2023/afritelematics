from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT
from afritech.afriprogramming.persistence import DEFAULT_ORGANIZATION_ID
from afriride_system.api.main import app


pytestmark = [pytest.mark.private_dev, pytest.mark.smoke]


def test_private_dev_server_health_and_authorized_snapshots() -> None:
    client = TestClient(app)
    token = client.post(
        "/auth/token",
        json={"user_id": "pilot-admin", "role": "ADMIN"},
    ).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/health").status_code == 200
    assert client.get("/health").json()["status"] == "ok"

    architecture = client.get("/v1/architecture/signature", headers=headers)
    assert architecture.status_code == 200
    assert architecture.json()["private_development"] is True
    assert architecture.json()["environment"] == "PRIVATE_DEVELOPMENT"

    treasury = client.get("/v1/treasury/snapshot", headers=headers)
    assert treasury.status_code == 200
    assert treasury.json()["simulated"] is True
    assert treasury.json()["mode"] == "SIMULATED"

    regions = client.get("/v1/global/regions", headers=headers)
    assert regions.status_code == 200
    assert "Australia" in str(regions.json())


def test_rider_request_reaches_driver_queue_in_private_dev() -> None:
    client = TestClient(app)
    driver_token = JWT.create_token(
        "driver-1", role="DRIVER", organization_id=DEFAULT_ORGANIZATION_ID
    )
    driver_headers = {"Authorization": f"Bearer {driver_token}"}
    ride_id = f"ride-private-dev-{uuid4().hex[:8]}"
    rider_request = client.post(
        "/v1/rider/rides",
        json={
            "rider_id": "rider-1",
            "pickup": "Melbourne CBD",
            "dropoff": "Melbourne Airport",
            "pickup_lat": -37.81,
            "pickup_lng": 144.96,
            "ride_id": ride_id,
            "ride_type": "Airport",
        },
        headers={"Idempotency-Key": f"private-dev-ride-{ride_id}"},
    )
    assert rider_request.status_code == 200
    assert rider_request.json()["status"] == "requested"

    driver_online = client.post(
        "/v1/driver/driver-1/availability",
        json={"status": "available"},
        headers=driver_headers,
    )
    assert driver_online.status_code == 200

    queue = client.get("/v1/driver/driver-1/ride-queue", headers=driver_headers)
    assert queue.status_code == 200
    assert queue.json()["requested_count"] >= 1
    assert any(item["ride_id"] == ride_id for item in queue.json()["items"])
