"""
AfriTech Formal Proof Checker (Lean)
===================================

Phase‑3 proof presence verifier.

This checker verifies that:
- Each compiled constitutional invariant
- Has a corresponding Lean theorem declaration

This file DOES NOT attempt full proof discharge.
It only verifies proof *existence* and *alignment*.

FAIL‑CLOSED.
"""

from __future__ import annotations

import json
import sys
import re
from pathlib import Path
from typing import Set


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

IR_FILE = (
    ROOT
    / "afritech"
    / "constitution"
    / "compiled"
    / "invariants_ir.json"
)

LEAN_FILE = (
    ROOT
    / "afritech"
    / "formal"
    / "generated"
    / "invariants.lean"
)


# ---------------------------------------------------------------------
# FAILURE
# ---------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"[PROOF CHECK FAILURE] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------
# LOAD COMPILED INVARIANTS
# ---------------------------------------------------------------------

def load_compiled_invariants() -> Set[str]:
    if not IR_FILE.exists():
        fail("Missing compiled invariant IR")

    try:
        data = json.loads(IR_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"Failed to parse invariant IR: {e}")

    invariants = data.get("invariants")

    if not isinstance(invariants, dict):
        fail("Invalid compiled invariant IR format")

    return set(invariants.keys())


# ---------------------------------------------------------------------
# LOAD LEAN THEOREMS
# ---------------------------------------------------------------------

def load_lean_theorems() -> Set[str]:
    if not LEAN_FILE.exists():
        fail("Missing generated Lean invariant file")

    text = LEAN_FILE.read_text(encoding="utf-8")

    theorems: Set[str] = set()

    for line in text.splitlines():
        match = re.match(r"^\s*theorem\s+([a-zA-Z0-9_]+)\b", line)
        if match:
            theorems.add(match.group(1))

    return theorems


# ---------------------------------------------------------------------
# CHECK
# ---------------------------------------------------------------------

def main() -> None:
    compiled = load_compiled_invariants()
    theorems = load_lean_theorems()

    # Expected Lean theorem names are lowercased invariant IDs
    expected = {inv.lower() for inv in compiled}

    missing = expected - theorems
    extra = theorems - expected

    if missing:
        fail(
            "Missing Lean theorem(s) for invariant(s): "
            + ", ".join(sorted(missing))
        )

    # Extra theorems are allowed (helper lemmas, future extensions)

    print("✅ Lean proof presence verified")
    print(f"   Compiled invariants: {len(compiled)}")
    print(f"   Lean theorems found: {len(theorems)}")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()