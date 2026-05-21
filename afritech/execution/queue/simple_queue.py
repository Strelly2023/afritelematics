"""Simple in-process queue for deterministic MVP pipeline tests."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class SimpleQueue:
    """FIFO queue with explicit publish and consume operations."""

    def __init__(self) -> None:
        self._events: deque[dict[str, Any]] = deque()

    def publish(self, event: Mapping[str, Any]) -> None:
        self._events.append(deepcopy(dict(event)))

    def consume(self) -> dict[str, Any]:
        if not self._events:
            raise IndexError("Cannot consume from an empty queue")

        return self._events.popleft()

    def is_empty(self) -> bool:
        return not self._events

