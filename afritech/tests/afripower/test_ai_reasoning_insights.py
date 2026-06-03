from __future__ import annotations

import pytest

from afritech.afripower.ai_reasoning.explain import AFRIPowerExplanation
from afritech.afripower.ai_reasoning.insights import (
    AFRIPowerInsight,
    AFRIPowerInsightError,
    AFRIPowerInsightReport,
    build_insight_report,
    build_insight_report_dict,
    ensure_insight_boundary,
    insight_from_explanation,
    summarize_insights,
)


def test_insight_accepts_valid_values():
    insight = AFRIPowerInsight(
        insight_id="insight.001",
        insight_type="insight",
        summary="Read-only insight",
    )

    assert insight.insight_id == "insight.001"
    assert insight.insight_type == "insight"


def test_insight_rejects_empty_id():
    with pytest.raises(AFRIPowerInsightError):
        AFRIPowerInsight(
            insight_id="",
            insight_type="insight",
            summary="summary",
        )


def test_insight_rejects_empty_type():
    with pytest.raises(AFRIPowerInsightError):
        AFRIPowerInsight(
            insight_id="insight.001",
            insight_type="",
            summary="summary",
        )


def test_insight_rejects_empty_summary():
    with pytest.raises(AFRIPowerInsightError):
        AFRIPowerInsight(
            insight_id="insight.001",
            insight_type="insight",
            summary="",
        )


@pytest.mark.parametrize(
    "forbidden_type",
    (
        "authority_decision",
        "truth_validation",
        "runtime_command",
        "governance_decision",
        "admissibility_decision",
        "proof_verdict",
        "ci_verdict",
    ),
)
def test_insight_rejects_forbidden_types(forbidden_type: str):
    with pytest.raises(AFRIPowerInsightError):
        AFRIPowerInsight(
            insight_id="insight.001",
            insight_type=forbidden_type,
            summary="forbidden",
        )


def test_insight_canonical_dict_preserves_boundary():
    insight = AFRIPowerInsight(
        insight_id="insight.001",
        insight_type="insight",
        summary="Read-only insight",
        evidence_ids=("receipt.001",),
    )

    data = insight.canonical_dict()

    assert data["insight_id"] == "insight.001"
    assert data["insight_type"] == "insight"
    assert data["summary"] == "Read-only insight"
    assert data["evidence_ids"] == ("receipt.001",)

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["observational_only"] is True
    assert data["interpretive_only"] is True
    assert data["enterprise_intelligence_only"] is True

    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False
    assert data["decides_admissibility"] is False
    assert data["influences_runtime"] is False
    assert data["influences_replay"] is False
    assert data["influences_proof"] is False
    assert data["influences_ci"] is False
    assert data["influences_governance"] is False


def test_insight_report_canonical_dict():
    report = AFRIPowerInsightReport(
        insights=(
            AFRIPowerInsight(
                insight_id="insight.001",
                insight_type="insight",
                summary="Read-only insight",
            ),
        )
    )

    data = report.canonical_dict()

    assert data["insight_count"] == 1
    assert len(data["insights"]) == 1

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["observational_only"] is True
    assert data["interpretive_only"] is True
    assert data["enterprise_intelligence_only"] is True

    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False
    assert data["decides_admissibility"] is False


def test_insight_from_explanation():
    explanation = AFRIPowerExplanation(
        explanation_id="explanation.001",
        summary="Interpretive explanation",
        evidence_ids=("receipt.001",),
    )

    insight = insight_from_explanation(explanation)

    assert insight.insight_id == "insight.explanation.001"
    assert insight.insight_type == "insight"
    assert "Read-only enterprise insight" in insight.summary
    assert insight.evidence_ids == ("receipt.001",)


def test_insight_from_explanation_rejects_wrong_type():
    with pytest.raises(AFRIPowerInsightError):
        insight_from_explanation("bad")  # type: ignore[arg-type]


def test_build_insight_report():
    report = build_insight_report(
        (
            {
                "receipt_id": "receipt.001",
                "receipt_type": "receipt_reference",
                "status": "existing_reference",
            },
        )
    )

    data = report.canonical_dict()

    assert data["insight_count"] == 1
    assert data["read_only"] is True
    assert data["creates_authority"] is False


def test_build_insight_report_dict():
    data = build_insight_report_dict(
        (
            {
                "proof_id": "proof.001",
                "proof_type": "proof_reference",
            },
        )
    )

    assert data["insight_count"] == 1
    assert data["read_only"] is True
    assert data["interpretive_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False


def test_summarize_insights():
    data = summarize_insights(
        (
            {
                "receipt_id": "receipt.001",
                "receipt_type": "receipt_reference",
            },
        )
    )

    assert data["insight_count"] == 1
    assert len(data["insight_ids"]) == 1
    assert len(data["summaries"]) == 1

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["observational_only"] is True
    assert data["interpretive_only"] is True
    assert data["enterprise_intelligence_only"] is True

    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False
    assert data["decides_admissibility"] is False


def test_ensure_insight_boundary_accepts_report():
    data = build_insight_report_dict(
        (
            {
                "receipt_id": "receipt.001",
            },
        )
    )

    ensure_insight_boundary(data)


def test_ensure_insight_boundary_accepts_summary():
    data = summarize_insights(
        (
            {
                "receipt_id": "receipt.001",
            },
        )
    )

    ensure_insight_boundary(data)


@pytest.mark.parametrize(
    "field",
    (
        "read_only",
        "reference_only",
        "display_only",
        "projection_only",
        "observational_only",
        "interpretive_only",
        "enterprise_intelligence_only",
    ),
)
def test_ensure_insight_boundary_rejects_required_true_fields(field: str):
    data = build_insight_report_dict(
        (
            {"receipt_id": "receipt.001"},
        )
    )
    data[field] = False

    with pytest.raises(AFRIPowerInsightError):
        ensure_insight_boundary(data)


@pytest.mark.parametrize(
    "field",
    (
        "creates_authority",
        "validates_truth",
        "executes_runtime",
        "mutates_artifacts",
        "decides_admissibility",
    ),
)
def test_ensure_insight_boundary_rejects_required_false_fields(field: str):
    data = build_insight_report_dict(
        (
            {"receipt_id": "receipt.001"},
        )
    )
    data[field] = True

    with pytest.raises(AFRIPowerInsightError):
        ensure_insight_boundary(data)


def test_insight_report_is_deterministic():
    payloads = (
        {
            "receipt_id": "receipt.001",
            "receipt_type": "receipt_reference",
        },
    )

    first = build_insight_report_dict(payloads)
    second = build_insight_report_dict(payloads)

    assert first == second


def test_insight_summary_is_deterministic():
    payloads = (
        {
            "receipt_id": "receipt.001",
            "receipt_type": "receipt_reference",
        },
    )

    first = summarize_insights(payloads)
    second = summarize_insights(payloads)

    assert first == second
