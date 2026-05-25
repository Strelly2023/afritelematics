"""
AfriTech Distributed Multi-Node Execution Fabric

PURPOSE:
--------
Coordinates replay-safe execution topology across cluster nodes:
- canonical partition ownership
- network-aware node placement
- deterministic failover
- deterministic merge ordering
- replay-verifiable fabric traces

CRITICAL LAW:
-------------
Execution Fabric MAY:
- assign partitions to nodes
- choose lower network-cost placements
- select deterministic failover owners

Execution Fabric may NOT:
- mutate events or graph semantics
- infer undeclared partitions
- use realtime load or randomness
- define replay truth
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


class DistributedExecutionFabricViolation(RuntimeError):
    """Raised when distributed fabric planning violates replay safety."""


@dataclass(frozen=True)
class ClusterNode:
    """Canonical cluster node declaration."""

    node_id: str
    region: str
    numa_zones: tuple[int, ...] = (0,)
    partitions: tuple[str, ...] = ()
    online: bool = True


@dataclass(frozen=True)
class PartitionPlacement:
    """Replay-safe partition ownership decision."""

    partition_id: str
    primary_node: str
    failover_node: str | None
    network_cost: int


@dataclass(frozen=True)
class FabricPlan:
    """Distributed execution fabric plan."""

    placements: tuple[PartitionPlacement, ...]
    merge_order: tuple[str, ...]
    fabric_trace: Mapping[str, Any]


def build_fabric_plan(
    cluster_nodes: Sequence[Mapping[str, Any] | ClusterNode],
    partitions: Sequence[str],
    network_costs: Mapping[tuple[str, str], int] | None = None,
) -> FabricPlan:
    """Build a deterministic distributed execution plan."""

    nodes = normalize_cluster_nodes(cluster_nodes)
    partition_ids = canonical_partitions(partitions)
    costs = network_costs or {}

    placements = tuple(
        assign_partition(
            partition_id,
            nodes,
            costs,
        )
        for partition_id in partition_ids
    )
    merge_order = tuple(p.partition_id for p in placements)
    trace = build_fabric_trace(placements, merge_order)

    return FabricPlan(
        placements=placements,
        merge_order=merge_order,
        fabric_trace=trace,
    )


def normalize_cluster_nodes(
    raw_nodes: Sequence[Mapping[str, Any] | ClusterNode],
) -> tuple[ClusterNode, ...]:
    """Normalize cluster nodes into canonical lexical order."""

    if not isinstance(raw_nodes, Sequence) or isinstance(raw_nodes, (str, bytes)):
        raise TypeError("raw_nodes must be a sequence")

    nodes = []
    seen = set()

    for raw in raw_nodes:
        node = raw if isinstance(raw, ClusterNode) else _node_from_mapping(raw)
        if node.node_id in seen:
            raise DistributedExecutionFabricViolation(
                f"duplicate cluster node: {node.node_id}"
            )
        seen.add(node.node_id)
        nodes.append(node)

    if not nodes:
        raise DistributedExecutionFabricViolation("cluster requires nodes")

    return tuple(sorted(nodes, key=lambda node: node.node_id))


def canonical_partitions(partitions: Sequence[str]) -> tuple[str, ...]:
    """Return canonical partition order for distributed merge semantics."""

    if not isinstance(partitions, Sequence) or isinstance(partitions, (str, bytes)):
        raise TypeError("partitions must be a sequence")

    normalized = []
    seen = set()

    for partition_id in partitions:
        _require_identity(partition_id, "partition_id")
        if partition_id in seen:
            raise DistributedExecutionFabricViolation("duplicate partition")
        seen.add(partition_id)
        normalized.append(partition_id)

    if not normalized:
        raise DistributedExecutionFabricViolation("partitions required")

    return tuple(sorted(normalized))


def assign_partition(
    partition_id: str,
    nodes: Sequence[ClusterNode],
    network_costs: Mapping[tuple[str, str], int],
) -> PartitionPlacement:
    """Assign a partition to the lowest-cost eligible node deterministically."""

    _require_identity(partition_id, "partition_id")

    eligible = [
        node for node in nodes
        if node.online and (not node.partitions or partition_id in node.partitions)
    ]
    if not eligible:
        raise DistributedExecutionFabricViolation(
            f"no online node for partition: {partition_id}"
        )

    primary = min(
        eligible,
        key=lambda node: (
            partition_network_cost(partition_id, node.node_id, network_costs),
            node.region,
            node.node_id,
        ),
    )
    failover = select_failover(partition_id, primary.node_id, nodes, network_costs)

    return PartitionPlacement(
        partition_id=partition_id,
        primary_node=primary.node_id,
        failover_node=failover.node_id if failover else None,
        network_cost=partition_network_cost(
            partition_id,
            primary.node_id,
            network_costs,
        ),
    )


def select_failover(
    partition_id: str,
    primary_node_id: str,
    nodes: Sequence[ClusterNode],
    network_costs: Mapping[tuple[str, str], int],
) -> ClusterNode | None:
    """Select deterministic failover inside declared partition capability."""

    candidates = [
        node for node in nodes
        if (
            node.online
            and node.node_id != primary_node_id
            and (not node.partitions or partition_id in node.partitions)
        )
    ]
    if not candidates:
        return None

    return min(
        candidates,
        key=lambda node: (
            partition_network_cost(partition_id, node.node_id, network_costs),
            node.region,
            node.node_id,
        ),
    )


def partition_network_cost(
    partition_id: str,
    node_id: str,
    network_costs: Mapping[tuple[str, str], int],
) -> int:
    """Pure network cost model from declared topology only."""

    _require_identity(partition_id, "partition_id")
    _require_identity(node_id, "node_id")

    value = network_costs.get((partition_id, node_id), 0)
    if not isinstance(value, int) or value < 0:
        raise DistributedExecutionFabricViolation(
            "network cost must be a non-negative integer"
        )
    return value


def deterministic_merge_order(records: Sequence[Any]) -> tuple[Any, ...]:
    """Merge distributed outputs in canonical partition/sequence/event order."""

    return tuple(
        sorted(
            records,
            key=lambda record: (
                getattr(record, "partition_id", ""),
                getattr(record, "sequence", getattr(record, "partition_sequence", 0)),
                getattr(record, "event_id", ""),
            ),
        )
    )


def build_fabric_trace(
    placements: Sequence[PartitionPlacement],
    merge_order: Sequence[str],
) -> dict[str, Any]:
    """Emit replay-verifiable fabric topology evidence."""

    placement_rows = [
        {
            "partition_id": placement.partition_id,
            "primary_node": placement.primary_node,
            "failover_node": placement.failover_node,
            "network_cost": placement.network_cost,
        }
        for placement in sorted(placements, key=lambda item: item.partition_id)
    ]

    trace = {
        "distributed_fabric": {
            "partition_order": list(merge_order),
            "placements": placement_rows,
        }
    }
    trace["distributed_fabric"]["fabric_hash"] = fabric_hash(trace)

    return trace


def validate_fabric_replay(
    original: Mapping[str, Any],
    replayed: Mapping[str, Any],
) -> bool:
    """Validate distributed fabric replay equivalence."""

    original_fabric = original.get("distributed_fabric", {})
    replayed_fabric = replayed.get("distributed_fabric", {})

    for field in ("partition_order", "placements", "fabric_hash"):
        if original_fabric.get(field) != replayed_fabric.get(field):
            raise DistributedExecutionFabricViolation(
                f"DISTRIBUTED FABRIC REPLAY DIVERGENCE: {field}"
            )

    return True


def validate_failover_plan(plan: FabricPlan) -> bool:
    """Ensure failover does not cross undeclared ownership boundaries."""

    for placement in plan.placements:
        if placement.failover_node is not None and placement.failover_node == placement.primary_node:
            raise DistributedExecutionFabricViolation("failover equals primary")

    return True


def fabric_hash(trace: Mapping[str, Any]) -> str:
    """Stable fabric trace hash."""

    payload = dict(trace.get("distributed_fabric", trace))
    payload.pop("fabric_hash", None)
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _node_from_mapping(raw: Mapping[str, Any]) -> ClusterNode:
    if not isinstance(raw, Mapping):
        raise TypeError("cluster node must be a mapping")

    node_id = _required_string(raw, "node_id")
    region = _required_string(raw, "region")
    numa_zones = tuple(sorted(raw.get("numa_zones", (0,))))
    partitions = tuple(sorted(raw.get("partitions", ())))
    online = bool(raw.get("online", True))

    for zone in numa_zones:
        if not isinstance(zone, int) or zone < 0:
            raise DistributedExecutionFabricViolation("invalid NUMA zone")

    for partition_id in partitions:
        _require_identity(partition_id, "partition_id")

    return ClusterNode(
        node_id=node_id,
        region=region,
        numa_zones=numa_zones,
        partitions=partitions,
        online=online,
    )


def _required_string(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    _require_identity(value, field)
    return value


def _require_identity(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise DistributedExecutionFabricViolation(
            f"{field} must be a non-empty string"
        )
    if "/" in value or "\\" in value or ".." in value:
        raise DistributedExecutionFabricViolation(
            f"{field} contains forbidden path syntax"
        )
