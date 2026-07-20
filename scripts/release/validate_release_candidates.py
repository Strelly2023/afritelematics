#!/usr/bin/env python3
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_tools.release_context import repo_root

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    if yaml is None:
        raise SystemExit("PyYAML is required for release validation")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_candidate(root: Path, manifest: dict[str, object], branch: str, scope_id: str) -> list[str]:
    blockers: list[str] = []
    commit = str(manifest.get("commit_sha") or "")
    if len(commit) != 40:
        blockers.append("commit must be a full 40-character SHA")
        return blockers
    try:
        resolved = git(root, "rev-parse", "--verify", f"{commit}^{{commit}}")
        if resolved != commit:
            blockers.append("commit does not resolve exactly")
    except subprocess.CalledProcessError:
        blockers.append("commit not found")
    try:
        subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, branch], check=True)
    except subprocess.CalledProcessError:
        blockers.append("commit is not reachable from selected branch")

    if str(manifest.get("scope_id") or "") != scope_id:
        blockers.append("scope id mismatch")

    boundaries = load_yaml(root / "release" / "governance" / "PRODUCT_BOUNDARIES.yaml")
    product = str(manifest.get("product") or "")
    product_cfg = boundaries.get("products", {}).get(product, {})
    boundary_paths: list[str] = []
    for key in ("source_roots", "test_roots", "migration_roots", "deployment_roots", "mobile_roots", "evidence_roots", "certificate_roots"):
        boundary_paths.extend(product_cfg.get(key, []))
    boundary_paths = sorted(dict.fromkeys(boundary_paths))
    if not boundary_paths:
        blockers.append("no boundary paths recorded")
    listing = git(root, "ls-tree", "-r", "--full-tree", commit, "--", *boundary_paths) if boundary_paths else ""
    product_tree_sha = sha256_text(listing)
    if product_tree_sha != str(manifest.get("product_tree_sha256") or ""):
        blockers.append("product tree hash mismatch")
    repo_listing = git(root, "ls-tree", "-r", "--full-tree", commit)
    repo_tree_sha = sha256_text(repo_listing)
    if repo_tree_sha != str(manifest.get("repository_tree_sha256") or ""):
        blockers.append("repository tree hash mismatch")
    if bool(manifest.get("dirty_tree")):
        blockers.append("manifest recorded dirty tree")
    if str(manifest.get("selected_from_branch") or "") != branch:
        blockers.append("selected branch mismatch")
    return blockers


def main() -> int:
    root = repo_root()
    set_path = root / "release" / "candidates" / "RELEASE_CANDIDATE_SET.json"
    if not set_path.exists():
        print("candidate set missing", file=sys.stderr)
        return 1
    combined = load_json(set_path)
    branch = str(combined.get("selected_from_branch") or "")
    scope_id = str(combined.get("scope_id") or "")
    blockers: dict[str, list[str]] = {}
    for product in ("novaid", "novaride", "novapay"):
        manifest_path = root / "release" / "candidates" / f"{product.upper()}_RC.json"
        if not manifest_path.exists():
            blockers[product] = ["candidate manifest missing"]
            continue
        blockers[product] = validate_candidate(root, load_json(manifest_path), branch, scope_id)

    ok = all(not values for values in blockers.values())
    report = {
        "repository": str(root),
        "branch": branch,
        "scope_id": scope_id,
        "status": "PASS" if ok else "FAIL",
        "blockers": blockers,
        "validated_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    (root / "artifacts" / "release-baseline" / "preflight" / "release-candidate-validation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
