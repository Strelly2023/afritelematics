from __future__ import annotations

import pytest

from afritech.afripower.ai_reasoning import constants as ai_constants


def test_ai_reasoning_identity():
    assert ai_constants.AI_REASONING_COMPONENT == "AFRIPowerAIReasoning"
    assert ai_constants.AI_REASONING_COMPONENT_ID == (
        "afritech.afripower.ai_reasoning"
    )
    assert ai_constants.AI_REASONING_VERSION == "1.0"


def test_ai_reasoning_status_and_mode():
    assert ai_constants.AI_REASONING_STATUS == (
        "INTERPRETIVE_OBSERVATIONAL_ONLY"
    )
    assert ai_constants.AI_REASONING_MODE == (
        "READ_ONLY_ENTERPRISE_INTELLIGENCE_REASONING"
    )


def test_ai_reasoning_safe_flags_are_true():
    assert ai_constants.AI_REASONING_READ_ONLY is True
    assert ai_constants.AI_REASONING_REFERENCE_ONLY is True
    assert ai_constants.AI_REASONING_DISPLAY_ONLY is True
    assert ai_constants.AI_REASONING_PROJECTION_ONLY is True
    assert ai_constants.AI_REASONING_OBSERVATIONAL_ONLY is True
    assert ai_constants.AI_REASONING_INTERPRETIVE_ONLY is True
    assert ai_constants.AI_REASONING_ENTERPRISE_INTELLIGENCE_ONLY is True


def test_ai_reasoning_authority_flags_are_false():
    assert ai_constants.AI_REASONING_AUTHORITATIVE is False
    assert ai_constants.AI_REASONING_CREATES_AUTHORITY is False
    assert ai_constants.AI_REASONING_VALIDATES_TRUTH is False
    assert ai_constants.AI_REASONING_EXECUTES_RUNTIME is False
    assert ai_constants.AI_REASONING_MUTATES_ARTIFACTS is False
    assert ai_constants.AI_REASONING_DECIDES_ADMISSIBILITY is False
    assert ai_constants.AI_REASONING_INFLUENCES_RUNTIME is False
    assert ai_constants.AI_REASONING_INFLUENCES_REPLAY is False
    assert ai_constants.AI_REASONING_INFLUENCES_PROOF is False
    assert ai_constants.AI_REASONING_INFLUENCES_CI is False
    assert ai_constants.AI_REASONING_INFLUENCES_GOVERNANCE is False


def test_ai_reasoning_input_types():
    assert "graph_summary" in ai_constants.AI_REASONING_INPUT_TYPES
    assert "dashboard_metrics" in ai_constants.AI_REASONING_INPUT_TYPES
    assert "receipt_reference" in ai_constants.AI_REASONING_INPUT_TYPES
    assert "proof_reference" in ai_constants.AI_REASONING_INPUT_TYPES
    assert "traceability_reference" in ai_constants.AI_REASONING_INPUT_TYPES
    assert "projection_payload" in ai_constants.AI_REASONING_INPUT_TYPES


def test_ai_reasoning_output_types():
    assert "summary" in ai_constants.AI_REASONING_OUTPUT_TYPES
    assert "explanation" in ai_constants.AI_REASONING_OUTPUT_TYPES
    assert "insight" in ai_constants.AI_REASONING_OUTPUT_TYPES
    assert "observation" in ai_constants.AI_REASONING_OUTPUT_TYPES
    assert "recommendation_for_human_review" in (
        ai_constants.AI_REASONING_OUTPUT_TYPES
    )


def test_ai_reasoning_forbidden_output_types():
    assert "authority_decision" in ai_constants.AI_REASONING_FORBIDDEN_OUTPUT_TYPES
    assert "truth_validation" in ai_constants.AI_REASONING_FORBIDDEN_OUTPUT_TYPES
    assert "runtime_command" in ai_constants.AI_REASONING_FORBIDDEN_OUTPUT_TYPES
    assert "governance_decision" in ai_constants.AI_REASONING_FORBIDDEN_OUTPUT_TYPES
    assert "admissibility_decision" in (
        ai_constants.AI_REASONING_FORBIDDEN_OUTPUT_TYPES
    )
    assert "proof_verdict" in ai_constants.AI_REASONING_FORBIDDEN_OUTPUT_TYPES
    assert "ci_verdict" in ai_constants.AI_REASONING_FORBIDDEN_OUTPUT_TYPES


def test_ai_reasoning_metadata_preserves_boundary():
    metadata = ai_constants.ai_reasoning_metadata()

    assert metadata["component"] == "AFRIPowerAIReasoning"
    assert metadata["read_only"] is True
    assert metadata["reference_only"] is True
    assert metadata["display_only"] is True
    assert metadata["projection_only"] is True
    assert metadata["observational_only"] is True
    assert metadata["interpretive_only"] is True
    assert metadata["enterprise_intelligence_only"] is True

    assert metadata["authoritative"] is False
    assert metadata["creates_authority"] is False
    assert metadata["validates_truth"] is False
    assert metadata["executes_runtime"] is False
    assert metadata["mutates_artifacts"] is False
    assert metadata["decides_admissibility"] is False
    assert metadata["influences_runtime"] is False
    assert metadata["influences_replay"] is False
    assert metadata["influences_proof"] is False
    assert metadata["influences_ci"] is False
    assert metadata["influences_governance"] is False


def test_ai_reasoning_metadata_is_deterministic():
    assert (
        ai_constants.ai_reasoning_metadata()
        == ai_constants.ai_reasoning_metadata()
    )


def test_assert_ai_reasoning_constants_passes():
    ai_constants.assert_ai_reasoning_constants()


def test_assert_ai_reasoning_constants_fails_on_authority(monkeypatch):
    monkeypatch.setattr(ai_constants, "AI_REASONING_AUTHORITATIVE", True)

    with pytest.raises(RuntimeError):
        ai_constants.assert_ai_reasoning_constants()


def test_assert_ai_reasoning_constants_fails_on_truth_validation(monkeypatch):
    monkeypatch.setattr(ai_constants, "AI_REASONING_VALIDATES_TRUTH", True)

    with pytest.raises(RuntimeError):
        ai_constants.assert_ai_reasoning_constants()


def test_assert_ai_reasoning_constants_fails_on_runtime_execution(monkeypatch):
    monkeypatch.setattr(ai_constants, "AI_REASONING_EXECUTES_RUNTIME", True)

    with pytest.raises(RuntimeError):
        ai_constants.assert_ai_reasoning_constants()


def test_assert_ai_reasoning_constants_fails_on_mutation(monkeypatch):
    monkeypatch.setattr(ai_constants, "AI_REASONING_MUTATES_ARTIFACTS", True)

    with pytest.raises(RuntimeError):
        ai_constants.assert_ai_reasoning_constants()


def test_assert_ai_reasoning_constants_fails_on_admissibility_decision(
    monkeypatch,
):
    monkeypatch.setattr(
        ai_constants,
        "AI_REASONING_DECIDES_ADMISSIBILITY",
        True,
    )

    with pytest.raises(RuntimeError):
        ai_constants.assert_ai_reasoning_constants()


def test_assert_ai_reasoning_constants_fails_on_missing_read_only(monkeypatch):
    monkeypatch.setattr(ai_constants, "AI_REASONING_READ_ONLY", False)

    with pytest.raises(RuntimeError):
        ai_constants.assert_ai_reasoning_constants()
