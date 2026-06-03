from __future__ import annotations

from collections import defaultdict
from typing import Any

from afritech.execution.partition.router import get_partition


class PartitionSimulator:
    def __init__(self, *, num_partitions: int = 8) -> None:
        if num_partitions <= 0:
            raise ValueError("num_partitions must be positive")
        self.num_partitions = num_partitions

    def split(
        self,
        events: tuple[dict[str, Any], ...],
    ) -> tuple[tuple[dict[str, Any], ...], ...]:
        partitions: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            partition_id = get_partition(event, self.num_partitions)
            partitioned_event = {
                **event,
                "partition_id": partition_id,
                "partition_sequence": len(partitions[partition_id]),
            }
            partitions[partition_id].append(partitioned_event)

        return tuple(
            tuple(partitions.get(partition_id, ()))
            for partition_id in range(self.num_partitions)
        )

    def canonical_order(
        self,
        events: tuple[dict[str, Any], ...],
    ) -> tuple[dict[str, Any], ...]:
        split_partitions = self.split(events)
        return tuple(event for partition in split_partitions for event in partition)
