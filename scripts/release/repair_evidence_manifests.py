#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release._common import dump_json, repo_root, load_json
from scripts.release.validate_evidence_manifests import manifest_files, validate_manifest


def main() -> int:
    root = repo_root()
    repair_log: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": str(root),
        "repairs": [],
        "quarantined": [],
    }
    for manifest in manifest_files(root):
        errors = validate_manifest(root, manifest)
        if not errors:
            continue
        repair_log["quarantined"].append({"manifest": str(manifest.relative_to(root)), "reasons": errors})
    out_dir = root / "artifacts" / "release-baseline" / "evidence"
    dump_json(out_dir / "MANIFEST_REPAIR_LOG.json", repair_log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
