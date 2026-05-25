"""
AfriTech Execution Graph Optimizer

PURPOSE:
--------
Optimizes DAG execution while preserving constitutional runtime boundaries:
- deterministic graph order
- partition-preserving pipeline fusion
- zero-copy edge planning
- vector-ready execution hints
- scheduler-compatible locality plans

CRITICAL LAW:
-------------
Graph Optimizer MAY:
- reorder independent work canonically
- fuse partition-local linear pipelines
- emit execution topology hints

Graph Optimizer may NOT:
- change operation semantics
- cross partition boundaries during fusion
- introduce nondeterministic planning
- define replay truth
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from afritech.runtime.locality.scheduler import (
    LocalityScheduleViolation,
    ScheduledTask,
    build_scheduler_trace,
    schedule_batch,
)


class ExecutionGraphOptimizationViolation(RuntimeError):
    """Raised when a graph cannot be optimized safely."""


@dataclass(frozen=True)
class GraphNode:
    """Immutable graph node declaration."""

    node_id: str
    partition_id: str
    operator: str
    dependencies: tuple[str, ...] = ()
    data_range: tuple[int, int] = (0, 0)
    fusion_safe: bool = True
    zero_copy: bool = True
    vectorizable: bool = False
    memory_alignment: int = 1


@dataclass(frozen=True)
class PlanStage:
    """Optimized execution stage."""

    stage_id: str
    node_ids: tuple[str, ...]
    partition_id: str
    operators: tuple[str, ...]
    data_range: tuple[int, int]
    zero_copy: bool
    vectorized: bool
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class OptimizedExecutionPlan:
    """Replay-verifiable graph optimization output."""

    stages: tuple[PlanStage, ...]
    scheduler_tasks: tuple[ScheduledTask, ...]
    scheduler_trace: Mapping[str, Any]
    optimization_trace: Mapping[str, Any]


def build_execution_plan(
    raw_nodes: Sequence[Mapping[str, Any] | GraphNode],
    partition_node_map: Mapping[str, str],
    node_topology: Mapping[str, Any],
    mode: str = "strict",
) -> OptimizedExecutionPlan:
    """Build a deterministic optimized execution plan from graph nodes."""

    nodes = normalize_graph_nodes(raw_nodes)
    order = canonical_topological_order(nodes)
    stages = tuple(fuse_partition_pipelines(nodes, order))
    scheduler_tasks = tuple(
        schedule_batch(
            [stage_to_scheduler_task(stage) for stage in stages],
            partition_node_map=partition_node_map,
            node_topology=node_topology,
            mode=mode,
        )
    )
    scheduler_trace = build_scheduler_trace(scheduler_tasks, mode)

    return OptimizedExecutionPlan(
        stages=stages,
        scheduler_tasks=scheduler_tasks,
        scheduler_trace=scheduler_trace,
        optimization_trace=build_optimization_trace(stages, scheduler_trace, mode),
    )


def normalize_graph_nodes(
    raw_nodes: Sequence[Mapping[str, Any] | GraphNode],
) -> dict[str, GraphNode]:
    """Normalize raw node declarations without mutating caller data."""

    if not isinstance(raw_nodes, Sequence) or isinstance(raw_nodes, (str, bytes)):
        raise TypeError("raw_nodes must be a sequence")

    nodes: dict[str, GraphNode] = {}

    for raw in raw_nodes:
        node = raw if isinstance(raw, GraphNode) else _node_from_mapping(raw)
        if node.node_id in nodes:
            raise ExecutionGraphOptimizationViolation(
                f"duplicate graph node: {node.node_id}"
            )
        nodes[node.node_id] = node

    if not nodes:
        raise ExecutionGraphOptimizationViolation("graph must contain nodes")

    return nodes


def canonical_topological_order(nodes: Mapping[str, GraphNode]) -> list[str]:
    """Return deterministic topological order with lexical tie-breaking."""

    validate_graph(nodes)

    dependents: dict[str, list[str]] = defaultdict(list)
    remaining_deps: dict[str, set[str]] = {}

    for node_id, node in nodes.items():
        remaining_deps[node_id] = set(node.dependencies)
        for dependency in node.dependencies:
            dependents[dependency].append(node_id)

    ready = sorted(node_id for node_id, deps in remaining_deps.items() if not deps)
    order: list[str] = []

    while ready:
        node_id = ready.pop(0)
        order.append(node_id)

        for dependent in sorted(dependents.get(node_id, [])):
            remaining_deps[dependent].remove(node_id)
            if not remaining_deps[dependent]:
                ready.append(dependent)
                ready.sort()

    if len(order) != len(nodes):
        raise ExecutionGraphOptimizationViolation("graph cycle detected")

    return order


def fuse_partition_pipelines(
    nodes: Mapping[str, GraphNode],
    order: Sequence[str],
) -> list[PlanStage]:
    """Fuse linear same-partition pipelines into deterministic stages."""

    stages: list[PlanStage] = []
    consumed: set[str] = set()
    dependents = _dependents(nodes)

    for node_id in order:
        if node_id in consumed:
            continue

        chain = [nodes[node_id]]
        consumed.add(node_id)
        current = nodes[node_id]

        while True:
            candidates = [
                dependent
                for dependent in sorted(dependents.get(current.node_id, ()))
                if dependent not in consumed
            ]
            if len(candidates) != 1:
                break

            candidate = nodes[candidates[0]]
            if not can_fuse(current, candidate, dependents):
                break

            chain.append(candidate)
            consumed.add(candidate.node_id)
            current = candidate

        stages.append(_stage_from_chain(chain))

    return stages


def can_fuse(
    upstream: GraphNode,
    downstream: GraphNode,
    dependents: Mapping[str, Sequence[str]],
) -> bool:
    """Allow fusion only for linear, same-partition, contiguous-safe edges."""

    if not upstream.fusion_safe or not downstream.fusion_safe:
        return False
    if upstream.partition_id != downstream.partition_id:
        return False
    if tuple(downstream.dependencies) != (upstream.node_id,):
        return False
    if len(dependents.get(upstream.node_id, ())) != 1:
        return False
    if upstream.data_range[1] > downstream.data_range[0]:
        return False
    return True


def stage_to_scheduler_task(stage: PlanStage) -> dict[str, Any]:
    """Project an optimized stage into scheduler task metadata."""

    return {
        "id": stage.stage_id,
        "partition_id": stage.partition_id,
        "data_range": [stage.data_range[0], stage.data_range[1]],
        "locality": {
            "node_affinity": None,
            "memory_block": "contiguous",
        },
        "execution": {
            "access_pattern": "sequential",
            "working_set_size": "vector" if stage.vectorized else "scalar",
            "zero_copy": stage.zero_copy,
        },
    }


def build_optimization_trace(
    stages: Sequence[PlanStage],
    scheduler_trace: Mapping[str, Any],
    mode: str,
) -> dict[str, Any]:
    """Emit replay-verifiable graph optimization evidence."""

    return {
        "graph_optimizer": {
            "stage_order": [stage.stage_id for stage in stages],
            "fused_stages": {
                stage.stage_id: list(stage.node_ids)
                for stage in stages
                if len(stage.node_ids) > 1
            },
            "zero_copy_edges": [
                stage.stage_id for stage in stages if stage.zero_copy
            ],
            "vectorized_stages": [
                stage.stage_id for stage in stages if stage.vectorized
            ],
            "scheduler": dict(scheduler_trace),
            "optimization_mode": mode,
        }
    }


def validate_graph_optimizer_replay(
    original: Mapping[str, Any],
    replayed: Mapping[str, Any],
) -> bool:
    """Validate graph optimizer replay equivalence."""

    original_graph = original.get("graph_optimizer", {})
    replayed_graph = replayed.get("graph_optimizer", {})

    for field in (
        "stage_order",
        "fused_stages",
        "zero_copy_edges",
        "vectorized_stages",
        "scheduler",
        "optimization_mode",
    ):
        if original_graph.get(field) != replayed_graph.get(field):
            raise ExecutionGraphOptimizationViolation(
                f"GRAPH OPTIMIZER REPLAY DIVERGENCE: {field}"
            )

    return True


def validate_zero_copy_boundaries(stages: Sequence[PlanStage]) -> bool:
    """Ensure zero-copy stages never imply cross-partition sharing."""

    for stage in stages:
        if stage.zero_copy and not stage.partition_id:
            raise ExecutionGraphOptimizationViolation(
                "zero-copy stage missing partition boundary"
            )
        for dependency in stage.dependencies:
            if not isinstance(dependency, str) or not dependency:
                raise ExecutionGraphOptimizationViolation(
                    "invalid zero-copy dependency boundary"
                )

    return True


def validate_graph(nodes: Mapping[str, GraphNode]) -> bool:
    """Validate graph references and node-local execution metadata."""

    for node_id, node in nodes.items():
        if node.node_id != node_id:
            raise ExecutionGraphOptimizationViolation("node key mismatch")
        if not node.partition_id:
            raise ExecutionGraphOptimizationViolation("node missing partition")
        if node.data_range[0] < 0 or node.data_range[1] < node.data_range[0]:
            raise ExecutionGraphOptimizationViolation("invalid node data range")
        for dependency in node.dependencies:
            if dependency not in nodes:
                raise ExecutionGraphOptimizationViolation(
                    f"unknown dependency: {dependency}"
                )

    return True


def _node_from_mapping(raw: Mapping[str, Any]) -> GraphNode:
    if not isinstance(raw, Mapping):
        raise TypeError("graph node must be a mapping")

    node_id = _required_string(raw, "id")
    partition_id = _required_string(raw, "partition_id")
    operator = _required_string(raw, "operator")
    data_range = _data_range(raw.get("data_range", (0, 0)))
    dependencies = tuple(sorted(raw.get("dependencies", ())))

    return GraphNode(
        node_id=node_id,
        partition_id=partition_id,
        operator=operator,
        dependencies=dependencies,
        data_range=data_range,
        fusion_safe=bool(raw.get("fusion_safe", True)),
        zero_copy=bool(raw.get("zero_copy", True)),
        vectorizable=bool(raw.get("vectorizable", False)),
        memory_alignment=_positive_int(raw.get("memory_alignment", 1), "memory_alignment"),
    )


def _stage_from_chain(chain: Sequence[GraphNode]) -> PlanStage:
    first = chain[0]
    last = chain[-1]
    node_ids = tuple(node.node_id for node in chain)
    stage_id = f"stage.{_stable_hash(':'.join(node_ids))[:12]}"
    vectorized = all(node.vectorizable and node.memory_alignment % 16 == 0 for node in chain)

    return PlanStage(
        stage_id=stage_id,
        node_ids=node_ids,
        partition_id=first.partition_id,
        operators=tuple(node.operator for node in chain),
        data_range=(first.data_range[0], last.data_range[1]),
        zero_copy=all(node.zero_copy for node in chain),
        vectorized=vectorized,
        dependencies=tuple(
            dependency
            for dependency in first.dependencies
            if dependency not in node_ids
        ),
    )


def _dependents(nodes: Mapping[str, GraphNode]) -> dict[str, list[str]]:
    dependents: dict[str, list[str]] = defaultdict(list)
    for node in nodes.values():
        for dependency in node.dependencies:
            dependents[dependency].append(node.node_id)
    return dependents


def _required_string(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value:
        raise ExecutionGraphOptimizationViolation(
            f"{field} must be a non-empty string"
        )
    return value


def _data_range(value: Any) -> tuple[int, int]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 2
    ):
        raise ExecutionGraphOptimizationViolation("data_range must be [start, end]")

    start, end = value
    if not isinstance(start, int) or not isinstance(end, int):
        raise ExecutionGraphOptimizationViolation("data_range bounds must be integers")
    if start < 0 or end < start:
        raise ExecutionGraphOptimizationViolation("data_range must be ordered")

    return start, end


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ExecutionGraphOptimizationViolation(f"{field} must be positive")
    return value


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
