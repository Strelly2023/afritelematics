"""Validate anticipatory suppression containment under predictive governance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from afritech.ci.predictive_future_space_validator import validate as validate_base_policy


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "afritech/constitution/evolution/anticipatory_suppression_policy.yaml"

EXPECTED_FIELDS = {
    "admissible_future_space",
    "authority_disclaimer",
    "divergence_visibility",
    "future_space_scope",
    "instability_classification",
    "ratification_status",
    "replay_reference",
    "uncertainty_disclosure",
}
EXPECTED_ALLOWED = {
    "compare_alternative_futures",
    "expose_instability_risk",
    "identify_preventive_closure_pressure",
    "preserve_authorized_divergence_visibility",
    "recommend_authority_review",
    "surface_uncertainty",
}
EXPECTED_FORBIDDEN = {
    "close_admissible_future_space",
    "convert_risk_into_exclusion",
    "suppress_authorized_divergence",
    "treat_instability_as_illegitimacy",
    "treat_uncertainty_as_inadmissibility",
}
EXPECTED_DISCLAIMER = (
    "This anticipatory analysis warns about instability and uncertainty. It "
    "does not suppress, close, or delegitimize admissible constitutional futures."
)


class AnticipatorySuppressionValidationError(RuntimeError):
    """Raised when risk analysis is allowed to close future-space."""


def validate() -> None:
    validate_base_policy()
    validate_policy_payload(_load_yaml(POLICY))


def validate_policy_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.anticipatory_suppression_policy.v1":
        _fail("anticipatory suppression policy schema mismatch")
    if payload.get("authority") != "PREVENTIVE_CLOSURE_CONTAINMENT_ONLY":
        _fail(
            "anticipatory suppression authority must be "
            "PREVENTIVE_CLOSURE_CONTAINMENT_ONLY"
        )
    _require_inheritance(payload)
    _require_lock(payload)
    _require_set(payload, "required_payload_fields", EXPECTED_FIELDS)
    _require_set(payload, "allowed_actions", EXPECTED_ALLOWED)
    _require_set(payload, "forbidden_drift", EXPECTED_FORBIDDEN)
    if _normalize(payload.get("required_authority_disclaimer")) != EXPECTED_DISCLAIMER:
        _fail("authority disclaimer must deny preventive future closure")


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
    raise AnticipatorySuppressionValidationError(message)


def main() -> int:
    try:
        validate()
    except AnticipatorySuppressionValidationError as exc:
        print(f"Anticipatory suppression validation FAILED: {exc}")
        return 1
    print("Anticipatory suppression validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
