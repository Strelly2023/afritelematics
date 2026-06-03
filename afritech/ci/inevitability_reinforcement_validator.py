"""Validate inevitability reinforcement containment under predictive governance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from afritech.ci.predictive_future_space_validator import validate as validate_base_policy


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "afritech/constitution/evolution/inevitability_reinforcement_policy.yaml"

EXPECTED_FIELDS = {
    "authority_disclaimer",
    "forecast_lineage",
    "operational_influence_scope",
    "ratification_status",
    "recommendation_pressure",
    "replay_reference",
    "resource_routing_signal",
    "salience_amplification_signal",
}
EXPECTED_ALLOWED = {
    "detect_forecast_amplification",
    "expose_self_fulfilling_pressure",
    "identify_recommendation_pressure",
    "monitor_resource_concentration",
    "recommend_authority_review",
    "surface_operational_preselection_risk",
}
EXPECTED_FORBIDDEN = {
    "convert_forecast_confidence_into_operational_priority",
    "operationally_preselect_constitutional_future",
    "optimize_toward_predicted_legitimacy",
    "reinforce_prediction_as_authority",
    "route_resources_toward_predicted_future",
}
EXPECTED_DISCLAIMER = (
    "This reinforcement analysis exposes self-fulfilling prediction pressure. "
    "It does not prioritize, select, or legitimize constitutional futures."
)


class InevitabilityReinforcementValidationError(RuntimeError):
    """Raised when forecast reinforcement is allowed to select futures."""


def validate() -> None:
    validate_base_policy()
    validate_policy_payload(_load_yaml(POLICY))


def validate_policy_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.inevitability_reinforcement_policy.v1":
        _fail("inevitability reinforcement policy schema mismatch")
    if payload.get("authority") != "SELF_FULFILLING_PRESSURE_CONTAINMENT_ONLY":
        _fail(
            "inevitability reinforcement authority must be "
            "SELF_FULFILLING_PRESSURE_CONTAINMENT_ONLY"
        )
    _require_inheritance(payload)
    _require_lock(payload)
    _require_set(payload, "required_payload_fields", EXPECTED_FIELDS)
    _require_set(payload, "allowed_actions", EXPECTED_ALLOWED)
    _require_set(payload, "forbidden_drift", EXPECTED_FORBIDDEN)
    if _normalize(payload.get("required_authority_disclaimer")) != EXPECTED_DISCLAIMER:
        _fail("authority disclaimer must deny operational future selection")


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
    raise InevitabilityReinforcementValidationError(message)


def main() -> int:
    try:
        validate()
    except InevitabilityReinforcementValidationError as exc:
        print(f"Inevitability reinforcement validation FAILED: {exc}")
        return 1
    print("Inevitability reinforcement validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
