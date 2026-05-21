"""Partitioned in-process queue for deterministic scalable pipeline tests."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class PartitionedQueue:
    """FIFO queue set with explicit partition admission and consumption."""

    def __init__(self, num_partitions: int = 8) -> None:
        if num_partitions <= 0:
            raise ValueError("num_partitions must be positive")

        self.num_partitions = num_partitions
        self._partitions: tuple[deque[dict[str, Any]], ...] = tuple(
            deque() for _ in range(num_partitions)
        )

    def publish(self, event: Mapping[str, Any], partition_id: int) -> None:
        self._validate_partition(partition_id)
        self._partitions[partition_id].append(deepcopy(dict(event)))

    def consume(self, partition_id: int) -> dict[str, Any] | None:
        self._validate_partition(partition_id)
        if not self._partitions[partition_id]:
            return None

        return self._partitions[partition_id].popleft()

    def is_empty(self, partition_id: int | None = None) -> bool:
        if partition_id is not None:
            self._validate_partition(partition_id)
            return not self._partitions[partition_id]

        return all(not partition for partition in self._partitions)

    def clear(self) -> None:
        for partition in self._partitions:
            partition.clear()

    def _validate_partition(self, partition_id: int) -> None:
        if partition_id < 0 or partition_id >= self.num_partitions:
            raise ValueError("partition_id outside configured partition range")

