"""Guard that verifies the federated API catalog is complete."""

from __future__ import annotations

import sys

from afritech.api_catalog.registry import get_api_catalog


REQUIRED_DOMAINS = {
    "platform",
    "novaride",
    "novapay",
    "novaid",
    "novatrust",
    "novaprogramming",
    "operations",
    "public-verification",
    "partner",
}


def validate_api_catalog() -> list[str]:
    catalog = get_api_catalog()
    domains = set(catalog.domains())
    issues: list[str] = []
    missing = sorted(REQUIRED_DOMAINS - domains)
    if missing:
        issues.append(f"missing_domains:{','.join(missing)}")
    for contract in catalog.contracts:
        if not contract.owner:
            issues.append(f"missing_owner:{contract.domain}")
        if not contract.version:
            issues.append(f"missing_version:{contract.domain}")
        if not contract.supported_until:
            issues.append(f"missing_supported_until:{contract.domain}")
        if not contract.endpoints:
            issues.append(f"missing_endpoints:{contract.domain}")
    return issues


def main() -> int:
    issues = validate_api_catalog()
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("api_catalog_guard=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
