"""
afritech.tests.distributed.test_worker_node

Tests for deterministic distributed worker node execution.
"""

from __future__ import annotations

import hashlib
import pytest

from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record

from afritech.distributed.worker.worker_node import (
    DeterministicWorkerNode,
    WorkerAssignment,
    WorkerExecutionOutcome,
    WorkerNodeError,
    build_default_worker_node,
    build_worker_assignment,
    build_worker_execution_receipt,
    build_worker_identity,
    default_worker_executor,
)

from afritech.distributed.worker.worker_result import require_worker_results


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
    event_id: str = "event.worker.001",
    routing_key: str = "ride.worker.shared",  # ✅ stable partition
    sequence: int = 0,
):
    registry = default_partition_registry()

    assignment = assign_partition(
        routing_key=routing_key,
        routing_scope="rides",
        registry=registry,
    )

    return build_queue_record(
        event_id=event_id,
        sequence=sequence,
        normalized_payload_hash=_sha256(f"normalized.{event_id}"),
        event=_event(event_id, routing_key),
        assignment=assignment,
        registry=registry,
    )


# ============================================================
# TESTS ✅
# ============================================================

def test_worker_assignment_is_deterministic():
    a = build_worker_assignment(
        worker_id="worker_01",
        partition_id="partition.rides.region_01",
    )

    b = build_worker_assignment(
        worker_id="worker_01",
        partition_id="partition.rides.region_01",
    )

    assert isinstance(a, WorkerAssignment)
    assert a == b
    assert len(a.assignment_hash) == 64


def test_executor_must_return_mapping():
    identity = build_worker_identity("worker_01")

    assignment = build_worker_assignment(
        worker_id="worker_01",
        partition_id="partition.rides.region_01",
    )

    worker = DeterministicWorkerNode(
        identity=identity,
        assignments=(assignment,),
        executor=lambda _: "bad",
    )

    with pytest.raises(WorkerNodeError):
        worker.execute(_record())


def test_executor_failure_is_wrapped():
    identity = build_worker_identity("worker_01")

    assignment = build_worker_assignment(
        worker_id="worker_01",
        partition_id="partition.rides.region_01",
    )

    def failing(_):
        raise RuntimeError("boom")

    worker = DeterministicWorkerNode(
        identity=identity,
        assignments=(assignment,),
        executor=failing,
    )

    with pytest.raises(WorkerNodeError):
        worker.execute(_record())


def test_non_serializable_output_rejected():
    record = _record()

    identity = build_worker_identity("worker_01")

    assignment = build_worker_assignment(
        worker_id="worker_01",
        partition_id=record.partition_id,
    )

    worker = DeterministicWorkerNode(
        identity=identity,
        assignments=(assignment,),
        executor=lambda _: {"bad": object()},
    )

    # ✅ FIX: error is wrapped into WorkerNodeError
    with pytest.raises(WorkerNodeError):
        worker.execute(record)


def test_worker_constructor_validation():
    identity = build_worker_identity("worker_01")

    with pytest.raises(WorkerNodeError):
        DeterministicWorkerNode(
            identity=identity,
            assignments=(),
            executor=default_worker_executor,
        )

    wrong = build_worker_assignment(
        worker_id="worker_02",
        partition_id="partition.rides.region_01",
    )

    worker = DeterministicWorkerNode(
        identity=identity,
        assignments=(wrong,),
        executor=default_worker_executor,
    )

    assert worker.assigned_partition_ids


def test_build_default_worker_requires_partitions():
    with pytest.raises(WorkerNodeError):
        build_default_worker_node(
            worker_id="worker_01",
            partition_ids=(),
        )


def test_worker_executes_and_receipt_matches():
    record = _record()

    worker = build_default_worker_node(
        worker_id="worker_01",
        partition_ids=(record.partition_id,),
    )

    outcome = worker.execute(record)

    assert isinstance(outcome, WorkerExecutionOutcome)

    result = outcome.result

    receipt = build_worker_execution_receipt(
        worker_id=result.worker_id,
        result=result,
    )

    assert receipt == outcome.receipt
    assert receipt.replay_hash == result.replay_hash
    assert len(receipt.worker_receipt_hash) == 64

    require_worker_results([result])


def test_worker_execution_is_deterministic():
    record = _record()

    worker = build_default_worker_node(
        worker_id="worker_01",
        partition_ids=(record.partition_id,),
    )

    a = worker.execute(record)
    b = worker.execute(record)

    assert a.result == b.result
    assert a.receipt == b.receipt


def test_execute_many_orders_records_canonically():
    first = _record(event_id="event.worker.001", sequence=0)
    second = _record(event_id="event.worker.002", sequence=1)

    worker = build_default_worker_node(
        worker_id="worker_01",
        partition_ids=(first.partition_id,),
    )

    outcomes = worker.execute_many((second, first))

    assert tuple(o.result.event_id for o in outcomes) == (
        "event.worker.001",
        "event.worker.002",
    )