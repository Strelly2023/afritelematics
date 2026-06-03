"""
afritech.distributed.api.worker

🔒 OPERATIVE SURFACE

Approved public interface for distributed worker execution.

All consumers MUST import from this module instead of internal
worker modules.

Ensures:
- constitutional import topology compliance
- deterministic execution boundary
- stable worker abstraction layer
"""

from __future__ import annotations


# ============================================================
# INTERNAL IMPORTS (CONTROLLED)
# ============================================================

from afritech.distributed.worker.worker_result import (
    WorkerResult,
    build_worker_result as _build_worker_result,
)

from afritech.distributed.worker.worker_node import (
    WorkerIdentity,
    WorkerAssignment,
    WorkerExecutor,
    WorkerNodeError,
    DeterministicWorkerNode,
    WorkerExecutionOutcome,
    build_worker_identity,
    build_worker_assignment,
    build_worker_execution_receipt,
    default_worker_executor,
)

from afritech.distributed.partition.partition_registry import (
    default_partition_registry,
)


# ============================================================
# API ERROR
# ============================================================

class WorkerAPIError(ValueError):
    """Raised when API-level worker constraints are violated."""


# ============================================================
# SAFE RESULT BUILDER ✅
# ============================================================

def build_result(
    *,
    worker_id: str,
    record,
    output_payload,
) -> WorkerResult:
    """
    Safe API wrapper around WorkerResult builder.

    Guarantees:
    - deterministic construction
    - replay-safe output
    - validated record binding
    """

    if worker_id is None:
        raise WorkerAPIError("worker_id required")

    if record is None:
        raise WorkerAPIError("record required")

    if output_payload is None:
        raise WorkerAPIError("output_payload required")

    try:
        return _build_worker_result(
            worker_id=worker_id,
            record=record,
            output_payload=output_payload,
            normalized_input_hash=record.normalized_payload_hash,
            canonical_event_hash=record.canonical_event_hash,
        )
    except Exception as exc:
        raise WorkerAPIError("build_result failed") from exc


# ============================================================
# SAFE WORKER CREATION ✅
# ============================================================

def create_worker(
    *,
    worker_id: str,
    partition_ids: tuple[str, ...] | None = None,
    executor: WorkerExecutor | None = None,
) -> DeterministicWorkerNode:
    """
    Safe worker node factory.

    Guarantees:
    - explicit identity
    - deterministic partition assignment
    - valid executor binding
    """

    if worker_id is None:
        raise WorkerAPIError("worker_id required")

    if partition_ids is None:
        registry = default_partition_registry()
        partition_ids = registry.partition_ids

    if not partition_ids:
        raise WorkerAPIError("partition_ids required")

    identity = build_worker_identity(worker_id=worker_id)

    assignments = tuple(
        build_worker_assignment(
            worker_id=worker_id,
            partition_id=p,
        )
        for p in partition_ids
    )

    exec_fn = executor or default_worker_executor

    if not callable(exec_fn):
        raise WorkerAPIError("executor must be callable")

    return DeterministicWorkerNode(
        identity=identity,
        assignments=assignments,
        executor=exec_fn,
    )


# ============================================================
# SAFE EXECUTION ✅
# ============================================================

def execute(
    *,
    worker: DeterministicWorkerNode,
    record,
) -> WorkerExecutionOutcome:
    """
    Execute a single record safely.
    """

    if worker is None:
        raise WorkerAPIError("worker required")

    if record is None:
        raise WorkerAPIError("record required")

    try:
        return worker.execute(record)
    except Exception as exc:
        raise WorkerAPIError("execution failed") from exc


def execute_many(
    *,
    worker: DeterministicWorkerNode,
    records: tuple,
) -> tuple[WorkerExecutionOutcome, ...]:
    """
    Execute multiple records with canonical ordering.
    """

    if worker is None:
        raise WorkerAPIError("worker required")

    if records is None:
        raise WorkerAPIError("records required")

    try:
        return worker.execute_many(records)
    except Exception as exc:
        raise WorkerAPIError("execution_many failed") from exc


# ============================================================
# SAFE DEFAULT BUILDER ✅
# ============================================================

def build_default_worker_node(
    *,
    worker_id: str,
    partition_ids: tuple[str, ...] | None = None,
) -> DeterministicWorkerNode:
    """
    Safe public builder.

    If partition_ids is not provided, automatically assigns
    all partitions from the default registry.

    Prevents unassigned partition execution errors.
    """

    if worker_id is None:
        raise WorkerAPIError("worker_id required")

    if partition_ids is None:
        registry = default_partition_registry()
        partition_ids = registry.partition_ids

    # lazy import to preserve boundary discipline
    from afritech.distributed.worker.worker_node import (
        build_default_worker_node as _build_internal,
    )

    return _build_internal(
        worker_id=worker_id,
        partition_ids=partition_ids,
    )


# ============================================================
# PUBLIC EXPORTS (CANONICAL)
# ============================================================

__all__ = [
    # --- API builders ---
    "build_result",
    "create_worker",
    "execute",
    "execute_many",
    "build_default_worker_node",

    # --- result model ---
    "WorkerResult",

    # --- core ---
    "WorkerIdentity",
    "WorkerAssignment",
    "WorkerExecutor",
    "WorkerNodeError",

    # --- execution ---
    "DeterministicWorkerNode",
    "WorkerExecutionOutcome",

    # --- helpers ---
    "build_worker_identity",
    "build_worker_assignment",
    "build_worker_execution_receipt",
    "default_worker_executor",

    # --- API error ---
    "WorkerAPIError",
]