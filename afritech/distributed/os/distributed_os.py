"""
AfriTech Distributed OS Layer

PURPOSE:
--------
Controls deterministic execution environments above the execution engine:
- deterministic autoscaling
- cross-cluster federation routing
- hardware acceleration policy
- persistent execution snapshots
- global resource contracts

CRITICAL LAW:
-------------
Distributed OS MAY:
- frame the environment where execution occurs
- choose declared cluster size
- route partitions to clusters
- bind stages to declared hardware devices
- snapshot and restore execution state

Distributed OS may NOT:
- define execution truth
- use realtime load authority
- use random selection
- mutate engine semantics
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


class DistributedOSViolation(RuntimeError):
    """Raised when the deterministic OS layer violates its contract."""


@dataclass(frozen=True)
class ExecutionContract:
    """Declared execution environment limits."""

    max_memory_mb: int
    max_nodes: int
    required_devices: tuple[str, ...] = ("cpu",)


@dataclass(frozen=True)
class WorkloadSignature:
    """Replay-safe workload declaration for environment decisions."""

    workload_id: str
    partition_distribution: Mapping[str, int]
    data_volume_mb: int


@dataclass(frozen=True)
class ClusterDefinition:
    """Declared federated cluster identity."""

    cluster_id: str
    partitions: tuple[str, ...]
    max_nodes: int


@dataclass(frozen=True)
class HardwareDevice:
    """Declared hardware device."""

    device_id: str
    device_type: str
    supported_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionEnvironmentPlan:
    """Replay-verifiable OS environment plan."""

    cluster_size: int
    federation_routes: Mapping[str, str]
    hardware_bindings: Mapping[str, str]
    resource_contract_hash: str
    os_trace: Mapping[str, Any]


def build_environment_plan(
    workload: Mapping[str, Any] | WorkloadSignature,
    contract: Mapping[str, Any] | ExecutionContract,
    clusters: Sequence[Mapping[str, Any] | ClusterDefinition],
    devices: Sequence[Mapping[str, Any] | HardwareDevice],
    stages: Sequence[Mapping[str, Any]],
) -> ExecutionEnvironmentPlan:
    """Build a deterministic distributed OS execution environment."""

    normalized_workload = normalize_workload(workload)
    normalized_contract = normalize_contract(contract)
    normalized_clusters = normalize_clusters(clusters)
    normalized_devices = normalize_devices(devices)

    cluster_size = deterministic_autoscale(normalized_workload, normalized_contract)
    routes = route_federation(normalized_workload.partition_distribution.keys(), normalized_clusters)
    hardware_bindings = bind_hardware(stages, normalized_devices, normalized_contract)
    contract_hash = resource_contract_hash(normalized_contract)
    trace = build_os_trace(
        workload=normalized_workload,
        cluster_size=cluster_size,
        routes=routes,
        hardware_bindings=hardware_bindings,
        contract_hash=contract_hash,
    )

    return ExecutionEnvironmentPlan(
        cluster_size=cluster_size,
        federation_routes=routes,
        hardware_bindings=hardware_bindings,
        resource_contract_hash=contract_hash,
        os_trace=trace,
    )


def deterministic_autoscale(
    workload: WorkloadSignature,
    contract: ExecutionContract,
) -> int:
    """Compute cluster size from declared workload only."""

    total_partitions = len(workload.partition_distribution)
    total_weight = sum(workload.partition_distribution.values())
    data_factor = max(1, (workload.data_volume_mb + 1023) // 1024)
    requested = max(1, total_partitions, data_factor, (total_weight + 9) // 10)

    return min(contract.max_nodes, requested)


def route_federation(
    partitions: Sequence[str],
    clusters: Sequence[ClusterDefinition],
) -> dict[str, str]:
    """Route partitions to clusters by canonical declared ownership."""

    routes = {}

    for partition_id in sorted(partitions):
        _require_identity(partition_id, "partition_id")
        eligible = [
            cluster for cluster in clusters
            if partition_id in cluster.partitions
        ]
        if not eligible:
            raise DistributedOSViolation(
                f"no declared cluster for partition: {partition_id}"
            )

        selected = sorted(eligible, key=lambda cluster: cluster.cluster_id)[0]
        routes[partition_id] = selected.cluster_id

    return routes


def bind_hardware(
    stages: Sequence[Mapping[str, Any]],
    devices: Sequence[HardwareDevice],
    contract: ExecutionContract,
) -> dict[str, str]:
    """Bind execution stages to declared devices deterministically."""

    if not stages:
        return {}

    device_by_type = {}
    for device in sorted(devices, key=lambda item: item.device_id):
        device_by_type.setdefault(device.device_type, []).append(device)

    bindings = {}
    allowed_types = set(contract.required_devices)

    for stage in sorted(stages, key=lambda item: _required_string(item, "stage_id")):
        stage_id = _required_string(stage, "stage_id")
        capability = stage.get("required_capability", "scalar")
        preferred_type = _preferred_device_type(capability)

        if preferred_type not in allowed_types:
            preferred_type = "cpu"

        candidates = [
            device for device in device_by_type.get(preferred_type, ())
            if capability in device.supported_capabilities
            or "generic" in device.supported_capabilities
        ]

        if not candidates and preferred_type != "cpu":
            candidates = [
                device for device in device_by_type.get("cpu", ())
                if capability in device.supported_capabilities
                or "generic" in device.supported_capabilities
            ]

        if not candidates:
            raise DistributedOSViolation(
                f"no declared hardware device for stage: {stage_id}"
            )

        bindings[stage_id] = candidates[0].device_id

    return bindings


def create_execution_snapshot(
    *,
    dag_state: Mapping[str, Any],
    scheduler_state: Mapping[str, Any],
    fabric_state: Mapping[str, Any],
    memory_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a deterministic persistent execution snapshot."""

    snapshot = {
        "dag_state": _canonical_copy(dag_state),
        "scheduler_state": _canonical_copy(scheduler_state),
        "fabric_state": _canonical_copy(fabric_state),
        "memory_state": _canonical_copy(memory_state),
    }
    snapshot["snapshot_hash"] = stable_hash(snapshot)
    return snapshot


