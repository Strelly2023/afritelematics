"""Compare generated contracts with the last published contract baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from afritech.api_catalog.breaking_changes import detect_breaking_changes
from afritech.api_catalog.metrics import record_breaking_change
from afritech.api_catalog.registry import get_api_catalog


BASELINE_DIR = Path("contracts/api/baselines")


def validate_breaking_changes() -> list[str]:
    issues: list[str] = []
    catalog = get_api_catalog()
    for contract in catalog.contracts:
        if contract.maturity != "stable":
            continue
        baseline_path = BASELINE_DIR / contract.domain / "latest.openapi.json"
        if not baseline_path.exists():
            issues.append(f"missing_baseline:{contract.domain}")
            continue
        previous = json.loads(baseline_path.read_text(encoding="utf-8"))
        current = catalog.openapi(contract.domain)
        for change in detect_breaking_changes(previous, current):
            record_breaking_change(domain=contract.domain)
            issues.append(f"{contract.domain}:{change.code}:{change.location}")
    return issues


def main() -> int:
    issues = validate_breaking_changes()
    if issues:
        print("\n".join(issues))
        return 1
    print("api_breaking_change_guard=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
