from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.command_center.task_dispatcher import DispatchResult


@dataclass(frozen=True)
class LifecycleSnapshot:
    intent: str
    task_count: int
    admitted_count: int
    rejected_count: int
    write_enabled: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "task_count": self.task_count,
            "admitted_count": self.admitted_count,
            "rejected_count": self.rejected_count,
            "write_enabled": self.write_enabled,
            "status": "green" if self.rejected_count == 0 else "attention_required",
        }


class LifecycleMonitor:
    """Summarize an Afriprog autonomous coding lifecycle."""

    def snapshot(self, result: DispatchResult) -> LifecycleSnapshot:
        admitted = sum(1 for execution in result.executions if execution.review.admitted)
        rejected = len(result.executions) - admitted

        return LifecycleSnapshot(
            intent=result.generated.intent,
            task_count=len(result.generated.tasks),
            admitted_count=admitted,
            rejected_count=rejected,
            write_enabled=False,
        )
