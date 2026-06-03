"""
afritech.distributed.partition.partition_registry

Deterministic distributed partition registry for AfriTech.

PURPOSE:
--------
Defines canonical partition registry used for:
- deterministic routing
- replay-safe partition resolution
- closed-world enforcement
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Mapping


# ============================================================
# ERROR
# ============================================================

class PartitionRegistryError(ValueError):
    pass


# ============================================================
# HELPERS
# ============================================================

def _require_identity(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise PartitionRegistryError(f"{field} must be non-empty string")

    if "/" in value or "\\" in value:
        raise PartitionRegistryError(f"{field} contains forbidden path chars")

    if ".." in value:
        raise PartitionRegistryError(f"{field} contains invalid traversal")


def _canonical_json(data: dict) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )


# ============================================================
# PARTITION DEFINITION
# ============================================================

@dataclass(frozen=True, order=True)
class PartitionDefinition:

    partition_id: str
    routing_scope: str
    description: str = ""

    def __post_init__(self) -> None:
        _require_identity(self.partition_id, "partition_id")
        _require_identity(self.routing_scope, "routing_scope")

        if not isinstance(self.description, str):
            raise PartitionRegistryError("description must be string")

        if ".." in self.partition_id:
            raise PartitionRegistryError("partition_id invalid")

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "partition_id": self.partition_id,
            "routing_scope": self.routing_scope,
            "description": self.description,
        }


# ============================================================
# REGISTRY ✅ FINAL
# ============================================================

@dataclass(frozen=True)
class PartitionRegistry:

    partitions: tuple[PartitionDefinition, ...]

    def __init__(self, partitions: Iterable) -> None:

        if partitions is None:
            raise PartitionRegistryError("partitions required")

        # ✅ normalize + deterministic ordering
        normalized = tuple(
            sorted(
                partitions,
                key=lambda p: getattr(p, "partition_id", "")
            )
        )

        if not normalized:
            raise PartitionRegistryError("empty registry")

        seen_ids = set()

        for p in normalized:

            if p is None:
                raise PartitionRegistryError("invalid partition")

            # ✅ structural validation
            for field in ("partition_id", "routing_scope"):
                if not hasattr(p, field):
                    raise PartitionRegistryError(
                        f"invalid partition: missing {field}"
                    )

            # ✅ identity validation
            _require_identity(p.partition_id, "partition_id")
            _require_identity(p.routing_scope, "routing_scope")

            # ✅ uniqueness enforcement
            if p.partition_id in seen_ids:
                raise PartitionRegistryError("duplicate partition_id")

            seen_ids.add(p.partition_id)

        object.__setattr__(self, "partitions", normalized)

    # ---------------------------------------------------------
    # ACCESS
    # ---------------------------------------------------------

    @property
    def partition_ids(self) -> tuple[str, ...]:
        return tuple(p.partition_id for p in self.partitions)

    def contains(self, partition_id: str) -> bool:
        _require_identity(partition_id, "partition_id")
        return partition_id in self.partition_ids

    def require_declared(self, partition_id: str):

        _require_identity(partition_id, "partition_id")

        for p in self.partitions:
            if p.partition_id == partition_id:
                return p

        raise PartitionRegistryError(f"undeclared partition: {partition_id}")

    # ---------------------------------------------------------
    # CANONICAL REPRESENTATION ✅
    # ---------------------------------------------------------

    def to_canonical_dict(self) -> dict:

        # ✅ enforce deterministic ordering (already sorted, but explicit safety)
        ordered = sorted(self.partitions, key=lambda p: p.partition_id)

        return {
            "schema": "afritech.distributed.partition_registry.v1",
            "partition_count": len(ordered),
            "partitions": [
                p.to_canonical_dict()
                for p in ordered
            ],
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_canonical_dict())

    def registry_hash(self) -> str:
        return sha256(self.canonical_json().encode()).hexdigest()

    # ---------------------------------------------------------
    # INTEGRITY VALIDATION ✅ NEW (HIGH VALUE)
    # ---------------------------------------------------------

    def verify_integrity(self) -> bool:
        """
        Non-throwing validation for replay safety.
        """

        try:
            if not self.partitions:
                return False

            seen = set()

            for p in self.partitions:
                if not hasattr(p, "partition_id"):
                    return False

                if p.partition_id in seen:
                    return False

                seen.add(p.partition_id)

            return True

        except Exception:
            return False

    # ---------------------------------------------------------
    # BUILDERS
    # ---------------------------------------------------------

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Mapping[str, str]]):

        if mapping is None:
            raise PartitionRegistryError("mapping required")

        if not isinstance(mapping, Mapping):
            raise PartitionRegistryError("mapping must be dict-like")

        partitions = []

        for partition_id in sorted(mapping.keys()):

            data = mapping[partition_id]

            if not isinstance(data, Mapping):
                raise PartitionRegistryError("invalid mapping entry")

            if "routing_scope" not in data:
                raise PartitionRegistryError("missing routing_scope")

            partitions.append(
                PartitionDefinition(
                    partition_id=partition_id,
                    routing_scope=data["routing_scope"],
                    description=data.get("description", ""),
                )
            )

        return cls(partitions)


# ============================================================
# DEFAULT REGISTRY ✅ SAFE
# ============================================================

def default_partition_registry() -> PartitionRegistry:

    return PartitionRegistry(
        (
            PartitionDefinition(
                partition_id="partition.rides.region_01",
                routing_scope="rides",
                description="Primary deterministic ride partition",
            ),
            PartitionDefinition(
                partition_id="partition.rides.region_02",
                routing_scope="rides",
                description="Secondary deterministic ride partition",
            ),
            PartitionDefinition(
                partition_id="partition.dispatch.priority",
                routing_scope="dispatch",
                description="Dispatch priority partition",
            ),
        )
    )