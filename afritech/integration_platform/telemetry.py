"""Telemetry recorder for integration runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass(slots=True)
class IntegrationTelemetryRecorder:
    events: list[dict[str, object]] = field(default_factory=list)

    def record(self, event_type: str, **attributes: object) -> dict[str, object]:
        event = {"event_type": event_type, "timestamp": time(), **attributes}
        self.events.append(event)
        return event

