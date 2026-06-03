from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.task_planner.task_model import Task


@dataclass(frozen=True)
class CodePlan:
    task_id: str
    target_files: tuple[str, ...]
    operations: tuple[str, ...]
    validation_commands: tuple[tuple[str, ...], ...]
    plan_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "target_files": list(self.target_files),
            "operations": list(self.operations),
            "validation_commands": [list(command) for command in self.validation_commands],
            "plan_hash": self.plan_hash,
        }


class CodePlanner:
    """Translate a generated task into a deterministic code plan."""

    def plan(self, task: Task) -> CodePlan:
        operations = self._operations(task)
        validation_commands = (
            ("python3", "-m", "compileall", "afritech/extensions/afriprog"),
            ("python3", "-m", "pytest", "-q", "afritech/tests/extensions/afriprog"),
        )
        material = "|".join(
            (
                task.task_id,
                task.task_type,
                ",".join(task.target_files),
                ",".join(operations),
            )
        )

        return CodePlan(
            task_id=task.task_id,
            target_files=task.target_files,
            operations=operations,
            validation_commands=validation_commands,
            plan_hash=hashlib.sha256(material.encode("utf-8")).hexdigest(),
        )

    def _operations(self, task: Task) -> tuple[str, ...]:
        if task.task_type == "test_failure":
            return ("generate_test_cases", "bind_validation_command")
        if task.task_type == "refactor":
            return ("inspect_existing_surface", "propose_refactor")
        if task.task_type == "bug_fix":
            return ("reproduce_failure", "propose_fix", "rerun_validation")
        if task.task_type == "documentation":
            return ("draft_documentation", "review_claims")
        if task.task_type == "missing_element":
            return ("scaffold_missing_element", "generate_contract_stub")
        return ("investigate", "propose_next_step")
