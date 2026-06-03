"""
afritech.ci.distributed_queue_validator

CI validator for AfriTech distributed queue layer.

This validator enforces that distributed queue behavior remains:
- deterministic
- replay-safe
- partition-isolated
- sequence-consistent
- canonically ordered
- free from hidden mutation or nondeterminism

Constitutional boundary:
- Queue defines execution order, not execution truth.
- Queue must remain replay-reconstructable.
"""

from __future__ import annotations

from dataclasses import dataclass
import sys

from afritech.distributed.partition.partition_registry import (
    default_partition_registry,
    PartitionRegistryError,
)

from afritech.distributed.partition.partition_assignment import (
    assign_partition,
    PartitionAssignmentError,
)

from afritech.distributed.queue.distributed_queue_adapter import (
    InMemoryDistributedQueueAdapter,
    DistributedQueueError,
    build_queue_record,
    canonical_queue_hash,
)


# ============================================================
# ERROR
# ============================================================

class DistributedQueueValidatorError(ValueError):
    pass


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class DistributedQueueValidationResult:
    passed: bool
    checked_records: int
    checked_operations: int
    failures: tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Distributed queue validation PASSED\n"
                f"✅ Checked records: {self.checked_records}\n"
                f"✅ Checked operations: {self.checked_operations}"
            )

        return (
            "❌ Distributed queue validation FAILED\n"
            f"❌ Checked records: {self.checked_records}\n"
            f"❌ Checked operations: {self.checked_operations}\n"
            + "\n".join(f" - {f}" for f in self.failures)
        )


# ============================================================
# HELPERS
# ============================================================

def _event(event_id: str, routing_key: str) -> dict:
    return {
        "event_id": event_id,
        "routing_key": routing_key,
        "routing_scope": "rides",
        "payload": {"value": event_id},
    }


def _hash(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode()).hexdigest()


# ============================================================
# RECORD VALIDATION ✅
# ============================================================

def validate_queue_record_building():
    failures = []
    checked = 0

    try:
        registry = default_partition_registry()
    except PartitionRegistryError as exc:
        return 0, (f"registry invalid: {exc}",)

    try:
        assignment = assign_partition(
            routing_key="ride.validation.001",
            routing_scope="rides",
            registry=registry,
        )
    except PartitionAssignmentError as exc:
        return 0, (f"assignment failed: {exc}",)

    checked += 1

    try:
        record = build_queue_record(
            event_id="event.validation.001",
            sequence=0,
            normalized_payload_hash=_hash("payload"),
            event=_event("event.validation.001", "ride.validation.001"),
            assignment=assignment,
            registry=registry,
        )

        if len(record.record_hash()) != 64:
            failures.append("record hash invalid length")

        # ✅ determinism
        r2 = build_queue_record(
            event_id="event.validation.001",
            sequence=0,
            normalized_payload_hash=_hash("payload"),
            event=_event("event.validation.001", "ride.validation.001"),
            assignment=assignment,
            registry=registry,
        )

        if record != r2:
            failures.append("record building not deterministic")

    except Exception as exc:
        failures.append(f"record build failed: {exc}")

    return checked, tuple(failures)


# ============================================================
# QUEUE EXECUTION ✅ FIXED
# ============================================================

