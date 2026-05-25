"""
AfriTech Distributed Execution Fabric Tests

VALIDATES:
----------
- canonical cluster partition placement
- declared network-cost placement
- deterministic failover
- deterministic merge ordering
- replay-verifiable fabric traces
"""

import pytest

from afritech.distributed.fabric.execution_fabric import (
    DistributedExecutionFabricViolation,
    build_fabric_plan,
    deterministic_merge_order,
    validate_fabric_replay,
    validate_failover_plan,
)


class Result:
    def __init__(self, partition_id, partition_sequence, event_id):
        self.partition_id = partition_id
        self.partition_sequence = partition_sequence
        self.event_id = event_id


def cluster_nodes():
    return [
        {
            "node_id": "NODE_B",
            "region": "eu",
            "numa_zones": [0, 1],
            "partitions": ["P2"],
        },
        {
            "node_id": "NODE_A",
            "region": "au",
            "numa_zones": [0, 1],
            "partitions": ["P1", "P2"],
        },
        {
            "node_id": "NODE_C",
            "region": "au",
            "numa_zones": [0],
            "partitions": ["P1"],
        },
    ]


def test_fabric_plan_assigns_partitions_by_declared_network_cost():
    plan = build_fabric_plan(
        cluster_nodes(),
        ["P2", "P1"],
        {
            ("P1", "NODE_A"): 3,
            ("P1", "NODE_C"): 1,
            ("P2", "NODE_A"): 2,
            ("P2", "NODE_B"): 1,
        },
    )

    placements = {p.partition_id: p for p in plan.placements}

    assert plan.merge_order == ("P1", "P2")
    assert placements["P1"].primary_node == "NODE_C"
    assert placements["P1"].failover_node == "NODE_A"
    assert placements["P2"].primary_node == "NODE_B"
    assert placements["P2"].failover_node == "NODE_A"
    assert validate_failover_plan(plan)


def test_fabric_trace_replay_validation_is_strict():
    plan = build_fabric_plan(cluster_nodes(), ["P1", "P2"])
    replayed = build_fabric_plan(list(reversed(cluster_nodes())), ["P2", "P1"])

    assert validate_fabric_replay(plan.fabric_trace, replayed.fabric_trace)

    mutated = {
        "distributed_fabric": {
            **replayed.fabric_trace["distributed_fabric"],
            "partition_order": ["P2", "P1"],
        }
    }

    with pytest.raises(DistributedExecutionFabricViolation, match="partition_order"):
        validate_fabric_replay(plan.fabric_trace, mutated)


def test_deterministic_merge_order():
    results = [
        Result("P2", 0, "e3"),
        Result("P1", 1, "e2"),
        Result("P1", 0, "e1"),
    ]

    ordered = deterministic_merge_order(results)

    assert [item.event_id for item in ordered] == ["e1", "e2", "e3"]


def test_no_online_node_for_partition_is_rejected():
    with pytest.raises(DistributedExecutionFabricViolation, match="no online node"):
        build_fabric_plan(
            [
                {
                    "node_id": "NODE_A",
                    "region": "au",
                    "partitions": ["P1"],
                    "online": False,
                }
            ],
            ["P1"],
        )


def test_fabric_plan_does_not_mutate_input():
    nodes = cluster_nodes()
    before = [dict(node) for node in nodes]

    _ = build_fabric_plan(nodes, ["P1", "P2"])

    assert nodes == before
