from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest
from django.test import Client

from afritech.api import afriride_driver_views
from afriride_system.django_app.config.middleware import AFRIRIDE_ALLOWED_HEADERS


ROOT = Path(__file__).resolve().parents[2]
DJANGO_APP = ROOT / "afriride_system/django_app"

if str(DJANGO_APP) not in sys.path:
    sys.path.insert(0, str(DJANGO_APP))


@pytest.fixture(autouse=True)
def isolate_pilot_observability_records(tmp_path, monkeypatch):
    monkeypatch.setattr(
        afriride_driver_views,
        "PILOT_OBSERVABILITY_RECORDS_PATH",
        tmp_path / "pilot_observability_records.jsonl",
    )


def test_api_root_exposes_development_status():
    client = Client()

    for path in ("/", "/api/"):
        response = client.get(path, HTTP_ACCEPT="application/json")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["service"] == "afriride-django-api"


def test_health_route_exposes_simple_readiness_payload():
    client = Client()

    response = client.get("/health", HTTP_ACCEPT="application/json")

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


def test_evidence_and_guard_summary_routes_are_lightweight() -> None:
    client = Client()

    evidence = client.get("/system/evidence/summary", HTTP_ACCEPT="application/json")
    guards = client.get("/system/guards/summary", HTTP_ACCEPT="application/json")

    assert evidence.status_code == 200
    assert evidence.json()["summary"]["status"] == "healthy"

    assert guards.status_code == 200
    assert guards.json()["summary"]["violations_count"] == 0
    assert guards.json()["summary"]["highest_severity"] == "NONE"


