"""
afritech.distributed.partition.partition_assignment

PURPOSE:
--------
Deterministic partition assignment for distributed execution.

Guarantees:
- deterministic mapping
- replay-safe assignment
- canonical ordering support
- closed-world enforcement
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


# ============================================================
# ERROR
# ============================================================

class PartitionAssignmentError(ValueError):
    pass


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class PartitionAssignment:
    routing_key: str
    routing_scope: str
    partition_id: str
    assignment_hash: str

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "routing_key": self.routing_key,
            "routing_scope": self.routing_scope,
            "partition_id": self.partition_id,
            "assignment_hash": self.assignment_hash,
        }


# ============================================================
# VALIDATION
# ============================================================

def _require_non_empty_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise PartitionAssignmentError(f"{field_name} must be non-empty string")

    # ✅ closed-world safe characters
    if "/" in value or "\\" in value or ".." in value:
        raise PartitionAssignmentError(f"{field_name} contains forbidden pattern")


def _require_registry(registry) -> None:
    if registry is None:
        raise PartitionAssignmentError("registry is required")

    if not hasattr(registry, "partitions"):
        raise PartitionAssignmentError("registry missing partitions")

    if not hasattr(registry, "registry_hash"):
        raise PartitionAssignmentError("registry missing registry_hash()")


# ============================================================
# CANONICAL HASHING
# ============================================================

def _canonical_json(data: dict) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_assignment_payload(
    *,
    routing_key: str,
    routing_scope: str,
    partition_id: str,
    registry_hash: str,
) -> str:

    _require_non_empty_string(routing_key, "routing_key")
    _require_non_empty_string(routing_scope, "routing_scope")
    _require_non_empty_string(partition_id, "partition_id")
    _require_non_empty_string(registry_hash, "registry_hash")

    return _canonical_json({
        "partition_id": partition_id,
        "registry_hash": registry_hash,
        "routing_key": routing_key,
        "routing_scope": routing_scope,
    })


def assignment_hash(
    *,
    routing_key: str,
    routing_scope: str,
    partition_id: str,
    registry_hash: str,
) -> str:

    payload = canonical_assignment_payload(
        routing_key=routing_key,
        routing_scope=routing_scope,
        partition_id=partition_id,
        registry_hash=registry_hash,
    )

    return sha256(payload.encode()).hexdigest()


# ============================================================
# PARTITION RESOLUTION
# ============================================================

def _partitions_for_scope(registry, routing_scope: str):

    partitions = tuple(
        p for p in registry.partitions
        if getattr(p, "routing_scope", None) == routing_scope
    )

    if not partitions:
        raise PartitionAssignmentError(
            f"no partitions for routing_scope: {routing_scope}"
        )

    # ✅ deterministic ordering (CRITICAL)
    partitions = sorted(
        partitions,
        key=lambda p: getattr(p, "partition_id", "")
    )

    return tuple(partitions)


# ============================================================
# CORE ASSIGNMENT ✅ FINAL
# ============================================================

def assign_partition(
    *,
    routing_key: str,
    routing_scope: str,
    registry,
) -> PartitionAssignment:

    _require_non_empty_string(routing_key, "routing_key")
    _require_non_empty_string(routing_scope, "routing_scope")

    _require_registry(registry)

    partitions = _partitions_for_scope(registry, routing_scope)

    registry_hash = registry.registry_hash()

    if not isinstance(registry_hash, str) or not registry_hash:
        raise PartitionAssignmentError("invalid registry_hash")

    # ✅ deterministic hashing input
    payload = _canonical_json({
        "routing_key": routing_key,
        "routing_scope": routing_scope,
        "registry_hash": registry_hash,
    })

    digest = sha256(payload.encode()).hexdigest()

    # ✅ deterministic index selection
    index = int(digest, 16) % len(partitions)

    selected = partitions[index]

    if not hasattr(selected, "partition_id"):
        raise PartitionAssignmentError("partition missing partition_id")

    partition_id = selected.partition_id

    _require_non_empty_string(partition_id, "partition_id")

    # ✅ closed-world enforcement
    if hasattr(registry, "require_declared"):
        registry.require_declared(partition_id)

    return PartitionAssignment(
        routing_key=routing_key,
        routing_scope=routing_scope,
        partition_id=partition_id,
        assignment_hash=assignment_hash(
            routing_key=routing_key,
            routing_scope=routing_scope,
            partition_id=partition_id,
            registry_hash=registry_hash,
        ),
    )


# ============================================================
# EVENT-BASED ASSIGNMENT
# ============================================================

def assign_partition_from_event(
    *,
    event: Mapping[str, object],
    routing_key_field: str,
    routing_scope: str,
    registry,
) -> PartitionAssignment:

    _require_non_empty_string(routing_key_field, "routing_key_field")

    if not isinstance(event, Mapping):
        raise PartitionAssignmentError("event must be mapping")

    if routing_key_field not in event:
        raise PartitionAssignmentError("missing routing key field")

    value = event[routing_key_field]

    if not isinstance(value, str):
        raise PartitionAssignmentError("routing key must be string")

    return assign_partition(
        routing_key=value,
        routing_scope=routing_scope,
        registry=registry,
    )


# ============================================================
# VERIFICATION ✅ SAFE + NON-THROWING
# ============================================================

def verify_assignment(*, assignment, registry) -> bool:
    try:
        if assignment is None:
            return False

        required_fields = (
            "routing_key",
            "routing_scope",
            "partition_id",
            "assignment_hash",
        )

        for field in required_fields:
            if not hasattr(assignment, field):
                return False

        _require_registry(registry)

        # ✅ closed-world enforcement (safe)
        if hasattr(registry, "require_declared"):
            registry.require_declared(assignment.partition_id)

        # ✅ recompute deterministically
        expected = assign_partition(
            routing_key=assignment.routing_key,
            routing_scope=assignment.routing_scope,
            registry=registry,
        )

        return (
            expected.routing_key == assignment.routing_key
            and expected.routing_scope == assignment.routing_scope
            and expected.partition_id == assignment.partition_id
            and expected.assignment_hash == assignment.assignment_hash
        )

    except Exception:
        return False


def require_valid_assignment(*, assignment, registry):
    if not verify_assignment(assignment=assignment, registry=registry):
        raise PartitionAssignmentError("assignment verification failed")
    return assignment


# ============================================================
# LIST HASH ✅ GLOBAL CONSISTENCY
# ============================================================

def canonical_assignment_list_hash(
    assignments: Sequence[PartitionAssignment]
) -> str:

    if not isinstance(assignments, Sequence):
        raise PartitionAssignmentError("assignments must be sequence")

    canonical = []

    for a in assignments:
        if a is None or not hasattr(a, "assignment_hash"):
            raise PartitionAssignmentError("invalid assignment in list")
        canonical.append(a)

    # ✅ global deterministic ordering
    ordered = sorted(
        canonical,
        key=lambda x: (
            x.routing_scope,
            x.routing_key,
            x.partition_id,
            x.assignment_hash,
        ),
    )

    payload = _canonical_json([
        a.to_canonical_dict() for a in ordered
    ])

    return sha256(payload.encode()).hexdigest()


def locality_partition_key(entity: Mapping[str, Any] | object) -> str:
    """Return a replay-stable locality key for related distributed data.

    The key prefers stable domain identifiers so records for the same user,
    entity, ride, or routing key can be co-located without using Python's
    process-randomized ``hash()``.
    """

    candidates = (
        "user_id",
        "entity_id",
        "ride_id",
        "routing_key",
        "device_id",
        "event_id",
    )

    for field in candidates:
        value = _field_value(entity, field)
        if isinstance(value, str) and value:
            return sha256(value.encode("utf-8")).hexdigest()

    raise PartitionAssignmentError("entity missing locality key")


def _field_value(entity: Mapping[str, Any] | object, field: str) -> Any:
    if isinstance(entity, Mapping):
        return entity.get(field)

    return getattr(entity, field, None)
