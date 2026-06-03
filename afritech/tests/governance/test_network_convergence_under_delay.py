from __future__ import annotations

from afritech.simulation.distributed.convergence_engine import ConvergenceEngine
from afritech.simulation.distributed.network_model import NetworkModel
from afritech.simulation.distributed.partition_simulator import PartitionSimulator


def _events(count: int = 50) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "id": f"m{index:03d}",
            "timestamp": index,
            "request_id": f"req-{index:03d}",
            "trip_id": f"trip-{index:03d}",
            "city_id": f"city-{index % 4}",
        }
        for index in range(count)
    )


def test_network_convergence() -> None:
    model = NetworkModel(seed=42)
    simulator = PartitionSimulator(num_partitions=6)
    engine = ConvergenceEngine()
    events = _events()

    part1 = events[:25]
    part2 = events[25:]

    delivered1 = model.transmit(part1)
    delivered2 = model.transmit(part2)
    partitions = simulator.split(delivered1 + delivered2)

    merged = engine.converge(partitions)
    merged2 = engine.converge(tuple(reversed(partitions)))

    assert merged == merged2
    assert engine.convergence_hash(merged) == engine.convergence_hash(merged2)


def test_network_convergence_is_stable_under_arrival_reordering() -> None:
    model = NetworkModel(seed=202)
    simulator = PartitionSimulator(num_partitions=8)
    engine = ConvergenceEngine()
    events = _events(80)

    delivered = model.transmit(events)
    delayed_arrival = tuple(reversed(delivered))

    converged_a = engine.converge(simulator.split(model.canonical_delivery(delivered)))
    converged_b = engine.converge(
        simulator.split(model.canonical_delivery(delayed_arrival))
    )

    assert converged_a == converged_b
