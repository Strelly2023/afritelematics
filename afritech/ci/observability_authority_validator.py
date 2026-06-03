"""Validate compatibility observability remains explanatory only."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
POLICY = (
    ROOT
    / "afritech/constitution/evolution/compatibility_observability_policy.yaml"
)
GA_WORKFLOW = ROOT / ".github/workflows/ga_plus_plus_plus.yml"


class ObservabilityAuthorityValidationError(RuntimeError):
    """Raised when observability surfaces drift into authority."""


def validate() -> None:
    payload = _load_yaml(POLICY)
    validate_policy_payload(payload)
    validate_ga_workflow(payload, GA_WORKFLOW.read_text(encoding="utf-8"))


def validate_policy_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != (
        "afritech.constitution.evolution.compatibility_observability_policy.v1"
    ):
        _fail("compatibility observability policy schema mismatch")

    if payload.get("authority") != "non_authoritative_observability_policy":
        _fail("compatibility observability policy must remain non-authoritative")

    boundary = _require_mapping(payload, "boundary")
    expected_boundary = {
        "constitution": "defines_legitimacy",
        "replay": "validates_truth",
        "validators": "enforce_governance",
        "observability": "explains_validator_derived_state",
    }
    for key, expected_value in expected_boundary.items():
        if boundary.get(key) != expected_value:
            _fail(f"boundary.{key} must be {expected_value}")

    required_scope = payload.get("required_scope")
    if required_scope != "OBSERVATION_ONLY":
        _fail("required_scope must be OBSERVATION_ONLY")

    required_forbidden = set(_require_list(payload, "required_forbidden_actions"))
    surfaces = _require_mapping(payload, "observability_surfaces")
    if not surfaces:
        _fail("observability_surfaces must not be empty")

    for surface_id, surface in sorted(surfaces.items()):
        if not isinstance(surface, dict):
            _fail(f"{surface_id} must be a mapping")
        _validate_surface(surface_id, surface, required_scope, required_forbidden)


def validate_ga_workflow(payload: dict[str, Any], workflow_text: str) -> None:
    surfaces = _require_mapping(payload, "observability_surfaces")
    for surface_id, surface in sorted(surfaces.items()):
        integration = surface.get("ga_integration")
        if integration is None:
            continue
        if not isinstance(integration, dict):
            _fail(f"{surface_id}.ga_integration must be a mapping")
        if integration.get("continue_on_error_required") is not True:
            _fail(f"{surface_id}.ga_integration must require continue-on-error")

        step_name = str(integration.get("step_name", ""))
        command = str(surface.get("command", ""))
        if not step_name:
            _fail(f"{surface_id}.ga_integration missing step_name")
        if not command:
            _fail(f"{surface_id} missing command")
        _assert_non_blocking_step(workflow_text, step_name, command)


def _validate_surface(
    surface_id: str,
    surface: dict[str, Any],
    required_scope: str,
    required_forbidden: set[str],
) -> None:
    if surface.get("authority_scope") != required_scope:
        _fail(f"{surface_id} must declare authority_scope {required_scope}")
    if surface.get("blocking") is not False:
        _fail(f"{surface_id} must be non-blocking observability")

    for key in ("path", "data_sources", "allowed_actions", "forbidden_actions"):
        if key == "path":
            if not surface.get(key):
                _fail(f"{surface_id} missing path")
        else:
            values = _require_list(surface, key, context=surface_id)
            if not values:
                _fail(f"{surface_id}.{key} must not be empty")

    forbidden_actions = set(_require_list(surface, "forbidden_actions", surface_id))
    missing = sorted(required_forbidden - forbidden_actions)
    if missing:
        _fail(f"{surface_id} missing forbidden actions: {missing}")

    disallowed_allowed = sorted(required_forbidden & set(surface["allowed_actions"]))
    if disallowed_allowed:
        _fail(f"{surface_id} allows forbidden actions: {disallowed_allowed}")


def _assert_non_blocking_step(
    workflow_text: str,
    step_name: str,
    command: str,
) -> None:
    lines = workflow_text.splitlines()
    for index, line in enumerate(lines):
        if f"- name: {step_name}" not in line:
            continue
        window = "\n".join(lines[index : index + 6])
        if "continue-on-error: true" not in window:
            _fail(f"GA step '{step_name}' must be non-blocking")
        if f"run: {command}" not in window:
            _fail(f"GA step '{step_name}' must run {command}")
        return
    _fail(f"GA workflow missing observability step '{step_name}'")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        _fail(f"missing policy: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _fail(f"{path} must be a mapping")
    return payload


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


def _require_list(
    payload: dict[str, Any],
    key: str,
    context: str | None = None,
) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        label = f"{context}.{key}" if context else key
        _fail(f"{label} must be a list")
    return value


def _fail(message: str) -> None:
    raise ObservabilityAuthorityValidationError(message)


def main() -> int:
    try:
        validate()
    except ObservabilityAuthorityValidationError as exc:
        print(f"❌ Observability authority validation FAILED: {exc}")
        return 1
    print("✅ Observability authority validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
