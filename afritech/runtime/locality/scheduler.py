"""
AfriTech Locality-Aware Scheduler

PURPOSE:
--------
Schedules partition-bound work under the dual-locality model:
- data-local placement (partition -> node)
- memory-local execution (node -> NUMA zone -> CPU core)

CRITICAL LAW:
-------------
Scheduler MAY:
- group tasks by partition
- select node, NUMA zone, and CPU core
- emit locality traces and operational metrics

Scheduler may NOT:
- mutate task payloads
- cross partition boundaries
- use remote memory unless explicitly allowed
- reorder work in a way that changes replay equivalence
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


STRICT_MODE = "strict"
OPTIMIZATION_MODE = "optimize"

DEFAULT_NUMA_PINNING_MAP = {
    0: (0, 1, 2, 3),
    1: (4, 5, 6, 7),
}


class LocalityScheduleViolation(RuntimeError):
    """Raised when a task cannot be scheduled inside locality law."""


@dataclass(frozen=True)
class CpuCore:
    """Deterministic CPU-core identity used by scheduler traces."""

    core_id: str


@dataclass(frozen=True)
class NumaZone:
    """NUMA zone with deterministic core selection."""

    zone_id: int
    cores: tuple[CpuCore, ...]

    def get_available_core(self) -> CpuCore:
        if not self.cores:
            raise LocalityScheduleViolation("NUMA zone has no CPU cores")
        return self.cores[0]


@dataclass(frozen=True)
class NodeTopology:
    """Execution topology for a physical or logical node."""

    node_id: str
    numa_zones: Mapping[int, NumaZone]

    def bind_to_numa(self, zone_id: int) -> NumaZone:
        if zone_id not in self.numa_zones:
            raise LocalityScheduleViolation(
                f"NUMA zone unavailable on node {self.node_id}: {zone_id}"
            )
        return self.numa_zones[zone_id]


@dataclass(frozen=True)
class ScheduledTask:
    """Immutable scheduling decision for a single task."""

    task_id: str
    partition_id: str
    node: str
    numa_zone: int
    cpu_core: str
    data_range: tuple[int, int]
    execution_order: int
    optimization_mode: str = STRICT_MODE
    scheduler_adjustments: Mapping[str, Any] | None = None


def route_task(task: Mapping[str, Any], partition_map: Mapping[str, Any]) -> Any:
    """Resolve a task to its declared data partition target."""

    partition_id = _required_string(task, "partition_id")

    if partition_id not in partition_map:
        raise LocalityScheduleViolation(f"unknown partition: {partition_id}")

    return partition_map[partition_id]


def assign_node(task: Mapping[str, Any], partition_node_map: Mapping[str, str]) -> str:
    """Resolve the node that owns the task partition."""

    partition_id = _required_string(task, "partition_id")

    if partition_id not in partition_node_map:
        raise LocalityScheduleViolation(f"partition has no node owner: {partition_id}")

    node = partition_node_map[partition_id]
    if not isinstance(node, str) or not node:
        raise LocalityScheduleViolation("partition node owner must be non-empty")

    return node


def bind_to_numa(task: Mapping[str, Any], node: NodeTopology) -> NumaZone:
    """Bind a task to its requested NUMA zone on the selected node."""

    zone_id = _locality(task).get("numa_zone")
    if zone_id is None:
        zone_id = assign_numa_zone(_required_string(task, "partition_id"), node.numa_zones)

    if not isinstance(zone_id, int):
        raise LocalityScheduleViolation("numa_zone must be an integer")

    return node.bind_to_numa(zone_id)


def schedule_on_cpu(task: Mapping[str, Any], numa_zone: NumaZone) -> CpuCore:
    """Select a deterministic CPU core inside the NUMA zone."""

    assigned_core_ids = assign_cpu(_required_string(task, "partition_id"))

    for core_index in assigned_core_ids:
        suffix = f".c{core_index}"
        for core in numa_zone.cores:
            if core.core_id.endswith(suffix):
                return core

    return numa_zone.get_available_core()


def schedule_task(
    task: Mapping[str, Any],
    partition_node_map: Mapping[str, str],
    node_topology: Mapping[str, NodeTopology],
    execution_order: int = 0,
    allow_remote_memory: bool = False,
    mode: str = STRICT_MODE,
) -> ScheduledTask:
    """Schedule a single task after validating partition and memory locality."""

    _validate_mode(mode)
    candidate = task
    scheduler_adjustments = None

    try:
        validate_task_locality(
            candidate,
            current_partition=_required_string(candidate, "partition_id"),
            partition_node_map=partition_node_map,
            allow_remote_memory=allow_remote_memory,
        )
    except LocalityScheduleViolation:
        if mode == STRICT_MODE:
            raise
        candidate = reschedule_to_locality(candidate, partition_node_map)
        scheduler_adjustments = describe_scheduler_adjustment(
            original=task,
            adjusted=candidate,
            reason="locality_optimization",
        )
        validate_task_locality(
            candidate,
            current_partition=_required_string(candidate, "partition_id"),
            partition_node_map=partition_node_map,
            allow_remote_memory=allow_remote_memory,
        )

    node_id = assign_node(candidate, partition_node_map)
    if node_id not in node_topology:
        raise LocalityScheduleViolation(f"node topology unavailable: {node_id}")

    numa_zone = bind_to_numa(candidate, node_topology[node_id])
    cpu_core = schedule_on_cpu(candidate, numa_zone)
    start, end = _data_range(candidate)

    return ScheduledTask(
        task_id=_required_string(candidate, "id"),
        partition_id=_required_string(candidate, "partition_id"),
        node=node_id,
        numa_zone=numa_zone.zone_id,
        cpu_core=cpu_core.core_id,
        data_range=(start, end),
        execution_order=execution_order,
        optimization_mode=mode,
        scheduler_adjustments=scheduler_adjustments,
    )


def schedule_batch(
    tasks: Sequence[Mapping[str, Any]],
    partition_node_map: Mapping[str, str],
    node_topology: Mapping[str, NodeTopology],
    allow_remote_memory: bool = False,
    mode: str = STRICT_MODE,
) -> list[ScheduledTask]:
    """Group tasks by partition, then schedule each partition sequentially."""

    _validate_mode(mode)

    if not isinstance(tasks, Sequence) or isinstance(tasks, (str, bytes)):
        raise TypeError("tasks must be a sequence")

    grouped = group_by_partition(tasks)
    scheduled: list[ScheduledTask] = []
    execution_order = 0

    for partition_id in canonical_partition_order(grouped.keys()):
        batch = grouped[partition_id]

        try:
            validate_partition_batch(partition_id, batch)
        except LocalityScheduleViolation:
            if mode == STRICT_MODE:
                raise
            batch = sorted(batch, key=_data_range)
            validate_partition_batch(partition_id, batch)

        for task in batch:
            scheduled.append(
                schedule_task(
                    task,
                    partition_node_map=partition_node_map,
                    node_topology=node_topology,
                    execution_order=execution_order,
                    allow_remote_memory=allow_remote_memory,
                    mode=mode,
                )
            )
            execution_order += 1

    return scheduled


def canonical_partition_order(partitions: Sequence[str]) -> list[str]:
    """Return canonical scheduler order for partition execution."""

    for partition in partitions:
        if not isinstance(partition, str) or not partition:
            raise LocalityScheduleViolation("partitions must be non-empty strings")

    return sorted(partitions)


def execute_task(
    task: Mapping[str, Any],
    data_loader: Callable[[tuple[int, int]], Sequence[Any]],
    processor: Callable[[Any], Any],
) -> list[Any]:
    """Execute a task over a contiguous block with sequential traversal."""

    validate_access_pattern(task)

    data_range = _data_range(task)
    data = data_loader(data_range)

    if not isinstance(data, Sequence) or isinstance(data, (str, bytes)):
        raise LocalityScheduleViolation("data_loader must return a sequence")

    results = []
    for index in range(len(data)):
        results.append(processor(data[index]))

    return results


def execute_partition(
    partition_id: str,
    data: Sequence[Any],
    processor: Callable[[Any], Any],
    partition_cache: dict[str, tuple[Any, ...]] | None = None,
) -> dict[str, Any]:
    """Execute a partition with explicit cache-warm reuse state."""

    if not isinstance(partition_id, str) or not partition_id:
        raise LocalityScheduleViolation("partition_id must be a non-empty string")
    if not isinstance(data, Sequence) or isinstance(data, (str, bytes)):
        raise LocalityScheduleViolation("partition data must be a sequence")

    cache = partition_cache if partition_cache is not None else {}
    cache_reused = partition_id in cache
    previous_block = cache.get(partition_id)

    result = [processor(item) for item in data]
    cache[partition_id] = tuple(data)

    return {
        "partition_id": partition_id,
        "cache_reused": cache_reused,
        "previous_block": previous_block,
        "result": result,
    }


def emit_execution_trace(
    scheduled_task: ScheduledTask,
    cache_hits: int = 0,
    cache_misses: int = 0,
    remote_access_count: int = 0,
    numa_switches: int = 0,
    sequential_ratio: float = 1.0,
    working_set_size: int | None = None,
) -> dict[str, Any]:
    """Emit locality trace data without influencing execution."""

    if working_set_size is None:
        working_set_size = scheduled_task.data_range[1] - scheduled_task.data_range[0]

    total_cache = cache_hits + cache_misses
    line_reuse_ratio = 0.0 if total_cache == 0 else cache_hits / total_cache
    cache_miss_rate = 0.0 if total_cache == 0 else cache_misses / total_cache
    cross_partition = False
    scheduler_trace = build_scheduler_trace(
        [scheduled_task],
        scheduled_task.optimization_mode,
    )

    trace = {
        "execution_trace": {
            "task_id": scheduled_task.task_id,
            "node": scheduled_task.node,
            "partition": scheduled_task.partition_id,
            "numa_zone": scheduled_task.numa_zone,
            "cpu_core": scheduled_task.cpu_core,
            "execution_order": scheduled_task.execution_order,
            "cache": {
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "line_reuse_ratio": line_reuse_ratio,
            },
            "memory": {
                "remote_access_count": remote_access_count,
                "numa_switches": numa_switches,
            },
            "execution": {
                "sequential_ratio": sequential_ratio,
                "working_set_size": working_set_size,
            },
            "locality": {
                "cpu": {
                    "cache_miss_rate": cache_miss_rate,
                    "access_pattern": "sequential",
                },
                "numa": {
                    "node_id": scheduled_task.node,
                    "zone_id": scheduled_task.numa_zone,
                    "remote_access": remote_access_count > 0,
                },
                "partition": {
                    "partition_id": scheduled_task.partition_id,
                    "cross_partition": cross_partition,
                },
            },
            "scheduler": scheduler_trace,
        }
    }

    if scheduled_task.scheduler_adjustments:
        trace["execution_trace"]["scheduler_adjustments"] = dict(
            scheduled_task.scheduler_adjustments
        )

    return trace


def build_scheduler_trace(
    scheduled_tasks: Sequence[ScheduledTask],
    optimization_mode: str = STRICT_MODE,
) -> dict[str, Any]:
    """Build first-class scheduler witness data for replay reconstruction."""

    _validate_mode(optimization_mode)

    partition_order = []
    seen_partitions = set()
    numa_assignment = {}
    cpu_pinning = {}

    for task in scheduled_tasks:
        if task.partition_id not in seen_partitions:
            partition_order.append(task.partition_id)
            seen_partitions.add(task.partition_id)

        numa_assignment[task.partition_id] = task.numa_zone
        cpu_pinning[task.partition_id] = task.cpu_core

    return {
        "partition_order": partition_order,
        "numa_assignment": numa_assignment,
        "cpu_pinning": cpu_pinning,
        "optimization_mode": optimization_mode,
    }


def validate_scheduler_replay(
    original: Mapping[str, Any],
    replayed: Mapping[str, Any],
) -> bool:
    """Validate that scheduler decisions are replay-reproducible."""

    for field in ("partition_order", "numa_assignment", "cpu_pinning"):
        if original.get(field) != replayed.get(field):
            raise LocalityScheduleViolation(
                f"SCHEDULER REPLAY DIVERGENCE: {field}"
            )

    if original.get("optimization_mode") != replayed.get("optimization_mode"):
        raise LocalityScheduleViolation(
            "SCHEDULER REPLAY DIVERGENCE: optimization_mode"
        )

    return True


def validate_cache_locality(
    trace: Mapping[str, Any],
    max_cache_miss_rate: float = 0.4,
) -> bool:
    """Validate cache locality using scheduler trace evidence."""

    if not isinstance(max_cache_miss_rate, (int, float)):
        raise TypeError("max_cache_miss_rate must be numeric")

    miss_rate = (
        trace.get("locality", {})
        .get("cpu", {})
        .get("cache_miss_rate")
    )

    if not isinstance(miss_rate, (int, float)):
        raise LocalityScheduleViolation("cache_miss_rate missing from trace")

    if miss_rate >= max_cache_miss_rate:
        raise LocalityScheduleViolation("CACHE LOCALITY THRESHOLD VIOLATION")

    return True


def describe_scheduler_adjustment(
    original: Mapping[str, Any],
    adjusted: Mapping[str, Any],
    reason: str,
) -> dict[str, Any]:
    """Describe optimize-mode scheduler metadata repair."""

    if not isinstance(reason, str) or not reason:
        raise LocalityScheduleViolation("adjustment reason must be non-empty")

    return {
        "original_partition": original.get("partition_id"),
        "adjusted_partition": adjusted.get("partition_id"),
        "original_node_affinity": _safe_locality_value(original, "node_affinity"),
        "adjusted_node_affinity": _safe_locality_value(adjusted, "node_affinity"),
        "original_access_pattern": _safe_execution_value(original, "access_pattern"),
        "adjusted_access_pattern": _safe_execution_value(adjusted, "access_pattern"),
        "reason": reason,
    }


def group_by_partition(
    tasks: Sequence[Mapping[str, Any]],
) -> "OrderedDict[str, list[Mapping[str, Any]]]":
    """Group tasks by partition while preserving first-seen partition order."""

    grouped: "OrderedDict[str, list[Mapping[str, Any]]]" = OrderedDict()

    for task in tasks:
        partition_id = _required_string(task, "partition_id")
        grouped.setdefault(partition_id, []).append(task)

    return grouped


def validate_task_locality(
    task: Mapping[str, Any],
    current_partition: str,
    partition_node_map: Mapping[str, str],
    allow_remote_memory: bool = False,
) -> bool:
    """Enforce partition, node, memory, and access-pattern locality."""

    partition_id = _required_string(task, "partition_id")
    if partition_id != current_partition:
        raise LocalityScheduleViolation("CROSS-PARTITION EXECUTION VIOLATION")

    assigned_node = assign_node(task, partition_node_map)
    locality = _locality(task)
    node_affinity = locality.get("node_affinity")

    if node_affinity is not None:
        if not isinstance(node_affinity, str) or not node_affinity:
            raise LocalityScheduleViolation("node_affinity must be non-empty")
        if node_affinity != assigned_node and not allow_remote_memory:
            raise LocalityScheduleViolation("REMOTE MEMORY ACCESS DETECTED")

    memory_block = locality.get("memory_block", "contiguous")
    if memory_block != "contiguous":
        raise LocalityScheduleViolation("MEMORY LOCALITY VIOLATION")

    validate_access_pattern(task)
    _data_range(task)

    return True


def validate_partition_batch(
    partition_id: str,
    batch: Sequence[Mapping[str, Any]],
) -> bool:
    """Validate that a partition batch is single-partition and sequential."""

    last_end: int | None = None

    for task in batch:
        if _required_string(task, "partition_id") != partition_id:
            raise LocalityScheduleViolation("CROSS-PARTITION EXECUTION VIOLATION")

        start, end = _data_range(task)
        if last_end is not None and start < last_end:
            raise LocalityScheduleViolation("NON-SEQUENTIAL PARTITION ACCESS")
        last_end = end

    return True


def validate_access_pattern(task: Mapping[str, Any]) -> bool:
    """Reject access patterns that break cache-local sequential execution."""

    execution = task.get("execution", {})
    if not isinstance(execution, Mapping):
        raise LocalityScheduleViolation("execution must be a mapping")

    access_pattern = execution.get("access_pattern", "sequential")
    if access_pattern != "sequential":
        raise LocalityScheduleViolation("CACHE LOCALITY VIOLATION")

    return True


def can_work_steal(
    donor: ScheduledTask,
    candidate_node: str,
    candidate_numa_zone: int,
    candidate_partition: str | None = None,
) -> bool:
    """Permit work stealing only inside the same node, NUMA zone, and partition."""

    same_locality = (
        donor.node == candidate_node
        and donor.numa_zone == candidate_numa_zone
    )

    if candidate_partition is None:
        return same_locality

    return same_locality and donor.partition_id == candidate_partition


def can_steal(work: ScheduledTask, context: Mapping[str, Any]) -> bool:
    """Replay-safe work stealing contract."""

    if not isinstance(context, Mapping):
        raise TypeError("context must be a mapping")

    return (
        bool(context.get("idle_worker"))
        and bool(context.get("same_numa_node"))
        and bool(context.get("same_partition"))
        and can_work_steal(
            work,
            _required_context_string(context, "candidate_node"),
            _required_context_int(context, "candidate_numa_zone"),
            _required_context_string(context, "candidate_partition"),
        )
    )


def enforce_work_stealing_constraints(
    task: ScheduledTask,
    worker: Mapping[str, Any],
) -> bool:
    """Enforce same-partition and same-NUMA work-stealing boundaries."""

    worker_partition = _required_context_string(worker, "partition")
    worker_numa_node = _required_context_int(worker, "numa_node")

    if task.partition_id != worker_partition:
        raise LocalityScheduleViolation("WORK STEALING PARTITION VIOLATION")

    if task.numa_zone != worker_numa_node:
        raise LocalityScheduleViolation("WORK STEALING NUMA VIOLATION")

    return True


def assign_numa_zone(partition_id: str, numa_zones: Sequence[int] | Mapping[int, Any]) -> int:
    """Map the same partition to the same NUMA zone deterministically."""

    if not isinstance(partition_id, str) or not partition_id:
        raise LocalityScheduleViolation("partition_id must be a non-empty string")

    zone_ids = sorted(numa_zones.keys() if isinstance(numa_zones, Mapping) else numa_zones)
    if not zone_ids:
        raise LocalityScheduleViolation("NUMA topology is empty")

    return zone_ids[_stable_hash(partition_id) % len(zone_ids)]


def assign_cpu(
    partition_id: str,
    numa_map: Mapping[int, Sequence[int]] = DEFAULT_NUMA_PINNING_MAP,
) -> tuple[int, ...]:
    """Return deterministic CPU candidates for a partition."""

    if not isinstance(partition_id, str) or not partition_id:
        raise LocalityScheduleViolation("partition_id must be a non-empty string")
    if not isinstance(numa_map, Mapping) or not numa_map:
        raise LocalityScheduleViolation("numa_map must be a non-empty mapping")

    zone_ids = sorted(numa_map)
    selected_zone = zone_ids[_stable_hash(partition_id) % len(zone_ids)]
    cpus = tuple(numa_map[selected_zone])

    if not cpus:
        raise LocalityScheduleViolation("NUMA CPU map cannot be empty")

    return cpus


def locality_cost(ctx: Mapping[str, Any]) -> int:
    """Score locality pressure from execution context only."""

    if not isinstance(ctx, Mapping):
        raise TypeError("ctx must be a mapping")

    remote_access = _non_negative_int(ctx.get("remote_access", 0), "remote_access")
    cache_miss = _non_negative_int(ctx.get("cache_miss", 0), "cache_miss")
    partition_hop = _non_negative_int(ctx.get("partition_hop", 0), "partition_hop")

    return remote_access * 10 + cache_miss * 5 + partition_hop * 20


def choose_min_cost(candidates: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Choose the lowest locality-cost candidate deterministically."""

    if not candidates:
        raise LocalityScheduleViolation("candidates cannot be empty")

    return sorted(
        candidates,
        key=lambda candidate: (
            locality_cost(candidate),
            str(candidate.get("candidate_id", "")),
        ),
    )[0]


