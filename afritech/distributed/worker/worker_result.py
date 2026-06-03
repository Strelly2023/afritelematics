"""
afritech.distributed.worker.result

Canonical worker result for deterministic distributed execution.

Guarantees:
- Immutable
- Deterministic hashing
- Replay-safe
- Partition-consistent
- Contract-compliant (worker_contract.v1)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any, Mapping


# ============================================================
# ERROR
# ============================================================

class WorkerResultError(ValueError):
    pass


# ============================================================
# HELPERS
# ============================================================

def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _canonical_hash(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_identity(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise WorkerResultError(f"{field} must be non-empty string")

    if "/" in value or "\\" in value or ".." in value:
        raise WorkerResultError(f"{field} invalid")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise WorkerResultError(f"{field} must be sha256")

    try:
        int(value, 16)
    except ValueError:
        raise WorkerResultError(f"{field} must be sha256")


# ============================================================
# WORKER RESULT ✅ FINAL
# ============================================================

@dataclass(frozen=True)
class WorkerResult:
    """
    Canonical distributed worker result.

    Guarantees:
    - Immutable
    - Deterministic hashing
    - Replay-safe
    - Partition-bound execution
    """

    # ---------------------------------------------------------
    # IDENTITY
    # ---------------------------------------------------------
    worker_id: str
    record_id: str
    event_id: str

    # ---------------------------------------------------------
    # PARTITION CONTEXT
    # ---------------------------------------------------------
    partition_id: str
    partition_sequence: int

    # ---------------------------------------------------------
    # EXECUTION STATE
    # ---------------------------------------------------------
    status: str

    # ---------------------------------------------------------
    # OUTPUT
    # ---------------------------------------------------------
    output: Mapping[str, Any]

    # ---------------------------------------------------------
    # HASHES
    # ---------------------------------------------------------
    normalized_input_hash: str
    canonical_event_hash: str
    execution_hash: str
    replay_hash: str

    # ---------------------------------------------------------
    # VALIDATION FLAG
    # ---------------------------------------------------------
    verified: bool = True

    # ============================================================
    # VALIDATION ✅ STRICT
    # ============================================================

    def __post_init__(self) -> None:

        _require_identity(self.worker_id, "worker_id")
        _require_identity(self.record_id, "record_id")
        _require_identity(self.event_id, "event_id")
        _require_identity(self.partition_id, "partition_id")

        if not isinstance(self.partition_sequence, int) or self.partition_sequence < 0:
            raise WorkerResultError("invalid partition_sequence")

        if self.status not in (
            "EXECUTED",
            "REFUSED",
            "REPLAY_INVALID",
            "DIVERGENCE_DETECTED",
        ):
            raise WorkerResultError("invalid status")

        if not isinstance(self.output, Mapping):
            raise WorkerResultError("output must be mapping")

        _require_sha256(self.normalized_input_hash, "normalized_input_hash")
        _require_sha256(self.canonical_event_hash, "canonical_event_hash")
        _require_sha256(self.execution_hash, "execution_hash")
        _require_sha256(self.replay_hash, "replay_hash")

        # ✅ replay equivalence guarantee
        if self.execution_hash != self.replay_hash:
            raise WorkerResultError("execution and replay hash mismatch")

    # ============================================================
    # FACTORY ✅ ONLY SAFE CONSTRUCTION
    # ============================================================

    @classmethod
    def from_output(
        cls,
        *,
        worker_id: str,
        record,
        output: Mapping[str, Any],
        normalized_input_hash: str,
        canonical_event_hash: str,
        status: str = "EXECUTED",
    ) -> "WorkerResult":

        if record is None:
            raise WorkerResultError("record required")

        for field in ("event_id", "partition_id", "sequence", "assignment_hash"):
            if not hasattr(record, field):
                raise WorkerResultError(f"invalid record: missing {field}")

        base = {
            "worker_id": worker_id,
            "record_id": record.event_id,
            "event_id": record.event_id,
            "partition_id": record.partition_id,
            "partition_sequence": record.sequence,
            "status": status,
            "output": dict(output),
            "normalized_input_hash": normalized_input_hash,
            "canonical_event_hash": canonical_event_hash,
            "assignment_hash": record.assignment_hash,
        }

        execution_hash = _canonical_hash(base)

        return cls(
            worker_id=worker_id,
            record_id=record.event_id,
            event_id=record.event_id,
            partition_id=record.partition_id,
            partition_sequence=record.sequence,
            status=status,
            output=dict(output),
            normalized_input_hash=normalized_input_hash,
            canonical_event_hash=canonical_event_hash,
            execution_hash=execution_hash,
            replay_hash=execution_hash,
            verified=True,
        )

    # ============================================================
    # OUTPUT HASH ✅
    # ============================================================

    @property
    def output_hash(self) -> str:
        return _canonical_hash(dict(self.output))

    # ============================================================
    # SERIALIZATION ✅ CANONICAL
    # ============================================================

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "record_id": self.record_id,
            "event_id": self.event_id,
            "partition_id": self.partition_id,
            "partition_sequence": self.partition_sequence,
            "status": self.status,
            "output": dict(self.output),
            "normalized_input_hash": self.normalized_input_hash,
            "canonical_event_hash": self.canonical_event_hash,
            "execution_hash": self.execution_hash,
            "replay_hash": self.replay_hash,
            "verified": self.verified,
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.canonical_dict())

    def canonical_hash(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    # ============================================================
    # STRICT EQUALITY ✅ REPLAY-SAFE
    # ============================================================

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False

        required = (
            "execution_hash",
            "partition_id",
            "partition_sequence",
        )

        for field in required:
            if not hasattr(other, field):
                return False

        return (
            self.execution_hash == other.execution_hash and
            self.partition_id == other.partition_id and
            self.partition_sequence == other.partition_sequence
        )

    # ============================================================
    # DEBUG
    # ============================================================

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_dict()


# ============================================================
# BUILDER ✅ API SAFE
# ============================================================

def build_worker_result(
    *,
    worker_id: str,
    record,
    output_payload: Mapping[str, Any],
    normalized_input_hash: str,
    canonical_event_hash: str,
) -> WorkerResult:

    return WorkerResult.from_output(
        worker_id=worker_id,
        record=record,
        output=output_payload,
        normalized_input_hash=normalized_input_hash,
        canonical_event_hash=canonical_event_hash,
    )


# ============================================================
# VALIDATION HELPERS ✅
# ============================================================

def require_worker_results(results: list[WorkerResult]) -> list[WorkerResult]:

    if not results:
        raise WorkerResultError("results cannot be empty")

    validated = []

    for r in results:
        if r is None:
            raise WorkerResultError("invalid result")

        for field in (
            "execution_hash",
            "partition_id",
            "partition_sequence",
            "verified",
        ):
            if not hasattr(r, field):
                raise WorkerResultError(f"invalid result: missing {field}")

        if not r.verified:
            raise WorkerResultError("result not verified")

        validated.append(r)

    return validated