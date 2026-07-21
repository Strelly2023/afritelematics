#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON = ROOT / "artifacts" / "ga-readiness" / "release" / "manifests" / "release-manifest.json"
DEFAULT_YAML = ROOT / "artifacts" / "ga-readiness" / "release" / "manifests" / "release-manifest.yaml"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def commit_epoch() -> int:
    return int(git("show", "-s", "--format=%ct", "HEAD"))


def yaml_value(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if value == "" or any(ch in value for ch in ":#{}[]\n"):
            return json.dumps(value)
        return value
    if isinstance(value, list):
        if not value:
            return "[]"
        lines = []
        for item in value:
            rendered = yaml_value(item, indent + 2)
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}- {rendered.splitlines()[0]}")
                for line in rendered.splitlines()[1:]:
                    lines.append(f"{prefix}  {line}")
            else:
                lines.append(f"{prefix}- {rendered}")
        return "\n".join(lines)
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = []
        for key, item in value.items():
            rendered = yaml_value(item, indent + 2)
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                for line in rendered.splitlines():
                    lines.append(f"{prefix}  {line}")
            else:
                lines.append(f"{prefix}{key}: {rendered}")
        return "\n".join(lines)
    return json.dumps(str(value))


def build_manifest() -> dict[str, Any]:
    commit_sha = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    remote_sha = git("rev-parse", f"origin/{branch}")
    release_scope = ROOT / "docs" / "release" / "release-scope.yaml"
    checksum_manifest = ROOT / "artifacts" / "ga-readiness" / "release" / "checksums" / "SHA256SUMS"
    reproducibility = ROOT / "artifacts" / "ga-readiness" / "release" / "reproducibility" / "report.json"
    commit_time = datetime.fromtimestamp(commit_epoch(), tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "release_id": "novatech-2026.1.0",
        "release_candidate": "novatech-2026.1.0-rc.1",
        "status": "BASELINE_IN_PROGRESS",
        "branch": branch,
        "commit_sha": commit_sha,
        "remote_commit_sha": remote_sha,
        "tag": None,
        "created_at": commit_time,
        "source_date_epoch": commit_epoch(),
        "repository": "afritelematics",
        "products": ["NovaID", "NovaPay", "NovaRide", "NovaCodePro"],
        "components": [
            {
                "component_id": "novacodepro_portal",
                "product": "NovaCodePro",
                "source_path": "novacodepro_portal",
                "artifact_type": "web_portal",
                "build_command": "npm run build --prefix novacodepro_portal",
                "test_command": "npm test --prefix novacodepro_portal",
                "version": "0.1.0",
                "runtime": "Node.js 20.19.5",
                "expected_output": "dist/",
                "release_criticality": "high",
                "current_inclusion_status": "VERIFIED",
                "external_blocker": None,
            },
            {
                "component_id": "novaid_backend",
                "product": "NovaID",
                "source_path": "afritech/novaid",
                "artifact_type": "backend_service",
                "build_command": "python3 -m compileall afritech/novaid",
                "test_command": "python3 -m pytest -q afritech/tests/novaid",
                "version": "current-baseline",
                "runtime": "Python 3.11.8",
                "expected_output": "service validation artifacts",
                "release_criticality": "high",
                "current_inclusion_status": "IN_PROGRESS",
                "external_blocker": "current baseline not rerun in this pass",
            },
            {
                "component_id": "novapay_backend",
                "product": "NovaPay",
                "source_path": "afritech/novapay",
                "artifact_type": "backend_service",
                "build_command": "python3 -m compileall afritech/novapay",
                "test_command": "python3 -m pytest -q afritech/tests/novapay",
                "version": "current-baseline",
                "runtime": "Python 3.11.8",
                "expected_output": "ledger and outbox validation artifacts",
                "release_criticality": "high",
                "current_inclusion_status": "IN_PROGRESS",
                "external_blocker": "current financial certification not rerun in this pass",
            },
            {
                "component_id": "novaride_runtime",
                "product": "NovaRide",
                "source_path": "afritech/novaride_runtime",
                "artifact_type": "runtime_service",
                "build_command": "python3 -m compileall afritech/novaride_runtime",
                "test_command": "python3 -m pytest -q afritech/tests/novaride_runtime",
                "version": "current-baseline",
                "runtime": "Python 3.11.8",
                "expected_output": "runtime validation artifacts",
                "release_criticality": "high",
                "current_inclusion_status": "IN_PROGRESS",
                "external_blocker": "real runtime certification not rerun in this pass",
            },
        ],
        "runtime_versions": {
            "python": "3.11.8",
            "node": "20.19.5",
            "npm": "10.8.2",
            "java": "17.0.9",
        },
        "build_commands": ["npm run build --prefix novacodepro_portal"],
        "test_commands": ["npm test --prefix novacodepro_portal"],
        "artifacts": [
            "novacodepro_portal/dist",
            "docs/release/RELEASE_ARTIFACT_CLASSIFICATION.md",
            "docs/release/release-artifact-inventory.json",
            "docs/release/release-scope.yaml",
            "artifacts/ga-readiness/release/reproducibility/report.json",
            "artifacts/ga-readiness/release/reproducibility/report.md",
        ],
        "artifact_hashes": {
            "checksum_manifest": str(checksum_manifest.relative_to(ROOT)),
            "reproducibility_report": str(reproducibility.relative_to(ROOT)),
        },
        "container_digests": [],
        "database_migrations": [],
        "sbom_references": [],
        "checksum_manifest": str(checksum_manifest.relative_to(ROOT)),
        "reproducibility_report": str(reproducibility.relative_to(ROOT)),
        "security_evidence": ["docs/release/GA_READINESS_BLOCKER_MATRIX.md"],
        "infrastructure_evidence": [],
        "mobile_evidence": [],
        "pilot_evidence": [],
        "prr_evidence": [],
        "known_blockers": [
            "production signing material unavailable",
            "NovaID/NovaPay/NovaRide certification not rerun in this pass",
            "mobile and infrastructure certification not rerun in this pass",
        ],
        "external_blockers": [
            "production signing material unavailable",
        ],
        "approval_status": "UNSIGNED",
        "signature_status": "EXTERNALLY_BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--yaml", type=Path, default=DEFAULT_YAML)
    args = parser.parse_args()
    manifest = build_manifest()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.yaml.write_text(yaml_value(manifest) + "\n", encoding="utf-8")
    print(args.json)
    print(args.yaml)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
