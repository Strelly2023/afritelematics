"""
AfriTech Semantic Coverage Verifier
===================================

Enforces constitutional semantic closure between:

1. Canonical invariant registry
2. Semantic runtime enforcement registry
3. Compiled runtime invariant IR
4. Deterministic runtime index
5. Concrete executable enforcement references
6. Witness completeness

FAIL-CLOSED.

Coverage is established through either:

A) Explicit module declaration

    ENFORCED_INVARIANTS = { ... }

or

B) Direct invariant symbol references
   in executable runtime code.

CONSTITUTIONAL MODEL:

Canonical Registry
    ↓
Semantic Runtime Projection
    ↓
Compiled Runtime Projection
    ↓
Executable Enforcement Surfaces
"""

from __future__ import annotations

import ast
import json
import re
import sys
import yaml

from pathlib import Path
from typing import Dict, Set, Any


# =============================================================
# PATHS
# =============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

AFRITECH_ROOT = (
    ROOT / "afritech"
)

# -------------------------------------------------------------
# Canonical registry
# -------------------------------------------------------------

CANONICAL_REGISTRY = (
    AFRITECH_ROOT
    / "constitution"
    / "INVARIANTS.yaml"
)

# -------------------------------------------------------------
# Semantic runtime enforcement registry
# -------------------------------------------------------------

SEMANTIC_REGISTRY = (
    AFRITECH_ROOT
    / "constitution"
    / "invariants_semantics.yaml"
)

# -------------------------------------------------------------
# Compiled IR
# -------------------------------------------------------------

COMPILED_IR = (
    AFRITECH_ROOT
    / "constitution"
    / "compiled"
    / "invariants_ir.json"
)

# -------------------------------------------------------------
# Deterministic invariant index
# -------------------------------------------------------------

INDEX_FILE = (
    AFRITECH_ROOT
    / "constitution"
    / "compiled"
    / "invariants_index.py"
)


# =============================================================
# ENFORCEMENT SURFACES
# =============================================================

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

    ROOT / "ecosystems",
]


# =============================================================
# FAILURE
# =============================================================

def fail(msg: str) -> None:

    print(
        f"[SEMANTIC COVERAGE VIOLATION] "
        f"{msg}",
        file=sys.stderr,
    )

    sys.exit(1)


# =============================================================
# YAML LOADER
# =============================================================

def load_yaml(
    path: Path,
) -> Dict[str, Any]:

    if not path.exists():

        fail(
            f"Missing YAML source: {path}"
        )

    try:

        return yaml.safe_load(
            path.read_text(
                encoding="utf-8"
            )
        )

    except yaml.YAMLError as exc:

        fail(
            f"Invalid YAML: {exc}"
        )


# =============================================================
# JSON LOADER
# =============================================================

def load_json(
    path: Path,
) -> Dict[str, Any]:

    if not path.exists():

        fail(
            f"Missing JSON source: {path}"
        )

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:

        fail(
            f"Invalid JSON: {exc}"
        )


# =============================================================
# CANONICAL REGISTRY
# =============================================================

def load_canonical_ids() -> Set[str]:

    data = load_yaml(
        CANONICAL_REGISTRY
    )

    invariants = data.get(
        "invariants"
    )

    if not isinstance(
        invariants,
        list,
    ):

        fail(
            "Canonical registry "
            "must contain invariants list"
        )

    discovered: Set[str] = set()

    for inv in invariants:

        if not isinstance(
            inv,
            dict,
        ):

            fail(
                "Invariant entry "
                "must be mapping"
            )

        inv_id = inv.get("id")

        if not isinstance(
            inv_id,
            str,
        ):

            fail(
                "Invariant missing "
                "valid id"
            )

        discovered.add(inv_id)

    return discovered


# =============================================================
# SEMANTIC PROJECTION
# =============================================================

