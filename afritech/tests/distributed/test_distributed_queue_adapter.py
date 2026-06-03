"""
afritech.tests.distributed.test_distributed_queue_adapter

Tests for replay-safe distributed queue adapter.
"""

from __future__ import annotations

import hashlib
import pytest

from afritech.distributed.api.partition import (
    assign,
    get_default_registry,
)

from afritech.distributed.api.queue import (
    QueueAPIError,
    DistributedQueueError,
    InMemoryDistributedQueueAdapter,
    QueueSnapshot,
    create_record,
    create_inmemory_queue,
    publish,
    publish_many,
    consume_partition,
    peek_partition,
    queue_size,
    snapshot,
    queue_hash,
)


# ============================================================
# HELPERS ✅
# ============================================================

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _event(event_id: str, routing_key: str) -> dict[str, object]:
    return {
        "event_id": event_id,
        "routing_key": routing_key,
        "routing_scope": "rides",
        "payload": {
            "rider_id": f"rider.{event_id}",
            "pickup": "melbourne.cbd",
            "dropoff": "melbourne.airport",
        },
    }


def _record(
    *,
    event_id: str = "event.queue.001",
    routing_key: str = "ride.queue.001",
    sequence: int = 0,
):
    registry = get_default_registry()

    assignment = assign(
        routing_key=routing_key,
        routing_scope="rides",
        registry=registry,
    )

    return create_record(
        event_id=event_id,
        sequence=sequence,
        normalized_payload_hash=_sha256(f"normalized.{event_id}"),
        event=_event(event_id, routing_key),
        assignment=assignment,
        registry=registry,
    )


# ============================================================
# RECORD TESTS ✅
# ============================================================

def test_build_queue_record_is_hash_bound_and_canonical():
    record = _record()

    assert record.event_id == "event.queue.001"
    assert record.sequence == 0

    assert len(record.normalized_payload_hash) == 64
    assert len(record.canonical_event_hash) == 64
    assert len(record.assignment_hash) == 64
    assert len(record.record_hash()) == 64

    canonical = record.to_canonical_dict()

    assert canonical["event_id"] == record.event_id
    assert canonical["partition_id"] == record.partition_id
    assert canonical["sequence"] == record.sequence


# ============================================================
# QUEUE BEHAVIOR ✅
# ============================================================

def test_queue_publish_and_consume_preserves_fifo_order():
    registry = get_default_registry()
    queue = create_inmemory_queue(registry=registry)

    first = _record(sequence=0)

    second = create_record(
        event_id="event.queue.002",
        sequence=1,
        normalized_payload_hash=_sha256("normalized.event.queue.002"),
        event=_event("event.queue.002", "ride.queue.001"),
        assignment=assign(
            routing_key="ride.queue.001",
            routing_scope="rides",
            registry=registry,
        ),
        registry=registry,
    )

    publish(queue=queue, record=first)
    publish(queue=queue, record=second)

    consumed = consume_partition(
        queue=queue,
        partition_id=first.partition_id,
    )

    assert consumed == (first, second)


def test_peek_does_not_consume_records():
    queue = create_inmemory_queue(registry=get_default_registry())

    record = _record()

    publish(queue=queue, record=record)

    assert peek_partition(queue=queue, partition_id=record.partition_id) == (record,)
    assert queue_size(queue=queue, partition_id=record.partition_id) == 1


def test_snapshot_is_deterministic():
    queue = create_inmemory_queue(registry=get_default_registry())

    r1 = _record(sequence=0)
    r2 = _record(event_id="event.queue.002", sequence=1)

    publish_many(queue=queue, records=(r1, r2))

    s1 = snapshot(queue=queue)
    s2 = snapshot(queue=queue)

    assert isinstance(s1, QueueSnapshot)
    assert s1.records == s2.records
    assert s1.snapshot_hash() == s2.snapshot_hash()


# ============================================================
# SEQUENCE SAFETY ✅
# ============================================================

