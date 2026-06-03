"""
afritech.ci.distributed_coordinator_validator

CI validator for distributed coordination layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import sys
from typing import Any


# ✅ API ONLY IMPORTS
from afritech.distributed.api.coordinator import (
    DistributedCoordinator,
    DeterministicBatchCoordinator,
    build_batch_plan,
    BatchCoordinatorError,
)

from afritech.distributed.api.partition import (
    assign_partition,
    default_partition_registry,
)

from afritech.distributed.api.queue import build_queue_record

from afritech.distributed.api.worker import build_default_worker_node


# ============================================================
# ERROR
# ============================================================

class DistributedCoordinatorValidatorError(ValueError):
    pass


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class DistributedCoordinatorValidationResult:
    passed: bool
    checked: int
    failures: tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Distributed coordinator validation PASSED\n"
                f"✅ Checks executed: {self.checked}"
            )

        return (
            "❌ Distributed coordinator validation FAILED\n"
            f"❌ Checks executed: {self.checked}\n"
            + "\n".join(f" - {f}" for f in self.failures)
        )


# ============================================================
# VALIDATOR
# ============================================================

def validate_distributed_coordinator() -> DistributedCoordinatorValidationResult:

    failures: list[str] = []
    checked = 0

    # ---------------------------------------------------------
    # SETUP ✅ FIXED
    # ---------------------------------------------------------

    try:
        registry = default_partition_registry()

        # ✅ CRITICAL FIX: worker supports ALL partitions
        worker = build_default_worker_node(
            worker_id="afritech.distributed.worker.node.worker_01",
            partition_ids=registry.partition_ids,
        )

        coordinator = DistributedCoordinator(workers=(worker,))

        batch_coordinator = DeterministicBatchCoordinator(
            coordinator=coordinator,
            max_batch_size=2,
        )

    except Exception as exc:
        return DistributedCoordinatorValidationResult(
            passed=False,
            checked=0,
            failures=(f"setup failed: {exc}",),
        )

    # ---------------------------------------------------------
    # RECORDS
    # ---------------------------------------------------------

    try:
        records = tuple(
            _record(
                event_id=f"event.coordinator.{i:03d}",
                routing_key=f"ride.coordinator.{i:03d}",
                sequence=i,
                registry=registry,
            )
            for i in range(4)
        )
    except Exception as exc:
        return DistributedCoordinatorValidationResult(
            passed=False,
            checked=0,
            failures=(f"record creation failed: {exc}",),
        )

    # ---------------------------------------------------------
    # TEST 1 — PLAN CREATION
    # ---------------------------------------------------------

    checked += 1
    try:
        plan = build_batch_plan(records=records, max_batch_size=2)

        if not getattr(plan, "batches", None):
            failures.append("empty batch plan")

    except Exception as exc:
        failures.append(f"plan creation failed: {exc}")

    # ---------------------------------------------------------
    # TEST 2 — COORDINATION SUCCESS
    # ---------------------------------------------------------

    checked += 1
    try:
        report = batch_coordinator.coordinate_records(records)

        if not getattr(report, "coordination_results", None):
            failures.append("no coordination results")

    except Exception as exc:
        failures.append(f"coordination failed: {exc}")

    # ---------------------------------------------------------
    # TEST 3 — VERIFIED EXECUTION
    # ---------------------------------------------------------

    checked += 1
    try:
        verified = batch_coordinator.coordinate_records_verified(records)

        if not getattr(verified, "verified", False):
            failures.append("verification did not pass")

    except BatchCoordinatorError as exc:
        failures.append(f"verified coordination failed: {exc}")

    except Exception as exc:
        failures.append(f"unexpected verification failure: {exc}")

    # ---------------------------------------------------------
    # TEST 4 — DETERMINISM
    # ---------------------------------------------------------

    checked += 1
    try:
        a = batch_coordinator.coordinate_records(records)
        b = batch_coordinator.coordinate_records(tuple(reversed(records)))

        if getattr(a, "report_hash", None) != getattr(b, "report_hash", None):
            failures.append("non-deterministic report hash")

        if getattr(a, "plan_hash", None) != getattr(b, "plan_hash", None):
            failures.append("non-deterministic plan hash")

    except Exception as exc:
        failures.append(f"determinism test failed: {exc}")

    # ---------------------------------------------------------
    # TEST 5 — INVALID INPUT
    # ---------------------------------------------------------

    checked += 1
    try:
        build_batch_plan(records=(), max_batch_size=2)
        failures.append("empty records accepted")

    except BatchCoordinatorError:
        pass

    except Exception as exc:
        failures.append(f"unexpected invalid-input failure: {exc}")

    # ---------------------------------------------------------
    # TEST 6 — INVALID COORDINATOR
    # ---------------------------------------------------------

    checked += 1
    try:
        DeterministicBatchCoordinator(
            coordinator=None,
            max_batch_size=2,
        )
        failures.append("invalid coordinator accepted")

    except BatchCoordinatorError:
        pass

    except Exception as exc:
        failures.append(f"unexpected invalid coordinator failure: {exc}")

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    return DistributedCoordinatorValidationResult(
        passed=not failures,
        checked=checked,
        failures=tuple(failures),
    )


# ============================================================
# HELPERS
# ============================================================

def _record(*, event_id: str, routing_key: str, sequence: int, registry: Any):

    assignment = assign_partition(
        routing_key=routing_key,
        routing_scope="rides",
        registry=registry,
    )

    event = {
        "event_id": event_id,
        "routing_key": routing_key,
        "routing_scope": "rides",
        "payload": {
            "rider_id": f"rider.{event_id}",
            "pickup": "melbourne.cbd",
            "dropoff": "melbourne.airport",
        },
    }

    return build_queue_record(
        event_id=event_id,
        sequence=sequence,
        normalized_payload_hash=_sha256(f"normalized.{event_id}"),
        event=event,
        assignment=assignment,
        registry=registry,
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:
    result = validate_distributed_coordinator()
    print(result.report())
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
