#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release._common import dump_json, dump_text, repo_root


def classify(path: Path) -> str:
    suffix = path.suffix.lower()
    if "certificate" in path.name.lower():
        return "certificate"
    if "manifest" in path.name.lower() or suffix in {".sha256", ".sha512"}:
        return "checksum_manifest"
    if "evidence" in path.parts or "evidence" in path.name.lower():
        return "evidence"
    return "other"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    root = repo_root()
    inventory: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in {".git", "venv", "node_modules"} for part in path.parts):
            continue
        if "artifacts" not in path.parts and "contracts" not in path.parts and "docs" not in path.parts:
            continue
        inventory.append(
            {
                "path": str(path.relative_to(root)),
                "type": classify(path),
                "size": path.stat().st_size,
                "sha256": sha256(path),
                "last_modified_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                "product": "novaride" if "novaride" in path.parts else ("novaid" if "novaid" in path.parts else ("novapay" if "novapay" in path.parts else "unknown")),
                "release_candidate_id": "UNKNOWN",
                "commit_sha": "",
                "environment": "local",
                "test_command": "",
                "status": "NOT_RUN",
                "manifest_membership": "unknown",
                "certificate_membership": "unknown",
                "validation_result": "NOT_RUN",
            }
        )
    out_dir = root / "artifacts" / "release-baseline" / "evidence"
    dump_json(out_dir / "EVIDENCE_INVENTORY.json", {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "entries": inventory})
    md = ["# Evidence inventory", "", f"Entries: {len(inventory)}", ""]
    for entry in inventory[:200]:
        md.append(f"- {entry['path']} ({entry['type']})")
    dump_text(out_dir / "EVIDENCE_INVENTORY.md", "\n".join(md) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
