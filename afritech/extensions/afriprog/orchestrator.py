from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from afritech.extensions.afriprog.repository_intelligence.orchestrator_preview import (
    run_repository_intelligence,
)
from afritech.extensions.afriprog.task_planner.planner import TaskPlanner
from afritech.extensions.afriprog.task_planner.task_model import Task


class AfriProgOrchestratorError(Exception):
    """Raised when AfriProgramming orchestration fails."""


@dataclass(frozen=True)
class AfriProgPlanResult:
    root: str
    mode: str
    repository_summary: Mapping[str, object]
    tasks: tuple[Task, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "mode": self.mode,
            "repository_summary": self.repository_summary,
            "task_count": len(self.tasks),
            "tasks": [
                task.canonical_dict()
                for task in self.tasks
            ],
        }


class AfriProgOrchestrator:
    """
    Phase 2 AfriProgramming entry point.

    Constitutional behavior:
    - repository intelligence is read-only
    - task planning is read-only
    - no writes
    - no patches
    - no commits
    - no PR creation
    """

    MODE = "PHASE_2_READ_ONLY_PLANNING"

    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()

        if not self.root.exists():
            raise AfriProgOrchestratorError(
                f"repository root does not exist: {self.root}"
            )

        if not self.root.is_dir():
            raise AfriProgOrchestratorError(
                f"repository root is not a directory: {self.root}"
            )

    def plan_from_failures(
        self,
        failure_texts: Iterable[str],
        related_tests: Iterable[str] = (),
        candidate_files: Iterable[str] = (),
    ) -> AfriProgPlanResult:
        planner = TaskPlanner()

        tasks = tuple(
            planner.plan_from_failure(
                failure_text=failure_text,
                related_tests=related_tests,
                candidate_files=candidate_files,
            )
            for failure_text in failure_texts
        )

        repository_summary = run_repository_intelligence(
            root=self.root,
            output_path=None,
        ).canonical_dict()

        return AfriProgPlanResult(
            root=str(self.root),
            mode=self.MODE,
            repository_summary=repository_summary,
            tasks=tasks,
        )

    def plan_single_failure(
        self,
        failure_text: str,
        related_tests: Iterable[str] = (),
        candidate_files: Iterable[str] = (),
    ) -> AfriProgPlanResult:
        return self.plan_from_failures(
            failure_texts=(failure_text,),
            related_tests=related_tests,
            candidate_files=candidate_files,
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "root": str(self.root),
            "mode": self.MODE,
            "write_enabled": False,
            "patch_enabled": False,
            "git_enabled": False,
        }


def run_phase_2_preview(
    root: str | Path = ".",
    failure_text: str = "",
    related_tests: Iterable[str] = (),
    candidate_files: Iterable[str] = (),
) -> AfriProgPlanResult:
    orchestrator = AfriProgOrchestrator(root=root)

    return orchestrator.plan_single_failure(
        failure_text=failure_text,
        related_tests=related_tests,
        candidate_files=candidate_files,
    )


if __name__ == "__main__":
    result = run_phase_2_preview(
        failure_text=(
            "ImportError: cannot import name 'ReplayVerifier'. "
            "AssertionError: expected replay validation to pass."
        ),
        related_tests=(
            "afritech/tests/runtime/test_replay.py",
        ),
        candidate_files=(
            "afritech/runtime/replay.py",
        ),
    )

    print(result.canonical_dict())