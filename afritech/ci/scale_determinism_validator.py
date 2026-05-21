from __future__ import annotations

import sys

from afritech.simulation.scale.cluster_simulator import (
    ClusterSimulator,
    hash_scale_trace,
)
from afritech.simulation.scale.failure_injector import FailureInjector
from afritech.simulation.scale.load_generator import LoadGenerator


def run() -> None:
    events = LoadGenerator().generate(2_000, seed=401)
    cluster = ClusterSimulator(num_partitions=16)
    workers = tuple(f"worker-{index}" for index in range(10))
    surviving_workers = FailureInjector().kill_workers(workers, percentage=0.4)

    trace_a = cluster.execute(events, workers=surviving_workers)
    trace_b = cluster.execute(events, workers=surviving_workers)
    if hash_scale_trace(trace_a) != hash_scale_trace(trace_b):
        raise RuntimeError("Scale trace hash mismatch")

    midpoint = len(events) // 2
    left = cluster.execute(events[:midpoint], workers=surviving_workers)
    right = cluster.execute(events[midpoint:], workers=surviving_workers)
    merged = cluster.merge(left, right)
    if hash_scale_trace(merged) != hash_scale_trace(trace_a):
        raise RuntimeError("Partition merge did not converge")

    print("✅ Scale determinism validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Scale determinism validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
