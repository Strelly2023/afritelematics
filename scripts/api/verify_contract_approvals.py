"""Verify governed API contract approval records."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afritech.api_catalog.registry import get_api_catalog


def validate_contract_approvals() -> list[str]:
    catalog = get_api_catalog()
    issues: list[str] = []
    for domain in catalog.domains():
        approval = catalog.approval(domain)
        if not approval.get("publishable"):
            issues.append(f"approval_not_publishable:{domain}")
        if not approval.get("adr_ids"):
            issues.append(f"approval_missing_adr:{domain}")
        if approval.get("status") != "approved":
            issues.append(f"approval_not_approved:{domain}")
    return issues


def main() -> int:
    issues = validate_contract_approvals()
    if issues:
        print("\n".join(issues))
        return 1
    print("contract_approval_verification=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
