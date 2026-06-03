from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.ingestion.event_ingestion import MobileEventAuthenticator


ROOT = Path(__file__).resolve().parents[3]


def test_flutter_pilot_clients_are_event_producers() -> None:
    required_files = [
        ROOT / "afriride_system/flutter/driver_app/lib/core/event_store.dart",
        ROOT / "afriride_system/flutter/driver_app/lib/core/logical_clock.dart",
        ROOT / "afriride_system/flutter/driver_app/lib/core/signer.dart",
        ROOT / "afriride_system/flutter/driver_app/lib/driver/driver_controller.dart",
        ROOT / "afriride_system/flutter/driver_app/lib/driver/gps_service.dart",
        ROOT / "afriride_system/flutter/rider_app/lib/core/event_store.dart",
        ROOT / "afriride_system/flutter/rider_app/lib/core/logical_clock.dart",
        ROOT / "afriride_system/flutter/rider_app/lib/core/signer.dart",
        ROOT / "afriride_system/flutter/rider_app/lib/rider/rider_controller.dart",
        ROOT / "afriride_system/flutter/rider_app/lib/rider/ws_client.dart",
    ]

    for path in required_files:
        assert path.exists(), f"missing pilot client file: {path}"

    driver_controller = (ROOT / "afriride_system/flutter/driver_app/lib/driver/driver_controller.dart").read_text()
    rider_controller = (ROOT / "afriride_system/flutter/rider_app/lib/rider/rider_controller.dart").read_text()

    assert "DRIVER_ACCEPTED_RIDE" in driver_controller
    assert "DRIVER_LOCATION_UPDATE" in driver_controller
    assert "RIDER_REQUESTED_RIDE" in rider_controller
    assert "/v1/events" in (ROOT / "afriride_system/flutter/driver_app/lib/core/api_client.dart").read_text()


def test_pilot_docker_stack_targets_constitutional_api() -> None:
    dockerfile = (ROOT / "afritech/docker/Dockerfile.pilot").read_text()
    compose = (ROOT / "afritech/docker/docker-compose.pilot.yml").read_text()

    assert "afritech.api.app:app" in dockerfile
    assert "uvicorn" in dockerfile
    assert "pilot-api" in compose
    assert "8000:8000" in compose


def test_fastapi_root_reports_bounded_pilot_status() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["classification"] == "controlled_pilot_api"
    assert body["product_ready"] is False
    assert body["docs"] == "/docs"


def test_fastapi_pilot_ingestion_accepts_signed_mobile_event() -> None:
    client = TestClient(app)
    event = {
        "event_id": "pilot_driver_1_101",
        "event_type": "DRIVER_ACCEPTED_RIDE",
        "device_id": "pilot_driver_1",
        "entity_id": "ride_123",
        "timestamp": 1710000000000,
        "logical_clock": 101,
        "payload": {"ride_id": "ride_123"},
        "signature": "",
    }
    event["signature"] = MobileEventAuthenticator().generate_signature(event, "pilot-secret")

    response = client.post("/v1/events", json={"received_at_ms": 1710000000100, "events": [event]})

    assert response.status_code == 200
    assert response.json()["accepted"] == ["pilot_driver_1_101"]
    assert response.json()["rejected"] == []


def test_realtime_projection_endpoint_is_observation_only() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/realtime/ride/ride_123/projection",
        json={"data": {"status": "DRIVER_EN_ROUTE"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "published"
    assert body["message"]["authority"] == "projection_only"
    assert body["message"]["type"] == "STATE_UPDATE"
