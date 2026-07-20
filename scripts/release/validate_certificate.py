#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release._common import repo_root


def main() -> int:
    root = repo_root()
    cert_root = root / "artifacts" / "release-baseline" / "certificates"
    if not cert_root.exists():
        print(json.dumps({"result": "NOT_RUN", "reason": "no certificates present"}))
        return 0
    issues = []
    for path in cert_root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues.append(str(path.relative_to(root)))
            continue
        if data.get("result") == "PASS" and not data.get("commit_sha"):
            issues.append(str(path.relative_to(root)))
    print(json.dumps({"result": "PASS" if not issues else "FAIL", "issues": issues}, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
