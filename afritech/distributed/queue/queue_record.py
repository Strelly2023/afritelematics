"""
afritech.distributed.queue.queue_record

Canonical queue record model for AfriTech distributed scale execution.

Guarantees:
- deterministic record structure
- replay-safe hashing
- canonical ordering support
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping


# ============================================================
# ERROR
# ============================================================

class QueueRecordError(ValueError):
    """Raised when a distributed queue record violates replay safety."""


# ============================================================
# INTERNAL UTIL
# ============================================================

def _canonical_json(data: object) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )


def _require_identity(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise QueueRecordError(f"{field_name} must be a non-empty string")

    if "/" in value or "\\" in value or ".." in value:
        raise QueueRecordError(
            f"{field_name} must not contain filesystem path syntax"
        )

    if value != value.strip():
        raise QueueRecordError(f"{field_name} must be trimmed")


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise QueueRecordError(
            f"{field_name} must be a non-empty SHA-256 string"
        )

    if len(value) != 64:
        raise QueueRecordError(f"{field_name} must be SHA-256 hex")

    try:
        int(value, 16)
    except ValueError as exc:
        raise QueueRecordError(
            f"{field_name} must be SHA-256 hex"
        ) from exc


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
        _require_identity(self.event_id, "event_id")
        _require_identity(self.partition_id, "partition_id")

        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise QueueRecordError("sequence must be non-negative int")

        _require_sha256(self.normalized_payload_hash, "normalized_payload_hash")
        _require_sha256(self.canonical_event_hash, "canonical_event_hash")
        _require_sha256(self.assignment_hash, "assignment_hash")

    def to_canonical_dict(self) -> dict[str, object]:
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
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


# ============================================================
# ENVELOPE ✅ FINAL
# ============================================================

@dataclass(frozen=True)
class QueueRecordEnvelope:
    record: DistributedQueueRecord
    record_hash: str

    def __post_init__(self) -> None:

        if self.record is None:
            raise QueueRecordError("invalid record")

        # ✅ structural validation (no isinstance dependency)
        for field in (
            "event_id",
            "partition_id",
            "sequence",
            "assignment_hash",
        ):
            if not hasattr(self.record, field):
                raise QueueRecordError(f"invalid record: missing {field}")

        _require_sha256(self.record_hash, "record_hash")

        expected = (
            self.record.record_hash()
            if hasattr(self.record, "record_hash")
            else _fallback_hash(self.record)
        )

        if self.record_hash != expected:
            raise QueueRecordError("record_hash mismatch")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "record": self.record.to_canonical_dict(),
            "record_hash": self.record_hash,
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_canonical_dict())


# ============================================================
# BATCH ✅ FINAL
# ============================================================

@dataclass(frozen=True)
class QueueRecordBatch:
    records: tuple[DistributedQueueRecord, ...]

    def __post_init__(self) -> None:

        if not isinstance(self.records, tuple):
            raise QueueRecordError("records must be tuple")

        seen: set[tuple[str, int]] = set()

        for record in self.records:

            if record is None:
                raise QueueRecordError("invalid record")

            # ✅ structural validation
            for field in (
                "event_id",
                "partition_id",
                "sequence",
                "normalized_payload_hash",
                "canonical_event_hash",
                "assignment_hash",
            ):
                if not hasattr(record, field):
                    raise QueueRecordError(f"invalid record: missing {field}")

            identity = (record.partition_id, record.sequence)

            # ✅ uniqueness constraint (no duplicate sequence per partition)
            if identity in seen:
                raise QueueRecordError(
                    f"duplicate partition sequence detected: {identity}"
                )

            seen.add(identity)

    @classmethod
    def from_records(
        cls,
        records: tuple[DistributedQueueRecord, ...] | list[DistributedQueueRecord],
    ) -> "QueueRecordBatch":
        return cls(records=tuple(records))

    def canonical_records(self) -> tuple[DistributedQueueRecord, ...]:
        return tuple(
            sorted(
                self.records,
                key=lambda r: (
                    r.partition_id,
                    r.sequence,
                    r.event_id,
                    r.record_hash(),
                ),
            )
        )

    def to_canonical_list(self) -> list[dict[str, object]]:
        return [
            r.to_canonical_dict()
            for r in self.canonical_records()
        ]

    def canonical_json(self) -> str:
        return _canonical_json(self.to_canonical_list())

    def batch_hash(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


# ============================================================
# HASHING ✅ FINAL
# ============================================================

def canonical_event_hash(event: Mapping[str, object]) -> str:

    if not isinstance(event, Mapping):
        raise QueueRecordError("event must be mapping")

    try:
        payload = _canonical_json(dict(event))
    except TypeError as exc:
        raise QueueRecordError("event must be JSON serializable") from exc

    return sha256(payload.encode("utf-8")).hexdigest()


# ============================================================
# BUILDER ✅ FINAL
# ============================================================

def build_queue_record(
    *,
    event_id: str,
    partition_id: str,
    sequence: int,
    normalized_payload_hash: str,
    event: Mapping[str, object],
    assignment_hash: str,
) -> DistributedQueueRecord:

    _require_identity(event_id, "event_id")
    _require_identity(partition_id, "partition_id")
    _require_sha256(normalized_payload_hash, "normalized_payload_hash")
    _require_sha256(assignment_hash, "assignment_hash")

    return DistributedQueueRecord(
        event_id=event_id,
        partition_id=partition_id,
        sequence=sequence,
        normalized_payload_hash=normalized_payload_hash,
        canonical_event_hash=canonical_event_hash(event),
        assignment_hash=assignment_hash,
    )


# ============================================================
# HELPERS ✅ FINAL
# ============================================================

def envelope_record(record: DistributedQueueRecord) -> QueueRecordEnvelope:
    return QueueRecordEnvelope(
        record=record,
        record_hash=record.record_hash(),
    )


def canonical_queue_record_collection_hash(
    records: tuple[DistributedQueueRecord, ...] | list[DistributedQueueRecord],
) -> str:
    return QueueRecordBatch.from_records(records).batch_hash()


def _fallback_hash(obj) -> str:
    return sha256(
        json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
