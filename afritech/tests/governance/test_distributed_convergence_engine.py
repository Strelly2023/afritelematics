from __future__ import annotations

import pytest

from afritech.ci import convergence_validator
from afritech.simulation.distributed.convergence_engine import (
    ConvergenceEngine,
    ConvergenceError,
)
from afritech.simulation.distributed.partition_simulator import PartitionSimulator


def _events() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "request_id": f"req-{index:04d}",
            "trip_id": f"trip-{index // 2:04d}",
            "city_id": f"city-{index % 4}",
            "sequence": index,
        }
        for index in range(64)
    )


def test_partition_simulator_produces_stable_canonical_order() -> None:
    events = _events()
    simulator = PartitionSimulator(num_partitions=6)

    assert simulator.split(events) == simulator.split(events)
    assert simulator.canonical_order(events) == simulator.canonical_order(events)


def test_convergence_matches_canonical_partition_order() -> None:
    events = _events()
    simulator = PartitionSimulator(num_partitions=6)
    engine = ConvergenceEngine()

    partitions = simulator.split(events)
    converged = engine.converge(partitions)

    assert converged == simulator.canonical_order(events)
    assert engine.convergence_hash(converged) == engine.convergence_hash(converged)


def test_convergence_is_independent_of_partition_delivery_order() -> None:
    events = _events()
    simulator = PartitionSimulator(num_partitions=6)
    engine = ConvergenceEngine()

    partitions = simulator.split(events)

    assert engine.converge(partitions) == engine.converge(tuple(reversed(partitions)))


def test_convergence_rejects_duplicate_authority_branch() -> None:
    events = _events()
    simulator = PartitionSimulator(num_partitions=6)
    engine = ConvergenceEngine()
    partitions = [list(partition) for partition in simulator.split(events)]

    target_partition = next(partition for partition in partitions if partition)
    duplicate = dict(target_partition[0])
    duplicate["partition_sequence"] = len(target_partition)
    target_partition.append(duplicate)

    with pytest.raises(ConvergenceError, match="duplicate authority branch"):
        engine.converge(tuple(tuple(partition) for partition in partitions))


def test_convergence_validator_emits_stable_receipt() -> None:
    receipt_a = convergence_validator.build_receipt()
    receipt_b = convergence_validator.build_receipt()

    assert receipt_a == receipt_b
    assert receipt_a.replay_hash == receipt_b.replay_hash
    assert receipt_a.surface == "afritech.simulation.distributed.convergence_engine"
    assert "convergence_trace_validation" in receipt_a.evidence


def test_convergence_validator_passes() -> None:
    convergence_validator.run()
