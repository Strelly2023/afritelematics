"""
AfriTech Semantic Coverage Verifier
===================================

Enforces constitutional semantic closure between:

1. Compiled invariant semantics
2. Runtime enforcement declarations
3. Concrete code-level invariant references
4. Witness completeness

FAIL-CLOSED.

Coverage is established through either:

A) Explicit module declaration

    ENFORCED_INVARIANTS = { ... }

or

B) Direct invariant symbol references in executable code
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Dict, Set


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

COMPILED_DIR = ROOT / "afritech" / "constitution" / "compiled"

IR_FILE = COMPILED_DIR / "invariants_ir.json"
INDEX_FILE = COMPILED_DIR / "invariants_index.py"


# ---------------------------------------------------------------------
# ENFORCEMENT SURFACES
# ---------------------------------------------------------------------

ENFORCEMENT_ROOTS = [
    ROOT / "afritech" / "kernel",
    ROOT / "afritech" / "runtime",
    ROOT / "afritech" / "guards",
    ROOT / "afritech" / "proof",
    ROOT / "afritech" / "replay",
    ROOT / "afritech" / "ci",
    ROOT / "afritech" / "epoch",
    ROOT / "afritech" / "registry",
    ROOT / "afritech" / "mutation",
]


# ---------------------------------------------------------------------
# FAILURE
# ---------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"[SEMANTIC COVERAGE VIOLATION] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------
# LOAD SEMANTIC IR
# ---------------------------------------------------------------------

def load_semantic_ir() -> Dict:
    if not IR_FILE.exists():
        fail(f"Missing compiled invariant IR: {IR_FILE}")

    data = json.loads(IR_FILE.read_text(encoding="utf-8"))

    invariants = data.get("invariants")

    if not isinstance(invariants, dict):
        fail("Invalid invariant IR structure")

    return invariants


# ---------------------------------------------------------------------
# LOAD INDEX SYMBOLS
# ---------------------------------------------------------------------

def load_index_symbols() -> Set[str]:
    if not INDEX_FILE.exists():
        fail(f"Missing invariant index: {INDEX_FILE}")

    tree = ast.parse(INDEX_FILE.read_text(encoding="utf-8"))

    symbols: Set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)

    return symbols


# ---------------------------------------------------------------------
# INVARIANT REFERENCE VISITOR
# ---------------------------------------------------------------------

class InvariantReferenceVisitor(ast.NodeVisitor):
    def __init__(self, known: Set[str]) -> None:
        self.known = known
        self.referenced: Set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self.known:
            self.referenced.add(node.id)

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in self.known:
            self.referenced.add(node.attr)

        self.generic_visit(node)


# ---------------------------------------------------------------------
# EXPLICIT ENFORCEMENT DECLARATION EXTRACTION
# ---------------------------------------------------------------------

def extract_declared_invariants(
    tree: ast.AST,
    known: Set[str],
) -> Set[str]:
    """
    Extract:

        ENFORCED_INVARIANTS = {I1, I2}

    declarations.
    """

    found: Set[str] = set()

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id == "ENFORCED_INVARIANTS"
            ):
                if isinstance(node.value, (ast.Set, ast.Tuple, ast.List)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Name):
                            if elt.id in known:
                                found.add(elt.id)

    return found


# ---------------------------------------------------------------------
# SCAN ENFORCEMENT CODE
# ---------------------------------------------------------------------

def scan_enforcement_references(
    known_invariants: Set[str],
) -> Set[str]:
    referenced: Set[str] = set()

    for root in ENFORCEMENT_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*.py"):
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except Exception:
                continue

            # ---------------------------------------------
            # Explicit declarations
            # ---------------------------------------------

            referenced |= extract_declared_invariants(
                tree,
                known_invariants,
            )

            # ---------------------------------------------
            # AST symbol references
            # ---------------------------------------------

            visitor = InvariantReferenceVisitor(known_invariants)
            visitor.visit(tree)

            referenced |= visitor.referenced

    return referenced


# ---------------------------------------------------------------------
# WITNESS VALIDATION
# ---------------------------------------------------------------------

def verify_witness_structure(ir_data: Dict) -> None:
    for inv_id, inv in ir_data.items():
        witnesses = inv.get("witnesses")

        if not isinstance(witnesses, dict):
            fail(f"Invariant {inv_id} missing witnesses block")

        for domain, spec in witnesses.items():
            required = spec.get("required")

            if not isinstance(required, list) or not required:
                fail(
                    f"Invariant {inv_id} "
                    f"witnesses.{domain}.required "
                    "must be a non-empty list"
                )


# ---------------------------------------------------------------------
# VERIFY CONSISTENCY
# ---------------------------------------------------------------------

def verify_symbol_consistency(
    semantic_ids: Set[str],
    index_symbols: Set[str],
) -> None:
    if semantic_ids != index_symbols:
        fail(
            "Semantic invariants and index symbols differ:\n"
            f"semantic={sorted(semantic_ids)}\n"
            f"index={sorted(index_symbols)}"
        )


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    semantic_ir = load_semantic_ir()

    semantic_ids = set(semantic_ir.keys())
    index_symbols = load_index_symbols()

    verify_symbol_consistency(
        semantic_ids,
        index_symbols,
    )

    enforcement_refs = scan_enforcement_references(
        semantic_ids
    )

    orphaned = enforcement_refs - semantic_ids
    unenforced = semantic_ids - enforcement_refs

    if orphaned:
        fail(
            "Enforcement references undefined invariants: "
            f"{sorted(orphaned)}"
        )

    if unenforced:
        fail(
            "Semantic invariants never enforced: "
            f"{sorted(unenforced)}"
        )

    verify_witness_structure(semantic_ir)

    print("✅ Semantic coverage verified")
    print(f"   Invariants: {len(semantic_ids)}")
    print(f"   Enforced:   {len(enforcement_refs)}")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()