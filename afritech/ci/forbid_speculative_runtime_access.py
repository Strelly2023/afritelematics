# afritech/ci/forbid_speculative_runtime_access.py

"""
AfriTech CI — Forbid Speculative Runtime Access
==============================================

This CI validator enforces the constitutional separation between:

- OPERATIVE code (runtime, kernel, guards, replay, proof, epoch, registry)
- SPECULATIVE code (afritech/speculative/*)

RULE (HARD LAW):
No operative code may import, reference, or depend on speculative artifacts.

Speculative artifacts are:
- non-operative
- non-authoritative
- non-replayable
- non-enforced

Any import from afritech.speculative into operative code
constitutes a CONSTITUTIONAL VIOLATION.

FAIL-CLOSED.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AFRITECH_ROOT = PROJECT_ROOT / "afritech"


# ---------------------------------------------------------------------
# OPERATIVE DOMAINS (SUBJECT TO ENFORCEMENT)
# ---------------------------------------------------------------------

OPERATIVE_DIRS = [
    "kernel",
    "runtime",
    "guards",
    "replay",
    "proof",
    "epoch",
    "registry",
    "state",
    "trace",
    "ci",
]

SPECULATIVE_PREFIX = "afritech.speculative"


# ---------------------------------------------------------------------
# FAILURE HANDLER
# ---------------------------------------------------------------------

def fail(violations: List[str]) -> None:
    print("❌ CONSTITUTIONAL SPECULATIVE ACCESS VIOLATIONS DETECTED")
    for v in sorted(set(violations)):
        print("  -", v)
    sys.exit(1)


# ---------------------------------------------------------------------
# PATH → MODULE RESOLUTION
# ---------------------------------------------------------------------

def module_path_from_file(path: Path) -> str:
    rel = path.relative_to(PROJECT_ROOT)
    return ".".join(rel.with_suffix("").parts)


# ---------------------------------------------------------------------
# AST SCAN
# ---------------------------------------------------------------------

def scan_file(path: Path) -> List[str]:
    violations: List[str] = []

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return violations  # syntax errors not our concern

    importer = module_path_from_file(path)

    for node in ast.walk(tree):

        # import afritech.speculative.x
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(SPECULATIVE_PREFIX):
                    violations.append(
                        f"{importer} illegally imports speculative module "
                        f"{alias.name}"
                    )

        # from afritech.speculative.x import y
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(SPECULATIVE_PREFIX):
                violations.append(
                    f"{importer} illegally imports from speculative module "
                    f"{node.module}"
                )

    return violations


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    violations: List[str] = []

    for subdir in OPERATIVE_DIRS:
        base = AFRITECH_ROOT / subdir
        if not base.exists():
            continue

        for path in base.rglob("*.py"):
            if any(part in ("__pycache__", ".git", ".venv", "venv") for part in path.parts):
                continue

            violations.extend(scan_file(path))

    if violations:
        fail(violations)

    print("✅ Speculative runtime access forbidden — constitutional separation enforced")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()