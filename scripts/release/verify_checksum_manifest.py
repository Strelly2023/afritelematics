#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(manifest: Path, *, base_dir: Path = ROOT) -> dict[str, object]:
    missing: list[str] = []
    mismatched: list[dict[str, str]] = []
    entries = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        path = base_dir / rel
        if not path.exists():
            missing.append(rel)
            continue
        actual = sha256(path)
        if actual != digest:
            mismatched.append({"path": rel, "expected": digest, "actual": actual})
        entries.append(rel)
    status = "PASS" if not missing and not mismatched else "FAIL"
    return {"status": status, "missing": missing, "mismatched": mismatched, "file_count": len(entries)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    report = verify(args.manifest)
    print(report["status"])
    if report["status"] != "PASS":
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
