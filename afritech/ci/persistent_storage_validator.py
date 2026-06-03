"""Validate persistent event store proof for production readiness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.storage.postgres_event_store import (
    AUTHORITY_DISCLAIMER,
    PersistentEventStoreError,
    PostgresEventStore,
    restore_event_store,
)


class PersistentStorageValidationError(RuntimeError):
    """Raised when persistent storage proof fails."""


@dataclass(frozen=True)
class PersistentStorageProofReport:
    append_only_enforced: bool
    canonical_event_hash_preserved: bool
    replay_hash: str
    restored_replay_hash: str
    snapshot_hash: str
    restored_snapshot_hash: str
    mutation_rejected: bool
    record_count: int
    authority_disclaimer: str

    @property
    def verified(self) -> bool:
        return (
            self.append_only_enforced
            and self.canonical_event_hash_preserved
            and self.replay_hash == self.restored_replay_hash
            and self.snapshot_hash == self.restored_snapshot_hash
            and self.mutation_rejected
            and self.record_count > 0
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "append_only_enforced": self.append_only_enforced,
            "authority_disclaimer": self.authority_disclaimer,
            "canonical_event_hash_preserved": self.canonical_event_hash_preserved,
            "mutation_rejected": self.mutation_rejected,
            "record_count": self.record_count,
            "replay_hash": self.replay_hash,
            "restored_replay_hash": self.restored_replay_hash,
            "restored_snapshot_hash": self.restored_snapshot_hash,
            "schema": "afritech.persistent_storage_proof_report.v1",
            "snapshot_hash": self.snapshot_hash,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> PersistentStorageProofReport:
    report = run_persistent_storage_proof()
    if not report.verified:
        raise PersistentStorageValidationError("persistent storage proof failed")
    return report


def run_persistent_storage_proof() -> PersistentStorageProofReport:
    store = PostgresEventStore()
    records = store.append_many(_events())
    rows = store.backend.rows()
    restored = restore_event_store(rows)

    return PersistentStorageProofReport(
        append_only_enforced=_append_only_enforced(store),
        authority_disclaimer=AUTHORITY_DISCLAIMER,
        canonical_event_hash_preserved=all(
            record.canonical_event_hash == row["canonical_event_hash"]
            for record, row in zip(records, rows)
        ),
        mutation_rejected=_mutation_rejected(rows),
        record_count=store.row_count(),
        replay_hash=store.replay_hash(),
        restored_replay_hash=restored.replay_hash(),
        restored_snapshot_hash=restored.snapshot().snapshot_hash(),
        snapshot_hash=store.snapshot().snapshot_hash(),
    )


def _append_only_enforced(store: PostgresEventStore) -> bool:
    try:
        store.update_event("event.001", {"bad": True})
    except PersistentEventStoreError:
        update_rejected = True
    else:
        update_rejected = False

    try:
        store.delete_event("event.001")
    except PersistentEventStoreError:
        delete_rejected = True
    else:
        delete_rejected = False

    return update_rejected and delete_rejected


def _mutation_rejected(rows) -> bool:
    mutated = [dict(row) for row in rows]
    mutated[0] = dict(mutated[0])
    mutated[0]["event"] = dict(mutated[0]["event"])
    mutated[0]["event"]["payload"] = {"tampered": True}
    try:
        restore_event_store(mutated)
    except PersistentEventStoreError:
        return True
    return False


def _events() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "event_id": f"persistent.event.{index:03d}",
            "payload": {
                "amount": index * 17,
                "rider_id": f"rider.{index:03d}",
            },
            "timestamp": f"2026-05-26T00:{index:02d}:00Z",
            "type": "ride.event",
        }
        for index in range(8)
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = validate()
    except PersistentStorageValidationError as exc:
        print(f"Persistent storage validation FAILED: {exc}")
        return 1
    print(
        "Persistent storage validation PASSED: "
        f"replay_hash={report.replay_hash} report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
