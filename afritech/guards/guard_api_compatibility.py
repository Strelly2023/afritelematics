"""Guard that enforces API lifecycle and compatibility lint results."""

from __future__ import annotations

import sys

from afritech.api_catalog.registry import get_api_catalog


def validate_api_compatibility() -> list[str]:
    catalog = get_api_catalog()
    summary = catalog.compatibility()
    issues = [f"{issue['domain']}:{issue['code']}:{issue['path']}" for issue in summary.get("issues", [])]
    if summary.get("status") != "PASS" and not issues:
        issues.append("compatibility_status_failed")
    return issues


def main() -> int:
    issues = validate_api_compatibility()
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("api_compatibility_guard=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
