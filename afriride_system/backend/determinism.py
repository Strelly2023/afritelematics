"""Determinism helpers for migration verification and replay audits."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from afriride_system.backend.evidence_engine import EvidenceEngine, EvidenceRecord
from afriride_system.backend.receipt_engine import ReceiptEngine, ReceiptRecord
from afriride_system.backend.replay_engine import ReplayEngine, ReplaySnapshot
from afriride_system.backend.repositories.trace_repository import TraceRepository
from afriride_system.backend.storage import AfriRideStorage
from afriride_system.backend.trace_enforcement import TraceEvent, trace_event_from_payload


@dataclass(frozen=True)
class RideDeterminismSnapshot:
    ride_id: str
    trace_event_count: int
    replay: ReplaySnapshot
    evidence: EvidenceRecord
    receipt: ReceiptRecord

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "ride_id": self.ride_id,
            "trace_event_count": self.trace_event_count,
            "replay": self.replay.canonical_dict(),
            "evidence": self.evidence.canonical_dict(),
            "receipt": self.receipt.canonical_dict(),
        }


def trace_ride_ids(storage: AfriRideStorage) -> tuple[str, ...]:
    with storage.connect() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT ride_id
            FROM trace_events
            WHERE ride_id IS NOT NULL
            ORDER BY ride_id
            """
        ).fetchall()
    return tuple(str(row["ride_id"]) for row in rows)


def collect_ride_snapshot(storage: AfriRideStorage, ride_id: str) -> RideDeterminismSnapshot:
    events = _trace_events_for_ride(storage, ride_id)
    replay = ReplayEngine().replay(ride_id, events)
    evidence = EvidenceEngine().derive(ride_id, events)
    receipt = ReceiptEngine().derive(ride_id, events)
    return RideDeterminismSnapshot(
        ride_id=ride_id,
        trace_event_count=len(events),
        replay=replay,
        evidence=evidence,
        receipt=receipt,
    )


def compare_ride_snapshots(
    source: RideDeterminismSnapshot,
    target: RideDeterminismSnapshot,
) -> dict[str, tuple[Any, Any]]:
    mismatches: dict[str, tuple[Any, Any]] = {}
    if source.trace_event_count != target.trace_event_count:
        mismatches["trace_event_count"] = (source.trace_event_count, target.trace_event_count)
    if source.replay.canonical_dict() != target.replay.canonical_dict():
        mismatches["replay"] = (source.replay.canonical_dict(), target.replay.canonical_dict())
    if source.evidence.canonical_dict() != target.evidence.canonical_dict():
        mismatches["evidence"] = (
            source.evidence.canonical_dict(),
            target.evidence.canonical_dict(),
        )
    if source.receipt.canonical_dict() != target.receipt.canonical_dict():
        mismatches["receipt"] = (source.receipt.canonical_dict(), target.receipt.canonical_dict())
    return mismatches


def persist_derived_snapshots(storage: AfriRideStorage, snapshot: RideDeterminismSnapshot) -> None:
    with storage.connect() as connection:
        connection.execute(
            """
            INSERT INTO replay_snapshots (
                ride_id,
                status,
                assigned_driver,
                passenger_id,
                transitions_json,
                trace_hash,
                replay_hash,
                authority_hash,
                replay_verified,
                generated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ride_id) DO UPDATE SET
                status = excluded.status,
                assigned_driver = excluded.assigned_driver,
                passenger_id = excluded.passenger_id,
                transitions_json = excluded.transitions_json,
                trace_hash = excluded.trace_hash,
                replay_hash = excluded.replay_hash,
                authority_hash = excluded.authority_hash,
                replay_verified = excluded.replay_verified,
                generated_at = excluded.generated_at
            """,
            (
                snapshot.ride_id,
                snapshot.replay.status,
                snapshot.replay.assigned_driver,
                snapshot.replay.passenger_id,
                json.dumps(list(snapshot.replay.transitions), sort_keys=True, separators=(",", ":")),
                snapshot.replay.trace_hash,
                snapshot.replay.replay_hash,
                snapshot.replay.canonical_dict()["authority"]["authority_hash"],
                int(snapshot.replay.replay_verified),
                snapshot.evidence.generated_at,
            ),
        )
        connection.execute(
            """
            INSERT INTO evidence_records (
                ride_id,
                trace_hash,
                replay_hash,
                authority_hash,
                verification_status,
                receipt_id,
                generated_at,
                replay_snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ride_id) DO UPDATE SET
                trace_hash = excluded.trace_hash,
                replay_hash = excluded.replay_hash,
                authority_hash = excluded.authority_hash,
                verification_status = excluded.verification_status,
                receipt_id = excluded.receipt_id,
                generated_at = excluded.generated_at,
                replay_snapshot_json = excluded.replay_snapshot_json
            """,
            (
                snapshot.ride_id,
                snapshot.evidence.trace_hash,
                snapshot.evidence.replay_hash,
                snapshot.evidence.canonical_dict()["authority"]["authority_hash"],
                snapshot.evidence.verification_status,
                snapshot.evidence.receipt_id,
                snapshot.evidence.generated_at,
                json.dumps(
                    snapshot.replay.canonical_dict(),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )
        connection.execute(
            """
            INSERT INTO receipt_records (
                receipt_id,
                ride_id,
                replay_id,
                status,
                trace_hash,
                replay_hash,
                authority_hash,
                execution_fingerprint,
                receipt_hash,
                issued_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(receipt_id) DO UPDATE SET
                ride_id = excluded.ride_id,
                replay_id = excluded.replay_id,
                status = excluded.status,
                trace_hash = excluded.trace_hash,
                replay_hash = excluded.replay_hash,
                authority_hash = excluded.authority_hash,
                execution_fingerprint = excluded.execution_fingerprint,
                receipt_hash = excluded.receipt_hash,
                issued_at = excluded.issued_at
            """,
            (
                snapshot.receipt.receipt_id,
                snapshot.ride_id,
                snapshot.receipt.replay_id,
                snapshot.receipt.status,
                snapshot.receipt.trace_hash,
                snapshot.receipt.replay_hash,
                snapshot.receipt.canonical_dict()["authority"]["authority_hash"],
                snapshot.receipt.execution_fingerprint,
                snapshot.receipt.receipt_hash,
                snapshot.receipt.issued_at,
            ),
        )


def _trace_events_for_ride(storage: AfriRideStorage, ride_id: str) -> tuple[TraceEvent, ...]:
    repository = TraceRepository(storage)
    return tuple(trace_event_from_payload(row) for row in repository.events_for_ride(ride_id))