def validate_queue_execution():
    failures = []
    checked = 0

    try:
        registry = default_partition_registry()
        queue = InMemoryDistributedQueueAdapter(registry)
    except Exception as exc:
        return 0, (f"queue init failed: {exc}",)

    try:
        # ✅ CRITICAL FIX: FORCE SAME PARTITION
        routing_key = "ride.execution.shared"

        assignment = assign_partition(
            routing_key=routing_key,
            routing_scope="rides",
            registry=registry,
        )

        r1 = build_queue_record(
            event_id="event.execution.001",
            sequence=0,
            normalized_payload_hash=_hash("p1"),
            event=_event("event.execution.001", routing_key),
            assignment=assignment,
            registry=registry,
        )

        r2 = build_queue_record(
            event_id="event.execution.002",
            sequence=1,
            normalized_payload_hash=_hash("p2"),
            event=_event("event.execution.002", routing_key),
            assignment=assignment,  # ✅ SAME PARTITION
            registry=registry,
        )

        checked += 2

        queue.publish(r1)
        queue.publish(r2)

        consumed = queue.consume_partition(r1.partition_id)

        if consumed != (r1, r2):
            failures.append("FIFO order violated")

    except Exception as exc:
        failures.append(f"queue execution failed: {exc}")

    return checked, tuple(failures)


# ============================================================
# SEQUENCE VALIDATION ✅
# ============================================================

def validate_sequence_rules():
    failures = []
    checked = 0

    registry = default_partition_registry()
    queue = InMemoryDistributedQueueAdapter(registry)

    routing_key = "ride.seq.shared"

    a = assign_partition(
        routing_key=routing_key,
        routing_scope="rides",
        registry=registry,
    )

    r1 = build_queue_record(
        event_id="event.seq.001",
        sequence=0,
        normalized_payload_hash=_hash("p1"),
        event=_event("event.seq.001", routing_key),
        assignment=a,
        registry=registry,
    )

    queue.publish(r1)
    checked += 1

    # duplicate
    try:
        queue.publish(r1)
        failures.append("duplicate sequence accepted")
    except DistributedQueueError:
        pass

    # gap
    try:
        r2 = build_queue_record(
            event_id="event.seq.002",
            sequence=2,
            normalized_payload_hash=_hash("p2"),
            event=_event("event.seq.002", routing_key),
            assignment=a,
            registry=registry,
        )
        queue.publish(r2)
        failures.append("sequence gap accepted")
    except DistributedQueueError:
        pass

    return checked, tuple(failures)


# ============================================================
# HASH CONSISTENCY ✅
# ============================================================

def validate_queue_hashing():
    failures = []
    checked = 0

    registry = default_partition_registry()
    queue = InMemoryDistributedQueueAdapter(registry)

    routing_key = "ride.hash.shared"

    a = assign_partition(
        routing_key=routing_key,
        routing_scope="rides",
        registry=registry,
    )

    r1 = build_queue_record(
        event_id="event.hash.001",
        sequence=0,
        normalized_payload_hash=_hash("p1"),
        event=_event("event.hash.001", routing_key),
        assignment=a,
        registry=registry,
    )

    r2 = build_queue_record(
        event_id="event.hash.002",
        sequence=1,
        normalized_payload_hash=_hash("p2"),
        event=_event("event.hash.002", routing_key),
        assignment=a,
        registry=registry,
    )

    queue.publish(r1)
    queue.publish(r2)

    snap1 = queue.snapshot()
    snap2 = queue.snapshot()

    checked += 2

    if snap1.snapshot_hash() != snap2.snapshot_hash():
        failures.append("snapshot hash not deterministic")

    if canonical_queue_hash(snap1.records) != canonical_queue_hash(snap2.records):
        failures.append("queue hash not deterministic")

    return checked, tuple(failures)


# ============================================================
# ROOT VALIDATOR
# ============================================================

def validate_distributed_queue() -> DistributedQueueValidationResult:

    r_checked, r_failures = validate_queue_record_building()
    e_checked, e_failures = validate_queue_execution()
    s_checked, s_failures = validate_sequence_rules()
    h_checked, h_failures = validate_queue_hashing()

    failures = r_failures + e_failures + s_failures + h_failures

    return DistributedQueueValidationResult(
        passed=(len(failures) == 0),
        checked_records=r_checked,
        checked_operations=e_checked + s_checked + h_checked,
        failures=failures,
    )


# ============================================================
# CLI
# ============================================================

def main() -> int:
    result = validate_distributed_queue()
    print(result.report())
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())