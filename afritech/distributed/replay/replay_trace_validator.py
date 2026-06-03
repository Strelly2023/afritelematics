"""
afritech.distributed.replay.replay_trace_validator
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from afritech.distributed.api.queue import DistributedQueueRecord

from afritech.distributed.audit.trace import (
    ExecutionTrace,
    ExecutionTraceBatch,
    build_execution_trace,
)

from afritech.distributed.replay.replay_engine import (
    ReplaySnapshot,
    DistributedReplayEngine,
)


# ============================================================
# ERROR
# ============================================================

class ReplayTraceValidationError(ValueError):
    pass


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class ReplayTraceValidationResult:
    passed: bool
    checked_traces: int
    mismatches: Tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Replay trace validation PASSED\n"
                f"✅ Checked traces: {self.checked_traces}"
            )

        return (
            "❌ Replay trace validation FAILED\n"
            f"❌ Checked traces: {self.checked_traces}\n"
            + "\n".join(self.mismatches)
        )


# ============================================================
# VALIDATOR ✅ FIXED
# ============================================================

class ReplayTraceValidator:

    def __init__(self):
        self._engine = DistributedReplayEngine()

    # ---------------------------------------------------------
    # MAIN ✅ CORRECTED
    # ---------------------------------------------------------

    def validate(self, snapshot: ReplaySnapshot) -> ReplayTraceValidationResult:

        if snapshot is None or not hasattr(snapshot, "records"):
            raise ReplayTraceValidationError("invalid snapshot")

        mismatches: list[str] = []

        original_records = snapshot.records
        original_results = snapshot.expected_results

        # ✅ TRACE FROM ORIGINAL EXECUTION
        original_traces = self._build_trace_batch(
            original_records,
            original_results,
        )

        # ✅ TRACE FROM REPLAY EXECUTION
        replayed_results = self._engine.replay(snapshot)

        replayed_traces = self._build_trace_batch(
            original_records,
            replayed_results,
        )

        # ---------------------------------------------------------
        # COMPARE
        # ---------------------------------------------------------

        original_canonical = original_traces.canonical_traces()
        replayed_canonical = replayed_traces.canonical_traces()

        if len(original_canonical) != len(replayed_canonical):
            mismatches.append("trace length mismatch")

        for i, (a, b) in enumerate(zip(original_canonical, replayed_canonical)):
            if not self._equal_traces(a, b):
                mismatches.append(
                    f"trace mismatch index={i} event={a.event_id}"
                )

        return ReplayTraceValidationResult(
            passed=not mismatches,
            checked_traces=len(original_canonical),
            mismatches=tuple(mismatches),
        )

    # ---------------------------------------------------------
    # INTERNAL ✅ FIXED (CRITICAL)
    # ---------------------------------------------------------

    def _build_trace_batch(
        self,
        records: Tuple[DistributedQueueRecord, ...],
        results: Tuple,
    ) -> ExecutionTraceBatch:

        if len(records) != len(results):
            raise ReplayTraceValidationError("records/results mismatch")

        # ✅ canonical ordering (same as replay engine)
        ordered_pairs = sorted(
            zip(records, results),
            key=lambda x: (
                x[0].partition_id,
                x[0].sequence,
                x[0].event_id,
            ),
        )

        ordered_records = [r for r, _ in ordered_pairs]
        ordered_results = [res for _, res in ordered_pairs]

        batch_hash = self._batch_hash(ordered_records)

        traces: list[ExecutionTrace] = []

        for record, result in zip(ordered_records, ordered_results):

            # ✅ synthetic receipt (deterministic)
            receipt_hash = _receipt_hash(result)

            class _Receipt:
                worker_receipt_hash = receipt_hash

            trace = build_execution_trace(
                record=record,
                batch_hash=batch_hash,
                result=result,
                receipt=_Receipt(),
            )

            traces.append(trace)

        return ExecutionTraceBatch(traces=tuple(traces))

    def _batch_hash(self, records: Tuple) -> str:
        from hashlib import sha256
        import json

        payload = json.dumps(
            [
                {
                    "event_id": r.event_id,
                    "partition_id": r.partition_id,
                    "sequence": r.sequence,
                }
                for r in sorted(
                    records,
                    key=lambda r: (r.partition_id, r.sequence),
                )
            ],
            sort_keys=True,
            separators=(",", ":"),
        )

        return sha256(payload.encode()).hexdigest()

    # ---------------------------------------------------------
    # TRACE COMPARISON ✅
    # ---------------------------------------------------------

    def _equal_traces(self, a: ExecutionTrace, b: ExecutionTrace) -> bool:

        if a is None or b is None:
            return False

        return a.trace_hash() == b.trace_hash()


# ============================================================
# RECEIPT HASH ✅
# ============================================================

def _receipt_hash(result) -> str:
    from hashlib import sha256
    import json

    payload = json.dumps(
        {
            "execution_hash": getattr(result, "execution_hash", None),
            "partition_id": getattr(result, "partition_id", None),
            "sequence": getattr(result, "partition_sequence", None),
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    return sha256(payload.encode()).hexdigest()


# ============================================================
# CONVENIENCE
# ============================================================

def validate_replay_traces(snapshot: ReplaySnapshot) -> bool:
    validator = ReplayTraceValidator()
    result = validator.validate(snapshot)
    return result.passed