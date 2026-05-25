"""
AfriTech Execution Graph Optimizer Tests

VALIDATES:
----------
- deterministic DAG ordering
- same-partition pipeline fusion
- zero-copy and vector-ready planning
- scheduler trace integration
- replay validation of graph optimization decisions
"""

import pytest

from afritech.runtime.locality.scheduler import build_default_topology
from afritech.runtime.orchestration.execution_graph_optimizer import (
    ExecutionGraphOptimizationViolation,
    build_execution_plan,
    build_optimization_trace,
    canonical_topological_order,
    fuse_partition_pipelines,
    normalize_graph_nodes,
    validate_graph_optimizer_replay,
    validate_zero_copy_boundaries,
)


@pytest.fixture
def partition_node_map():
    return {
        "P1": "NODE_A",
        "P2": "NODE_B",
    }


@pytest.fixture
def topology():
    return build_default_topology(["NODE_A", "NODE_B"], numa_zones=2, cores_per_zone=2)


def graph_nodes():
    return [
        {
            "id": "load",
            "partition_id": "P1",
            "operator": "load",
            "data_range": [0, 4],
            "vectorizable": True,
            "memory_alignment": 16,
        },
        {
            "id": "filter",
            "partition_id": "P1",
            "operator": "filter",
            "dependencies": ["load"],
            "data_range": [4, 8],
            "vectorizable": True,
            "memory_alignment": 16,
        },
        {
            "id": "emit",
            "partition_id": "P2",
            "operator": "emit",
            "dependencies": ["filter"],
            "data_range": [0, 1],
        },
    ]


def test_canonical_topological_order_is_deterministic():
    nodes = normalize_graph_nodes(list(reversed(graph_nodes())))

    assert canonical_topological_order(nodes) == ["load", "filter", "emit"]


def test_partition_pipeline_fusion_preserves_partition_boundary():
    nodes = normalize_graph_nodes(graph_nodes())
    order = canonical_topological_order(nodes)
    stages = fuse_partition_pipelines(nodes, order)

    assert [stage.node_ids for stage in stages] == [("load", "filter"), ("emit",)]
    assert stages[0].partition_id == "P1"
    assert stages[0].zero_copy is True
    assert stages[0].vectorized is True
    assert stages[1].partition_id == "P2"


def test_build_execution_plan_integrates_scheduler_trace(partition_node_map, topology):
    plan = build_execution_plan(graph_nodes(), partition_node_map, topology)

    assert [stage.partition_id for stage in plan.stages] == ["P1", "P2"]
    assert plan.scheduler_trace["partition_order"] == ["P1", "P2"]
    assert "P1" in plan.scheduler_trace["numa_assignment"]
    assert plan.optimization_trace["graph_optimizer"]["vectorized_stages"] == [
        plan.stages[0].stage_id
    ]


def test_graph_optimizer_replay_validation(partition_node_map, topology):
    plan = build_execution_plan(graph_nodes(), partition_node_map, topology)
    original = plan.optimization_trace
    replayed = build_optimization_trace(
        plan.stages,
        plan.scheduler_trace,
        "strict",
    )

    assert validate_graph_optimizer_replay(original, replayed)

    mutated = {
        "graph_optimizer": {
            **replayed["graph_optimizer"],
            "stage_order": ["different"],
        }
    }

    with pytest.raises(ExecutionGraphOptimizationViolation, match="stage_order"):
        validate_graph_optimizer_replay(original, mutated)


def test_zero_copy_boundaries_are_validated(partition_node_map, topology):
    plan = build_execution_plan(graph_nodes(), partition_node_map, topology)

    assert validate_zero_copy_boundaries(plan.stages)


def test_cycle_is_rejected():
    nodes = normalize_graph_nodes(
        [
            {
                "id": "a",
                "partition_id": "P1",
                "operator": "a",
                "dependencies": ["b"],
            },
            {
                "id": "b",
                "partition_id": "P1",
                "operator": "b",
                "dependencies": ["a"],
            },
        ]
    )

    with pytest.raises(ExecutionGraphOptimizationViolation, match="cycle"):
        canonical_topological_order(nodes)


def test_graph_optimizer_does_not_mutate_input(partition_node_map, topology):
    raw = graph_nodes()
    before = [dict(node) for node in raw]

    _ = build_execution_plan(raw, partition_node_map, topology)

    assert raw == before
