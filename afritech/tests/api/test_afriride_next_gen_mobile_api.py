from __future__ import annotations

from importlib import import_module

from fastapi.testclient import TestClient

from afritech.api.app import app

_runtime = import_module("afriride_system.api.dependencies.runtime")
reset_gateway = _runtime.reset_gateway
reset_trace_log = _runtime.reset_trace_log


def test_next_gen_mobile_api_supports_rider_driver_and_operator_flows(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "next-gen-mobile.sqlite3"))
    reset_gateway()
    reset_trace_log()

    client = TestClient(app)

    session = client.post(
        "/v1/mobile/auth/session",
        json={
            "actor_id": "rider-1",
            "role": "RIDER",
            "device_id": "device-1",
            "app_version": "1.0.0",
            "platform": "ios",
        },
    )
    assert session.status_code == 200
    assert session.json()["actor_id"] == "rider-1"

    driver_online = client.post(
        "/v1/driver/driver-1/availability",
        json={"status": "available"},
    )
    assert driver_online.status_code == 200
    assert driver_online.json()["status"] == "available"

    requested = client.post(
        "/v1/rider/rides",
        json={
            "rider_id": "rider-1",
            "pickup": "Melbourne CBD",
            "dropoff": "Melbourne Airport",
            "ride_id": "ride-next-gen-001",
            "ride_type": "Airport",
        },
        headers={"Idempotency-Key": "ride-next-gen-request-001"},
    )
    assert requested.status_code == 200
    assert requested.json()["status"] == "requested"

    queue = client.get("/v1/driver/driver-1/ride-queue")
    assert queue.status_code == 200
    assert queue.json()["items"][0]["ride_id"] == "ride-next-gen-001"

    accepted = client.post(
        "/v1/driver/rides/ride-next-gen-001/accept",
        json={"driver_id": "driver-1"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    arrived = client.post(
        "/v1/driver/rides/ride-next-gen-001/arrive",
        json={"driver_id": "driver-1"},
    )
    assert arrived.status_code == 200
    assert arrived.json()["status"] == "arrived"

    started = client.post(
        "/v1/driver/rides/ride-next-gen-001/start",
        json={"driver_id": "driver-1"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "started"

    completed = client.post(
        "/v1/driver/rides/ride-next-gen-001/complete",
        json={"driver_id": "driver-1"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    receipt = client.get("/v1/rider/rides/ride-next-gen-001/receipt")
    assert receipt.status_code == 200
    assert receipt.json()["verification_status"] == "PASSED"

    replay = client.get("/v1/rider/rides/ride-next-gen-001/replay")
    assert replay.status_code == 200
    assert replay.json()["replay_verified"] is True

    operator = client.get("/v1/operator/dashboard")
    assert operator.status_code == 200
    payload = operator.json()
    assert "fleet_trust_score" in payload
    assert "driver_trust_trend" in payload
    assert "public_verification" in payload
