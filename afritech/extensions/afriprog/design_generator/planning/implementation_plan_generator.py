from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.design_generator.architecture.architecture_generator import (
    ArchitectureProposal,
)
from afritech.extensions.afriprog.design_generator.planning.milestone_generator import (
    MilestoneGenerator,
    MilestonePlan,
)
from afritech.extensions.afriprog.task_planner.task_model import Task
from afritech.extensions.afriprog.task_planner.task_types import RiskLevel, TaskType


@dataclass(frozen=True)
class ImplementationPlan:
    milestones: MilestonePlan
    tasks: tuple[Task, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "milestones": self.milestones.canonical_dict(),
            "tasks": [task.canonical_dict() for task in self.tasks],
        }


class ImplementationPlanGenerator:
    """Generate proposal implementation tasks from architecture."""

    def __init__(self, milestone_generator: MilestoneGenerator | None = None) -> None:
        self.milestone_generator = milestone_generator or MilestoneGenerator()

    def generate(self, architecture: ArchitectureProposal) -> ImplementationPlan:
        tasks: list[Task] = []

        for index, model in enumerate(architecture.modules.domain_models, start=1):
            tasks.append(
                Task(
                    task_id=f"TASK-{index:04d}",
                    task_type=TaskType.MISSING_ELEMENT.value,
                    description=f"Create {model} domain model proposal",
                    target_files=(f"afritech/extensions/afriprog/generated/domain/{_snake(model)}.py",),
                    risk_level=RiskLevel.LOW.value,
                    requires_write=False,
                    source_tests=(),
                )
            )

        offset = len(tasks)
        for module_index, module in enumerate(architecture.modules.modules, start=1):
            tasks.append(
                Task(
                    task_id=f"TASK-{offset + module_index:04d}",
                    task_type=TaskType.STRUCTURE_REPAIR.value,
                    description=f"Define {module} layer implementation proposal",
                    target_files=(f"afritech/extensions/afriprog/generated/{module}/README.md",),
                    risk_level=RiskLevel.MEDIUM.value,
                    requires_write=False,
                    source_tests=(),
                )
            )

        return ImplementationPlan(
            milestones=self.milestone_generator.generate(),
            tasks=tuple(tasks),
        )


def _snake(value: str) -> str:
    pieces = []
    for index, character in enumerate(value):
        if character.isupper() and index:
            pieces.append("_")
        pieces.append(character.lower())
    return "".join(pieces)
