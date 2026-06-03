"""
afritech.tests.distributed.test_batch_coordinator

Tests for deterministic distributed batch coordination.
"""

from __future__ import annotations

import hashlib
import pytest

# ✅ API IMPORTS ONLY
from afritech.distributed.api.coordinator import (
    BatchCoordinatorError,
    BatchCoordinationReport,
    BatchPlan,
    DeterministicBatchCoordinator,
    build_batch_plan,
    CoordinationBatch,
    DistributedCoordinator,
)

from afritech.distributed.api.partition import (
    assign_partition,
    default_partition_registry,
)

from afritech.distributed.api.queue import (
    DistributedQueueRecord,
    build_queue_record,
)

from afritech.distributed.api.worker import build_default_worker_node


# ============================================================
# HELPERS
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
    event_id: str,
    routing_key: str,
    sequence: int,
) -> DistributedQueueRecord:

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


def _records(count: int = 4) -> tuple[DistributedQueueRecord, ...]:
    return tuple(
        _record(
            event_id=f"event.batch.{i:03d}",
            routing_key=f"ride.batch.{i:03d}",
            sequence=i,
        )
        for i in range(count)
    )


# ✅ ✅ ✅ FIXED COORDINATOR
def _coordinator() -> DistributedCoordinator:

    registry = default_partition_registry()

    worker = build_default_worker_node(
        worker_id="afritech.distributed.worker.node.worker_01",
        # ✅ CRITICAL FIX — worker handles ALL partitions
        partition_ids=registry.partition_ids,
    )

    return DistributedCoordinator(workers=(worker,))


# ============================================================
# TESTS
# ============================================================

def test_build_batch_plan_splits_records_by_max_batch_size():
    records = _records(5)

    plan = build_batch_plan(records=records, max_batch_size=2)

    assert isinstance(plan, BatchPlan)
    assert len(plan.batches) == 3
    assert [len(batch.records) for batch in plan.batches] == [2, 2, 1]


def test_build_batch_plan_is_deterministic_independent_of_input_order():
    records = _records(4)

    forward = build_batch_plan(records=records, max_batch_size=2)
    reverse = build_batch_plan(records=tuple(reversed(records)), max_batch_size=2)

    assert forward.plan_hash() == reverse.plan_hash()
    assert forward.to_canonical_dict() == reverse.to_canonical_dict()


def test_batch_plan_rejects_empty_records():
    with pytest.raises(BatchCoordinatorError):
        build_batch_plan(records=(), max_batch_size=2)


def test_batch_plan_rejects_invalid_max_batch_size():
    with pytest.raises(BatchCoordinatorError):
        build_batch_plan(records=_records(2), max_batch_size=0)


def test_batch_plan_hash_is_stable():
    plan = build_batch_plan(records=_records(3), max_batch_size=2)

    assert len(plan.plan_hash()) == 64
    assert plan.plan_hash() == plan.plan_hash()


def test_coordination_batch_create_is_canonical():
    records = _records(3)

    batch = CoordinationBatch.create(tuple(reversed(records)))

    assert isinstance(batch, CoordinationBatch)

    expected = tuple(
        sorted(
            records,
            key=lambda r: (
                r.partition_id,
                r.sequence,
                r.event_id,
                r.record_hash(),
            ),
        )
    )

    assert batch.records == expected

    assert batch.batch_id.startswith("batch.")
    assert len(batch.batch_hash()) == 64


def test_deterministic_batch_coordinator_builds_plan():
    coordinator = DeterministicBatchCoordinator(
        coordinator=_coordinator(),
        max_batch_size=2,
    )

    plan = coordinator.build_plan(_records(5))

    assert isinstance(plan, BatchPlan)
    assert len(plan.batches) == 3


def test_coordinate_records_produces_report():
    coordinator = DeterministicBatchCoordinator(
        coordinator=_coordinator(),
        max_batch_size=2,
    )

    report = coordinator.coordinate_records(_records(4))

    assert isinstance(report, BatchCoordinationReport)
    assert len(report.coordination_results) == 2
    assert len(report.report_hash) == 64


def test_coordinate_records_verified_succeeds():
    coordinator = DeterministicBatchCoordinator(
        coordinator=_coordinator(),
        max_batch_size=2,
    )

    report = coordinator.coordinate_records_verified(_records(4))

    assert report.verified is True
    assert report.status == "VERIFIED"


def test_coordinate_records_is_deterministic():
    coordinator = DeterministicBatchCoordinator(
        coordinator=_coordinator(),
        max_batch_size=2,
    )

    records = _records(4)

    a = coordinator.coordinate_records(records)
    b = coordinator.coordinate_records(tuple(reversed(records)))

    assert a.report_hash == b.report_hash
    assert a.plan_hash == b.plan_hash


def test_coordinate_records_rejects_invalid_coordinator():
    with pytest.raises(BatchCoordinatorError):
        DeterministicBatchCoordinator(coordinator=None, max_batch_size=2)


def test_coordinate_records_verified_fails_on_invalid_replay():
    class BadCoordinator:
        def coordinate(self, records):
            raise Exception("forced failure")

    coordinator = DeterministicBatchCoordinator(
        coordinator=BadCoordinator(),
        max_batch_size=2,
    )

    with pytest.raises(BatchCoordinatorError):
        coordinator.coordinate_records(_records(2))