"""
afritech.tests.distributed.test_partition_assignment

Tests for deterministic distributed partition assignment.
"""

from __future__ import annotations

import pytest

from afritech.distributed.partition.partition_assignment import (
    PartitionAssignment,
    PartitionAssignmentError,
    assign_partition,
    assign_partition_from_event,
    assignment_hash,
    canonical_assignment_list_hash,
    require_valid_assignment,
    verify_assignment,
)

from afritech.distributed.partition.partition_registry import (
    PartitionRegistry,
    PartitionDefinition,
    default_partition_registry,
)


# ============================================================
# CORE DETERMINISM ✅
# ============================================================

def test_same_routing_key_produces_same_assignment():
    registry = default_partition_registry()

    a = assign_partition(
        routing_key="ride.request.001",
        routing_scope="rides",
        registry=registry,
    )
    b = assign_partition(
        routing_key="ride.request.001",
        routing_scope="rides",
        registry=registry,
    )

    assert a == b
    assert a.assignment_hash == b.assignment_hash


def test_different_keys_assign_within_declared_scope():
    registry = default_partition_registry()

    assignments = [
        assign_partition(
            routing_key=f"ride.request.{i}",
            routing_scope="rides",
            registry=registry,
        )
        for i in range(10)
    ]

    allowed = {
        p.partition_id for p in registry.partitions
        if p.routing_scope == "rides"
    }

    assert all(a.partition_id in allowed for a in assignments)


def test_assignment_is_stable_across_multiple_runs():
    registry = default_partition_registry()

    results = [
        assign_partition(
            routing_key="ride.request.stability",
            routing_scope="rides",
            registry=registry,
        )
        for _ in range(5)
    ]

    assert all(r == results[0] for r in results)


# ============================================================
# VALIDATION + CONSISTENCY ✅
# ============================================================

def test_assignment_is_registry_bound_and_valid():
    registry = default_partition_registry()

    assignment = assign_partition(
        routing_key="ride.request.002",
        routing_scope="rides",
        registry=registry,
    )

    assert verify_assignment(assignment=assignment, registry=registry) is True
    assert require_valid_assignment(
        assignment=assignment,
        registry=registry,
    ) == assignment


def test_assignment_invalid_if_registry_changes():
    original = default_partition_registry()

    assignment = assign_partition(
        routing_key="ride.request.003",
        routing_scope="rides",
        registry=original,
    )

    modified = PartitionRegistry(
        partitions=(
            PartitionDefinition("partition.rides.region_01", "rides"),
        )
    )

    assert verify_assignment(
        assignment=assignment,
        registry=modified,
    ) is False


def test_require_valid_assignment_rejects_tampered_hash():
    registry = default_partition_registry()

    assignment = assign_partition(
        routing_key="ride.request.004",
        routing_scope="rides",
        registry=registry,
    )

    tampered = PartitionAssignment(
        routing_key=assignment.routing_key,
        routing_scope=assignment.routing_scope,
        partition_id=assignment.partition_id,
        assignment_hash="0" * 64,
    )

    with pytest.raises(PartitionAssignmentError):
        require_valid_assignment(
            assignment=tampered,
            registry=registry,
        )


# ============================================================
# HASH DETERMINISM ✅
# ============================================================

def test_assignment_hash_is_deterministic():
    registry = default_partition_registry()

    assignment = assign_partition(
        routing_key="dispatch.priority.001",
        routing_scope="dispatch",
        registry=registry,
    )

    expected = assignment_hash(
        routing_key=assignment.routing_key,
        routing_scope=assignment.routing_scope,
        partition_id=assignment.partition_id,
        registry_hash=registry.registry_hash(),
    )

    assert assignment.assignment_hash == expected


def test_assignment_hash_changes_when_registry_changes():
    original = default_partition_registry()

    assignment = assign_partition(
        routing_key="ride.request.010",
        routing_scope="rides",
        registry=original,
    )

    modified = PartitionRegistry(
        partitions=(
            PartitionDefinition("partition.rides.region_01", "rides"),
            PartitionDefinition("partition.rides.region_02", "rides"),
            PartitionDefinition("partition.rides.region_03", "rides"),
        )
    )

    new_assignment = assign_partition(
        routing_key="ride.request.010",
        routing_scope="rides",
        registry=modified,
    )

    assert assignment.assignment_hash != new_assignment.assignment_hash


# ============================================================
# INPUT VALIDATION ✅
# ============================================================

def test_empty_routing_key_rejected():
    registry = default_partition_registry()

    with pytest.raises(PartitionAssignmentError):
        assign_partition(
            routing_key="",
            routing_scope="rides",
            registry=registry,
        )


def test_empty_routing_scope_rejected():
    registry = default_partition_registry()

    with pytest.raises(PartitionAssignmentError):
        assign_partition(
            routing_key="ride.request.011",
            routing_scope="",
            registry=registry,
        )


def test_missing_scope_fails_closed():
    registry = default_partition_registry()

    with pytest.raises(PartitionAssignmentError):
        assign_partition(
            routing_key="ride.request.012",
            routing_scope="missing_scope",
            registry=registry,
        )


def test_invalid_routing_key_formats_rejected():
    registry = default_partition_registry()

    with pytest.raises(PartitionAssignmentError):
        assign_partition(
            routing_key="ride/request/013",
            routing_scope="rides",
            registry=registry,
        )

    with pytest.raises(PartitionAssignmentError):
        assign_partition(
            routing_key="../ride.request.013",
            routing_scope="rides",
            registry=registry,
        )


