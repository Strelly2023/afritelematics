"""
afritech.simulation.scale.cluster_simulator

Deterministic multi-node distributed simulation engine.

Guarantees:
- Partition-consistent execution
- Deterministic worker assignment
- Replay-stable output
- Failure-safe execution
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Any, Mapping, Sequence, Dict, List

from afritech.distributed.api.partition import (
    assign_partition,
    default_partition_registry,
)

from afritech.distributed.api.worker import (
    build_default_worker_node,
    DeterministicWorkerNode,
)

from afritech.distributed.api.queue import (
    build_queue_record,
)

from afritech.simulation.scale.failure_injector import (
    safe_execute_with_injection,
)


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class SimulationResult:
    execution_hashes: tuple[str, ...]
    processed_events: int
    worker_count: int
    partition_count: int

    def is_deterministic_with(self, other: "SimulationResult") -> bool:
        return self.execution_hashes == other.execution_hashes


# ============================================================
# CLUSTER SIMULATOR
# ============================================================

class DeterministicClusterSimulator:

    def __init__(
        self,
        *,
        worker_count: int | None = None,
        num_partitions: int | None = None,
    ):
        if worker_count is None:
            worker_count = num_partitions or 1

        if worker_count <= 0:
            raise ValueError("worker_count must be > 0")

        self._registry = default_partition_registry()

        # ---------------------------------------------------------
        # Workers (ALL partitions assigned by default builder)
        # ---------------------------------------------------------
        self._workers: tuple[DeterministicWorkerNode, ...] = tuple(
            build_default_worker_node(worker_id=f"worker_{i}")
            for i in range(worker_count)
        )

        self._partition_ids = tuple(sorted(self._registry.partition_ids))

        # ---------------------------------------------------------
        # Deterministic partition → worker mapping
        # ---------------------------------------------------------
        self._partition_owner: Dict[str, DeterministicWorkerNode] = {}

        for i, pid in enumerate(self._partition_ids):
            self._partition_owner[pid] = self._workers[i % worker_count]

    # ---------------------------------------------------------
    # RUN
    # ---------------------------------------------------------

    def run(
        self,
        *,
        events: Sequence[Mapping[str, object]],
        inject_failures: bool = False,
    ) -> SimulationResult:

        execution_hashes: List[str] = []
        partition_sequences = defaultdict(int)

        for idx, event in enumerate(events):

            # -----------------------------------------------------
            # Partition assignment
            # -----------------------------------------------------
            assignment = assign_partition(
                routing_key=event["routing_key"],
                routing_scope=event["routing_scope"],
                registry=self._registry,
            )

            pid = assignment.partition_id
            seq = partition_sequences[pid]

            # -----------------------------------------------------
            # Record construction
            # -----------------------------------------------------
            record = build_queue_record(
                event_id=event["event_id"],
                sequence=seq,
                normalized_payload_hash=_deterministic_payload_hash(event),
                event=event,
                assignment=assignment,
                registry=self._registry,
            )

            partition_sequences[pid] += 1

            # -----------------------------------------------------
            # Select worker
            # -----------------------------------------------------
            worker = self._partition_owner[pid]

            # -----------------------------------------------------
            # Optional failure injection
            # -----------------------------------------------------
            if inject_failures:
                outcome = safe_execute_with_injection(worker, record, idx)
                if outcome is None:
                    continue
            else:
                outcome = worker.execute(record)

            result = outcome.result

            # -----------------------------------------------------
            # Collect deterministic output hash
            # -----------------------------------------------------
            execution_hashes.append(result.execution_hash)

        return SimulationResult(
            execution_hashes=tuple(execution_hashes),
            processed_events=len(events),
            worker_count=len(self._workers),
            partition_count=len(self._partition_ids),
        )

    def execute(
        self,
        events: Sequence[Mapping[str, object]],
        *,
        workers: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Legacy dictionary trace API used by governance validators."""
        active_workers = tuple(workers or (f"worker-{index}" for index in range(len(self._workers))))
        if not active_workers:
            raise ValueError("workers must be non-empty")

        records: List[dict[str, Any]] = []
        partition_sequences = defaultdict(int)

        for idx, event in enumerate(events):
            event_index = _event_index(event)
            assignment = assign_partition(
                routing_key=event["routing_key"],
                routing_scope=event["routing_scope"],
                registry=self._registry,
            )
            pid = assignment.partition_id
            seq = event_index
            partition_sequences[pid] += 1
            worker_id = active_workers[event_index % len(active_workers)]

            records.append(
                {
                    "event_id": event["event_id"],
                    "partition_id": pid,
                    "partition_sequence": seq,
                    "worker_id": worker_id,
                    "payload_hash": _deterministic_payload_hash(event),
                }
            )

        return {
            "records": records,
            "processed_events": len(records),
            "workers": active_workers,
            "partition_count": len(self._partition_ids),
        }

    def merge(self, left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
        """Merge legacy traces into the same canonical order as a full run."""
        records = list(left.get("records", ())) + list(right.get("records", ()))
        records.sort(key=lambda item: str(item["event_id"]))

        return {
            "records": records,
            "processed_events": len(records),
            "workers": tuple(left.get("workers", ())) or tuple(right.get("workers", ())),
            "partition_count": left.get("partition_count", right.get("partition_count")),
        }


# ============================================================
# PUBLIC RUNNER
# ============================================================

def run_cluster_simulation(
    *,
    worker_count: int,
    events: Sequence[Mapping[str, object]],
    inject_failures: bool = False,
) -> SimulationResult:
    """
    Convenience wrapper.
    """

    simulator = DeterministicClusterSimulator(
        worker_count=worker_count
    )

    return simulator.run(
        events=events,
        inject_failures=inject_failures,
    )


ClusterSimulator = DeterministicClusterSimulator


def hash_scale_trace(trace: Mapping[str, Any] | SimulationResult) -> str:
    import hashlib
    import json

    if isinstance(trace, SimulationResult):
        payload: Any = {
            "execution_hashes": trace.execution_hashes,
            "processed_events": trace.processed_events,
            "worker_count": trace.worker_count,
            "partition_count": trace.partition_count,
        }
    else:
        payload = trace

    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=list).encode()
    ).hexdigest()


# ============================================================
# TEST UTILITIES
# ============================================================

def generate_test_events(count: int) -> List[Mapping[str, object]]:
    """
    Deterministic event generator.
    """
    events = []

    for i in range(count):
        events.append({
            "event_id": f"event.sim.{i:06d}",
            "routing_key": f"ride.sim.{i % 10:03d}",  # controlled distribution
            "routing_scope": "rides",
            "payload": {
                "rider_id": f"rider.{i:06d}",
                "pickup": "melbourne.cbd",
                "dropoff": "melbourne.airport",
            },
        })

    return events


# ============================================================
# INTERNAL
# ============================================================

def _deterministic_payload_hash(event: Mapping[str, object]) -> str:
    """
    Stable payload hashing for simulation.

    NOTE: simplified for simulation — real system uses normalized payload
    """
    import hashlib
    import json

    return hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _event_index(event: Mapping[str, object]) -> int:
    event_id = str(event.get("event_id", "0"))
    suffix = event_id.rsplit(".", 1)[-1]
    try:
        return int(suffix)
    except ValueError:
        return 0
