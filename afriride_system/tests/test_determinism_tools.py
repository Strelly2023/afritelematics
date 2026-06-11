from __future__ import annotations

from pathlib import Path

from afriride_system.backend.determinism import (
    collect_ride_snapshot,
    compare_ride_snapshots,
    persist_derived_snapshots,
    trace_ride_ids,
)
from afriride_system.backend.storage import AfriRideStorage
from afriride_system.backend.trace_enforcement import build_trace_log


def _append(log, *, event_id: str, actor_type: str, actor_id: str, action: str, ride_id: str) -> None:
    log.append(
        {
            "event_id": event_id,
            "device_id": f"device-{actor_id}",
            "actor_type": actor_type,
            "actor_id": actor_id,
            "action": action,
            "payload": {"ride_id": ride_id},
            "local_timestamp": "2026-01-01T10:00:00Z",
            "app_version": "1.0.0",
            "test_mode": True,
        },
        ride_id,
    )


def test_collect_and_compare_ride_snapshots_are_deterministic(tmp_path: Path) -> None:
    left_path = tmp_path / "left.sqlite3"
    right_path = tmp_path / "right.sqlite3"
    left_log = build_trace_log(db_path=left_path)
    right_log = build_trace_log(db_path=right_path)

    for log in (left_log, right_log):
        _append(
            log,
            event_id="event-request-1",
            actor_type="rider",
            actor_id="rider-1",
            action="POST /passenger/request-ride",
            ride_id="ride-compare-1",
        )
        _append(
            log,
            event_id="event-accept-1",
            actor_type="driver",
            actor_id="driver-1",
            action="POST /ride/ride-compare-1/accept",
            ride_id="ride-compare-1",
        )

    left_storage = AfriRideStorage(left_path)
    right_storage = AfriRideStorage(right_path)

    assert trace_ride_ids(left_storage) == ("ride-compare-1",)
    diff = compare_ride_snapshots(
        collect_ride_snapshot(left_storage, "ride-compare-1"),
        collect_ride_snapshot(right_storage, "ride-compare-1"),
    )
    assert diff == {}


def test_persist_derived_snapshots_writes_rebuildable_projection_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "derived.sqlite3"
    log = build_trace_log(db_path=db_path)
    _append(
        log,
        event_id="derived-request-1",
        actor_type="rider",
        actor_id="rider-1",
        action="POST /passenger/request-ride",
        ride_id="ride-derived-1",
    )
    _append(
        log,
        event_id="derived-accept-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-derived-1/accept",
        ride_id="ride-derived-1",
    )
    _append(
        log,
        event_id="derived-arrive-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-derived-1/arrive",
        ride_id="ride-derived-1",
    )
    _append(
        log,
        event_id="derived-start-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-derived-1/start",
        ride_id="ride-derived-1",
    )
    _append(
        log,
        event_id="derived-complete-1",
        actor_type="driver",
        actor_id="driver-1",
        action="POST /ride/ride-derived-1/complete",
        ride_id="ride-derived-1",
    )

    storage = AfriRideStorage(db_path)
    snapshot = collect_ride_snapshot(storage, "ride-derived-1")
    persist_derived_snapshots(storage, snapshot)

    with storage.connect() as connection:
        replay_row = connection.execute(
            "SELECT ride_id, trace_hash, replay_hash FROM replay_snapshots WHERE ride_id = ?",
            ("ride-derived-1",),
        ).fetchone()
        evidence_row = connection.execute(
            "SELECT ride_id, verification_status FROM evidence_records WHERE ride_id = ?",
            ("ride-derived-1",),
        ).fetchone()
        receipt_row = connection.execute(
            "SELECT ride_id, receipt_hash FROM receipt_records WHERE ride_id = ?",
            ("ride-derived-1",),
        ).fetchone()

    assert replay_row is not None
    assert replay_row["trace_hash"] == snapshot.replay.trace_hash
    assert replay_row["replay_hash"] == snapshot.replay.replay_hash
    assert evidence_row == {
        "ride_id": "ride-derived-1",
        "verification_status": "VERIFIED",
    }
    assert receipt_row is not None
    assert receipt_row["receipt_hash"] == snapshot.receipt.receipt_hash