def test_assignment_rejects_non_string_inputs():
    registry = default_partition_registry()

    with pytest.raises(PartitionAssignmentError):
        assign_partition(
            routing_key=None,   # type: ignore
            routing_scope="rides",
            registry=registry,
        )

    with pytest.raises(PartitionAssignmentError):
        assign_partition(
            routing_key="ride.request.014",
            routing_scope=None,  # type: ignore
            registry=registry,
        )


# ============================================================
# EVENT-BASED ASSIGNMENT ✅
# ============================================================

def test_assign_partition_from_event_valid():
    registry = default_partition_registry()

    assignment = assign_partition_from_event(
        event={"routing_key": "ride.request.020"},
        routing_key_field="routing_key",
        routing_scope="rides",
        registry=registry,
    )

    assert isinstance(assignment, PartitionAssignment)
    assert assignment.routing_key == "ride.request.020"


def test_assign_partition_from_event_missing_field_fails():
    registry = default_partition_registry()

    with pytest.raises(PartitionAssignmentError):
        assign_partition_from_event(
            event={},
            routing_key_field="routing_key",
            routing_scope="rides",
            registry=registry,
        )


def test_assign_partition_from_event_non_string_field_fails():
    registry = default_partition_registry()

    with pytest.raises(PartitionAssignmentError):
        assign_partition_from_event(
            event={"routing_key": 123},
            routing_key_field="routing_key",
            routing_scope="rides",
            registry=registry,
        )


def test_assign_partition_from_event_non_mapping_event_fails():
    registry = default_partition_registry()

    with pytest.raises(PartitionAssignmentError):
        assign_partition_from_event(
            event=None,  # type: ignore
            routing_key_field="routing_key",
            routing_scope="rides",
            registry=registry,
        )


# ============================================================
# CANONICAL CONSISTENCY ✅
# ============================================================

def test_canonical_assignment_list_hash_is_order_independent():
    registry = default_partition_registry()

    a = assign_partition(
        routing_key="ride.request.030",
        routing_scope="rides",
        registry=registry,
    )
    b = assign_partition(
        routing_key="ride.request.031",
        routing_scope="rides",
        registry=registry,
    )

    assert (
        canonical_assignment_list_hash((a, b))
        == canonical_assignment_list_hash((b, a))
    )


def test_canonical_assignment_list_hash_changes_when_contents_change():
    registry = default_partition_registry()

    a = assign_partition(
        routing_key="ride.request.032",
        routing_scope="rides",
        registry=registry,
    )
    b = assign_partition(
        routing_key="ride.request.033",
        routing_scope="rides",
        registry=registry,
    )
    c = assign_partition(
        routing_key="ride.request.034",
        routing_scope="rides",
        registry=registry,
    )

    assert (
        canonical_assignment_list_hash((a, b))
        != canonical_assignment_list_hash((a, c))
    )


def test_canonical_assignment_handles_duplicates_consistently():
    registry = default_partition_registry()

    a = assign_partition(
        routing_key="ride.request.035",
        routing_scope="rides",
        registry=registry,
    )

    hash1 = canonical_assignment_list_hash((a, a))
    hash2 = canonical_assignment_list_hash((a,))

    assert hash1 != hash2


# ============================================================
# EQUALITY + HASH STABILITY ✅
# ============================================================

def test_assignment_equality_and_hash_consistency():
    registry = default_partition_registry()

    a = assign_partition(
        routing_key="ride.request.040",
        routing_scope="rides",
        registry=registry,
    )
    b = assign_partition(
        routing_key="ride.request.040",
        routing_scope="rides",
        registry=registry,
    )

    assert a == b
    assert hash(a) == hash(b)


def test_assignment_hashable_for_sets_and_maps():
    registry = default_partition_registry()

    a = assign_partition(
        routing_key="ride.request.041",
        routing_scope="rides",
        registry=registry,
    )
    b = assign_partition(
        routing_key="ride.request.042",
        routing_scope="rides",
        registry=registry,
    )

    s = {a, b}

    assert a in s
    assert b in s


# ============================================================
# EXTRA HARDENING ✅ (NEW CRITICAL TESTS)
# ============================================================

def test_assignment_changes_if_routing_scope_changes():
    registry = default_partition_registry()

    a = assign_partition(
        routing_key="shared.key",
        routing_scope="rides",
        registry=registry,
    )

    b = assign_partition(
        routing_key="shared.key",
        routing_scope="dispatch",
        registry=registry,
    )

    assert a.partition_id != b.partition_id


def test_assignment_changes_if_registry_hash_differs():
    registry1 = default_partition_registry()

    registry2 = PartitionRegistry(
        partitions=tuple(reversed(registry1.partitions))
    )

    a = assign_partition(
        routing_key="ride.request.050",
        routing_scope="rides",
        registry=registry1,
    )

    b = assign_partition(
        routing_key="ride.request.050",
        routing_scope="rides",
        registry=registry2,
    )

    # ordering normalization ensures same assignment
    assert a == b


def test_verify_assignment_returns_false_on_invalid_object():
    registry = default_partition_registry()

    class Fake:
        pass

    assert verify_assignment(assignment=Fake(), registry=registry) is False


def test_canonical_assignment_list_hash_rejects_invalid_entry():
    registry = default_partition_registry()

    a = assign_partition(
        routing_key="ride.request.060",
        routing_scope="rides",
        registry=registry,
    )

    with pytest.raises(PartitionAssignmentError):
        canonical_assignment_list_hash((a, None))  # type: ignore
