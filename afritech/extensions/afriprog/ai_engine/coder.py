from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afritech.extensions.afriprog.ai_engine.planner import CodePlan, CodePlanner
from afritech.extensions.afriprog.code_executor.patch_model import (
    Patch,
    PatchMode,
    PatchRiskLevel,
)
from afritech.extensions.afriprog.code_executor.sandbox import (
    SandboxError,
    validate_path,
)
from afritech.extensions.afriprog.task_planner.task_model import Task


class CoderError(Exception):
    """Raised when code synthesis cannot produce a proposal."""


@dataclass(frozen=True)
class CodeGenerationResult:
    task: Task
    plan: CodePlan
    patches: tuple[Patch, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "task": self.task.canonical_dict(),
            "plan": self.plan.canonical_dict(),
            "patches": [patch.canonical_dict() for patch in self.patches],
            "write_enabled": False,
            "mode": "PROPOSAL_ONLY_CODE_GENERATION",
        }


class Coder:
    """
    Code brain for Afriprog.

    Produces concrete patch proposals for tasks. The engine synthesizes code but
    never writes it to disk.
    """

    def __init__(self, planner: CodePlanner | None = None) -> None:
        self.planner = planner or CodePlanner()

    def generate(self, task: Task) -> CodeGenerationResult:
        plan = self.planner.plan(task)
        patches = tuple(
            self._patch_for_target(task, target)
            for target in task.target_files
            if self._is_allowed_target(target)
        )

        if not patches:
            raise CoderError(f"no admissible target files for task: {task.task_id}")

        return CodeGenerationResult(
            task=task,
            plan=plan,
            patches=patches,
        )

    def _patch_for_target(self, task: Task, target: str) -> Patch:
        original = ""
        updated = _generated_content(task, target)

        return Patch(
            file_path=target,
            original_content=original,
            updated_content=updated,
            patch_type=task.task_type,
            risk_level=_patch_risk(task.risk_level),
            mode=PatchMode.PROPOSAL_ONLY.value,
            write_permitted=False,
        )

    def _is_allowed_target(self, target: str) -> bool:
        try:
            validate_path(target)
        except SandboxError:
            return False

        return Path(target).suffix in {".py", ".md"}


def _generated_content(task: Task, target: str) -> str:
    if target.endswith(".md") or task.task_type == "documentation":
        return (
            "# AfriProg Generated Documentation Proposal\n\n"
            f"Task: {task.task_id}\n\n"
            f"Intent: {task.description}\n\n"
            "Boundary: proposal-only, non-authoritative.\n"
        )

    if task.task_type == "test_failure" or Path(target).name.startswith("test_"):
        return (
            "from __future__ import annotations\n\n\n"
            "def test_generated_contract_is_explicit():\n"
            f"    assert {task.task_id!r}.startswith('TASK-')\n"
            "    assert True\n"
        )

    class_name = "".join(part.capitalize() for part in Path(target).stem.split("_")) or "Generated"
    return (
        "from __future__ import annotations\n\n\n"
        f"class {class_name}Proposal:\n"
        "    \"\"\"Proposal-only Afriprog generated implementation.\"\"\"\n\n"
        f"    task_id = {task.task_id!r}\n"
        f"    description = {task.description!r}\n"
        "    write_enabled = False\n\n"
        "    def canonical_dict(self) -> dict[str, object]:\n"
        "        return {\n"
        "            'task_id': self.task_id,\n"
        "            'description': self.description,\n"
        "            'write_enabled': self.write_enabled,\n"
        "        }\n"
    )


def _patch_risk(risk: str) -> str:
    allowed = {item.value for item in PatchRiskLevel}
    return risk if risk in allowed else PatchRiskLevel.MEDIUM.value
