"""Observable graph views for persistent AfriTPPS orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.models import OrchestrationStepState, PersistentOrchestration


@dataclass(frozen=True)
class StepView:
    step_id: str
    domain: str
    operation: str
    status: str
    event_id: str | None
    evidence_bundle_hash: str
    verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "domain": self.domain,
            "operation": self.operation,
            "status": self.status,
            "event_id": self.event_id,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class DependencyEdge:
    from_step: str
    to_step: str

    def canonical_dict(self) -> dict[str, str]:
        return {
            "from_step": self.from_step,
            "to_step": self.to_step,
        }


@dataclass(frozen=True)
class OrchestrationView:
    orchestration_id: str
    name: str
    status: str
    steps: tuple[StepView, ...]
    edges: tuple[DependencyEdge, ...]
    final_state_hash: str
    fully_verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "orchestration_id": self.orchestration_id,
            "name": self.name,
            "status": self.status,
            "steps": [step.canonical_dict() for step in self.steps],
            "edges": [edge.canonical_dict() for edge in self.edges],
            "final_state_hash": self.final_state_hash,
            "fully_verified": self.fully_verified,
            "percent_complete": percent_complete(self.steps),
        }


def build_orchestration_view(orchestration_id: str) -> OrchestrationView:
    orchestration = PersistentOrchestration.objects.get(
        orchestration_id=orchestration_id
    )
    states = tuple(
        OrchestrationStepState.objects.filter(orchestration=orchestration).order_by(
            "created_at",
            "step_id",
        )
    )
    return OrchestrationView(
        orchestration_id=orchestration.orchestration_id,
        name=orchestration.name,
        status=orchestration.status,
        steps=tuple(_step_view(state) for state in states),
        edges=tuple(
            DependencyEdge(from_step=dependency, to_step=state.step_id)
            for state in states
            for dependency in state.dependencies
        ),
        final_state_hash=orchestration.final_state_hash,
        fully_verified=orchestration.fully_verified,
    )


def list_orchestration_views() -> list[dict[str, Any]]:
    return [
        build_orchestration_view(row.orchestration_id).canonical_dict()
        for row in PersistentOrchestration.objects.order_by("-created_at")
    ]


def percent_complete(steps: tuple[StepView, ...]) -> int:
    if not steps:
        return 0
    verified = sum(1 for step in steps if step.verified)
    return round((verified / len(steps)) * 100)


def _step_view(state: OrchestrationStepState) -> StepView:
    return StepView(
        step_id=state.step_id,
        domain=state.domain,
        operation=state.operation,
        status=state.status,
        event_id=str(state.event_id) if state.event_id else None,
        evidence_bundle_hash=state.evidence_bundle_hash,
        verified=state.verified,
    )
