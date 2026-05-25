"""
AfriTech Locality-Aware Scheduler Tests

VALIDATES:
----------
- partition-first scheduling
- sticky node and NUMA execution
- sequential partition processing
- remote-memory and cache-locality violations
- non-authoritative trace emission
"""

import pytest

from afritech.runtime.locality.scheduler import (
    OPTIMIZATION_MODE,
    LocalityScheduleViolation,
    assign_cpu,
    assign_numa_zone,
    build_scheduler_trace,
    build_default_topology,
    can_steal,
    can_work_steal,
    canonical_partition_order,
    choose_min_cost,
    emit_execution_trace,
    enforce_work_stealing_constraints,
    execute_partition,
    execute_task,
    group_by_partition,
    locality_cost,
    schedule_batch,
    schedule_task,
    validate_cache_locality,
    validate_scheduler_replay,
    validate_task_locality,
)


def make_task(
    task_id,
    partition_id="P1",
    data_range=None,
    node_affinity="NODE_A",
    numa_zone=0,
    access_pattern="sequential",
):
    return {
        "id": task_id,
        "partition_id": partition_id,
        "data_range": data_range or [0, 2],
        "locality": {
            "node_affinity": node_affinity,
            "numa_zone": numa_zone,
            "memory_block": "contiguous",
        },
        "execution": {
            "access_pattern": access_pattern,
            "working_set_size": "small",
        },
    }


@pytest.fixture
def partition_node_map():
    return {
        "P1": "NODE_A",
        "P2": "NODE_B",
    }


@pytest.fixture
def topology():
    return build_default_topology(["NODE_A", "NODE_B"], numa_zones=2, cores_per_zone=2)


def test_schedule_task_binds_partition_node_numa_and_cpu(partition_node_map, topology):
    task = make_task("T123", partition_id="P1", data_range=[4, 8], numa_zone=1)

    scheduled = schedule_task(task, partition_node_map, topology)

    assert scheduled.task_id == "T123"
    assert scheduled.partition_id == "P1"
    assert scheduled.node == "NODE_A"
    assert scheduled.numa_zone == 1
    assert scheduled.cpu_core == "NODE_A.z1.c0"
    assert scheduled.data_range == (4, 8)


def test_batch_scheduler_groups_by_partition_and_preserves_order(partition_node_map, topology):
    tasks = [
        make_task("T1", "P1", [0, 2], "NODE_A"),
        make_task("T2", "P2", [0, 1], "NODE_B"),
        make_task("T3", "P1", [2, 4], "NODE_A"),
    ]

    grouped = group_by_partition(tasks)
    scheduled = schedule_batch(tasks, partition_node_map, topology)

    assert list(grouped.keys()) == ["P1", "P2"]
    assert [item.task_id for item in scheduled] == ["T1", "T3", "T2"]
    assert [item.execution_order for item in scheduled] == [0, 1, 2]


def test_batch_scheduler_uses_canonical_partition_order(partition_node_map, topology):
    tasks = [
        make_task("T2", "P2", [0, 1], "NODE_B"),
        make_task("T1", "P1", [0, 2], "NODE_A"),
    ]

    scheduled = schedule_batch(tasks, partition_node_map, topology)

    assert canonical_partition_order(["P2", "P1"]) == ["P1", "P2"]
    assert [item.partition_id for item in scheduled] == ["P1", "P2"]


def test_remote_memory_access_is_blocked(partition_node_map):
    task = make_task("T-remote", partition_id="P1", node_affinity="NODE_B")

    with pytest.raises(LocalityScheduleViolation, match="REMOTE MEMORY ACCESS"):
        validate_task_locality(task, "P1", partition_node_map)


def test_cross_partition_execution_is_blocked(partition_node_map):
    task = make_task("T-cross", partition_id="P1", node_affinity="NODE_A")

    with pytest.raises(LocalityScheduleViolation, match="CROSS-PARTITION"):
        validate_task_locality(task, "P2", partition_node_map)


def test_cache_break_random_access_is_blocked(partition_node_map):
    task = make_task("T-random", access_pattern="random")

    with pytest.raises(LocalityScheduleViolation, match="CACHE LOCALITY"):
        validate_task_locality(task, "P1", partition_node_map)


