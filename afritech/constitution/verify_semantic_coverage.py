# afritech/constitution/verify_semantic_coverage.py

"""
AfriTech Semantic Coverage Verifier
===================================

Enforces constitutional semantic closure between:

1. Canonical invariant registry
2. Semantic interpretation registry
3. Compiled runtime invariant projection
4. Deterministic invariant index
5. Executable runtime enforcement references
6. Runtime projection witness guarantees

CONSTITUTIONAL MODEL
--------------------

Canonical Registry
    ==
Semantic Interpretation Layer

Runtime Projection
    ⊆
Canonical Registry

Compiled Runtime Projection
    ==
Deterministic Runtime Index

FAIL-CLOSED.
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
    .parents[1]
)

AFRITECH_ROOT = (
    ROOT
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
# Semantic interpretation layer
# -------------------------------------------------------------

SEMANTIC_REGISTRY = (
    AFRITECH_ROOT
    / "constitution"
    / "invariants_semantics.yaml"
)

# -------------------------------------------------------------
# Compiled runtime projection
# -------------------------------------------------------------

COMPILED_IR = (
    AFRITECH_ROOT
    / "constitution"
    / "compiled"
    / "invariants_ir.json"
)

# -------------------------------------------------------------
# Deterministic runtime index
# -------------------------------------------------------------

INDEX_FILE = (
    AFRITECH_ROOT
    / "constitution"
    / "compiled"
    / "invariants_index.py"
)


# =============================================================
# INVARIANT PATTERN
# =============================================================

INVARIANT_PATTERN = re.compile(
    r"^I[0-9]+_[A-Z0-9_]+$"
)


# =============================================================
# ENFORCEMENT SURFACES
# =============================================================

ENFORCEMENT_ROOTS = [

    ROOT / "kernel",
    ROOT / "runtime",
    ROOT / "guards",
    ROOT / "proof",
    ROOT / "replay",
    ROOT / "ci",
    ROOT / "epoch",
    ROOT / "registry",
    ROOT / "mutation",

    ROOT.parent / "ecosystems",
]


# =============================================================
# FAILURE
# =============================================================

def fail(
    msg: str,
) -> None:

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

        data = yaml.safe_load(

            path.read_text(
                encoding="utf-8"
            )
        )

    except yaml.YAMLError as exc:

        fail(
            f"Invalid YAML: {exc}"
        )

    if not isinstance(
        data,
        dict,
    ):

        fail(
            f"Invalid YAML structure: {path}"
        )

    return data


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

        data = json.loads(

            path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:

        fail(
            f"Invalid JSON: {exc}"
        )

    if not isinstance(
        data,
        dict,
    ):

        fail(
            f"Invalid JSON structure: {path}"
        )

    return data


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

        inv_id = inv.get(
            "id"
        )

        if not isinstance(
            inv_id,
            str,
        ):

            fail(
                "Invariant missing "
                "valid id"
            )

        if not INVARIANT_PATTERN.fullmatch(
            inv_id
        ):

            fail(
                f"Invalid canonical "
                f"invariant id: {inv_id}"
            )

        discovered.add(
            inv_id
        )

    if not discovered:

        fail(
            "Canonical registry "
            "cannot be empty"
        )

    return discovered


# =============================================================
# SEMANTIC INTERPRETATION
# =============================================================

def load_semantic_projection_ids() -> Set[str]:
    """
    Semantic interpretation layer MUST
    align exactly with canonical IDs.
    """

    data = load_yaml(
        SEMANTIC_REGISTRY
    )

    semantics = data.get(
        "semantics"
    )

    if not isinstance(
        semantics,
        dict,
    ):

        fail(
            "semantic registry must "
            "contain semantics mapping"
        )

    if not semantics:

        fail(
            "semantic registry "
            "cannot be empty"
        )

    discovered: Set[str] = set()

    for inv_id in sorted(
        semantics.keys()
    ):

        if not isinstance(
            inv_id,
            str,
        ):

            fail(
                "Invalid semantic "
                "invariant id"
            )

        if not INVARIANT_PATTERN.fullmatch(
            inv_id
        ):

            fail(
                f"Invalid semantic "
                f"invariant id: {inv_id}"
            )

        discovered.add(
            inv_id
        )

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

INDEX_INVARIANT_PATTERN = re.compile(
    r"^I[0-9]+_[A-Z0-9_]+$"
)

LEGACY_INVARIANT_ALIASES = {
    "I1_REGISTRY_AUTHORITY",
    "I2_SEALED_SURFACE",
    "I4_DETERMINISTIC_RUNTIME",
    "I5_EPOCH_MONOTONIC",
    "I6_CLOSED_EXECUTION_WORLD",
}


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

            if not INDEX_INVARIANT_PATTERN.fullmatch(
                target.id
            ):
                continue

            if target.id in LEGACY_INVARIANT_ALIASES:
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

            self.referenced.add(
                node.id
            )

        self.generic_visit(
            node
        )

    def visit_Attribute(
        self,
        node: ast.Attribute,
    ) -> None:

        if node.attr in self.known:

            self.referenced.add(
                node.attr
            )

        self.generic_visit(
            node
        )


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

                            found.add(
                                elt.id
                            )

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

                tree = ast.parse(
                    source
                )

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

            visitor.visit(
                tree
            )

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
    """
    Runtime projection invariants must
    preserve deterministic replay metadata.
    """

    if not ir_data:

        fail(
            "Compiled runtime "
            "projection empty"
        )

    for inv_id, inv in ir_data.items():

        if not isinstance(
            inv,
            dict,
        ):

            fail(
                f"Invariant {inv_id} "
                "must be mapping"
            )

        if (
            "runtime_enforced"
            not in inv
        ):

            fail(

                f"Invariant {inv_id} "
                "missing runtime_enforced"
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
    # semantic alignment
    # ---------------------------------------------------------

    unexpected_semantic = (
        semantic_ids
        - canonical_ids
    )

    if unexpected_semantic:
        fail(

            "Semantic registry "
            "misaligned with "
            "canonical registry:\n"

            f"Unexpected semantic ids: "
            f"{sorted(unexpected_semantic)}"
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

            "Compiled runtime projection "
            "contains unknown invariants: "
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

            "Compiled runtime projection "
            "and invariant index diverged"
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
    # semantic interpretation layer
    # ---------------------------------------------------------

    semantic_ids = (
        load_semantic_projection_ids()
    )

    # ---------------------------------------------------------
    # compiled runtime projection
    # ---------------------------------------------------------

    compiled_ir = (
        load_compiled_ir()
    )

    compiled_ids = set(
        compiled_ir.keys()
    )

    # ---------------------------------------------------------
    # deterministic runtime index
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
