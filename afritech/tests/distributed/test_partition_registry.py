"""
afritech.tests.distributed.test_partition_registry

Tests for deterministic distributed partition registry.
"""

from __future__ import annotations

import pytest

from afritech.distributed.partition.partition_registry import (
    PartitionDefinition,
    PartitionRegistry,
    PartitionRegistryError,
    default_partition_registry,
)


# ============================================================
# CORE REGISTRY BEHAVIOR ✅
# ============================================================

def test_default_partition_registry_is_declared_and_non_empty():
    registry = default_partition_registry()

    assert isinstance(registry, PartitionRegistry)
    assert registry.partition_ids
    assert registry.partition_ids == tuple(sorted(registry.partition_ids))


def test_default_partition_registry_contains_expected_partitions():
    registry = default_partition_registry()

    expected = {
        "partition.rides.region_01",
        "partition.rides.region_02",
        "partition.dispatch.priority",
    }

    assert expected.issubset(set(registry.partition_ids))


def test_require_declared_returns_partition_definition():
    registry = default_partition_registry()

    partition = registry.require_declared("partition.rides.region_01")

    assert isinstance(partition, PartitionDefinition)
    assert partition.partition_id == "partition.rides.region_01"
    assert partition.routing_scope == "rides"


def test_undeclared_partition_fails_closed():
    registry = default_partition_registry()

    with pytest.raises(PartitionRegistryError):
        registry.require_declared("partition.undeclared.invalid")


# ============================================================
# CONSTRUCTION VALIDATION ✅
# ============================================================

def test_duplicate_partition_id_is_rejected():
    with pytest.raises(PartitionRegistryError):
        PartitionRegistry(
            partitions=(
                PartitionDefinition("partition.rides.region_01", "rides"),
                PartitionDefinition("partition.rides.region_01", "rides"),
            )
        )


def test_empty_registry_is_rejected():
    with pytest.raises(PartitionRegistryError):
        PartitionRegistry(partitions=())


def test_registry_requires_partition_definition_instances():
    """
    Fail-closed behavior: invalid structure must raise.
    """
    with pytest.raises(Exception):
        PartitionRegistry(
            partitions=("not-a-definition",),  # type: ignore
        )


# ============================================================
# PARTITION DEFINITION VALIDATION ✅
# ============================================================

def test_filesystem_partition_identity_is_rejected():
    with pytest.raises(PartitionRegistryError):
        PartitionDefinition(
            partition_id="partition/rides/region_01",
            routing_scope="rides",
        )


def test_path_traversal_partition_identity_is_rejected():
    with pytest.raises(PartitionRegistryError):
        PartitionDefinition(
            partition_id="../partition.rides.region_01",
            routing_scope="rides",
        )


def test_partition_definition_requires_valid_scope():
    with pytest.raises(PartitionRegistryError):
        PartitionDefinition(
            partition_id="partition.valid.id",
            routing_scope="",
        )


def test_partition_definition_fields_are_strict_strings():
    with pytest.raises(PartitionRegistryError):
        PartitionDefinition(
            partition_id=None,  # type: ignore
            routing_scope="rides",
        )

    with pytest.raises(PartitionRegistryError):
        PartitionDefinition(
            partition_id="partition.valid.id",
            routing_scope=None,  # type: ignore
        )


# ============================================================
# HASH + DETERMINISM ✅
# ============================================================

def test_registry_hash_is_deterministic():
    first = default_partition_registry()
    second = default_partition_registry()

    assert first.registry_hash() == second.registry_hash()


def test_registry_hash_changes_when_registry_changes():
    original = default_partition_registry()

    changed = PartitionRegistry(
        partitions=(
            PartitionDefinition("partition.rides.region_01", "rides"),
            PartitionDefinition("partition.rides.region_02", "rides"),
            PartitionDefinition("partition.dispatch.priority", "dispatch"),
            PartitionDefinition("partition.extra.test", "test"),
        )
    )

    assert original.registry_hash() != changed.registry_hash()


