from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


class ObjectiveEngineError(Exception):
    """Raised when an objective cannot be defined or evaluated."""


@dataclass(frozen=True)
class SuccessCriterion:
    name: str
    operator: str
    expected: bool | int | str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "operator": self.operator,
            "expected": self.expected,
        }


@dataclass(frozen=True)
class Objective:
    objective_id: str
    description: str
    success_criteria: tuple[SuccessCriterion, ...]
    constraints: tuple[str, ...]
    max_iterations: int

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "description": self.description,
            "success_criteria": [
                criterion.canonical_dict()
                for criterion in self.success_criteria
            ],
            "constraints": list(self.constraints),
            "max_iterations": self.max_iterations,
            "write_enabled": False,
            "authority": "proposal_only",
        }


@dataclass(frozen=True)
class CriterionEvaluation:
    criterion: SuccessCriterion
    actual: bool | int | str | None
    satisfied: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "criterion": self.criterion.canonical_dict(),
            "actual": self.actual,
            "satisfied": self.satisfied,
        }


@dataclass(frozen=True)
class ObjectiveEvaluation:
    satisfied: bool
    criteria: tuple[CriterionEvaluation, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "satisfied": self.satisfied,
            "criteria": [
                criterion.canonical_dict()
                for criterion in self.criteria
            ],
            "write_enabled": False,
            "authority": "proposal_only",
        }


class ObjectiveEngine:
    """Define and evaluate bounded, proposal-only engineering objectives."""

    DEFAULT_MAX_ITERATIONS = 3

    def define(
        self,
        description: str,
        *,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> Objective:
        if not isinstance(description, str) or not description.strip():
            raise ObjectiveEngineError("description must be a non-empty string")
        if max_iterations < 1 or max_iterations > 10:
            raise ObjectiveEngineError("max_iterations must be between 1 and 10")

        normalized = " ".join(description.strip().split())
        criteria = [
            SuccessCriterion("proposals_generated", "==", True),
            SuccessCriterion("evidence_present", "==", True),
            SuccessCriterion("all_guards_pass", "==", True),
            SuccessCriterion("tests_simulated", "==", True),
            SuccessCriterion("writes_disabled", "==", True),
        ]
        lower = normalized.lower()
        if any(token in lower for token in ("auth", "rbac", "token", "login")):
            criteria.extend(
                (
                    SuccessCriterion("rbac_enforced", "==", True),
                    SuccessCriterion("token_validation_coverage", ">=", 90),
                )
            )

        return Objective(
            objective_id=f"OBJ-{_stable_id(normalized)}",
            description=normalized,
            success_criteria=tuple(criteria),
            constraints=(
                "No repository mutation",
                "No privilege escalation",
                "All generated proposals must pass constitutional guards",
                "Objective success cannot override invariants",
            ),
            max_iterations=max_iterations,
        )

    def evaluate(
        self,
        objective: Objective,
        metrics: dict[str, bool | int | str],
    ) -> ObjectiveEvaluation:
        criteria = tuple(
            CriterionEvaluation(
                criterion=criterion,
                actual=metrics.get(criterion.name),
                satisfied=_compare(
                    metrics.get(criterion.name),
                    criterion.operator,
                    criterion.expected,
                ),
            )
            for criterion in objective.success_criteria
        )

        return ObjectiveEvaluation(
            satisfied=all(criterion.satisfied for criterion in criteria),
            criteria=criteria,
        )


def _compare(
    actual: bool | int | str | None,
    operator: str,
    expected: bool | int | str,
) -> bool:
    if operator == "==":
        return actual == expected
    if operator == ">=" and isinstance(actual, int) and isinstance(expected, int):
        return actual >= expected
    raise ObjectiveEngineError(f"unsupported success criterion operator: {operator}")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:10].upper()
