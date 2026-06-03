import copy

import pytest
import yaml

from afritech.ci.temporal_cognition_validator import (
    TEMPORAL_COGNITION_POLICY,
    TemporalCognitionValidationError,
    validate_policy_payload,
)


def load_policy():
    return yaml.safe_load(TEMPORAL_COGNITION_POLICY.read_text(encoding="utf-8"))


def test_temporal_cognition_policy_is_valid():
    validate_policy_payload(load_policy())


def test_rejects_non_temporal_authority():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["authority"] = "SALIENCE_ONLY"

    with pytest.raises(
        TemporalCognitionValidationError,
        match="TEMPORAL_CONSISTENCY_ONLY",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_temporal_lock():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["lock"] = "Evolution may rewrite operational reality."

    with pytest.raises(
        TemporalCognitionValidationError,
        match="longitudinal boundary",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_required_context():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["required_context"].remove("evidence_id")

    with pytest.raises(
        TemporalCognitionValidationError,
        match="required_context mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_ai_conditional_context():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["conditional_context"].remove("ai_model_version")

    with pytest.raises(
        TemporalCognitionValidationError,
        match="conditional_context mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_temporal_drift_surface():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["temporal_drift_surfaces"].remove("ui_redesign")

    with pytest.raises(
        TemporalCognitionValidationError,
        match="temporal_drift_surfaces mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_source_reference_preservation():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["temporal_explanation_equivalence"]["required_preservation"].remove(
        "source_references"
    )

    with pytest.raises(
        TemporalCognitionValidationError,
        match="required_preservation mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_softening_hard_failure_through_explanation():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["temporal_explanation_equivalence"]["forbidden_changes"].remove(
        "red_failure_to_yellow_warning_without_source_change"
    )

    with pytest.raises(
        TemporalCognitionValidationError,
        match="forbidden_changes mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_salience_policy_version():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["temporal_salience_stability"]["required_visible_versions"].remove(
        "salience_policy_version"
    )

    with pytest.raises(
        TemporalCognitionValidationError,
        match="required_visible_versions mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_ai_only_reprioritization_allowed():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["temporal_salience_stability"]["forbidden_changes"].remove(
        "ai_only_reprioritization"
    )

    with pytest.raises(
        TemporalCognitionValidationError,
        match="forbidden_changes mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_narrative_source_ids():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["temporal_narrative_stability"]["required_preservation"].remove(
        "composition_source_ids"
    )

    with pytest.raises(
        TemporalCognitionValidationError,
        match="required_preservation mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_ai_advisory_status():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["ai_temporal_stability"]["required_fields"].remove("advisory_status")

    with pytest.raises(
        TemporalCognitionValidationError,
        match="required_fields mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_model_version_dependent_operational_reality():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["ai_temporal_stability"]["forbidden_changes"].remove(
        "creating_model_version_dependent_operational_reality"
    )

    with pytest.raises(
        TemporalCognitionValidationError,
        match="forbidden_changes mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_hidden_ordering_rewrite():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["temporal_ordering_stability"]["forbidden_evolution"].remove(
        "hidden_priority_rewrite"
    )

    with pytest.raises(
        TemporalCognitionValidationError,
        match="forbidden_evolution mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_forbidden_temporal_drift():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["forbidden_temporal_drift"].remove("summary_drift")

    with pytest.raises(
        TemporalCognitionValidationError,
        match="forbidden_temporal_drift mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_authority_disclaimer_drift():
    payload = load_policy()
    broken = copy.deepcopy(payload)
    broken["required_authority_disclaimer"] = "Temporal cognition validates truth."

    with pytest.raises(
        TemporalCognitionValidationError,
        match="deny truth and legitimacy",
    ):
        validate_policy_payload(broken)
