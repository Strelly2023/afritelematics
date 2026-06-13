"""AfriPay metrics and tracing primitives."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class MetricsRegistry:
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    histograms: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] += value

    def observe(self, name: str, value: float) -> None:
        self.histograms[name].append(value)

    def snapshot(self) -> dict[str, Any]:
        return {
            "counters": dict(self.counters),
            "histograms": {key: list(values) for key, values in self.histograms.items()},
        }


@dataclass(frozen=True)
class TraceSpan:
    name: str
    duration_ms: float
    attributes: dict[str, object]


class Tracer:
    def __init__(self) -> None:
        self._spans: list[TraceSpan] = []

    def record(self, name: str, started_at: float, **attributes: object) -> TraceSpan:
        span = TraceSpan(name, (perf_counter() - started_at) * 1000, dict(attributes))
        self._spans.append(span)
        return span

    def spans(self) -> tuple[TraceSpan, ...]:
        return tuple(self._spans)
