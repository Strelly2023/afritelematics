from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TaskModelError(Exception):
    """Raised when task construction fails."""


class TaskType(str, Enum):
    FIX_TEST = "fix_test"
    ADD_TEST = "add_test"
    REFINE_STRUCTURE = "refine_structure"
    ADD_DOCUMENTATION = "add_documentation"
    VALIDATE_SURFACE = "validate_surface"
    INVESTIGATE_FAILURE = "investigate_failure"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Task:
    """
    Canonical engineering task contract.

    Constitutional properties:
    - deterministic
    - immutable
    - replay-safe
    - non-authoritative
    """

    task_id: str
    task_type: str
    description: str
    target_files: tuple[str, ...]
    risk_level: str
    requires_write: bool
    source_tests: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise TaskModelError("task_id must not be empty")

        if not self.description.strip():
            raise TaskModelError("description must not be empty")

        if self.risk_level not in {
            RiskLevel.LOW.value,
            RiskLevel.MEDIUM.value,
            RiskLevel.HIGH.value,
            RiskLevel.CRITICAL.value,
        }:
            raise TaskModelError(
                f"invalid risk level: {self.risk_level}"
            )

    @property
    def target_count(self) -> int:
        return len(self.target_files)

    @property
    def source_test_count(self) -> int:
        return len(self.source_tests)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "target_files": list(sorted(self.target_files)),
            "risk_level": self.risk_level,
            "requires_write": self.requires_write,
            "source_tests": list(sorted(self.source_tests)),
            "target_count": self.target_count,
            "source_test_count": self.source_test_count,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_dict()