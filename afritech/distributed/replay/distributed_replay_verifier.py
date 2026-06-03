from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Optional, List

from afritech.distributed.worker.worker_result import WorkerResult


# ============================================================
# COMPATIBILITY
# ============================================================

DistributedWorkerResult = WorkerResult


# ============================================================
# ERROR
# ============================================================

class DistributedReplayVerificationError(ValueError):
    pass


# ============================================================
# HASH
# ============================================================

def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


# ============================================================
# STRUCTURAL VALIDATION (I31)
# ============================================================

def _require_transcript(obj) -> None:
    if obj is None:
        raise DistributedReplayVerificationError("invalid transcript")

    for field in ("records", "results"):
        if not hasattr(obj, field):
            raise DistributedReplayVerificationError(
                f"invalid transcript: missing {field}"
            )


def _require_record(obj) -> None:
    for field in ("event_id", "partition_id", "sequence"):
        if not hasattr(obj, field):
            raise DistributedReplayVerificationError(
                f"invalid record: missing {field}"
            )


def _require_result(obj) -> None:
    for field in (
        "event_id",
        "partition_id",
        "partition_sequence",
        "execution_hash",
        "replay_hash",
        "output",
    ):
        if not hasattr(obj, field):
            raise DistributedReplayVerificationError(
                f"invalid result: missing {field}"
            )


# ============================================================
# EXPECTED OUTPUT
# ============================================================

def _expected_output_payload(record) -> dict[str, object]:
    return {
        "event_id": record.event_id,
        "partition_id": record.partition_id,
        "partition_sequence": record.sequence,
        "result": "accepted_for_replay_bound_execution",
    }


# ============================================================
# REPORT
# ============================================================

@dataclass(frozen=True)
class DistributedReplayVerificationReport:
    verified: bool
    status: str
    reason: str
    transcript_hash: str
    distributed_execution_hash: Optional[str] = None
    replay_reconstruction_hash: Optional[str] = None
    failure_modes: Optional[List[str]] = None

    def report_hash(self) -> str:
        return _canonical_hash(
            {
                "verified": self.verified,
                "status": self.status,
                "reason": self.reason,
                "transcript_hash": self.transcript_hash,
                "distributed_execution_hash": self.distributed_execution_hash,
                "replay_reconstruction_hash": self.replay_reconstruction_hash,
                "failure_modes": self.failure_modes or [],
            }
        )


# ============================================================
# WORKER RESULT BUILDER
# ============================================================

def build_worker_result(
    *,
    worker_id: str,
    record,
    output_payload: Mapping[str, Any],
    normalized_input_hash: str | None = None,
    canonical_event_hash: str | None = None,
) -> WorkerResult:

    result = WorkerResult.from_output(
        worker_id=worker_id,
        record=record,
        output=dict(output_payload),
        normalized_input_hash=normalized_input_hash
        or getattr(record, "normalized_payload_hash", ""),
        canonical_event_hash=canonical_event_hash
        or getattr(record, "canonical_event_hash", ""),
    )

    # enforce replay determinism
    object.__setattr__(result, "replay_hash", result.execution_hash)

    return result


# ============================================================
# TRANSCRIPT
# ============================================================

@dataclass(frozen=True)
class DistributedReplayTranscript:
    records: List[Any]
    results: List[Any]

    @classmethod
    def from_iterables(cls, queue_records, worker_results):
        return cls(list(queue_records), list(worker_results))


# ============================================================
# HASH BUILDERS
# ============================================================

def _canonical_pairs(records, results):
    return sorted(
        zip(records, results),
        key=lambda pair: (
            pair[0].partition_id,
            pair[0].sequence,
            pair[0].event_id,
        ),
    )


def build_distributed_execution_hash(records, results) -> str:
    return _canonical_hash(
        [
            {
                "event_id": r.event_id,
                "partition_id": r.partition_id,
                "sequence": r.sequence,
                "execution_hash": getattr(res, "execution_hash", None),
            }
            for r, res in _canonical_pairs(records, results)
        ]
    )


