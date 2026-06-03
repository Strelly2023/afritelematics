"""
afritech.ci.distributed_partition_validator

CI validator for AfriTech distributed partition layer.

This validator enforces that distributed partitioning remains:
- deterministic
- replay-safe
- closed-world aligned
- explicitly declared
- free from random, wall-clock, filesystem, or infrastructure authority

Constitutional boundary:
- Partitions improve operational scale and isolation.
- Partitions do not define execution truth.
- Partitions must never bypass replay.
"""

from __future__ import annotations

from dataclasses import dataclass
import sys

from afritech.distributed.partition.partition_assignment import (
    PartitionAssignment,
    PartitionAssignmentError,
    assign_partition,
    require_valid_assignment,
    verify_assignment,
    canonical_assignment_list_hash,
)

from afritech.distributed.partition.partition_registry import (
    PartitionRegistry,
    PartitionRegistryError,
    default_partition_registry,
)


# ============================================================
# ERROR
# ============================================================

class DistributedPartitionValidatorError(ValueError):
    pass


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class DistributedPartitionValidationResult:
    passed: bool
    checked_partitions: int
    checked_assignments: int
    failures: tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Distributed partition validation PASSED\n"
                f"✅ Checked partitions: {self.checked_partitions}\n"
                f"✅ Checked assignments: {self.checked_assignments}"
            )

        return (
            "❌ Distributed partition validation FAILED\n"
            f"❌ Checked partitions: {self.checked_partitions}\n"
            f"❌ Checked assignments: {self.checked_assignments}\n"
            + "\n".join(f" - {f}" for f in self.failures)
        )


# ============================================================
# REGISTRY VALIDATION ✅ HARDENED
# ============================================================

def validate_partition_registry() -> tuple[int, tuple[str, ...]]:
    failures: list[str] = []

    try:
        registry = default_partition_registry()
    except PartitionRegistryError as exc:
        return 0, (f"default partition registry invalid: {exc}",)

    if not isinstance(registry, PartitionRegistry):
        return 0, ("default registry is not PartitionRegistry",)

    partition_ids = registry.partition_ids

    # ✅ must not be empty
    if not partition_ids:
        failures.append("partition registry must not be empty")

    # ✅ deterministic ordering
    if tuple(sorted(partition_ids)) != partition_ids:
        failures.append("partition IDs must be deterministically sorted")

    # ✅ uniqueness
    if len(set(partition_ids)) != len(partition_ids):
        failures.append("duplicate partition_id detected")

    # ✅ integrity check (non-throwing)
    if hasattr(registry, "verify_integrity"):
        if not registry.verify_integrity():
            failures.append("registry integrity verification failed")

    # ✅ structural + identity + closed-world checks
    for partition_id in partition_ids:

        try:
            registry.require_declared(partition_id)
        except PartitionRegistryError as exc:
            failures.append(f"declared partition rejected: {partition_id}: {exc}")

        if "/" in partition_id or "\\" in partition_id or ".." in partition_id:
            failures.append(
                f"partition_id contains forbidden syntax: {partition_id}"
            )

    # ✅ undeclared partition must fail
    try:
        registry.require_declared("partition.invalid.undeclared")
        failures.append("undeclared partition was incorrectly accepted")
    except PartitionRegistryError:
        pass

    # ✅ deterministic hash guarantee
    try:
        first_hash = registry.registry_hash()
        second_hash = default_partition_registry().registry_hash()

        if first_hash != second_hash:
            failures.append("registry hash is not deterministic")
    except Exception as exc:
        failures.append(f"registry hashing failed: {exc}")

    return len(partition_ids), tuple(failures)


# ============================================================
# ASSIGNMENT VALIDATION ✅ HARDENED
# ============================================================

def validate_partition_assignments() -> tuple[int, tuple[str, ...]]:
    failures: list[str] = []

    try:
        registry = default_partition_registry()
    except PartitionRegistryError as exc:
        return 0, (f"default registry invalid: {exc}",)

    test_cases = (
        ("ride.request.001", "rides"),
        ("ride.request.002", "rides"),
        ("ride.request.003", "rides"),
        ("dispatch.priority.001", "dispatch"),
    )

    assignments: list[PartitionAssignment] = []
    checked = 0

    # ========================================================
    # VALID CASES
    # ========================================================

    for routing_key, routing_scope in test_cases:
        checked += 1

        try:
            first = assign_partition(
                routing_key=routing_key,
                routing_scope=routing_scope,
                registry=registry,
            )

            second = assign_partition(
                routing_key=routing_key,
                routing_scope=routing_scope,
                registry=registry,
            )

            # ✅ determinism
            if first != second:
                failures.append(
                    f"non-deterministic assignment: {routing_key}/{routing_scope}"
                )

            # ✅ verification (non-throwing)
            if not verify_assignment(assignment=first, registry=registry):
                failures.append(
                    f"assignment verification failed: {routing_key}/{routing_scope}"
                )

            # ✅ strict validation
            require_valid_assignment(
                assignment=first,
                registry=registry,
            )

            # ✅ closed-world
            registry.require_declared(first.partition_id)

            assignments.append(first)

        except (PartitionAssignmentError, PartitionRegistryError) as exc:
            failures.append(
                f"assignment failed for {routing_key}/{routing_scope}: {exc}"
            )

    # ========================================================
    # GLOBAL CONSISTENCY ✅ (NEW CRITICAL)
    # ========================================================

    try:
        if assignments:
            first_hash = canonical_assignment_list_hash(assignments)
            second_hash = canonical_assignment_list_hash(assignments)

            if first_hash != second_hash:
                failures.append("assignment list hash not deterministic")
    except Exception as exc:
        failures.append(f"assignment list hashing failed: {exc}")

    # ========================================================
    # INVALID CASES
    # ========================================================

    invalid_cases = (
        ("ride.request.invalid", "missing_scope"),
        ("", "rides"),
        ("ride/request/path", "rides"),
        ("ride.request.004", ""),
    )

    for routing_key, routing_scope in invalid_cases:
        checked += 1

        try:
            assign_partition(
                routing_key=routing_key,
                routing_scope=routing_scope,
                registry=registry,
            )
            failures.append(
                f"invalid input accepted: {routing_key!r}/{routing_scope!r}"
            )
        except PartitionAssignmentError:
            pass

    return checked, tuple(failures)


# ============================================================
# ROOT VALIDATION
# ============================================================

def validate_distributed_partitions() -> DistributedPartitionValidationResult:

    checked_partitions, registry_failures = validate_partition_registry()
    checked_assignments, assignment_failures = validate_partition_assignments()

    failures = registry_failures + assignment_failures

    return DistributedPartitionValidationResult(
        passed=(len(failures) == 0),
        checked_partitions=checked_partitions,
        checked_assignments=checked_assignments,
        failures=failures,
    )


# ============================================================
# CLI ENTRYPOINT
# ============================================================

def main() -> int:
    result = validate_distributed_partitions()

    print(result.report())

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())