"""Validate the cognitive salience policy for bounded attention semantics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
COGNITIVE_SALIENCE_POLICY = (
    ROOT / "afritech/constitution/evolution/cognitive_salience_policy.yaml"
)

EXPECTED_ALLOWED_SOURCES = {
    "canonical_id_ordering",
    "declared_incident_severity",
    "declared_lifecycle_state",
    "declared_timestamp_ordering",
    "replay_mismatch_status",
    "role_specific_operational_need",
    "validator_severity",
}
EXPECTED_FORBIDDEN_SOURCES = {
    "ai_preference",
    "dashboard_local_urgency_rules",
    "hidden_heuristics",
    "runtime_environment_ordering",
    "user_specific_semantic_inference",
}
EXPECTED_HIGHLIGHT_LEVELS = {"critical", "informational", "neutral", "warning"}
EXPECTED_PRIORITIZATION_FIELDS = {
    "primary_ordering_key",
    "secondary_tie_breaker",
    "source_authority",
    "stable_deterministic_fallback",
    "unknown_state_handling",
}
EXPECTED_FORBIDDEN_ORDERING = {
    "ai_preference",
    "dashboard_local_ranking",
    "hidden_heuristic_priority",
    "runtime_environment_ordering",
    "user_specific_semantic_inference",
}
EXPECTED_RECOMMENDATION_FIELDS = {
    "advisory_status",
    "alternative_inspection_paths",
    "reason_for_recommendation",
    "source_explanation_ids",
    "source_replay_or_validator_refs",
}
EXPECTED_RECOMMENDATION_FORBIDDEN = {
    "approve_exceptions",
    "create_hidden_operational_priority",
    "infer_legitimacy",
    "override_validators",
    "reinterpret_replay",
    "repair_state",
}
EXPECTED_ROLE_DIVERGENCE = {
    "role_specific_hidden_evidence",
    "role_specific_legitimacy_claims",
    "role_specific_replay_result",
    "role_specific_truth",
    "role_specific_validator_severity",
}
EXPECTED_TRANSPARENCY_FIELDS = {
    "advisory_flag",
    "authority_disclaimer",
    "ordering_key",
    "salience_id",
    "salience_level",
    "salience_type",
    "source_evidence_reference",
    "source_signal",
    "tie_breaker",
}
EXPECTED_AUTHORITY_DISCLAIMER = (
    "Salience directs attention. "
    "It does not validate truth or define legitimacy."
)
EXPECTED_ATTENTION_BUDGET = {
    "max_ai_generated_summaries": 1,
    "max_critical_banners": 1,
    "max_highlighted_items": 3,
    "max_pinned_investigation_paths": 1,
    "max_recommended_next_actions": 5,
}
EXPECTED_INCIDENT_BUDGET = {
    "max_affected_artifacts": 5,
    "max_primary_failures": 1,
    "max_recommended_next_checks": 1,
    "max_replay_or_validator_refs": 7,
    "max_secondary_failures": 3,
}
EXPECTED_AI_BUDGET = {
    "max_omitted_detail_warnings": 1,
    "max_primary_concerns": 1,
    "max_recommended_next_checks": 1,
    "max_secondary_concerns": 3,
    "max_source_explanation_records": 5,
}


class CognitiveSalienceValidationError(RuntimeError):
    """Raised when salience governance drifts toward attention authority."""


def validate() -> None:
    validate_policy_payload(_load_yaml(COGNITIVE_SALIENCE_POLICY))


def validate_policy_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.cognitive_salience_policy.v1":
        _fail("cognitive salience policy schema mismatch")
    if payload.get("authority") != "SALIENCE_ONLY":
        _fail("cognitive salience policy must be SALIENCE_ONLY")

    lock = str(payload.get("lock", ""))
    for phrase in (
        "Governed attention.",
        "Transparent priority.",
        "No salience-driven truth.",
    ):
        if phrase not in lock:
            _fail("salience lock must preserve attention boundary")

    _require_set(payload, "allowed_salience_sources", EXPECTED_ALLOWED_SOURCES)
    _require_set(payload, "forbidden_salience_sources", EXPECTED_FORBIDDEN_SOURCES)
    _require_set(payload, "highlight_levels", EXPECTED_HIGHLIGHT_LEVELS)

    if set(payload["allowed_salience_sources"]) & set(
        payload["forbidden_salience_sources"]
    ):
        _fail("salience sources cannot be both allowed and forbidden")

    _validate_prioritization(_require_mapping(payload, "deterministic_prioritization"))
    _validate_urgency(_require_mapping(payload, "urgency_constraints"))
    _validate_recommendations(_require_mapping(payload, "recommendation_transparency"))
    _validate_budget(_require_mapping(payload, "attention_budget"), EXPECTED_ATTENTION_BUDGET, "attention_budget")
    _validate_budget(_require_mapping(payload, "incident_attention_budget"), EXPECTED_INCIDENT_BUDGET, "incident_attention_budget")
    _validate_budget(_require_mapping(payload, "ai_attention_budget"), EXPECTED_AI_BUDGET, "ai_attention_budget")
    _validate_role_salience(_require_mapping(payload, "role_based_salience"))
    _validate_ai_salience(_require_mapping(payload, "ai_salience"))
    _require_set(
        payload,
        "required_transparency_fields",
        EXPECTED_TRANSPARENCY_FIELDS,
    )

    if _normalize(payload.get("required_authority_disclaimer")) != (
        EXPECTED_AUTHORITY_DISCLAIMER
    ):
        _fail("required authority disclaimer must deny truth and legitimacy")


def _validate_prioritization(section: dict[str, Any]) -> None:
    _require_set(section, "required_fields", EXPECTED_PRIORITIZATION_FIELDS)
    _require_set(section, "forbidden_ordering_sources", EXPECTED_FORBIDDEN_ORDERING)


def _validate_urgency(section: dict[str, Any]) -> None:
    _require_set(
        section,
        "critical_requires",
        {"declared_incident_severity", "replay_mismatch_status", "validator_failure"},
    )
    _require_set(section, "warning_allows", {"degraded", "incomplete_evidence", "pending"})
    if section.get("unknown_must_not_display_as_healthy") is not True:
        _fail("unknown state must not display as healthy")
    if section.get("ai_only_urgency_escalation_allowed") is not False:
        _fail("AI-only urgency escalation must be forbidden")


def _validate_recommendations(section: dict[str, Any]) -> None:
    _require_set(section, "required_fields", EXPECTED_RECOMMENDATION_FIELDS)
    _require_set(section, "forbidden_actions", EXPECTED_RECOMMENDATION_FORBIDDEN)


def _validate_budget(
    section: dict[str, Any],
    expected: dict[str, int],
    context: str,
) -> None:
    for key, expected_value in sorted(expected.items()):
        value = section.get(key)
        if value != expected_value:
            _fail(f"{context}.{key} must be {expected_value}")
        if not isinstance(value, int) or value <= 0:
            _fail(f"{context}.{key} must be a positive integer")


def _validate_role_salience(section: dict[str, Any]) -> None:
    if section.get("must_preserve_shared_source_evidence") is not True:
        _fail("role-based salience must preserve shared source evidence")
    _require_set(section, "forbidden_role_divergence", EXPECTED_ROLE_DIVERGENCE)


def _validate_ai_salience(section: dict[str, Any]) -> None:
    required_true = ("advisory_only", "must_preserve_source_refs")
    for key in required_true:
        if section.get(key) is not True:
            _fail(f"ai_salience.{key} must be true")

    required_false = (
        "may_create_urgency_from_speculation",
        "may_infer_causality",
        "may_infer_legitimacy",
        "may_override_deterministic_ordering",
        "may_prioritize_without_source_evidence",
    )
    for key in required_false:
        if section.get(key) is not False:
            _fail(f"ai_salience.{key} must be false")


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
    raise CognitiveSalienceValidationError(message)


def main() -> int:
    try:
        validate()
    except CognitiveSalienceValidationError as exc:
        print(f"❌ Cognitive salience validation FAILED: {exc}")
        return 1
    print("✅ Cognitive salience validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
