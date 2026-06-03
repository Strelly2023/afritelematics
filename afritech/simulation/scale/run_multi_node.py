"""
afritech.simulation.scale.run_multi_node

Multi-node distributed simulation runner.

Guarantees:
- Deterministic execution across runs
- Stable partition routing
- Worker scaling invariance
- Optional failure injection
"""

from __future__ import annotations

from collections import defaultdict
from typing import List

from afritech.distributed.api.partition import (
    default_partition_registry,
    assign_partition,
)

from afritech.distributed.api.worker import (
    build_default_worker_node,
)

from afritech.distributed.api.queue import (
    build_queue_record,
)

from afritech.simulation.scale.load_generator import (
    generate_events,
)

from afritech.simulation.scale.failure_injector import (
    apply_failure_strategy,
    FailurePolicy,
)

import hashlib
import json


# ============================================================
# RUNNER
# ============================================================

def run_simulation(
    worker_count: int = 5,
    event_count: int = 50,
    *,
    inject_failures: bool = False,
    failure_rate: int = 10,
) -> List[str]:

    if worker_count <= 0:
        raise ValueError("worker_count must be > 0")

    # ---------------------------------------------------------
    # Registry
    # ---------------------------------------------------------
    registry = default_partition_registry()

    # ---------------------------------------------------------
    # Workers (full partition coverage)
    # ---------------------------------------------------------
    workers = [
        build_default_worker_node(worker_id=f"worker_{i}")
        for i in range(worker_count)
    ]

    # ---------------------------------------------------------
    # Deterministic partition → worker mapping
    # ---------------------------------------------------------
    partition_map = {}
    partitions = tuple(sorted(registry.partition_ids))

    for i, p in enumerate(partitions):
        partition_map[p] = workers[i % worker_count]

    # ---------------------------------------------------------
    # Generate deterministic events
    # ---------------------------------------------------------
    events = generate_events(event_count)

    results: List[str] = []
    partition_sequences = defaultdict(int)

    # ---------------------------------------------------------
    # Failure policy
    # ---------------------------------------------------------
    policy = FailurePolicy(fail_every_n=failure_rate)

    # ---------------------------------------------------------
    # Process events
    # ---------------------------------------------------------
    for idx, e in enumerate(events):

        # -----------------------------------------------------
        # Deterministic partition assignment
        # -----------------------------------------------------
        assignment = assign_partition(
            routing_key=e["routing_key"],
            routing_scope=e["routing_scope"],
            registry=registry,
        )

        pid = assignment.partition_id
        seq = partition_sequences[pid]

        # -----------------------------------------------------
        # Build record (with deterministic payload hash)
        # -----------------------------------------------------
        record = build_queue_record(
            event_id=e["event_id"],
            sequence=seq,
            normalized_payload_hash=_deterministic_payload_hash(e),
            event=e,
            assignment=assignment,
            registry=registry,
        )

        partition_sequences[pid] += 1

        # -----------------------------------------------------
        # Select worker
        # -----------------------------------------------------
        worker = partition_map[pid]

        # -----------------------------------------------------
        # Execute (failure-aware or normal)
        # -----------------------------------------------------
        if inject_failures:
            outcomes = apply_failure_strategy(
                worker,
                record,
                idx,
                policy=policy,
            )

            for outcome in outcomes:
                if outcome is None:
                    continue
                results.append(outcome.result.execution_hash)

        else:
            outcome = worker.execute(record)
            results.append(outcome.result.execution_hash)

    return results


# ============================================================
# UTIL
# ============================================================

def _deterministic_payload_hash(event: dict) -> str:
    """
    Deterministic hash of event payload.

    Ensures replay-safe normalized payload.
    """
    return hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


# ============================================================
# SELF TESTS (PYTEST COMPATIBLE)
# ============================================================

def test_multi_node_determinism():
    a = run_simulation(worker_count=5, event_count=100)
    b = run_simulation(worker_count=5, event_count=100)

    assert a == b, "Non-deterministic execution detected"


def test_worker_scaling_invariance():
    a = run_simulation(worker_count=3, event_count=100)
    b = run_simulation(worker_count=10, event_count=100)

    assert a == b, "Worker scaling changed output"


def test_failure_resilience():
    a = run_simulation(
        worker_count=5,
        event_count=100,
        inject_failures=True,
    )

    b = run_simulation(
        worker_count=5,
        event_count=100,
        inject_failures=True,
    )

    assert a == b, "Failure injection broke determinism"