import copy

import pytest
import yaml

from afritech.ci.cognitive_complexity_validator import (
    COGNITIVE_COMPLEXITY_BUDGET,
    CognitiveComplexityValidationError,
    validate_budget_payload,
)


def load_budget():
    return yaml.safe_load(COGNITIVE_COMPLEXITY_BUDGET.read_text(encoding="utf-8"))


def test_cognitive_complexity_budget_is_valid():
    validate_budget_payload(load_budget())


def test_rejects_non_budget_authority():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["authority"] = "EXPLANATION_ONLY"

    with pytest.raises(CognitiveComplexityValidationError, match="BUDGET_ONLY"):
        validate_budget_payload(broken)


def test_rejects_missing_core_test():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    del broken["core_tests"]["reduce_cognitive_load"]

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="three bounded cognition tests",
    ):
        validate_budget_payload(broken)


def test_rejects_core_test_disabled():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["core_tests"]["preserve_source_evidence"] = False

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="preserve_source_evidence must be true",
    ):
        validate_budget_payload(broken)


def test_rejects_view_density_budget_drift():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["view_density"]["max_visible_units"] = 24

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="view_density.max_visible_units must be 12",
    ):
        validate_budget_payload(broken)


def test_rejects_unbounded_lineage_depth():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["lineage_depth"]["expandable_with_source_refs"] = False

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="expandable_with_source_refs must be true",
    ):
        validate_budget_payload(broken)


def test_rejects_ai_legitimacy_inference():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["ai_summarization_scope"]["may_infer_legitimacy"] = True

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="may_infer_legitimacy must be false",
    ):
        validate_budget_payload(broken)


def test_rejects_missing_forbidden_pattern():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["forbidden_patterns"].remove("synthetic_causality")

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="forbidden_patterns mismatch",
    ):
        validate_budget_payload(broken)


def test_rejects_missing_warning_field():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["required_warning_fields"].remove("omitted_detail_count")

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="required_warning_fields mismatch",
    ):
        validate_budget_payload(broken)


def test_rejects_missing_source_preservation_field():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["required_source_preservation"].remove("source_refs")

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="required_source_preservation mismatch",
    ):
        validate_budget_payload(broken)


def test_rejects_dashboard_without_source_refs():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["future_surfaces"]["dashboards"]["must_preserve_source_refs"] = False

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="dashboards must preserve source refs",
    ):
        validate_budget_payload(broken)


def test_rejects_ai_assistant_without_advisory_boundary():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["future_surfaces"]["ai_assistants"]["advisory_only"] = False

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="ai assistants must remain advisory",
    ):
        validate_budget_payload(broken)


def test_rejects_budget_without_boundary_lock():
    payload = load_budget()
    broken = copy.deepcopy(payload)
    broken["lock"] = "Cognition may hide meaning."

    with pytest.raises(
        CognitiveComplexityValidationError,
        match="bounded cognition boundary",
    ):
        validate_budget_payload(broken)
