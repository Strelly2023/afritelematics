"""Event publishing helper for integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass(frozen=True, slots=True)
class IntegrationEvent:
    event_id: str
    product_code: str
    event_type: str
    payload: dict[str, object]
    correlation_id: str
    occurred_at: float = field(default_factory=time)


@dataclass(slots=True)
class IntegrationEventClient:
    events: list[IntegrationEvent] = field(default_factory=list)

    def publish(self, event: IntegrationEvent) -> IntegrationEvent:
        self.events.append(event)
        return event

