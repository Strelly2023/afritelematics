from __future__ import annotations

import pytest

from afritech.ci.persistent_storage_validator import run_persistent_storage_proof
from afritech.storage.postgres_event_store import (
    AUTHORITY_DISCLAIMER,
    PersistentEventStoreError,
    PostgresEventStore,
    restore_event_store,
)


def _event(event_id: str = "persistent.test.001") -> dict[str, object]:
    return {
        "event_id": event_id,
        "payload": {"value": 42},
        "timestamp": "2026-05-26T00:00:00Z",
        "type": "test.event",
    }


def test_persistent_event_store_preserves_canonical_event_hash_after_restore():
    store = PostgresEventStore()
    record = store.append(_event())
    restored = restore_event_store(store.backend.rows())

    assert restored.snapshot().records[0].canonical_event_hash == record.canonical_event_hash
    assert restored.replay_hash() == store.replay_hash()


def test_persistent_event_store_rejects_update_and_delete_mutation():
    store = PostgresEventStore()
    store.append(_event())

    with pytest.raises(PersistentEventStoreError, match="append-only"):
        store.update_event("persistent.test.001", {"bad": True})

    with pytest.raises(PersistentEventStoreError, match="append-only"):
        store.delete_event("persistent.test.001")


def test_persistent_event_store_rejects_tampered_snapshot_row():
    store = PostgresEventStore()
    store.append(_event())
    row = dict(store.backend.rows()[0])
    row["event"] = dict(row["event"])
    row["event"]["payload"] = {"value": 99}

    with pytest.raises(PersistentEventStoreError, match="canonical event hash mismatch"):
        restore_event_store((row,))


def test_persistent_event_store_rows_include_non_authoritative_disclaimer():
    store = PostgresEventStore()
    store.append(_event())

    row = store.backend.rows()[0]

    assert row["authority_disclaimer"] == AUTHORITY_DISCLAIMER
    assert "replay validation remain authority" in row["authority_disclaimer"]


def test_persistent_storage_validator_report_is_verified():
    report = run_persistent_storage_proof()

    assert report.verified is True
    assert report.append_only_enforced is True
    assert report.canonical_event_hash_preserved is True
    assert report.replay_hash == report.restored_replay_hash
    assert report.snapshot_hash == report.restored_snapshot_hash
    assert report.mutation_rejected is True
    assert len(report.report_hash()) == 64
