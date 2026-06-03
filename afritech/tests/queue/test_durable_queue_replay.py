from __future__ import annotations

import pytest

from afritech.ci.durable_queue_validator import run_durable_queue_proof
from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record
from afritech.execution.queue.durable_queue import (
    AUTHORITY_DISCLAIMER,
    DurableQueueAdapter,
    DurableQueueError,
    restore_durable_queue,
)


def _record(event_id: str = "durable.test.001", sequence: int = 0):
    registry = default_partition_registry()
    assignment = assign_partition(
        routing_key="ride.durable.test",
        routing_scope="rides",
        registry=registry,
    )
    event = {
        "event_id": event_id,
        "payload": {"rider_id": "rider.durable"},
        "routing_key": "ride.durable.test",
        "routing_scope": "rides",
    }
    return registry, build_queue_record(
        event_id=event_id,
        sequence=sequence,
        normalized_payload_hash="a" * 64,
        event=event,
        assignment=assignment,
        registry=registry,
    )


def test_durable_queue_restore_preserves_delivery_hash():
    registry, record = _record()
    queue = DurableQueueAdapter(registry=registry)

    queue.publish(record)
    restored = restore_durable_queue(registry=registry, rows=queue.backend.rows())

    assert restored.delivery_hash() == queue.delivery_hash()
    assert restored.peek_partition(record.partition_id) == (record,)


def test_durable_queue_rows_include_non_authoritative_disclaimer():
    registry, record = _record()
    queue = DurableQueueAdapter(registry=registry)

    queue.publish(record)
    row = queue.backend.rows()[0]

    assert row["authority_disclaimer"] == AUTHORITY_DISCLAIMER
    assert "replay log remains authority" in row["authority_disclaimer"]


def test_durable_queue_rejects_tampered_row_on_restore():
    registry, record = _record()
    queue = DurableQueueAdapter(registry=registry)
    queue.publish(record)
    row = dict(queue.backend.rows()[0])
    row["record"] = dict(row["record"])
    row["record"]["event_id"] = "durable.tampered"

    with pytest.raises(DurableQueueError, match="record hash mismatch"):
        restore_durable_queue(registry=registry, rows=(row,))


def test_durable_queue_rejects_duplicate_delivery_record():
    registry, record = _record()
    queue = DurableQueueAdapter(registry=registry)
    queue.publish(record)

    with pytest.raises(DurableQueueError, match="duplicate durable queue record"):
        queue.publish(record)


def test_durable_queue_validator_report_is_verified():
    report = run_durable_queue_proof()

    assert report.verified is True
    assert report.delivery_hash == report.restored_delivery_hash
    assert report.mutation_rejected is True
    assert report.duplicate_rejected is True
    assert len(report.report_hash()) == 64
