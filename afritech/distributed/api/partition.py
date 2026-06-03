"""
afritech.distributed.api.partition

🔒 OPERATIVE SURFACE

This module defines the ONLY approved public interface for
distributed partition operations.

All consumers MUST import from this module instead of accessing
internal partition modules directly.
"""

from __future__ import annotations

from typing import Mapping


# ============================================================
# INTERNAL IMPORTS (CONTROLLED)
# ============================================================

from afritech.distributed.partition.partition_assignment import (
    assign_partition as _assign_partition,
    assign_partition_from_event as _assign_partition_from_event,
    locality_partition_key as _locality_partition_key,
    require_valid_assignment as _require_valid_assignment,
    verify_assignment as _verify_assignment,
    PartitionAssignment,
    PartitionAssignmentError,
)

from afritech.distributed.partition.partition_registry import (
    PartitionDefinition,
    PartitionRegistry,
    PartitionRegistryError,
    default_partition_registry as _default_partition_registry,
)


# ============================================================
# API ERROR
# ============================================================

class PartitionAPIError(ValueError):
    pass


# ============================================================
# SAFE ASSIGNMENT API
# ============================================================

def assign(
    *,
    routing_key: str,
    routing_scope: str,
    registry: PartitionRegistry,
) -> PartitionAssignment:

    if registry is None:
        raise PartitionAPIError("registry required")

    if hasattr(registry, "verify_integrity"):
        if not registry.verify_integrity():
            raise PartitionAPIError("invalid registry integrity")

    return _assign_partition(
        routing_key=routing_key,
        routing_scope=routing_scope,
        registry=registry,
    )


# ✅ BACKWARD COMPATIBILITY (REQUIRED FOR CI)
def assign_partition(
    *,
    routing_key: str,
    routing_scope: str,
    registry: PartitionRegistry,
) -> PartitionAssignment:
    return assign(
        routing_key=routing_key,
        routing_scope=routing_scope,
        registry=registry,
    )


# ============================================================
# EVENT ASSIGNMENT
# ============================================================

def assign_from_event(
    *,
    event: Mapping[str, object],
    routing_key_field: str,
    routing_scope: str,
    registry: PartitionRegistry,
) -> PartitionAssignment:

    if event is None:
        raise PartitionAPIError("event required")

    return _assign_partition_from_event(
        event=event,
        routing_key_field=routing_key_field,
        routing_scope=routing_scope,
        registry=registry,
    )


def locality_key(entity: Mapping[str, object] | object) -> str:
    return _locality_partition_key(entity)


# ============================================================
# VALIDATION
# ============================================================

def validate(
    *,
    assignment: PartitionAssignment,
    registry: PartitionRegistry,
) -> bool:

    return _verify_assignment(
        assignment=assignment,
        registry=registry,
    )


def require_valid(
    *,
    assignment: PartitionAssignment,
    registry: PartitionRegistry,
) -> PartitionAssignment:

    return _require_valid_assignment(
        assignment=assignment,
        registry=registry,
    )


# ============================================================
# REGISTRY API
# ============================================================

def create_registry(
    *,
    partitions,
) -> PartitionRegistry:

    if partitions is None:
        raise PartitionAPIError("partitions required")

    return PartitionRegistry(partitions)


def create_registry_from_mapping(
    mapping: Mapping[str, Mapping[str, str]]
) -> PartitionRegistry:

    if mapping is None:
        raise PartitionAPIError("mapping required")

    return PartitionRegistry.from_mapping(mapping)


def require_partition_declared(
    *,
    partition_id: str,
    registry: PartitionRegistry,
) -> None:

    if registry is None:
        raise PartitionAPIError("registry required")

    registry.require_declared(partition_id)


# ============================================================
# DEFAULT REGISTRY (FIX FOR CI)
# ============================================================

def get_default_registry() -> PartitionRegistry:

    registry = _default_partition_registry()

    if hasattr(registry, "verify_integrity"):
        if not registry.verify_integrity():
            raise PartitionAPIError("default registry corrupted")

    return registry


# ✅ BACKWARD COMPATIBILITY (CI EXPECTS THIS NAME)
def default_partition_registry() -> PartitionRegistry:
    return get_default_registry()


# ============================================================
# TOPOLOGY PROTECTION
# ============================================================

def assert_registry_compatible(
    *,
    registry: PartitionRegistry,
    expected_hash: str,
) -> None:

    if registry is None:
        raise PartitionAPIError("registry required")

    if not isinstance(expected_hash, str) or not expected_hash:
        raise PartitionAPIError("expected_hash invalid")

    actual = registry.registry_hash()

    if actual != expected_hash:
        raise PartitionAPIError(
            "registry hash mismatch (topology divergence)"
        )


# ============================================================
# EXPORTS ✅ FIXED
# ============================================================

__all__ = [
    # ✅ assignment API
    "assign",
    "assign_partition",               # ✅ REQUIRED FOR CI
    "assign_from_event",
    "locality_key",

    # ✅ validation
    "validate",
    "require_valid",

    # ✅ registry creation
    "create_registry",
    "create_registry_from_mapping",

    # ✅ registry access
    "get_default_registry",
    "default_partition_registry",     # ✅ REQUIRED FOR CI

    # ✅ enforcement
    "require_partition_declared",
    "assert_registry_compatible",

    # ✅ models + errors
    "PartitionAssignment",
    "PartitionAssignmentError",
    "PartitionDefinition",
    "PartitionRegistry",
    "PartitionRegistryError",

    # ✅ API error
    "PartitionAPIError",
]