def reschedule_to_locality(
    task: Mapping[str, Any],
    partition_node_map: Mapping[str, str],
) -> dict[str, Any]:
    """Create an optimized task copy aligned with partition-local execution."""

    partition_id = _required_string(task, "partition_id")
    assigned_node = assign_node(task, partition_node_map)

    optimized = dict(task)
    locality = dict(_locality(task))
    locality["node_affinity"] = assigned_node
    locality["memory_block"] = "contiguous"
    optimized["locality"] = locality

    execution = dict(optimized.get("execution", {}))
    execution["access_pattern"] = "sequential"
    optimized["execution"] = execution

    if "data_range" in optimized:
        optimized["data_range"] = list(_data_range(optimized))

    if "partition_id" not in optimized:
        optimized["partition_id"] = partition_id

    return optimized


def build_default_topology(
    node_ids: Sequence[str],
    numa_zones: int = 1,
    cores_per_zone: int = 1,
) -> dict[str, NodeTopology]:
    """Build a deterministic topology for tests and local simulations."""

    if numa_zones <= 0:
        raise ValueError("numa_zones must be positive")
    if cores_per_zone <= 0:
        raise ValueError("cores_per_zone must be positive")

    topology = {}

    for node_id in node_ids:
        zones = {}
        for zone_id in range(numa_zones):
            cores = tuple(
                CpuCore(f"{node_id}.z{zone_id}.c{core_id}")
                for core_id in range(cores_per_zone)
            )
            zones[zone_id] = NumaZone(zone_id=zone_id, cores=cores)

        topology[node_id] = NodeTopology(node_id=node_id, numa_zones=zones)

    return topology


