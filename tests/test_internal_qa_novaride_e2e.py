from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app
from tests.internal_qa._helpers import BUTTON_REGISTRY_PATH, read_json, read_text
from tests.private_dev._helpers import assert_contains_all


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_mobile, pytest.mark.novaride, pytest.mark.rider, pytest.mark.driver, pytest.mark.operator]


def test_novaride_internal_qa_app_surfaces_are_documented() -> None:
    registry = read_json(BUTTON_REGISTRY_PATH)["apps"]
    rider = read_text("rider_app/App.tsx")
    driver = read_text("driver_app/App.tsx")
    operator = read_text("novaride_operator_app/App.tsx")

    assert_contains_all(rider, registry["novaride_rider"]["tabs"], context="NovaRide rider tabs")
    assert_contains_all(rider, registry["novaride_rider"]["buttons"], context="NovaRide rider buttons")
    assert_contains_all(driver, registry["novaride_driver"]["tabs"], context="NovaRide driver tabs")
    assert_contains_all(driver, registry["novaride_driver"]["buttons"], context="NovaRide driver buttons")
    assert_contains_all(operator, registry["novaride_operator"]["tabs"], context="NovaRide operator tabs")
    assert_contains_all(operator, registry["novaride_operator"]["buttons"], context="NovaRide operator buttons")


def test_novaride_internal_qa_ride_lifecycle_reaches_driver_queue() -> None:
    client = TestClient(app)
    token = client.post("/auth/token", json={"user_id": "qa-operator", "role": "ADMIN"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    ride_id = f"qa-ride-{uuid4().hex[:8]}"
    rider_request = client.post(
        "/v1/rider/rides",
        json={
            "rider_id": "rider-qa-1",
            "pickup": "Melbourne CBD",
            "dropoff": "Melbourne Airport",
            "pickup_lat": -37.8136,
            "pickup_lng": 144.9631,
            "ride_id": ride_id,
            "ride_type": "Comfort",
        },
        headers={"Idempotency-Key": f"qa-{ride_id}"},
    )
    assert rider_request.status_code == 200
    assert rider_request.json()["status"] == "requested"

    driver_online = client.post("/v1/driver/driver-1/availability", json={"status": "available"})
    assert driver_online.status_code == 200

    queue = client.get("/v1/driver/driver-1/ride-queue")
    assert queue.status_code == 200
    assert any(item["ride_id"] == ride_id for item in queue.json()["items"])

    dashboard = client.get("/v1/operations/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["status"] == "operational"

    trip = client.get(f"/v1/rider/rides/{ride_id}", headers=headers)
    assert trip.status_code == 200
    assert trip.json()["ride_id"] == ride_id
