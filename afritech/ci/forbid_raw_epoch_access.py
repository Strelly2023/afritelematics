# afritech/ci/forbid_raw_epoch_access.py

"""
AfriTech CI — Forbid Raw Epoch Access
====================================

FINAL RULE:
- Operative code MUST NOT access raw epoch artifacts on disk.
- YAML usage itself is NOT forbidden.
- Epoch identifiers (e.g. "EPOCH_6") are ALLOWED as labels.
- Only filesystem/path-level epoch access is forbidden.

This validator is precise and authority-safe.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AFRITECH_ROOT = PROJECT_ROOT / "afritech"

# Operative domains
OPERATIVE_DIRS = {
    "runtime",
    "guards",
    "replay",
    "kernel",
    "proof",
}

# Paths allowed to reference raw epoch artifacts
EXEMPT_PATH_FRAGMENTS = (
    "/epoch/compiler/",
    "/epoch/legacy/",
    "/ci/",
)

# Forbidden ONLY when used as filesystem artifacts
FORBIDDEN_EPOCH_PATH_FRAGMENTS = (
    "registry/epochs/",
    "epoch_registry.yaml",
    "epoch_semantics.yaml",
    "registry/history/epoch_",
)


def fail(violations: List[str]) -> None:
    print("❌ CONSTITUTIONAL EPOCH ACCESS VIOLATIONS DETECTED")
    for v in sorted(set(violations)):
        print("  -", v)
    sys.exit(1)


def is_exempt(path: Path) -> bool:
    return any(fragment in str(path) for fragment in EXEMPT_PATH_FRAGMENTS)


def scan_file(path: Path) -> List[str]:
    violations: List[str] = []

    if is_exempt(path):
        return violations

    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return violations

    for fragment in FORBIDDEN_EPOCH_PATH_FRAGMENTS:
        if fragment in content:
            violations.append(
                f"{path.relative_to(PROJECT_ROOT)} references forbidden epoch filesystem artifact: {fragment}"
            )

    return violations


def main() -> None:
    violations: List[str] = []

    for subdir in OPERATIVE_DIRS:
        base = AFRITECH_ROOT / subdir
        if not base.exists():
            continue

        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue

            violations.extend(scan_file(path))

    if violations:
        fail(violations)

    print("✅ Raw epoch access forbidden — semantic epoch exclusivity enforced")


if __name__ == "__main__":
    main()