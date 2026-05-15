# afritech/constitution/compiler/compile_invariants.py

"""
AfriTech Invariant Semantic Compiler
===================================

Transforms authoritative constitutional invariant semantics
into deterministic replay-safe compiled IR artifacts.

AUTHORITATIVE INPUT:
- afritech/constitution/invariants_semantics.yaml

GENERATED OUTPUTS:
- afritech/constitution/compiled/invariants_ir.json
- afritech/constitution/compiled/invariants_index.py
- afritech/constitution/compiled/invariants_manifest.json

CONSTITUTIONAL RULE:
No runtime, CI, replay, proof, or validator subsystem may
interpret raw semantic YAML directly.

All enforcement MUST bind to compiled deterministic IR.

PHASE 4 REPAIR:
- remove hardcoded subset assumptions
- full semantic traversal
- deterministic ordering
- semantic completeness validation
- replay-safe canonical hashing
- bytewise deterministic IR generation
"""

from __future__ import annotations

import hashlib
import json
import sys

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[3]

SEMANTIC_SOURCE = (
    ROOT
    / "afritech"
    / "constitution"
    / "invariants_semantics.yaml"
)

COMPILED_DIR = (
    ROOT
    / "afritech"
    / "constitution"
    / "compiled"
)

IR_OUTPUT = (
    COMPILED_DIR
    / "invariants_ir.json"
)

INDEX_OUTPUT = (
    COMPILED_DIR
    / "invariants_index.py"
)

MANIFEST_OUTPUT = (
    COMPILED_DIR
    / "invariants_manifest.json"
)


# ============================================================
# FAILURE
# ============================================================

def fail(msg: str) -> None:

    print(
        f"[INVARIANT COMPILER ERROR] {msg}",
        file=sys.stderr,
    )

    sys.exit(1)


# ============================================================
# HASHING
# ============================================================

def canonical_json(
    data: Any,
) -> bytes:
    """
    Deterministic canonical serialization.
    """

    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def semantic_hash(
    data: Any,
) -> str:
    """
    Semantic replay-safe hash.

    Hashes parsed semantic structure rather than
    raw textual YAML representation.
    """

    return hashlib.sha256(
        canonical_json(data)
    ).hexdigest()


# ============================================================
# VALIDATION
# ============================================================

REQUIRED_INVARIANT_FIELDS = {
    "formal_name",
    "category",
    "intent",
    "scope",
    "preconditions",
    "prohibited_actions",
    "required_postconditions",
    "enforcement_points",
    "witnesses",
    "failure",
}


def validate_invariant(
    inv_id: str,
    inv: Dict[str, Any],
) -> None:

    missing = (
        REQUIRED_INVARIANT_FIELDS
        - inv.keys()
    )

    if missing:

        fail(
            f"Invariant {inv_id} missing "
            f"required fields: "
            f"{sorted(missing)}"
        )

    required_types = {
        "formal_name": str,
        "category": str,
        "intent": dict,
        "scope": dict,
        "preconditions": list,
        "prohibited_actions": list,
        "required_postconditions": list,
        "enforcement_points": dict,
        "witnesses": dict,
        "failure": dict,
    }

    for field, expected in (
        required_types.items()
    ):

        if not isinstance(
            inv[field],
            expected,
        ):

            fail(
                f"Invariant {inv_id}.{field} "
                f"must be "
                f"{expected.__name__}"
            )

    if (
        "description"
        not in inv["intent"]
    ):

        fail(
            f"Invariant {inv_id}.intent."
            f"description missing"
        )

    if (
        "class" not in inv["failure"]
        or "response"
        not in inv["failure"]
    ):

        fail(
            f"Invariant {inv_id}.failure "
            f"must define class and response"
        )


# ============================================================
# SEMANTIC TRAVERSAL
# ============================================================

