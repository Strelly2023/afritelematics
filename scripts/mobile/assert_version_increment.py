#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERSION = "2026.1.4"


def version_code(path: Path) -> int:
    match = re.search(r"versionCode\s+(\d+)", path.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"missing versionCode in {path}")
    return int(match.group(1))


def main() -> int:
    expected_codes = {
        "rider_app": 7,
        "driver_app": 7,
    }
    for app, minimum_version_code in expected_codes.items():
        app_json = json.loads((ROOT / app / "app.json").read_text(encoding="utf-8"))["expo"]
        if app_json["version"] != VERSION:
            raise SystemExit(f"{app} version {app_json['version']} != {VERSION}")
        code = version_code(ROOT / app / "android" / "app" / "build.gradle")
        if code < minimum_version_code:
            raise SystemExit(f"{app} versionCode {code} is not incremented")
    print("NovaRide mobile version increment verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
