#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    if os.environ.get("ALLOW_DIRTY_RELEASE_TREE") == "1":
        print("dirty release tree allowed by ALLOW_DIRTY_RELEASE_TREE=1")
        return 0
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    if status.strip():
        raise SystemExit("release tree is dirty; commit or set ALLOW_DIRTY_RELEASE_TREE=1 for local dry runs")
    print("release tree clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

