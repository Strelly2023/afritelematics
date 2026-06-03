from __future__ import annotations

from fastapi.testclient import TestClient

from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app
from afriride_system.backend.trace_enforcement import TRACE_LOG, reset_trace_log


def envelope(
    event_id: str,
    *,
    actor_type: str = "driver",
    actor_id: str = "driver-1",
    action: str,
    payload: dict,
) -> dict:
    return {
        "event_id": event_id,
        "device_id": f"device-{actor_id}",
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "payload": payload,
        "local_timestamp": "2026-06-02T10:00:00Z",
        "app_version": "0.1",
        "test_mode": True,
    }


def headers(event_id: str = "operator-event-1") -> dict[str, str]:
    return {
        "X-AfriRide-Device-Id": "operator-device",
        "X-AfriRide-App-Version": "0.1",
        "X-AfriRide-Event-Id": event_id,
        "X-AfriRide-Client-Timestamp": "2026-06-02T10:00:00Z",
        "X-AfriRide-Test-Mode": "true",
    }


def setup_function() -> None:
    reset_gateway()
    reset_trace_log()


def test_instrumented_request_without_envelope_is_rejected() -> None:
    client = TestClient(app)

    response = client.post(
        "/ride/ride-missing-envelope/accept",
        json={"driver_id": "driver-1"},
        headers=headers("missing-envelope"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MISSING_TRACE_ENVELOPE"
    assert TRACE_LOG.all_events() == ()


def test_invalid_trace_envelope_is_rejected_before_execution() -> None:
    client = TestClient(app)

    response = client.post(
        "/ride/ride-bad-envelope/accept",
        json={
            "driver_id": "driver-1",
            "client_event": {
                "event_id": "bad-event",
                "device_id": "device-driver",
                "actor_type": "invalid",
                "actor_id": "driver-1",
                "action": "POST /ride/ride-bad-envelope/accept",
                "payload": {"driver_id": "driver-1"},
                "local_timestamp": "2026-06-02T10:00:00Z",
                "app_version": "0.1",
            },
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_TRACE_ENVELOPE"
    assert TRACE_LOG.all_events() == ()


def test_complete_instrumented_lifecycle_is_ordered_hashable_and_replay_verified() -> None:
    client = TestClient(app)

    client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers={"Idempotency-Key": "trace-driver-online"},
    )
    request = client.post(
        "/passenger/request-ride",
        json={
            "passenger_id": "rider-1",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": "ride-trace-1",
            "client_event": envelope(
                "trace-request-1",
                actor_type="rider",
                actor_id="rider-1",
                action="POST /passenger/request-ride",
                payload={"ride_id": "ride-trace-1"},
            ),
        },
        headers={"Idempotency-Key": "trace-request"},
    )
    assert request.status_code == 200

    for event_id, action in (
        ("trace-accept-1", "accept"),
        ("trace-start-1", "start"),
        ("trace-complete-1", "complete"),
    ):
        response = client.post(
            f"/ride/ride-trace-1/{action}",
            json={
                "driver_id": "driver-1",
                "client_event": envelope(
                    event_id,
                    action=f"POST /ride/ride-trace-1/{action}",
                    payload={"driver_id": "driver-1"},
                ),
            },
            headers={"Idempotency-Key": f"trace-{action}"},
        )
        assert response.status_code == 200
        assert response.headers["X-AfriRide-Trace-Sequence"]
        assert len(response.headers["X-AfriRide-Trace-Hash"]) == 64

    trace = client.get("/system/traces/ride-trace-1", headers=headers("operator-trace-read"))
    assert trace.status_code == 200
    trace_payload = trace.json()
    assert trace_payload["valid"] is True
    assert trace_payload["ordered"] is True
    assert trace_payload["complete"] is True
    assert trace_payload["replay_verified"] is True
    assert trace_payload["trace_hash"] == trace_payload["replay_hash"]

    evidence = client.get("/system/evidence", headers=headers("operator-evidence-read"))
    assert evidence.status_code == 200
    assert evidence.json()["valid_traces"] == 1
    assert evidence.json()["missing_traces"] == 0

    replay = client.get("/system/replay/health", headers=headers("operator-replay-read"))
    assert replay.status_code == 200
    assert replay.json()["replay_success_rate"] == "100%"
    assert replay.json()["status"] == "PASS"


def test_duplicate_event_id_is_idempotent_not_duplicated() -> None:
    event = envelope(
        "duplicate-event-1",
        action="POST /ride/ride-dup/accept",
        payload={"driver_id": "driver-1"},
    )

    first = TRACE_LOG.append(event, ride_id="ride-dup")
    second = TRACE_LOG.append(event, ride_id="ride-dup")

    assert first == second
    assert len(TRACE_LOG.all_events()) == 1


def test_missing_lifecycle_transition_marks_trace_invalid_and_guard_visible() -> None:
    client = TestClient(app)
    TRACE_LOG.append(
        envelope(
            "incomplete-request",
            actor_type="rider",
            actor_id="rider-1",
            action="POST /passenger/request-ride",
            payload={"ride_id": "ride-incomplete"},
        ),
        ride_id="ride-incomplete",
    )

    trace = client.get("/system/traces/ride-incomplete", headers=headers("operator-incomplete"))
    assert trace.status_code == 200
    assert trace.json()["valid"] is False
    assert "DRIVER_ACCEPTED" in trace.json()["missing_transitions"]

    guards = client.get("/system/guards", headers=headers("operator-guards"))
    assert guards.status_code == 200
    assert guards.json()["violations"][0]["type"] == "TRACE_COMPLETENESS"
