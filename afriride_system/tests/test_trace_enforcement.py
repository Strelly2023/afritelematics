from __future__ import annotations

from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app
from afriride_system.backend.trace_enforcement import (
    TRACE_LOG,
    build_trace_log,
    compute_trace_event_hash,
    reset_trace_log,
)
from afriride_system.backend.repositories.trace_repository import TraceRepository
from afriride_system.backend.storage import AfriRideStorage


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
        "Authorization": f"Bearer {JWT.create_token('operator-1', 'OPERATOR')}",
        "X-AfriRide-Device-Id": "operator-device",
        "X-AfriRide-App-Version": "0.1",
        "X-AfriRide-Event-Id": event_id,
        "X-AfriRide-Client-Timestamp": "2026-06-02T10:00:00Z",
        "X-AfriRide-Test-Mode": "true",
    }


def rider_headers(event_id: str, rider_id: str = "rider-1") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {JWT.create_token(rider_id, 'RIDER')}",
        "Idempotency-Key": event_id,
    }


def driver_headers(event_id: str, driver_id: str = "driver-1") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {JWT.create_token(driver_id, 'DRIVER')}",
        "Idempotency-Key": event_id,
    }


def setup_function() -> None:
    reset_gateway()
    reset_trace_log()


def test_instrumented_request_without_envelope_is_rejected() -> None:
    client = TestClient(app)

    response = client.post(
        "/ride/ride-missing-envelope/accept",
        json={"driver_id": "driver-1"},
        headers={
            "Authorization": f"Bearer {JWT.create_token('driver-1', 'DRIVER')}",
            "X-AfriRide-Device-Id": "driver-device",
            "X-AfriRide-App-Version": "0.1",
            "X-AfriRide-Event-Id": "missing-envelope",
            "X-AfriRide-Client-Timestamp": "2026-06-02T10:00:00Z",
            "X-AfriRide-Test-Mode": "true",
        },
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
                "local_timestamp": "not-a-timestamp",
                "app_version": "0.1",
            },
        },
        headers={"Authorization": f"Bearer {JWT.create_token('driver-1', 'DRIVER')}"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_TRACE_ENVELOPE"
    assert TRACE_LOG.all_events() == ()


def test_complete_instrumented_lifecycle_is_ordered_hashable_and_replay_verified() -> None:
    client = TestClient(app)

    client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers=driver_headers("trace-driver-online"),
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
        headers=rider_headers("trace-request"),
    )
    assert request.status_code == 200

    for event_id, action in (
        ("trace-accept-1", "accept"),
        ("trace-arrive-1", "arrive"),
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
                headers=driver_headers(f"trace-{action}"),
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
    assert trace_payload["hash_chain_verified"] is True
    assert trace_payload["invariant_violations"] == []
    assert len(trace_payload["trace_hash"]) == 64
    assert len(trace_payload["replay_hash"]) == 64

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


def test_identical_trace_event_payload_with_different_authority_hash_changes_event_hash() -> None:
    base = {
        "event_id": "authority-event-1",
        "sequence_id": 1,
        "device_id": "device-driver-1",
        "actor_type": "driver",
        "actor_id": "driver-1",
        "action": "POST /ride/ride-authority-1/accept",
        "payload": {"driver_id": "driver-1"},
        "local_timestamp": "2026-06-02T10:00:00Z",
        "normalized_timestamp": "2026-06-02T10:00:00Z",
        "app_version": "0.1",
        "test_mode": True,
        "ride_id": "ride-authority-1",
        "transition": "DRIVER_ACCEPTED",
        "previous_hash": None,
    }
    left = compute_trace_event_hash(**base, authority_hash="a" * 64)
    right = compute_trace_event_hash(**base, authority_hash="b" * 64)
    assert left != right


def test_mixed_authority_trace_is_invalid(tmp_path) -> None:
    db_path = tmp_path / "mixed-authority.sqlite3"
    storage = AfriRideStorage(db_path)
    repository = TraceRepository(storage)
    first_hash = compute_trace_event_hash(
        event_id="mixed-request-1",
        sequence_id=1,
        device_id="device-rider-1",
        actor_type="rider",
        actor_id="rider-1",
        action="POST /passenger/request-ride",
        payload={"ride_id": "ride-mixed"},
        local_timestamp="2026-06-02T10:00:00Z",
        normalized_timestamp="2026-06-02T10:00:00Z",
        app_version="0.1",
        test_mode=True,
        ride_id="ride-mixed",
        transition="REQUESTED",
        previous_hash=None,
        authority_hash="a" * 64,
    )
    repository.save(
        {
            "event_id": "mixed-request-1",
            "sequence_id": 1,
            "device_id": "device-rider-1",
            "actor_type": "rider",
            "actor_id": "rider-1",
            "action": "POST /passenger/request-ride",
            "payload": {"ride_id": "ride-mixed"},
            "local_timestamp": "2026-06-02T10:00:00Z",
            "normalized_timestamp": "2026-06-02T10:00:00Z",
            "app_version": "0.1",
            "test_mode": True,
            "ride_id": "ride-mixed",
            "transition": "REQUESTED",
            "previous_hash": None,
            "authority_hash": "a" * 64,
            "event_hash": first_hash,
        }
    )
    second_hash = compute_trace_event_hash(
        event_id="mixed-accept-1",
        sequence_id=2,
        device_id="device-driver-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-mixed/accept",
        payload={"driver_id": "driver-1"},
        local_timestamp="2026-06-02T10:01:00Z",
        normalized_timestamp="2026-06-02T10:01:00Z",
        app_version="0.1",
        test_mode=True,
        ride_id="ride-mixed",
        transition="DRIVER_ACCEPTED",
        previous_hash=first_hash,
        authority_hash="b" * 64,
    )
    repository.save(
        {
            "event_id": "mixed-accept-1",
            "sequence_id": 2,
            "device_id": "device-driver-1",
            "actor_type": "driver",
            "actor_id": "driver-1",
            "action": "POST /ride/ride-mixed/accept",
            "payload": {"driver_id": "driver-1"},
            "local_timestamp": "2026-06-02T10:01:00Z",
            "normalized_timestamp": "2026-06-02T10:01:00Z",
            "app_version": "0.1",
            "test_mode": True,
            "ride_id": "ride-mixed",
            "transition": "DRIVER_ACCEPTED",
            "previous_hash": first_hash,
            "authority_hash": "b" * 64,
            "event_hash": second_hash,
        }
    )
    log = build_trace_log(db_path=db_path)
    result = log.validate_ride("ride-mixed")
    assert result.valid is False
    assert "authority_hash_mismatch" in result.invariant_violations


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
    assert "ARRIVED" in trace.json()["missing_transitions"]

    guards = client.get("/system/guards", headers=headers("operator-guards"))
    assert guards.status_code == 200
    assert guards.json()["violations"][0]["type"] == "TRACE_COMPLETENESS"


def test_trace_events_survive_log_rebuild(tmp_path) -> None:
    trace_log = build_trace_log(db_path=tmp_path / "trace.sqlite3")
    event = trace_log.append(
        envelope(
            "persisted-trace-1",
            actor_type="rider",
            actor_id="rider-1",
            action="POST /passenger/request-ride",
            payload={"ride_id": "ride-trace-persist"},
        ),
        ride_id="ride-trace-persist",
    )

    rebuilt_log = build_trace_log(db_path=tmp_path / "trace.sqlite3")
    events = rebuilt_log.events_for_ride("ride-trace-persist")

    assert len(events) == 1
    assert events[0] == event
    assert rebuilt_log.validate_ride("ride-trace-persist").ride_id == "ride-trace-persist"


def test_tampered_trace_hash_is_detected_and_reported() -> None:
    TRACE_LOG.append(
        envelope(
            "tampered-request-1",
            actor_type="rider",
            actor_id="rider-1",
            action="POST /passenger/request-ride",
            payload={"ride_id": "ride-tampered"},
        ),
        ride_id="ride-tampered",
    )

    with TRACE_LOG.repository.storage.connect() as connection:
        connection.execute(
            "UPDATE trace_events SET event_hash = ? WHERE event_id = ?",
            ("0" * 64, "tampered-request-1"),
        )

    client = TestClient(app)
    trace = client.get("/system/traces/ride-tampered", headers=headers("operator-tampered"))
    replay = client.get("/system/replay/health", headers=headers("operator-tampered-replay"))
    guards = client.get("/system/guards", headers=headers("operator-tampered-guards"))

    assert trace.status_code == 200
    trace_payload = trace.json()
    assert trace_payload["valid"] is False
    assert trace_payload["hash_chain_verified"] is False
    assert any(
        violation.startswith("event_hash_mismatch:")
        for violation in trace_payload["invariant_violations"]
    )

    assert replay.status_code == 200
    assert replay.json()["hash_chain_failures"] >= 1
    assert replay.json()["status"] == "FAIL"

    assert guards.status_code == 200
    assert any(
        violation["type"] == "TRACE_HASH_CHAIN_BREAK"
        for violation in guards.json()["violations"]
    )


def test_authenticated_identity_overrides_client_declared_trace_identity() -> None:
    client = TestClient(app)

    client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers=driver_headers("identity-driver-online"),
    )
    response = client.post(
        "/passenger/request-ride",
        json={
            "passenger_id": "rider-1",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": "ride-identity-1",
            "client_event": envelope(
                "identity-request-1",
                actor_type="driver",
                actor_id="forged-driver",
                action="POST /passenger/request-ride",
                payload={"ride_id": "ride-identity-1"},
            ),
        },
        headers=rider_headers("identity-request", rider_id="rider-authenticated"),
    )

    assert response.status_code == 200
    event = TRACE_LOG.events_for_ride("ride-identity-1")[0]
    assert event.actor_id == "rider-authenticated"
    assert event.actor_type == "rider"
