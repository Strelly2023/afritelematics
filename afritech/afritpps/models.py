"""Immutable AfriTPPS execution pillar models."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from afritech.afritpps.constants import (
    AFRITPPS_COMPONENT,
    AFRITPPS_PILLAR,
    AFRITPPS_STATUS,
    CAPABILITY_TYPES,
    MATURITY_LEVELS,
    MODEL_CLASSIFICATION,
    OUTPUT_CLASSIFICATION,
    WORKFLOW_STEP_STATUSES,
    assert_afritpps_constitution,
)


class AfriTPPSModelError(ValueError):
    """Raised when AfriTPPS execution model data is invalid."""


def _safe_str(value: object, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _freeze_mapping(
    value: Mapping[str, object] | None,
) -> tuple[tuple[str, object], ...]:
    if value is None:
        return tuple()
    if not isinstance(value, Mapping):
        raise AfriTPPSModelError("metadata must be a mapping")
    return tuple(sorted(value.items(), key=lambda item: str(item[0])))


@dataclass(frozen=True)
class AfriTPPSCapability:
    """Operational capability managed by AfriTPPS."""

    capability_id: str
    name: str
    capability_type: str
    maturity_level: str
    owner: str
    service_objective: str
    metadata: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.capability_id:
            raise AfriTPPSModelError("capability_id is required")
        if not self.name:
            raise AfriTPPSModelError("capability name is required")
        if self.capability_type not in CAPABILITY_TYPES:
            raise AfriTPPSModelError(
                f"unsupported capability_type: {self.capability_type}"
            )
        if self.maturity_level not in MATURITY_LEVELS:
            raise AfriTPPSModelError(
                f"unsupported maturity_level: {self.maturity_level}"
            )
        if not self.owner:
            raise AfriTPPSModelError("capability owner is required")
        if not self.service_objective:
            raise AfriTPPSModelError("service_objective is required")
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AfriTPPSCapability":
        if not isinstance(payload, Mapping):
            raise AfriTPPSModelError("capability payload must be a mapping")

        return cls(
            capability_id=_safe_str(payload.get("capability_id") or payload.get("id")),
            name=_safe_str(payload.get("name")),
            capability_type=_safe_str(payload.get("capability_type")),
            maturity_level=_safe_str(payload.get("maturity_level")),
            owner=_safe_str(payload.get("owner")),
            service_objective=_safe_str(payload.get("service_objective")),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def metadata_dict(self) -> dict[str, object]:
        return dict(self.metadata)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRITPPS_COMPONENT,
            "pillar": AFRITPPS_PILLAR,
            "status": AFRITPPS_STATUS,
            "classification": MODEL_CLASSIFICATION,
            "capability_id": self.capability_id,
            "name": self.name,
            "capability_type": self.capability_type,
            "maturity_level": self.maturity_level,
            "owner": self.owner,
            "service_objective": self.service_objective,
            "metadata": self.metadata_dict(),
            "output_classification": OUTPUT_CLASSIFICATION,
            "defines_execution": True,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


@dataclass(frozen=True)
class AfriTPPSWorkflowStep:
    """Single ordered step in an operational workflow."""

    step_id: str
    capability_id: str
    name: str
    process: str
    role: str
    expected_output: str
    sequence: int
    status: str = "planned"

    def __post_init__(self) -> None:
        if not self.step_id:
            raise AfriTPPSModelError("workflow step_id is required")
        if not self.capability_id:
            raise AfriTPPSModelError("workflow capability_id is required")
        if not self.name:
            raise AfriTPPSModelError("workflow step name is required")
        if not self.process:
            raise AfriTPPSModelError("workflow process is required")
        if not self.role:
            raise AfriTPPSModelError("workflow role is required")
        if not self.expected_output:
            raise AfriTPPSModelError("workflow expected_output is required")
        if not isinstance(self.sequence, int) or self.sequence < 1:
            raise AfriTPPSModelError("workflow sequence must be a positive integer")
        if self.status not in WORKFLOW_STEP_STATUSES:
            raise AfriTPPSModelError(f"unsupported workflow status: {self.status}")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AfriTPPSWorkflowStep":
        if not isinstance(payload, Mapping):
            raise AfriTPPSModelError("workflow step payload must be a mapping")

        return cls(
            step_id=_safe_str(payload.get("step_id") or payload.get("id")),
            capability_id=_safe_str(payload.get("capability_id")),
            name=_safe_str(payload.get("name")),
            process=_safe_str(payload.get("process")),
            role=_safe_str(payload.get("role")),
            expected_output=_safe_str(payload.get("expected_output")),
            sequence=int(payload.get("sequence", 0)),
            status=_safe_str(payload.get("status"), "planned"),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRITPPS_COMPONENT,
            "pillar": AFRITPPS_PILLAR,
            "step_id": self.step_id,
            "capability_id": self.capability_id,
            "name": self.name,
            "process": self.process,
            "role": self.role,
            "expected_output": self.expected_output,
            "sequence": self.sequence,
            "status": self.status,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


@dataclass(frozen=True)
class AfriTPPSWorkflow:
    """Deterministic operational workflow."""

    workflow_id: str
    name: str
    steps: tuple[AfriTPPSWorkflowStep, ...]

    def __post_init__(self) -> None:
        if not self.workflow_id:
            raise AfriTPPSModelError("workflow_id is required")
        if not self.name:
            raise AfriTPPSModelError("workflow name is required")
        if not self.steps:
            raise AfriTPPSModelError("workflow requires at least one step")

        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise AfriTPPSModelError("workflow step IDs must be unique")

        ordered = tuple(sorted(self.steps, key=lambda step: (step.sequence, step.step_id)))
        sequences = [step.sequence for step in ordered]
        expected = list(range(1, len(ordered) + 1))
        if sequences != expected:
            raise AfriTPPSModelError("workflow step sequence must be contiguous")

        object.__setattr__(self, "steps", ordered)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AfriTPPSWorkflow":
        if not isinstance(payload, Mapping):
            raise AfriTPPSModelError("workflow payload must be a mapping")

        raw_steps = payload.get("steps", ())
        if isinstance(raw_steps, (str, bytes)) or not isinstance(raw_steps, Iterable):
            raise AfriTPPSModelError("workflow steps must be iterable")

        return cls(
            workflow_id=_safe_str(payload.get("workflow_id") or payload.get("id")),
            name=_safe_str(payload.get("name")),
            steps=tuple(AfriTPPSWorkflowStep.from_mapping(step) for step in raw_steps),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRITPPS_COMPONENT,
            "pillar": AFRITPPS_PILLAR,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "step_count": len(self.steps),
            "steps": tuple(step.canonical_dict() for step in self.steps),
            "output_classification": OUTPUT_CLASSIFICATION,
            "defines_execution": True,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


@dataclass(frozen=True)
class AfriTPPSProgram:
    """Program execution model composed of capabilities and workflows."""

    program_id: str
    name: str
    capabilities: tuple[AfriTPPSCapability, ...]
    workflows: tuple[AfriTPPSWorkflow, ...]

    def __post_init__(self) -> None:
        assert_afritpps_constitution()

        if not self.program_id:
            raise AfriTPPSModelError("program_id is required")
        if not self.name:
            raise AfriTPPSModelError("program name is required")
        if not self.capabilities:
            raise AfriTPPSModelError("program requires at least one capability")
        if not self.workflows:
            raise AfriTPPSModelError("program requires at least one workflow")

        capability_ids = {capability.capability_id for capability in self.capabilities}
        for workflow in self.workflows:
            for step in workflow.steps:
                if step.capability_id not in capability_ids:
                    raise AfriTPPSModelError(
                        f"workflow step references unknown capability: {step.capability_id}"
                    )

        object.__setattr__(
            self,
            "capabilities",
            tuple(sorted(self.capabilities, key=lambda item: item.capability_id)),
        )
        object.__setattr__(
            self,
            "workflows",
            tuple(sorted(self.workflows, key=lambda item: item.workflow_id)),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRITPPS_COMPONENT,
            "pillar": AFRITPPS_PILLAR,
            "status": AFRITPPS_STATUS,
            "program_id": self.program_id,
            "name": self.name,
            "capability_count": len(self.capabilities),
            "workflow_count": len(self.workflows),
            "capabilities": tuple(
                capability.canonical_dict() for capability in self.capabilities
            ),
            "workflows": tuple(workflow.canonical_dict() for workflow in self.workflows),
            "output_classification": OUTPUT_CLASSIFICATION,
            "defines_execution": True,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


__all__ = [
    "AfriTPPSCapability",
    "AfriTPPSWorkflowStep",
    "AfriTPPSWorkflow",
    "AfriTPPSProgram",
    "AfriTPPSModelError",
]
