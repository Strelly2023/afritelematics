#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = ROOT / "reports/mobile/releases/2026.1.1/novaride-release-provenance.json"


def main() -> int:
    if not PROVENANCE.exists():
        raise SystemExit(f"missing provenance {PROVENANCE}")
    data = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    for app in ("rider", "driver"):
        entry = data.get(app)
        if not isinstance(entry, dict):
            raise SystemExit(f"missing {app} provenance")
        for key in ("version", "versionCode", "packageId", "apiHost", "apkSha256", "publicationUrl"):
            if not entry.get(key):
                raise SystemExit(f"missing {app}.{key}")
    print("release provenance verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())

