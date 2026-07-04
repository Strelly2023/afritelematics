"""AI-assisted change impact analysis for CI selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEPENDENCY_GRAPH_PATH = ROOT / "ci" / "impact" / "dependency_graph.yml"
TEST_SUITE_REGISTRY_PATH = ROOT / "ci" / "test_suites.yml"
ARTIFACT_DIR = ROOT / "ci_artifacts"
PLAN_PATH = ARTIFACT_DIR / "impact_plan.json"
SUMMARY_PATH = ARTIFACT_DIR / "impact_summary.md"

MANDATORY_GOVERNANCE_CHECKS = (
    "four_gate",
    "runtime_boundary",
    "secret_scan",
    "git_diff_check",
)

FULL_VALIDATION_SUITE_ORDER = (
    "governance",
    "trust",
    "payments",
    "identity",
    "novapay",
    "novaride",
    "rider_app",
    "driver_app",
    "dashboard",
    "android",
    "ios",
    "security",
    "performance",
    "docs",
    "release_certification",
    "core_api",
)


@dataclass
class ImpactPlan:
    changed_files: list[str] = field(default_factory=list)
    affected_modules: list[str] = field(default_factory=list)
    required_test_suites: list[str] = field(default_factory=list)
    skipped_test_suites: list[str] = field(default_factory=list)
    required_builds: list[str] = field(default_factory=list)
    required_governance_checks: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)
    full_validation_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": self.changed_files,
            "affected_modules": self.affected_modules,
            "required_test_suites": self.required_test_suites,
            "skipped_test_suites": self.skipped_test_suites,
            "required_builds": self.required_builds,
            "required_governance_checks": self.required_governance_checks,
            "confidence": round(self.confidence, 4),
            "reasons": self.reasons,
            "full_validation_required": self.full_validation_required,
        }


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"invalid_yaml:{path}")
    return payload


def _changed_files(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _match_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def _suite_registry() -> dict[str, dict[str, Any]]:
    payload = _load_yaml(TEST_SUITE_REGISTRY_PATH)
    suites = payload.get("suites", {})
    if not isinstance(suites, dict):
        raise ValueError("invalid_suite_registry")
    return suites


def _dependency_graph() -> dict[str, Any]:
    payload = _load_yaml(DEPENDENCY_GRAPH_PATH)
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("invalid_dependency_graph")
    payload["rules"] = rules
    payload["force_full_patterns"] = list(payload.get("force_full_patterns", []))
    return payload


def analyze_changed_files(changed_files: list[str]) -> ImpactPlan:
    graph = _dependency_graph()
    suites = _suite_registry()
    plan = ImpactPlan(changed_files=sorted(dict.fromkeys(changed_files)))

    selected_suites: set[str] = set()
    selected_builds: set[str] = set()
    selected_checks: set[str] = set(MANDATORY_GOVERNANCE_CHECKS)
    affected_modules: set[str] = set()
    reasons: list[str] = []
    confidence = 0.0
    full_validation_required = False

    for path in plan.changed_files:
        if _match_any(path, graph["force_full_patterns"]):
            full_validation_required = True
            reasons.append(f"{path} triggers full validation")
            confidence = max(confidence, 1.0)

        matched_rule = False
        for rule in graph["rules"]:
            if fnmatch(path, rule["match"]):
                matched_rule = True
                affected_modules.update(rule.get("modules", []))
                selected_suites.update(rule.get("suites", []))
                selected_builds.update(rule.get("builds", []))
                selected_checks.update(rule.get("governance_checks", []))
                rule_reason = str(rule.get("reason") or f"{path} matched {rule['match']}")
                reasons.append(rule_reason)
                confidence = max(confidence, float(rule.get("confidence", 0.85)))
        if not matched_rule:
            reasons.append(f"{path} had no explicit rule; defaulting to core governance checks")
            selected_suites.add("core_api")
            confidence = max(confidence, 0.7)

    if full_validation_required:
        selected_suites = set(suites.keys())
        selected_builds = {
            build
            for suite in suites.values()
            for build in suite.get("builds", [])
        }
        selected_checks.update(
            check
            for suite in suites.values()
            for check in suite.get("governance_checks", [])
        )
    else:
        for suite_name in list(selected_suites):
            suite = suites.get(suite_name, {})
            selected_builds.update(suite.get("builds", []))
            selected_checks.update(suite.get("governance_checks", []))

    skipped_suites = [name for name in FULL_VALIDATION_SUITE_ORDER if name not in selected_suites]
    selected_suites_ordered = [name for name in FULL_VALIDATION_SUITE_ORDER if name in selected_suites]

    plan.affected_modules = sorted(affected_modules)
    plan.required_test_suites = selected_suites_ordered
    plan.skipped_test_suites = skipped_suites
    plan.required_builds = sorted(selected_builds)
    plan.required_governance_checks = sorted(dict.fromkeys(selected_checks))
    plan.confidence = min(0.99, confidence if plan.changed_files else 1.0)
    plan.reasons = reasons or ["No changed files detected; defaulting to governance-only verification."]
    plan.full_validation_required = full_validation_required
    return plan


def write_impact_artifacts(plan: ImpactPlan) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    PLAN_PATH.write_text(json.dumps(plan.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    SUMMARY_PATH.write_text(render_summary(plan), encoding="utf-8")


def render_summary(plan: ImpactPlan) -> str:
    lines = [
        "# CI Impact Summary",
        "",
        f"- Confidence: `{plan.confidence:.2f}`",
        f"- Full validation required: `{plan.full_validation_required}`",
        "",
        "## Changed files",
        "",
    ]
    lines.extend(f"- `{path}`" for path in plan.changed_files or ["<none>"])
    lines.extend(["", "## Affected modules", ""])
    lines.extend(f"- `{module}`" for module in plan.affected_modules or ["<none>"])
    lines.extend(["", "## Selected suites", ""])
    lines.extend(f"- `{suite}`" for suite in plan.required_test_suites or ["<none>"])
    lines.extend(["", "## Skipped suites", ""])
    lines.extend(f"- `{suite}`" for suite in plan.skipped_test_suites or ["<none>"])
    lines.extend(["", "## Governance checks", ""])
    lines.extend(f"- `{check}`" for check in plan.required_governance_checks or ["<none>"])
    lines.extend(["", "## Reasons", ""])
    lines.extend(f"- {reason}" for reason in plan.reasons or ["<none>"])
    return "\n".join(lines) + "\n"


def analyze(base: str, head: str) -> ImpactPlan:
    changed_files = _changed_files(base, head)
    plan = analyze_changed_files(changed_files)
    write_impact_artifacts(plan)
    return plan


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Analyze CI impact and write plan artifacts.")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--json", action="store_true", help="Print JSON plan to stdout.")
    args = parser.parse_args(argv)

    plan = analyze(args.base, args.head)
    if args.json:
        print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_summary(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