def test_driver_queue_reseeds_pending_ride_after_completed_cycle():
    client = Client()

    first_queue = client.get("/driver/driver-demo-001/queue", HTTP_ACCEPT="application/json")
    assert first_queue.status_code == 200
    first_ride_id = first_queue.json()["rides"][0]["ride_id"]

    for path, payload in (
        (f"/ride/{first_ride_id}/accept", {"driver_id": "driver-demo-001"}),
        ("/ride/arrive", {"ride_id": first_ride_id, "driver_id": "driver-demo-001"}),
        (f"/ride/{first_ride_id}/start", {"driver_id": "driver-demo-001"}),
        (f"/ride/{first_ride_id}/complete", {"driver_id": "driver-demo-001"}),
    ):
        response = client.post(
            path,
            data=payload,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        assert response.status_code == 200

    next_queue = client.get("/driver/driver-demo-001/queue", HTTP_ACCEPT="application/json")
    assert next_queue.status_code == 200
    rides = next_queue.json()["rides"]
    assert rides
    assert rides[0]["ride_id"] != first_ride_id
    assert rides[0]["status"] == "pending"


def test_driver_lifecycle_rejects_out_of_order_transitions():
    client = Client()

    queue = client.get("/driver/driver-demo-order/queue", HTTP_ACCEPT="application/json")
    assert queue.status_code == 200
    ride_id = queue.json()["rides"][0]["ride_id"]

    start_before_accept = client.post(
        f"/ride/{ride_id}/start",
        data={"driver_id": "driver-demo-order"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert start_before_accept.status_code == 409
    assert start_before_accept.json()["expected_status"] == "arrived"
    assert start_before_accept.json()["current_status"] == "pending"

    accepted = client.post(
        f"/ride/{ride_id}/accept",
        data={"driver_id": "driver-demo-order"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert accepted.status_code == 200

    complete_before_start = client.post(
        f"/ride/{ride_id}/complete",
        data={"driver_id": "driver-demo-order"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert complete_before_start.status_code == 409
    assert complete_before_start.json()["expected_status"] == "started"
    assert complete_before_start.json()["current_status"] == "accepted"

    arrived = client.post(
        "/ride/arrive",
        data={"ride_id": ride_id, "driver_id": "driver-demo-order"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert arrived.status_code == 200

    started = client.post(
        f"/ride/{ride_id}/start",
        data={"driver_id": "driver-demo-order"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert started.status_code == 200

    completed = client.post(
        f"/ride/{ride_id}/complete",
        data={"driver_id": "driver-demo-order"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert completed.status_code == 200

    arrive_after_complete = client.post(
        "/ride/arrive",
        data={"ride_id": ride_id, "driver_id": "driver-demo-order"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert arrive_after_complete.status_code == 409
    assert arrive_after_complete.json()["current_status"] == "completed"


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
def test_pilot_evidence_endpoint_logs_observability_trace_metadata(caplog):
    client = Client()
    trace_id = "0123456789abcdef0123456789abcdef"
    caplog.set_level(logging.INFO, logger="afritech.pilot_observability")

    response = client.post(
        "/pilot/evidence",
        data={
            "type": "gps_accuracy_event",
            "driver_id": "driver-demo-observable",
            "surface": "driver_mobile",
            "payload": {"accuracy_m": 15},
            "constraints": {"expected_max_accuracy_m": 50},
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_TRACE_ID=trace_id,
        HTTP_TRACEPARENT=f"00-{trace_id}-1111111111111111-01",
    )

    assert response.status_code == 200
    events = [json.loads(record.message) for record in caplog.records]
    log = next(event for event in events if event["event"] == "pilot_evidence_request")
    assert log["traceId"] == trace_id
    assert log["driverId"] == "driver-demo-observable"
    assert log["evidenceType"] == "gps_accuracy_event"
    assert log["status"] == 200
    assert isinstance(log["durationMs"], int)


@pytest.mark.django_db
def test_pilot_evidence_endpoint_appends_jsonl_observability_record(tmp_path, monkeypatch):
    client = Client()
    trace_id = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    records_path = tmp_path / "pilot_observability_records.jsonl"
    monkeypatch.setattr(
        afriride_driver_views,
        "PILOT_OBSERVABILITY_RECORDS_PATH",
        records_path,
    )

    response = client.post(
        "/pilot/evidence",
        data={
            "type": "driver_shift_started",
            "driver_id": "driver-demo-jsonl",
            "surface": "driver_mobile",
            "payload": {"driver_id": "driver-demo-jsonl"},
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_TRACE_ID=trace_id,
    )

    assert response.status_code == 200
    lines = records_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["traceId"] == trace_id
    assert record["driverId"] == "driver-demo-jsonl"
    assert record["evidenceType"] == "driver_shift_started"
    assert record["status"] == 200
    assert isinstance(record["durationMs"], int)
    assert "structuredError" in record
    assert record["structuredError"] is None
    assert record["timestamp"]


@pytest.mark.django_db
def test_pilot_evidence_observability_metadata_is_not_authority():
    client = Client()
    trace_id = "fedcba9876543210fedcba9876543210"

    response = client.post(
        "/pilot/evidence",
        data={
            "type": "driver_shift_started",
            "driver_id": "driver-demo-authority-boundary",
            "surface": "driver_mobile",
            "payload": {"driver_id": "driver-demo-authority-boundary"},
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_TRACE_ID=trace_id,
        HTTP_TRACEPARENT=f"00-{trace_id}-2222222222222222-01",
    )

    assert response.status_code == 200
    graph = client.get("/trust/graph", HTTP_ACCEPT="application/json")
    change = graph.json()["records"][0]["proposal"]["change"]
    assert change["type"] == "driver_shift_started"
    assert "traceId" not in change
    assert "traceparent" not in change
    assert "observability" not in change


@pytest.mark.django_db
def test_pilot_observability_export_does_not_alter_authority_records(tmp_path, monkeypatch):
    client = Client()
    trace_id = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    records_path = tmp_path / "pilot_observability_records.jsonl"
    monkeypatch.setattr(
        afriride_driver_views,
        "PILOT_OBSERVABILITY_RECORDS_PATH",
        records_path,
    )

    response = client.post(
        "/pilot/evidence",
        data={
            "type": "gps_accuracy_event",
            "driver_id": "driver-demo-export-boundary",
            "surface": "driver_mobile",
            "payload": {"accuracy_m": 9},
            "constraints": {"expected_max_accuracy_m": 50},
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_TRACE_ID=trace_id,
    )

    assert response.status_code == 200
    assert records_path.exists()
    graph = client.get("/trust/graph", HTTP_ACCEPT="application/json")
    change = graph.json()["records"][0]["proposal"]["change"]
    assert change["type"] == "gps_accuracy_event"
    assert "traceId" not in change
    assert "structuredError" not in change
    assert "observability" not in change


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
def test_pilot_metrics_correlate_sequence_violations_and_propose_response():
    client = Client()

    first = client.post(
        "/pilot/evidence",
        data={
            "type": "gps_signal_loss_event",
            "driver_id": "driver-demo-001",
            "payload": {"error": "timeout"},
            "constraints": {"expected_signal": "available"},
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_EVENT_ID="evt-pilot-gps-loss",
    )
    assert first.status_code == 200
    assert first.json()["verdict"] == "violation"

    second = client.post(
        "/pilot/evidence",
        data={
            "type": "route_deviation_event",
            "driver_id": "driver-demo-001",
            "payload": {"distance_m": 900},
            "constraints": {"expected_max_sample_distance_m": 250},
        },
        content_type="application/json",
        HTTP_ACCEPT="application/json",
        HTTP_X_AFRIRIDE_EVENT_ID="evt-pilot-route-deviation",
    )
    assert second.status_code == 200
    assert second.json()["verdict"] == "violation"

    metrics = client.get("/pilot/metrics", HTTP_ACCEPT="application/json")
    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload["totals"]["violations"] >= 2
    assert payload["violation_counts"]["gps_signal_loss_event"] == 1
    assert payload["violation_counts"]["route_deviation_event"] == 1
    assert payload["correlations"]
    assert payload["correlations"][0]["classification"] == "correlated_violation"
    assert payload["metrics"]["correlated_violation_rate"] > 0
    assert any(
        proposal["validator"] == "movement_sequence_validator"
        and proposal["status"] == "validated_proposal"
        and proposal["authority"] == "proposal_only_not_execution"
        for proposal in payload["anomaly_proposals"]
    )


@pytest.mark.django_db
def test_pilot_metrics_detect_stability_window_degradation():
    client = Client()

    sequence = [
        ("driver_location_event", {"latitude": -37.814, "longitude": 144.963}, {}),
        ("gps_accuracy_event", {"accuracy_m": 12}, {"expected_max_accuracy_m": 50}),
        ("driver_location_event", {"latitude": -37.815, "longitude": 144.964}, {}),
        ("network_latency_event", {"latency_ms": 1200}, {"expected_max_latency_ms": 800}),
        ("gps_signal_loss_event", {"error": "timeout"}, {"expected_signal": "available"}),
        ("speed_consistency_event", {"speed_kph": 180}, {"expected_max_speed_kph": 130}),
    ]

    for index, (event_type, payload, constraints) in enumerate(sequence):
        response = client.post(
            "/pilot/evidence",
            data={
                "type": event_type,
                "driver_id": "driver-demo-001",
                "payload": payload,
                "constraints": constraints,
            },
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_AFRIRIDE_EVENT_ID=f"evt-pilot-stability-{index}",
        )
        assert response.status_code == 200

    metrics = client.get("/pilot/metrics", HTTP_ACCEPT="application/json")
    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload["stability"]["classification"] == "system_degradation"
    assert payload["stability"]["increasing_violation_rate"] is True
    stability_proposal = next(
        proposal
        for proposal in payload["anomaly_proposals"]
        if proposal["validator"] == "time_window_stability_validator"
    )
    assert stability_proposal["status"] == "validated_proposal"
    assert stability_proposal["priority_score"] >= 50


@pytest.mark.django_db
def test_pilot_readiness_gate_allows_candidate_claim_but_not_production_proven():
    client = Client()

    sequence = [
        ("driver_location_event", {"latitude": -37.814, "longitude": 144.963}, {}),
        ("gps_accuracy_event", {"accuracy_m": 18}, {"expected_max_accuracy_m": 50}),
        ("network_latency_event", {"latency_ms": 420}, {"expected_max_latency_ms": 800}),
        ("route_deviation_event", {"distance_m": 120}, {"expected_max_sample_distance_m": 250}),
        ("speed_consistency_event", {"speed_kph": 42}, {"expected_max_speed_kph": 130}),
    ]

    for index in range(20):
        event_type, payload, constraints = sequence[index % len(sequence)]
        response = client.post(
            "/pilot/evidence",
            data={
                "type": event_type,
                "driver_id": "driver-demo-001",
                "payload": payload,
                "constraints": constraints,
            },
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_AFRIRIDE_EVENT_ID=f"evt-pilot-clean-readiness-{index}",
        )
        assert response.status_code == 200
        assert response.json()["verdict"] in {"pass", "observed"}

    readiness = client.get("/pilot/readiness", HTTP_ACCEPT="application/json")
    assert readiness.status_code == 200
    payload = readiness.json()
    assert payload["profile"] == "melbourne_airport_controlled_pilot"
    assert payload["classification"] == "PRODUCTION_CANDIDATE_ELIGIBLE"
    assert payload["production_claim_authorized"] is True
    assert payload["production_proven"] is False
    assert payload["authority"] == "readiness_assessment_only_not_launch_authorization"
    assert payload["blocking_reasons"] == []
    assert all(check["passed"] for check in payload["checks"])


@pytest.mark.django_db
def test_pilot_readiness_gate_rejects_skewed_evidence_without_per_type_coverage():
    client = Client()

    for index in range(20):
        response = client.post(
            "/pilot/evidence",
            data={
                "type": "network_latency_event",
                "driver_id": "driver-demo-001",
                "payload": {"latency_ms": 420},
                "constraints": {"expected_max_latency_ms": 800},
            },
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_AFRIRIDE_EVENT_ID=f"evt-pilot-skewed-readiness-{index}",
        )
        assert response.status_code == 200

    readiness = client.get("/pilot/readiness", HTTP_ACCEPT="application/json")
    assert readiness.status_code == 200
    payload = readiness.json()
    assert payload["classification"] == "CONTROLLED_PILOT_CONTINUE"
    assert payload["production_claim_authorized"] is False
    assert any(
        check["name"] == "minimum_evidence_per_required_type"
        and check["passed"] is False
        and "driver_location_event" in check["actual"]
        for check in payload["checks"]
    )


@pytest.mark.django_db
def test_pilot_readiness_gate_blocks_candidate_claim_when_reality_degrades():
    client = Client()

    for index in range(14):
        response = client.post(
            "/pilot/evidence",
            data={
                "type": "network_latency_event",
                "driver_id": "driver-demo-001",
                "payload": {"latency_ms": 420},
                "constraints": {"expected_max_latency_ms": 800},
            },
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_AFRIRIDE_EVENT_ID=f"evt-pilot-readiness-pass-{index}",
        )
        assert response.status_code == 200

    for index in range(6):
        response = client.post(
            "/pilot/evidence",
            data={
                "type": "gps_signal_loss_event",
                "driver_id": "driver-demo-001",
                "payload": {"error": "timeout"},
                "constraints": {"expected_signal": "available"},
            },
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_AFRIRIDE_EVENT_ID=f"evt-pilot-readiness-loss-{index}",
        )
        assert response.status_code == 200
        assert response.json()["verdict"] == "violation"

    readiness = client.get("/pilot/readiness", HTTP_ACCEPT="application/json")
    assert readiness.status_code == 200
    payload = readiness.json()
    assert payload["classification"] == "CONTROLLED_PILOT_CONTINUE"
    assert payload["production_claim_authorized"] is False
    assert payload["production_proven"] is False
    assert any("gps_loss_rate" in reason for reason in payload["blocking_reasons"])
    assert any("validated_adaptive_proposals" in reason for reason in payload["blocking_reasons"])


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
