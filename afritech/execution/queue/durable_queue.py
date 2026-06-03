"""Non-authoritative durable queue adapter for replay-safe delivery."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.distributed.queue.distributed_queue_adapter import (
    DistributedQueueError,
    DistributedQueueRecord,
    QueueSnapshot,
    canonical_queue_hash,
)


AUTHORITY_DISCLAIMER = (
    "Durable queue storage may deliver work. It does not define truth; "
    "the replay log remains authority."
)


class DurableQueueError(ValueError):
    """Raised when durable queue evidence violates replay safety."""


@dataclass(frozen=True)
class DurableQueueStorageRecord:
    record: DistributedQueueRecord
    record_hash: str
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    def __post_init__(self) -> None:
        if self.authority_disclaimer != AUTHORITY_DISCLAIMER:
            raise DurableQueueError("durable queue authority disclaimer mismatch")
        if self.record_hash != self.record.record_hash():
            raise DurableQueueError("durable queue record hash mismatch")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "record": self.record.to_canonical_dict(),
            "record_hash": self.record_hash,
        }

    def storage_hash(self) -> str:
        return _canonical_hash(self.to_canonical_dict())


class InMemoryDurableQueueBackend:
    """Deterministic backend standing in for Redis/Postgres delivery storage."""

    def __init__(self, rows: Iterable[Mapping[str, object]] | None = None) -> None:
        self._rows = [dict(row) for row in rows or ()]

    def append(self, row: Mapping[str, object]) -> None:
        self._rows.append(dict(row))

    def replace_rows_for_test(self, rows: Iterable[Mapping[str, object]]) -> None:
        self._rows = [dict(row) for row in rows]

    def rows(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(row) for row in self._rows)


class DurableQueueAdapter:
    """Durable delivery adapter whose stored rows never become truth authority."""

    def __init__(self, *, registry, backend: InMemoryDurableQueueBackend | None = None):
        if registry is None or not hasattr(registry, "partition_ids"):
            raise DurableQueueError("registry required")
        self._registry = registry
        self._backend = backend or InMemoryDurableQueueBackend()

    @property
    def backend(self) -> InMemoryDurableQueueBackend:
        return self._backend

    def publish(self, record: DistributedQueueRecord) -> DistributedQueueRecord:
        self._validate_record(record)
        row = _storage_record(record).to_canonical_dict()
        key = (record.partition_id, record.sequence, record.event_id)
        if key in _row_keys(self._backend.rows()):
            raise DurableQueueError("duplicate durable queue record")
        self._backend.append(row)
        return record

    def publish_many(self, records: Iterable[DistributedQueueRecord]):
        if records is None:
            raise DurableQueueError("records required")
        return tuple(self.publish(record) for record in records)

    def peek_partition(self, partition_id: str, limit: int | None = None):
        self._registry.require_declared(partition_id)
        records = [
            _record_from_row(row)
            for row in self._backend.rows()
            if _row_record(row).get("partition_id") == partition_id
        ]
        records = _canonical_records(records)
        return tuple(records if limit is None else records[:limit])

    def consume_partition(self, partition_id: str, limit: int | None = None):
        # Durable consumption is modeled as delivery, not deletion authority.
        return self.peek_partition(partition_id, limit)

    def snapshot(self) -> QueueSnapshot:
        return QueueSnapshot(_canonical_records(_record_from_row(row) for row in self._backend.rows()))

    def queue_size(self, partition_id: str | None = None) -> int:
        if partition_id is None:
            return len(self._backend.rows())
        self._registry.require_declared(partition_id)
        return len(self.peek_partition(partition_id))

    def delivery_hash(self) -> str:
        return canonical_queue_hash(self.snapshot().records)

    def storage_hash(self) -> str:
        return _canonical_hash([_normalize_row(row) for row in self._backend.rows()])

    def _validate_record(self, record: DistributedQueueRecord) -> None:
        if record is None:
            raise DurableQueueError("record required")
        for field in (
            "event_id",
            "partition_id",
            "sequence",
            "normalized_payload_hash",
            "canonical_event_hash",
            "assignment_hash",
        ):
            if not hasattr(record, field):
                raise DurableQueueError(f"invalid record: missing {field}")
        self._registry.require_declared(record.partition_id)


def restore_durable_queue(*, registry, rows: Iterable[Mapping[str, object]]) -> DurableQueueAdapter:
    adapter = DurableQueueAdapter(
        registry=registry,
        backend=InMemoryDurableQueueBackend(rows),
    )
    # Force validation during restore.
    adapter.snapshot()
    return adapter


def _storage_record(record: DistributedQueueRecord) -> DurableQueueStorageRecord:
    return DurableQueueStorageRecord(record=record, record_hash=record.record_hash())


def _record_from_row(row: Mapping[str, object]) -> DistributedQueueRecord:
    normalized = _normalize_row(row)
    record_data = normalized["record"]
    record = DistributedQueueRecord(
        event_id=_require_string(record_data.get("event_id"), "event_id"),
        partition_id=_require_string(record_data.get("partition_id"), "partition_id"),
        sequence=_require_int(record_data.get("sequence"), "sequence"),
        normalized_payload_hash=_require_string(
            record_data.get("normalized_payload_hash"),
            "normalized_payload_hash",
        ),
        canonical_event_hash=_require_string(
            record_data.get("canonical_event_hash"),
            "canonical_event_hash",
        ),
        assignment_hash=_require_string(record_data.get("assignment_hash"), "assignment_hash"),
    )
    DurableQueueStorageRecord(
        record=record,
        record_hash=_require_string(normalized.get("record_hash"), "record_hash"),
        authority_disclaimer=_require_string(
            normalized.get("authority_disclaimer"),
            "authority_disclaimer",
        ),
    )
    return record


def _normalize_row(row: Mapping[str, object]) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        raise DurableQueueError("storage row must be mapping")
    normalized = dict(row)
    if "authority_disclaimer" not in normalized:
        raise DurableQueueError("storage row missing authority disclaimer")
    if "record" not in normalized:
        raise DurableQueueError("storage row missing record")
    if "record_hash" not in normalized:
        raise DurableQueueError("storage row missing record_hash")
    if not isinstance(normalized["record"], Mapping):
        raise DurableQueueError("storage row record must be mapping")
    return normalized


def _row_record(row: Mapping[str, object]) -> Mapping[str, object]:
    return _normalize_row(row)["record"]


def _row_keys(rows: Iterable[Mapping[str, object]]) -> set[tuple[str, int, str]]:
    keys = set()
    for row in rows:
        record = _record_from_row(row)
        keys.add((record.partition_id, record.sequence, record.event_id))
    return keys


def _canonical_records(records: Iterable[DistributedQueueRecord]) -> tuple[DistributedQueueRecord, ...]:
    try:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.partition_id,
                    record.sequence,
                    record.event_id,
                    record.record_hash(),
                ),
            )
        )
    except (DistributedQueueError, TypeError) as exc:
        raise DurableQueueError("durable queue canonicalization failed") from exc


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise DurableQueueError(f"{field} must be non-empty string")
    return value


def _require_int(value: object, field: str) -> int:
    if not isinstance(value, int):
        raise DurableQueueError(f"{field} must be int")
    return value
