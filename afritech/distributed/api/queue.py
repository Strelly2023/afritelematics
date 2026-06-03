"""
afritech.distributed.api.queue

🔒 OPERATIVE SURFACE

Approved public interface for distributed queue operations.
"""

from __future__ import annotations

from typing import Iterable


# ============================================================
# INTERNAL IMPORTS (CONTROLLED)
# ============================================================

from afritech.distributed.queue.distributed_queue_adapter import (
    DistributedQueueAdapter,
    DistributedQueueError as _QueueError,
    DistributedQueueError,  # ✅ exposed
    InMemoryDistributedQueueAdapter,
    QueueSnapshot,
    canonical_queue_hash as _canonical_queue_hash,
    DistributedQueueRecord,
    build_queue_record as _build_queue_record,
)


# ============================================================
# API ERROR
# ============================================================

class QueueAPIError(ValueError):
    """Raised when API-level queue constraints are violated."""


# ============================================================
# SAFE EXECUTOR
# ============================================================

def _execute(fn, error_message: str):
    try:
        return fn()
    except Exception as exc:
        raise QueueAPIError(error_message) from exc


# ============================================================
# SAFE RECORD CONSTRUCTION ✅
# ============================================================

def create_record(
    *,
    event_id: str,
    sequence: int,
    normalized_payload_hash: str,
    event,
    assignment,
    registry,
) -> DistributedQueueRecord:

    if assignment is None:
        raise QueueAPIError("assignment required")

    if registry is None:
        raise QueueAPIError("registry required")

    return _execute(
        lambda: _build_queue_record(
            event_id=event_id,
            sequence=sequence,
            normalized_payload_hash=normalized_payload_hash,
            event=event,
            assignment=assignment,
            registry=registry,
        ),
        "record creation failed",
    )


# ✅ ✅ ✅ BACKWARD COMPATIBILITY (CRITICAL FOR CI)
def build_queue_record(
    *,
    event_id: str,
    sequence: int,
    normalized_payload_hash: str,
    event,
    assignment,
    registry,
) -> DistributedQueueRecord:
    """
    Compatibility wrapper for legacy + CI usage.

    Delegates to create_record().
    """
    return create_record(
        event_id=event_id,
        sequence=sequence,
        normalized_payload_hash=normalized_payload_hash,
        event=event,
        assignment=assignment,
        registry=registry,
    )


# ============================================================
# QUEUE FACTORY
# ============================================================

def create_inmemory_queue(
    *,
    registry,
) -> DistributedQueueAdapter:

    if registry is None:
        raise QueueAPIError("registry required")

    return InMemoryDistributedQueueAdapter(registry)


# ============================================================
# SAFE PUBLISH OPERATIONS
# ============================================================

def publish(
    *,
    queue: DistributedQueueAdapter,
    record: DistributedQueueRecord,
) -> DistributedQueueRecord:

    if queue is None:
        raise QueueAPIError("queue required")

    return _execute(
        lambda: queue.publish(record),
        "publish failed",
    )


def publish_many(
    *,
    queue: DistributedQueueAdapter,
    records: Iterable[DistributedQueueRecord],
):

    if queue is None:
        raise QueueAPIError("queue required")

    if records is None:
        raise QueueAPIError("records required")

    return _execute(
        lambda: queue.publish_many(records),
        "publish_many failed",
    )


# ============================================================
# SAFE CONSUMPTION
# ============================================================

def consume_partition(
    *,
    queue: DistributedQueueAdapter,
    partition_id: str,
    limit: int | None = None,
):

    if queue is None:
        raise QueueAPIError("queue required")

    return _execute(
        lambda: queue.consume_partition(partition_id, limit),
        "consume_partition failed",
    )


def peek_partition(
    *,
    queue: DistributedQueueAdapter,
    partition_id: str,
    limit: int | None = None,
):

    if queue is None:
        raise QueueAPIError("queue required")

    return _execute(
        lambda: queue.peek_partition(partition_id, limit),
        "peek_partition failed",
    )


# ============================================================
# SNAPSHOT + HASH
# ============================================================

def snapshot(
    *,
    queue: DistributedQueueAdapter,
) -> QueueSnapshot:

    if queue is None:
        raise QueueAPIError("queue required")

    return _execute(
        lambda: queue.snapshot(),
        "snapshot failed",
    )


def queue_hash(
    *,
    records: Iterable[DistributedQueueRecord],
) -> str:

    if records is None:
        raise QueueAPIError("records required")

    return _execute(
        lambda: _canonical_queue_hash(records),
        "queue_hash failed",
    )


# ============================================================
# QUEUE INSPECTION
# ============================================================

def queue_size(
    *,
    queue: DistributedQueueAdapter,
    partition_id: str | None = None,
) -> int:

    if queue is None:
        raise QueueAPIError("queue required")

    try:
        if hasattr(queue, "queue_size"):
            return queue.queue_size(partition_id)

        raise QueueAPIError("queue does not support size inspection")

    except Exception as exc:
        raise QueueAPIError("queue_size failed") from exc


# ============================================================
# PUBLIC EXPORTS ✅ FIXED
# ============================================================

__all__ = [
    # ✅ adapter
    "DistributedQueueAdapter",
    "InMemoryDistributedQueueAdapter",

    # ✅ record API
    "create_record",
    "build_queue_record",      # ✅ CRITICAL FIX

    # ✅ queue ops
    "create_inmemory_queue",
    "publish",
    "publish_many",
    "consume_partition",
    "peek_partition",
    "snapshot",
    "queue_hash",
    "queue_size",

    # ✅ models
    "DistributedQueueRecord",
    "QueueSnapshot",

    # ✅ errors
    "DistributedQueueError",
    "QueueAPIError",
]