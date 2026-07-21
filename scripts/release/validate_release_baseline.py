#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.release.verify_checksum_manifest import verify as verify_checksum_manifest

DEFAULT_REPORT_DIR = ROOT / "artifacts" / "ga-readiness" / "release" / "baseline"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def current_untracked_paths() -> set[str]:
    paths: set[str] = set()
    for line in git("status", "--short", "--untracked-files=all").splitlines():
        if line.startswith("?? "):
            paths.add(line[3:])
    return paths


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(report_dir: Path) -> dict[str, object]:
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    remote = git("rev-parse", f"origin/{branch}")
    dirty_tracked = git("diff", "--name-only").splitlines() + git("diff", "--name-only", "--cached").splitlines()

    inventory_path = ROOT / "docs" / "release" / "release-artifact-inventory.json"
    classification_path = ROOT / "docs" / "release" / "RELEASE_ARTIFACT_CLASSIFICATION.md"
    scope_path = ROOT / "docs" / "release" / "release-scope.yaml"
    reproducibility_path = ROOT / "artifacts" / "ga-readiness" / "release" / "reproducibility" / "report.json"
    manifest_path = ROOT / "artifacts" / "ga-readiness" / "release" / "manifests" / "release-manifest.json"
    checksum_path = ROOT / "artifacts" / "ga-readiness" / "release" / "checksums" / "SHA256SUMS"
    sbom_dir = ROOT / "artifacts" / "ga-readiness" / "release" / "sbom"

    blockers: list[dict[str, object]] = []
    if branch != "feature/product-factory-enterprise-sdlc":
        blockers.append({"id": "branch_policy", "detail": branch})
    if head != remote:
        blockers.append({"id": "remote_sync", "detail": {"head": head, "remote": remote}})
    if dirty_tracked:
        blockers.append({"id": "dirty_tracked_worktree", "detail": dirty_tracked})
    if not inventory_path.exists() or not classification_path.exists():
        blockers.append({"id": "artifact_classification_missing", "detail": None})
    else:
        inventory = load_json(inventory_path)
        known = {item["relative_path"] for item in inventory.get("items", [])}
        unknown_untracked = sorted(current_untracked_paths() - known)
        if unknown_untracked:
            blockers.append({"id": "unknown_untracked_paths", "detail": unknown_untracked})
    if not scope_path.exists():
        blockers.append({"id": "release_scope_missing", "detail": None})
    if not reproducibility_path.exists():
        blockers.append({"id": "reproducibility_report_missing", "detail": None})
    else:
        reproducibility = load_json(reproducibility_path)
        if reproducibility.get("status") != "IDENTICAL":
            blockers.append({"id": "reproducibility_failed", "detail": reproducibility.get("status")})
    if not checksum_path.exists():
        blockers.append({"id": "checksum_manifest_missing", "detail": None})
    else:
        checksum_report = verify_checksum_manifest(checksum_path, base_dir=ROOT)
        if checksum_report["status"] != "PASS":
            blockers.append({"id": "checksum_mismatch", "detail": checksum_report})
    if not manifest_path.exists():
        blockers.append({"id": "release_manifest_missing", "detail": None})
    else:
        manifest = load_json(manifest_path)
        if manifest.get("signature_status") != "EXTERNALLY_BLOCKED":
            blockers.append({"id": "signature_status_unexpected", "detail": manifest.get("signature_status")})
    if not sbom_dir.exists() or not list(sbom_dir.glob("*.json")) and not list(sbom_dir.glob("*.cdx.json")):
        blockers.append({"id": "sbom_missing", "detail": str(sbom_dir.relative_to(ROOT))})

    status = "LOCAL_BASELINE_PASS" if not blockers else "RC_FREEZE_BLOCKED"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": branch,
        "head": head,
        "remote": remote,
        "status": status,
        "blockers": blockers,
        "paths": {
            "inventory": str(inventory_path.relative_to(ROOT)),
            "classification": str(classification_path.relative_to(ROOT)),
            "scope": str(scope_path.relative_to(ROOT)),
            "reproducibility": str(reproducibility_path.relative_to(ROOT)),
            "manifest": str(manifest_path.relative_to(ROOT)),
            "checksums": str(checksum_path.relative_to(ROOT)),
        },
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "validation-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_lines = [
        "# Release Baseline Validation Report",
        "",
        f"- branch: `{branch}`",
        f"- head: `{head}`",
        f"- remote: `{remote}`",
        f"- status: `{status}`",
        "",
        "## Blockers",
    ]
    if blockers:
        for blocker in blockers:
            md_lines.append(f"- `{blocker['id']}`: `{blocker['detail']}`")
    else:
        md_lines.append("- none")
    (report_dir / "validation-report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()
    report = validate(args.report_dir)
    print(report["status"])
    return 0 if report["status"] == "LOCAL_BASELINE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
