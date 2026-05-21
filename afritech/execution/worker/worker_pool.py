"""Partition-aware worker pool controls for the production MVP pipeline."""

from __future__ import annotations

from afritech.core.runtime.worker.worker import process_event
from afritech.execution.queue.partitioned_queue import PartitionedQueue


class WorkerPool:
    """Run deterministic worker cycles over declared queue partitions."""

    def __init__(self, queue: PartitionedQueue) -> None:
        self.queue = queue

    def run_partition_once(self, partition_id: int) -> dict[str, object] | None:
        event = self.queue.consume(partition_id)
        if event is None:
            return None

        return process_event(
            event,
            partition_id=partition_id,
            flow_trace={"stages": ["adapter", "normalization", "ingestion"]},
        )

    def drain(self, partition_id: int | None = None) -> list[dict[str, object]]:
        outputs: list[dict[str, object]] = []
        partitions = (
            range(self.queue.num_partitions)
            if partition_id is None
            else range(partition_id, partition_id + 1)
        )

        for current_partition in partitions:
            while True:
                output = self.run_partition_once(current_partition)
                if output is None:
                    break
                outputs.append(output)

        return outputs
