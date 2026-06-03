import copy

import pytest
import yaml

from afritech.ci.canonical_explanation_composition_validator import (
    CANONICAL_EXPLANATION_COMPOSITION_SCHEMA,
    CanonicalExplanationCompositionValidationError,
    validate_schema_payload,
)


def load_schema():
    return yaml.safe_load(
        CANONICAL_EXPLANATION_COMPOSITION_SCHEMA.read_text(encoding="utf-8")
    )


def test_canonical_explanation_composition_schema_is_valid():
    validate_schema_payload(load_schema())


def test_rejects_non_composition_authority():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["authority"] = "EXPLANATION_ONLY"

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="COMPOSITION_ONLY",
    ):
        validate_schema_payload(broken)


def test_rejects_missing_source_schema_binding():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["source_schema"] = "afritech.synthetic_narrative.v1"

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="canonical explanation schema",
    ):
        validate_schema_payload(broken)


def test_rejects_missing_forbidden_authority():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["forbidden_authority"].remove("synthetic_causality")

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="forbidden_authority mismatch",
    ):
        validate_schema_payload(broken)


def test_rejects_record_shape_without_required_source_explanation_ids():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["composition_record"]["source_explanation_ids"]["required"] = False

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="source_explanation_ids must be required",
    ):
        validate_schema_payload(broken)


def test_rejects_record_shape_without_advisory_required_true():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["composition_record"]["advisory"]["required_value"] = False

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="advisory required_value must be true",
    ):
        validate_schema_payload(broken)


def test_rejects_example_without_source_explanation_ids():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["canonical_examples"]["compatibility_timeline"][
        "source_explanation_ids"
    ] = []

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="source_explanation_ids required",
    ):
        validate_schema_payload(broken)


def test_rejects_example_with_false_advisory_flag():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["canonical_examples"]["compatibility_timeline"]["advisory"] = False

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="advisory must be true",
    ):
        validate_schema_payload(broken)


def test_rejects_example_with_authoritative_disclaimer():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["canonical_examples"]["compatibility_timeline"][
        "authority_disclaimer"
    ] = "This composition validates truth."

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="authority_disclaimer invalid",
    ):
        validate_schema_payload(broken)


def test_rejects_example_that_exceeds_source_record_budget():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["canonical_examples"]["compatibility_timeline"][
        "source_explanation_ids"
    ] = [f"explanation.{index}" for index in range(21)]

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="exceed budget",
    ):
        validate_schema_payload(broken)


def test_rejects_example_without_transformation_steps():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["canonical_examples"]["compatibility_timeline"][
        "transformation_steps"
    ] = []

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="transformation_steps required",
    ):
        validate_schema_payload(broken)


def test_rejects_schema_without_safe_aggregation_lock():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["lock"] = "Compositions are evidence."

    with pytest.raises(
        CanonicalExplanationCompositionValidationError,
        match="safe aggregation boundary",
    ):
        validate_schema_payload(broken)
