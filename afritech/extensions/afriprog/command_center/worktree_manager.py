from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afritech.extensions.afriprog.task_planner.task_model import Task


@dataclass(frozen=True)
class WorktreePlan:
    task_id: str
    branch_name: str
    worktree_path: str
    commands: tuple[tuple[str, ...], ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "branch_name": self.branch_name,
            "worktree_path": self.worktree_path,
            "commands": [list(command) for command in self.commands],
            "mutation_enabled": False,
        }


class WorktreeManager:
    """
    Worktree isolation planner.

    Produces the exact git commands a human or approved automation may run, but
    does not execute them.
    """

    DEFAULT_BASE = ".afriprog/worktrees"

    def plan(self, task: Task, *, base_path: str = DEFAULT_BASE) -> WorktreePlan:
        branch_name = _branch_name(task.task_id)
        worktree_path = f"{base_path.rstrip('/')}/{branch_name.replace('/', '-')}"
        commands = (
            ("git", "worktree", "add", worktree_path, "-b", branch_name),
            ("git", "status", "--short"),
        )

        return WorktreePlan(
            task_id=task.task_id,
            branch_name=branch_name,
            worktree_path=Path(worktree_path).as_posix(),
            commands=commands,
        )


def _branch_name(task_id: str) -> str:
    normalized = "".join(
        character.lower() if character.isalnum() else "-"
        for character in task_id
    ).strip("-")

    if not normalized:
        normalized = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:12]

    return f"codex/afriprog-{normalized}"