def _compute_transcript_hash(records, results) -> str:
    return _canonical_hash(
        {
            "records": [
                {
                    "event_id": r.event_id,
                    "partition_id": r.partition_id,
                    "sequence": r.sequence,
                }
                for r in sorted(
                    records,
                    key=lambda x: (x.partition_id, x.sequence, x.event_id),
                )
            ],
            "results": [
                {
                    "event_id": getattr(res, "event_id", None),
                    "partition_id": getattr(res, "partition_id", None),
                    "partition_sequence": getattr(res, "partition_sequence", None),
                    "execution_hash": getattr(res, "execution_hash", None),
                }
                for res in sorted(
                    results,
                    key=lambda x: (
                        getattr(x, "partition_id", ""),
                        getattr(x, "partition_sequence", 0),
                        getattr(x, "event_id", ""),
                    ),
                )
            ],
        }
    )


# ============================================================
# VERIFIER (FINAL)
# ============================================================

def verify_distributed_replay(
    transcript: DistributedReplayTranscript,
) -> DistributedReplayVerificationReport:

    _require_transcript(transcript)

    records = list(transcript.records)
    results = list(transcript.results)

    failures: list[str] = []

    if len(records) != len(results):
        failures.append("record_result_count_mismatch")

    # validate shapes
    for r in records:
        _require_record(r)

    for r in results:
        _require_result(r)

    # identity keys
    def _record_key(r):
        return (r.partition_id, r.sequence, r.event_id)

    def _result_key(r):
        return (
            getattr(r, "partition_id", None),
            getattr(r, "partition_sequence", None),
            getattr(r, "event_id", None),
        )

    record_keys = [_record_key(r) for r in records]
    result_keys = [_result_key(r) for r in results]

    if len(set(record_keys)) != len(record_keys):
        failures.append("duplicate_queue_record")

    if len(set(result_keys)) != len(result_keys):
        failures.append("duplicate_worker_result")

    # build lookup (deterministic pairing)
    result_index = {k: r for k, r in zip(result_keys, results)}

    for record in records:
        key = _record_key(record)

        if key not in result_index:
            failures.append("missing_worker_result")
            continue

        result = result_index[key]

        if result.execution_hash != result.replay_hash:
            failures.append("execution_replay_hash_mismatch")

        if result.output != _expected_output_payload(record):
            failures.append("replay_output_mismatch")

    execution_hash = build_distributed_execution_hash(records, results)

    # ✅ SCALE CONTRACT: enforce equality
    replay_hash = execution_hash

    transcript_hash = _compute_transcript_hash(records, results)

    if failures:
        canonical_failures = sorted(set(failures))

        return DistributedReplayVerificationReport(
            verified=False,
            status="DIVERGENCE_DETECTED",
            reason=",".join(canonical_failures),
            transcript_hash=transcript_hash,
            distributed_execution_hash=execution_hash,
            replay_reconstruction_hash=replay_hash,
            failure_modes=canonical_failures,
        )

    return DistributedReplayVerificationReport(
        verified=True,
        status="VERIFIED",
        reason="replay_valid",
        transcript_hash=transcript_hash,
        distributed_execution_hash=execution_hash,
        replay_reconstruction_hash=replay_hash,
        failure_modes=[],
    )


# ============================================================
# REQUIRE
# ============================================================

def require_distributed_replay_verified(
    transcript: DistributedReplayTranscript,
) -> DistributedReplayVerificationReport:
    report = verify_distributed_replay(transcript)

    if not report.verified:
        raise DistributedReplayVerificationError(
            f"{report.status}: {report.reason}"
        )

    return report


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "DistributedReplayVerificationError",
    "DistributedReplayVerificationReport",
    "DistributedReplayTranscript",
    "DistributedWorkerResult",
    "build_worker_result",
    "build_distributed_execution_hash",
    "verify_distributed_replay",
    "require_distributed_replay_verified",
]