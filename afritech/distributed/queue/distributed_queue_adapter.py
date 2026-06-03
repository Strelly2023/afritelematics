"""
afritech.distributed.queue.distributed_queue_adapter

Replay-safe distributed queue adapter for AfriTech distributed scale execution.

Guarantees:
- deterministic ordering
- partition isolation
- replay-safe execution
- canonical hashing
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Mapping


from afritech.distributed.partition.partition_assignment import (
    PartitionAssignment,
    PartitionAssignmentError,
    require_valid_assignment,
)

# ============================================================
# ERROR
# ============================================================

class DistributedQueueError(ValueError):
    pass


# ============================================================
# VALIDATION
# ============================================================

def _require_non_empty_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise DistributedQueueError(f"{field_name} invalid")

    if "/" in value or "\\" in value or ".." in value:
        raise DistributedQueueError(f"{field_name} invalid")

    if value != value.strip():
        raise DistributedQueueError(f"{field_name} invalid")


def _require_hex_hash(value: str, field_name: str) -> None:
    _require_non_empty_string(value, field_name)

    if len(value) != 64:
        raise DistributedQueueError(f"{field_name} must be sha256")

    try:
        int(value, 16)
    except ValueError:
        raise DistributedQueueError(f"{field_name} must be sha256")


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


# ============================================================
# RECORD ✅ FINAL
# ============================================================

@dataclass(frozen=True, order=True)
class DistributedQueueRecord:

    event_id: str
    partition_id: str
    sequence: int
    normalized_payload_hash: str
    canonical_event_hash: str
    assignment_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.event_id, "event_id")
        _require_non_empty_string(self.partition_id, "partition_id")

        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise DistributedQueueError("invalid sequence")

        _require_hex_hash(self.normalized_payload_hash, "normalized_payload_hash")
        _require_hex_hash(self.canonical_event_hash, "canonical_event_hash")
        _require_hex_hash(self.assignment_hash, "assignment_hash")

    def to_canonical_dict(self) -> dict:
        return {
            "assignment_hash": self.assignment_hash,
            "canonical_event_hash": self.canonical_event_hash,
            "event_id": self.event_id,
            "normalized_payload_hash": self.normalized_payload_hash,
            "partition_id": self.partition_id,
            "sequence": self.sequence,
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_canonical_dict())

    def record_hash(self) -> str:
        return sha256(self.canonical_json().encode()).hexdigest()


# ============================================================
# SNAPSHOT ✅ FINAL
# ============================================================

@dataclass(frozen=True)
class QueueSnapshot:
    records: tuple[DistributedQueueRecord, ...]

    def snapshot_hash(self) -> str:
        payload = _canonical_json(
            [r.to_canonical_dict() for r in self.records]
        )
        return sha256(payload.encode()).hexdigest()


# ============================================================
# HASHING
# ============================================================

def canonical_event_hash(event: Mapping[str, object]) -> str:
    if not isinstance(event, Mapping):
        raise DistributedQueueError("event must be mapping")

    payload = _canonical_json(dict(event))
    return sha256(payload.encode()).hexdigest()


# ============================================================
# RECORD BUILDER ✅ FINAL
# ============================================================

def build_queue_record(
    *,
    event_id: str,
    sequence: int,
    normalized_payload_hash: str,
    event: Mapping[str, object],
    assignment: PartitionAssignment,
    registry,
) -> DistributedQueueRecord:

    if registry is None or not hasattr(registry, "registry_hash"):
        raise DistributedQueueError("invalid registry")

    try:
        assignment = require_valid_assignment(
            assignment=assignment,
            registry=registry,
        )
    except PartitionAssignmentError as exc:
        raise DistributedQueueError("invalid assignment") from exc

    _require_non_empty_string(event_id, "event_id")
    _require_hex_hash(normalized_payload_hash, "normalized_payload_hash")

    record = DistributedQueueRecord(
        event_id=event_id,
        partition_id=assignment.partition_id,
        sequence=sequence,
        normalized_payload_hash=normalized_payload_hash,
        canonical_event_hash=canonical_event_hash(event),
        assignment_hash=assignment.assignment_hash,
    )

    registry.require_declared(record.partition_id)

    return record


# ============================================================
# ADAPTER INTERFACE
# ============================================================

class DistributedQueueAdapter:

    def publish(self, record):
        raise NotImplementedError

    def publish_many(self, records: Iterable):
        raise NotImplementedError

    def consume_partition(self, partition_id: str, limit: int | None = None):
        raise NotImplementedError

    def peek_partition(self, partition_id: str, limit: int | None = None):
        raise NotImplementedError

    def snapshot(self):
        raise NotImplementedError


# ============================================================
# IN-MEMORY IMPLEMENTATION ✅ FINAL
# ============================================================

class InMemoryDistributedQueueAdapter(DistributedQueueAdapter):

    def __init__(self, registry) -> None:
        if registry is None or not hasattr(registry, "partition_ids"):
            raise DistributedQueueError("invalid registry")

        self._registry = registry

        self._records = {
            pid: [] for pid in registry.partition_ids
        }

    # ---------------------------------------------------------
    # PUBLISH
    # ---------------------------------------------------------

    def publish(self, record) -> DistributedQueueRecord:
        self._validate(record)

        partition_records = self._records[record.partition_id]

        # ✅ strict sequence guarantee (no gaps, no reorder)
        if record.sequence != len(partition_records):
            raise DistributedQueueError(
                f"sequence mismatch for {record.partition_id}: "
                f"expected {len(partition_records)}, got {record.sequence}"
            )

        partition_records.append(record)
        return record

    def publish_many(self, records: Iterable):
        return tuple(self.publish(r) for r in records)

    # ---------------------------------------------------------
    # CONSUMPTION
    # ---------------------------------------------------------

    def consume_partition(self, partition_id: str, limit: int | None = None):
        self._registry.require_declared(partition_id)

        data = self._records[partition_id]
        n = len(data) if limit is None else min(limit, len(data))

        result = tuple(data[:n])

        # ✅ destructive consumption (replay predictable)
        del data[:n]

        return result

    def peek_partition(self, partition_id: str, limit: int | None = None):
        self._registry.require_declared(partition_id)

        data = self._records[partition_id]

        return tuple(data if limit is None else data[:limit])

    # ---------------------------------------------------------
    # UTIL
    # ---------------------------------------------------------

    def queue_size(self, partition_id: str | None = None) -> int:
        if partition_id is not None:
            self._registry.require_declared(partition_id)
            return len(self._records[partition_id])

        return sum(len(v) for v in self._records.values())

    def snapshot(self) -> QueueSnapshot:
        ordered = []

        # ✅ canonical ordering: partition -> sequence
        for pid in self._registry.partition_ids:
            ordered.extend(
                sorted(
                    self._records[pid],
                    key=lambda r: r.sequence
                )
            )

        return QueueSnapshot(tuple(ordered))

    # ---------------------------------------------------------
    # INTERNAL VALIDATION
    # ---------------------------------------------------------

    def _validate(self, record) -> None:

        if record is None:
            raise DistributedQueueError("invalid record")

        for field in (
            "event_id",
            "partition_id",
            "sequence",
            "normalized_payload_hash",
            "canonical_event_hash",
            "assignment_hash",
        ):
            if not hasattr(record, field):
                raise DistributedQueueError(
                    f"invalid record: missing {field}"
                )

        self._registry.require_declared(record.partition_id)

        _require_hex_hash(record.normalized_payload_hash, "normalized_payload_hash")
        _require_hex_hash(record.canonical_event_hash, "canonical_event_hash")
        _require_hex_hash(record.assignment_hash, "assignment_hash")


# ============================================================
# GLOBAL QUEUE HASH ✅ FINAL
# ============================================================

def canonical_queue_hash(records: Iterable) -> str:

    validated = []

    for r in records:
        if r is None:
            raise DistributedQueueError("invalid record")

        for field in ("partition_id", "sequence", "event_id"):
            if not hasattr(r, field):
                raise DistributedQueueError(
                    f"invalid record: missing {field}"
                )

        validated.append(r)

    ordered = sorted(
        validated,
        key=lambda r: (
            r.partition_id,
            r.sequence,
            r.event_id,
            r.record_hash(),
        )
    )

    payload = _canonical_json(
        [r.to_canonical_dict() for r in ordered]
    )

    return sha256(payload.encode()).hexdigest()