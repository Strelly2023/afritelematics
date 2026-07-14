"""Verify deterministic SDK artifacts generated from API contracts."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afritech.api_catalog.publication import sha256
from afritech.api_catalog.registry import get_api_catalog


EXPECTED = {
    "novaride": ("typescript", "kotlin", "swift"),
    "novapay": ("python", "typescript"),
    "novaid": ("java",),
    "novatrust": ("go",),
}


def verify_generated_sdks() -> list[str]:
    catalog = get_api_catalog()
    issues: list[str] = []
    for domain, languages in EXPECTED.items():
        contract = catalog.get(domain)
        openapi_hash = sha256(catalog.openapi(domain))
        for language in languages:
            metadata_path = Path("sdk") / domain / language / "sdk-metadata.json"
            if not metadata_path.exists():
                issues.append(f"missing_sdk:{domain}:{language}")
                continue
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("contract_version") != contract.version:
                issues.append(f"contract_version_mismatch:{domain}:{language}")
            if metadata.get("openapi_hash") != openapi_hash:
                issues.append(f"openapi_hash_mismatch:{domain}:{language}")
            if metadata.get("standard_error_model") != "NovaTechErrorEnvelope":
                issues.append(f"missing_standard_error_model:{domain}:{language}")
            if metadata.get("idempotency_header") != "Idempotency-Key":
                issues.append(f"missing_idempotency_header:{domain}:{language}")
    for report in ("manifest.json", "checksums.sha256", "compatibility.json", "signatures.json"):
        if not (Path("reports/sdk") / report).exists():
            issues.append(f"missing_sdk_report:{report}")
    return issues


def main() -> int:
    issues = verify_generated_sdks()
    if issues:
        print("\n".join(issues))
        return 1
    print("generated_sdk_verification=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
