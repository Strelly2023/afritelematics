import copy

import pytest
import yaml

from afritech.ci.observability_authority_validator import (
    GA_WORKFLOW,
    POLICY,
    ObservabilityAuthorityValidationError,
    validate_ga_workflow,
    validate_policy_payload,
)


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_observability_authority_policy_is_valid():
    validate_policy_payload(load_yaml(POLICY))


def test_ga_observability_step_is_non_blocking():
    validate_ga_workflow(load_yaml(POLICY), GA_WORKFLOW.read_text(encoding="utf-8"))


def test_rejects_observability_surface_with_validation_authority():
    payload = load_yaml(POLICY)
    broken = copy.deepcopy(payload)
    broken["observability_surfaces"]["compat_status_cli"][
        "authority_scope"
    ] = "VALIDATION_ONLY"

    with pytest.raises(ObservabilityAuthorityValidationError, match="OBSERVATION_ONLY"):
        validate_policy_payload(broken)


def test_rejects_observability_surface_that_allows_forbidden_action():
    payload = load_yaml(POLICY)
    broken = copy.deepcopy(payload)
    broken["observability_surfaces"]["compat_status_cli"][
        "allowed_actions"
    ].append("validate_truth")

    with pytest.raises(
        ObservabilityAuthorityValidationError,
        match="allows forbidden actions",
    ):
        validate_policy_payload(broken)


def test_rejects_observability_surface_missing_required_forbidden_action():
    payload = load_yaml(POLICY)
    broken = copy.deepcopy(payload)
    broken["observability_surfaces"]["compat_status_cli"][
        "forbidden_actions"
    ].remove("define_legitimacy")

    with pytest.raises(
        ObservabilityAuthorityValidationError,
        match="missing forbidden actions",
    ):
        validate_policy_payload(broken)


def test_rejects_blocking_ga_observability_step():
    payload = load_yaml(POLICY)
    workflow = GA_WORKFLOW.read_text(encoding="utf-8").replace(
        "        continue-on-error: true\n"
        "        run: python3 -m afritech.tools.compat_status status",
        "        run: python3 -m afritech.tools.compat_status status",
    )

    with pytest.raises(ObservabilityAuthorityValidationError, match="non-blocking"):
        validate_ga_workflow(payload, workflow)
