# afritech/proof/law_coverage.py

"""
AfriTech Constitutional Law Coverage
===================================

This module enforces COMPLETE COVERAGE between:

- Declared constitutional invariants (INVARIANTS.yaml)
- Executable constitutional law (profiles + constraints)

RULE:
If an invariant exists without executable enforcement → CI FAIL
If executable enforcement exists without a declared invariant → CI FAIL

This prevents:
- declarative-only law (theater)
- orphaned executable checks
- silent constitutional drift
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Set

import yaml


# ---------------------------------------------------------------------
# PATH CONFIGURATION
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INVARIANTS_FILE = PROJECT_ROOT / "afritech" / "constitution" / "INVARIANTS.yaml"
PROFILES_FILE = PROJECT_ROOT / "afritech" / "proof" / "constitutional_profiles.py"
CONSTRAINTS_FILE = PROJECT_ROOT / "afritech" / "proof" / "executable_constraints.py"


# ---------------------------------------------------------------------
# PARSING UTILITIES
# ---------------------------------------------------------------------

def load_declared_invariants() -> Set[str]:
    """
    Load invariant IDs from INVARIANTS.yaml.

    Expected format:
    invariants:
      - id: I1_REGISTRY_AUTHORITY
      - id: I2_SEALED_EXECUTION_SURFACE
      ...
    """

    if not INVARIANTS_FILE.exists():
        raise FileNotFoundError(
            f"INVARIANTS.yaml not found at {INVARIANTS_FILE}"
        )

    data = yaml.safe_load(INVARIANTS_FILE.read_text())

    invariants = set()

    for entry in data.get("invariants", []):
        inv_id = entry.get("id")
        if inv_id:
            invariants.add(inv_id)

    return invariants


def extract_executed_invariants() -> Set[str]:
    """
    Extract invariant IDs referenced in constitutional profiles
    via ConstitutionalReceipt.from_context(... invariants_executed=...)
    """

    invariants: Set[str] = set()

    for path in (PROFILES_FILE,):
        if not path.exists():
            continue

        text = path.read_text()

        for line in text.splitlines():
            line = line.strip()

            if line.startswith('"I') or line.startswith("'I"):
                token = line.strip('",\'')
                if token.startswith("I"):
                    invariants.add(token)

    return invariants


def extract_atomic_constraints() -> Set[str]:
    """
    Extract invariant IDs enforced by executable constraints.
    This scans for raised ConstitutionalViolation identifiers.
    """

    invariants: Set[str] = set()

    if not CONSTRAINTS_FILE.exists():
        return invariants

    text = CONSTRAINTS_FILE.read_text()

    for line in text.splitlines():
        line = line.strip()
        if line.startswith('"I') or line.startswith("'I"):
            token = line.strip('",\'')
            if token.startswith("I"):
                invariants.add(token)

    return invariants


# ---------------------------------------------------------------------
# COVERAGE CHECK
# ---------------------------------------------------------------------

def main() -> None:
    declared = load_declared_invariants()
    executed = extract_executed_invariants()
    atomic = extract_atomic_constraints()

    missing_execution = declared - executed
    orphaned_execution = executed - declared
    orphaned_atomic = atomic - declared

    failed = False

    if missing_execution:
        failed = True
        print("❌ DECLARED INVARIANTS WITH NO EXECUTABLE COVERAGE:")
        for inv in sorted(missing_execution):
            print("  -", inv)

    if orphaned_execution:
        failed = True
        print("❌ EXECUTABLE INVARIANTS NOT DECLARED IN INVARIANTS.yaml:")
        for inv in sorted(orphaned_execution):
            print("  -", inv)

    if orphaned_atomic:
        failed = True
        print("❌ ATOMIC CONSTRAINTS WITH NO DECLARED INVARIANT:")
        for inv in sorted(orphaned_atomic):
            print("  -", inv)

    if failed:
        sys.exit(1)

    print("✅ Constitutional law coverage verified")
    print(f"   Declared invariants: {len(declared)}")
    print(f"   Executable invariants: {len(executed)}")
    print(f"   Atomic constraints: {len(atomic)}")


if __name__ == "__main__":
    main()