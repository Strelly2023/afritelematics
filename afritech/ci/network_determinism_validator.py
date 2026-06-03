from __future__ import annotations

import sys
from typing import Any

from afritech.simulation.distributed.convergence_engine import ConvergenceEngine
from afritech.simulation.distributed.message_scheduler import MessageScheduler
from afritech.simulation.distributed.network_model import NetworkModel
from afritech.simulation.distributed.network_trace import NetworkTrace
from afritech.simulation.distributed.partition_simulator import PartitionSimulator
from afritech.simulation.validation_receipt import build_validation_receipt
#afritech.ci.network_determinism_validator

def validate_network_replay(trace1: Any, trace2: Any) -> None:
    if trace1 != trace2:
        raise AssertionError("Network nondeterminism detected")


def build_receipt():
    messages = tuple(
        {
            "id": f"m{index:03d}",
            "timestamp": index,
            "request_id": f"req-{index:03d}",
            "trip_id": f"trip-{index:03d}",
            "city_id": f"city-{index % 4}",
        }
        for index in range(64)
    )
    scheduler = MessageScheduler()
    model = NetworkModel(seed=42)
    simulator = PartitionSimulator(num_partitions=8)
    engine = ConvergenceEngine()

    canonical_messages = scheduler.schedule(messages)
    trace_a = model.trace(canonical_messages)
    trace_b = model.trace(scheduler.schedule(reversed(messages)))
    validate_network_replay(trace_a, trace_b)

    delivered = model.transmit(canonical_messages)
    converged_a = engine.converge(simulator.split(model.canonical_delivery(delivered)))
    converged_b = engine.converge(
        simulator.split(model.canonical_delivery(tuple(reversed(delivered))))
    )
    validate_network_replay(converged_a, converged_b)

    return build_validation_receipt(
        surface="afritech.simulation.distributed.network_model",
        validator="afritech.ci.network_determinism_validator",
        inputs=messages,
        outputs={
            "network_trace_hash": NetworkTrace.hash_trace(trace_a),
            "convergence_hash": engine.convergence_hash(converged_a),
        },
        trace={
            "network_trace": trace_a,
            "converged_trace": converged_a,
        },
        evidence=(
            "network_event_replay",
            "deterministic_latency_trace",
            "controlled_reordering_trace",
            "convergence_trace_validation",
        ),
    )


def run() -> None:
    receipt = build_receipt()
    if not receipt.deterministic or not receipt.replay_safe:
        raise RuntimeError("Network determinism receipt is not replay safe")
    print("Network determinism validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Network determinism validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
