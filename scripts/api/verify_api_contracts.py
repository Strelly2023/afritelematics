"""Verify generated API catalog, governance, compatibility, and publications."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afritech.api_catalog.registry import get_api_catalog
from afritech.api_catalog.signing import verify_signed_publication
from afritech.guards.guard_api_catalog import validate_api_catalog
from afritech.guards.guard_api_breaking_changes import validate_breaking_changes
from afritech.guards.guard_api_compatibility import validate_api_compatibility
from afritech.guards.guard_openapi_governance import validate_openapi_governance
from scripts.api.verify_contract_approvals import validate_contract_approvals


def main() -> int:
    catalog = get_api_catalog()
    issues: list[str] = []
    issues.extend(validate_api_catalog())
    issues.extend(validate_openapi_governance())
    issues.extend(validate_api_compatibility())
    issues.extend(validate_breaking_changes())
    issues.extend(validate_contract_approvals())
    for domain in catalog.domains():
        publication = catalog.publication(domain)
        if not str(publication.get("openapi_hash", "")).startswith("sha256:"):
            issues.append(f"missing_openapi_hash:{domain}")
        if not publication.get("signature", {}).get("value"):
            issues.append(f"missing_signature:{domain}")
        if not verify_signed_publication(publication):
            issues.append(f"invalid_signature:{domain}")
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print(f"api_contract_verification=PASS domains={len(catalog.domains())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
