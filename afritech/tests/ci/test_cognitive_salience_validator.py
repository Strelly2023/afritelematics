import copy

import pytest
import yaml

from afritech.ci.cognitive_salience_validator import (
    COGNITIVE_SALIENCE_POLICY,
    CognitiveSalienceValidationError,
    validate_policy_payload,
)


def load_policy():
    return yaml.safe_load(COGNITIVE_SALIENCE_POLICY.read_text(encoding="utf-8"))


def test_cognitive_salience_policy_is_valid():
    validate_policy_payload(load_policy())


def test_rejects_non_salience_authority():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["authority"] = "BUDGET_ONLY"

    with pytest.raises(CognitiveSalienceValidationError, match="SALIENCE_ONLY"):
        validate_policy_payload(broken)


def test_rejects_missing_salience_lock():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["lock"] = "Attention creates truth."

    with pytest.raises(CognitiveSalienceValidationError, match="attention boundary"):
        validate_policy_payload(broken)


def test_rejects_missing_allowed_source():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["allowed_salience_sources"].remove("validator_severity")

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="allowed_salience_sources mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_hidden_heuristics_as_allowed_source():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["allowed_salience_sources"].append("hidden_heuristics")

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="allowed_salience_sources mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_forbidden_source():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["forbidden_salience_sources"].remove("ai_preference")

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="forbidden_salience_sources mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_unbounded_highlight_items():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["attention_budget"]["max_highlighted_items"] = 9

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="max_highlighted_items must be 3",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_prioritization_field():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["deterministic_prioritization"]["required_fields"].remove(
        "stable_deterministic_fallback"
    )

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="required_fields mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_ai_only_urgency_escalation():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["urgency_constraints"]["ai_only_urgency_escalation_allowed"] = True

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="AI-only urgency escalation",
    ):
        validate_policy_payload(broken)


def test_rejects_recommendation_without_source_ids():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["recommendation_transparency"]["required_fields"].remove(
        "source_explanation_ids"
    )

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="required_fields mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_role_specific_truth_allowed():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["role_based_salience"]["forbidden_role_divergence"].remove(
        "role_specific_truth"
    )

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="forbidden_role_divergence mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_ai_legitimacy_inference():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["ai_salience"]["may_infer_legitimacy"] = True

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="may_infer_legitimacy must be false",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_transparency_field():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["required_transparency_fields"].remove("source_evidence_reference")

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="required_transparency_fields mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_authority_disclaimer_drift():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["required_authority_disclaimer"] = "Salience validates truth."

    with pytest.raises(
        CognitiveSalienceValidationError,
        match="deny truth and legitimacy",
    ):
        validate_policy_payload(broken)
