"""Validate epoch and replay translator lifecycle registries.

This validator enforces compatibility containment metadata. It does not define
epoch semantics or replay truth.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
EPOCH_LIFECYCLE_REGISTRY = (
    ROOT / "afritech/constitution/evolution/epoch_lifecycle_registry.yaml"
)
REPLAY_TRANSLATOR_REGISTRY = (
    ROOT / "afritech/constitution/evolution/replay_translator_registry.yaml"
)


class EpochLifecycleValidationError(RuntimeError):
    """Raised when epoch lifecycle metadata is invalid."""


def validate() -> None:
    """Validate lifecycle registries from disk."""

    epoch_payload = _load_yaml(EPOCH_LIFECYCLE_REGISTRY)
    translator_payload = _load_yaml(REPLAY_TRANSLATOR_REGISTRY)
    validate_epoch_lifecycle_payload(epoch_payload)
    validate_translator_registry_payload(translator_payload)


def validate_epoch_lifecycle_payload(payload: dict[str, Any]) -> None:
    """Validate epoch lifecycle registry shape."""

    allowed = _required_set(payload, "allowed_statuses")
    required_interfaces = _required_set(payload, "required_interface_versions")
    epochs = payload.get("epochs")
    if not isinstance(epochs, dict) or not epochs:
        _fail("epoch lifecycle registry must define epochs")

    for epoch_id, epoch in epochs.items():
        if not isinstance(epoch, dict):
            _fail(f"{epoch_id} must be a mapping")
        status = epoch.get("status")
        if status not in allowed:
            _fail(f"{epoch_id} has invalid status {status!r}")

        interface_versions = epoch.get("interface_versions")
        if not isinstance(interface_versions, dict):
            _fail(f"{epoch_id} must define interface_versions")
        missing = required_interfaces - set(interface_versions)
        if missing:
            _fail(f"{epoch_id} missing interface versions: {sorted(missing)}")
        for interface, version in interface_versions.items():
            if not isinstance(version, str) or not version.startswith(f"{interface}.v"):
                _fail(f"{epoch_id} has invalid {interface} version {version!r}")

        fixtures = epoch.get("compatibility_fixtures")
        if not isinstance(fixtures, dict):
            _fail(f"{epoch_id} must define compatibility_fixtures")
        if not fixtures.get("status"):
            _fail(f"{epoch_id} compatibility_fixtures missing status")

        retirement = epoch.get("retirement")
        if not isinstance(retirement, dict) or "eligible" not in retirement:
            _fail(f"{epoch_id} must define retirement.eligible")

        if status == "RETIRED" and retirement.get("eligible") is not True:
            _fail(f"{epoch_id} is RETIRED but retirement.eligible is not true")


def validate_translator_registry_payload(payload: dict[str, Any]) -> None:
    """Validate replay translator lifecycle registry shape and budget."""

    allowed = _required_set(payload, "allowed_statuses")
    required_fields = _required_set(payload, "required_fields")
    budget = payload.get("translator_budget")
    if not isinstance(budget, dict):
        _fail("translator registry must define translator_budget")
    max_per_pair = int(budget.get("default_max_per_source_epoch_per_interface", 1))

    translators = payload.get("translators")
    if not isinstance(translators, dict):
        _fail("translator registry must define translators")
    exceptions = payload.get("exceptions", {})
    if not isinstance(exceptions, dict):
        _fail("translator registry exceptions must be a mapping")

    by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
    for translator_id, translator in translators.items():
        if not isinstance(translator, dict):
            _fail(f"{translator_id} must be a mapping")

        missing = required_fields - set(translator)
        if missing:
            _fail(f"{translator_id} missing required fields: {sorted(missing)}")

        status = translator.get("status")
        if status not in allowed:
            _fail(f"{translator_id} has invalid status {status!r}")

        source_epoch = translator.get("source_epoch")
        target_interface = translator.get("target_interface")
        if not isinstance(source_epoch, str) or not source_epoch:
            _fail(f"{translator_id} source_epoch must be a non-empty string")
        if not isinstance(target_interface, str) or not target_interface:
            _fail(f"{translator_id} target_interface must be a non-empty string")

        fixture_status = translator.get("fixture_status")
        if status in {"ACTIVE", "STABLE"} and fixture_status != "PASSING":
            _fail(f"{translator_id} active translator fixtures must be PASSING")

        retirement_path = translator.get("retirement_path")
        if not retirement_path:
            _fail(f"{translator_id} must define retirement_path")

        by_pair[(source_epoch, target_interface)].append(translator_id)

    for pair, ids in by_pair.items():
        if len(ids) <= max_per_pair:
            continue
        if not _has_budget_exception(exceptions, pair):
            _fail(
                "translator budget exceeded for "
                f"{pair[0]} -> {pair[1]}: {sorted(ids)}"
            )


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        _fail(f"missing file: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _fail(f"{path} must be a mapping")
    return payload


def _required_set(payload: dict[str, Any], key: str) -> set[str]:
    values = payload.get(key)
    if not isinstance(values, list) or not values:
        _fail(f"registry must define non-empty {key}")
    return {str(value) for value in values}


def _has_budget_exception(
    exceptions: dict[str, Any],
    pair: tuple[str, str],
) -> bool:
    for exception in exceptions.values():
        if not isinstance(exception, dict):
            continue
        if (
            exception.get("source_epoch") == pair[0]
            and exception.get("target_interface") == pair[1]
            and exception.get("approved") is True
        ):
            return True
    return False


def _fail(message: str) -> None:
    raise EpochLifecycleValidationError(message)


def main() -> int:
    try:
        validate()
    except Exception as exc:
        print(f"❌ Epoch lifecycle validation FAILED: {exc}", file=sys.stderr)
        return 1
    print("✅ Epoch lifecycle validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
