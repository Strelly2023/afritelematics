from __future__ import annotations

import sys

from afritech.simulation.distributed.convergence_engine import ConvergenceEngine
from afritech.simulation.distributed.partition_simulator import PartitionSimulator
from afritech.simulation.validation_receipt import build_validation_receipt


def _events() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "request_id": f"req-{index:04d}",
            "trip_id": f"trip-{index // 3:04d}",
            "city_id": f"city-{index % 5}",
            "sequence": index,
        }
        for index in range(250)
    )


def build_receipt():
    events = _events()
    partitioner = PartitionSimulator(num_partitions=8)
    convergence = ConvergenceEngine()

    canonical = partitioner.canonical_order(events)
    partitions = partitioner.split(events)
    converged_a = convergence.converge(partitions)
    converged_b = convergence.converge(tuple(reversed(partitions)))

    if converged_a != converged_b:
        raise RuntimeError("Cross-partition convergence is order dependent")
    if converged_a != canonical:
        raise RuntimeError("Cross-partition convergence differs from canonical order")

    convergence_hash = convergence.convergence_hash(converged_a)
    return build_validation_receipt(
        surface="afritech.simulation.distributed.convergence_engine",
        validator="afritech.ci.convergence_validator",
        inputs={
            "event_count": len(events),
            "num_partitions": 8,
        },
        outputs={"convergence_hash": convergence_hash},
        trace=converged_a,
        evidence=(
            "convergence_trace_validation",
            "merge_hash_equivalence",
            "cross_partition_replay_verification",
        ),
    )


def run() -> None:
    receipt = build_receipt()
    if not receipt.deterministic or not receipt.replay_safe:
        raise RuntimeError("Convergence validation receipt is not replay safe")
    print("✅ Convergence validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Convergence validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
