"""Validate inevitability forecasting containment under predictive governance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from afritech.ci.predictive_future_space_validator import validate as validate_base_policy


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "afritech/constitution/evolution/inevitability_forecasting_policy.yaml"

EXPECTED_FIELDS = {
    "authority_disclaimer",
    "forecast_confidence",
    "forecast_uncertainty",
    "future_space_scope",
    "model_version",
    "probability_classification",
    "ratification_status",
    "replay_reference",
}
EXPECTED_ALLOWED = {
    "compare_future_scenarios",
    "describe_likelihood",
    "expose_forecast_pressure",
    "identify_probability_concentration",
    "model_governance_trajectories",
    "recommend_authority_review",
}
EXPECTED_FORBIDDEN = {
    "collapse_future_plurality_into_confidence",
    "convert_probability_into_legitimacy",
    "forecast_confidence_as_authority",
    "pre_ratify_constitutional_future",
    "treat_likely_future_as_destiny",
}
EXPECTED_DISCLAIMER = (
    "This inevitability forecast describes likelihood and uncertainty. It does "
    "not select, ratify, or legitimize constitutional futures."
)


class InevitabilityForecastingValidationError(RuntimeError):
    """Raised when forecast probability is allowed to become authority."""


def validate() -> None:
    validate_base_policy()
    validate_policy_payload(_load_yaml(POLICY))


def validate_policy_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.inevitability_forecasting_policy.v1":
        _fail("inevitability forecasting policy schema mismatch")
    if payload.get("authority") != "PROBABILITY_CONTAINMENT_ONLY":
        _fail("inevitability forecasting authority must be PROBABILITY_CONTAINMENT_ONLY")
    _require_inheritance(payload)
    _require_lock(payload)
    _require_set(payload, "required_payload_fields", EXPECTED_FIELDS)
    _require_set(payload, "allowed_actions", EXPECTED_ALLOWED)
    _require_set(payload, "forbidden_drift", EXPECTED_FORBIDDEN)
    if _normalize(payload.get("required_authority_disclaimer")) != EXPECTED_DISCLAIMER:
        _fail("authority disclaimer must deny forecast legitimacy")


def _require_inheritance(payload: dict[str, Any]) -> None:
    if payload.get("inherits_policy") != "afritech.predictive_future_space_policy.v1":
        _fail("specialized predictive validator must inherit future-space policy")


def _require_lock(payload: dict[str, Any]) -> None:
    lock = str(payload.get("lock", ""))
    for phrase in ("Prediction informs.", "Risk informs.", "Authority decides."):
        if phrase not in lock:
            _fail("specialized predictive lock must preserve shared authority law")


def _require_set(payload: dict[str, Any], key: str, expected: set[str]) -> None:
    value = payload.get(key)
    if not isinstance(value, list):
        _fail(f"{key} must be a list")
    actual = set(value)
    if actual != expected:
        _fail(f"{key} mismatch: expected {sorted(expected)}, got {sorted(actual)}")


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
    raise InevitabilityForecastingValidationError(message)


def main() -> int:
    try:
        validate()
    except InevitabilityForecastingValidationError as exc:
        print(f"Inevitability forecasting validation FAILED: {exc}")
        return 1
    print("Inevitability forecasting validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
