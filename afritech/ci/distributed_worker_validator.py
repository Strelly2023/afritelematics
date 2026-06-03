"""
afritech.ci.distributed_worker_validator

CI validator for AfriTech distributed worker layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
import hashlib

# ✅ API imports
from afritech.distributed.api.partition import (
    assign,
    get_default_registry,
    PartitionRegistryError,
)

from afritech.distributed.api.queue import create_record

from afritech.distributed.api.worker import (
    DeterministicWorkerNode,
    WorkerNodeError,
    build_default_worker_node,
    WorkerResult,
)


# ============================================================
# ERROR
# ============================================================

class DistributedWorkerValidatorError(ValueError):
    pass


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class DistributedWorkerValidationResult:
    passed: bool
    checked_workers: int
    checked_records: int
    failures: tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Distributed worker validation PASSED\n"
                f"✅ Checked workers: {self.checked_workers}\n"
                f"✅ Checked records: {self.checked_records}"
            )

        return (
            "❌ Distributed worker validation FAILED\n"
            f"❌ Checked workers: {self.checked_workers}\n"
            f"❌ Checked records: {self.checked_records}\n"
            + "\n".join(f" - {f}" for f in self.failures)
        )


# ============================================================
# STRICT TYPE CHECK
# ============================================================

def _validate_worker_result(result: object) -> WorkerResult:
    if not isinstance(result, WorkerResult):
        raise DistributedWorkerValidatorError(
            f"Non-canonical worker result: {type(result)}"
        )
    return result


# ============================================================
# MAIN VALIDATION
# ============================================================

def validate_distributed_workers() -> DistributedWorkerValidationResult:

    failures: list[str] = []
    checked_workers = 0
    checked_records = 0

    # ---------------------------------------------------------
    # REGISTRY
    # ---------------------------------------------------------
    try:
        registry = get_default_registry()
    except PartitionRegistryError as exc:
        return DistributedWorkerValidationResult(
            passed=False,
            checked_workers=0,
            checked_records=0,
            failures=(f"registry failure: {exc}",),
        )

    # ---------------------------------------------------------
    # ✅ WORKER (FULL COVERAGE)
    # ---------------------------------------------------------
    worker = build_default_worker_node(
        worker_id="afritech.distributed.worker.node.worker_01",
        partition_ids=registry.partition_ids,
    )
    checked_workers += 1

    if not isinstance(worker, DeterministicWorkerNode):
        failures.append("worker construction failed")

    # ---------------------------------------------------------
    # EVENT
    # ---------------------------------------------------------
    event = {
        "event_id": "event.ride.request.001",
        "routing_key": "ride.request.001",
        "routing_scope": "rides",
        "payload": {
            "rider_id": "rider.001",
            "pickup": "melbourne.cbd",
            "dropoff": "melbourne.airport",
        },
    }

    # ---------------------------------------------------------
    # ASSIGNMENT
    # ---------------------------------------------------------
    assignment = assign(
        routing_key=event["routing_key"],
        routing_scope=event["routing_scope"],
        registry=registry,
    )

    # ---------------------------------------------------------
    # RECORD (API SAFE)
    # ---------------------------------------------------------
    record = create_record(
        event_id=event["event_id"],
        sequence=0,
        normalized_payload_hash=_fake_sha256("payload"),
        event=event,
        assignment=assignment,
        registry=registry,
    )

    checked_records += 1

    # ---------------------------------------------------------
    # EXECUTION TEST (DETERMINISM)
    # ---------------------------------------------------------
    try:
        out1 = worker.execute(record)
        out2 = worker.execute(record)

        r1 = _validate_worker_result(out1.result)
        r2 = _validate_worker_result(out2.result)

        # ✅ deterministic guarantee
        if r1.execution_hash != r2.execution_hash:
            failures.append("worker not deterministic")

        # ✅ replay hash must match execution hash
        if r1.execution_hash != r1.replay_hash:
            failures.append("execution/replay hash mismatch")

    except (WorkerNodeError, DistributedWorkerValidatorError, TypeError) as exc:
        failures.append(f"worker execution failed: {exc}")

    # ---------------------------------------------------------
    # ✅ NEGATIVE TEST: UNASSIGNED PARTITION MUST FAIL
    # ---------------------------------------------------------
    bad_worker = build_default_worker_node(
        worker_id="afritech.distributed.worker.node.worker_02",
        partition_ids=("partition.invalid",),  # intentionally wrong
    )
    checked_workers += 1

    try:
        bad_worker.execute(record)
        failures.append("unassigned partition accepted")
    except WorkerNodeError:
        pass  # ✅ expected

    return DistributedWorkerValidationResult(
        passed=not failures,
        checked_workers=checked_workers,
        checked_records=checked_records,
        failures=tuple(failures),
    )


# ---------------------------------------------------------
# UTIL
# ---------------------------------------------------------

def _fake_sha256(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


# ---------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------

def main() -> int:
    result = validate_distributed_workers()
    print(result.report())
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())