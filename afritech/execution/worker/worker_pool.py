"""Partition-aware worker pool controls for the production MVP pipeline."""

from __future__ import annotations

from typing import List, Optional

from afritech.core.runtime.worker.worker import process_event
from afritech.execution.queue.partitioned_queue import PartitionedQueue
from afritech.execution.worker.types import WorkerResult


class WorkerPool:
    """Run deterministic worker cycles over declared queue partitions."""

    def __init__(self, queue: PartitionedQueue) -> None:
        self.queue = queue

    # ---------------------------------------------------------
    # INTERNAL VALIDATION
    # ---------------------------------------------------------

    def _validate_result(self, result: object) -> WorkerResult:
        """
        Enforce canonical WorkerResult output.

        This is a HARD boundary:
        - No coercion (prevents silent semantic drift)
        - No partial results
        """
        if not isinstance(result, WorkerResult):
            raise TypeError(
                f"Non-canonical worker result detected: {type(result)}. "
                "All worker executions must return WorkerResult."
            )
        return result

    # ---------------------------------------------------------
    # EXECUTION
    # ---------------------------------------------------------

    def run_partition_once(self, partition_id: int) -> Optional[WorkerResult]:
        """
        Execute one deterministic worker cycle for a partition.

        Returns:
            WorkerResult | None
        """
        event = self.queue.consume(partition_id)

        if event is None:
            return None

        result = process_event(
            event,
            partition_id=partition_id,
            flow_trace={"stages": ["adapter", "normalization", "ingestion"]},
        )

        # ✅ HARD ENFORCEMENT
        return self._validate_result(result)

    # ---------------------------------------------------------
    # DRAIN (MULTI-EVENT EXECUTION)
    # ---------------------------------------------------------

    def drain(self, partition_id: Optional[int] = None) -> List[WorkerResult]:
        """
        Drain one or all partitions deterministically.

        Returns:
            List[WorkerResult]
        """
        outputs: List[WorkerResult] = []

        partitions = (
            range(self.queue.num_partitions)
            if partition_id is None
            else range(partition_id, partition_id + 1)
        )

        for current_partition in partitions:
            while True:
                result = self.run_partition_once(current_partition)

                if result is None:
                    break

                outputs.append(result)

        return outputs
