from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afritech.extensions.afriprog.task_planner.task_model import Task
from afritech.extensions.afriprog.task_planner.task_types import (
    RiskLevel,
    TaskType,
    get_task_metadata,
)


class TaskGeneratorError(Exception):
    """Raised when intent cannot be converted into deterministic tasks."""


@dataclass(frozen=True)
class GeneratedTaskSet:
    intent: str
    tasks: tuple[Task, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "task_count": len(self.tasks),
            "tasks": [task.canonical_dict() for task in self.tasks],
            "engine": "afriprog.ai_engine.task_generator",
        }


class TaskGenerator:
    """
    Deterministic task brain for Afriprog.

    Converts high-level intent into bounded engineering tasks. It does not call
    an external model; GA Elite behavior here is replayable and auditable.
    """

    DEFAULT_SURFACE = "afritech/extensions/afriprog/generated"

    def generate(
        self,
        intent: str,
        *,
        surface_root: str = DEFAULT_SURFACE,
    ) -> GeneratedTaskSet:
        if not isinstance(intent, str) or not intent.strip():
            raise TaskGeneratorError("intent must be a non-empty string")

        normalized_intent = " ".join(intent.strip().split())
        slug = _slug(normalized_intent)
        target = f"{surface_root.rstrip('/')}/{slug}.py"
        test_target = f"{surface_root.rstrip('/')}/test_{slug}.py"

        task_specs = self._task_specs(normalized_intent)
        tasks = tuple(
            Task(
                task_id=f"TASK-{index:03d}",
                task_type=task_type.value,
                description=description,
                target_files=tuple(sorted(target_files)),
                risk_level=get_task_metadata(task_type).default_risk.value,
                requires_write=False,
                source_tests=tuple(sorted(source_tests)),
            )
            for index, (task_type, description, target_files, source_tests) in enumerate(
                task_specs(target, test_target),
                start=1,
            )
        )

        return GeneratedTaskSet(intent=normalized_intent, tasks=tasks)

    def _task_specs(self, intent: str):
        lower = intent.lower()

        def specs(target: str, test_target: str):
            if any(token in lower for token in ("auth", "jwt", "token", "login")):
                return (
                    (
                        TaskType.REFACTOR,
                        f"Design controlled authentication implementation for: {intent}",
                        (target,),
                        (),
                    ),
                    (
                        TaskType.TEST_FAILURE,
                        f"Generate authentication validation tests for: {intent}",
                        (test_target,),
                        (test_target,),
                    ),
                    (
                        TaskType.FIX,
                        f"Investigate token expiry and validation behavior for: {intent}",
                        (target,),
                        (test_target,),
                    ),
                )

            if any(token in lower for token in ("test", "coverage", "pytest")):
                return (
                    (
                        TaskType.TEST_FAILURE,
                        f"Generate missing test coverage for: {intent}",
                        (test_target,),
                        (test_target,),
                    ),
                    (
                        TaskType.VALIDATION_FAILURE,
                        f"Plan validation loop for: {intent}",
                        (test_target,),
                        (test_target,),
                    ),
                )

            if any(token in lower for token in ("doc", "readme", "explain")):
                return (
                    (
                        TaskType.DOCUMENTATION,
                        f"Draft documentation update for: {intent}",
                        (f"{Path(target).with_suffix('.md')}",),
                        (),
                    ),
                )

            return (
                (
                    TaskType.INVESTIGATION,
                    f"Decompose and investigate implementation intent: {intent}",
                    (target,),
                    (),
                ),
                (
                    TaskType.MISSING_ELEMENT,
                    f"Generate missing implementation scaffold for: {intent}",
                    (target,),
                    (),
                ),
                (
                    TaskType.TEST_FAILURE,
                    f"Generate validation tests for: {intent}",
                    (test_target,),
                    (test_target,),
                ),
            )

        return specs


def _slug(value: str) -> str:
    normalized = "".join(
        character.lower() if character.isalnum() else "_"
        for character in value
    )
    collapsed = "_".join(part for part in normalized.split("_") if part)
    if collapsed:
        return collapsed[:48]
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
