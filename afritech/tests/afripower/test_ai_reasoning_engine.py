from __future__ import annotations

import pytest

from afritech.afripower.ai_reasoning.engine import (
    AFRIPowerAIReasoningError,
    AFRIPowerReasoningInput,
    AFRIPowerReasoningObservation,
    AFRIPowerReasoningReport,
    build_observation_from_input,
    build_reasoning_report,
    build_reasoning_report_dict,
    ensure_reasoning_boundary,
    reasoning_input_from_mapping,
)


def test_reasoning_input_accepts_valid_values():
    item = AFRIPowerReasoningInput(
        input_id="receipt.001",
        input_type="receipt_reference",
        payload={"status": "existing_reference"},
    )

    assert item.input_id == "receipt.001"
    assert item.input_type == "receipt_reference"


def test_reasoning_input_rejects_empty_id():
    with pytest.raises(AFRIPowerAIReasoningError):
        AFRIPowerReasoningInput(
            input_id="",
            input_type="receipt_reference",
            payload={},
        )


def test_reasoning_input_rejects_empty_type():
    with pytest.raises(AFRIPowerAIReasoningError):
        AFRIPowerReasoningInput(
            input_id="receipt.001",
            input_type="",
            payload={},
        )


def test_reasoning_input_rejects_non_mapping_payload():
    with pytest.raises(AFRIPowerAIReasoningError):
        AFRIPowerReasoningInput(
            input_id="receipt.001",
            input_type="receipt_reference",
            payload="bad",  # type: ignore[arg-type]
        )


def test_reasoning_input_canonical_dict():
    item = AFRIPowerReasoningInput(
        input_id="receipt.001",
        input_type="receipt_reference",
        payload={"status": "existing_reference"},
    )

    data = item.canonical_dict()

    assert data["input_id"] == "receipt.001"
    assert data["input_type"] == "receipt_reference"

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


def test_reasoning_input_from_mapping_execution():
    item = reasoning_input_from_mapping(
        {
            "execution_id": "exec.001",
        }
    )

    assert item.input_id == "exec.001"
    assert item.input_type == "projection_payload"


def test_reasoning_input_from_mapping_receipt():
    item = reasoning_input_from_mapping(
        {
            "receipt_id": "receipt.001",
            "receipt_type": "receipt_reference",
        }
    )

    assert item.input_id == "receipt.001"
    assert item.input_type == "receipt_reference"


def test_reasoning_input_from_mapping_proof():
    item = reasoning_input_from_mapping(
        {
            "proof_id": "proof.001",
            "proof_type": "proof_reference",
        }
    )

    assert item.input_id == "proof.001"
    assert item.input_type == "proof_reference"


def test_reasoning_input_from_mapping_rejects_non_mapping():
    with pytest.raises(AFRIPowerAIReasoningError):
        reasoning_input_from_mapping("bad")  # type: ignore[arg-type]


def test_observation_accepts_valid_values():
    observation = AFRIPowerReasoningObservation(
        observation_id="obs.001",
        observation_type="observation",
        summary="Observed payload",
    )

    assert observation.observation_id == "obs.001"


def test_observation_rejects_forbidden_type():
    with pytest.raises(AFRIPowerAIReasoningError):
        AFRIPowerReasoningObservation(
            observation_id="obs.001",
            observation_type="authority_decision",
            summary="bad",
        )


def test_observation_rejects_empty_summary():
    with pytest.raises(AFRIPowerAIReasoningError):
        AFRIPowerReasoningObservation(
            observation_id="obs.001",
            observation_type="observation",
            summary="",
        )


def test_observation_canonical_dict():
    observation = AFRIPowerReasoningObservation(
        observation_id="obs.001",
        observation_type="observation",
        summary="Observed payload",
        evidence_ids=("receipt.001",),
    )

    data = observation.canonical_dict()

    assert data["observation_id"] == "obs.001"
    assert data["evidence_ids"] == ("receipt.001",)

    assert data["read_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False


def test_build_observation_from_input():
    item = AFRIPowerReasoningInput(
        input_id="receipt.001",
        input_type="receipt_reference",
        payload={"status": "existing_reference"},
    )

    observation = build_observation_from_input(item)

    assert observation.observation_type == "observation"
    assert observation.evidence_ids == ("receipt.001",)


def test_reasoning_report_canonical_dict():
    report = AFRIPowerReasoningReport(
        observations=(
            AFRIPowerReasoningObservation(
                observation_id="obs.001",
                observation_type="observation",
                summary="Observed payload",
            ),
        )
    )

    data = report.canonical_dict()

    assert data["observation_count"] == 1
    assert len(data["observations"]) == 1

    assert data["read_only"] is True
    assert data["creates_authority"] is False


def test_build_reasoning_report():
    report = build_reasoning_report(
        (
            {
                "receipt_id": "receipt.001",
                "receipt_type": "receipt_reference",
                "status": "existing_reference",
            },
        )
    )

    assert report.canonical_dict()["observation_count"] == 1


def test_build_reasoning_report_dict():
    data = build_reasoning_report_dict(
        (
            {
                "receipt_id": "receipt.001",
                "receipt_type": "receipt_reference",
            },
        )
    )

    assert data["observation_count"] == 1
    assert data["read_only"] is True
    assert data["creates_authority"] is False


def test_ensure_reasoning_boundary_accepts_valid_payload():
    payload = build_reasoning_report_dict(
        (
            {
                "receipt_id": "receipt.001",
            },
        )
    )

    ensure_reasoning_boundary(payload)


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
def test_ensure_reasoning_boundary_rejects_required_true_fields(
    field: str,
):
    payload = build_reasoning_report_dict(
        (
            {"receipt_id": "receipt.001"},
        )
    )

    payload[field] = False

    with pytest.raises(AFRIPowerAIReasoningError):
        ensure_reasoning_boundary(payload)


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
def test_ensure_reasoning_boundary_rejects_required_false_fields(
    field: str,
):
    payload = build_reasoning_report_dict(
        (
            {"receipt_id": "receipt.001"},
        )
    )

    payload[field] = True

    with pytest.raises(AFRIPowerAIReasoningError):
        ensure_reasoning_boundary(payload)


def test_reasoning_report_is_deterministic():
    payloads = (
        {
            "receipt_id": "receipt.001",
            "receipt_type": "receipt_reference",
        },
    )

    first = build_reasoning_report_dict(payloads)
    second = build_reasoning_report_dict(payloads)

    assert first == second
