from __future__ import annotations

from pathlib import Path

from afritech.extensions.afriprog.ai_engine.coder import Coder
from afritech.extensions.afriprog.code_executor.patch_model import Patch
from afritech.extensions.afriprog.task_planner.task_model import Task


class TestWriter:
    """Generate proposal-only tests for a task."""

    def __init__(self, coder: Coder | None = None) -> None:
        self.coder = coder or Coder()

    def generate_tests(self, task: Task) -> tuple[Patch, ...]:
        test_targets = tuple(
            target
            for target in task.target_files
            if Path(target).name.startswith("test_")
        )

        if test_targets:
            test_task = Task(
                task_id=task.task_id,
                task_type="test_failure",
                description=f"Generate tests for {task.description}",
                target_files=test_targets,
                risk_level=task.risk_level,
                requires_write=False,
                source_tests=test_targets,
            )
            return self.coder.generate(test_task).patches

        return ()
