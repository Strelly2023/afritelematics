from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from afritech.extensions.afriprog.code_executor.diff_model import Diff
from afritech.extensions.afriprog.code_executor.patch_generator import (
    PatchGenerator,
)
from afritech.extensions.afriprog.code_executor.patch_model import Patch
from afritech.extensions.afriprog.code_executor.sandbox import (
    SandboxError,
    validate_path,
)
from afritech.extensions.afriprog.repository_intelligence.repo_loader import (
    RepoLoader,
    RepositoryFile,
)
from afritech.extensions.afriprog.task_planner.planner import TaskPlanner
from afritech.extensions.afriprog.task_planner.task_model import Task


class ExecutorPreviewError(Exception):
    """Raised when patch preview execution fails."""


@dataclass(frozen=True)
class PatchPreviewResult:
    """
    Canonical Phase-4 patch preview result.

    Constitutional properties:
    - proposal-only
    - deterministic
    - no writes
    - evidence-ready
    - non-authoritative
    """

    root: str
    mode: str
    task: Task
    patch: Patch | None
    diff: Diff | None

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "mode": self.mode,
            "task": self.task.canonical_dict(),
            "patch": (
                self.patch.canonical_dict()
                if self.patch is not None
                else None
            ),
            "diff": (
                self.diff.canonical_dict()
                if self.diff is not None
                else None
            ),
            "write_enabled": False,
            "patch_applied": False,
        }


class PatchPreviewExecutor:
    """
    Phase-4 code executor preview.

    Allowed:
    - load repository files
    - plan a task
    - generate a patch proposal
    - generate a diff proposal

    Forbidden:
    - write files
    - apply patches
    - commit
    - open PR
    """

    MODE = "PHASE_3_PATCH_PROPOSAL_ONLY"

    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()

        if not self.root.exists():
            raise ExecutorPreviewError(
                f"root does not exist: {self.root}"
            )

        if not self.root.is_dir():
            raise ExecutorPreviewError(
                f"root is not a directory: {self.root}"
            )

        self.loader = RepoLoader(self.root)
        self.planner = TaskPlanner()
        self.generator = PatchGenerator(root=self.root)

    def run_patch_preview(
        self,
        failure_text: str,
        related_tests: Iterable[str] = (),
        candidate_files: Iterable[str] | None = None,
    ) -> PatchPreviewResult:
        if not isinstance(failure_text, str):
            raise ExecutorPreviewError("failure_text must be a string")

        selected_files = self._select_candidate_files(candidate_files)

        task = self.planner.plan_from_failure(
            failure_text=failure_text,
            related_tests=related_tests,
            candidate_files=selected_files,
        )

        patch = self.generator.generate_patch(task)

        diff: Diff | None = None

        if patch is not None and not patch.is_noop:
            diff = Diff(
                file_path=patch.file_path,
                diff_text=_create_diff(
                    original=patch.original_content,
                    updated=patch.updated_content,
                    fromfile=f"a/{patch.file_path}",
                    tofile=f"b/{patch.file_path}",
                ),
            )

        return PatchPreviewResult(
            root=str(self.root),
            mode=self.MODE,
            task=task,
            patch=patch,
            diff=diff,
        )

    def _select_candidate_files(
        self,
        candidate_files: Iterable[str] | None,
    ) -> tuple[str, ...]:
        if candidate_files is not None:
            return tuple(
                sorted(
                    _repo_relative_path(path, root=self.root)
                    for path in candidate_files
                )
            )

        files: tuple[RepositoryFile, ...] = self.loader.list_files()

        return tuple(
            item.path
            for item in files
            if _is_patch_candidate(item.path)
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "root": str(self.root),
            "mode": self.MODE,
            "write_enabled": False,
            "patch_apply_enabled": False,
            "git_enabled": False,
        }


def run_patch_preview(
    failure_text: str,
    root: str | Path = ".",
    related_tests: Iterable[str] = (),
    candidate_files: Iterable[str] | None = None,
) -> PatchPreviewResult:
    executor = PatchPreviewExecutor(root=root)

    return executor.run_patch_preview(
        failure_text=failure_text,
        related_tests=related_tests,
        candidate_files=candidate_files,
    )


def _create_diff(
    original: str,
    updated: str,
    *,
    fromfile: str = "a/original",
    tofile: str = "b/updated",
) -> str:
    diff = difflib.unified_diff(
        original.splitlines(),
        updated.splitlines(),
        fromfile=fromfile,
        tofile=tofile,
        lineterm="",
    )

    return "\n".join(diff)


def _repo_relative_path(path: str | Path, *, root: Path) -> str:
    path_obj = Path(path)

    if path_obj.is_absolute():
        try:
            return path_obj.resolve().relative_to(root).as_posix()
        except ValueError:
            return path_obj.as_posix()

    return path_obj.as_posix()


def _is_patch_candidate(path: str) -> bool:
    try:
        validate_path(path)
    except SandboxError:
        return False

    return Path(path).suffix == ".py"


if __name__ == "__main__":
    result = run_patch_preview(
        failure_text="ImportError: cannot import name MissingElement",
        candidate_files=(
            "afritech/extensions/afriprog/code_executor/patch_model.py",
        ),
    )

    print(result.canonical_dict())
