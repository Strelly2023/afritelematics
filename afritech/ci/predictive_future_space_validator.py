"""Validate predictive future-space survivability governance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
PREDICTIVE_FUTURE_SPACE_POLICY = (
    ROOT / "afritech/constitution/evolution/predictive_future_space_policy.yaml"
)

EXPECTED_REQUIRED_CONTEXT = {
    "authority_disclaimer",
    "constitution_reference",
    "future_space_scope",
    "prediction_model_version",
    "ratification_status",
    "replay_reference",
    "risk_model_version",
    "validator_reference",
}
EXPECTED_SURFACES = {
    "anticipatory_suppression_analysis",
    "inevitability_forecasting",
    "inevitability_reinforcement_monitoring",
}
EXPECTED_INVARIANT_SEPARATIONS = {
    "awareness_authority",
    "forecasting_future_selection",
    "prediction_destiny",
    "probability_legitimacy",
    "risk_exclusion",
    "uncertainty_illegitimacy",
}
EXPECTED_ALLOWED_ACTIONS = {
    "analyze_uncertainty",
    "compare_future_scenarios",
    "detect_reinforcement_loops",
    "expose_prediction_pressure",
    "forecast_trajectories",
    "model_instability",
    "reveal_lock_in_dynamics",
    "simulate_constitutional_pressure",
    "surface_convergence_pressure",
    "warn_about_future_risk",
}
EXPECTED_FORBIDDEN_ACTIONS = {
    "collapse_constitutional_plurality",
    "convert_prediction_into_legitimacy",
    "convert_risk_into_exclusion",
    "operationally_select_constitutional_futures",
    "operationalize_inevitability",
    "pre_ratify_constitutional_destiny",
    "silently_narrow_admissible_futures",
    "suppress_admissible_constitutional_futures",
}
EXPECTED_FORECAST_PRESERVATION = {
    "forecast_uncertainty",
    "future_plurality",
    "probability_authority_separation",
    "ratification_status",
    "replay_reference",
}
EXPECTED_FORECAST_FORBIDDEN = {
    "future_space_collapse",
    "high_probability_future_as_authority",
    "prediction_derived_legitimacy",
    "probabilistic_destiny",
}
EXPECTED_REINFORCEMENT_DETECTION = {
    "forecast_amplification",
    "operational_future_preselection",
    "prediction_driven_resource_concentration",
    "recommendation_pressure",
    "salience_amplification",
    "self_fulfilling_legitimacy",
}
EXPECTED_REINFORCEMENT_FORBIDDEN = {
    "forecast_confidence_to_operational_priority",
    "predictive_optimization_as_authority",
    "resource_routing_to_predicted_legitimacy",
    "self_fulfilling_future_selection",
}
EXPECTED_SUPPRESSION_PRESERVATION = {
    "admissible_future_space",
    "alternative_governance_trajectories",
    "authorized_divergence",
    "constitutional_experimentation_space",
    "low_confidence_constitutional_futures",
    "uncertainty_legitimacy_separation",
}
EXPECTED_SUPPRESSION_FORBIDDEN = {
    "preventive_future_closure",
    "risk_derived_illegitimacy",
    "suppression_of_authorized_divergence",
    "uncertainty_based_exclusion",
}
EXPECTED_AUTHORITY_DISCLAIMER = (
    "This predictive artifact informs review by describing future pressure, "
    "uncertainty, and reinforcement risk. It does not select, suppress, "
    "ratify, or legitimize constitutional futures."
)


class PredictiveFutureSpaceValidationError(RuntimeError):
    """Raised when predictive future-space policy permits authority drift."""


def validate() -> None:
    validate_policy_payload(_load_yaml(PREDICTIVE_FUTURE_SPACE_POLICY))


def validate_policy_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.predictive_future_space_policy.v1":
        _fail("predictive future-space policy schema mismatch")
    if payload.get("authority") != "PREDICTIVE_REVIEW_ONLY":
        _fail("predictive future-space policy must be PREDICTIVE_REVIEW_ONLY")

    lock = str(payload.get("lock", ""))
    for phrase in (
        "Prediction informs.",
        "Risk informs.",
        "Authority decides.",
        "Forecasts may not choose the future.",
        "Risk may not erase the future.",
        "AfriTech can see possible futures without being captured by them.",
    ):
        if phrase not in lock:
            _fail("predictive future-space lock must preserve authority boundary")

    _require_set(payload, "required_context", EXPECTED_REQUIRED_CONTEXT)
    _require_set(payload, "predictive_governance_surfaces", EXPECTED_SURFACES)
    _require_set(payload, "invariant_separations", EXPECTED_INVARIANT_SEPARATIONS)
    _require_set(payload, "allowed_predictive_actions", EXPECTED_ALLOWED_ACTIONS)
    _require_set(payload, "forbidden_predictive_actions", EXPECTED_FORBIDDEN_ACTIONS)

    _validate_inevitability_forecasting(
        _require_mapping(payload, "inevitability_forecasting")
    )
    _validate_inevitability_reinforcement(
        _require_mapping(payload, "inevitability_reinforcement_monitoring")
    )
    _validate_anticipatory_suppression(
        _require_mapping(payload, "anticipatory_suppression_analysis")
    )

    if _normalize(payload.get("required_authority_disclaimer")) != (
        EXPECTED_AUTHORITY_DISCLAIMER
    ):
        _fail("required authority disclaimer must deny future selection authority")


def _validate_inevitability_forecasting(section: dict[str, Any]) -> None:
    _require_set(section, "required_preservation", EXPECTED_FORECAST_PRESERVATION)
    _require_set(section, "forbidden_drift", EXPECTED_FORECAST_FORBIDDEN)


def _validate_inevitability_reinforcement(section: dict[str, Any]) -> None:
    _require_set(section, "required_detection", EXPECTED_REINFORCEMENT_DETECTION)
    _require_set(section, "forbidden_drift", EXPECTED_REINFORCEMENT_FORBIDDEN)


def _validate_anticipatory_suppression(section: dict[str, Any]) -> None:
    _require_set(section, "required_preservation", EXPECTED_SUPPRESSION_PRESERVATION)
    _require_set(section, "forbidden_drift", EXPECTED_SUPPRESSION_FORBIDDEN)


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


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        _fail(f"{key} must be a mapping")
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
    raise PredictiveFutureSpaceValidationError(message)


def main() -> int:
    try:
        validate()
    except PredictiveFutureSpaceValidationError as exc:
        print(f"Predictive future-space validation FAILED: {exc}")
        return 1
    print("Predictive future-space validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