def test_non_sequential_partition_batch_is_blocked(partition_node_map, topology):
    tasks = [
        make_task("T1", "P1", [4, 8], "NODE_A"),
        make_task("T2", "P1", [2, 4], "NODE_A"),
    ]

    with pytest.raises(LocalityScheduleViolation, match="NON-SEQUENTIAL"):
        schedule_batch(tasks, partition_node_map, topology)


def test_optimization_mode_reschedules_remote_memory_to_local_node(
    partition_node_map,
    topology,
):
    task = make_task("T-opt", partition_id="P1", node_affinity="NODE_B")

    scheduled = schedule_task(
        task,
        partition_node_map,
        topology,
        mode=OPTIMIZATION_MODE,
    )

    assert scheduled.node == "NODE_A"
    assert task["locality"]["node_affinity"] == "NODE_B"


def test_optimization_mode_sorts_partition_batch_for_sequential_access(
    partition_node_map,
    topology,
):
    tasks = [
        make_task("T2", "P1", [2, 4], "NODE_A"),
        make_task("T1", "P1", [0, 2], "NODE_A"),
    ]

    scheduled = schedule_batch(
        tasks,
        partition_node_map,
        topology,
        mode=OPTIMIZATION_MODE,
    )

    assert [item.task_id for item in scheduled] == ["T1", "T2"]


def test_execute_task_traverses_contiguous_data_in_order():
    task = make_task("T-exec", data_range=[1, 4])
    visited = []

    def load(data_range):
        return list(range(data_range[0], data_range[1]))

    def process(item):
        visited.append(item)
        return item * 10

    assert execute_task(task, load, process) == [10, 20, 30]
    assert visited == [1, 2, 3]


def test_execution_trace_is_observational_only(partition_node_map, topology):
    task = make_task("T-trace", partition_id="P1", data_range=[0, 4])
    scheduled = schedule_task(task, partition_node_map, topology)

    trace = emit_execution_trace(
        scheduled,
        cache_hits=3,
        cache_misses=1,
        remote_access_count=0,
        numa_switches=0,
    )

    assert trace["execution_trace"]["node"] == "NODE_A"
    assert trace["execution_trace"]["partition"] == "P1"
    assert trace["execution_trace"]["cache"]["line_reuse_ratio"] == 0.75
    assert trace["execution_trace"]["memory"]["remote_access_count"] == 0
    assert trace["execution_trace"]["locality"]["cpu"]["cache_miss_rate"] == 0.25
    assert trace["execution_trace"]["locality"]["numa"]["node_id"] == "NODE_A"
    assert trace["execution_trace"]["locality"]["numa"]["zone_id"] == 0
    assert trace["execution_trace"]["locality"]["numa"]["remote_access"] is False
    assert trace["execution_trace"]["locality"]["partition"]["cross_partition"] is False
    assert trace["execution_trace"]["scheduler"]["partition_order"] == ["P1"]
    assert trace["execution_trace"]["scheduler"]["optimization_mode"] == "strict"


def test_work_stealing_safe_mode_requires_same_node_and_numa(partition_node_map, topology):
    task = make_task("T-steal")
    scheduled = schedule_task(task, partition_node_map, topology)

    assert can_work_steal(scheduled, "NODE_A", 0) is True
    assert can_work_steal(scheduled, "NODE_A", 0, "P1") is True
    assert can_work_steal(scheduled, "NODE_A", 0, "P2") is False
    assert can_work_steal(scheduled, "NODE_A", 1) is False
    assert can_work_steal(scheduled, "NODE_B", 0) is False


def test_can_steal_requires_idle_worker_same_numa_and_same_partition(
    partition_node_map,
    topology,
):
    scheduled = schedule_task(make_task("T-steal-formal"), partition_node_map, topology)
    context = {
        "idle_worker": True,
        "same_numa_node": True,
        "same_partition": True,
        "candidate_node": "NODE_A",
        "candidate_numa_zone": 0,
        "candidate_partition": "P1",
    }

    assert can_steal(scheduled, context) is True
    assert can_steal(scheduled, {**context, "same_partition": False}) is False
    assert can_steal(scheduled, {**context, "candidate_partition": "P2"}) is False


