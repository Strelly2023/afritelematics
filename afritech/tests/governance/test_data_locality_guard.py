from __future__ import annotations

import pytest

from afritech.distributed.api.partition import locality_key
from afritech.guards.data_locality_guard import (
    DataLocalityViolation,
    validate_data_locality,
)


def test_data_locality_guard_accepts_bounded_context() -> None:
    report = validate_data_locality(
        {
            "accessed_data": ["ride:1", "user:1"],
            "allowed_scope": ["ride:1", "user:1", "city:melbourne"],
            "max_allowed": 4,
            "surface_id": "runtime_engine",
            "declared_surfaces": ["runtime_engine"],
            "partition_id": "rides-0",
            "allowed_partitions": ["rides-0"],
        }
    )

    assert report.accessed_count == 2
    assert report.allowed_count == 3
    assert report.surface_id == "runtime_engine"
    assert report.partition_id == "rides-0"


def test_data_locality_guard_rejects_out_of_scope_access() -> None:
    with pytest.raises(DataLocalityViolation, match="access outside bounded scope"):
        validate_data_locality(
            {
                "accessed_data": ["ride:1", "user:2"],
                "allowed_scope": ["ride:1"],
            }
        )


def test_data_locality_guard_rejects_unbounded_working_set() -> None:
    with pytest.raises(DataLocalityViolation, match="working set exceeds"):
        validate_data_locality(
            {
                "accessed_data": ["a", "b"],
                "allowed_scope": ["a", "b"],
                "max_allowed": 1,
            }
        )


def test_data_locality_guard_rejects_surface_escape() -> None:
    with pytest.raises(DataLocalityViolation, match="surface outside declared"):
        validate_data_locality(
            {
                "accessed_data": ["ride:1"],
                "allowed_scope": ["ride:1"],
                "surface_id": "trace",
                "declared_surfaces": ["runtime_engine"],
            }
        )


def test_locality_partition_key_is_replay_stable() -> None:
    first = locality_key({"user_id": "user-1", "event_id": "event-1"})
    second = locality_key({"user_id": "user-1", "event_id": "event-2"})

    assert first == second
    assert len(first) == 64
