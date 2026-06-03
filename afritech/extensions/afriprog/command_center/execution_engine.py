from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.ai_engine.coder import (
    CodeGenerationResult,
    Coder,
)
from afritech.extensions.afriprog.ai_engine.reviewer import (
    ReviewResult,
    Reviewer,
)
from afritech.extensions.afriprog.ai_engine.test_writer import TestWriter
from afritech.extensions.afriprog.command_center.worktree_manager import (
    WorktreeManager,
    WorktreePlan,
)
from afritech.extensions.afriprog.evidence.evidence_generator import EvidenceGenerator
from afritech.extensions.afriprog.evidence.evidence_model import EvidenceRecord
from afritech.extensions.afriprog.task_planner.task_model import Task


@dataclass(frozen=True)
class ExecutionResult:
    task: Task
    worktree: WorktreePlan
    code: CodeGenerationResult
    test_patches: tuple
    evidence: tuple[EvidenceRecord, ...]
    review: ReviewResult

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "task": self.task.canonical_dict(),
            "worktree": self.worktree.canonical_dict(),
            "code": self.code.canonical_dict(),
            "test_patches": [patch.canonical_dict() for patch in self.test_patches],
            "evidence": [record.canonical_dict() for record in self.evidence],
            "review": self.review.canonical_dict(),
            "status": "admitted" if self.review.admitted else "rejected",
            "write_enabled": False,
        }


class ExecutionEngine:
    """Closed-loop proposal execution for one generated task."""

    def __init__(
        self,
        *,
        coder: Coder | None = None,
        test_writer: TestWriter | None = None,
        reviewer: Reviewer | None = None,
        evidence_generator: EvidenceGenerator | None = None,
        worktree_manager: WorktreeManager | None = None,
    ) -> None:
        self.coder = coder or Coder()
        self.test_writer = test_writer or TestWriter()
        self.reviewer = reviewer or Reviewer()
        self.evidence_generator = evidence_generator or EvidenceGenerator()
        self.worktree_manager = worktree_manager or WorktreeManager()

    def execute(self, task: Task) -> ExecutionResult:
        worktree = self.worktree_manager.plan(task)
        code = self.coder.generate(task)
        test_patches = self.test_writer.generate_tests(task)
        all_patches = code.patches + test_patches

        evidence = (
            self.evidence_generator.from_task(task),
            *(
                self.evidence_generator.from_patch(patch)
                for patch in all_patches
            ),
        )
        evidence_ids = tuple(record.evidence_id for record in evidence)
        review = self.reviewer.review(
            all_patches,
            evidence_ids=evidence_ids,
            claims=(task.description,),
        )

        return ExecutionResult(
            task=task,
            worktree=worktree,
            code=code,
            test_patches=test_patches,
            evidence=evidence,
            review=review,
        )