def restore_execution_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and restore a deterministic snapshot payload."""

    required = ("dag_state", "scheduler_state", "fabric_state", "memory_state")
    for field in required:
        if field not in snapshot:
            raise DistributedOSViolation(f"snapshot missing {field}")

    expected_hash = stable_hash(
        {field: _canonical_copy(snapshot[field]) for field in required}
    )
    if snapshot.get("snapshot_hash") != expected_hash:
        raise DistributedOSViolation("snapshot hash mismatch")

    return {field: _canonical_copy(snapshot[field]) for field in required}


def validate_os_replay(
    original: Mapping[str, Any],
    replayed: Mapping[str, Any],
) -> bool:
    """Validate distributed OS replay equivalence."""

    original_os = original.get("distributed_os", {})
    replayed_os = replayed.get("distributed_os", {})

    for field in (
        "cluster_size",
        "federation_routes",
        "hardware_bindings",
        "resource_contract_hash",
        "os_hash",
    ):
        if original_os.get(field) != replayed_os.get(field):
            raise DistributedOSViolation(
                f"DISTRIBUTED OS REPLAY DIVERGENCE: {field}"
            )

    return True


def validate_resource_contract(
    plan: ExecutionEnvironmentPlan,
    contract: ExecutionContract,
) -> bool:
    """Ensure environment plan stays inside declared resource limits."""

    if plan.cluster_size > contract.max_nodes:
        raise DistributedOSViolation("cluster size exceeds contract")

    if plan.resource_contract_hash != resource_contract_hash(contract):
        raise DistributedOSViolation("resource contract hash mismatch")

    return True


def build_os_trace(
    *,
    workload: WorkloadSignature,
    cluster_size: int,
    routes: Mapping[str, str],
    hardware_bindings: Mapping[str, str],
    contract_hash: str,
) -> dict[str, Any]:
    """Emit first-class OS witness trace."""

    trace = {
        "distributed_os": {
            "workload_id": workload.workload_id,
            "cluster_size": cluster_size,
            "federation_routes": dict(sorted(routes.items())),
            "hardware_bindings": dict(sorted(hardware_bindings.items())),
            "resource_contract_hash": contract_hash,
        }
    }
    trace["distributed_os"]["os_hash"] = stable_hash(trace["distributed_os"])
    return trace


def normalize_workload(raw: Mapping[str, Any] | WorkloadSignature) -> WorkloadSignature:
    if isinstance(raw, WorkloadSignature):
        return raw
    if not isinstance(raw, Mapping):
        raise TypeError("workload must be a mapping")

    workload_id = _required_string(raw, "workload_id")
    partition_distribution = raw.get("partition_distribution")
    if not isinstance(partition_distribution, Mapping) or not partition_distribution:
        raise DistributedOSViolation("partition_distribution required")

    normalized_distribution = {}
    for partition_id, weight in partition_distribution.items():
        _require_identity(partition_id, "partition_id")
        if not isinstance(weight, int) or weight <= 0:
            raise DistributedOSViolation("partition weights must be positive integers")
        normalized_distribution[partition_id] = weight

    data_volume_mb = raw.get("data_volume_mb")
    if not isinstance(data_volume_mb, int) or data_volume_mb <= 0:
        raise DistributedOSViolation("data_volume_mb must be positive integer")

    return WorkloadSignature(
        workload_id=workload_id,
        partition_distribution=dict(sorted(normalized_distribution.items())),
        data_volume_mb=data_volume_mb,
    )


def normalize_contract(raw: Mapping[str, Any] | ExecutionContract) -> ExecutionContract:
    if isinstance(raw, ExecutionContract):
        return raw
    if not isinstance(raw, Mapping):
        raise TypeError("contract must be a mapping")

    max_memory_mb = raw.get("max_memory_mb")
    max_nodes = raw.get("max_nodes")
    required_devices = tuple(sorted(raw.get("required_devices", ("cpu",))))

    if not isinstance(max_memory_mb, int) or max_memory_mb <= 0:
        raise DistributedOSViolation("max_memory_mb must be positive integer")
    if not isinstance(max_nodes, int) or max_nodes <= 0:
        raise DistributedOSViolation("max_nodes must be positive integer")
    for device in required_devices:
        _require_identity(device, "required_device")

    return ExecutionContract(
        max_memory_mb=max_memory_mb,
        max_nodes=max_nodes,
        required_devices=required_devices,
    )


def normalize_clusters(
    raw_clusters: Sequence[Mapping[str, Any] | ClusterDefinition],
) -> tuple[ClusterDefinition, ...]:
    if not isinstance(raw_clusters, Sequence) or isinstance(raw_clusters, (str, bytes)):
        raise TypeError("clusters must be a sequence")

    clusters = []
    seen = set()

    for raw in raw_clusters:
        cluster = raw if isinstance(raw, ClusterDefinition) else _cluster_from_mapping(raw)
        if cluster.cluster_id in seen:
            raise DistributedOSViolation("duplicate cluster")
        seen.add(cluster.cluster_id)
        clusters.append(cluster)

    if not clusters:
        raise DistributedOSViolation("clusters required")

    return tuple(sorted(clusters, key=lambda item: item.cluster_id))


def normalize_devices(
    raw_devices: Sequence[Mapping[str, Any] | HardwareDevice],
) -> tuple[HardwareDevice, ...]:
    if not isinstance(raw_devices, Sequence) or isinstance(raw_devices, (str, bytes)):
        raise TypeError("devices must be a sequence")

    devices = []
    seen = set()

    for raw in raw_devices:
        device = raw if isinstance(raw, HardwareDevice) else _device_from_mapping(raw)
        if device.device_id in seen:
            raise DistributedOSViolation("duplicate device")
        seen.add(device.device_id)
        devices.append(device)

    if not devices:
        raise DistributedOSViolation("devices required")

    return tuple(sorted(devices, key=lambda item: item.device_id))


def resource_contract_hash(contract: ExecutionContract) -> str:
    return stable_hash(
        {
            "max_memory_mb": contract.max_memory_mb,
            "max_nodes": contract.max_nodes,
            "required_devices": list(contract.required_devices),
        }
    )


def stable_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _cluster_from_mapping(raw: Mapping[str, Any]) -> ClusterDefinition:
    if not isinstance(raw, Mapping):
        raise TypeError("cluster must be a mapping")

    cluster_id = _required_string(raw, "cluster_id")
    partitions = tuple(sorted(raw.get("partitions", ())))
    max_nodes = raw.get("max_nodes")

    if not partitions:
        raise DistributedOSViolation("cluster partitions required")
    for partition_id in partitions:
        _require_identity(partition_id, "partition_id")
    if not isinstance(max_nodes, int) or max_nodes <= 0:
        raise DistributedOSViolation("cluster max_nodes must be positive integer")

    return ClusterDefinition(
        cluster_id=cluster_id,
        partitions=partitions,
        max_nodes=max_nodes,
    )


def _device_from_mapping(raw: Mapping[str, Any]) -> HardwareDevice:
    if not isinstance(raw, Mapping):
        raise TypeError("device must be a mapping")

    device_id = _required_string(raw, "device_id")
    device_type = _required_string(raw, "device_type")
    supported_capabilities = tuple(sorted(raw.get("supported_capabilities", ())))

    if not supported_capabilities:
        raise DistributedOSViolation("supported_capabilities required")
    for capability in supported_capabilities:
        _require_identity(capability, "capability")

    return HardwareDevice(
        device_id=device_id,
        device_type=device_type,
        supported_capabilities=supported_capabilities,
    )


def _preferred_device_type(capability: Any) -> str:
    if capability in {"gpu", "matrix"}:
        return "gpu"
    if capability in {"vector", "simd"}:
        return "vector_unit"
    return "cpu"


def _canonical_copy(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise DistributedOSViolation("snapshot state must be a mapping")
    return json.loads(json.dumps(value, sort_keys=True))


def _required_string(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    _require_identity(value, field)
    return value


def _require_identity(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise DistributedOSViolation(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise DistributedOSViolation(f"{field} contains forbidden path syntax")
