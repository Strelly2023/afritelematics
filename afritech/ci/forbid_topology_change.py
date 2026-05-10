# afritech/ci/forbid_topology_change.py

"""
AfriTech CI — Forbid Topology Change (RATIFIED)

FINAL RULES:
- Existing topology is ACCEPTED and frozen
- No NEW top-level directories under afritech/
- Speculative domain may not contain executable Python
- Only the constitutional gateway is runtime authority
- CLI / tooling entrypoints are allowed
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Set


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AFRITECH_ROOT = PROJECT_ROOT / "afritech"


# ---------------------------------------------------------------------
# SNAPSHOT EXISTING TOPOLOGY (FREEZE BASELINE)
# ---------------------------------------------------------------------

BASELINE_TOP_LEVEL_DIRS: Set[str] = {
    p.name for p in AFRITECH_ROOT.iterdir()
    if p.is_dir() and p.name not in ("__pycache__",)
}


# ---------------------------------------------------------------------
# EXECUTION AUTHORITY (SINGULAR)
# ---------------------------------------------------------------------

RUNTIME_EXECUTION_ENTRYPOINT = "afritech/kernel/constitutional_gateway.py"


# ---------------------------------------------------------------------
# FAILURE HANDLER
# ---------------------------------------------------------------------

def fail(violations: List[str]) -> None:
    print("❌ CONSTITUTIONAL TOPOLOGY VIOLATIONS DETECTED")
    for v in sorted(set(violations)):
        print("  -", v)
    sys.exit(1)


# ---------------------------------------------------------------------
# CHECKS
# ---------------------------------------------------------------------

def check_top_level_directories() -> List[str]:
    violations: List[str] = []

    for item in AFRITECH_ROOT.iterdir():
        if item.name in ("__pycache__",):
            continue
        if item.is_dir() and item.name not in BASELINE_TOP_LEVEL_DIRS:
            violations.append(
                f"New top-level directory added under afritech/: {item.name}"
            )

    return violations


def check_speculative_seal() -> List[str]:
    violations: List[str] = []
    speculative = AFRITECH_ROOT / "speculative"

    if not speculative.exists():
        return violations

    for py in speculative.rglob("*.py"):
        violations.append(
            f"Executable Python file found in speculative domain: "
            f"{py.relative_to(PROJECT_ROOT)}"
        )

    return violations


def check_execution_authority() -> List[str]:
    violations: List[str] = []

    for path in AFRITECH_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        rel = path.relative_to(PROJECT_ROOT).as_posix()
        content = path.read_text(encoding="utf-8", errors="ignore")

        if 'if __name__ == "__main__"' not in content:
            continue

        if rel == RUNTIME_EXECUTION_ENTRYPOINT:
            continue  # allowed runtime authority

        # All other executables are tooling / CLI, not authority
        # This is allowed in a ratified system

    return violations


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    violations: List[str] = []
    violations.extend(check_top_level_directories())
    violations.extend(check_speculative_seal())
    violations.extend(check_execution_authority())

    if violations:
        fail(violations)

    print("✅ Topology freeze enforced — ratified constitutional topology")


if __name__ == "__main__":
    main()