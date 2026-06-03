import copy

import pytest
import yaml

from afritech.ci.predictive_future_space_validator import (
    PREDICTIVE_FUTURE_SPACE_POLICY,
    PredictiveFutureSpaceValidationError,
    validate_policy_payload,
)


def load_policy():
    return yaml.safe_load(PREDICTIVE_FUTURE_SPACE_POLICY.read_text(encoding="utf-8"))


def test_predictive_future_space_policy_is_valid():
    validate_policy_payload(load_policy())


def test_rejects_non_predictive_review_authority():
    broken = copy.deepcopy(load_policy())
    broken["authority"] = "PREDICTIVE_SELECTION_ALLOWED"

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="PREDICTIVE_REVIEW_ONLY",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_predictive_lock():
    broken = copy.deepcopy(load_policy())
    broken["lock"] = "Prediction chooses. Risk excludes."

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="authority boundary",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_probability_legitimacy_separation():
    broken = copy.deepcopy(load_policy())
    broken["invariant_separations"].remove("probability_legitimacy")

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="invariant_separations mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_uncertainty_illegitimacy_separation():
    broken = copy.deepcopy(load_policy())
    broken["invariant_separations"].remove("uncertainty_illegitimacy")

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="invariant_separations mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_future_selection_forbidden_action():
    broken = copy.deepcopy(load_policy())
    broken["forbidden_predictive_actions"].remove(
        "operationally_select_constitutional_futures"
    )

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="forbidden_predictive_actions mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_admissible_future_suppression_forbidden_action():
    broken = copy.deepcopy(load_policy())
    broken["forbidden_predictive_actions"].remove(
        "suppress_admissible_constitutional_futures"
    )

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="forbidden_predictive_actions mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_forecast_legitimacy_drift():
    broken = copy.deepcopy(load_policy())
    broken["inevitability_forecasting"]["forbidden_drift"].remove(
        "prediction_derived_legitimacy"
    )

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="forbidden_drift mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_self_fulfilling_reinforcement_detection():
    broken = copy.deepcopy(load_policy())
    broken["inevitability_reinforcement_monitoring"][
        "required_detection"
    ].remove("self_fulfilling_legitimacy")

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="required_detection mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_predictive_resource_routing_as_authority():
    broken = copy.deepcopy(load_policy())
    broken["inevitability_reinforcement_monitoring"]["forbidden_drift"].remove(
        "resource_routing_to_predicted_legitimacy"
    )

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="forbidden_drift mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_missing_authorized_divergence_preservation():
    broken = copy.deepcopy(load_policy())
    broken["anticipatory_suppression_analysis"]["required_preservation"].remove(
        "authorized_divergence"
    )

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="required_preservation mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_uncertainty_based_exclusion():
    broken = copy.deepcopy(load_policy())
    broken["anticipatory_suppression_analysis"]["forbidden_drift"].remove(
        "uncertainty_based_exclusion"
    )

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="forbidden_drift mismatch",
    ):
        validate_policy_payload(broken)


def test_rejects_authority_disclaimer_drift():
    broken = copy.deepcopy(load_policy())
    broken["required_authority_disclaimer"] = (
        "This predictive artifact can select likely futures."
    )

    with pytest.raises(
        PredictiveFutureSpaceValidationError,
        match="deny future selection authority",
    ):
        validate_policy_payload(broken)
