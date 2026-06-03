"""
afritech.distributed.coordinator.batch_coordinator
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

from afritech.distributed.coordinator.coordinator import (
    CoordinationBatch,
    CoordinationResult,
    DistributedCoordinatorError,
)

from afritech.distributed.queue.queue_record import (
    QueueRecordBatch,
)


# ============================================================
# ERROR
# ============================================================

class BatchCoordinatorError(ValueError):
    pass


# ============================================================
# PLAN
# ============================================================

@dataclass(frozen=True)
class BatchPlan:
    batches: tuple[CoordinationBatch, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.batches, tuple):
            raise BatchCoordinatorError("batches must be a tuple")

        if not self.batches:
            raise BatchCoordinatorError("batch plan cannot be empty")

        seen: set[str] = set()

        for batch in self.batches:
            if batch is None or not hasattr(batch, "batch_id"):
                raise BatchCoordinatorError("invalid batch")

            if batch.batch_id in seen:
                raise BatchCoordinatorError(f"duplicate batch_id: {batch.batch_id}")

            seen.add(batch.batch_id)

    def to_canonical_dict(self) -> dict:
        return {
            "batches": [
                b.to_canonical_dict()
                for b in sorted(self.batches, key=lambda b: b.batch_id)
            ]
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def plan_hash(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


# ============================================================
# REPORT
# ============================================================

@dataclass(frozen=True)
class BatchCoordinationReport:
    plan_hash: str
    coordination_results: tuple[CoordinationResult, ...]
    verified: bool
    status: str
    report_hash: str

    def __post_init__(self) -> None:
        _require_sha256(self.plan_hash, "plan_hash")
        _require_sha256(self.report_hash, "report_hash")

        if not isinstance(self.coordination_results, tuple):
            raise BatchCoordinatorError("coordination_results must be tuple")

        for r in self.coordination_results:
            if r is None or not hasattr(r, "coordination_hash"):
                raise BatchCoordinatorError("invalid coordination result")

        if not isinstance(self.verified, bool):
            raise BatchCoordinatorError("verified must be bool")

        if self.status not in {
            "VERIFIED",
            "REPLAY_INVALID",
            "PARTIAL_FAILURE",
        }:
            raise BatchCoordinatorError("invalid status")

    def _result_dict(self, r: CoordinationResult) -> dict:
        return {
            "batch_id": r.batch.batch_id,
            "coordination_hash": r.coordination_hash,
            "verified": r.verification_report.verified,
        }

    def to_canonical_dict(self) -> dict:
        return {
            "plan_hash": self.plan_hash,
            "verified": self.verified,
            "status": self.status,
            "coordination_results": [
                self._result_dict(r)
                for r in sorted(
                    self.coordination_results,
                    key=lambda x: (x.batch.batch_id, x.coordination_hash),
                )
            ],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )


# ============================================================
# COORDINATOR ✅ FIXED
# ============================================================

class DeterministicBatchCoordinator:

    def __init__(self, *, coordinator, max_batch_size: int) -> None:

        if coordinator is None or not hasattr(coordinator, "coordinate"):
            raise BatchCoordinatorError("invalid coordinator")

        if not isinstance(max_batch_size, int) or max_batch_size <= 0:
            raise BatchCoordinatorError("invalid max_batch_size")

        self._coordinator = coordinator
        self._max_batch_size = max_batch_size

    @property
    def max_batch_size(self) -> int:
        return self._max_batch_size

    # ---------------------------------------------------------
    # PLAN
    # ---------------------------------------------------------

    def build_plan(self, records: Iterable) -> BatchPlan:

        canonical_records = QueueRecordBatch.from_records(
            tuple(records)
        ).canonical_records()

        if not canonical_records:
            raise BatchCoordinatorError("cannot build plan from empty records")

        batches: list[CoordinationBatch] = []

        for i in range(0, len(canonical_records), self._max_batch_size):
            batches.append(
                CoordinationBatch.create(
                    canonical_records[i:i + self._max_batch_size]
                )
            )

        return BatchPlan(batches=tuple(batches))

    # ---------------------------------------------------------
    # EXECUTION ✅ FINAL FIX HERE
    # ---------------------------------------------------------

    def coordinate_plan(self, plan: BatchPlan) -> BatchCoordinationReport:

        if plan is None or not hasattr(plan, "batches"):
            raise BatchCoordinatorError("invalid plan")

        results: list[CoordinationResult] = []

        for batch in plan.batches:
            try:
                result = self._coordinator.coordinate(batch.records)
            except Exception as exc:  # ✅ CRITICAL FIX
                raise BatchCoordinatorError(
                    f"coordination failed for {batch.batch_id}"
                ) from exc

            results.append(result)

        verified = all(r.verification_report.verified for r in results)

        status = "VERIFIED" if verified else "REPLAY_INVALID"

        payload = {
            "plan_hash": plan.plan_hash(),
            "verified": verified,
            "status": status,
            "coordination_hashes": [
                r.coordination_hash
                for r in sorted(
                    results,
                    key=lambda x: (x.batch.batch_id, x.coordination_hash),
                )
            ],
        }

        report_hash = _canonical_payload_hash(payload)

        return BatchCoordinationReport(
            plan_hash=plan.plan_hash(),
            coordination_results=tuple(results),
            verified=verified,
            status=status,
            report_hash=report_hash,
        )

    # ---------------------------------------------------------
    # HIGH LEVEL
    # ---------------------------------------------------------

    def coordinate_records(self, records: Iterable) -> BatchCoordinationReport:
        return self.coordinate_plan(self.build_plan(records))

    def coordinate_records_verified(self, records: Iterable) -> BatchCoordinationReport:
        report = self.coordinate_records(records)

        if not report.verified:
            raise BatchCoordinatorError("batch verification failed")

        return report


# ============================================================
# BUILDER
# ============================================================

def build_batch_plan(
    *,
    records: Iterable,
    max_batch_size: int,
) -> BatchPlan:

    if not isinstance(max_batch_size, int) or max_batch_size <= 0:
        raise BatchCoordinatorError("invalid max_batch_size")

    canonical_records = QueueRecordBatch.from_records(
        tuple(records)
    ).canonical_records()

    if not canonical_records:
        raise BatchCoordinatorError("cannot build plan from empty records")

    batches = []

    for i in range(0, len(canonical_records), max_batch_size):
        batches.append(
            CoordinationBatch.create(
                canonical_records[i:i + max_batch_size]
            )
        )

    return BatchPlan(batches=tuple(batches))


# ============================================================
# HELPERS
# ============================================================

def _canonical_payload_hash(payload: dict) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise BatchCoordinatorError(f"{field} must be sha256")

    try:
        int(value, 16)
    except ValueError:
        raise BatchCoordinatorError(f"{field} invalid")
