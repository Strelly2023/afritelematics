# afritech/ci/ast_witness_validator.py

"""
AfriTech CI — AST Witness Validator
==================================

This validator enforces the constitutional requirement that
ALL witnesses declared in invariant semantic law are actually
emitted by runtime, replay, or registry code.

Rule:
- If a witness is declared in semantic law but no code path
  references or emits it, CI MUST FAIL.

This closes the final semantic gap:
meaning → enforcement → evidence.

FAIL-CLOSED.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set


# ---------------------------------------------------------------------
# PATHS (CANONICAL)
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SEMANTIC_IR = (
    PROJECT_ROOT
    / "afritech"
    / "constitution"
    / "compiled"
    / "invariants_ir.json"
)

AFRITECH_ROOT = PROJECT_ROOT / "afritech"

def is_legacy_path(path: Path) -> bool:
    return "legacy" in path.parts
# ---------------------------------------------------------------------
# FAILURE HANDLER
# ---------------------------------------------------------------------

def fail(violations: List[str]) -> None:
    print("❌ CONSTITUTIONAL WITNESS VIOLATIONS DETECTED")
    for v in sorted(set(violations)):
        print("  -", v)
    sys.exit(1)


# ---------------------------------------------------------------------
# LOAD DECLARED WITNESSES
# ---------------------------------------------------------------------

def load_declared_witnesses() -> Set[str]:
    if not SEMANTIC_IR.exists():
        fail(f"Missing semantic IR: {SEMANTIC_IR}")

    data = json.loads(SEMANTIC_IR.read_text(encoding="utf-8"))
    invariants = data.get("invariants", {})

    declared: Set[str] = set()

    for inv_id, inv in invariants.items():
        witnesses = inv.get("witnesses", {})
        for domain, spec in witnesses.items():
            required = spec.get("required", [])
            for w in required:
                declared.add(w)

    return declared


# ---------------------------------------------------------------------
# AST VISITOR — WITNESS EMISSION
# ---------------------------------------------------------------------

class WitnessVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.emitted: Set[str] = set()

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """
        Capture dotted attribute access like:
        receipt.surface_validation_hash
        transcript.admitted_surfaces_hash
        """
        full = self._resolve_attribute_chain(node)
        if full:
            self.emitted.add(full)
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        """
        Capture dictionary keys that may correspond to witness names.
        """
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                self.emitted.add(key.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """
        Capture keyword arguments used in calls that may emit witnesses.
        """
        for kw in node.keywords:
            if kw.arg:
                self.emitted.add(kw.arg)
        self.generic_visit(node)

    @staticmethod
    def _resolve_attribute_chain(node: ast.Attribute) -> str | None:
        parts: List[str] = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))

        return None


# ---------------------------------------------------------------------
# SCAN CODEBASE
# ---------------------------------------------------------------------

def scan_codebase() -> Set[str]:
    visitor = WitnessVisitor()

    for path in AFRITECH_ROOT.rglob("*.py"):
        if any(part in (".git", "__pycache__", "venv", ".venv") for part in path.parts):
            continue
        if is_legacy_path(path):
            continue

        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        visitor.visit(tree)

    return visitor.emitted


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    declared = load_declared_witnesses()
    emitted = scan_codebase()

    missing = declared - emitted

    if missing:
        fail(
            [
                f"Witness declared in semantic law but never emitted: {w}"
                for w in sorted(missing)
            ]
        )

    print("✅ AST witness validation passed — all semantic witnesses emitted")
    print(f"     Declared witnesses: {len(declared)}")
    print(f"     Emitted witnesses:  {len(emitted)}")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()