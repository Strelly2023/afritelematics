"""
afritech.distributed.worker.worker_node
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Callable, Mapping, Protocol

from afritech.distributed.worker.worker_result import (
    WorkerResult,
    WorkerResultError,
    build_worker_result,
)

from afritech.distributed.api.queue import DistributedQueueRecord

from afritech.distributed.partition.partition_registry import (
    default_partition_registry,
)


# ============================================================
# EXCEPTION
# ============================================================

class WorkerNodeError(ValueError):
    pass


# ============================================================
# EXECUTOR
# ============================================================

class WorkerExecutor(Protocol):
    def __call__(self, record: DistributedQueueRecord) -> Mapping[str, object]:
        ...


# ============================================================
# IDENTITY
# ============================================================

@dataclass(frozen=True)
class WorkerIdentity:
    worker_id: str

    def __post_init__(self):
        _require_identity(self.worker_id, "worker_id")


# ============================================================
# ASSIGNMENT
# ============================================================

@dataclass(frozen=True)
class WorkerAssignment:
    worker_id: str
    partition_id: str
    assignment_hash: str

    def __post_init__(self):
        _require_identity(self.worker_id, "worker_id")
        _require_identity(self.partition_id, "partition_id")
        _require_sha256(self.assignment_hash, "assignment_hash")

    @classmethod
    def create(cls, *, worker_id: str, partition_id: str):
        payload = {
            "worker_id": worker_id,
            "partition_id": partition_id,
        }

        return cls(
            worker_id=worker_id,
            partition_id=partition_id,
            assignment_hash=_canonical_payload_hash(payload),
        )


# ============================================================
# RECEIPT
# ============================================================

@dataclass(frozen=True)
class WorkerExecutionReceipt:
    worker_id: str
    event_id: str
    partition_id: str
    partition_sequence: int
    replay_hash: str
    worker_receipt_hash: str


# ============================================================
# OUTCOME
# ============================================================

@dataclass(frozen=True)
class WorkerExecutionOutcome:
    result: WorkerResult
    receipt: WorkerExecutionReceipt

    def __post_init__(self):
        if self.result is None:
            raise WorkerNodeError("invalid result")

        for field in (
            "event_id",
            "partition_id",
            "partition_sequence",
            "replay_hash",
            "execution_hash",
        ):
            if not hasattr(self.result, field):
                raise WorkerNodeError(f"invalid result: missing {field}")


# ============================================================
# NODE ✅ FINAL (WITH FIX)
# ============================================================

class DeterministicWorkerNode:

    def __init__(
        self,
        *,
        identity: WorkerIdentity,
        assignments: tuple[WorkerAssignment, ...],
        executor: WorkerExecutor | Callable[[DistributedQueueRecord], Mapping[str, object]],
    ):
        if identity is None or not hasattr(identity, "worker_id"):
            raise WorkerNodeError("invalid identity")

        if not isinstance(assignments, tuple) or not assignments:
            raise WorkerNodeError("invalid assignments")

        if not callable(executor):
            raise WorkerNodeError("executor must be callable")

        partition_ids = [a.partition_id for a in assignments]
        if len(set(partition_ids)) != len(partition_ids):
            raise WorkerNodeError("duplicate partition assignments")

        self._identity = identity
        self._assignments = assignments
        self._executor = executor

        # ✅ REQUIRED FOR COORDINATOR
        self._partition_ids = tuple(sorted(partition_ids))

    @property
    def worker_id(self) -> str:
        return self._identity.worker_id

    @property
    def assigned_partition_ids(self) -> tuple[str, ...]:
        return self._partition_ids

    # ✅ ✅ ✅ CRITICAL FIX
    def can_execute(self, record: DistributedQueueRecord) -> bool:
        """
        Determines if this worker can process the record.

        Deterministic rule:
        Worker can execute only assigned partitions.
        """
        if record is None:
            return False

        if not hasattr(record, "partition_id"):
            return False

        return record.partition_id in self._partition_ids

    # ---------------------------------------------------------
    # EXECUTION
    # ---------------------------------------------------------

    def execute(self, record: DistributedQueueRecord) -> WorkerExecutionOutcome:

        self._require_assigned_record(record)

        try:
            output = self._executor(record)
        except Exception as exc:
            raise WorkerNodeError("executor failure") from exc

        if not isinstance(output, Mapping):
            raise WorkerNodeError("executor must return mapping")

        try:
            json.dumps(output, sort_keys=True)
        except Exception as exc:
            raise WorkerNodeError("output must be JSON-serializable") from exc

        try:
            result = build_worker_result(
                worker_id=self.worker_id,
                record=record,
                output_payload=output,
                normalized_input_hash=record.normalized_payload_hash,
                canonical_event_hash=record.canonical_event_hash,
            )
        except WorkerResultError as exc:
            raise WorkerNodeError("result build failed") from exc

        receipt = build_worker_execution_receipt(self.worker_id, result)

        return WorkerExecutionOutcome(result=result, receipt=receipt)

    def execute_many(
        self,
        records: tuple[DistributedQueueRecord, ...],
    ) -> tuple[WorkerExecutionOutcome, ...]:

        ordered = tuple(
            sorted(
                records,
                key=lambda r: (
                    r.partition_id,
                    r.sequence,
                    r.event_id,
                ),
            )
        )

        return tuple(self.execute(r) for r in ordered)

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------

    def _require_assigned_record(self, record):
        if record is None:
            raise WorkerNodeError("invalid record")

        required_fields = (
            "event_id",
            "partition_id",
            "sequence",
            "normalized_payload_hash",
            "canonical_event_hash",
            "assignment_hash",
        )

        for field in required_fields:
            if not hasattr(record, field):
                raise WorkerNodeError(f"invalid record: missing {field}")

        if record.partition_id not in self._partition_ids:
            raise WorkerNodeError(
                f"unassigned partition: {record.partition_id}"
            )


# ============================================================
# BUILDERS
# ============================================================

def build_worker_execution_receipt(
    worker_id: str,
    result: WorkerResult,
) -> WorkerExecutionReceipt:

    payload = {
        "worker_id": worker_id,
        "event_id": result.event_id,
        "partition_id": result.partition_id,
        "partition_sequence": result.partition_sequence,
        "replay_hash": result.replay_hash,
    }

    return WorkerExecutionReceipt(
        worker_id=worker_id,
        event_id=result.event_id,
        partition_id=result.partition_id,
        partition_sequence=result.partition_sequence,
        replay_hash=result.replay_hash,
        worker_receipt_hash=_canonical_payload_hash(payload),
    )


def build_worker_identity(worker_id: str) -> WorkerIdentity:
    return WorkerIdentity(worker_id=worker_id)


def build_worker_assignment(*, worker_id: str, partition_id: str) -> WorkerAssignment:
    return WorkerAssignment.create(worker_id=worker_id, partition_id=partition_id)


# ============================================================
# DEFAULT EXECUTOR
# ============================================================

def default_worker_executor(record: DistributedQueueRecord) -> Mapping[str, object]:
    return {
        "event_id": record.event_id,
        "partition_id": record.partition_id,
        "partition_sequence": record.sequence,
        "result": "accepted_for_replay_bound_execution",
    }


def build_default_worker_node(
    *,
    worker_id: str,
    partition_ids: tuple[str, ...] | None = None,
) -> DeterministicWorkerNode:

    if partition_ids is None:
        registry = default_partition_registry()
        partition_ids = registry.partition_ids

    if not partition_ids:
        raise WorkerNodeError("partition_ids required")

    identity = build_worker_identity(worker_id)

    assignments = tuple(
        build_worker_assignment(worker_id=worker_id, partition_id=p)
        for p in partition_ids
    )

    return DeterministicWorkerNode(
        identity=identity,
        assignments=assignments,
        executor=default_worker_executor,
    )


# ============================================================
# HELPERS
# ============================================================

def _canonical_payload_hash(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _require_identity(value: str, field: str):
    if not isinstance(value, str) or not value:
        raise WorkerNodeError(f"{field} invalid")

    if "/" in value or "\\" in value or ".." in value:
        raise WorkerNodeError(f"{field} contains invalid syntax")


def _require_sha256(value: str, field: str):
    if not isinstance(value, str) or len(value) != 64:
        raise WorkerNodeError(f"{field} must be sha256")

    try:
        int(value, 16)
    except ValueError:
        raise WorkerNodeError(f"{field} invalid sha256")
