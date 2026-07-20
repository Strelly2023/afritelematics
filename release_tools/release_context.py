"""Runtime context helpers for release-governance tooling."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
from typing import Any


@dataclass(frozen=True)
class ReleaseContext:
    repository_root: Path
    current_commit: str
    current_branch: str
    worktree_clean: bool
    staged_changes: bool
    untracked_files: bool
    repository_tree_sha256: str
    selected_rc_manifest: Path | None
    product_tree_sha256: str | None
    environment_id: str
    scope_id: str | None
    evidence_manifest_status: str


def repo_root(start: Path | None = None) -> Path:
    path = start or Path(__file__).resolve()
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    raise RuntimeError("unable to locate repository root")


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def current_commit(root: Path | None = None) -> str:
    root = repo_root(root)
    return _git(root, "rev-parse", "HEAD")


def current_branch(root: Path | None = None) -> str:
    root = repo_root(root)
    return _git(root, "branch", "--show-current")


def worktree_status(root: Path | None = None) -> dict[str, bool]:
    root = repo_root(root)
    porcelain = _git(root, "status", "--porcelain=v1")
    staged = any(line[:2].strip() for line in porcelain.splitlines())
    untracked = any(line.startswith("??") for line in porcelain.splitlines())
    return {
        "clean": porcelain == "",
        "staged_changes": staged,
        "untracked_files": untracked,
    }


def _tree_listing(root: Path, commit: str, paths: list[str] | None = None) -> str:
    args = ["ls-tree", "-r", "--full-tree", commit]
    if paths:
        args.extend(["--", *paths])
    return _git(root, *args)


def tree_hash(root: Path | None = None, *, commit: str = "HEAD", paths: list[str] | None = None) -> str:
    root = repo_root(root)
    listing = _tree_listing(root, commit, paths)
    return sha256(listing.encode("utf-8")).hexdigest()


def selected_manifest_path(root: Path | None = None) -> Path | None:
    root = repo_root(root)
    path = root / "release" / "candidates" / "RELEASE_CANDIDATE_SET.json"
    return path if path.exists() else None


def scope_id_from_file(root: Path | None = None) -> str | None:
    root = repo_root(root)
    scope_file = root / "release" / "scopes" / "INITIAL_GA_SCOPE.yaml"
    if not scope_file.exists():
        return None
    for line in scope_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("scope_id:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def evidence_manifest_status(root: Path | None = None) -> str:
    root = repo_root(root)
    result = root / "artifacts" / "release-baseline" / "evidence" / "MANIFEST_VALIDATION_RESULT.json"
    if not result.exists():
        return "NOT_RUN"
    try:
        payload: dict[str, Any] = json.loads(result.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "FAIL"
    return str(payload.get("result", "NOT_RUN"))


def environment_id() -> str:
    return os.environ.get("RELEASE_ENVIRONMENT_ID") or os.environ.get("CI_ENVIRONMENT_NAME") or "local"


def release_context(root: Path | None = None) -> ReleaseContext:
    root = repo_root(root)
    status = worktree_status(root)
    repository_tree_sha = tree_hash(root, commit="HEAD")
    selected = selected_manifest_path(root)
    product_tree = None
    if selected and selected.exists():
        try:
            data = json.loads(selected.read_text(encoding="utf-8"))
            product_tree = str(data.get("product_tree_sha256") or "")
        except json.JSONDecodeError:
            product_tree = None
    return ReleaseContext(
        repository_root=root,
        current_commit=current_commit(root),
        current_branch=current_branch(root),
        worktree_clean=status["clean"],
        staged_changes=status["staged_changes"],
        untracked_files=status["untracked_files"],
        repository_tree_sha256=repository_tree_sha,
        selected_rc_manifest=selected,
        product_tree_sha256=product_tree,
        environment_id=environment_id(),
        scope_id=scope_id_from_file(root),
        evidence_manifest_status=evidence_manifest_status(root),
    )
