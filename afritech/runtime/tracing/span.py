from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Dict
import uuid


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def finish(self) -> None:
        self.end_time = time.time()

    def duration_ms(self) -> float:
        end = self.end_time if self.end_time is not None else time.time()
        return (end - self.start_time) * 1000

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms(),
            "metadata": dict(self.metadata),
        }
