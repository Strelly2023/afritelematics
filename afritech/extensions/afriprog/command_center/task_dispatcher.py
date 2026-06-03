from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.ai_engine.task_generator import (
    GeneratedTaskSet,
    TaskGenerator,
)
from afritech.extensions.afriprog.command_center.execution_engine import (
    ExecutionEngine,
    ExecutionResult,
)


@dataclass(frozen=True)
class DispatchResult:
    generated: GeneratedTaskSet
    executions: tuple[ExecutionResult, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "generated": self.generated.canonical_dict(),
            "executions": [
                execution.canonical_dict()
                for execution in self.executions
            ],
            "status": (
                "admitted"
                if all(execution.review.admitted for execution in self.executions)
                else "rejected"
            ),
            "write_enabled": False,
        }


class TaskDispatcher:
    """Intent-to-task-to-code command center."""

    def __init__(
        self,
        *,
        task_generator: TaskGenerator | None = None,
        execution_engine: ExecutionEngine | None = None,
    ) -> None:
        self.task_generator = task_generator or TaskGenerator()
        self.execution_engine = execution_engine or ExecutionEngine()

    def dispatch(self, intent: str) -> DispatchResult:
        generated = self.task_generator.generate(intent)
        executions = tuple(
            self.execution_engine.execute(task)
            for task in generated.tasks
        )

        return DispatchResult(
            generated=generated,
            executions=executions,
        )
