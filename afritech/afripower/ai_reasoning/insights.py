"""
AFRIPower insights layer.

Insights are read-only, interpretive, observational outputs derived from
existing references, explanations, dashboard summaries, and projection data.

They must not:
- validate truth
- create authority
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
from afritech.afripower.ai_reasoning.explain import (
    AFRIPowerExplanation,
    build_explanation_report,
)
from afritech.afripower.contracts.read_only_contract import (
    assert_read_only_contract,
)


class AFRIPowerInsightError(RuntimeError):
    """Raised when AFRIPower insight generation violates its boundary."""


@dataclass(frozen=True)
class AFRIPowerInsight:
    """Immutable read-only AFRIPower insight."""

    insight_id: str
    insight_type: str
    summary: str
    evidence_ids: tuple[str, ...] = tuple()

    def __post_init__(self) -> None:
        if not self.insight_id:
            raise AFRIPowerInsightError("insight_id is required")

        if not self.insight_type:
            raise AFRIPowerInsightError("insight_type is required")

        if self.insight_type in (
            "authority_decision",
            "truth_validation",
            "runtime_command",
            "governance_decision",
            "admissibility_decision",
            "proof_verdict",
            "ci_verdict",
        ):
            raise AFRIPowerInsightError(
                f"forbidden insight type: {self.insight_type}"
            )

        if not self.summary:
            raise AFRIPowerInsightError("insight summary is required")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "insight_id": self.insight_id,
            "insight_type": self.insight_type,
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
class AFRIPowerInsightReport:
    """Immutable read-only insight report."""

    insights: tuple[AFRIPowerInsight, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "insight_count": len(self.insights),
            "insights": tuple(
                insight.canonical_dict()
                for insight in self.insights
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


def _assert_insight_boundary() -> None:
    assert_read_only_contract()
    assert_ai_reasoning_constants()


def insight_from_explanation(
    explanation: AFRIPowerExplanation,
) -> AFRIPowerInsight:
    """Convert one explanation into a read-only insight."""

    _assert_insight_boundary()

    if not isinstance(explanation, AFRIPowerExplanation):
        raise AFRIPowerInsightError(
            "expected AFRIPowerExplanation"
        )

    return AFRIPowerInsight(
        insight_id=f"insight.{explanation.explanation_id}",
        insight_type="insight",
        summary=(
            "Read-only enterprise insight: "
            f"{explanation.summary}"
        ),
        evidence_ids=explanation.evidence_ids,
    )


def build_insight_report(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerInsightReport:
    """Build deterministic read-only insights from existing payloads."""

    _assert_insight_boundary()

    explanation_report = build_explanation_report(payloads)

    insights = tuple(
        insight_from_explanation(explanation)
        for explanation in explanation_report.explanations
    )

    return AFRIPowerInsightReport(insights=insights)


def build_insight_report_dict(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    return build_insight_report(payloads).canonical_dict()


def summarize_insights(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """
    Return a compact read-only insight summary.

    This is observational only and does not validate truth.
    """

    report = build_insight_report(payloads)

    return {
        "insight_count": len(report.insights),
        "insight_ids": tuple(
            insight.insight_id
            for insight in report.insights
        ),
        "summaries": tuple(
            insight.summary
            for insight in report.insights
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


def ensure_insight_boundary(
    payload: Mapping[str, object],
) -> None:
    """Fail closed if insight output violates AFRIPower boundaries."""

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
            raise AFRIPowerInsightError(
                f"insight field must be true: {key}"
            )

    for key in required_false:
        if payload.get(key) is not False:
            raise AFRIPowerInsightError(
                f"insight field must be false: {key}"
            )


__all__ = [
    "AFRIPowerInsightError",
    "AFRIPowerInsight",
    "AFRIPowerInsightReport",
    "insight_from_explanation",
    "build_insight_report",
    "build_insight_report_dict",
    "summarize_insights",
    "ensure_insight_boundary",
]