def test_duplicate_sequence_fails_closed():
    queue = create_inmemory_queue(registry=get_default_registry())

    first = _record(sequence=0)
    duplicate = _record(sequence=0)

    publish(queue=queue, record=first)

    with pytest.raises((DistributedQueueError, QueueAPIError)):
        publish(queue=queue, record=duplicate)


def test_non_contiguous_sequence_fails_closed():
    queue = create_inmemory_queue(registry=get_default_registry())

    with pytest.raises((DistributedQueueError, QueueAPIError)):
        publish(queue=queue, record=_record(sequence=1))


# ============================================================
# PARTITION SAFETY ✅
# ============================================================

def test_undeclared_partition_fails_closed():
    queue = create_inmemory_queue(registry=get_default_registry())

    with pytest.raises((DistributedQueueError, QueueAPIError)):
        consume_partition(
            queue=queue,
            partition_id="partition.invalid",
        )


# ============================================================
# BULK OPERATIONS ✅
# ============================================================

def test_publish_many_returns_records():
    queue = create_inmemory_queue(registry=get_default_registry())

    r1 = _record(sequence=0)
    r2 = _record(event_id="event.queue.002", sequence=1)

    published = publish_many(queue=queue, records=(r1, r2))

    assert published == (r1, r2)


def test_queue_size_total():
    queue = create_inmemory_queue(registry=get_default_registry())

    record = _record()

    publish(queue=queue, record=record)

    assert queue_size(queue=queue) == 1


# ============================================================
# CANONICAL HASH ✅
# ============================================================

def test_canonical_queue_hash_is_order_independent():
    r1 = _record(sequence=0)
    r2 = _record(event_id="event.queue.002", sequence=1)

    assert queue_hash(records=(r1, r2)) == queue_hash(records=(r2, r1))


# ============================================================
# INVALID INPUTS ✅
# ============================================================

def test_invalid_payload_hash_rejected():
    registry = get_default_registry()

    assignment = assign(
        routing_key="ride.queue.bad",
        routing_scope="rides",
        registry=registry,
    )

    with pytest.raises((DistributedQueueError, QueueAPIError)):
        create_record(
            event_id="event.bad",
            sequence=0,
            normalized_payload_hash="bad",
            event=_event("event.bad", "ride.queue.bad"),
            assignment=assignment,
            registry=registry,
        )


def test_negative_sequence_rejected():
    with pytest.raises((DistributedQueueError, QueueAPIError)):
        _record(sequence=-1)


# ============================================================
# EXTRA HARDENING ✅ (CRITICAL)
# ============================================================

def test_queue_hash_changes_when_content_changes():
    r1 = _record(sequence=0)
    r2 = _record(event_id="event.queue.002", sequence=1)

    r3 = _record(event_id="event.queue.003", sequence=2)

    assert queue_hash(records=(r1, r2)) != queue_hash(records=(r1, r3))


def test_consume_reduces_queue_size():
    queue = create_inmemory_queue(registry=get_default_registry())

    r = _record()

    publish(queue=queue, record=r)

    consume_partition(queue=queue, partition_id=r.partition_id)

    assert queue_size(queue=queue, partition_id=r.partition_id) == 0


def test_peek_then_consume_consistency():
    queue = create_inmemory_queue(registry=get_default_registry())

    r = _record()

    publish(queue=queue, record=r)

    peeked = peek_partition(queue=queue, partition_id=r.partition_id)
    consumed = consume_partition(queue=queue, partition_id=r.partition_id)

    assert peeked == consumed


def test_snapshot_matches_queue_hash():
    queue = create_inmemory_queue(registry=get_default_registry())

    r1 = _record(sequence=0)
    r2 = _record(event_id="event.queue.002", sequence=1)

    publish_many(queue=queue, records=(r1, r2))

    snap = snapshot(queue=queue)

    assert snap.snapshot_hash() == queue_hash(records=snap.records)