from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskTypeError(Exception):
    """Raised when task type operations fail."""


class TaskType(str, Enum):
    """
    Canonical AfriProgramming task taxonomy.
    """

    FIX = "bug_fix"
    REFACTOR = "refactor"
    MISSING_ELEMENT = "missing_element"
    VALIDATION_FAILURE = "validation_failure"
    TEST_FAILURE = "test_failure"
    CONTRACT_VIOLATION = "contract_violation"
    STRUCTURE_REPAIR = "structure_repair"
    DOCUMENTATION = "documentation"
    INVESTIGATION = "investigation"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """
    Engineering risk classification.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class TaskTypeMetadata:
    task_type: TaskType
    default_risk: RiskLevel
    requires_write: bool
    description: str

    def canonical_dict(self) -> dict[str, str | bool]:
        return {
            "task_type": self.task_type.value,
            "default_risk": self.default_risk.value,
            "requires_write": self.requires_write,
            "description": self.description,
        }


TASK_TYPE_REGISTRY: dict[TaskType, TaskTypeMetadata] = {
    TaskType.FIX: TaskTypeMetadata(
        task_type=TaskType.FIX,
        default_risk=RiskLevel.MEDIUM,
        requires_write=True,
        description="Repair defective behavior.",
    ),
    TaskType.REFACTOR: TaskTypeMetadata(
        task_type=TaskType.REFACTOR,
        default_risk=RiskLevel.HIGH,
        requires_write=True,
        description="Improve structure without changing behavior.",
    ),
    TaskType.MISSING_ELEMENT: TaskTypeMetadata(
        task_type=TaskType.MISSING_ELEMENT,
        default_risk=RiskLevel.LOW,
        requires_write=True,
        description="Add missing implementation element.",
    ),
    TaskType.VALIDATION_FAILURE: TaskTypeMetadata(
        task_type=TaskType.VALIDATION_FAILURE,
        default_risk=RiskLevel.MEDIUM,
        requires_write=True,
        description="Resolve validator failure.",
    ),
    TaskType.TEST_FAILURE: TaskTypeMetadata(
        task_type=TaskType.TEST_FAILURE,
        default_risk=RiskLevel.MEDIUM,
        requires_write=True,
        description="Resolve failing test.",
    ),
    TaskType.CONTRACT_VIOLATION: TaskTypeMetadata(
        task_type=TaskType.CONTRACT_VIOLATION,
        default_risk=RiskLevel.HIGH,
        requires_write=True,
        description="Repair contract mismatch.",
    ),
    TaskType.STRUCTURE_REPAIR: TaskTypeMetadata(
        task_type=TaskType.STRUCTURE_REPAIR,
        default_risk=RiskLevel.MEDIUM,
        requires_write=True,
        description="Repair repository structure.",
    ),
    TaskType.DOCUMENTATION: TaskTypeMetadata(
        task_type=TaskType.DOCUMENTATION,
        default_risk=RiskLevel.LOW,
        requires_write=True,
        description="Documentation improvement.",
    ),
    TaskType.INVESTIGATION: TaskTypeMetadata(
        task_type=TaskType.INVESTIGATION,
        default_risk=RiskLevel.LOW,
        requires_write=False,
        description="Read-only investigation.",
    ),
    TaskType.UNKNOWN: TaskTypeMetadata(
        task_type=TaskType.UNKNOWN,
        default_risk=RiskLevel.LOW,
        requires_write=False,
        description="Unclassified task.",
    ),
}


def get_task_metadata(task_type: TaskType) -> TaskTypeMetadata:
    try:
        return TASK_TYPE_REGISTRY[task_type]
    except KeyError as exc:
        raise TaskTypeError(
            f"unknown task type: {task_type}"
        ) from exc