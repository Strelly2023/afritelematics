"""
afritech.distributed.audit.trace

Deterministic execution trace system for AfriTech distributed platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping, Any


# ============================================================
# ERROR
# ============================================================

class ExecutionTraceError(ValueError):
    pass


# ============================================================
# TRACE OBJECT
# ============================================================

@dataclass(frozen=True)
class ExecutionTrace:

    event_id: str
    partition_id: str
    sequence: int

    record_hash: str
    batch_hash: str

    worker_id: str

    execution_hash: str
    receipt_hash: str

    def __post_init__(self) -> None:
        _require_identity(self.event_id, "event_id")
        _require_identity(self.partition_id, "partition_id")
        _require_identity(self.worker_id, "worker_id")

        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise ExecutionTraceError("sequence must be non-negative integer")

        _require_sha256(self.record_hash, "record_hash")
        _require_sha256(self.batch_hash, "batch_hash")
        _require_sha256(self.execution_hash, "execution_hash")
        _require_sha256(self.receipt_hash, "receipt_hash")

    # ---------------------------------------------------------
    # CANONICAL
    # ---------------------------------------------------------

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "batch_hash": self.batch_hash,
            "event_id": self.event_id,
            "execution_hash": self.execution_hash,
            "partition_id": self.partition_id,
            "record_hash": self.record_hash,
            "receipt_hash": self.receipt_hash,
            "sequence": self.sequence,
            "worker_id": self.worker_id,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def trace_hash(self) -> str:
        return sha256(self.canonical_json().encode()).hexdigest()


# ============================================================
# COLLECTION ✅
# ============================================================

@dataclass(frozen=True)
class ExecutionTraceBatch:

    traces: tuple[ExecutionTrace, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.traces, tuple):
            raise ExecutionTraceError("traces must be tuple")

        seen: set[tuple[str, int]] = set()

        for t in self.traces:
            if not isinstance(t, ExecutionTrace):
                raise ExecutionTraceError("invalid trace type")

            identity = (t.partition_id, t.sequence)

            if identity in seen:
                raise ExecutionTraceError(
                    f"duplicate trace sequence: {identity}"
                )

            seen.add(identity)

    def canonical_traces(self) -> tuple[ExecutionTrace, ...]:
        return tuple(
            sorted(
                self.traces,
                key=lambda t: (
                    t.partition_id,
                    t.sequence,
                    t.event_id,
                    t.trace_hash(),
                ),
            )
        )

    def canonical_json(self) -> str:
        return json.dumps(
            [t.to_canonical_dict() for t in self.canonical_traces()],
            sort_keys=True,
            separators=(",", ":"),
        )

    def batch_hash(self) -> str:
        return sha256(self.canonical_json().encode()).hexdigest()


# ============================================================
# BUILDER ✅
# ============================================================

def build_execution_trace(
    *,
    record,
    batch_hash: str,
    result,
    receipt,
) -> ExecutionTrace:

    # ---------------------------------------------------------
    # RECORD VALIDATION
    # ---------------------------------------------------------
    for f in ("event_id", "partition_id", "sequence"):
        if not hasattr(record, f):
            raise ExecutionTraceError(f"record missing {f}")

    record_hash = (
        record.record_hash()
        if hasattr(record, "record_hash") and callable(record.record_hash)
        else _fallback_hash(record)
    )

    # ---------------------------------------------------------
    # RESULT VALIDATION
    # ---------------------------------------------------------
    for f in ("worker_id", "execution_hash"):
        if not hasattr(result, f):
            raise ExecutionTraceError(f"result missing {f}")

    # ---------------------------------------------------------
    # RECEIPT VALIDATION
    # ---------------------------------------------------------
    if not hasattr(receipt, "worker_receipt_hash"):
        raise ExecutionTraceError("receipt missing worker_receipt_hash")

    _require_sha256(batch_hash, "batch_hash")

    return ExecutionTrace(
        event_id=record.event_id,
        partition_id=record.partition_id,
        sequence=record.sequence,
        record_hash=record_hash,
        batch_hash=batch_hash,
        worker_id=result.worker_id,
        execution_hash=result.execution_hash,
        receipt_hash=receipt.worker_receipt_hash,
    )


# ============================================================
# UTILITIES
# ============================================================

def _fallback_hash(obj: Any) -> str:
    """
    Safe fallback hashing for objects that do not expose record_hash().
    """
    try:
        if isinstance(obj, Mapping):
            payload = dict(obj)
        else:
            payload = {
                k: getattr(obj, k)
                for k in dir(obj)
                if not k.startswith("_") and not callable(getattr(obj, k))
            }
    except Exception:
        payload = str(obj)

    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode()
    ).hexdigest()


def _require_identity(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ExecutionTraceError(f"{field} invalid")

    if "/" in value or "\\" in value or ".." in value:
        raise ExecutionTraceError(f"{field} contains invalid syntax")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ExecutionTraceError(f"{field} must be sha256")

    try:
        int(value, 16)
    except ValueError as exc:
        raise ExecutionTraceError(f"{field} invalid sha256") from exc


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ExecutionTrace",
    "ExecutionTraceBatch",
    "ExecutionTraceError",
    "build_execution_trace",
]
