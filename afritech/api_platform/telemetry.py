"""Telemetry for the API platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TelemetrySnapshot:
    counters: dict[str, int] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


class TelemetryRecorder:
    def __init__(self) -> None:
        self.snapshot = TelemetrySnapshot()

    def increment(self, metric: str) -> None:
        self.snapshot.counters[metric] = self.snapshot.counters.get(metric, 0) + 1

    def emit(self, event: dict[str, Any]) -> None:
        self.snapshot.events.append(event)
