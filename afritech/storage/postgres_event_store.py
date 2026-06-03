"""PostgreSQL-shaped append-only event store with replay-safe semantics."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


AUTHORITY_DISCLAIMER = (
    "Persistent storage may preserve events. It does not define truth; "
    "canonical event hashes and replay validation remain authority."
)


class PersistentEventStoreError(ValueError):
    """Raised when persistent event storage violates replay safety."""


@dataclass(frozen=True)
class PersistentEventRecord:
    event_id: str
    sequence: int
    event: Mapping[str, Any]
    canonical_event_hash: str
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    def __post_init__(self) -> None:
        _require_identity(self.event_id, "event_id")
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise PersistentEventStoreError("sequence must be non-negative int")
        if not isinstance(self.event, Mapping):
            raise PersistentEventStoreError("event must be mapping")
        if self.authority_disclaimer != AUTHORITY_DISCLAIMER:
            raise PersistentEventStoreError("persistent storage authority disclaimer mismatch")
        if self.canonical_event_hash != canonical_event_hash(self.event):
            raise PersistentEventStoreError("canonical event hash mismatch")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "canonical_event_hash": self.canonical_event_hash,
            "event": dict(self.event),
            "event_id": self.event_id,
            "sequence": self.sequence,
        }

    def record_hash(self) -> str:
        return _canonical_hash(self.to_canonical_dict())


@dataclass(frozen=True)
class PersistentEventSnapshot:
    records: tuple[PersistentEventRecord, ...]

    def canonical_records(self) -> tuple[PersistentEventRecord, ...]:
        return tuple(sorted(self.records, key=lambda record: record.sequence))

    def to_canonical_list(self) -> list[dict[str, object]]:
        return [record.to_canonical_dict() for record in self.canonical_records()]

    def snapshot_hash(self) -> str:
        return _canonical_hash(self.to_canonical_list())

    def replay_hash(self) -> str:
        return _canonical_hash(
            [
                {
                    "canonical_event_hash": record.canonical_event_hash,
                    "event_id": record.event_id,
                    "sequence": record.sequence,
                }
                for record in self.canonical_records()
            ]
        )


class InMemoryPostgresEventBackend:
    """Deterministic backend standing in for PostgreSQL rows in CI."""

    def __init__(self, rows: Iterable[Mapping[str, object]] | None = None) -> None:
        self._rows = [dict(row) for row in rows or ()]

    def append(self, row: Mapping[str, object]) -> None:
        self._rows.append(dict(row))

    def rows(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(row) for row in self._rows)

    def update_for_test(self, index: int, row: Mapping[str, object]) -> None:
        self._rows[index] = dict(row)

    def delete_for_test(self, index: int) -> None:
        del self._rows[index]


class PostgresEventStore:
    """Append-only persistent event store. Backend delivery is non-authoritative."""

    def __init__(self, backend: InMemoryPostgresEventBackend | None = None) -> None:
        self._backend = backend or InMemoryPostgresEventBackend()
        self._validate_rows(self._backend.rows())

    @property
    def backend(self) -> InMemoryPostgresEventBackend:
        return self._backend

    def append(self, event: Mapping[str, Any]) -> PersistentEventRecord:
        event_id = _require_identity(event.get("event_id"), "event_id")
        sequence = len(self._backend.rows())
        record = PersistentEventRecord(
            event_id=event_id,
            sequence=sequence,
            event=dict(event),
            canonical_event_hash=canonical_event_hash(event),
        )
        self._backend.append(record.to_canonical_dict())
        return record

    def append_many(self, events: Iterable[Mapping[str, Any]]) -> tuple[PersistentEventRecord, ...]:
        if events is None:
            raise PersistentEventStoreError("events required")
        return tuple(self.append(event) for event in events)

    def snapshot(self) -> PersistentEventSnapshot:
        return PersistentEventSnapshot(
            tuple(_record_from_row(row) for row in self._backend.rows())
        )

    def replay_hash(self) -> str:
        return self.snapshot().replay_hash()

    def row_count(self) -> int:
        return len(self._backend.rows())

    def update_event(self, *_args, **_kwargs) -> None:
        raise PersistentEventStoreError("persistent event store is append-only")

    def delete_event(self, *_args, **_kwargs) -> None:
        raise PersistentEventStoreError("persistent event store is append-only")

    def _validate_rows(self, rows: Iterable[Mapping[str, object]]) -> None:
        records = tuple(_record_from_row(row) for row in rows)
        sequences = [record.sequence for record in records]
        if sequences != list(range(len(sequences))):
            raise PersistentEventStoreError("persistent event sequence mismatch")
        if len({record.event_id for record in records}) != len(records):
            raise PersistentEventStoreError("duplicate persistent event id")


def restore_event_store(rows: Iterable[Mapping[str, object]]) -> PostgresEventStore:
    return PostgresEventStore(InMemoryPostgresEventBackend(rows))


def canonical_event_hash(event: Mapping[str, Any]) -> str:
    if not isinstance(event, Mapping):
        raise PersistentEventStoreError("event must be mapping")
    return _canonical_hash(dict(event))


def _record_from_row(row: Mapping[str, object]) -> PersistentEventRecord:
    if not isinstance(row, Mapping):
        raise PersistentEventStoreError("persistent row must be mapping")
    if row.get("authority_disclaimer") != AUTHORITY_DISCLAIMER:
        raise PersistentEventStoreError("persistent row authority disclaimer mismatch")
    event = row.get("event")
    if not isinstance(event, Mapping):
        raise PersistentEventStoreError("persistent row event must be mapping")
    return PersistentEventRecord(
        event_id=_require_identity(row.get("event_id"), "event_id"),
        sequence=_require_int(row.get("sequence"), "sequence"),
        event=dict(event),
        canonical_event_hash=_require_hash(
            row.get("canonical_event_hash"),
            "canonical_event_hash",
        ),
        authority_disclaimer=_require_identity(
            row.get("authority_disclaimer"),
            "authority_disclaimer",
        ),
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


def _require_identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PersistentEventStoreError(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise PersistentEventStoreError(f"{field} contains forbidden path syntax")
    return value


def _require_int(value: object, field: str) -> int:
    if not isinstance(value, int):
        raise PersistentEventStoreError(f"{field} must be int")
    return value


def _require_hash(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise PersistentEventStoreError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise PersistentEventStoreError(f"{field} must be sha256") from exc
    return value
