from __future__ import annotations

from afriride_system.backend.replay_engine import ReplayEngine
from afriride_system.backend.trace_enforcement import TraceEventLog, build_trace_log, stable_hash


def _append(log: TraceEventLog, *, event_id: str, actor_type: str, actor_id: str, action: str) -> None:
    log.append(
        {
            "event_id": event_id,
            "device_id": f"device-{actor_id}",
            "actor_type": actor_type,
            "actor_id": actor_id,
            "action": action,
            "payload": {"ride_id": "ride-replay-1"},
            "local_timestamp": "2026-06-02T10:00:00Z",
            "app_version": "0.1",
            "test_mode": True,
        },
        ride_id="ride-replay-1",
    )


def test_replay_engine_reconstructs_completed_ride_from_trace(tmp_path) -> None:
    log = build_trace_log(db_path=tmp_path / "replay.sqlite3")
    _append(
        log,
        event_id="replay-request-1",
        actor_type="rider",
        actor_id="rider-1",
        action="POST /passenger/request-ride",
    )
    _append(
        log,
        event_id="replay-accept-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-replay-1/accept",
    )
    _append(
        log,
        event_id="replay-arrive-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-replay-1/arrive",
    )
    _append(
        log,
        event_id="replay-start-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-replay-1/start",
    )
    _append(
        log,
        event_id="replay-complete-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-replay-1/complete",
    )

    replay = ReplayEngine().replay("ride-replay-1", log.events_for_ride("ride-replay-1"))

    assert replay.ride_id == "ride-replay-1"
    assert replay.status == "COMPLETED"
    assert replay.assigned_driver == "driver-1"
    assert replay.passenger_id == "rider-1"
    assert replay.transitions == ("REQUESTED", "DRIVER_ACCEPTED", "ARRIVED", "STARTED", "COMPLETED")
    assert replay.replay_verified is True
    payload = replay.canonical_dict()
    assert payload["authority"]["doc_id"] == "DOC-ARCH-001"
    assert payload["authority"]["doc_version"] == "1.0.0"
    assert len(payload["authority"]["authority_hash"]) == 64
    assert payload["authority"]["surface"] == "replay_snapshot"
    assert "I6_REPLAY_AUTHORITY" in payload["authority"]["governed_invariants"]
    assert replay.replay_hash == stable_hash(
        {
            "ride_id": "ride-replay-1",
            "status": "COMPLETED",
            "assigned_driver": "driver-1",
            "passenger_id": "rider-1",
            "transitions": ["REQUESTED", "DRIVER_ACCEPTED", "ARRIVED", "STARTED", "COMPLETED"],
            "ordered": True,
            "hash_chain_verified": True,
            "invariant_violations": [],
            "terminal_event_hash": replay.terminal_event_hash,
            "authority_hash": payload["authority"]["authority_hash"],
        }
    )
    assert replay.replay_hash == stable_hash(
        {
            "ride_id": "ride-replay-1",
            "status": "COMPLETED",
            "assigned_driver": "driver-1",
            "passenger_id": "rider-1",
            "transitions": ["REQUESTED", "DRIVER_ACCEPTED", "ARRIVED", "STARTED", "COMPLETED"],
            "ordered": True,
            "hash_chain_verified": True,
            "invariant_violations": [],
            "terminal_event_hash": replay.terminal_event_hash,
            "authority_hash": payload["authority"]["authority_hash"],
        }
    )


def test_replay_engine_is_deterministic_for_same_trace(tmp_path) -> None:
    log = build_trace_log(db_path=tmp_path / "replay-determinism.sqlite3")
    _append(
        log,
        event_id="det-request-1",
        actor_type="rider",
        actor_id="rider-1",
        action="POST /passenger/request-ride",
    )
    _append(
        log,
        event_id="det-accept-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-replay-1/accept",
    )

    events = log.events_for_ride("ride-replay-1")
    engine = ReplayEngine()
    first = engine.replay("ride-replay-1", events)
    second = engine.replay("ride-replay-1", events)

    assert first == second
    assert first.replay_hash == second.replay_hash


def test_replay_engine_rejects_invalid_transition_order(tmp_path) -> None:
    log = build_trace_log(db_path=tmp_path / "replay-invalid-order.sqlite3")
    _append(
        log,
        event_id="bad-request-1",
        actor_type="rider",
        actor_id="rider-1",
        action="POST /passenger/request-ride",
    )
    _append(
        log,
        event_id="bad-complete-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-replay-1/complete",
    )

    replay = ReplayEngine().replay("ride-replay-1", log.events_for_ride("ride-replay-1"))

    assert replay.replay_verified is False
    assert "invalid_transition:REQUESTED->COMPLETED" in replay.invariant_violations


def test_replay_engine_rejects_duplicate_transitions(tmp_path) -> None:
    log = build_trace_log(db_path=tmp_path / "replay-duplicate-transition.sqlite3")
    _append(
        log,
        event_id="dup-request-1",
        actor_type="rider",
        actor_id="rider-1",
        action="POST /passenger/request-ride",
    )
    _append(
        log,
        event_id="dup-accept-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-replay-1/accept",
    )
    _append(
        log,
        event_id="dup-accept-2",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-replay-1/accept",
    )

    replay = ReplayEngine().replay("ride-replay-1", log.events_for_ride("ride-replay-1"))

    assert replay.replay_verified is False
    assert "duplicate_transition:DRIVER_ACCEPTED" in replay.invariant_violations
