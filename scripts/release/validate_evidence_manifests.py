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

from scripts.release._common import dump_json, dump_text, repo_root, load_json


def manifest_files(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for base in (
        root / "artifacts" / "release-baseline" / "evidence",
        root / "artifacts" / "novaride",
        root / "artifacts" / "novaid",
        root / "artifacts" / "novapay",
    ):
        if base.exists():
            for path in base.rglob("*.json"):
                if "manifest" in path.name.lower():
                    candidates.append(path)
    return sorted(set(candidates))


def validate_manifest(root: Path, path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = load_json(path)
    except Exception as exc:  # pragma: no cover
        return [f"invalid json: {exc}"]
    for key in ("schema_version", "manifest_id", "product", "release_candidate_id", "commit_sha", "result", "artifacts"):
        if key not in data:
            errors.append(f"missing {key}")
    for artifact in data.get("artifacts", []):
        rel = artifact.get("path")
        if not rel:
            errors.append("artifact path missing")
            continue
        artifact_path = (root / rel).resolve(strict=False)
        if not artifact_path.exists():
            errors.append(f"missing artifact: {rel}")
            continue
        digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if digest != artifact.get("sha256"):
            errors.append(f"checksum mismatch: {rel}")
    return errors


def main() -> int:
    root = repo_root()
    manifests = manifest_files(root)
    results: list[dict[str, Any]] = []
    blockers: dict[str, list[str]] = {}
    for manifest in manifests:
        errors = validate_manifest(root, manifest)
        result = "PASS" if not errors else "FAIL"
        results.append({"manifest": str(manifest.relative_to(root)), "result": result, "errors": errors})
        if errors:
            blockers[str(manifest.relative_to(root))] = errors
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": str(root),
        "result": "PASS" if not blockers else "FAIL",
        "manifest_count": len(manifests),
        "validated_count": len(results),
        "blockers": blockers,
    }
    out_dir = root / "artifacts" / "release-baseline" / "evidence"
    dump_json(out_dir / "MANIFEST_VALIDATION_RESULT.json", payload)
    dump_text(out_dir / "MANIFEST_VALIDATION_RESULT.md", "# Manifest validation\n\n" + json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
