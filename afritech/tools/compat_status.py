"""Read-only compatibility status tool for epoch and translator registries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.ci.epoch_lifecycle_validator import (
    EPOCH_LIFECYCLE_REGISTRY,
    REPLAY_TRANSLATOR_REGISTRY,
    validate,
)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must be a mapping")
    return payload


def compatibility_status() -> dict[str, Any]:
    """Return read-only compatibility health derived from registries."""

    epoch_payload = load_yaml(EPOCH_LIFECYCLE_REGISTRY)
    translator_payload = load_yaml(REPLAY_TRANSLATOR_REGISTRY)
    validation_error = None
    try:
        validate()
        lifecycle_valid = True
    except Exception as exc:
        lifecycle_valid = False
        validation_error = str(exc)

    epochs = epoch_payload.get("epochs", {})
    translators = translator_payload.get("translators", {})
    exceptions = translator_payload.get("exceptions", {})
    translator_budget = translator_payload.get("translator_budget", {})

    epoch_counts = _count_statuses(epochs)
    translator_counts = _count_statuses(translators)
    fixture_failures = _fixture_failures(translators)
    budget_violations = _budget_violations(translators, exceptions, translator_budget)

    health = "green"
    if not lifecycle_valid or fixture_failures or budget_violations:
        health = "red"
    elif translator_counts.get("DEPRECATED", 0) or epoch_counts.get("LEGACY_SUPPORTED", 0):
        health = "amber"

    return {
        "active_epochs": epoch_counts.get("ACTIVE", 0),
        "budget_violations": budget_violations,
        "deprecated_translators": translator_counts.get("DEPRECATED", 0),
        "epoch_lifecycle": "valid" if lifecycle_valid else "invalid",
        "epochs": _epoch_rows(epochs),
        "fixture_failures": fixture_failures,
        "health": health,
        "legacy_supported_epochs": epoch_counts.get("LEGACY_SUPPORTED", 0),
        "retired_epochs": epoch_counts.get("RETIRED", 0),
        "translator_count": len(translators),
        "translators": _translator_rows(translators),
        "validation_error": validation_error,
    }


def summary(status: dict[str, Any]) -> str:
    """Return human-readable compatibility status."""

    lines = [
        f"Compatibility health: {status['health']}",
        f"Epoch lifecycle: {status['epoch_lifecycle']}",
        f"Active epochs: {status['active_epochs']}",
        f"Legacy-supported epochs: {status['legacy_supported_epochs']}",
        f"Retired epochs: {status['retired_epochs']}",
        f"Translators: {status['translator_count']}",
        f"Deprecated translators: {status['deprecated_translators']}",
        f"Budget violations: {len(status['budget_violations'])}",
        f"Fixture failures: {len(status['fixture_failures'])}",
    ]
    if status["validation_error"]:
        lines.append(f"Validation error: {status['validation_error']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m afritech.tools.compat_status",
        description="Show read-only AfriTech epoch and translator compatibility status.",
    )
    parser.add_argument(
        "command",
        choices=["status"],
        help="Compatibility command to run.",
    )
    parser.add_argument(
        "--format",
        choices=["summary", "json"],
        default="summary",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    status = compatibility_status()
    if args.format == "json":
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(summary(status))
    return 0 if status["epoch_lifecycle"] == "valid" else 1


def _count_statuses(items: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items.values():
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def _epoch_rows(epochs: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for epoch_id, epoch in sorted(epochs.items()):
        if not isinstance(epoch, dict):
            continue
        rows.append(
            {
                "active_trace_policy": epoch.get("active_trace_policy"),
                "epoch": epoch_id,
                "fixture_status": (
                    epoch.get("compatibility_fixtures", {}).get("status")
                    if isinstance(epoch.get("compatibility_fixtures"), dict)
                    else None
                ),
                "interface_versions": epoch.get("interface_versions", {}),
                "retirement_eligible": (
                    epoch.get("retirement", {}).get("eligible")
                    if isinstance(epoch.get("retirement"), dict)
                    else None
                ),
                "status": epoch.get("status"),
            }
        )
    return rows


def _translator_rows(translators: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for translator_id, translator in sorted(translators.items()):
        if not isinstance(translator, dict):
            continue
        rows.append(
            {
                "compatibility_class": translator.get("compatibility_class"),
                "fixture_status": translator.get("fixture_status"),
                "owner": translator.get("owner"),
                "retirement_path": translator.get("retirement_path"),
                "source_epoch": translator.get("source_epoch"),
                "status": translator.get("status"),
                "target_interface": translator.get("target_interface"),
                "translator": translator_id,
            }
        )
    return rows


def _fixture_failures(translators: dict[str, Any]) -> list[dict[str, str]]:
    failures = []
    for translator_id, translator in sorted(translators.items()):
        if not isinstance(translator, dict):
            continue
        if translator.get("status") in {"ACTIVE", "STABLE"} and translator.get(
            "fixture_status"
        ) != "PASSING":
            failures.append(
                {
                    "translator": translator_id,
                    "fixture_status": str(translator.get("fixture_status")),
                }
            )
    return failures


def _budget_violations(
    translators: dict[str, Any],
    exceptions: dict[str, Any],
    translator_budget: dict[str, Any],
) -> list[dict[str, Any]]:
    max_per_pair = int(
        translator_budget.get("default_max_per_source_epoch_per_interface", 1)
    )
    by_pair: dict[tuple[str, str], list[str]] = {}
    for translator_id, translator in sorted(translators.items()):
        if not isinstance(translator, dict):
            continue
        pair = (
            str(translator.get("source_epoch")),
            str(translator.get("target_interface")),
        )
        by_pair.setdefault(pair, []).append(translator_id)

    violations = []
    for pair, ids in sorted(by_pair.items()):
        if len(ids) <= max_per_pair:
            continue
        if _has_exception(exceptions, pair):
            continue
        violations.append(
            {
                "source_epoch": pair[0],
                "target_interface": pair[1],
                "translators": ids,
            }
        )
    return violations


def _has_exception(exceptions: dict[str, Any], pair: tuple[str, str]) -> bool:
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


if __name__ == "__main__":
    sys.exit(main())
