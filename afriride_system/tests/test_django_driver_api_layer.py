from __future__ import annotations

import sys
from pathlib import Path

import pytest
from django.test import Client

from afriride_system.django_app.config.middleware import AFRIRIDE_ALLOWED_HEADERS


ROOT = Path(__file__).resolve().parents[2]
DJANGO_APP = ROOT / "afriride_system/django_app"

if str(DJANGO_APP) not in sys.path:
    sys.path.insert(0, str(DJANGO_APP))


def test_api_root_exposes_development_status():
    client = Client()

    for path in ("/", "/api/"):
        response = client.get(path, HTTP_ACCEPT="application/json")

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
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS=(
            "Content-Type, X-Client-Event-Id, X-AfriRide-Device-Id, "
            "X-AfriRide-App-Version, X-AfriRide-Event-Id, "
            "X-AfriRide-Client-Timestamp, X-AfriRide-Test-Mode"
        ),
    )
    assert preflight.status_code == 200
    assert preflight["Access-Control-Allow-Origin"] == "*"
    allowed_headers = set(preflight["Access-Control-Allow-Headers"].split(", "))
    assert allowed_headers >= set(AFRIRIDE_ALLOWED_HEADERS)

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


def test_root_operator_dashboard_routes_expose_trust_surface():
    client = Client()

    active = client.get("/rides/active", HTTP_ACCEPT="application/json")
    assert active.status_code == 200
    assert "rides" in active.json()

    replay = client.get("/system/replay/health", HTTP_ACCEPT="application/json")
    assert replay.status_code == 200
    assert replay.json()["replay_success_rate"] == "100%"
    assert replay.json()["failures"] == 0

    evidence = client.get("/system/evidence", HTTP_ACCEPT="application/json")
    assert evidence.status_code == 200
    assert evidence.json()["missing_traces"] == 0

    guards = client.get("/system/guards", HTTP_ACCEPT="application/json")
    assert guards.status_code == 200
    assert guards.json()["violations"] == []


