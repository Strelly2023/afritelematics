"""Generate objective NovaRide implementation-gap evidence from traceability."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from afritech.ci.novaride_mobile_feature_gate import DEFAULT_MATRICES, ROOT


@dataclass(frozen=True)
class BindingRule:
    field: str
    report_name: str
    path_backed: bool = True


RULES = (
    BindingRule("source_file", "missing-source-bindings"),
    BindingRule("api_endpoint", "missing-api-bindings", path_backed=False),
    BindingRule("unit_test", "missing-test-bindings"),
    BindingRule("integration_test", "missing-test-bindings"),
    BindingRule("mobile_e2e_test", "missing-test-bindings"),
    BindingRule("cross_application_e2e_test", "missing-test-bindings"),
    BindingRule("build_artifact", "missing-release-evidence"),
    BindingRule("evidence_file", "missing-release-evidence"),
    BindingRule("release_commit", "missing-release-evidence", path_backed=False),
)


def _load(paths: tuple[Path, ...]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in paths:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        requirements = payload.get("requirements", [])
        if not isinstance(requirements, list):
            raise ValueError(f"{path}: requirements must be a list")
        items.extend(requirements)
    return items


def _is_placeholder(value: Any) -> bool:
    return (
        value is None
        or not isinstance(value, str)
        or not value.strip()
        or value.startswith("pending/")
        or value in {"not-applicable", "TBD", "TODO"}
    )


def _api_inventory() -> str:
    roots = (ROOT / "afritech/api", ROOT / "afritech/novaride_runtime")
    chunks: list[str] = []
    for directory in roots:
        for path in directory.rglob("*.py"):
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def _api_is_bound(endpoint: str, inventory: str) -> bool:
    # Dynamic identifiers are removed so route decorators and client contracts
    # can be matched without accepting a mere traceability declaration.
    prefix = endpoint.split("{", 1)[0].rstrip("/")
    candidates = {prefix}
    if prefix.startswith("/api"):
        candidates.add(prefix.removeprefix("/api"))
    return any(candidate and candidate in inventory for candidate in candidates)


def build_report(paths: tuple[Path, ...] = DEFAULT_MATRICES) -> dict[str, Any]:
    requirements = _load(paths)
    api_inventory = _api_inventory()
    missing: dict[str, list[dict[str, str]]] = {
        rule.report_name: [] for rule in RULES
    }
    for item in requirements:
        for rule in RULES:
            value = item.get(rule.field)
            reason = ""
            if _is_placeholder(value):
                reason = "missing_or_placeholder"
            elif rule.field == "api_endpoint" and not _api_is_bound(
                str(value), api_inventory
            ):
                reason = "route_not_found_in_backend"
            elif rule.path_backed and not (ROOT / str(value)).is_file():
                reason = "path_not_found"
            if reason:
                missing[rule.report_name].append(
                    {
                        "id": str(item.get("id", "")),
                        "application": str(item.get("application", "")),
                        "field": rule.field,
                        "value": "" if value is None else str(value),
                        "reason": reason,
                    }
                )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_matrices": [str(path.relative_to(ROOT)) for path in paths],
        "requirement_count": len(requirements),
        "application_counts": dict(
            sorted(Counter(str(item.get("application")) for item in requirements).items())
        ),
        "state_counts": dict(
            sorted(Counter(str(item.get("state")) for item in requirements).items())
        ),
        "requirements": requirements,
        "missing": missing,
    }


def _markdown_summary(report: dict[str, Any]) -> str:
    lines = [
        "# NovaRide current mandatory feature state",
        "",
        f"- Requirements: {report['requirement_count']}",
        f"- Generated: `{report['generated_at']}`",
        "",
        "## Applications",
        "",
    ]
    lines.extend(
        f"- {name}: {count}" for name, count in report["application_counts"].items()
    )
    lines.extend(["", "## Certification states", ""])
    lines.extend(f"- {name}: {count}" for name, count in report["state_counts"].items())
    lines.extend(["", "## Missing bindings", ""])
    lines.extend(
        f"- {name}: {len(items)}" for name, items in report["missing"].items()
    )
    lines.extend(
        [
            "",
            "This report is inventory evidence only. It does not promote any feature",
            "state and does not authorize pilot, PRR, production, or GA.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reports(output: Path, report: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    current = {key: value for key, value in report.items() if key != "missing"}
    (output / "current-feature-state.json").write_text(
        json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "current-feature-state.md").write_text(
        _markdown_summary(report), encoding="utf-8"
    )
    for name, items in report["missing"].items():
        (output / f"{name}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "generated_at": report["generated_at"],
                    "requirement_count": report["requirement_count"],
                    "missing_count": len(items),
                    "items": items,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/novaride/implementation",
    )
    args = parser.parse_args(argv)
    report = build_report()
    write_reports(args.output, report)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "requirement_count": report["requirement_count"],
                "state_counts": report["state_counts"],
                "missing_counts": {
                    key: len(value) for key, value in report["missing"].items()
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
