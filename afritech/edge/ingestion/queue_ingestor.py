"""Queue-mediated ingestion for normalized edge events."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Protocol


class PublishQueue(Protocol):
    """Minimal queue protocol required for deterministic edge ingestion."""

    def publish(self, event: Mapping[str, Any]) -> None:
        """Publish a normalized event."""


def ingest_event(normalized_input: Mapping[str, Any], queue: PublishQueue) -> None:
    """Enqueue a normalized deterministic event through a declared queue."""

    queue.publish(deepcopy(dict(normalized_input)))

