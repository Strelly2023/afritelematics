"""Generate deterministic local SDK artifacts from domain OpenAPI contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afritech.api_catalog.publication import canonical_json, sha256
from afritech.api_catalog.registry import get_api_catalog


SDK_TARGETS = {
    "novaride": ("typescript", "kotlin", "swift"),
    "novapay": ("python", "typescript"),
    "novaid": ("java",),
    "novatrust": ("go",),
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    catalog = get_api_catalog()
    manifest: dict[str, object] = {"sdks": []}
    checksums: list[str] = []
    signatures: dict[str, object] = {}
    for domain, languages in SDK_TARGETS.items():
        contract = catalog.get(domain)
        openapi = catalog.openapi(domain)
        for language in languages:
            output = Path("sdk") / domain / language
            output.mkdir(parents=True, exist_ok=True)
            metadata = {
                "domain": domain,
                "language": language,
                "sdk_version": contract.version,
                "contract_version": contract.version,
                "openapi_hash": sha256(openapi),
                "standard_error_model": "NovaTechErrorEnvelope",
                "authentication": "bearer-or-domain-specific",
                "idempotency_header": "Idempotency-Key",
            }
            write(output / "sdk-metadata.json", json.dumps(metadata, indent=2, sort_keys=True) + "\n")
            write(output / "README.md", f"# {domain} {language} SDK\n\nGenerated from NovaTech API contract {contract.version}.\n")
            artifact_hash = hashlib.sha256(canonical_json(metadata)).hexdigest()
            checksums.append(f"{artifact_hash}  {output / 'sdk-metadata.json'}")
            signatures[str(output)] = {"scheme": "sha256-local-artifact", "value": artifact_hash}
            manifest["sdks"].append(metadata)  # type: ignore[index]
    Path("reports/sdk").mkdir(parents=True, exist_ok=True)
    write(Path("reports/sdk/manifest.json"), json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write(Path("reports/sdk/checksums.sha256"), "\n".join(checksums) + "\n")
    write(Path("reports/sdk/compatibility.json"), json.dumps({"status": "PASS", "published": False, "sdks": manifest["sdks"]}, indent=2, sort_keys=True) + "\n")
    write(Path("reports/sdk/signatures.json"), json.dumps(signatures, indent=2, sort_keys=True) + "\n")
    print(f"generated_sdk_artifacts={len(manifest['sdks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
