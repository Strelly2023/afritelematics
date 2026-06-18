"""Regression tests for AfriRide product routes on the AfriTech FastAPI app."""

from __future__ import annotations

from importlib import import_module

from fastapi.testclient import TestClient

from afritech.api.app import app

_runtime = import_module("afriride_system.api.dependencies.runtime")
reset_gateway = _runtime.reset_gateway
reset_trace_log = _runtime.reset_trace_log


def test_dashboard_operational_routes_are_mounted(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "dashboard-routes.sqlite3"))
    reset_gateway()
    reset_trace_log()

    client = TestClient(app)

    assert client.get("/rides/active").status_code == 200
    assert client.get("/system/drivers").status_code == 200
    assert client.get("/system/replay/health").status_code == 200
    assert client.get("/system/trust-metrics").status_code == 200
    assert client.get("/system/pilot-metrics").status_code == 200


def test_full_mobile_ready_ride_flow_on_top_level_fastapi(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "ride-flow.sqlite3"))
    reset_gateway()
    reset_trace_log()

    client = TestClient(app)
    ride_id = "ride-product-flow-001"
    driver_id = "driver-product-001"

    driver = client.post(
        "/driver/status",
        json={"driver_id": driver_id, "online": True},
        headers={"Idempotency-Key": "driver-product-online-001"},
    )
    assert driver.status_code == 200
    assert driver.json()["data"]["online"] is True

    requested = client.post(
        "/ride/request",
        json={
            "passenger_id": "rider-product-001",
            "pickup": "Bujumbura Central",
            "destination": "Rohero Market",
            "ride_id": ride_id,
        },
        headers={"Idempotency-Key": "request-product-flow-001"},
    )
    assert requested.status_code == 200
    assert requested.json()["data"]["status"] == "REQUESTED"

    active = client.get("/rides/active")
    assert active.status_code == 200
    assert active.json()["rides"] == [
        {
            "ride_id": ride_id,
            "state": "REQUESTED",
            "driver_id": None,
            "rider_id": "rider-product-001",
        }
    ]

    accepted = client.post(
        f"/ride/{ride_id}/accept",
        json={"driver_id": driver_id},
        headers={"Idempotency-Key": "accept-product-flow-001"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "DRIVER_ASSIGNED"

    arrived = client.post(
        "/ride/arrive",
        json={"driver_id": driver_id, "ride_id": ride_id},
        headers={"Idempotency-Key": "arrive-product-flow-001"},
    )
    assert arrived.status_code == 200
    assert arrived.json()["data"]["status"] == "DRIVER_ARRIVED"

    started = client.post(
        f"/ride/{ride_id}/start",
        json={"driver_id": driver_id},
        headers={"Idempotency-Key": "start-product-flow-001"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "IN_TRIP"

    completed = client.post(
        f"/ride/{ride_id}/complete",
        json={"driver_id": driver_id},
        headers={"Idempotency-Key": "complete-product-flow-001"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    status = client.get(f"/ride/{ride_id}/status")
    assert status.status_code == 200
    assert status.json()["data"]["status"] == "COMPLETED"

    receipt = client.get(f"/ride/{ride_id}/receipt")
    assert receipt.status_code == 200
    assert receipt.json()["receipt_hash"]

    replay = client.get(f"/ride/{ride_id}/replay")
    assert replay.status_code == 200
    assert replay.json()["replay_verified"] is True

    evidence = client.get(f"/ride/{ride_id}/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["trace_hash"]

    price = client.get(f"/ride/{ride_id}/price-explanation")
    assert price.status_code == 200
    assert price.json()["source"] == "core_system"

    metrics = client.get("/system/trust-metrics")
    assert metrics.status_code == 200
    assert metrics.json()["trust_state"] in {"VERIFIED", "REVIEW"}
