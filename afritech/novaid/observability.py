"""Dependency-free, low-cardinality NovaID telemetry primitives."""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Iterator, Mapping


ALLOWED_LABELS = frozenset({"operation", "outcome", "reason", "strength"})


@dataclass
class NovaIDMetrics:
    values: Counter[tuple[str, tuple[tuple[str, str], ...]]] = field(default_factory=Counter)

    def increment(self, name: str, **labels: str) -> None:
        forbidden = set(labels) - ALLOWED_LABELS
        if forbidden:
            raise ValueError(f"high_cardinality_metric_labels:{','.join(sorted(forbidden))}")
        self.values[(name, tuple(sorted(labels.items())))] += 1

    def prometheus(self) -> str:
        lines: list[str] = []
        for (name, labels), value in sorted(self.values.items()):
            rendered = ""
            if labels:
                rendered = (
                    "{"
                    + ",".join(
                        f'{key}="{item.replace(chr(34), chr(92) + chr(34))}"'
                        for key, item in labels
                    )
                    + "}"
                )
            lines.append(f"{name}{rendered} {value}")
        return "\n".join(lines) + ("\n" if lines else "")


@dataclass
class RecordedSpan:
    name: str
    attributes: dict[str, str]
    error: str | None = None


@dataclass
class NovaIDTracer:
    spans: list[RecordedSpan] = field(default_factory=list)
    export_path: Path | None = None

    @contextmanager
    def span(
        self, name: str, attributes: Mapping[str, str] | None = None
    ) -> Iterator[RecordedSpan]:
        current = RecordedSpan(name, dict(attributes or {}))
        self.spans.append(current)
        try:
            yield current
        except Exception as exc:
            current.error = type(exc).__name__
            raise
        finally:
            if self.export_path:
                payload = {
                    "name": current.name,
                    "attributes": current.attributes,
                    "error": current.error,
                }
                with self.export_path.open("a", encoding="utf-8") as output:
                    output.write(json.dumps(payload, sort_keys=True) + "\n")
