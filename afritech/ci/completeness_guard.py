"""
AfriTech CI — Constitutional Completeness Guard
===============================================

Enforces minimum constitutional completeness guarantees.

This guard consumes ONLY the mechanically generated artifact:

    afritech/proof/completeness.json

RULE (FAIL-CLOSED):
- compiled invariants must not exceed semantic definitions
- runtime enforcement must cover all compiled invariants
- Lean generation must keep pace with compilation

This guard prevents constitutional regression.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict


# ---------------------------------------------------------------------
# PATH
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

COMPLETENESS = (
    ROOT
    / "afritech"
    / "proof"
    / "completeness.json"
)


# ---------------------------------------------------------------------
# FAILURE
# ---------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"[COMPLETENESS GUARD FAILURE] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------

def load_completeness() -> Dict:
    if not COMPLETENESS.exists():
        fail("Missing completeness.json — generator must run first")

    try:
        data = json.loads(COMPLETENESS.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"Invalid completeness.json: {e}")

    return data


# ---------------------------------------------------------------------
# VALIDATION RULES
# ---------------------------------------------------------------------

def validate(data: Dict) -> None:
    constitution = data.get("constitution", {})
    formal = data.get("formal", {})
    runtime = data.get("runtime", {})
    coverage = data.get("coverage", {})

    declared = constitution.get("declared")
    defined = constitution.get("semantically_defined")
    compiled = constitution.get("compiled")

    lean_generated = formal.get("lean_generated")
    runtime_enforced = runtime.get("runtime_enforced")

    # -------------------------------------------------------------
    # HARD INVARIANT RELATIONS
    # -------------------------------------------------------------

    if defined > declared:
        fail(
            f"Semantically defined invariants ({defined}) "
            f"exceed declared ({declared})"
        )

    if compiled > defined:
        fail(
            f"Compiled invariants ({compiled}) "
            f"exceed semantically defined ({defined})"
        )

    if runtime_enforced < compiled:
        fail(
            f"Runtime enforces {runtime_enforced} invariants "
            f"but {compiled} are compiled"
        )

    if lean_generated < compiled:
        fail(
            f"Lean artifacts generated ({lean_generated}) "
            f"lag behind compiled invariants ({compiled})"
        )

    # -------------------------------------------------------------
    # CLOSURE FLAGS MUST MATCH COUNTS
    # -------------------------------------------------------------

    if compiled == defined and not coverage.get("semantic_closure"):
        fail("Semantic closure flag is false but counts indicate closure")

    if runtime_enforced == compiled and not coverage.get("runtime_closure"):
        fail("Runtime closure flag is false but enforcement is complete")

    # -------------------------------------------------------------
    # PASS
    # -------------------------------------------------------------

    print("✅ Constitutional completeness guard passed")
    print(
        f"   Declared={declared}, Defined={defined}, "
        f"Compiled={compiled}, Runtime={runtime_enforced}, "
        f"Lean={lean_generated}"
    )


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

def main() -> None:
    data = load_completeness()
    validate(data)


if __name__ == "__main__":
    main()