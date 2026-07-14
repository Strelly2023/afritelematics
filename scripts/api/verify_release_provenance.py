"""Verify API contract publication provenance and signatures."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afritech.api_catalog.registry import get_api_catalog
from afritech.api_catalog.signing import verify_signed_publication


def validate_release_provenance() -> list[str]:
    catalog = get_api_catalog()
    issues: list[str] = []
    for domain in catalog.domains():
        publication = catalog.publication(domain)
        provenance = publication.get("provenance", {})
        for field in ("domain", "contract_version", "release_id", "published_at"):
            if not provenance.get(field):
                issues.append(f"missing_provenance:{domain}:{field}")
        if not verify_signed_publication(publication):
            issues.append(f"invalid_signature:{domain}")
    return issues


def main() -> int:
    issues = validate_release_provenance()
    if issues:
        print("\n".join(issues))
        return 1
    print("release_provenance_verification=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
