"""Immutable AfriProgramming autonomous engineering models."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from afritech.afriprogramming.constants import (
    AFRIPROGRAMMING_COMPONENT,
    AFRIPROGRAMMING_PILLAR,
    AFRIPROGRAMMING_STATUS,
    AGENT_ROLES,
    ARTIFACT_CLASSIFICATION,
    ARTIFACT_TYPES,
    CAPABILITIES,
    LIFECYCLE_STAGES,
    MODEL_CLASSIFICATION,
    OUTPUT_CLASSIFICATION,
    assert_afriprogramming_constitution,
)


class AfriProgrammingModelError(ValueError):
    """Raised when AfriProgramming engineering model data is invalid."""


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
        raise AfriProgrammingModelError("metadata must be a mapping")
    return tuple(sorted(value.items(), key=lambda item: str(item[0])))


def _freeze_str_tuple(
    values: Iterable[object],
    allowed: tuple[str, ...],
    label: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise AfriProgrammingModelError(f"{label} must be iterable")

    normalized = tuple(_safe_str(value) for value in values)
    if not normalized or any(not value for value in normalized):
        raise AfriProgrammingModelError(f"{label} requires at least one value")

    invalid = sorted({value for value in normalized if value not in allowed})
    if invalid:
        raise AfriProgrammingModelError(
            f"unsupported {label}: " + ", ".join(invalid)
        )

    return tuple(sorted(set(normalized)))


@dataclass(frozen=True)
class AfriProgrammingAgent:
    """Autonomous engineering agent with a bounded role and capabilities."""

    agent_id: str
    name: str
    role: str
    capabilities: tuple[str, ...]
    sandbox_profile: str = "isolated"
    metadata: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.agent_id:
            raise AfriProgrammingModelError("agent_id is required")
        if not self.name:
            raise AfriProgrammingModelError("agent name is required")
        if self.role not in AGENT_ROLES:
            raise AfriProgrammingModelError(f"unsupported agent role: {self.role}")
        if not self.sandbox_profile:
            raise AfriProgrammingModelError("sandbox_profile is required")

        object.__setattr__(
            self,
            "capabilities",
            _freeze_str_tuple(self.capabilities, CAPABILITIES, "capabilities"),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AfriProgrammingAgent":
        if not isinstance(payload, Mapping):
            raise AfriProgrammingModelError("agent payload must be a mapping")

        raw_capabilities = payload.get("capabilities", ())
        return cls(
            agent_id=_safe_str(payload.get("agent_id") or payload.get("id")),
            name=_safe_str(payload.get("name")),
            role=_safe_str(payload.get("role")),
            capabilities=tuple(raw_capabilities),  # type: ignore[arg-type]
            sandbox_profile=_safe_str(payload.get("sandbox_profile"), "isolated"),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def metadata_dict(self) -> dict[str, object]:
        return dict(self.metadata)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRIPROGRAMMING_COMPONENT,
            "pillar": AFRIPROGRAMMING_PILLAR,
            "status": AFRIPROGRAMMING_STATUS,
            "classification": MODEL_CLASSIFICATION,
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
            "sandbox_profile": self.sandbox_profile,
            "metadata": self.metadata_dict(),
            "engineers_systems": True,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


@dataclass(frozen=True)
class AfriProgrammingTask:
    """Engineering intent that can be handled by autonomous agents."""

    task_id: str
    intent: str
    lifecycle_stage: str
    required_capabilities: tuple[str, ...]
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.task_id:
            raise AfriProgrammingModelError("task_id is required")
        if not self.intent:
            raise AfriProgrammingModelError("task intent is required")
        if self.lifecycle_stage not in LIFECYCLE_STAGES:
            raise AfriProgrammingModelError(
                f"unsupported lifecycle_stage: {self.lifecycle_stage}"
            )

        object.__setattr__(
            self,
            "required_capabilities",
            _freeze_str_tuple(
                self.required_capabilities,
                CAPABILITIES,
                "required_capabilities",
            ),
        )

        evidence_refs = tuple(
            sorted({ref.strip() for ref in self.evidence_refs if ref.strip()})
        )
        object.__setattr__(self, "evidence_refs", evidence_refs)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AfriProgrammingTask":
        if not isinstance(payload, Mapping):
            raise AfriProgrammingModelError("task payload must be a mapping")

        raw_capabilities = payload.get("required_capabilities", ())
        raw_evidence = payload.get("evidence_refs", ())
        return cls(
            task_id=_safe_str(payload.get("task_id") or payload.get("id")),
            intent=_safe_str(payload.get("intent")),
            lifecycle_stage=_safe_str(payload.get("lifecycle_stage")),
            required_capabilities=tuple(raw_capabilities),  # type: ignore[arg-type]
            evidence_refs=tuple(raw_evidence),  # type: ignore[arg-type]
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRIPROGRAMMING_COMPONENT,
            "pillar": AFRIPROGRAMMING_PILLAR,
            "task_id": self.task_id,
            "intent": self.intent,
            "lifecycle_stage": self.lifecycle_stage,
            "required_capabilities": self.required_capabilities,
            "evidence_refs": self.evidence_refs,
            "claim_evidence_mapping": bool(self.evidence_refs),
            "engineers_systems": True,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


@dataclass(frozen=True)
class AfriProgrammingArtifact:
    """Proof-aware engineering artifact emitted by AfriProgramming."""

    artifact_id: str
    artifact_type: str
    title: str
    source_task_id: str
    trace_refs: tuple[str, ...]
    metadata: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise AfriProgrammingModelError("artifact_id is required")
        if self.artifact_type not in ARTIFACT_TYPES:
            raise AfriProgrammingModelError(
                f"unsupported artifact_type: {self.artifact_type}"
            )
        if not self.title:
            raise AfriProgrammingModelError("artifact title is required")
        if not self.source_task_id:
            raise AfriProgrammingModelError("source_task_id is required")

        trace_refs = tuple(sorted({ref.strip() for ref in self.trace_refs if ref.strip()}))
        if not trace_refs:
            raise AfriProgrammingModelError("artifact requires trace_refs")
        object.__setattr__(self, "trace_refs", trace_refs)
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AfriProgrammingArtifact":
        if not isinstance(payload, Mapping):
            raise AfriProgrammingModelError("artifact payload must be a mapping")

        raw_trace_refs = payload.get("trace_refs", ())
        return cls(
            artifact_id=_safe_str(payload.get("artifact_id") or payload.get("id")),
            artifact_type=_safe_str(payload.get("artifact_type")),
            title=_safe_str(payload.get("title")),
            source_task_id=_safe_str(payload.get("source_task_id")),
            trace_refs=tuple(raw_trace_refs),  # type: ignore[arg-type]
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def metadata_dict(self) -> dict[str, object]:
        return dict(self.metadata)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRIPROGRAMMING_COMPONENT,
            "pillar": AFRIPROGRAMMING_PILLAR,
            "classification": ARTIFACT_CLASSIFICATION,
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "source_task_id": self.source_task_id,
            "trace_refs": self.trace_refs,
            "metadata": self.metadata_dict(),
            "proof_aware": self.artifact_type
            in {"PROOF_ARTIFACT", "WITNESS", "VERIFICATION_RECEIPT"},
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


@dataclass(frozen=True)
class AfriProgrammingEngineeringPlan:
    """Bounded autonomous engineering plan with traceable artifacts."""

    plan_id: str
    task: AfriProgrammingTask
    agents: tuple[AfriProgrammingAgent, ...]
    artifacts: tuple[AfriProgrammingArtifact, ...]

    def __post_init__(self) -> None:
        assert_afriprogramming_constitution()

        if not self.plan_id:
            raise AfriProgrammingModelError("plan_id is required")
        if not self.agents:
            raise AfriProgrammingModelError("plan requires at least one agent")
        if not self.artifacts:
            raise AfriProgrammingModelError("plan requires at least one artifact")

        agent_ids = [agent.agent_id for agent in self.agents]
        if len(agent_ids) != len(set(agent_ids)):
            raise AfriProgrammingModelError("agent IDs must be unique")

        artifact_ids = [artifact.artifact_id for artifact in self.artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise AfriProgrammingModelError("artifact IDs must be unique")

        for artifact in self.artifacts:
            if artifact.source_task_id != self.task.task_id:
                raise AfriProgrammingModelError(
                    f"artifact references unknown task: {artifact.source_task_id}"
                )

        covered_capabilities = {
            capability for agent in self.agents for capability in agent.capabilities
        }
        missing = sorted(set(self.task.required_capabilities) - covered_capabilities)
        if missing:
            raise AfriProgrammingModelError(
                "task capabilities not covered by agents: " + ", ".join(missing)
            )

        object.__setattr__(
            self,
            "agents",
            tuple(sorted(self.agents, key=lambda item: item.agent_id)),
        )
        object.__setattr__(
            self,
            "artifacts",
            tuple(sorted(self.artifacts, key=lambda item: item.artifact_id)),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRIPROGRAMMING_COMPONENT,
            "pillar": AFRIPROGRAMMING_PILLAR,
            "status": AFRIPROGRAMMING_STATUS,
            "plan_id": self.plan_id,
            "task": self.task.canonical_dict(),
            "agent_count": len(self.agents),
            "artifact_count": len(self.artifacts),
            "agents": tuple(agent.canonical_dict() for agent in self.agents),
            "artifacts": tuple(artifact.canonical_dict() for artifact in self.artifacts),
            "output_classification": OUTPUT_CLASSIFICATION,
            "engineers_systems": True,
            "proof_aware": any(
                artifact.artifact_type
                in {"PROOF_ARTIFACT", "WITNESS", "VERIFICATION_RECEIPT"}
                for artifact in self.artifacts
            ),
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


__all__ = [
    "AfriProgrammingAgent",
    "AfriProgrammingTask",
    "AfriProgrammingArtifact",
    "AfriProgrammingEngineeringPlan",
    "AfriProgrammingModelError",
]
