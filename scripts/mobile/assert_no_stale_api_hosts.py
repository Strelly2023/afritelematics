#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [
    ROOT / "driver_app",
    ROOT / "rider_app",
    ROOT / "afriride_system" / "mobile",
    ROOT / "packages" / "novatech-platform-sdk",
]
STALE_PATTERNS = [
    re.compile(r"http://localhost", re.I),
    re.compile(r"http://127\.0\.0\.1", re.I),
    re.compile(r"http://10\.\d+\.\d+\.\d+", re.I),
    re.compile(r"http://192\.168\.\d+\.\d+", re.I),
    re.compile(r"https://your-backend-url", re.I),
]
IGNORED_DIRS = {"node_modules", "build", ".gradle", ".expo", "dist", "coverage"}
IGNORED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".jar", ".keystore", ".apk", ".md", ".log"}


def main() -> int:
    failures: list[str] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in IGNORED_DIRS for part in path.parts) or path.suffix in IGNORED_SUFFIXES:
                continue
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in STALE_PATTERNS:
                if pattern.search(text):
                    failures.append(str(path.relative_to(ROOT)))
                    break
    if failures:
        raise SystemExit("stale API hosts found: " + ", ".join(sorted(failures)))
    print("no stale API hosts found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
