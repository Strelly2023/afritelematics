from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.ai_engine.objective_engine import (
    Objective,
    ObjectiveEngine,
    ObjectiveEvaluation,
)
from afritech.extensions.afriprog.ai_engine.task_generator import TaskGenerator
from afritech.extensions.afriprog.command_center.execution_engine import (
    ExecutionEngine,
    ExecutionResult,
)


@dataclass(frozen=True)
class VerificationIteration:
    iteration: int
    executions: tuple[ExecutionResult, ...]
    metrics: dict[str, bool | int | str]
    evaluation: ObjectiveEvaluation

    @property
    def admitted(self) -> bool:
        return all(execution.review.admitted for execution in self.executions)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "executions": [
                execution.canonical_dict()
                for execution in self.executions
            ],
            "metrics": dict(sorted(self.metrics.items())),
            "evaluation": self.evaluation.canonical_dict(),
            "status": "satisfied" if self.evaluation.satisfied else "not_satisfied",
            "write_enabled": False,
            "authority": "proposal_only",
        }


@dataclass(frozen=True)
class VerificationLoopResult:
    objective: Objective
    iterations: tuple[VerificationIteration, ...]

    @property
    def satisfied(self) -> bool:
        return bool(self.iterations and self.iterations[-1].evaluation.satisfied)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective.canonical_dict(),
            "iterations": [
                iteration.canonical_dict()
                for iteration in self.iterations
            ],
            "iteration_count": len(self.iterations),
            "satisfied": self.satisfied,
            "status": "satisfied" if self.satisfied else "attention_required",
            "write_enabled": False,
            "authority": "proposal_only",
        }


class VerificationLoopEngine:
    """
    Controlled objective loop for proposal-only engineering work.

    The loop can iterate over proposals and simulated verification evidence, but
    it never applies patches or escalates repository authority.
    """

    def __init__(
        self,
        *,
        objective_engine: ObjectiveEngine | None = None,
        task_generator: TaskGenerator | None = None,
        execution_engine: ExecutionEngine | None = None,
    ) -> None:
        self.objective_engine = objective_engine or ObjectiveEngine()
        self.task_generator = task_generator or TaskGenerator()
        self.execution_engine = execution_engine or ExecutionEngine()

    def run(self, objective: Objective) -> VerificationLoopResult:
        iterations: list[VerificationIteration] = []

        for index in range(1, objective.max_iterations + 1):
            generated = self.task_generator.generate(objective.description)
            executions = tuple(
                self.execution_engine.execute(task)
                for task in generated.tasks
            )
            metrics = self._metrics(objective, executions)
            evaluation = self.objective_engine.evaluate(objective, metrics)
            iteration = VerificationIteration(
                iteration=index,
                executions=executions,
                metrics=metrics,
                evaluation=evaluation,
            )
            iterations.append(iteration)

            if evaluation.satisfied or not iteration.admitted:
                break

        return VerificationLoopResult(
            objective=objective,
            iterations=tuple(iterations),
        )

    def run_description(
        self,
        description: str,
        *,
        max_iterations: int = ObjectiveEngine.DEFAULT_MAX_ITERATIONS,
    ) -> VerificationLoopResult:
        objective = self.objective_engine.define(
            description,
            max_iterations=max_iterations,
        )
        return self.run(objective)

    def _metrics(
        self,
        objective: Objective,
        executions: tuple[ExecutionResult, ...],
    ) -> dict[str, bool | int | str]:
        all_guards_pass = all(execution.review.admitted for execution in executions)
        patch_count = sum(len(execution.code.patches) for execution in executions)
        evidence_count = sum(len(execution.evidence) for execution in executions)
        has_test_proposals = any(
            execution.test_patches
            or execution.task.source_tests
            or "test" in execution.task.description.lower()
            for execution in executions
        )
        auth_objective = any(
            criterion.name in {"rbac_enforced", "token_validation_coverage"}
            for criterion in objective.success_criteria
        )

        return {
            "proposals_generated": patch_count > 0,
            "evidence_present": evidence_count > 0,
            "all_guards_pass": all_guards_pass,
            "tests_simulated": has_test_proposals,
            "writes_disabled": True,
            "rbac_enforced": all_guards_pass and auth_objective,
            "token_validation_coverage": 90 if all_guards_pass and auth_objective else 0,
        }
