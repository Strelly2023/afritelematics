from __future__ import annotations

import hashlib
import json
from typing import Any


class ClusterSimulator:
    def __init__(self, *, num_partitions: int = 8) -> None:
        if num_partitions <= 0:
            raise ValueError("num_partitions must be positive")
        self.num_partitions = num_partitions

    def execute(
        self,
        events: tuple[dict[str, Any], ...],
        *,
        workers: tuple[str, ...] = ("worker-0",),
    ) -> tuple[dict[str, Any], ...]:
        if not workers:
            raise ValueError("at least one worker is required")

        results = [self._process(event, workers=workers) for event in events]
        return tuple(sorted(results, key=lambda item: (item["partition"], item["ride_id"])))

    def _process(
        self,
        event: dict[str, Any],
        *,
        workers: tuple[str, ...],
    ) -> dict[str, Any]:
        partition = self._partition_for(str(event["ride_id"]))
        worker = workers[partition % len(workers)]
        return {
            "ride_id": event["ride_id"],
            "user_id": event["user_id"],
            "sequence": int(event["sequence"]),
            "partition": partition,
            "worker": worker,
            "event_hash": self._event_hash(event),
        }

    def merge(
        self,
        *partitions: tuple[dict[str, Any], ...],
    ) -> tuple[dict[str, Any], ...]:
        merged = [item for partition in partitions for item in partition]
        return tuple(sorted(merged, key=lambda item: (item["partition"], item["ride_id"])))

    def _partition_for(self, key: str) -> int:
        digest = hashlib.sha256(key.encode()).hexdigest()
        return int(digest[:16], 16) % self.num_partitions

    def _event_hash(self, event: dict[str, Any]) -> str:
        payload = json.dumps(event, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def hash_scale_trace(trace: tuple[dict[str, Any], ...]) -> str:
    payload = json.dumps(trace, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
