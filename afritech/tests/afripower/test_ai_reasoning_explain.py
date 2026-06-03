from __future__ import annotations

import pytest

from afritech.afripower.ai_reasoning.engine import (
    AFRIPowerReasoningObservation,
)
from afritech.afripower.ai_reasoning.explain import (
    AFRIPowerExplanation,
    AFRIPowerExplanationError,
    AFRIPowerExplanationReport,
    build_explanation_report,
    build_explanation_report_dict,
    ensure_explanation_boundary,
    explain_payload,
    explanation_from_observation,
)


def test_explanation_accepts_valid_values():
    explanation = AFRIPowerExplanation(
        explanation_id="explanation.001",
        summary="Interpretive explanation",
    )

    assert explanation.explanation_id == "explanation.001"
    assert explanation.summary == "Interpretive explanation"


def test_explanation_rejects_empty_id():
    with pytest.raises(AFRIPowerExplanationError):
        AFRIPowerExplanation(
            explanation_id="",
            summary="summary",
        )


def test_explanation_rejects_empty_summary():
    with pytest.raises(AFRIPowerExplanationError):
        AFRIPowerExplanation(
            explanation_id="explanation.001",
            summary="",
        )


def test_explanation_canonical_dict_preserves_boundary():
    explanation = AFRIPowerExplanation(
        explanation_id="explanation.001",
        summary="Interpretive explanation",
        evidence_ids=("receipt.001",),
    )

    data = explanation.canonical_dict()

    assert data["explanation_id"] == "explanation.001"
    assert data["summary"] == "Interpretive explanation"
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


def test_explanation_report_canonical_dict():
    report = AFRIPowerExplanationReport(
        explanations=(
            AFRIPowerExplanation(
                explanation_id="explanation.001",
                summary="Interpretive explanation",
            ),
        )
    )

    data = report.canonical_dict()

    assert data["explanation_count"] == 1
    assert len(data["explanations"]) == 1
    assert data["read_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False


def test_explanation_from_observation():
    observation = AFRIPowerReasoningObservation(
        observation_id="observation.001",
        observation_type="observation",
        summary="Observed receipt",
        evidence_ids=("receipt.001",),
    )

    explanation = explanation_from_observation(observation)

    assert explanation.explanation_id == "explanation.observation.001"
    assert "Interpretive explanation only" in explanation.summary
    assert explanation.evidence_ids == ("receipt.001",)


def test_explanation_from_observation_rejects_wrong_type():
    with pytest.raises(AFRIPowerExplanationError):
        explanation_from_observation("bad")  # type: ignore[arg-type]


def test_build_explanation_report():
    report = build_explanation_report(
        (
            {
                "receipt_id": "receipt.001",
                "receipt_type": "receipt_reference",
                "status": "existing_reference",
            },
        )
    )

    data = report.canonical_dict()

    assert data["explanation_count"] == 1
    assert data["read_only"] is True
    assert data["creates_authority"] is False


def test_build_explanation_report_dict():
    data = build_explanation_report_dict(
        (
            {
                "proof_id": "proof.001",
                "proof_type": "proof_reference",
            },
        )
    )

    assert data["explanation_count"] == 1
    assert data["read_only"] is True
    assert data["interpretive_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False


def test_explain_payload():
    data = explain_payload(
        {
            "receipt_id": "receipt.001",
            "receipt_type": "receipt_reference",
        }
    )

    assert data["explanation_id"].startswith("explanation.")
    assert data["read_only"] is True
    assert data["interpretive_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False


def test_ensure_explanation_boundary_accepts_valid_payload():
    data = explain_payload(
        {
            "receipt_id": "receipt.001",
        }
    )

    ensure_explanation_boundary(data)


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
def test_ensure_explanation_boundary_rejects_required_true_fields(
    field: str,
):
    data = explain_payload(
        {
            "receipt_id": "receipt.001",
        }
    )
    data[field] = False

    with pytest.raises(AFRIPowerExplanationError):
        ensure_explanation_boundary(data)


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
def test_ensure_explanation_boundary_rejects_required_false_fields(
    field: str,
):
    data = explain_payload(
        {
            "receipt_id": "receipt.001",
        }
    )
    data[field] = True

    with pytest.raises(AFRIPowerExplanationError):
        ensure_explanation_boundary(data)


def test_explanation_report_is_deterministic():
    payloads = (
        {
            "receipt_id": "receipt.001",
            "receipt_type": "receipt_reference",
        },
    )

    first = build_explanation_report_dict(payloads)
    second = build_explanation_report_dict(payloads)

    assert first == second
