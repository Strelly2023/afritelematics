from __future__ import annotations

from pathlib import Path

from afritech.extensions.afriprog.code_executor.ast_editor import (
    ASTEditor,
)
from afritech.extensions.afriprog.code_executor.patch_model import (
    Patch,
    PatchMode,
    PatchRiskLevel,
)
from afritech.extensions.afriprog.code_executor.sandbox import (
    SandboxError,
    validate_path,
)
from afritech.extensions.afriprog.task_planner.task_model import (
    Task,
)


class PatchGeneratorError(Exception):
    """Raised when patch proposal generation fails."""


class PatchGenerator:
    """
    Phase 4 patch proposal generator.

    Constitutional properties:
    - proposal only
    - deterministic
    - sandbox constrained
    - no writes
    - non-authoritative
    """

    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()
        self.editor = ASTEditor()

    def generate_patch(
        self,
        task: Task,
    ) -> Patch | None:
        if task.requires_write:
            return None

        if not task.target_files:
            return None

        if task.task_type == "missing_element":
            return self._handle_missing_element(task)

        if task.task_type in {
            "bug_fix",
            "test_failure",
            "validation_failure",
        }:
            return self._handle_investigation(task)

        return None

    def _handle_missing_element(
        self,
        task: Task,
    ) -> Patch | None:
        file_path = task.target_files[0]

        try:
            validate_path(file_path)
        except SandboxError:
            return None

        path_obj = self.root / file_path

        if not path_obj.exists():
            return None

        original = path_obj.read_text(
            encoding="utf-8"
        )

        proposal = (
            "# AfriProgramming Proposal\n"
            "# Missing implementation element detected.\n"
            "# Manual review required.\n"
        )

        updated = self.editor.insert_text(
            original,
            proposal,
        )

        return Patch(
            file_path=file_path,
            original_content=original,
            updated_content=updated,
            patch_type="missing_element",
            risk_level=PatchRiskLevel.LOW.value,
            mode=PatchMode.PROPOSAL_ONLY.value,
            write_permitted=False,
        )

    def _handle_investigation(
        self,
        task: Task,
    ) -> Patch | None:
        file_path = task.target_files[0]

        try:
            validate_path(file_path)
        except SandboxError:
            return None

        path_obj = self.root / file_path

        if not path_obj.exists():
            return None

        original = path_obj.read_text(
            encoding="utf-8"
        )

        proposal = (
            "# AfriProgramming Proposal\n"
            f"# Investigate task: {task.task_id}\n"
            f"# Description: {task.description}\n"
        )

        updated = self.editor.insert_text(
            original,
            proposal,
        )

        return Patch(
            file_path=file_path,
            original_content=original,
            updated_content=updated,
            patch_type="investigation",
            risk_level=PatchRiskLevel.MEDIUM.value,
            mode=PatchMode.PROPOSAL_ONLY.value,
            write_permitted=False,
        )

    def generate_many(
        self,
        tasks: tuple[Task, ...],
    ) -> tuple[Patch, ...]:
        patches: list[Patch] = []

        for task in tasks:
            patch = self.generate_patch(task)

            if patch is not None:
                patches.append(patch)

        return tuple(
            sorted(
                patches,
                key=lambda item: item.file_path,
            )
        )
