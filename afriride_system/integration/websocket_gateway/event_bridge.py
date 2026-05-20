"""In-memory event bridge used by Phase 1 app simulation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppEvent:
    channel: str
    event_type: str
    payload: dict[str, Any]


class EventBridge:
    def __init__(self) -> None:
        self._events: dict[str, list[AppEvent]] = defaultdict(list)

    def publish(
        self,
        channel: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> AppEvent:
        event = AppEvent(
            channel=channel,
            event_type=event_type,
            payload=dict(payload),
        )
        self._events[channel].append(event)
        return event

    def events_for(self, channel: str) -> tuple[AppEvent, ...]:
        return tuple(self._events.get(channel, ()))
