from __future__ import annotations

from typing import Dict

from afritech.runtime.tracing.tracer import Tracer


class ExecutionTrace:
    def __init__(self, execution_id: str, tracer: Tracer | None = None) -> None:
        self.execution_id = execution_id
        self.tracer = tracer or Tracer()

    def record(self, stage: str, **metadata) -> None:
        with self.tracer.span(stage, execution_id=self.execution_id, **metadata):
            pass

    def snapshot(self) -> Dict[str, object]:
        return {
            "execution_id": self.execution_id,
            **self.tracer.snapshot(),
        }
