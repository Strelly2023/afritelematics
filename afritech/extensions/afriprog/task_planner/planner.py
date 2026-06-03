from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from afritech.extensions.afriprog.task_planner.failure_parser import (
    FailureParser,
)
from afritech.extensions.afriprog.task_planner.task_model import Task
from afritech.extensions.afriprog.task_planner.task_types import (
    RiskLevel,
    TaskType,
    get_task_metadata,
)


class TaskPlannerError(Exception):
    """Raised when task planning fails."""


@dataclass(frozen=True)
class PlanningDecision:
    task_type: TaskType
    description: str
    risk_level: RiskLevel
    requires_write: bool
    signals: tuple[str, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "task_type": self.task_type.value,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "requires_write": self.requires_write,
            "signals": list(self.signals),
        }


class TaskPlanner:
    """
    Deterministic read-only task planner.

    Constitutional properties:
    - read-only
    - deterministic task IDs
    - inference only
    - no writes
    - non-authoritative
    """

    def __init__(self, task_prefix: str = "TASK"):
        if not task_prefix.strip():
            raise TaskPlannerError("task_prefix must not be empty")

        self.task_prefix = task_prefix
        self.counter = 0

    def _next_id(self) -> str:
        self.counter += 1
        return f"{self.task_prefix}-{self.counter:04d}"

    def plan_from_failure(
        self,
        failure_text: str,
        related_tests: Iterable[str],
        candidate_files: Iterable[str],
    ) -> Task:
        if not isinstance(failure_text, str):
            raise TaskPlannerError("failure_text must be a string")

        parser = FailureParser(failure_text)
        signals = parser.signal_names()

        decision = self._decide(signals)

        return Task(
            task_id=self._next_id(),
            task_type=decision.task_type.value,
            description=decision.description,
            target_files=tuple(sorted(str(item) for item in candidate_files)),
            risk_level=decision.risk_level.value,
            requires_write=False,
            source_tests=tuple(sorted(str(item) for item in related_tests)),
        )

    def plan_many_from_failures(
        self,
        failures: Iterable[str],
        related_tests: Iterable[str] = (),
        candidate_files: Iterable[str] = (),
    ) -> tuple[Task, ...]:
        return tuple(
            self.plan_from_failure(
                failure_text=failure,
                related_tests=related_tests,
                candidate_files=candidate_files,
            )
            for failure in failures
        )

    def _decide(
        self,
        signals: tuple[str, ...],
    ) -> PlanningDecision:
        signal_set = set(signals)

        if "missing_element" in signal_set or "import_error" in signal_set:
            task_type = TaskType.MISSING_ELEMENT
            metadata = get_task_metadata(task_type)

            return PlanningDecision(
                task_type=task_type,
                description="Investigate missing implementation element.",
                risk_level=metadata.default_risk,
                requires_write=False,
                signals=tuple(sorted(signal_set)),
            )

        if "assertion_failure" in signal_set:
            task_type = TaskType.TEST_FAILURE
            metadata = get_task_metadata(task_type)

            return PlanningDecision(
                task_type=task_type,
                description="Investigate failing assertion.",
                risk_level=metadata.default_risk,
                requires_write=False,
                signals=tuple(sorted(signal_set)),
            )

        if "runtime_error" in signal_set or "syntax_error" in signal_set:
            task_type = TaskType.FIX
            metadata = get_task_metadata(task_type)

            return PlanningDecision(
                task_type=task_type,
                description="Investigate runtime or syntax failure.",
                risk_level=metadata.default_risk,
                requires_write=False,
                signals=tuple(sorted(signal_set)),
            )

        if "validation_failure" in signal_set:
            task_type = TaskType.VALIDATION_FAILURE
            metadata = get_task_metadata(task_type)

            return PlanningDecision(
                task_type=task_type,
                description="Investigate validator failure.",
                risk_level=metadata.default_risk,
                requires_write=False,
                signals=tuple(sorted(signal_set)),
            )

        task_type = TaskType.UNKNOWN
        metadata = get_task_metadata(task_type)

        return PlanningDecision(
            task_type=task_type,
            description="Unclassified failure; read-only investigation required.",
            risk_level=metadata.default_risk,
            requires_write=False,
            signals=tuple(sorted(signal_set)),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "task_prefix": self.task_prefix,
            "tasks_planned": self.counter,
            "mode": "READ_ONLY",
        }