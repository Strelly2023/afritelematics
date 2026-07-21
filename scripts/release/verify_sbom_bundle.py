#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SBOM_DIR = ROOT / "artifacts" / "ga-readiness" / "release" / "sbom"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_sbom(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        payload = load_json(path)
    except Exception as exc:  # pragma: no cover - defensive
        return [f"invalid_json:{path.as_posix()}:{exc}"]
    if payload.get("bomFormat") != "CycloneDX":
        issues.append(f"bom_format:{path.as_posix()}")
    if payload.get("specVersion") not in {"1.5", "1.6"}:
        issues.append(f"spec_version:{path.as_posix()}")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or not metadata.get("component"):
        issues.append(f"metadata_missing:{path.as_posix()}")
    components = payload.get("components")
    if not isinstance(components, list) or not components:
        issues.append(f"components_missing:{path.as_posix()}")
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, list):
        issues.append(f"dependencies_missing:{path.as_posix()}")
    return issues


def verify_bundle(sbom_dir: Path) -> dict[str, Any]:
    files = sorted(sbom_dir.glob("*.cdx.json"))
    report = {
        "sbom_dir": _display_path(sbom_dir),
        "files": [_display_path(path) for path in files],
        "issues": [],
        "status": "PASS",
    }
    if not files:
        report["issues"].append(f"missing_sbom_files:{sbom_dir.relative_to(ROOT).as_posix()}")
        report["status"] = "FAIL"
        return report
    issues: list[str] = []
    for path in files:
        issues.extend(verify_sbom(path))
    report["issues"] = issues
    report["status"] = "PASS" if not issues else "FAIL"
    return report


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sbom-dir", type=Path, default=DEFAULT_SBOM_DIR)
    args = parser.parse_args()
    report = verify_bundle(args.sbom_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