def _required_string(task: Mapping[str, Any], field: str) -> str:
    if not isinstance(task, Mapping):
        raise TypeError("task must be a mapping")

    value = task.get(field)
    if not isinstance(value, str) or not value:
        raise LocalityScheduleViolation(f"{field} must be a non-empty string")

    return value


def _required_context_string(context: Mapping[str, Any], field: str) -> str:
    value = context.get(field)
    if not isinstance(value, str) or not value:
        raise LocalityScheduleViolation(f"{field} must be a non-empty string")
    return value


def _required_context_int(context: Mapping[str, Any], field: str) -> int:
    value = context.get(field)
    if not isinstance(value, int):
        raise LocalityScheduleViolation(f"{field} must be an integer")
    return value


def _safe_locality_value(task: Mapping[str, Any], field: str) -> Any:
    locality = task.get("locality", {})
    if not isinstance(locality, Mapping):
        return None
    return locality.get(field)


def _safe_execution_value(task: Mapping[str, Any], field: str) -> Any:
    execution = task.get("execution", {})
    if not isinstance(execution, Mapping):
        return None
    return execution.get(field)


def _locality(task: Mapping[str, Any]) -> Mapping[str, Any]:
    locality = task.get("locality")
    if not isinstance(locality, Mapping):
        raise LocalityScheduleViolation("task locality metadata is required")
    return locality


def _data_range(task: Mapping[str, Any]) -> tuple[int, int]:
    value = task.get("data_range")
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 2
    ):
        raise LocalityScheduleViolation("data_range must be [start, end]")

    start, end = value
    if not isinstance(start, int) or not isinstance(end, int):
        raise LocalityScheduleViolation("data_range bounds must be integers")
    if start < 0 or end < start:
        raise LocalityScheduleViolation("data_range must be contiguous and ordered")

    return start, end


def _stable_hash(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest, 16)


def _non_negative_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise LocalityScheduleViolation(f"{field} must be a non-negative integer")
    return value


def _validate_mode(mode: str) -> bool:
    if mode not in {STRICT_MODE, OPTIMIZATION_MODE}:
        raise LocalityScheduleViolation(f"unknown scheduler mode: {mode}")
    return True