def test_enforce_work_stealing_constraints_blocks_partition_or_numa_escape(
    partition_node_map,
    topology,
):
    scheduled = schedule_task(make_task("T-steal-enforce"), partition_node_map, topology)

    assert enforce_work_stealing_constraints(
        scheduled,
        {"partition": "P1", "numa_node": 0},
    )

    with pytest.raises(LocalityScheduleViolation, match="PARTITION"):
        enforce_work_stealing_constraints(
            scheduled,
            {"partition": "P2", "numa_node": 0},
        )

    with pytest.raises(LocalityScheduleViolation, match="NUMA"):
        enforce_work_stealing_constraints(
            scheduled,
            {"partition": "P1", "numa_node": 1},
        )


def test_execute_partition_reuses_explicit_partition_cache():
    cache = {}

    first = execute_partition("P1", [1, 2], lambda item: item + 1, cache)
    second = execute_partition("P1", [3], lambda item: item + 1, cache)

    assert first["cache_reused"] is False
    assert second["cache_reused"] is True
    assert second["previous_block"] == (1, 2)
    assert second["result"] == [4]


def test_numa_pinning_is_deterministic():
    zones = {0: object(), 1: object()}

    assert assign_numa_zone("P42", zones) == assign_numa_zone("P42", zones)
    assert assign_cpu("P42") == assign_cpu("P42")
    assert assign_cpu("P42") in {(0, 1, 2, 3), (4, 5, 6, 7)}


def test_locality_cost_model_and_min_cost_choice():
    expensive = {
        "candidate_id": "b",
        "remote_access": 1,
        "cache_miss": 1,
        "partition_hop": 1,
    }
    cheap = {
        "candidate_id": "a",
        "remote_access": 0,
        "cache_miss": 1,
        "partition_hop": 0,
    }

    assert locality_cost(expensive) == 35
    assert locality_cost(cheap) == 5
    assert choose_min_cost([expensive, cheap]) == cheap


def test_scheduler_trace_replay_validation(partition_node_map, topology):
    scheduled = schedule_batch(
        [
            make_task("T1", "P1", [0, 1], "NODE_A"),
            make_task("T2", "P2", [0, 1], "NODE_B"),
        ],
        partition_node_map,
        topology,
    )
    original = build_scheduler_trace(scheduled)
    replayed = build_scheduler_trace(scheduled)

    assert validate_scheduler_replay(original, replayed)

    with pytest.raises(LocalityScheduleViolation, match="cpu_pinning"):
        validate_scheduler_replay(
            original,
            {**replayed, "cpu_pinning": {"P1": "different"}},
        )


def test_optimize_mode_emits_scheduler_adjustment_trace(partition_node_map, topology):
    task = make_task(
        "T-adjust",
        partition_id="P1",
        node_affinity="NODE_B",
        access_pattern="random",
    )

    scheduled = schedule_task(
        task,
        partition_node_map,
        topology,
        mode=OPTIMIZATION_MODE,
    )
    trace = emit_execution_trace(scheduled)

    assert trace["execution_trace"]["scheduler_adjustments"]["reason"] == (
        "locality_optimization"
    )
    assert trace["execution_trace"]["scheduler_adjustments"]["original_node_affinity"] == (
        "NODE_B"
    )
    assert trace["execution_trace"]["scheduler_adjustments"]["adjusted_node_affinity"] == (
        "NODE_A"
    )
    assert trace["execution_trace"]["scheduler_adjustments"]["original_access_pattern"] == (
        "random"
    )
    assert trace["execution_trace"]["scheduler"]["optimization_mode"] == OPTIMIZATION_MODE


def test_cache_locality_validator_uses_trace_evidence(partition_node_map, topology):
    scheduled = schedule_task(make_task("T-cache"), partition_node_map, topology)
    execution_trace = emit_execution_trace(
        scheduled,
        cache_hits=8,
        cache_misses=2,
    )["execution_trace"]

    assert validate_cache_locality(execution_trace)

    with pytest.raises(LocalityScheduleViolation, match="CACHE LOCALITY"):
        validate_cache_locality(
            {
                "locality": {
                    "cpu": {
                        "cache_miss_rate": 0.5,
                    }
                }
            }
        )
