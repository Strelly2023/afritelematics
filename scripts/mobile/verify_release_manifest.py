#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from release_lineage import current_android_fingerprint


ROOT = Path(__file__).resolve().parents[2]
VERSION = "2026.1.3"
RELEASE_DIR = ROOT / f"apk-public/novaride/releases/{VERSION}"
MANIFEST = RELEASE_DIR / "release-manifest.json"


def main() -> int:
    if not MANIFEST.exists():
        raise SystemExit(f"missing release manifest: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("release") != VERSION:
        raise SystemExit(f"release manifest version mismatch: {data.get('release')}")
    if data.get("ga_allowed") is not False:
        raise SystemExit("release manifest must keep ga_allowed=false")
    if data.get("real_payments_enabled") is not False:
        raise SystemExit("release manifest must keep real_payments_enabled=false")

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict):
        raise SystemExit("release manifest missing artifacts")
    for app in ("rider", "driver"):
        entry = artifacts.get(app)
        if not isinstance(entry, dict):
            raise SystemExit(f"release manifest missing artifact: {app}")
        for key in ("file", "sha256", "byte_size"):
            if not entry.get(key):
                raise SystemExit(f"release manifest missing {app}.{key}")

    fingerprint = current_android_fingerprint()
    for path in [
        ROOT / "docs/mobile/release/novaride_rider_v2026.1.3_manifest.json",
        ROOT / "docs/mobile/release/novaride_driver_v2026.1.3_manifest.json",
    ]:
        text = path.read_text(encoding="utf-8").lower()
        if "pending-release-build" in text:
            continue
        if fingerprint not in text.replace(":", "").replace(" ", ""):
            raise SystemExit(f"manifest does not contain release fingerprint: {path}")

    print("release manifest verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
