import copy

import pytest
import yaml

from afritech.ci.anticipatory_suppression_validator import (
    POLICY as ANTICIPATORY_SUPPRESSION_POLICY,
    AnticipatorySuppressionValidationError,
    validate_policy_payload as validate_anticipatory_suppression,
)
from afritech.ci.inevitability_forecasting_validator import (
    POLICY as INEVITABILITY_FORECASTING_POLICY,
    InevitabilityForecastingValidationError,
    validate_policy_payload as validate_inevitability_forecasting,
)
from afritech.ci.inevitability_reinforcement_validator import (
    POLICY as INEVITABILITY_REINFORCEMENT_POLICY,
    InevitabilityReinforcementValidationError,
    validate_policy_payload as validate_inevitability_reinforcement,
)


def load_policy(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_inevitability_forecasting_policy_is_valid():
    validate_inevitability_forecasting(load_policy(INEVITABILITY_FORECASTING_POLICY))


def test_inevitability_reinforcement_policy_is_valid():
    validate_inevitability_reinforcement(
        load_policy(INEVITABILITY_REINFORCEMENT_POLICY)
    )


def test_anticipatory_suppression_policy_is_valid():
    validate_anticipatory_suppression(load_policy(ANTICIPATORY_SUPPRESSION_POLICY))


@pytest.mark.parametrize(
    ("path", "validator", "error_type"),
    [
        (
            INEVITABILITY_FORECASTING_POLICY,
            validate_inevitability_forecasting,
            InevitabilityForecastingValidationError,
        ),
        (
            INEVITABILITY_REINFORCEMENT_POLICY,
            validate_inevitability_reinforcement,
            InevitabilityReinforcementValidationError,
        ),
        (
            ANTICIPATORY_SUPPRESSION_POLICY,
            validate_anticipatory_suppression,
            AnticipatorySuppressionValidationError,
        ),
    ],
)
def test_specialized_validators_reject_missing_base_policy_inheritance(
    path, validator, error_type
):
    broken = copy.deepcopy(load_policy(path))
    broken["inherits_policy"] = "local.predictive_authority_model.v1"

    with pytest.raises(error_type, match="inherit future-space policy"):
        validator(broken)


@pytest.mark.parametrize(
    ("path", "validator", "error_type"),
    [
        (
            INEVITABILITY_FORECASTING_POLICY,
            validate_inevitability_forecasting,
            InevitabilityForecastingValidationError,
        ),
        (
            INEVITABILITY_REINFORCEMENT_POLICY,
            validate_inevitability_reinforcement,
            InevitabilityReinforcementValidationError,
        ),
        (
            ANTICIPATORY_SUPPRESSION_POLICY,
            validate_anticipatory_suppression,
            AnticipatorySuppressionValidationError,
        ),
    ],
)
def test_specialized_validators_reject_local_authority_law(path, validator, error_type):
    broken = copy.deepcopy(load_policy(path))
    broken["lock"] = "The local predictive surface decides authority."

    with pytest.raises(error_type, match="shared authority law"):
        validator(broken)


def test_inevitability_forecasting_rejects_probability_as_legitimacy():
    broken = copy.deepcopy(load_policy(INEVITABILITY_FORECASTING_POLICY))
    broken["forbidden_drift"].remove("convert_probability_into_legitimacy")

    with pytest.raises(
        InevitabilityForecastingValidationError,
        match="forbidden_drift mismatch",
    ):
        validate_inevitability_forecasting(broken)


def test_inevitability_forecasting_rejects_missing_uncertainty_field():
    broken = copy.deepcopy(load_policy(INEVITABILITY_FORECASTING_POLICY))
    broken["required_payload_fields"].remove("forecast_uncertainty")

    with pytest.raises(
        InevitabilityForecastingValidationError,
        match="required_payload_fields mismatch",
    ):
        validate_inevitability_forecasting(broken)


def test_inevitability_reinforcement_rejects_operational_preselection():
    broken = copy.deepcopy(load_policy(INEVITABILITY_REINFORCEMENT_POLICY))
    broken["forbidden_drift"].remove("operationally_preselect_constitutional_future")

    with pytest.raises(
        InevitabilityReinforcementValidationError,
        match="forbidden_drift mismatch",
    ):
        validate_inevitability_reinforcement(broken)


def test_inevitability_reinforcement_rejects_missing_resource_routing_signal():
    broken = copy.deepcopy(load_policy(INEVITABILITY_REINFORCEMENT_POLICY))
    broken["required_payload_fields"].remove("resource_routing_signal")

    with pytest.raises(
        InevitabilityReinforcementValidationError,
        match="required_payload_fields mismatch",
    ):
        validate_inevitability_reinforcement(broken)


def test_anticipatory_suppression_rejects_risk_as_exclusion():
    broken = copy.deepcopy(load_policy(ANTICIPATORY_SUPPRESSION_POLICY))
    broken["forbidden_drift"].remove("convert_risk_into_exclusion")

    with pytest.raises(
        AnticipatorySuppressionValidationError,
        match="forbidden_drift mismatch",
    ):
        validate_anticipatory_suppression(broken)


def test_anticipatory_suppression_rejects_missing_divergence_visibility():
    broken = copy.deepcopy(load_policy(ANTICIPATORY_SUPPRESSION_POLICY))
    broken["required_payload_fields"].remove("divergence_visibility")

    with pytest.raises(
        AnticipatorySuppressionValidationError,
        match="required_payload_fields mismatch",
    ):
        validate_anticipatory_suppression(broken)
