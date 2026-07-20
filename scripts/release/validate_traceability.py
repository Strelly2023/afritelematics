#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def repo_root() -> Path:
    path = Path(__file__).resolve()
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    raise SystemExit("unable to locate repository root")


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML is required for traceability validation")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def commit_has_path(root: Path, commit: str, path: str) -> bool:
    try:
        out = git(root, "ls-tree", "--name-only", commit, "--", path)
        if out:
            return True
    except subprocess.CalledProcessError:
        pass
    try:
        git(root, "cat-file", "-e", f"{commit}:{path}")
        return True
    except subprocess.CalledProcessError:
        return False


def validate_matrix(root: Path, matrix: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    commit = str(matrix.get("commit_sha") or "")
    if len(commit) != 40:
        blockers.append("invalid commit sha")
    requirements = matrix.get("requirements", [])
    if not requirements:
        blockers.append("no requirements present")
    for requirement in requirements:
        req_id = requirement.get("requirement_id")
        impl = requirement.get("implementation", {})
        ver = requirement.get("verification", {})
        ev = requirement.get("evidence", {})
        acc = requirement.get("acceptance", {})
        if requirement.get("mandatory_for_ga") and requirement.get("in_scope"):
            if not impl.get("source_paths"):
                blockers.append(f"{req_id}: missing source mapping")
            if not ver.get("test_ids"):
                blockers.append(f"{req_id}: missing test mapping")
            if not ev.get("artifact_paths"):
                blockers.append(f"{req_id}: missing evidence mapping")
        for rel in impl.get("source_paths", []) + impl.get("configuration_paths", []) + impl.get("migration_paths", []):
            if not commit_has_path(root, commit, rel):
                blockers.append(f"{req_id}: source path missing at rc commit: {rel}")
        for rel in ver.get("result_artifacts", []) + ev.get("artifact_paths", []) + ev.get("manifest_paths", []):
            if not (root / rel).exists():
                blockers.append(f"{req_id}: artifact missing: {rel}")
        if acc.get("status") == "PASS" and ev.get("status") != "PASS":
            blockers.append(f"{req_id}: acceptance PASS without evidence PASS")
        if requirement.get("current_status") == "PASS" and ev.get("status") != "PASS":
            blockers.append(f"{req_id}: current status PASS without evidence")
        if requirement.get("last_validated_commit") != commit:
            blockers.append(f"{req_id}: validated commit mismatch")
    summary_path = root / "artifacts" / "release-baseline" / "evidence" / str(matrix.get("product") or "") / "TRACEABILITY_SUMMARY.json"
    if not summary_path.exists():
        blockers.append("summary artifact missing")
    return blockers


def main() -> int:
    root = repo_root()
    if yaml is None:
        raise SystemExit("PyYAML is required for traceability validation")
    blockers: dict[str, list[str]] = {}
    for product in ("novaid", "novaride", "novapay"):
        matrix_path = root / "release" / "traceability" / f"{product.upper()}_TRACEABILITY.yaml"
        if not matrix_path.exists():
            blockers[product] = ["traceability matrix missing"]
            continue
        blockers[product] = validate_matrix(root, load_yaml(matrix_path))
    ok = all(not values for values in blockers.values())
    report = {
        "repository": str(root),
        "status": "PASS" if ok else "FAIL",
        "blockers": blockers,
        "validated_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    out = root / "artifacts" / "release-baseline" / "preflight" / "traceability-validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