def load_semantic_projection_ids() -> Set[str]:

    data = load_yaml(
        SEMANTIC_REGISTRY
    )

    semantic_root = data.get(
        "semantic_enforcement"
    )

    if not isinstance(
        semantic_root,
        dict,
    ):

        fail(
            "semantic_enforcement "
            "must be mapping"
        )

    discovered: Set[str] = set()

    for _, spec in semantic_root.items():

        if not isinstance(
            spec,
            dict,
        ):

            continue

        enforced = spec.get(
            "enforced_invariants",
            []
        )

        if not isinstance(
            enforced,
            list,
        ):

            fail(
                "enforced_invariants "
                "must be list"
            )

        for inv_id in enforced:

            if not isinstance(
                inv_id,
                str,
            ):

                fail(
                    "Invalid enforced "
                    "invariant id"
                )

            discovered.add(inv_id)

    return discovered


# =============================================================
# COMPILED IR
# =============================================================

def load_compiled_ir() -> Dict[str, Any]:

    data = load_json(
        COMPILED_IR
    )

    invariants = data.get(
        "invariants"
    )

    if not isinstance(
        invariants,
        dict,
    ):

        fail(
            "Compiled IR invariants "
            "must be mapping"
        )

    return invariants


# =============================================================
# INDEX SYMBOLS
# =============================================================


# =============================================================
# INDEX SYMBOLS
# =============================================================

INDEX_INVARIANT_PATTERN = re.compile(
    r"^I[0-9]+_[A-Z0-9_]+$"
)


def load_index_symbols() -> Set[str]:

    if not INDEX_FILE.exists():

        fail(
            f"Missing invariant index: "
            f"{INDEX_FILE}"
        )

    tree = ast.parse(
        INDEX_FILE.read_text(
            encoding="utf-8"
        )
    )

    symbols: Set[str] = set()

    for node in tree.body:

        if not isinstance(
            node,
            ast.Assign,
        ):
            continue

        for target in node.targets:

            if not isinstance(
                target,
                ast.Name,
            ):
                continue

            # -------------------------------------------------
            # strict invariant symbol filtering
            # -------------------------------------------------

            if not INDEX_INVARIANT_PATTERN.fullmatch(
                target.id
            ):
                continue

            symbols.add(
                target.id
            )

    return symbols

# =============================================================
# AST REFERENCE VISITOR
# =============================================================

class InvariantReferenceVisitor(
    ast.NodeVisitor
):

    def __init__(
        self,
        known: Set[str],
    ) -> None:

        self.known = known

        self.referenced: Set[str] = set()

    def visit_Name(
        self,
        node: ast.Name,
    ) -> None:

        if node.id in self.known:
            self.referenced.add(node.id)

        self.generic_visit(node)

    def visit_Attribute(
        self,
        node: ast.Attribute,
    ) -> None:

        if node.attr in self.known:
            self.referenced.add(node.attr)

        self.generic_visit(node)


# =============================================================
# EXPLICIT DECLARATION EXTRACTION
# =============================================================

def extract_declared_invariants(
    tree: ast.AST,
    known: Set[str],
) -> Set[str]:

    found: Set[str] = set()

    for node in tree.body:

        if not isinstance(
            node,
            ast.Assign,
        ):
            continue

        for target in node.targets:

            if (
                isinstance(
                    target,
                    ast.Name,
                )
                and target.id
                == "ENFORCED_INVARIANTS"
            ):

                if isinstance(
                    node.value,
                    (
                        ast.Set,
                        ast.Tuple,
                        ast.List,
                    ),
                ):

                    for elt in node.value.elts:

                        if (
                            isinstance(
                                elt,
                                ast.Name,
                            )
                            and elt.id in known
                        ):

                            found.add(elt.id)

    return found


# =============================================================
# ENFORCEMENT SCAN
# =============================================================

def scan_enforcement_references(
    known_invariants: Set[str],
) -> Set[str]:

    referenced: Set[str] = set()

    for root in ENFORCEMENT_ROOTS:

        if not root.exists():
            continue

        for path in root.rglob("*.py"):

            try:

                source = path.read_text(
                    encoding="utf-8"
                )

                tree = ast.parse(source)

            except Exception:
                continue

            referenced |= (
                extract_declared_invariants(
                    tree,
                    known_invariants,
                )
            )

            visitor = (
                InvariantReferenceVisitor(
                    known_invariants
                )
            )

            visitor.visit(tree)

            referenced |= (
                visitor.referenced
            )

    return referenced