@pytest.mark.django_db
def test_pilot_evidence_endpoint_records_real_world_surface_evidence():
    client = Client()

    response = client.post(
        "/pilot/evidence",
        data={
            "type": "gps_accuracy_event",
            "driver_id": "driver-demo-001",
            "surface": "driver_mobile",
            "payload": {
                "latitude": -37.814,
                "longitude": 144.963,
                "accuracy_m": 18,
            },
            "constraints": {"expected_max_accuracy_m": 50},
            "verdict": "pass",
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_EVENT_ID="evt-pilot-location",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "captured"
    assert response.json()["verdict"] == "pass"
    assert response.json()["validator"]["name"] == "real_device_validator.gps_accuracy"

    graph = client.get("/trust/graph", HTTP_ACCEPT="application/json")
    latest = graph.json()["records"][0]
    assert latest["proposal"]["type"] == "PilotEvidenceCaptured"
    assert latest["proposal"]["source"] == "driver_mobile_pilot"
    assert latest["proposal"]["change"]["type"] == "gps_accuracy_event"


@pytest.mark.django_db
def test_pilot_latency_and_movement_validators_detect_violations():
    client = Client()

    latency = client.post(
        "/pilot/evidence",
        data={
            "type": "network_latency_event",
            "driver_id": "driver-demo-001",
            "payload": {"latency_ms": 1200, "path": "/driver/D001/queue"},
            "constraints": {"expected_max_latency_ms": 800},
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert latency.status_code == 200
    assert latency.json()["verdict"] == "violation"
    assert latency.json()["validator"]["name"] == "pilot_latency_threshold_validator"

    speed = client.post(
        "/pilot/evidence",
        data={
            "type": "speed_consistency_event",
            "driver_id": "driver-demo-001",
            "payload": {"speed_kph": 180},
            "constraints": {"expected_max_speed_kph": 130},
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert speed.status_code == 200
    assert speed.json()["verdict"] == "violation"
    assert speed.json()["validator"]["name"] == (
        "long_duration_continuity_validator.speed_consistency"
    )


@pytest.mark.django_db
def test_driver_action_writes_trust_graph_and_conversation_explains_decision():
    client = Client()

    accepted = client.post(
        "/ride/ride-trust-graph/accept",
        data={"driver_id": "D001"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_DEVICE_ID="operator-test-device",
        HTTP_X_AFRIRIDE_APP_VERSION="0.1",
        HTTP_X_AFRIRIDE_EVENT_ID="evt-trust-graph-accept",
        HTTP_X_AFRIRIDE_CLIENT_TIMESTAMP="2026-06-06T00:00:00Z",
        HTTP_X_AFRIRIDE_TEST_MODE="true",
    )
    assert accepted.status_code == 200

    graph = client.get("/trust/graph", HTTP_ACCEPT="application/json")
    assert graph.status_code == 200
    records = graph.json()["records"]
    assert records
    latest = records[0]
    assert latest["event_id"] == "evt-trust-graph-accept"
    assert latest["proposal"]["type"] == "RideAccepted"
    assert latest["validation"]["replay"] == "PASS"
    assert latest["decision"]["status"] == "approved"
    assert latest["execution"]["status"] == "applied"

    conversation = client.post(
        "/trust/conversation",
        data={"query": "Why was this ride approved?"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert conversation.status_code == 200
    payload = conversation.json()
    assert "approved" in payload["answer"]
    assert payload["evidence"]["proposal_id"] == latest["proposal_id"]


@pytest.mark.django_db
def test_trust_process_creates_risk_prediction_and_proof_certificate():
    client = Client()

    response = client.post(
        "/trust/process",
        data={
            "type": "RideAccepted",
            "actor_id": "D001",
            "subject_id": "ride-ga-elite",
            "change": {
                "ride_id": "ride-ga-elite",
                "driver_id": "D001",
                "status": "accepted",
            },
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_EVENT_ID="evt-ga-elite-process",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "approved"
    assert payload["execution"] == "applied"
    assert payload["risk"]["level"] == "low"
    assert payload["proof"]["status"] == "valid"

    certificate = client.get(
        f"/trust/proof/{payload['proposal_id']}",
        HTTP_ACCEPT="application/json",
    )
    assert certificate.status_code == 200
    assert certificate.json()["status"] == "valid"


@pytest.mark.django_db
def test_governance_rule_quorum_activation_and_simulation():
    client = Client()

    saved = client.post(
        "/trust/rules/save",
        data={
            "name": "ride_status_pending",
            "condition_key": "status",
            "expected_value": "pending",
            "priority": "critical",
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert saved.status_code == 200
    version_id = saved.json()["version_id"]

    submitted = client.post(
        f"/trust/rules/{version_id}/submit",
        data={"required_approvals": 2},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert submitted.status_code == 200
    request_id = submitted.json()["request_id"]

    first_vote = client.post(
        f"/trust/change-requests/{request_id}/vote",
        data={"reviewer": "alice", "vote": "approve"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert first_vote.status_code == 200
    assert first_vote.json()["status"] == "pending"

    second_vote = client.post(
        f"/trust/change-requests/{request_id}/vote",
        data={"reviewer": "bob", "vote": "approve"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert second_vote.status_code == 200
    assert second_vote.json()["status"] == "approved"

    rules = client.get("/trust/rules", HTTP_ACCEPT="application/json")
    assert rules.status_code == 200
    active = rules.json()[0]["active_version"]
    assert active["status"] == "active"
    assert active["expected_value"] == "pending"

    rejected = client.post(
        "/trust/simulate",
        data={"type": "RideAccepted", "payload": {"ride_id": "R1", "driver_id": "D1", "status": "completed"}},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert rejected.status_code == 200
    assert rejected.json()["decision"]["approved"] is False
    assert rejected.json()["risk"]["level"] in {"medium", "high"}
