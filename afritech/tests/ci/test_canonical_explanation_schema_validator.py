import copy

import pytest
import yaml

from afritech.ci.canonical_explanation_schema_validator import (
    CANONICAL_EXPLANATION_SCHEMA,
    CanonicalExplanationSchemaValidationError,
    validate_schema_payload,
)


def load_schema():
    return yaml.safe_load(CANONICAL_EXPLANATION_SCHEMA.read_text(encoding="utf-8"))


def test_canonical_explanation_schema_is_valid():
    validate_schema_payload(load_schema())


def test_rejects_non_explanation_authority():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["authority"] = "VALIDATION_ONLY"

    with pytest.raises(
        CanonicalExplanationSchemaValidationError,
        match="EXPLANATION_ONLY",
    ):
        validate_schema_payload(broken)


def test_rejects_missing_source_authority():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["source_authorities"].remove("replay")

    with pytest.raises(
        CanonicalExplanationSchemaValidationError,
        match="source_authorities mismatch",
    ):
        validate_schema_payload(broken)


def test_rejects_missing_forbidden_authority():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["forbidden_authority"].remove("legitimacy_definition")

    with pytest.raises(
        CanonicalExplanationSchemaValidationError,
        match="forbidden_authority mismatch",
    ):
        validate_schema_payload(broken)


def test_rejects_allowed_action_that_is_also_forbidden():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["allowed_actions"].append("redefine_truth")

    with pytest.raises(
        CanonicalExplanationSchemaValidationError,
        match="allowed_actions mismatch",
    ):
        validate_schema_payload(broken)


def test_rejects_record_shape_without_required_source_refs():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["explanation_record"]["source_refs"]["required"] = False

    with pytest.raises(
        CanonicalExplanationSchemaValidationError,
        match="source_refs must be required",
    ):
        validate_schema_payload(broken)


def test_rejects_example_without_source_refs():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["canonical_examples"]["compatibility_green"]["source_refs"] = []

    with pytest.raises(
        CanonicalExplanationSchemaValidationError,
        match="source_refs must not be empty",
    ):
        validate_schema_payload(broken)


def test_rejects_schema_without_explanation_evidence_lock():
    payload = load_schema()
    broken = copy.deepcopy(payload)
    broken["lock"] = "Explanations are evidence."

    with pytest.raises(
        CanonicalExplanationSchemaValidationError,
        match="explanation/evidence boundary",
    ):
        validate_schema_payload(broken)