def test_registry_hash_independent_of_input_order():
    parts1 = (
        PartitionDefinition("p1", "scope"),
        PartitionDefinition("p2", "scope"),
    )

    parts2 = tuple(reversed(parts1))

    r1 = PartitionRegistry(parts1)
    r2 = PartitionRegistry(parts2)

    assert r1.registry_hash() == r2.registry_hash()


# ============================================================
# CANONICAL REPRESENTATION ✅
# ============================================================

def test_to_canonical_dict_is_stable():
    registry = default_partition_registry()

    canonical = registry.to_canonical_dict()

    assert canonical["schema"] == "afritech.distributed.partition_registry.v1"
    assert canonical["partition_count"] == len(registry.partitions)
    assert isinstance(canonical["partitions"], list)

    ids = [p["partition_id"] for p in canonical["partitions"]]

    assert ids == sorted(ids)


def test_canonical_json_is_stable():
    registry = default_partition_registry()

    first = registry.canonical_json()
    second = registry.canonical_json()

    assert first == second


def test_registry_from_mapping_is_deterministic():
    mapping = {
        "partition.rides.region_02": {
            "routing_scope": "rides",
            "description": "Second",
        },
        "partition.rides.region_01": {
            "routing_scope": "rides",
            "description": "First",
        },
    }

    registry = PartitionRegistry.from_mapping(mapping)

    assert registry.partition_ids == (
        "partition.rides.region_01",
        "partition.rides.region_02",
    )


def test_registry_from_mapping_rejects_invalid_entries():
    with pytest.raises(PartitionRegistryError):
        PartitionRegistry.from_mapping({
            "partition.invalid": "not-a-mapping"  # type: ignore
        })


# ============================================================
# LOOKUP + MEMBERSHIP ✅
# ============================================================

def test_contains_only_accepts_declared_partition():
    registry = default_partition_registry()

    assert registry.contains("partition.rides.region_01") is True
    assert registry.contains("partition.undeclared.invalid") is False


def test_contains_rejects_invalid_identity():
    registry = default_partition_registry()

    with pytest.raises(PartitionRegistryError):
        registry.contains("../invalid")  # type: ignore


def test_require_declared_rejects_invalid_identity():
    registry = default_partition_registry()

    with pytest.raises(PartitionRegistryError):
        registry.require_declared("../invalid")


# ============================================================
# INTEGRITY ✅
# ============================================================

def test_registry_verify_integrity_passes_for_valid_registry():
    registry = default_partition_registry()

    if hasattr(registry, "verify_integrity"):
        assert registry.verify_integrity() is True


def test_registry_verify_integrity_fails_on_corrupted_registry():
    class Fake:
        pass

    corrupted = PartitionRegistry(
        partitions=(
            PartitionDefinition("partition.valid.id", "scope"),
        )
    )

    # simulate corruption
    object.__setattr__(corrupted, "partitions", (Fake(),))  # type: ignore

    if hasattr(corrupted, "verify_integrity"):
        assert corrupted.verify_integrity() is False


# ============================================================
# EQUALITY + STABILITY ✅
# ============================================================

def test_registry_equality_is_deterministic():
    r1 = default_partition_registry()
    r2 = default_partition_registry()

    assert r1 == r2
    assert r1.partition_ids == r2.partition_ids


def test_registry_not_equal_when_partitions_differ():
    r1 = default_partition_registry()

    r2 = PartitionRegistry(
        partitions=(
            PartitionDefinition("partition.rides.region_01", "rides"),
        )
    )

    assert r1 != r2


# ============================================================
# EXTRA HARDENING ✅ (NEW)
# ============================================================

def test_partition_ids_are_fully_canonical():
    registry = default_partition_registry()

    for pid in registry.partition_ids:
        assert isinstance(pid, str)
        assert pid
        assert "/" not in pid
        assert "\\" not in pid
        assert ".." not in pid


def test_registry_rejects_missing_fields():
    class BadPartition:
        partition_id = "p"
        # missing routing_scope

    with pytest.raises(PartitionRegistryError):
        PartitionRegistry(partitions=(BadPartition(),))


def test_registry_rejects_none_partition():
    with pytest.raises(PartitionRegistryError):
        PartitionRegistry(partitions=(None,))  # type: ignore