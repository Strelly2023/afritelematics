"""Execute the selected CI suites from an impact plan."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
TEST_SUITE_REGISTRY_PATH = ROOT / "ci" / "test_suites.yml"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"invalid_yaml:{path}")
    return payload


def _suite_registry() -> dict[str, dict[str, Any]]:
    payload = _load_yaml(TEST_SUITE_REGISTRY_PATH)
    suites = payload.get("suites", {})
    if not isinstance(suites, dict):
        raise ValueError("invalid_suite_registry")
    return suites


def _load_plan(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("invalid_plan")
    return payload


def run_selected_tests(plan_path: Path, *, dry_run: bool = False) -> int:
    plan = _load_plan(plan_path)
    suites = _suite_registry()
    selected = list(plan.get("required_test_suites", []))
    if plan.get("full_validation_required"):
        selected = list(suites.keys())

    exit_code = 0
    for suite_name in selected:
        suite = suites.get(suite_name)
        if suite is None:
            print(f"[skip] unknown suite {suite_name}")
            continue
        command = str(suite.get("command", "")).strip()
        if not command:
            print(f"[skip] suite {suite_name} has no command")
            continue
        if suite.get("parallel_safe", False) and command.startswith("python3 -m pytest") and " -n " not in command:
            command = command.replace("python3 -m pytest", "python3 -m pytest -n auto", 1)
        print(f"[run] {suite_name}: {command}")
        if dry_run:
            continue
        completed = subprocess.run(command, cwd=ROOT, shell=True, env=os.environ.copy())
        if completed.returncode != 0:
            exit_code = completed.returncode
            break
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the impacted CI suites from an impact plan.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    return run_selected_tests(Path(args.plan), dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
