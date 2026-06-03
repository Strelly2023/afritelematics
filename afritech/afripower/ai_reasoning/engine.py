"""
AFRIPower AI reasoning engine.

The engine produces read-only, interpretive observations from existing
references, graph summaries, dashboard metrics, and projection payloads.

It must not:
- validate truth
- execute runtime behavior
- mutate artifacts
- create authority
- decide admissibility
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from afritech.afripower.ai_reasoning.constants import (
    AI_REASONING_DISPLAY_ONLY,
    AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY,
    AI_REASONING_FORBIDDEN_OUTPUT_TYPES,
    AI_REASONING_INTERPRETIVE_ONLY,
    AI_REASONING_OBSERVATIONAL_ONLY,
    AI_REASONING_OUTPUT_TYPES,
    AI_REASONING_PROJECTION_ONLY,
    AI_REASONING_READ_ONLY,
    AI_REASONING_REFERENCE_ONLY,
    assert_ai_reasoning_constants,
)
from afritech.afripower.contracts.read_only_contract import (
    assert_read_only_contract,
)


class AFRIPowerAIReasoningError(RuntimeError):
    """Raised when AFRIPower AI reasoning violates its boundary."""


@dataclass(frozen=True)
class AFRIPowerReasoningInput:
    """Immutable read-only reasoning input."""

    input_id: str
    input_type: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.input_id:
            raise AFRIPowerAIReasoningError("reasoning input_id is required")

        if not self.input_type:
            raise AFRIPowerAIReasoningError("reasoning input_type is required")

        if not isinstance(self.payload, Mapping):
            raise AFRIPowerAIReasoningError("reasoning payload must be a mapping")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "input_id": self.input_id,
            "input_type": self.input_type,
            "payload": dict(self.payload),
            "read_only": AI_REASONING_READ_ONLY,
            "reference_only": AI_REASONING_REFERENCE_ONLY,
            "display_only": AI_REASONING_DISPLAY_ONLY,
            "projection_only": AI_REASONING_PROJECTION_ONLY,
            "observational_only": AI_REASONING_OBSERVATIONAL_ONLY,
            "interpretive_only": AI_REASONING_INTERPRETIVE_ONLY,
            "enterprise_intelligence_only": (
                AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY
            ),
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
            "decides_admissibility": False,
        }


@dataclass(frozen=True)
class AFRIPowerReasoningObservation:
    """Immutable interpretive observation."""

    observation_id: str
    observation_type: str
    summary: str
    evidence_ids: tuple[str, ...] = tuple()

    def __post_init__(self) -> None:
        if self.observation_type in AI_REASONING_FORBIDDEN_OUTPUT_TYPES:
            raise AFRIPowerAIReasoningError(
                f"forbidden reasoning output type: {self.observation_type}"
            )

        if self.observation_type not in AI_REASONING_OUTPUT_TYPES:
            raise AFRIPowerAIReasoningError(
                f"unsupported reasoning output type: {self.observation_type}"
            )

        if not self.observation_id:
            raise AFRIPowerAIReasoningError(
                "reasoning observation_id is required"
            )

        if not self.summary:
            raise AFRIPowerAIReasoningError(
                "reasoning observation summary is required"
            )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "observation_id": self.observation_id,
            "observation_type": self.observation_type,
            "summary": self.summary,
            "evidence_ids": tuple(self.evidence_ids),
            "read_only": AI_REASONING_READ_ONLY,
            "reference_only": AI_REASONING_REFERENCE_ONLY,
            "display_only": AI_REASONING_DISPLAY_ONLY,
            "projection_only": AI_REASONING_PROJECTION_ONLY,
            "observational_only": AI_REASONING_OBSERVATIONAL_ONLY,
            "interpretive_only": AI_REASONING_INTERPRETIVE_ONLY,
            "enterprise_intelligence_only": (
                AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY
            ),
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
            "decides_admissibility": False,
            "influences_runtime": False,
            "influences_replay": False,
            "influences_proof": False,
            "influences_ci": False,
            "influences_governance": False,
        }


@dataclass(frozen=True)
class AFRIPowerReasoningReport:
    """Immutable read-only reasoning report."""

    observations: tuple[AFRIPowerReasoningObservation, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "observation_count": len(self.observations),
            "observations": tuple(
                observation.canonical_dict()
                for observation in self.observations
            ),
            "read_only": AI_REASONING_READ_ONLY,
            "reference_only": AI_REASONING_REFERENCE_ONLY,
            "display_only": AI_REASONING_DISPLAY_ONLY,
            "projection_only": AI_REASONING_PROJECTION_ONLY,
            "observational_only": AI_REASONING_OBSERVATIONAL_ONLY,
            "interpretive_only": AI_REASONING_INTERPRETIVE_ONLY,
            "enterprise_intelligence_only": (
                AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY
            ),
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
            "decides_admissibility": False,
        }


def _assert_reasoning_boundary() -> None:
    assert_read_only_contract()
    assert_ai_reasoning_constants()


def _safe_str(value: object, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def reasoning_input_from_mapping(
    payload: Mapping[str, object],
) -> AFRIPowerReasoningInput:
    """Build a read-only reasoning input from a mapping."""

    _assert_reasoning_boundary()

    if not isinstance(payload, Mapping):
        raise AFRIPowerAIReasoningError(
            "reasoning input payload must be a mapping"
        )

    input_id = _safe_str(
        payload.get("input_id")
        or payload.get("artifact_id")
        or payload.get("execution_id")
        or payload.get("receipt_id")
        or payload.get("proof_id")
        or payload.get("id")
        or "unknown-input"
    )

    input_type = _safe_str(
        payload.get("input_type")
        or payload.get("artifact_type")
        or payload.get("receipt_type")
        or payload.get("proof_type")
        or payload.get("type")
        or "projection_payload"
    )

    return AFRIPowerReasoningInput(
        input_id=input_id,
        input_type=input_type,
        payload=dict(payload),
    )


def build_observation_from_input(
    reasoning_input: AFRIPowerReasoningInput,
) -> AFRIPowerReasoningObservation:
    """
    Build an interpretive observation from one input.

    This is not truth validation. It is a display-only reasoning summary.
    """

    _assert_reasoning_boundary()

    payload = reasoning_input.payload

    declared_status = _safe_str(payload.get("status"), "observed")
    declared_label = _safe_str(
        payload.get("label")
        or payload.get("title")
        or reasoning_input.input_id
    )

    summary = (
        f"Observed {reasoning_input.input_type} reference "
        f"{declared_label} with status {declared_status}."
    )

    return AFRIPowerReasoningObservation(
        observation_id=f"observation.{reasoning_input.input_id}",
        observation_type="observation",
        summary=summary,
        evidence_ids=(reasoning_input.input_id,),
    )


def build_reasoning_report(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerReasoningReport:
    """Build a deterministic read-only reasoning report."""

    _assert_reasoning_boundary()

    inputs = tuple(
        reasoning_input_from_mapping(payload)
        for payload in payloads
    )

    observations = tuple(
        build_observation_from_input(reasoning_input)
        for reasoning_input in inputs
    )

    return AFRIPowerReasoningReport(observations=observations)


def build_reasoning_report_dict(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    return build_reasoning_report(payloads).canonical_dict()


def ensure_reasoning_boundary(
    payload: Mapping[str, object],
) -> None:
    """Fail closed if a reasoning output violates AFRIPower boundaries."""

    required_true = (
        "read_only",
        "reference_only",
        "display_only",
        "projection_only",
        "observational_only",
        "interpretive_only",
        "enterprise_intelligence_only",
    )

    required_false = (
        "creates_authority",
        "validates_truth",
        "executes_runtime",
        "mutates_artifacts",
        "decides_admissibility",
    )

    for key in required_true:
        if payload.get(key) is not True:
            raise AFRIPowerAIReasoningError(
                f"reasoning field must be true: {key}"
            )

    for key in required_false:
        if payload.get(key) is not False:
            raise AFRIPowerAIReasoningError(
                f"reasoning field must be false: {key}"
            )


__all__ = [
    "AFRIPowerAIReasoningError",
    "AFRIPowerReasoningInput",
    "AFRIPowerReasoningObservation",
    "AFRIPowerReasoningReport",
    "reasoning_input_from_mapping",
    "build_observation_from_input",
    "build_reasoning_report",
    "build_reasoning_report_dict",
    "ensure_reasoning_boundary",
]
