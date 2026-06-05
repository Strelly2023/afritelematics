"""Cross-domain orchestration for AfriTPPS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from afritech.afritpps.domain_contracts import execute_domain_operation
from afritech.afritpps.execution_engine import AfriTPPSExecutionOutcome
from afritech.trust_kernel.projections import projection_hash


class AfriTPPSOrchestrationError(RuntimeError):
    """Raised when cross-domain orchestration cannot produce a verified result."""


@dataclass(frozen=True)
class OrchestrationStep:
    step_id: str
    domain: str
    operation: str
    actor_id: str
    subject_id: str
    payload: dict[str, Any]
    signature: dict[str, Any]
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    witnesses: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    require_client_signature: bool = False


@dataclass(frozen=True)
class AfriTPPSOrchestrationIntent:
    orchestration_id: str
    name: str
    operations: tuple[OrchestrationStep, ...]
    policy_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AfriTPPSOrchestrationOutcome:
    orchestration_id: str
    name: str
    status: str
    step_results: dict[str, AfriTPPSExecutionOutcome]
    final_state_hash: str
    fully_verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "orchestration_id": self.orchestration_id,
            "name": self.name,
            "status": self.status,
            "step_results": {
                step_id: outcome.canonical_dict()
                for step_id, outcome in self.step_results.items()
            },
            "final_state_hash": self.final_state_hash,
            "fully_verified": self.fully_verified,
        }


def execute_orchestration(
    intent: AfriTPPSOrchestrationIntent,
) -> AfriTPPSOrchestrationOutcome:
    _validate_orchestration_intent(intent)
    step_by_id = {step.step_id: step for step in intent.operations}
    executed: dict[str, AfriTPPSExecutionOutcome] = {}
    pending = list(intent.operations)

    while pending:
        progress = False
        next_pending: list[OrchestrationStep] = []
        for step in pending:
            if not all(dep in executed for dep in step.dependencies):
                next_pending.append(step)
                continue
            _guard_dependencies_verified(step, executed)
            outcome = execute_domain_operation(
                operation_id=f"{intent.orchestration_id}:{step.step_id}",
                domain=step.domain,
                operation=step.operation,
                actor_id=step.actor_id,
                subject_id=step.subject_id,
                payload=step.payload,
                signature=step.signature,
                witnesses=step.witnesses,
                require_client_signature=step.require_client_signature,
            )
            if not outcome.verified:
                raise AfriTPPSOrchestrationError(
                    f"step did not return verified outcome: {step.step_id}"
                )
            executed[step.step_id] = outcome
            progress = True

        if not progress:
            unresolved = ", ".join(step.step_id for step in next_pending)
            raise AfriTPPSOrchestrationError(
                f"orchestration dependencies unresolved or cyclic: {unresolved}"
            )
        pending = next_pending

    fully_verified = all(outcome.verified for outcome in executed.values())
    if not fully_verified:
        raise AfriTPPSOrchestrationError("orchestration produced unverified outcomes")
    return AfriTPPSOrchestrationOutcome(
        orchestration_id=intent.orchestration_id,
        name=intent.name,
        status="verified",
        step_results=executed,
        final_state_hash=projection_hash(),
        fully_verified=True,
    )


def _validate_orchestration_intent(intent: AfriTPPSOrchestrationIntent) -> None:
    if not intent.orchestration_id:
        raise AfriTPPSOrchestrationError("orchestration_id is required")
    if not intent.name:
        raise AfriTPPSOrchestrationError("orchestration name is required")
    if not intent.operations:
        raise AfriTPPSOrchestrationError("orchestration requires at least one step")

    step_ids = [step.step_id for step in intent.operations]
    if len(step_ids) != len(set(step_ids)):
        raise AfriTPPSOrchestrationError("orchestration step IDs must be unique")

    known = set(step_ids)
    for step in intent.operations:
        if not step.step_id:
            raise AfriTPPSOrchestrationError("step_id is required")
        for dependency in step.dependencies:
            if dependency not in known:
                raise AfriTPPSOrchestrationError(
                    f"{step.step_id} has unknown dependency: {dependency}"
                )


def _guard_dependencies_verified(
    step: OrchestrationStep,
    executed: dict[str, AfriTPPSExecutionOutcome],
) -> None:
    for dependency in step.dependencies:
        outcome = executed[dependency]
        if not outcome.verified:
            raise AfriTPPSOrchestrationError(
                f"{step.step_id} dependency is not verified: {dependency}"
            )
