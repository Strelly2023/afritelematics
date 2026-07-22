from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app
from afriride_system.operations.fleet_twin import TrustSafetyEngine, build_fleet_twin


def auth(role: str, actor: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {JWT.create_token(actor, role)}"}


def device_auth(role: str, actor: str) -> dict[str, str]:
    token = JWT.create_token(actor, role)
    return {"Authorization": f"Bearer {token}"}


def telemetry(driver_id: str, **overrides):
    values = {
        "driver_id": driver_id,
        "latitude": -37.8136,
        "longitude": 144.9631,
        "heading": 90,
        "speed_mps": 10,
        "accuracy_m": 8,
        "battery_level": 80,
        "device_trusted": True,
        "is_mocked": False,
        "route_deviation_m": 0,
        "stationary_seconds": 0,
        "captured_at": datetime.now(UTC).isoformat(),
    }
    values.update(overrides)
    return values


def test_trust_safety_detects_spoofing_speed_stop_route_and_integrity() -> None:
    engine = TrustSafetyEngine()
    current = telemetry(
        "driver-risk",
        speed_mps=40,
        is_mocked=True,
        route_deviation_m=900,
        stationary_seconds=700,
        device_trusted=False,
    )
    types = {signal["type"] for signal in engine.evaluate(current)}
    assert types == {
        "gps_spoofing",
        "unsafe_speed",
        "long_stop",
        "unexpected_route_deviation",
        "device_integrity",
    }


def test_digital_twin_projects_positions_rides_heat_traffic_health_and_queues() -> None:
    gateway = reset_gateway()
    gateway.driver.status({"driver_id": "driver-twin", "online": True})
    gateway.passenger.request_ride({
        "ride_id": "ride-twin",
        "passenger_id": "rider-twin",
        "pickup": "A",
        "destination": "B",
    })
    gateway.fleet_operations_repository.upsert_telemetry(telemetry("driver-twin"))
    twin = build_fleet_twin(gateway)
    assert twin["driver_positions"][0]["driver_id"] == "driver-twin"
    assert twin["active_rides"][0]["ride_id"] == "ride-twin"
    assert twin["heat_map"]
    assert twin["traffic"]
    assert twin["fleet_health"]["online_drivers"] == 1
    assert twin["queue_lengths"]["unassigned_rides"] == 1
    assert twin["authority"] == "projection_only"


def test_location_signal_creates_incident_and_command_center_displays_it() -> None:
    reset_gateway()
    client = TestClient(app)
    response = client.post(
        "/v1/drivers/location",
        json={
            "driver_id": "driver-spoof",
            "lat": -37.81,
            "lng": 144.96,
            "speed_mps": 45,
            "is_mocked": True,
            "device_trusted": False,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        headers=device_auth("DRIVER", "driver-spoof"),
    )
    assert response.status_code == 200
    assert response.json()["safety_signal_count"] >= 3
    twin = client.get(
        "/v1/operations/digital-twin", headers=auth("OPERATOR", "operator-1")
    )
    assert twin.status_code == 200
    assert twin.json()["safety_alerts"]


def test_rider_distress_is_idempotent_and_triggers_sos_workflow() -> None:
    reset_gateway()
    client = TestClient(app)
    payload = {
        "rider_id": "rider-sos",
        "ride_id": "ride-sos",
        "latitude": -37.81,
        "longitude": 144.96,
        "signal": "silent_sos",
    }
    first = client.post(
        "/v1/operations/safety/distress",
        json=payload,
        headers=auth("CUSTOMER", "rider-sos"),
    )
    second = client.post(
        "/v1/operations/safety/distress",
        json=payload,
        headers=auth("CUSTOMER", "rider-sos"),
    )
    assert first.status_code == 200
    assert second.json()["incident"]["incident_id"] == first.json()["incident"]["incident_id"]
    assert first.json()["incident"]["workflow"] == "sos_handling"
    action = client.post(
        f"/v1/operations/safety/incidents/{first.json()['incident']['incident_id']}/actions",
        json={"action": "sos_dispatched"},
        headers=auth("OPERATOR", "operator-1"),
    )
    assert action.status_code == 200
    assert action.json()["status"] == "responding"


def test_safety_sweep_creates_driver_inactivity_verification() -> None:
    gateway = reset_gateway()
    gateway.fleet_operations_repository.upsert_telemetry(
        telemetry(
            "driver-stale",
            captured_at=(datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
        )
    )
    response = TestClient(app).post(
        "/v1/operations/safety/sweep", headers=auth("OPERATOR", "operator-1")
    )
    assert response.status_code == 200
    incident = response.json()["incidents"][0]
    assert incident["incident_type"] == "driver_inactivity"
    assert incident["workflow"] == "driver_verification"
