#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "release"


def human_size(size_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB"]
    value = float(size_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024.0
    return f"{int(size_bytes)} B"


def safe_timestamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def classify(path: Path) -> dict[str, object]:
    rel = path.as_posix()
    lower = rel.lower()
    if rel == "csv.py":
        return {
            "classification": "SOURCE_OR_SCRIPT",
            "contains_sensitive_data": "unknown",
            "reproducible": "unknown",
            "keep": True,
            "ignore": False,
            "archive": False,
            "remove": False,
            "requires_operator_review": True,
            "reason": "Top-level python shim may shadow stdlib csv and should be reviewed before release use.",
        }
    if lower.startswith("var/"):
        return {
            "classification": "TEMPORARY_RUNTIME_OUTPUT",
            "contains_sensitive_data": "unknown",
            "reproducible": "yes",
            "keep": False,
            "ignore": True,
            "archive": False,
            "remove": False,
            "requires_operator_review": False,
            "reason": "Runtime output; keep out of release commits and ignore narrowly.",
        }
    if lower.startswith("deployment-evidence/"):
        return {
            "classification": "REQUIRED_RELEASE_EVIDENCE",
            "contains_sensitive_data": "unknown",
            "reproducible": "no",
            "keep": True,
            "ignore": False,
            "archive": False,
            "remove": False,
            "requires_operator_review": False,
            "reason": "Historical deployment evidence should be preserved until explicitly superseded.",
        }
    if lower.startswith("artifacts/"):
        return {
            "classification": "HISTORICAL_EVIDENCE",
            "contains_sensitive_data": "unknown",
            "reproducible": "no",
            "keep": True,
            "ignore": False,
            "archive": False,
            "remove": False,
            "requires_operator_review": False,
            "reason": "Existing artifacts capture prior release and certification evidence; preserve unless later regenerated canonically.",
        }
    return {
        "classification": "UNKNOWN",
        "contains_sensitive_data": "unknown",
        "reproducible": "unknown",
        "keep": False,
        "ignore": False,
        "archive": False,
        "remove": False,
        "requires_operator_review": True,
        "reason": "Path not recognized by inventory heuristics.",
    }


def summarize_directory(path: Path) -> dict[str, object]:
    file_count = 0
    dir_count = 0
    total_size = 0
    ext = Counter()
    if path.is_file():
        stat = path.stat()
        return {
            "relative_path": path.as_posix(),
            "type": "file",
            "size_bytes": stat.st_size,
            "modified_at": safe_timestamp(path),
            "file_count": 1,
            "extension_distribution": {path.suffix.lower() or "<no_ext>": 1},
        }
    for child in path.rglob("*"):
        try:
            stat = child.stat()
        except FileNotFoundError:
            continue
        if child.is_file():
            file_count += 1
            total_size += stat.st_size
            ext[child.suffix.lower() or "<no_ext>"] += 1
        elif child.is_dir():
            dir_count += 1
    return {
        "relative_path": path.as_posix(),
        "type": "directory",
        "size_bytes": total_size,
        "modified_at": safe_timestamp(path),
        "file_count": file_count,
        "directory_count": dir_count,
        "extension_distribution": dict(sorted(ext.items(), key=lambda item: item[0])),
    }


def discover_untracked_paths() -> list[Path]:
    result = []
    for line in os.popen(f"git -C {ROOT} status --short --untracked-files=all").read().splitlines():
        if not line.startswith("?? "):
            continue
        result.append(Path(line[3:]))
    return sorted(set(result), key=lambda p: p.as_posix())


def build_items(paths: Iterable[Path]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        rel = path.as_posix()
        if rel in seen or not path.exists():
            return
        seen.add(rel)
        summary = summarize_directory(path)
        summary.update(classify(path))
        items.append(summary)

    for path in paths:
        add(path)
        if path.is_dir():
            for child in sorted(path.iterdir(), key=lambda p: p.as_posix()):
                # Only record first-level children for readability; the root summary contains recursive counts.
                if child.is_dir() or child.is_file():
                    add(child)
    return sorted(items, key=lambda item: item["relative_path"])


def write_outputs(items: list[dict[str, object]], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = output_dir / "release-artifact-inventory.json"
    classification_path = output_dir / "RELEASE_ARTIFACT_CLASSIFICATION.md"

    inventory_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": os.popen(f"git -C {ROOT} branch --show-current").read().strip(),
        "commit": os.popen(f"git -C {ROOT} rev-parse HEAD").read().strip(),
        "worktree": os.popen(f"git -C {ROOT} status --short --branch").read().splitlines(),
        "items": items,
    }
    inventory_path.write_text(json.dumps(inventory_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Release Artifact Classification",
        "",
        "This classification was generated from the current synchronized baseline.",
        "",
        "| path | type | classification | keep | ignore | archive | remove | review | reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            "| {relative_path} | {type} | {classification} | {keep} | {ignore} | {archive} | {remove} | {requires_operator_review} | {reason} |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## Policy notes",
            "",
            "- `artifacts/` and `deployment-evidence/` are preserved as historical or required evidence until a later canonical regeneration replaces them.",
            "- `var/` is treated as temporary runtime output and should be ignored narrowly rather than committed.",
            "- `csv.py` is intentionally left for operator review because a top-level module named `csv.py` can shadow the Python stdlib module.",
        ]
    )
    classification_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return classification_path, inventory_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    items = build_items(discover_untracked_paths())
    classification_path, inventory_path = write_outputs(items, args.output_dir)
    print(classification_path)
    print(inventory_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
