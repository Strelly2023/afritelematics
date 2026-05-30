"""Validate Data Locality as an AfriTech constitutional pillar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from afritech.guards.data_locality_guard import (
    DataLocalityViolation,
    validate_data_locality,
)
from afritech.runtime.locality.scheduler import (
    LocalityScheduleViolation,
    build_default_topology,
    build_scheduler_trace,
    schedule_batch,
    validate_scheduler_replay,
    validate_task_locality,
)


ROOT = Path(__file__).resolve().parents[2]
CONCEPT = ROOT / "afritech/constitution/canonical/concepts/data_locality.yaml"
RULE = ROOT / "afritech/governance/rules/RULE-036-data-locality.yaml"
GUARD = ROOT / "afritech/guards/data_locality_guard.py"
SCHEDULER = ROOT / "afritech/runtime/locality/scheduler.py"
TESTS = (
    ROOT / "afritech/tests/governance/test_data_locality_guard.py",
    ROOT / "afritech/tests/runtime/test_locality_scheduler.py",
)


class DataLocalityValidationError(RuntimeError):
    """Raised when Data Locality is not GA Elite complete."""


@dataclass(frozen=True)
class DataLocalityValidationReport:
    concept_id: str
    scheduler_trace_verified: bool
    strict_guard_verified: bool
    violation_cases: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return (
            self.concept_id == "CONCEPT_DATA_LOCALITY"
            and self.scheduler_trace_verified
            and self.strict_guard_verified
            and self.violation_cases
            == (
                "access_outside_scope",
                "cross_surface_data_dependency",
                "remote_memory_access",
                "scheduler_replay_drift",
            )
        )


def compute_locality_score(access_sequence: list[int]) -> float:
    """Return 1.0 for sequential access and lower values for locality breaks."""

    if not access_sequence:
        return 1.0

    jumps = 0
    for index in range(1, len(access_sequence)):
        if abs(access_sequence[index] - access_sequence[index - 1]) > 1:
            jumps += 1

    return 1 - (jumps / len(access_sequence))


def validate_locality_quality(execution_context: dict[str, object]) -> bool:
    sequence = execution_context.get("access_pattern", [])
    if not isinstance(sequence, list) or not all(
        isinstance(item, int) for item in sequence
    ):
        raise DataLocalityValidationError("access_pattern must be a list of integers")

    score = compute_locality_score(sequence)
    if score < 0.6:
        raise DataLocalityValidationError(
            f"low locality score: {score:.2f} (threshold 0.6)"
        )

    return True


def validate() -> DataLocalityValidationReport:
    _validate_required_files()
    concept = _load_yaml(CONCEPT)
    _validate_concept(concept)
    _validate_quality_score()
    _validate_strict_guard()
    _validate_scheduler()

    report = DataLocalityValidationReport(
        concept_id=str(concept["concept"]["id"]),
        scheduler_trace_verified=True,
        strict_guard_verified=True,
        violation_cases=(
            "access_outside_scope",
            "cross_surface_data_dependency",
            "remote_memory_access",
            "scheduler_replay_drift",
        ),
    )
    if not report.verified:
        raise DataLocalityValidationError("Data Locality report failed")
    return report


def _validate_required_files() -> None:
    missing = [path for path in (CONCEPT, RULE, GUARD, SCHEDULER, *TESTS) if not path.exists()]
    if missing:
        raise DataLocalityValidationError(
            "missing Data Locality files: " + ", ".join(map(str, missing))
        )


def _load_yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DataLocalityValidationError(f"{path} must contain a mapping")
    return payload


def _validate_concept(concept: dict[str, object]) -> None:
    if concept.get("schema") != "afritech.concept.data_locality.v1":
        raise DataLocalityValidationError("Data Locality concept schema mismatch")

    concept_body = concept.get("concept")
    if not isinstance(concept_body, dict):
        raise DataLocalityValidationError("Data Locality concept body missing")
    if concept_body.get("id") != "CONCEPT_DATA_LOCALITY":
        raise DataLocalityValidationError("Data Locality concept id mismatch")

    definition = concept.get("definition")
    if not isinstance(definition, dict):
        raise DataLocalityValidationError("Data Locality definition missing")
    required = set(definition.get("requires", ()))
    expected = {
        "bounded_data_access",
        "surface_scoped_data",
        "deterministic_access_patterns",
        "partition_affinity",
        "declared_working_set_limits",
    }
    if not expected <= required:
        raise DataLocalityValidationError("Data Locality requirements incomplete")


def _validate_quality_score() -> None:
    validate_locality_quality({"access_pattern": [1, 2, 3, 4, 5]})
    try:
        validate_locality_quality({"access_pattern": [1, 9, 2, 8, 3]})
    except DataLocalityValidationError:
        return
    raise DataLocalityValidationError("random access was not rejected")


def _validate_strict_guard() -> None:
    report = validate_data_locality(
        {
            "accessed_data": ("ride.1", "driver.1"),
            "allowed_scope": ("ride.1", "driver.1"),
            "max_allowed": 4,
            "surface_id": "dispatch",
            "declared_surfaces": ("dispatch",),
            "partition_id": "partition.1",
            "allowed_partitions": ("partition.1",),
        }
    )
    if report.accessed_count != 2 or report.allowed_count != 2:
        raise DataLocalityValidationError("strict guard report mismatch")

    _expect_guard_violation(
        {
            "accessed_data": ("ride.1", "driver.2"),
            "allowed_scope": ("ride.1",),
        },
        "access_outside_scope",
    )
    _expect_guard_violation(
        {
            "accessed_data": ("ride.1",),
            "allowed_scope": ("ride.1",),
            "surface_id": "payments",
            "declared_surfaces": ("dispatch",),
        },
        "cross_surface_data_dependency",
    )


def _expect_guard_violation(context: dict[str, object], label: str) -> None:
    try:
        validate_data_locality(context)
    except DataLocalityViolation:
        return
    raise DataLocalityValidationError(f"{label} was not rejected")


def _validate_scheduler() -> None:
    partition_node_map = {"P1": "NODE_A", "P2": "NODE_B"}
    topology = build_default_topology(["NODE_A", "NODE_B"], numa_zones=2, cores_per_zone=2)
    tasks = (
        _task("T1", "P1", [0, 2], "NODE_A"),
        _task("T2", "P2", [0, 1], "NODE_B"),
    )
    scheduled = schedule_batch(tasks, partition_node_map, topology)
    original = build_scheduler_trace(scheduled)
    replayed = build_scheduler_trace(scheduled)
    if validate_scheduler_replay(original, replayed) is not True:
        raise DataLocalityValidationError("scheduler replay validation failed")

    try:
        validate_task_locality(_task("T-remote", "P1", [0, 1], "NODE_B"), "P1", partition_node_map)
    except LocalityScheduleViolation:
        pass
    else:
        raise DataLocalityValidationError("remote memory access was not rejected")

    try:
        validate_scheduler_replay(original, {**replayed, "cpu_pinning": {"P1": "drift"}})
    except LocalityScheduleViolation:
        pass
    else:
        raise DataLocalityValidationError("scheduler replay drift was not rejected")


def _task(
    task_id: str,
    partition_id: str,
    data_range: list[int],
    node_affinity: str,
) -> dict[str, object]:
    return {
        "id": task_id,
        "partition_id": partition_id,
        "data_range": data_range,
        "locality": {
            "node_affinity": node_affinity,
            "numa_zone": 0,
            "memory_block": "contiguous",
        },
        "execution": {
            "access_pattern": "sequential",
            "working_set_size": "small",
        },
    }


def main() -> int:
    try:
        report = validate()
    except DataLocalityValidationError as exc:
        print(f"Data Locality validation FAILED: {exc}")
        return 1

    print(
        "Data Locality validation PASSED: "
        f"concept_id={report.concept_id} "
        f"violation_cases={len(report.violation_cases)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
