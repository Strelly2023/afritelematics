#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "artifacts" / "ga-readiness" / "release" / "checksums" / "SHA256SUMS"
DEFAULT_REPORT = ROOT / "artifacts" / "ga-readiness" / "release" / "checksums" / "checksum-report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files() -> list[Path]:
    paths: list[Path] = []
    candidates = [
        ROOT / "docs" / "release" / "RELEASE_ARTIFACT_CLASSIFICATION.md",
        ROOT / "docs" / "release" / "release-artifact-inventory.json",
        ROOT / "docs" / "release" / "release-scope.yaml",
        ROOT / "artifacts" / "ga-readiness" / "release" / "reproducibility" / "report.json",
        ROOT / "artifacts" / "ga-readiness" / "release" / "reproducibility" / "report.md",
    ]
    portal_dist = ROOT / "novacodepro_portal" / "dist"
    if portal_dist.exists():
        candidates.extend(sorted(path for path in portal_dist.rglob("*") if path.is_file()))
    for path in candidates:
        if path.exists() and path.is_file():
            paths.append(path)
    return sorted(set(paths), key=lambda p: p.relative_to(ROOT).as_posix())


def write_manifest(paths: list[Path], manifest_path: Path, report_path: Path) -> dict[str, object]:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        entries.append({"path": rel, "sha256": sha256(path), "size_bytes": path.stat().st_size})
    manifest_lines = [f"{entry['sha256']}  {entry['path']}" for entry in entries]
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    report = {
        "schema_version": 1,
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
        "file_count": len(entries),
        "entries": entries,
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = write_manifest(collect_files(), args.manifest, args.report)
    print(json.dumps({"manifest": report["manifest"], "file_count": report["file_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
