"""Generate domain OpenAPI contracts and signed publication metadata."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afritech.api_catalog.publication import canonical_json
from afritech.api_catalog.registry import get_api_catalog


OUTPUT_DIR = Path("reports/api-contracts")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_bytes(canonical_json(payload))
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    catalog = get_api_catalog()
    manifest = catalog.list_contracts()
    write_json(OUTPUT_DIR / "catalog.json", manifest)
    for domain in catalog.domains():
        write_json(OUTPUT_DIR / f"{domain}.openapi.json", catalog.openapi(domain))
        write_json(OUTPUT_DIR / f"{domain}.publication.json", catalog.publication(domain))
    print(f"generated_api_contracts={len(catalog.domains())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
