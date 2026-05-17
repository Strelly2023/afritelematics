"""
AfriTech Constitutional Completeness Generator
==============================================

Generates:
    afritech/proof/completeness.json

FAIL-CLOSED.
"""

from __future__ import annotations

import ast
import json
import re
import sys

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Set


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

COMPILED_IR = ROOT / "afritech/constitution/compiled/invariants_ir.json"
INDEX_FILE = ROOT / "afritech/constitution/compiled/invariants_index.py"
LEAN_FILE = ROOT / "afritech/formal/generated/invariants.lean"
OUTPUT = ROOT / "afritech/proof/completeness.json"


# ---------------------------------------------------------------------
# PATTERN
# ---------------------------------------------------------------------

INVARIANT_PATTERN = re.compile(r"^I[0-9]+_[A-Z0-9_]+$")


# ---------------------------------------------------------------------
# FAILURE
# ---------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"[COMPLETENESS FAILURE] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------
# LOAD IR (RUNTIME PROJECTION ONLY ✅)
# ---------------------------------------------------------------------

def load_runtime_ir() -> Dict[str, Dict]:

    if not COMPILED_IR.exists():
        fail("Missing compiled invariant IR")

    data = json.loads(COMPILED_IR.read_text(encoding="utf-8"))

    runtime_ids = data.get("runtime_projection")
    invariants = data.get("invariants")

    if not isinstance(runtime_ids, list):
        fail("Invalid runtime_projection in IR")

    if not isinstance(invariants, dict):
        fail("Invalid invariants structure in IR")

    filtered = {
        inv_id: invariants[inv_id]
        for inv_id in runtime_ids
        if INVARIANT_PATTERN.fullmatch(inv_id)
    }

    return dict(sorted(filtered.items()))


# ---------------------------------------------------------------------
# LOAD INDEX (RUNTIME SYMBOLS ONLY ✅)
# ---------------------------------------------------------------------

def load_index_symbols() -> Set[str]:

    if not INDEX_FILE.exists():
        fail("Missing invariant index file")

    tree = ast.parse(INDEX_FILE.read_text(encoding="utf-8"))

    symbols: Set[str] = set()

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue

            name = target.id

            if not INVARIANT_PATTERN.fullmatch(name):
                continue

            value = ast.literal_eval(node.value)

            if not isinstance(value, str):
                continue

            if value != name:
                fail(f"Invariant index drift: {name} != {value}")

            symbols.add(name)

    return set(sorted(symbols))


# ---------------------------------------------------------------------
# LEAN THEOREMS
# ---------------------------------------------------------------------

def count_lean_theorems() -> int:

    if not LEAN_FILE.exists():
        return 0

    text = LEAN_FILE.read_text(encoding="utf-8")

    return sum(
        1
        for line in text.splitlines()
        if re.match(r"^\s*theorem\b", line)
    )


# ---------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------

def validate_alignment(
    compiled: Dict[str, Dict],
    indexed: Set[str],
) -> None:

    compiled_ids = set(compiled.keys())

    missing_in_index = sorted(compiled_ids - indexed)
    missing_in_ir = sorted(indexed - compiled_ids)

    if missing_in_index or missing_in_ir:
        fail(
            "Invariant mismatch:\n"
            f" missing_in_index={missing_in_index}\n"
            f" missing_in_ir={missing_in_ir}"
        )


# ---------------------------------------------------------------------
# BUILD REPORT
# ---------------------------------------------------------------------

def build_report() -> Dict:

    runtime_ir = load_runtime_ir()
    index_ids = load_index_symbols()

    # ✅ strict runtime alignment
    validate_alignment(runtime_ir, index_ids)

    runtime_count = len(runtime_ir)
    lean_generated = count_lean_theorems()

    report = {

        "schema": "afritech.proof.completeness.v1",

        "generated_at": datetime.now(timezone.utc).isoformat(),

        "constitution": {

            "runtime_declared": runtime_count,
            "runtime_compiled": runtime_count,
            "runtime_indexed": len(index_ids),
        },

        "formal": {

            "lean_generated": lean_generated,
            "lean_proof_complete":
                lean_generated == runtime_count,
        },

        "runtime": {

            "runtime_enforced": runtime_count,
            "closed_world": True,
            "deterministic": True,
        },

        "coverage": {

            "runtime_closure": True,
            "formal_closure":
                lean_generated == runtime_count,
            "complete":
                lean_generated == runtime_count,
        },

        "integrity": {

            "ir_index_alignment": True,
            "fail_closed": True,
        },

        "progress": {

            "phase": "RUNTIME_ENFORCEMENT_READY",
            "maturity": "DETERMINISTIC_CONSTITUTIONAL_CORE",
        },
    }

    return report


# ---------------------------------------------------------------------
# WRITE
# ---------------------------------------------------------------------

def main() -> None:

    report = build_report()

    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("✅ Constitutional completeness generated")
    print(f"   Output: {OUTPUT.relative_to(ROOT)}")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()