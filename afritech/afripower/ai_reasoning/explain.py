"""
AFRIPower explanation layer.

Explanations are interpretive, observational, and display-only.

They must not:
- validate truth
- decide authority
- execute runtime behavior
- mutate artifacts
- decide admissibility
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from afritech.afripower.ai_reasoning.constants import (
    AI_REASONING_DISPLAY_ONLY,
    AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY,
    AI_REASONING_INTERPRETIVE_ONLY,
    AI_REASONING_OBSERVATIONAL_ONLY,
    AI_REASONING_PROJECTION_ONLY,
    AI_REASONING_READ_ONLY,
    AI_REASONING_REFERENCE_ONLY,
    assert_ai_reasoning_constants,
)
from afritech.afripower.ai_reasoning.engine import (
    AFRIPowerAIReasoningError,
    AFRIPowerReasoningObservation,
    build_reasoning_report,
)
from afritech.afripower.contracts.read_only_contract import (
    assert_read_only_contract,
)


class AFRIPowerExplanationError(RuntimeError):
    """Raised when AFRIPower explanation violates its boundary."""


@dataclass(frozen=True)
class AFRIPowerExplanation:
    """Immutable read-only explanation."""

    explanation_id: str
    summary: str
    evidence_ids: tuple[str, ...] = tuple()

    def __post_init__(self) -> None:
        if not self.explanation_id:
            raise AFRIPowerExplanationError("explanation_id is required")

        if not self.summary:
            raise AFRIPowerExplanationError("explanation summary is required")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "explanation_id": self.explanation_id,
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
class AFRIPowerExplanationReport:
    """Immutable read-only explanation report."""

    explanations: tuple[AFRIPowerExplanation, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "explanation_count": len(self.explanations),
            "explanations": tuple(
                explanation.canonical_dict()
                for explanation in self.explanations
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


def _assert_explanation_boundary() -> None:
    assert_read_only_contract()
    assert_ai_reasoning_constants()


def explanation_from_observation(
    observation: AFRIPowerReasoningObservation,
) -> AFRIPowerExplanation:
    """Convert one reasoning observation into an explanation."""

    _assert_explanation_boundary()

    if not isinstance(observation, AFRIPowerReasoningObservation):
        raise AFRIPowerExplanationError(
            "expected AFRIPowerReasoningObservation"
        )

    return AFRIPowerExplanation(
        explanation_id=f"explanation.{observation.observation_id}",
        summary=(
            "Interpretive explanation only: "
            f"{observation.summary}"
        ),
        evidence_ids=observation.evidence_ids,
    )


def build_explanation_report(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerExplanationReport:
    """Build a deterministic read-only explanation report."""

    _assert_explanation_boundary()

    try:
        reasoning_report = build_reasoning_report(payloads)
    except AFRIPowerAIReasoningError as exc:
        raise AFRIPowerExplanationError(str(exc)) from exc

    explanations = tuple(
        explanation_from_observation(observation)
        for observation in reasoning_report.observations
    )

    return AFRIPowerExplanationReport(explanations=explanations)


def build_explanation_report_dict(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    return build_explanation_report(payloads).canonical_dict()


def explain_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Explain one payload as read-only interpretive output."""

    report = build_explanation_report((payload,))
    data = report.canonical_dict()

    explanations = data.get("explanations", tuple())
    first = explanations[0] if explanations else {}

    if not isinstance(first, Mapping):
        raise AFRIPowerExplanationError("invalid explanation payload")

    return dict(first)


def ensure_explanation_boundary(
    payload: Mapping[str, object],
) -> None:
    """Fail closed if explanation output violates AFRIPower boundaries."""

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
            raise AFRIPowerExplanationError(
                f"explanation field must be true: {key}"
            )

    for key in required_false:
        if payload.get(key) is not False:
            raise AFRIPowerExplanationError(
                f"explanation field must be false: {key}"
            )


__all__ = [
    "AFRIPowerExplanationError",
    "AFRIPowerExplanation",
    "AFRIPowerExplanationReport",
    "explanation_from_observation",
    "build_explanation_report",
    "build_explanation_report_dict",
    "explain_payload",
    "ensure_explanation_boundary",
]
