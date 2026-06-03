"""
afritech.distributed.coordinator.coordinator
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

from afritech.distributed.queue.distributed_queue_adapter import DistributedQueueRecord

from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
    DistributedReplayVerificationReport,
    DistributedWorkerResult,
    verify_distributed_replay,
)

from afritech.distributed.worker.worker_node import (
    DeterministicWorkerNode,
    WorkerExecutionOutcome,
)


# ============================================================
# ERROR
# ============================================================

class DistributedCoordinatorError(ValueError):
    pass


# ============================================================
# BATCH
# ============================================================

@dataclass(frozen=True)
class CoordinationBatch:
    batch_id: str
    records: tuple[DistributedQueueRecord, ...]

    def __post_init__(self) -> None:
        if not self.records:
            raise DistributedCoordinatorError("batch cannot be empty")

    @classmethod
    def create(cls, records: Iterable[DistributedQueueRecord]) -> "CoordinationBatch":

        canonical_records = tuple(
            sorted(
                tuple(records),
                key=lambda r: (
                    r.partition_id,
                    r.sequence,
                    r.event_id,
                    r.record_hash(),
                ),
            )
        )

        if not canonical_records:
            raise DistributedCoordinatorError("empty batch")

        payload = {
            "records": [r.to_canonical_dict() for r in canonical_records]
        }

        return cls(
            batch_id=f"batch.{_hash(payload)}",
            records=canonical_records,
        )

    def batch_hash(self) -> str:
        return _hash(self.to_canonical_dict())

    def to_canonical_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "records": [r.to_canonical_dict() for r in self.records],
        }


# ============================================================
# ASSIGNMENT
# ============================================================

@dataclass(frozen=True)
class CoordinationAssignment:
    batch_id: str
    worker_id: str
    event_id: str
    partition_id: str
    partition_sequence: int
    assignment_hash: str

    @classmethod
    def create(cls, batch_id: str, worker_id: str, record: DistributedQueueRecord):
        payload = {
            "batch_id": batch_id,
            "worker_id": worker_id,
            "event_id": record.event_id,
            "partition_id": record.partition_id,
            "partition_sequence": record.sequence,
        }

        return cls(
            batch_id=batch_id,
            worker_id=worker_id,
            event_id=record.event_id,
            partition_id=record.partition_id,
            partition_sequence=record.sequence,
            assignment_hash=_hash(payload),
        )


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class CoordinationResult:
    batch: CoordinationBatch
    assignments: tuple[CoordinationAssignment, ...]
    worker_results: tuple[DistributedWorkerResult, ...]
    verification_report: DistributedReplayVerificationReport
    coordination_hash: str


# ============================================================
# COORDINATOR ✅ FINAL
# ============================================================

class DistributedCoordinator:

    def __init__(self, *, workers: tuple[DeterministicWorkerNode, ...]):
        if not workers:
            raise DistributedCoordinatorError("workers required")

        self._workers = tuple(sorted(workers, key=lambda w: w.worker_id))

    def coordinate(self, records: Iterable[DistributedQueueRecord]) -> CoordinationResult:

        batch = CoordinationBatch.create(records)

        assignments: list[CoordinationAssignment] = []
        results: list[DistributedWorkerResult] = []

        # -----------------------------------------------------
        # EXECUTION
        # -----------------------------------------------------

        for record in batch.records:

            worker = self._select_worker(record)

            assignment = CoordinationAssignment.create(
                batch.batch_id,
                worker.worker_id,
                record,
            )

            try:
                outcome = worker.execute(record)
            except Exception as exc:
                raise DistributedCoordinatorError(
                    f"worker execution failed for {record.event_id}"
                ) from exc

            _validate(outcome, assignment)

            assignments.append(assignment)
            results.append(outcome.result)

        # -----------------------------------------------------
        # REPLAY VERIFICATION (DO NOT ENFORCE)
        # -----------------------------------------------------

        transcript = DistributedReplayTranscript.from_iterables(
            queue_records=batch.records,
            worker_results=tuple(results),
        )

        report = verify_distributed_replay(transcript)

        # ✅ IMPORTANT: do NOT raise here

        # -----------------------------------------------------
        # RESULT
        # -----------------------------------------------------

        return CoordinationResult(
            batch=batch,
            assignments=tuple(assignments),
            worker_results=tuple(results),
            verification_report=report,
            coordination_hash=_coord_hash(batch, assignments, results, report),
        )

    def coordinate_verified(self, records):

        result = self.coordinate(records)

        if not result.verification_report.verified:
            raise DistributedCoordinatorError(
                "verification failed: "
                + ",".join(result.verification_report.failure_modes or [])
            )

        return result

    # ---------------------------------------------------------
    # WORKER SELECTION
    # ---------------------------------------------------------

    def _select_worker(self, record: DistributedQueueRecord):

        eligible = [w for w in self._workers if w.can_execute(record)]

        if not eligible:
            raise DistributedCoordinatorError(
                f"no worker for partition {record.partition_id}"
            )

        selector = _hash({
            "event_id": record.event_id,
            "partition_id": record.partition_id,
            "sequence": record.sequence,
            "workers": [w.worker_id for w in eligible],
        })

        return eligible[int(selector, 16) % len(eligible)]


# ============================================================
# HELPERS
# ============================================================

def _validate(outcome: WorkerExecutionOutcome, assignment: CoordinationAssignment):
    r = outcome.result

    if r.worker_id != assignment.worker_id:
        raise DistributedCoordinatorError("worker mismatch")

    if r.event_id != assignment.event_id:
        raise DistributedCoordinatorError("event mismatch")

    if r.partition_id != assignment.partition_id:
        raise DistributedCoordinatorError("partition mismatch")

    if r.partition_sequence != assignment.partition_sequence:
        raise DistributedCoordinatorError("sequence mismatch")


def _coord_hash(batch, assignments, results, report):

    payload = {
        "batch": batch.batch_hash(),
        "assignments": [a.assignment_hash for a in assignments],
        "results": [r.execution_hash for r in results],
        "report": report.report_hash(),
    }

    return _hash(payload)


def _hash(payload):
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()