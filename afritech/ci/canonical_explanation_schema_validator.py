"""Validate the canonical explanation schema remains non-authoritative."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_EXPLANATION_SCHEMA = (
    ROOT / "afritech/constitution/evolution/canonical_explanation_schema.yaml"
)

EXPECTED_SOURCE_AUTHORITIES = {"artifacts", "registries", "replay", "validators"}
EXPECTED_FORBIDDEN_AUTHORITY = {
    "governance_enforcement",
    "legitimacy_definition",
    "replay_truth_validation",
    "semantic_reinterpretation",
}
EXPECTED_STATUS_VALUES = {"green", "red", "unknown", "yellow"}
EXPECTED_SOURCE_REF_TYPES = {"artifact", "registry", "replay", "validator"}
EXPECTED_ALLOWED_ACTIONS = {
    "expand",
    "inspect",
    "link_to_source",
    "recommend_next_check",
}
EXPECTED_FORBIDDEN_ACTIONS = {
    "infer_legitimacy",
    "mutate_replay_meaning",
    "override_validator",
    "redefine_truth",
}


class CanonicalExplanationSchemaValidationError(RuntimeError):
    """Raised when the explanation schema drifts into authority or ambiguity."""


def validate() -> None:
    validate_schema_payload(_load_yaml(CANONICAL_EXPLANATION_SCHEMA))


def validate_schema_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.canonical_explanation.v1":
        _fail("canonical explanation schema id mismatch")
    if payload.get("authority") != "EXPLANATION_ONLY":
        _fail("canonical explanation schema must be EXPLANATION_ONLY")

    _require_set(payload, "source_authorities", EXPECTED_SOURCE_AUTHORITIES)
    _require_set(payload, "forbidden_authority", EXPECTED_FORBIDDEN_AUTHORITY)
    _require_set(payload, "status_values", EXPECTED_STATUS_VALUES)
    _require_set(payload, "source_ref_types", EXPECTED_SOURCE_REF_TYPES)
    _require_set(payload, "allowed_actions", EXPECTED_ALLOWED_ACTIONS)
    _require_set(payload, "forbidden_actions", EXPECTED_FORBIDDEN_ACTIONS)

    overlap = set(payload["allowed_actions"]) & set(payload["forbidden_actions"])
    if overlap:
        _fail(f"actions cannot be both allowed and forbidden: {sorted(overlap)}")

    record = _require_mapping(payload, "explanation_record")
    _validate_explanation_record_shape(record, payload)

    examples = _require_mapping(payload, "canonical_examples")
    if not examples:
        _fail("canonical_examples must not be empty")
    for example_id, example in sorted(examples.items()):
        if not isinstance(example, dict):
            _fail(f"canonical_examples.{example_id} must be a mapping")
        _validate_example(example_id, example, payload)

    lock = str(payload.get("lock", ""))
    if (
        "Explanations may summarize evidence." not in lock
        or "Explanations may not become evidence." not in lock
    ):
        _fail("schema lock must preserve explanation/evidence boundary")


def _validate_explanation_record_shape(
    record: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    for field in (
        "id",
        "status",
        "summary",
        "source_refs",
        "allowed_actions",
        "forbidden_actions",
    ):
        field_spec = _require_mapping(record, field, "explanation_record")
        if field_spec.get("required") is not True:
            _fail(f"explanation_record.{field} must be required")

    if record["id"].get("type") != "string":
        _fail("explanation_record.id must be string")
    if record["summary"].get("type") != "string":
        _fail("explanation_record.summary must be string")
    if record["status"].get("type") != "enum":
        _fail("explanation_record.status must be enum")
    if set(record["status"].get("values", [])) != set(payload["status_values"]):
        _fail("explanation_record.status values must match status_values")

    source_refs = record["source_refs"]
    if source_refs.get("type") != "list":
        _fail("explanation_record.source_refs must be list")
    item_shape = _require_mapping(source_refs, "item_shape", "source_refs")
    for field in ("type", "name", "result"):
        field_spec = _require_mapping(item_shape, field, "source_refs.item_shape")
        if field_spec.get("required") is not True:
            _fail(f"source_refs.item_shape.{field} must be required")
    if set(item_shape["type"].get("values", [])) != set(payload["source_ref_types"]):
        _fail("source_refs type values must match source_ref_types")

    for field in ("allowed_actions", "forbidden_actions"):
        if record[field].get("type") != "list":
            _fail(f"explanation_record.{field} must be list")
        if set(record[field].get("values", [])) != set(payload[field]):
            _fail(f"explanation_record.{field} values must match top-level {field}")


def _validate_example(
    example_id: str,
    example: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    for field in (
        "id",
        "status",
        "summary",
        "source_refs",
        "allowed_actions",
        "forbidden_actions",
    ):
        if field not in example:
            _fail(f"canonical_examples.{example_id} missing {field}")
    if not isinstance(example["id"], str) or not example["id"]:
        _fail(f"canonical_examples.{example_id}.id must be non-empty string")
    if example["status"] not in payload["status_values"]:
        _fail(f"canonical_examples.{example_id}.status is not allowed")
    if not isinstance(example["summary"], str) or not example["summary"]:
        _fail(f"canonical_examples.{example_id}.summary must be non-empty string")

    source_refs = example["source_refs"]
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

    _require_example_action_set(example_id, example, "allowed_actions", payload)
    _require_example_action_set(example_id, example, "forbidden_actions", payload)


def _require_example_action_set(
    example_id: str,
    example: dict[str, Any],
    field: str,
    payload: dict[str, Any],
) -> None:
    actions = example[field]
    if not isinstance(actions, list):
        _fail(f"canonical_examples.{example_id}.{field} must be a list")
    if set(actions) != set(payload[field]):
        _fail(f"canonical_examples.{example_id}.{field} must match schema")


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


def _fail(message: str) -> None:
    raise CanonicalExplanationSchemaValidationError(message)


def main() -> int:
    try:
        validate()
    except CanonicalExplanationSchemaValidationError as exc:
        print(f"❌ Canonical explanation schema validation FAILED: {exc}")
        return 1
    print("✅ Canonical explanation schema validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
