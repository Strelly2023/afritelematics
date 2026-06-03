"""Validate the canonical explanation composition schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_EXPLANATION_COMPOSITION_SCHEMA = (
    ROOT / "afritech/constitution/evolution/canonical_explanation_composition_schema.yaml"
)

EXPECTED_COMPOSITION_TYPES = {
    "diagnostic_sequence",
    "lineage_group",
    "replay_trace",
    "timeline",
    "validator_cluster",
}
EXPECTED_STATUS_VALUES = {"green", "red", "unknown", "yellow"}
EXPECTED_SOURCE_REF_TYPES = {"artifact", "registry", "replay", "validator"}
EXPECTED_FORBIDDEN_AUTHORITY = {
    "inferred_legitimacy",
    "narrative_truth_generation",
    "replay_truth_validation",
    "semantic_interpolation",
    "synthetic_causality",
}
EXPECTED_AUTHORITY_DISCLAIMER = (
    "This composition organizes explanations. "
    "It does not validate truth or define legitimacy."
)
EXPECTED_BUDGET = {
    "max_cross_reference_groups": 5,
    "max_nesting_levels": 3,
    "max_primary_narrative_summaries": 1,
    "max_recommended_investigation_paths": 1,
    "max_source_explanation_records": 20,
}


class CanonicalExplanationCompositionValidationError(RuntimeError):
    """Raised when composition schema drifts toward synthetic truth."""


def validate() -> None:
    validate_schema_payload(_load_yaml(CANONICAL_EXPLANATION_COMPOSITION_SCHEMA))


def validate_schema_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.canonical_explanation_composition.v1":
        _fail("canonical explanation composition schema id mismatch")
    if payload.get("authority") != "COMPOSITION_ONLY":
        _fail("canonical explanation composition schema must be COMPOSITION_ONLY")
    if payload.get("source_schema") != "afritech.canonical_explanation.v1":
        _fail("composition schema must bind to canonical explanation schema v1")

    _require_set(payload, "composition_types", EXPECTED_COMPOSITION_TYPES)
    _require_set(payload, "status_values", EXPECTED_STATUS_VALUES)
    _require_set(payload, "source_ref_types", EXPECTED_SOURCE_REF_TYPES)
    _require_set(payload, "forbidden_authority", EXPECTED_FORBIDDEN_AUTHORITY)

    if _normalize(payload.get("required_authority_disclaimer")) != (
        EXPECTED_AUTHORITY_DISCLAIMER
    ):
        _fail("required authority disclaimer must deny truth and legitimacy")

    _validate_complexity_budget(_require_mapping(payload, "complexity_budget"))

    record = _require_mapping(payload, "composition_record")
    _validate_composition_record_shape(record, payload)

    examples = _require_mapping(payload, "canonical_examples")
    if not examples:
        _fail("canonical_examples must not be empty")
    for example_id, example in sorted(examples.items()):
        if not isinstance(example, dict):
            _fail(f"canonical_examples.{example_id} must be a mapping")
        _validate_example(example_id, example, payload)

    lock = str(payload.get("lock", ""))
    if (
        "Safe units." not in lock
        or "Safe aggregation." not in lock
        or "No synthetic truth." not in lock
    ):
        _fail("schema lock must preserve safe aggregation boundary")


def _validate_complexity_budget(budget: dict[str, Any]) -> None:
    for key, expected in EXPECTED_BUDGET.items():
        if budget.get(key) != expected:
            _fail(f"complexity_budget.{key} must be {expected}")


def _validate_composition_record_shape(
    record: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    for field in (
        "advisory",
        "authority_disclaimer",
        "id",
        "omitted_detail_count",
        "source_explanation_ids",
        "source_refs",
        "status",
        "summary",
        "transformation_steps",
        "type",
    ):
        field_spec = _require_mapping(record, field, "composition_record")
        if field_spec.get("required") is not True:
            _fail(f"composition_record.{field} must be required")

    if record["id"].get("type") != "string":
        _fail("composition_record.id must be string")
    if record["summary"].get("type") != "string":
        _fail("composition_record.summary must be string")

    if record["type"].get("type") != "enum":
        _fail("composition_record.type must be enum")
    if set(record["type"].get("values", [])) != set(payload["composition_types"]):
        _fail("composition_record.type values must match composition_types")

    if record["status"].get("type") != "enum":
        _fail("composition_record.status must be enum")
    if set(record["status"].get("values", [])) != set(payload["status_values"]):
        _fail("composition_record.status values must match status_values")

    source_ids = record["source_explanation_ids"]
    if source_ids.get("type") != "list":
        _fail("composition_record.source_explanation_ids must be list")
    if source_ids.get("min_items") != 1:
        _fail("composition_record.source_explanation_ids min_items must be 1")
    if (
        source_ids.get("max_items")
        != payload["complexity_budget"]["max_source_explanation_records"]
    ):
        _fail("composition_record.source_explanation_ids max_items must match budget")

    transformation_steps = record["transformation_steps"]
    if transformation_steps.get("type") != "list":
        _fail("composition_record.transformation_steps must be list")
    if transformation_steps.get("min_items") != 1:
        _fail("composition_record.transformation_steps min_items must be 1")

    omitted = record["omitted_detail_count"]
    if omitted.get("type") != "integer":
        _fail("composition_record.omitted_detail_count must be integer")
    if omitted.get("minimum") != 0:
        _fail("composition_record.omitted_detail_count minimum must be 0")

    advisory = record["advisory"]
    if advisory.get("type") != "boolean":
        _fail("composition_record.advisory must be boolean")
    if advisory.get("required_value") is not True:
        _fail("composition_record.advisory required_value must be true")

    disclaimer = record["authority_disclaimer"]
    if disclaimer.get("type") != "string":
        _fail("composition_record.authority_disclaimer must be string")
    if _normalize(disclaimer.get("required_value")) != EXPECTED_AUTHORITY_DISCLAIMER:
        _fail("composition_record.authority_disclaimer must deny authority")

    _validate_source_refs_shape(record["source_refs"], payload)


def _validate_source_refs_shape(
    source_refs: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    if source_refs.get("type") != "list":
        _fail("composition_record.source_refs must be list")
    item_shape = _require_mapping(source_refs, "item_shape", "source_refs")
    for field in ("type", "name", "result"):
        field_spec = _require_mapping(item_shape, field, "source_refs.item_shape")
        if field_spec.get("required") is not True:
            _fail(f"source_refs.item_shape.{field} must be required")
    if set(item_shape["type"].get("values", [])) != set(payload["source_ref_types"]):
        _fail("source_refs type values must match source_ref_types")


def _validate_example(
    example_id: str,
    example: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    for field in (
        "advisory",
        "authority_disclaimer",
        "id",
        "omitted_detail_count",
        "source_explanation_ids",
        "source_refs",
        "status",
        "summary",
        "transformation_steps",
        "type",
    ):
        if field not in example:
            _fail(f"canonical_examples.{example_id} missing {field}")

    if not isinstance(example["id"], str) or not example["id"]:
        _fail(f"canonical_examples.{example_id}.id must be non-empty string")
    if example["type"] not in payload["composition_types"]:
        _fail(f"canonical_examples.{example_id}.type is not allowed")
    if example["status"] not in payload["status_values"]:
        _fail(f"canonical_examples.{example_id}.status is not allowed")
    if not isinstance(example["summary"], str) or not example["summary"]:
        _fail(f"canonical_examples.{example_id}.summary must be non-empty string")
    if example["advisory"] is not True:
        _fail(f"canonical_examples.{example_id}.advisory must be true")
    if _normalize(example["authority_disclaimer"]) != EXPECTED_AUTHORITY_DISCLAIMER:
        _fail(f"canonical_examples.{example_id}.authority_disclaimer invalid")

    source_ids = example["source_explanation_ids"]
    max_source_records = payload["complexity_budget"]["max_source_explanation_records"]
    if not isinstance(source_ids, list) or not source_ids:
        _fail(f"canonical_examples.{example_id}.source_explanation_ids required")
    if len(source_ids) > max_source_records:
        _fail(f"canonical_examples.{example_id}.source_explanation_ids exceed budget")
    if not all(isinstance(source_id, str) and source_id for source_id in source_ids):
        _fail(f"canonical_examples.{example_id}.source_explanation_ids invalid")

    transformation_steps = example["transformation_steps"]
    if not isinstance(transformation_steps, list) or not transformation_steps:
        _fail(f"canonical_examples.{example_id}.transformation_steps required")
    if not all(isinstance(step, str) and step for step in transformation_steps):
        _fail(f"canonical_examples.{example_id}.transformation_steps invalid")

    omitted_detail_count = example["omitted_detail_count"]
    if not isinstance(omitted_detail_count, int) or omitted_detail_count < 0:
        _fail(f"canonical_examples.{example_id}.omitted_detail_count invalid")

    _validate_example_source_refs(example_id, example["source_refs"], payload)


def _validate_example_source_refs(
    example_id: str,
    source_refs: Any,
    payload: dict[str, Any],
) -> None:
    if not isinstance(source_refs, list) or not source_refs:
        _fail(f"canonical_examples.{example_id}.source_refs must not be empty")
    for index, source_ref in enumerate(source_refs):
        if not isinstance(source_ref, dict):
            _fail(f"canonical_examples.{example_id}.source_refs[{index}] must map")
        if source_ref.get("type") not in payload["source_ref_types"]:
            _fail(f"canonical_examples.{example_id}.source_refs[{index}] type invalid")
        for field in ("name", "result"):
            if not isinstance(source_ref.get(field), str) or not source_ref.get(field):
                _fail(
                    f"canonical_examples.{example_id}.source_refs[{index}].{field}"
                    " must be non-empty string"
                )


def _require_set(
    payload: dict[str, Any],
    key: str,
    expected: set[str],
) -> None:
    value = payload.get(key)
    if not isinstance(value, list):
        _fail(f"{key} must be a list")
    actual = set(value)
    if actual != expected:
        _fail(f"{key} mismatch: expected {sorted(expected)}, got {sorted(actual)}")


def _require_mapping(
    payload: dict[str, Any],
    key: str,
    context: str | None = None,
) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        label = f"{context}.{key}" if context else key
        _fail(f"{label} must be a mapping")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        _fail(f"missing schema: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _fail(f"{path} must be a mapping")
    return payload


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").split())


def _fail(message: str) -> None:
    raise CanonicalExplanationCompositionValidationError(message)


def main() -> int:
    try:
        validate()
    except CanonicalExplanationCompositionValidationError as exc:
        print(f"❌ Canonical explanation composition validation FAILED: {exc}")
        return 1
    print("✅ Canonical explanation composition validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
