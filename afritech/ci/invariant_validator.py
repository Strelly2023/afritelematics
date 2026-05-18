from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

CANONICAL = ROOT / "afritech/constitution/INVARIANTS.yaml"
SEMANTIC = ROOT / "afritech/constitution/invariants_semantics.yaml"
IR_FILE = ROOT / "afritech/constitution/compiled/invariants_ir.json"
INDEX_FILE = ROOT / "afritech/constitution/compiled/invariants_index.py"


# ============================================================
# FAILURE
# ============================================================

def fail(msg: str) -> None:
    raise RuntimeError(msg)


# ============================================================
# LOADERS
# ============================================================

def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        fail(f"Missing file: {path}")

    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"Invalid YAML: {exc}")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        fail(f"Missing file: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: {exc}")


# ============================================================
# SORTING
# ============================================================

ID_PATTERN = re.compile(r"^I(\d+)_")


def sort_key(inv_id: str):
    match = ID_PATTERN.match(inv_id)
    return (int(match.group(1)) if match else 9999, inv_id)


def invariant_sort_key(inv_id: str):
    return sort_key(inv_id)


# ============================================================
# LOADERS
# ============================================================

def load_canonical_ids() -> List[str]:
    data = load_yaml(CANONICAL)

    invs = data.get("invariants")
    if not isinstance(invs, list):
        fail("Canonical invariants must be list")

    return sorted(
        [inv["id"] for inv in invs],
        key=sort_key,
    )


def load_semantic_ids() -> List[str]:
    data = load_yaml(SEMANTIC)

    semantics = data.get("semantics")
    if not isinstance(semantics, dict):
        fail("Semantic registry must be mapping")

    return sorted(semantics.keys(), key=sort_key)


def load_ir_ids() -> List[str]:
    ir = load_json(IR_FILE)

    runtime = ir.get("runtime_projection")
    if not isinstance(runtime, list):
        fail("IR runtime_projection must be list")

    return sorted(runtime, key=sort_key)


INDEX_PATTERN = re.compile(r"I\d+_[A-Z0-9_]+")
LEGACY_INVARIANT_ALIASES = {
    "I1_REGISTRY_AUTHORITY",
    "I2_SEALED_SURFACE",
    "I4_DETERMINISTIC_RUNTIME",
    "I5_EPOCH_MONOTONIC",
    "I6_CLOSED_EXECUTION_WORLD",
}


def load_index_ids() -> List[str]:
    return parse_index_ids(INDEX_FILE)


def parse_index_ids(path: Path) -> List[str]:
    if not path.exists():
        fail("Missing invariant index")

    ids: List[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if "=" not in line:
            continue

        left = line.split("=", 1)[0].strip()

        if INDEX_PATTERN.fullmatch(left) and left not in LEGACY_INVARIANT_ALIASES:
            ids.append(left)

    return sorted(set(ids), key=sort_key)


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_no_duplicates(ids: List[str], name: str):
    seen: Set[str] = set()
    for i in ids:
        if i in seen:
            fail(f"{name} duplicate detected: {i}")
        seen.add(i)


def validate_order(ids: List[str], name: str):
    if ids != sorted(ids, key=sort_key):
        fail(f"{name} ordering not deterministic")


def validate_deterministic_ordering(ids: List[str]) -> None:
    validate_order(ids, "invariants")


def validate_subset(parent: Set[str], child: Set[str], name: str):
    diff = child - parent
    if diff:
        fail(f"{name} contains unknown invariants: {sorted(diff)}")


def validate_runtime_projection(
    registry: Set[str],
    projection: Set[str],
    name: str,
) -> None:
    validate_subset(registry, projection, name)


# ============================================================
# IR STRUCTURE VALIDATION ✅ FINAL
# ============================================================

FORBIDDEN_TERMS = {
    "intent",
    "duplicate",
    "equivalence",
    "identity",
    "retry",
    "canonicalization",
}


def validate_ir_structure(ir: Dict[str, Any]) -> None:

    invs = ir.get("invariants")

    if not isinstance(invs, dict):
        fail("IR invariants must be mapping")

    for inv_id, inv in invs.items():

        if not isinstance(inv, dict):
            fail(f"{inv_id} invalid structure")

        # ✅ FINAL REQUIRED FIELDS (MATCH COMPILER + YAML)
        required = [
            "category",
            "constitutional_assertion",
            "runtime_scope",
            "enforcement",
        ]

        for field in required:
            if field not in inv:
                fail(f"{inv_id} missing field: {field}")

        # ✅ enforcement must match YAML structure
        if not isinstance(inv.get("enforcement"), dict):
            fail(f"{inv_id} enforcement must be mapping")

        # ✅ runtime_scope validation
        valid_scopes = {"PRE", "DURING", "POST", "REPLAY", "GOVERNANCE"}
        if inv.get("runtime_scope") not in valid_scopes:
            fail(f"{inv_id} invalid runtime_scope: {inv.get('runtime_scope')}")

        # ✅ semantic leakage protection
        text = json.dumps(inv).lower()
        for term in FORBIDDEN_TERMS:
            if term in text:
                fail(f"{inv_id} contains forbidden semantic term: {term}")


# ============================================================
# MAIN VALIDATION
# ============================================================

def run() -> None:

    canonical_ids = load_canonical_ids()
    semantic_ids = load_semantic_ids()
    ir_ids = load_ir_ids()
    index_ids = load_index_ids()

    ir = load_json(IR_FILE)
    validate_ir_structure(ir)

    cs = set(canonical_ids)
    ss = set(semantic_ids)
    rs = set(ir_ids)
    ix = set(index_ids)

    # --------------------------------------------------------
    # BASIC
    # --------------------------------------------------------

    validate_no_duplicates(canonical_ids, "canonical")
    validate_no_duplicates(semantic_ids, "semantic")
    validate_no_duplicates(ir_ids, "ir")
    validate_no_duplicates(index_ids, "index")

    validate_order(canonical_ids, "canonical")
    validate_order(semantic_ids, "semantic")
    validate_order(ir_ids, "ir")
    validate_order(index_ids, "index")

    # --------------------------------------------------------
    # ALIGNMENT
    # --------------------------------------------------------

    validate_subset(cs, rs, "IR")
    validate_subset(cs, ix, "Index")
    validate_subset(cs, ss, "Semantic")

    # ✅ semantic must cover runtime invariants
    validate_subset(set(semantic_ids), rs, "Semantic coverage")

    # --------------------------------------------------------
    # IR ↔ INDEX LOCK
    # --------------------------------------------------------

    if ir_ids != index_ids:
        fail(
            f"IR/index mismatch\n"
            f"IR: {ir_ids}\n"
            f"INDEX: {index_ids}"
        )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    print("✅ Invariant validation PASSED")
    print("✅ Canonical registry verified")
    print("✅ Semantic registry aligned")
    print("✅ IR structure validated")
    print("✅ Runtime projection validated")
    print("✅ Deterministic ordering verified")
    print("✅ Duplicate prevention verified")
    print(f"✅ Runtime invariants: {len(ir_ids)}")


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
