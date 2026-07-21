#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "ga-readiness" / "release" / "reproducibility"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def commit_timestamp_iso() -> str:
    seconds = int(subprocess.run(
        ["git", "show", "-s", "--format=%ct", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip())
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def short_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def build_command_for_target(target: str) -> list[str]:
    if target == "novacodepro_portal":
        return ["npm", "run", "build"]
    raise SystemExit(f"unsupported reproducible build target: {target}")


def required_inputs_for_target(target: str) -> list[Path]:
    if target == "novacodepro_portal":
        return [ROOT / "contracts" / "app-registry.json"]
    raise SystemExit(f"unsupported reproducible build target: {target}")


def target_source_dir(target: str) -> Path:
    if target == "novacodepro_portal":
        return ROOT / "novacodepro_portal"
    raise SystemExit(f"unsupported reproducible build target: {target}")


def copy_inputs(temp_root: Path, target: str) -> Path:
    source = target_source_dir(target)
    temp_target = temp_root / source.name
    shutil.copytree(
        source,
        temp_target,
        ignore=shutil.ignore_patterns("node_modules", "dist", ".vite", "coverage", ".turbo"),
    )
    source_node_modules = source / "node_modules"
    if source_node_modules.exists():
        temp_node_modules = temp_target / "node_modules"
        if temp_node_modules.exists() or temp_node_modules.is_symlink():
            if temp_node_modules.is_dir() and not temp_node_modules.is_symlink():
                shutil.rmtree(temp_node_modules)
            else:
                temp_node_modules.unlink()
        temp_node_modules.symlink_to(source_node_modules, target_is_directory=True)
    for extra in required_inputs_for_target(target):
        rel = extra.relative_to(ROOT)
        dest = temp_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extra, dest)
    return temp_target


def build_target(temp_root: Path, target: str, *, commit: str, timestamp: str) -> Path:
    temp_target = copy_inputs(temp_root, target)
    env = os.environ.copy()
    env["NOVACODEPRO_BUILD_COMMIT"] = commit
    env["NOVACODEPRO_BUILD_TIMESTAMP"] = timestamp
    subprocess.run(
        build_command_for_target(target),
        cwd=temp_target,
        check=True,
        env=env,
    )
    dist = temp_target / "dist"
    if not dist.is_dir():
        raise SystemExit(f"missing build output directory: {dist}")
    return dist


def hash_tree(root: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        entries.append(
            {
                "path": rel,
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return entries


def compare_hash_trees(a: list[dict[str, object]], b: list[dict[str, object]]) -> dict[str, object]:
    by_path_a = {entry["path"]: entry for entry in a}
    by_path_b = {entry["path"]: entry for entry in b}
    paths = sorted(set(by_path_a) | set(by_path_b))
    differing = []
    missing = []
    extra = []
    identical = 0
    for path in paths:
        left = by_path_a.get(path)
        right = by_path_b.get(path)
        if left and right:
            if left["sha256"] == right["sha256"]:
                identical += 1
            else:
                differing.append({"path": path, "left": left, "right": right})
        elif left and not right:
            missing.append({"path": path, "side": "right"})
        elif right and not left:
            extra.append({"path": path, "side": "right"})
    status = "IDENTICAL" if not differing and not missing and not extra else "DIFFERENT"
    return {
        "status": status,
        "identical_files": identical,
        "differing_files": differing,
        "missing_files": missing,
        "extra_files": extra,
    }


def run_verification(target: str, report_dir: Path) -> dict[str, object]:
    commit = short_commit()
    timestamp = commit_timestamp_iso()
    report_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ncp-repro-a-", dir="/private/tmp") as a_tmp, tempfile.TemporaryDirectory(
        prefix="ncp-repro-b-", dir="/private/tmp"
    ) as b_tmp:
        dist_a = build_target(Path(a_tmp), target, commit=commit, timestamp=timestamp)
        dist_b = build_target(Path(b_tmp), target, commit=commit, timestamp=timestamp)
        hashes_a = hash_tree(dist_a)
        hashes_b = hash_tree(dist_b)
        comparison = compare_hash_trees(hashes_a, hashes_b)
        report = {
            "schema_version": 1,
            "target": target,
            "commit_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip(),
            "commit_timestamp": timestamp,
            "build_command": "npm run build",
            "status": comparison["status"],
            "builds": [
                {"label": "a", "dist": dist_a.as_posix(), "artifacts": hashes_a},
                {"label": "b", "dist": dist_b.as_posix(), "artifacts": hashes_b},
            ],
            "comparison": comparison,
        }
        (report_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_lines = [
            "# Reproducible Build Verification",
            "",
            f"- target: `{target}`",
            f"- commit: `{report['commit_sha']}`",
            f"- timestamp: `{timestamp}`",
            f"- status: `{comparison['status']}`",
            f"- identical files: `{comparison['identical_files']}`",
            f"- differing files: `{len(comparison['differing_files'])}`",
            f"- missing files: `{len(comparison['missing_files'])}`",
            f"- extra files: `{len(comparison['extra_files'])}`",
            "",
            "## Artifact hashes",
            "",
            "| path | sha256 | size bytes |",
            "| --- | --- | --- |",
        ]
        for entry in hashes_a:
            md_lines.append(f"| {entry['path']} | {entry['sha256']} | {entry['size_bytes']} |")
        (report_dir / "report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
        return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="novacodepro_portal")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()
    report = run_verification(args.target, args.report_dir)
    print(json.dumps({"target": args.target, "status": report["status"]}, indent=2))
    if report["status"] != "IDENTICAL":
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