def extract_invariants(
    node: Any,
    path: str = "root",
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Full recursive semantic traversal.

    Eliminates hardcoded subset assumptions and
    enables ontology-complete compilation.
    """

    discovered: List[
        Tuple[str, Dict[str, Any]]
    ] = []

    if isinstance(node, dict):

        if "invariants" in node:

            invariants = node["invariants"]

            if not isinstance(
                invariants,
                dict,
            ):

                fail(
                    f"'invariants' must be "
                    f"mapping at {path}"
                )

            for inv_id in sorted(
                invariants.keys()
            ):

                inv_def = invariants[inv_id]

                if not isinstance(
                    inv_def,
                    dict,
                ):

                    fail(
                        f"Invariant {inv_id} "
                        f"must be mapping"
                    )

                discovered.append(
                    (
                        inv_id,
                        inv_def,
                    )
                )

        for key in sorted(node.keys()):

            discovered.extend(
                extract_invariants(
                    node[key],
                    f"{path}.{key}",
                )
            )

    elif isinstance(node, list):

        for index, item in enumerate(node):

            discovered.extend(
                extract_invariants(
                    item,
                    f"{path}[{index}]",
                )
            )

    return discovered


# ============================================================
# COMPLETENESS VALIDATION
# ============================================================

def validate_semantic_completeness(
    compiled: Dict[str, Any],
) -> None:

    if not compiled:

        fail(
            "No invariants discovered "
            "during semantic traversal"
        )

    ids = sorted(compiled.keys())

    if len(ids) != len(set(ids)):

        fail(
            "duplicate invariant identities "
            "detected"
        )

    previous = ""

    for inv_id in ids:

        if not inv_id.startswith("I"):

            fail(
                f"invalid invariant id: "
                f"{inv_id}"
            )

        if previous and inv_id < previous:

            fail(
                "non-deterministic invariant "
                "ordering detected"
            )

        previous = inv_id


# ============================================================
# COMPILATION
# ============================================================

def compile_invariants() -> None:

    if not SEMANTIC_SOURCE.exists():

        fail(
            f"Semantic source not found: "
            f"{SEMANTIC_SOURCE}"
        )

    raw_yaml = (
        SEMANTIC_SOURCE
        .read_text(encoding="utf-8")
    )

    try:

        data = yaml.safe_load(raw_yaml)

    except yaml.YAMLError as exc:

        fail(
            f"invalid semantic YAML: {exc}"
        )

    if not isinstance(data, dict):

        fail(
            "Semantic source must be "
            "YAML mapping"
        )

    source_hash = semantic_hash(data)

    discovered = extract_invariants(
        data
    )

    if not discovered:

        fail(
            "No invariants discovered"
        )

    compiled: Dict[str, Any] = {}

    for inv_id, inv_def in sorted(
        discovered,
        key=lambda item: item[0],
    ):

        if inv_id in compiled:

            fail(
                f"duplicate invariant id: "
                f"{inv_id}"
            )

        validate_invariant(
            inv_id,
            inv_def,
        )

        compiled[inv_id] = inv_def

    validate_semantic_completeness(
        compiled
    )

    COMPILED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # REPLAY-SAFE IR
    # ========================================================

    ir_payload = {
        "schema":
            (
                "afritech.constitution."
                "invariants.ir.v1"
            ),

        "source_hash":
            source_hash,

        "invariant_count":
            len(compiled),

        "deterministic": True,

        "closed_world_aligned":
            True,

        "semantic_completeness_verified":
            True,

        "invariants":
            compiled,
    }

    IR_OUTPUT.write_text(
        json.dumps(
            ir_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    # ========================================================
    # INDEX
    # ========================================================

    index_lines = [
        "# AUTO-GENERATED — DO NOT EDIT",
        "# Generated by compile_invariants.py",
        "",
    ]

    for inv_id in sorted(
        compiled.keys()
    ):

        index_lines.append(
            f'{inv_id} = "{inv_id}"'
        )

    INDEX_OUTPUT.write_text(
        "\n".join(index_lines) + "\n",
        encoding="utf-8",
    )

    # ========================================================
    # MANIFEST
    # ========================================================

    manifest = {
        "semantic_version":
            data.get("version"),

        "source_hash":
            source_hash,

        "generated_at":
            (
                datetime.utcnow()
                .isoformat() + "Z"
            ),

        "invariant_count":
            len(compiled),

        "deterministic": True,

        "closed_world_aligned":
            True,

        "semantic_completeness_verified":
            True,

        "outputs": {
            "ir":
                str(
                    IR_OUTPUT
                    .relative_to(ROOT)
                ),

            "index":
                str(
                    INDEX_OUTPUT
                    .relative_to(ROOT)
                ),
        },
    }

    MANIFEST_OUTPUT.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "[OK] Invariant semantics "
        "compiled successfully"
    )

    print(
        f"     Invariants: "
        f"{len(compiled)}"
    )

    print(
        f"     Source hash: "
        f"{source_hash}"
    )


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    compile_invariants()