# =============================================================
# WITNESS VALIDATION
# =============================================================

def verify_witness_structure(
    ir_data: Dict[str, Any],
) -> None:

    for inv_id, inv in ir_data.items():

        required = inv.get(
            "required_witnesses"
        )

        if not isinstance(
            required,
            list,
        ):

            fail(
                f"Invariant {inv_id} "
                "missing required_witnesses"
            )

        if not required:

            fail(
                f"Invariant {inv_id} "
                "required_witnesses empty"
            )


# =============================================================
# PROJECTION CONSISTENCY
# =============================================================

def verify_projection_consistency(
    canonical_ids: Set[str],
    semantic_ids: Set[str],
    compiled_ids: Set[str],
    index_ids: Set[str],
) -> None:

    # ---------------------------------------------------------
    # semantic subset
    # ---------------------------------------------------------

    semantic_unknown = (
        semantic_ids
        - canonical_ids
    )

    if semantic_unknown:

        fail(
            "Semantic projection contains "
            "unknown invariants: "
            f"{sorted(semantic_unknown)}"
        )

    # ---------------------------------------------------------
    # compiled subset
    # ---------------------------------------------------------

    compiled_unknown = (
        compiled_ids
        - canonical_ids
    )

    if compiled_unknown:

        fail(
            "Compiled IR contains "
            "unknown invariants: "
            f"{sorted(compiled_unknown)}"
        )

    # ---------------------------------------------------------
    # index subset
    # ---------------------------------------------------------

    index_unknown = (
        index_ids
        - canonical_ids
    )

    if index_unknown:

        fail(
            "Invariant index contains "
            "unknown invariants: "
            f"{sorted(index_unknown)}"
        )

    # ---------------------------------------------------------
    # compiled/index parity
    # ---------------------------------------------------------

    if compiled_ids != index_ids:

        fail(
            "Compiled IR and invariant "
            "index diverged"
        )


# =============================================================
# MAIN
# =============================================================

def main() -> None:

    # ---------------------------------------------------------
    # canonical registry
    # ---------------------------------------------------------

    canonical_ids = (
        load_canonical_ids()
    )

    # ---------------------------------------------------------
    # semantic projection
    # ---------------------------------------------------------

    semantic_ids = (
        load_semantic_projection_ids()
    )

    # ---------------------------------------------------------
    # compiled runtime IR
    # ---------------------------------------------------------

    compiled_ir = (
        load_compiled_ir()
    )

    compiled_ids = set(
        compiled_ir.keys()
    )

    # ---------------------------------------------------------
    # deterministic index
    # ---------------------------------------------------------

    index_ids = (
        load_index_symbols()
    )

    # ---------------------------------------------------------
    # projection consistency
    # ---------------------------------------------------------

    verify_projection_consistency(
        canonical_ids,
        semantic_ids,
        compiled_ids,
        index_ids,
    )

    # ---------------------------------------------------------
    # runtime enforcement references
    # ---------------------------------------------------------

    enforcement_refs = (
        scan_enforcement_references(
            compiled_ids
        )
    )

    unenforced = (
        compiled_ids
        - enforcement_refs
    )

    if unenforced:

        fail(
            "Compiled runtime invariants "
            "never enforced: "
            f"{sorted(unenforced)}"
        )

    # ---------------------------------------------------------
    # witness verification
    # ---------------------------------------------------------

    verify_witness_structure(
        compiled_ir
    )

    # =========================================================
    # SUCCESS
    # =========================================================

    print(
        "✅ Semantic coverage verified"
    )

    print(
        "✅ Canonical registry alignment verified"
    )

    print(
        "✅ Semantic runtime projection verified"
    )

    print(
        "✅ Runtime enforcement references verified"
    )

    print(
        "✅ Witness completeness verified"
    )

    print(
        f"   Canonical invariants: "
        f"{len(canonical_ids)}"
    )

    print(
        f"   Runtime projection:   "
        f"{len(compiled_ids)}"
    )

    print(
        f"   Enforced runtime:     "
        f"{len(enforcement_refs)}"
    )


# =============================================================
# ENTRYPOINT
# =============================================================

if __name__ == "__main__":

    main()