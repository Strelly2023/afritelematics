"""Queue-mediated ingestion for normalized edge events."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Protocol


class PublishQueue(Protocol):
    """Minimal queue protocol required for deterministic edge ingestion."""

    def publish(self, event: Mapping[str, Any], partition_id: int | None = None) -> None:
        """Publish a normalized event."""


def ingest_event(
    normalized_input: Mapping[str, Any],
    queue: PublishQueue,
    partition_id: int | None = None,
) -> None:
    """Enqueue a normalized deterministic event through a declared queue."""

    if partition_id is None:
        queue.publish(deepcopy(dict(normalized_input)))
    else:
        queue.publish(deepcopy(dict(normalized_input)), partition_id)
