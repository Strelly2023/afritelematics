"""
AfriTech Distributed OS Tests

VALIDATES:
----------
- deterministic autoscaling from declared workload
- cross-cluster federation routing
- deterministic hardware binding
- persistent snapshot restore
- OS replay trace validation
"""

import pytest

from afritech.distributed.os.distributed_os import (
    DistributedOSViolation,
    build_environment_plan,
    create_execution_snapshot,
    deterministic_autoscale,
    normalize_contract,
    normalize_clusters,
    normalize_workload,
    restore_execution_snapshot,
    route_federation,
    validate_os_replay,
    validate_resource_contract,
)


def workload():
    return {
        "workload_id": "w1",
        "partition_distribution": {
            "P2": 5,
            "P1": 15,
        },
        "data_volume_mb": 2048,
    }


def contract():
    return {
        "max_memory_mb": 4096,
        "max_nodes": 5,
        "required_devices": ["cpu", "vector_unit", "gpu"],
    }


def clusters():
    return [
        {
            "cluster_id": "cluster_b",
            "partitions": ["P2"],
            "max_nodes": 3,
        },
        {
            "cluster_id": "cluster_a",
            "partitions": ["P1", "P2"],
            "max_nodes": 5,
        },
    ]


def devices():
    return [
        {
            "device_id": "gpu.0",
            "device_type": "gpu",
            "supported_capabilities": ["gpu", "matrix"],
        },
        {
            "device_id": "vec.0",
            "device_type": "vector_unit",
            "supported_capabilities": ["vector", "simd"],
        },
        {
            "device_id": "cpu.0",
            "device_type": "cpu",
            "supported_capabilities": ["generic", "scalar"],
        },
    ]


def stages():
    return [
        {"stage_id": "s2", "required_capability": "gpu"},
        {"stage_id": "s1", "required_capability": "vector"},
        {"stage_id": "s3", "required_capability": "scalar"},
    ]


def test_deterministic_autoscaling_uses_declared_workload_only():
    size = deterministic_autoscale(
        normalize_workload(workload()),
        normalize_contract(contract()),
    )

    assert size == 2


def test_federation_routing_uses_canonical_cluster_order():
    routes = route_federation(["P2", "P1"], normalize_clusters(clusters()))

    assert routes == {
        "P1": "cluster_a",
        "P2": "cluster_a",
    }


def test_environment_plan_binds_hardware_and_resource_contract():
    plan = build_environment_plan(
        workload(),
        contract(),
        clusters(),
        devices(),
        stages(),
    )

    assert plan.cluster_size == 2
    assert plan.federation_routes == {"P1": "cluster_a", "P2": "cluster_a"}
    assert plan.hardware_bindings == {
        "s1": "vec.0",
        "s2": "gpu.0",
        "s3": "cpu.0",
    }
    assert validate_resource_contract(plan, normalize_contract(contract()))


def test_os_replay_validation_is_strict():
    original = build_environment_plan(
        workload(),
        contract(),
        clusters(),
        devices(),
        stages(),
    )
    replayed = build_environment_plan(
        dict(workload()),
        dict(contract()),
        list(reversed(clusters())),
        list(reversed(devices())),
        list(reversed(stages())),
    )

    assert validate_os_replay(original.os_trace, replayed.os_trace)

    mutated = {
        "distributed_os": {
            **replayed.os_trace["distributed_os"],
            "cluster_size": 99,
        }
    }

    with pytest.raises(DistributedOSViolation, match="cluster_size"):
        validate_os_replay(original.os_trace, mutated)


def test_execution_snapshot_round_trip_and_tamper_detection():
    snapshot = create_execution_snapshot(
        dag_state={"stage_order": ["s1", "s2"]},
        scheduler_state={"partition_order": ["P1"]},
        fabric_state={"partition_order": ["P1"]},
        memory_state={"P1": "block.1"},
    )

    restored = restore_execution_snapshot(snapshot)

    assert restored["dag_state"] == {"stage_order": ["s1", "s2"]}
    assert restored["memory_state"] == {"P1": "block.1"}

    tampered = dict(snapshot)
    tampered["memory_state"] = {"P1": "changed"}

    with pytest.raises(DistributedOSViolation, match="snapshot hash"):
        restore_execution_snapshot(tampered)


def test_realtime_load_like_fields_do_not_affect_plan():
    noisy_workload = {
        **workload(),
        "realtime_cpu_usage": 99,
        "random_seed": "forbidden-to-authority",
    }

    clean = build_environment_plan(
        workload(),
        contract(),
        clusters(),
        devices(),
        stages(),
    )
    noisy = build_environment_plan(
        noisy_workload,
        contract(),
        clusters(),
        devices(),
        stages(),
    )

    assert clean.os_trace == noisy.os_trace


def test_missing_cluster_route_is_rejected():
    with pytest.raises(DistributedOSViolation, match="no declared cluster"):
        build_environment_plan(
            {
                "workload_id": "w2",
                "partition_distribution": {"P9": 1},
                "data_volume_mb": 1,
            },
            contract(),
            clusters(),
            devices(),
            stages(),
        )
