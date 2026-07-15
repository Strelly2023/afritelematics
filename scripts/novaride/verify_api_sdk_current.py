#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "packages" / "novaride-api-sdk" / "src" / "generated"
REPORT = ROOT / "reports" / "novaride" / "deployment" / "api-sdk-verification.json"
MODULES = {"rider", "driver", "operator", "fleet", "logistics", "corporate", "transit", "safety", "diagnostics", "replay", "models"}


def main() -> int:
    present = {path.stem for path in GENERATED.glob("*.ts")}
    missing = sorted(MODULES - present)
    stale = [path.name for path in GENERATED.glob("*.ts") if "source_spec_hash:" not in path.read_text()]
    report = {
        "status": "PASS" if not missing and not stale else "FAIL",
        "generated_modules": sorted(present),
        "missing_modules": missing,
        "stale_modules": sorted(stale),
        "source": "/openapi.json",
        "live_openapi_export_verified": False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
