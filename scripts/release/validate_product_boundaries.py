#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import json
import os
import sys
from typing import Any


try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


@dataclass
class BoundaryEntry:
    product: str
    root_kind: str
    path: str
    exists: bool
    symlink_safe: bool
    action: str
    reason: str


def repo_root() -> Path:
    path = Path(__file__).resolve()
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    raise SystemExit("unable to locate repository root")


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML is required for release validation")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def safe_path(root: Path, value: str) -> tuple[bool, bool, Path]:
    current = root / value
    candidate = current.resolve(strict=False)
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return False, False, candidate
    symlink_safe = True
    probe = root
    for part in Path(value).parts:
        probe = probe / part
        if probe.exists() and probe.is_symlink():
            target = probe.resolve(strict=False)
            try:
                target.relative_to(root.resolve())
            except ValueError:
                symlink_safe = False
                break
    return candidate.exists(), symlink_safe, candidate


def collect_entries(root: Path, boundaries: dict[str, Any]) -> list[BoundaryEntry]:
    entries: list[BoundaryEntry] = []
    seen_paths: dict[str, str] = {}
    product_sections = boundaries.get("products", {})
    for product, sections in product_sections.items():
        for root_kind, paths in sections.items():
            if not isinstance(paths, list):
                continue
            for rel in paths:
                if rel in seen_paths and seen_paths[rel] != product:
                    entries.append(
                        BoundaryEntry(
                            product=product,
                            root_kind=root_kind,
                            path=rel,
                            exists=False,
                            symlink_safe=True,
                            action="investigate",
                            reason=f"path is reused by {seen_paths[rel]}",
                        )
                    )
                    continue
                seen_paths[rel] = product
                exists, symlink_safe, resolved = safe_path(root, rel)
                action = "preserve" if exists and symlink_safe else "investigate"
                reason = "" if exists and symlink_safe else f"missing or unsafe path: {resolved}"
                entries.append(
                    BoundaryEntry(
                        product=product,
                        root_kind=root_kind,
                        path=rel,
                        exists=exists,
                        symlink_safe=symlink_safe,
                        action=action,
                        reason=reason,
                    )
                )
    return entries


def main() -> int:
    root = repo_root()
    boundaries_path = root / "release" / "governance" / "PRODUCT_BOUNDARIES.yaml"
    boundaries = load_yaml(boundaries_path)
    entries = collect_entries(root, boundaries)
    failures = [entry for entry in entries if not entry.exists or not entry.symlink_safe]
    report = {
        "generated_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "repository": str(root),
        "status": "FAIL" if failures else "PASS",
        "entries": [asdict(entry) for entry in entries],
        "summary": {
            "products": sorted(boundaries.get("products", {}).keys()),
            "entries": len(entries),
            "failures": len(failures),
        },
    }
    output = root / "artifacts" / "release-baseline" / "preflight" / "product-boundary-validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
