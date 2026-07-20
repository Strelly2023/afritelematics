#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release._common import dump_json, dump_text, repo_root


def main() -> int:
    root = repo_root()
    cert_paths = []
    for path in root.rglob("*certificate*"):
        if path.is_file() and "node_modules" not in path.parts and ".git" not in path.parts:
            cert_paths.append(path)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": str(root),
        "certificates": [
            {
                "path": str(path.relative_to(root)),
                "classification": "informational only",
                "result": "UNVERIFIABLE",
            }
            for path in sorted(cert_paths)
        ],
    }
    out_dir = root / "artifacts" / "release-baseline" / "certificates"
    dump_json(out_dir / "CERTIFICATE_AUDIT.json", audit)
    dump_text(out_dir / "CERTIFICATE_AUDIT.md", "# Certificate audit\n\n" + json.dumps(audit, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
