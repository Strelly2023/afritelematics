"""Data-locality guard for bounded runtime and replay validation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


class DataLocalityViolation(RuntimeError):
    """Raised when execution reads outside its declared locality boundary."""


@dataclass(frozen=True)
class DataLocalityReport:
    accessed_count: int
    allowed_count: int
    surface_id: str | None
    partition_id: str | None


def validate_data_locality(execution_context: Mapping[str, Any]) -> DataLocalityReport:
    """Validate that execution stays inside its declared data-locality scope.

    Expected context keys:
    - accessed_data: data identifiers touched by execution
    - allowed_scope: data identifiers declared for this execution
    - max_allowed: optional working-set limit
    - surface_id / declared_surfaces: optional surface-boundary check
    - partition_id / allowed_partitions: optional partition-affinity check
    """

    if not isinstance(execution_context, Mapping):
        raise DataLocalityViolation("execution_context must be a mapping")

    accessed = _normalize_scope(execution_context.get("accessed_data", ()), "accessed_data")
    allowed = _normalize_scope(execution_context.get("allowed_scope", ()), "allowed_scope")

    max_allowed = execution_context.get("max_allowed", 1000)
    if not isinstance(max_allowed, int) or max_allowed < 0:
        raise DataLocalityViolation("max_allowed must be a non-negative integer")

    if len(accessed) > max_allowed:
        raise DataLocalityViolation("working set exceeds declared locality bound")

    outside_scope = sorted(accessed - allowed)
    if outside_scope:
        raise DataLocalityViolation(
            f"access outside bounded scope: {outside_scope}"
        )

    surface_id = _optional_string(execution_context.get("surface_id"), "surface_id")
    declared_surfaces = _normalize_scope(
        execution_context.get("declared_surfaces", ()),
        "declared_surfaces",
    )
    if surface_id is not None and declared_surfaces and surface_id not in declared_surfaces:
        raise DataLocalityViolation(
            f"surface outside declared surfaces: {surface_id}"
        )

    partition_id = _optional_string(execution_context.get("partition_id"), "partition_id")
    allowed_partitions = _normalize_scope(
        execution_context.get("allowed_partitions", ()),
        "allowed_partitions",
    )
    if partition_id is not None and allowed_partitions and partition_id not in allowed_partitions:
        raise DataLocalityViolation(
            f"partition outside declared locality set: {partition_id}"
        )

    return DataLocalityReport(
        accessed_count=len(accessed),
        allowed_count=len(allowed),
        surface_id=surface_id,
        partition_id=partition_id,
    )


def _normalize_scope(value: Any, field: str) -> frozenset[str]:
    if value is None:
        return frozenset()

    if isinstance(value, str):
        return frozenset((value,))

    if not isinstance(value, Iterable):
        raise DataLocalityViolation(f"{field} must be iterable")

    normalized: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item:
            raise DataLocalityViolation(f"{field} entries must be non-empty strings")
        if "/" in item or "\\" in item or ".." in item:
            raise DataLocalityViolation(f"{field} entry contains forbidden pattern")
        normalized.add(item)

    return frozenset(normalized)


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise DataLocalityViolation(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise DataLocalityViolation(f"{field} contains forbidden pattern")
    return value
