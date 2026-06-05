from __future__ import annotations

import sys
from pathlib import Path

from django.test import Client


ROOT = Path(__file__).resolve().parents[2]
DJANGO_APP = ROOT / "afriride_system/django_app"

if str(DJANGO_APP) not in sys.path:
    sys.path.insert(0, str(DJANGO_APP))


def test_api_root_exposes_development_status():
    response = Client().get("/api/", HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "afriride-django-api"


def test_driver_api_minimal_lifecycle_matches_mobile_response_shape():
    client = Client()

    availability = client.post(
        "/api/driver/availability",
        data={"driver_id": "D001", "status": "available"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert availability.status_code == 200
    assert availability.json()["status"] == "available"

    queue = client.get("/api/driver/D001/queue", HTTP_ACCEPT="application/json")
    assert queue.status_code == 200
    rides = queue.json()["rides"]
    assert rides
    ride_id = rides[0]["ride_id"]

    accepted = client.post(
        f"/api/ride/{ride_id}/accept",
        data={"driver_id": "D001"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    arrived = client.post(
        "/api/ride/arrive",
        data={"ride_id": ride_id, "driver_id": "D001"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert arrived.status_code == 200
    assert arrived.json()["status"] == "arrived"

    started = client.post(
        f"/api/ride/{ride_id}/start",
        data={"driver_id": "D001"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert started.status_code == 200
    assert started.json()["status"] == "started"

    completed = client.post(
        f"/api/ride/{ride_id}/complete",
        data={"driver_id": "D001"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    earnings = client.get("/api/driver/D001/earnings", HTTP_ACCEPT="application/json")
    assert earnings.status_code == 200
    assert earnings.json()["source"] == "core_system"

    replay = client.get(
        "/api/driver/replay-history?driver_id=D001",
        HTTP_ACCEPT="application/json",
    )
    assert replay.status_code == 200
    assert replay.json()["rides"][0]["replay_verified"] is True


def test_root_driver_compatibility_routes_support_web_preflight_and_mobile_paths():
    client = Client()

    preflight = client.options(
        "/driver/availability",
        HTTP_ORIGIN="http://localhost:8081",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="Content-Type, X-Client-Event-Id",
    )
    assert preflight.status_code == 200
    assert preflight["Access-Control-Allow-Origin"] == "*"

    availability = client.post(
        "/driver/availability",
        data={"driver_id": "D001", "status": "available"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_ORIGIN="http://localhost:8081",
    )
    assert availability.status_code == 200
    assert availability["Access-Control-Allow-Origin"] == "*"
    assert availability.json()["driver_id"] == "D001"
