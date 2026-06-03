"""Validate temporal cognition consistency for longitudinal cognition governance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
TEMPORAL_COGNITION_POLICY = (
    ROOT / "afritech/constitution/evolution/temporal_cognition_policy.yaml"
)

EXPECTED_REQUIRED_CONTEXT = {
    "authority_disclaimer",
    "cognitive_complexity_budget_version",
    "composition_schema_version",
    "evidence_id",
    "explanation_schema_version",
    "salience_policy_version",
    "summary_template_version",
}
EXPECTED_CONDITIONAL_CONTEXT = {
    "ai_model_version",
    "epoch_context",
    "translator_context",
}
EXPECTED_DRIFT_SURFACES = {
    "ai_model_upgrade",
    "epoch_evolution",
    "policy_evolution",
    "summary_template_evolution",
    "translator_evolution",
    "ui_redesign",
}
EXPECTED_EXPLANATION_PRESERVATION = {
    "authority_boundary",
    "explanation_identifiers",
    "replay_implications",
    "source_references",
    "status_meaning",
    "validator_semantics",
}
EXPECTED_EXPLANATION_FORBIDDEN = {
    "changing_replay_mismatch_meaning_through_wording",
    "hiding_old_hard_failures_in_modernized_summaries",
    "presenting_translated_explanation_as_original_evidence",
    "red_failure_to_yellow_warning_without_source_change",
    "removing_source_evidence_from_newer_explanations",
}
EXPECTED_SALIENCE_VERSIONS = {
    "ai_salience_model_version_when_ai_is_used",
    "ordering_rule_version",
    "salience_policy_version",
    "urgency_classification_version",
}
EXPECTED_SALIENCE_FORBIDDEN = {
    "ai_only_reprioritization",
    "hidden_salience_weighting_change",
    "silent_priority_downgrade",
    "silent_urgency_inflation",
    "visual_redesign_hides_critical_historical_failures",
}
EXPECTED_NARRATIVE_PRESERVATION = {
    "authority_disclaimers",
    "composition_source_ids",
    "narrative_template_version",
    "summarization_policy_version",
    "transformation_steps",
}
EXPECTED_NARRATIVE_FORBIDDEN = {
    "advisory_narrative_to_evidence",
    "adding_synthetic_legitimacy",
    "changing_incident_meaning_without_source_change",
    "inferring_new_causality",
    "removing_omitted_detail_indicators",
}
EXPECTED_AI_FIELDS = {
    "advisory_status",
    "authority_disclaimer",
    "model_identifier",
    "omitted_detail_indicator",
    "prompt_or_template_version",
    "salience_policy_version",
    "source_explanation_ids",
}
EXPECTED_AI_FORBIDDEN = {
    "changing_hard_failure_severity",
    "creating_model_version_dependent_operational_reality",
    "hiding_old_evidence",
    "inferring_legitimacy_from_old_evidence",
    "synthesizing_replay_truth",
}
EXPECTED_ORDERING_ALLOWED = {
    "accessibility_ordering_with_preserved_semantics",
    "clearer_grouping_with_preserved_source_ids",
    "new_declared_tie_breaker",
    "role_scoped_ordering_with_declared_policy_version",
}
EXPECTED_ORDERING_FORBIDDEN = {
    "ai_model_preference_ordering",
    "dashboard_redesign_ordering_without_declaration",
    "hidden_priority_rewrite",
    "removing_hard_failures_from_top_level_historical_view",
    "runtime_order_dependent_historical_replay_display",
}
EXPECTED_FORBIDDEN_DRIFT = {
    "ai_model_cognition_instability",
    "authority_disclaimer_loss",
    "epoch_context_loss",
    "explanation_reinterpretation",
    "hard_failure_softening",
    "narrative_divergence",
    "salience_drift",
    "source_reference_loss",
    "summary_drift",
    "translator_context_loss",
}
EXPECTED_AUTHORITY_DISCLAIMER = (
    "This cognition artifact presents evidence under declared temporal context. "
    "It does not validate truth or define legitimacy."
)


class TemporalCognitionValidationError(RuntimeError):
    """Raised when temporal cognition policy permits longitudinal drift."""


def validate() -> None:
    validate_policy_payload(_load_yaml(TEMPORAL_COGNITION_POLICY))


def validate_policy_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.temporal_cognition_policy.v1":
        _fail("temporal cognition policy schema mismatch")
    if payload.get("authority") != "TEMPORAL_CONSISTENCY_ONLY":
        _fail("temporal cognition policy must be TEMPORAL_CONSISTENCY_ONLY")

    lock = str(payload.get("lock", ""))
    for phrase in (
        "Evolution may improve cognition.",
        "Evidence meaning must persist.",
        "Operational reality must remain time-stable.",
    ):
        if phrase not in lock:
            _fail("temporal cognition lock must preserve longitudinal boundary")

    _require_set(payload, "required_context", EXPECTED_REQUIRED_CONTEXT)
    _require_set(payload, "conditional_context", EXPECTED_CONDITIONAL_CONTEXT)
    _require_set(payload, "temporal_drift_surfaces", EXPECTED_DRIFT_SURFACES)
    _require_set(payload, "forbidden_temporal_drift", EXPECTED_FORBIDDEN_DRIFT)

    _validate_explanation_equivalence(
        _require_mapping(payload, "temporal_explanation_equivalence")
    )
    _validate_salience_stability(
        _require_mapping(payload, "temporal_salience_stability")
    )
    _validate_narrative_stability(
        _require_mapping(payload, "temporal_narrative_stability")
    )
    _validate_ai_temporal_stability(
        _require_mapping(payload, "ai_temporal_stability")
    )
    _validate_ordering_stability(
        _require_mapping(payload, "temporal_ordering_stability")
    )

    if _normalize(payload.get("required_authority_disclaimer")) != (
        EXPECTED_AUTHORITY_DISCLAIMER
    ):
        _fail("required authority disclaimer must deny truth and legitimacy")


def _validate_explanation_equivalence(section: dict[str, Any]) -> None:
    _require_set(section, "required_preservation", EXPECTED_EXPLANATION_PRESERVATION)
    _require_set(section, "forbidden_changes", EXPECTED_EXPLANATION_FORBIDDEN)


def _validate_salience_stability(section: dict[str, Any]) -> None:
    _require_set(section, "required_visible_versions", EXPECTED_SALIENCE_VERSIONS)
    _require_set(section, "forbidden_changes", EXPECTED_SALIENCE_FORBIDDEN)


def _validate_narrative_stability(section: dict[str, Any]) -> None:
    _require_set(section, "required_preservation", EXPECTED_NARRATIVE_PRESERVATION)
    _require_set(section, "forbidden_changes", EXPECTED_NARRATIVE_FORBIDDEN)


def _validate_ai_temporal_stability(section: dict[str, Any]) -> None:
    _require_set(section, "required_fields", EXPECTED_AI_FIELDS)
    _require_set(section, "forbidden_changes", EXPECTED_AI_FORBIDDEN)


def _validate_ordering_stability(section: dict[str, Any]) -> None:
    _require_set(section, "allowed_evolution", EXPECTED_ORDERING_ALLOWED)
    _require_set(section, "forbidden_evolution", EXPECTED_ORDERING_FORBIDDEN)


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
        _fail(f"missing policy: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _fail(f"{path} must be a mapping")
    return payload


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").split())


def _fail(message: str) -> None:
    raise TemporalCognitionValidationError(message)


def main() -> int:
    try:
        validate()
    except TemporalCognitionValidationError as exc:
        print(f"❌ Temporal cognition validation FAILED: {exc}")
        return 1
    print("✅ Temporal cognition validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
