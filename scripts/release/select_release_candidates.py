#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_tools.release_context import repo_root, tree_hash, worktree_status

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


LOCKFILE_NAMES = ("package-lock.json", "poetry.lock", "Pipfile.lock", "uv.lock", "yarn.lock", "pnpm-lock.yaml")


@dataclass
class Candidate:
    schema_version: str
    product: str
    release_candidate_id: str
    commit_sha: str
    repository_tree_sha256: str
    product_tree_sha256: str
    selected_from_branch: str
    selected_at_utc: str
    scope_id: str
    source_paths: list[str]
    test_paths: list[str]
    migration_paths: list[str]
    lockfiles: list[dict[str, str]]
    migrations: list[dict[str, str]]
    dirty_tree: bool
    selection_status: str
    selection_blockers: list[str]


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML is required for release selection")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def ensure_clean(root: Path) -> None:
    status = worktree_status(root)
    if not status["clean"]:
        raise SystemExit("release candidate selection requires a clean source tree")


def normalize_commit(root: Path, value: str) -> str:
    if len(value) != 40:
        raise SystemExit(f"commit must be a full 40-character SHA: {value}")
    resolved = git(root, "rev-parse", "--verify", f"{value}^{{commit}}")
    if resolved != value:
        raise SystemExit(f"commit did not resolve exactly: {value}")
    return resolved


def commit_reachable(root: Path, commit: str, branch: str) -> None:
    subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, branch], check=True)


def path_exists_at_commit(root: Path, commit: str, path: str) -> bool:
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


def discover_files(root: Path, commit: str, paths: list[str], patterns: tuple[str, ...]) -> list[str]:
    discovered: list[str] = []
    if not paths:
        return discovered
    listing = git(root, "ls-tree", "-r", "--full-tree", commit, "--", *paths)
    for line in listing.splitlines():
        if not line:
            continue
        _, _, _, rel = line.split(None, 3)
        if rel.endswith(patterns):
            discovered.append(rel)
    return sorted(set(discovered))


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def sha256_blob(root: Path, commit: str, path: str) -> str:
    blob = git(root, "show", f"{commit}:{path}")
    return sha256_text(blob)


def product_tree_hash(root: Path, commit: str, boundary_paths: list[str]) -> str:
    listing = git(root, "ls-tree", "-r", "--full-tree", commit, "--", *boundary_paths)
    return sha256_text(listing)


def repository_tree_hash(root: Path, commit: str) -> str:
    return tree_hash(root, commit=commit)


def build_candidate(root: Path, boundaries: dict[str, Any], scope_id: str, branch: str, product: str, commit: str) -> Candidate:
    product_cfg = boundaries["products"][product]
    boundary_paths: list[str] = []
    for key in ("source_roots", "test_roots", "migration_roots", "deployment_roots", "mobile_roots", "evidence_roots", "certificate_roots"):
        boundary_paths.extend(product_cfg.get(key, []))
    boundary_paths = sorted(dict.fromkeys(boundary_paths))
    missing = [path for path in boundary_paths if not path_exists_at_commit(root, commit, path)]
    if missing:
        raise SystemExit(f"paths missing at candidate commit for {product}: {', '.join(missing)}")

    lockfiles = discover_files(root, commit, boundary_paths, LOCKFILE_NAMES)
    migrations = discover_files(root, commit, list(product_cfg.get("migration_roots", [])), (".sql", ".yaml", ".yml", ".json"))
    candidate = Candidate(
        schema_version="1.0",
        product=product,
        release_candidate_id=f"{product.upper()}-RC-001",
        commit_sha=commit,
        repository_tree_sha256=repository_tree_hash(root, commit),
        product_tree_sha256=product_tree_hash(root, commit, boundary_paths),
        selected_from_branch=branch,
        selected_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        scope_id=scope_id,
        source_paths=list(product_cfg.get("source_roots", [])),
        test_paths=list(product_cfg.get("test_roots", [])),
        migration_paths=list(product_cfg.get("migration_roots", [])),
        lockfiles=[{"path": path, "sha256": sha256_blob(root, commit, path)} for path in lockfiles],
        migrations=[{"path": path, "sha256": sha256_blob(root, commit, path)} for path in migrations],
        dirty_tree=False,
        selection_status="SELECTED",
        selection_blockers=[],
    )
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novatech-scope", required=True)
    parser.add_argument("--novaid-commit", required=True)
    parser.add_argument("--novaride-commit", required=True)
    parser.add_argument("--novapay-commit", required=True)
    parser.add_argument("--selected-branch", default="release/initial-ga-baseline-2026")
    args = parser.parse_args()

    root = repo_root()
    ensure_clean(root)
    scope = load_yaml(root / args.novatech_scope)
    boundaries = load_yaml(root / "release" / "governance" / "PRODUCT_BOUNDARIES.yaml")
    scope_id = str(scope.get("scope_id") or "")
    if scope_id != "INITIAL-GA-AU-VIC-001":
        raise SystemExit("unexpected scope id")

    candidates: dict[str, Candidate] = {}
    for product, commit_arg in {
        "novaid": args.novaid_commit,
        "novaride": args.novaride_commit,
        "novapay": args.novapay_commit,
    }.items():
        commit = normalize_commit(root, commit_arg)
        commit_reachable(root, commit, args.selected_branch)
        candidates[product] = build_candidate(root, boundaries, scope_id, args.selected_branch, product, commit)

    same_commit = len({candidate.commit_sha for candidate in candidates.values()}) == 1
    combined = {
        "schema_version": "1.0",
        "release_candidate_set_id": "INITIAL-GA-AU-VIC-001-RC-SET-001",
        "scope_id": scope_id,
        "selected_from_branch": args.selected_branch,
        "selection_model": "common_monorepo_commit" if same_commit else "separate_product_commits",
        "products_share_commit": same_commit,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "products": {
            product: asdict(candidate) for product, candidate in candidates.items()
        },
    }

    out_dir = root / "release" / "candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    for product, candidate in candidates.items():
        (out_dir / f"{product.upper()}_RC.json").write_text(
            json.dumps(asdict(candidate), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (out_dir / "RELEASE_CANDIDATE_SET.json").write_text(
        json.dumps(combined, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(combined, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
