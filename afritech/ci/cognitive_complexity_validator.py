"""Validate the cognitive complexity budget for bounded cognition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
COGNITIVE_COMPLEXITY_BUDGET = (
    ROOT / "afritech/constitution/evolution/cognitive_complexity_budget.yaml"
)

EXPECTED_CORE_TESTS = {
    "avoid_changing_meaning",
    "preserve_source_evidence",
    "reduce_cognitive_load",
}
EXPECTED_FORBIDDEN_PATTERNS = {
    "ai_legitimacy_inference",
    "dashboards_that_obscure_source_references",
    "hidden_evidence_omission",
    "meaning_changing_compression",
    "role_views_with_conflicting_semantics",
    "synthetic_causality",
    "unbounded_diagnostic_branching",
    "unbounded_lineage_expansion",
}
EXPECTED_WARNING_FIELDS = {
    "actual_count",
    "allowed_count",
    "drill_down_path",
    "exceeded_budget_name",
    "omitted_detail_count",
}
EXPECTED_SOURCE_PRESERVATION = {
    "authority_disclaimer",
    "drill_down_path",
    "omitted_detail_count",
    "source_explanation_ids",
    "source_refs",
}
EXPECTED_BUDGETS = {
    "diagnostic_fan_out.max_next_actions": 7,
    "lineage_depth.max_default_depth": 3,
    "narrative_branching.max_branches": 5,
    "replay_relationship_exposure.max_default_relationships": 15,
    "role_complexity.max_role_specific_dimensions": 6,
    "view_density.max_visible_units": 12,
}


class CognitiveComplexityValidationError(RuntimeError):
    """Raised when cognitive complexity governance drifts."""


def validate() -> None:
    validate_budget_payload(_load_yaml(COGNITIVE_COMPLEXITY_BUDGET))


def validate_budget_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.cognitive_complexity_budget.v1":
        _fail("cognitive complexity budget schema mismatch")
    if payload.get("authority") != "BUDGET_ONLY":
        _fail("cognitive complexity budget must be BUDGET_ONLY")

    lock = str(payload.get("lock", ""))
    for phrase in (
        "Bounded cognition.",
        "Preserved evidence.",
        "No hidden meaning.",
    ):
        if phrase not in lock:
            _fail("budget lock must preserve bounded cognition boundary")

    _validate_core_tests(_require_mapping(payload, "core_tests"))
    _validate_budget_values(payload)
    _validate_ai_summarization_scope(
        _require_mapping(payload, "ai_summarization_scope")
    )
    _validate_boolean_requirement(
        _require_mapping(payload, "lineage_depth"),
        "expandable_with_source_refs",
        "lineage_depth",
    )
    _validate_boolean_requirement(
        _require_mapping(payload, "replay_relationship_exposure"),
        "requires_progressive_disclosure",
        "replay_relationship_exposure",
    )

    _require_set(payload, "forbidden_patterns", EXPECTED_FORBIDDEN_PATTERNS)
    _require_set(payload, "required_warning_fields", EXPECTED_WARNING_FIELDS)
    _require_set(
        payload,
        "required_source_preservation",
        EXPECTED_SOURCE_PRESERVATION,
    )
    _validate_future_surfaces(_require_mapping(payload, "future_surfaces"))


def _validate_core_tests(core_tests: dict[str, Any]) -> None:
    if set(core_tests) != EXPECTED_CORE_TESTS:
        _fail("core_tests must define the three bounded cognition tests")
    for key, value in sorted(core_tests.items()):
        if value is not True:
            _fail(f"core_tests.{key} must be true")


def _validate_budget_values(payload: dict[str, Any]) -> None:
    for dotted_key, expected_value in sorted(EXPECTED_BUDGETS.items()):
        section_name, field = dotted_key.split(".")
        section = _require_mapping(payload, section_name)
        value = section.get(field)
        if value != expected_value:
            _fail(f"{dotted_key} must be {expected_value}")
        if not isinstance(value, int) or value <= 0:
            _fail(f"{dotted_key} must be a positive integer")


def _validate_ai_summarization_scope(scope: dict[str, Any]) -> None:
    if scope.get("max_source_records") != 20:
        _fail("ai_summarization_scope.max_source_records must be 20")
    if scope.get("must_preserve_source_refs") is not True:
        _fail("ai_summarization_scope.must_preserve_source_refs must be true")
    if scope.get("may_infer_legitimacy") is not False:
        _fail("ai_summarization_scope.may_infer_legitimacy must be false")


def _validate_boolean_requirement(
    payload: dict[str, Any],
    key: str,
    context: str,
) -> None:
    if payload.get(key) is not True:
        _fail(f"{context}.{key} must be true")


def _validate_future_surfaces(surfaces: dict[str, Any]) -> None:
    for surface_name in ("ai_assistants", "cli", "dashboards"):
        surface = _require_mapping(surfaces, surface_name, "future_surfaces")
        if surface.get("must_preserve_source_refs") is not True:
            _fail(f"future_surfaces.{surface_name} must preserve source refs")

    dashboards = surfaces["dashboards"]
    if dashboards.get("must_use_canonical_explanation_schema") is not True:
        _fail("dashboards must use canonical explanation schema")
    if dashboards.get("must_use_canonical_composition_schema_for_narratives") is not True:
        _fail("dashboards must use canonical composition schema for narratives")

    cli = surfaces["cli"]
    if cli.get("must_match_dashboard_health_language") is not True:
        _fail("cli must match dashboard health language")

    ai_assistants = surfaces["ai_assistants"]
    if ai_assistants.get("advisory_only") is not True:
        _fail("ai assistants must remain advisory")
    if ai_assistants.get("may_infer_legitimacy") is not False:
        _fail("ai assistants may not infer legitimacy")


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
        _fail(f"missing budget: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _fail(f"{path} must be a mapping")
    return payload


def _fail(message: str) -> None:
    raise CognitiveComplexityValidationError(message)


def main() -> int:
    try:
        validate()
    except CognitiveComplexityValidationError as exc:
        print(f"❌ Cognitive complexity validation FAILED: {exc}")
        return 1
    print("✅ Cognitive complexity validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
