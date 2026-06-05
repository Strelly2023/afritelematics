from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterator, List
import uuid

from afritech.runtime.tracing.span import Span


class Tracer:
    def __init__(self) -> None:
        self._spans: List[Span] = []

    def start_span(self, name: str, trace_id: str | None = None, **metadata) -> Span:
        span = Span(
            name=name,
            trace_id=trace_id or uuid.uuid4().hex,
            metadata=dict(metadata),
        )
        self._spans.append(span)
        return span

    @contextmanager
    def span(self, name: str, trace_id: str | None = None, **metadata) -> Iterator[Span]:
        active = self.start_span(name, trace_id, **metadata)
        try:
            yield active
        finally:
            active.finish()

    def snapshot(self) -> Dict[str, object]:
        return {"spans": [span.to_dict() for span in self._spans]}

    def reset(self) -> None:
        self._spans.clear()
