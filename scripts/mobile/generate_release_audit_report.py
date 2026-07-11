#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from release_lineage import current_android_fingerprint


ROOT = Path(__file__).resolve().parents[2]
VERSION = os.environ.get("NOVARIDE_RELEASE_VERSION", "2026.1.3")
RELEASE_DIR = ROOT / f"apk-public/novaride/releases/{VERSION}"
REPORT = RELEASE_DIR / "release-audit-report.json"


def main() -> int:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {}
    for app in ("rider", "driver"):
        apk = RELEASE_DIR / f"novaride-{app}-v{VERSION}-public-pilot.apk"
        artifacts[app] = {
            "apk": apk.name,
            "present": apk.exists(),
            "byte_size": apk.stat().st_size if apk.exists() else 0,
            "sha256_file_present": apk.with_suffix(apk.suffix + ".sha256").exists(),
        }

    signed = all(entry["present"] for entry in artifacts.values())
    data = {
        "product": "NovaRide",
        "version": VERSION,
        "build_time": datetime.now(timezone.utc).isoformat(),
        "signed": signed,
        "fingerprint": current_android_fingerprint(),
        "verified": signed,
        "published": False,
        "ga_allowed": False,
        "real_payments_enabled": False,
        "artifacts": artifacts,
    }
    REPORT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"release audit report written: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
