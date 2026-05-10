# afritech/constitution/compiler/compile_invariants.py

"""
AfriTech Invariant Semantic Compiler
===================================

This compiler transforms the authoritative human-authored
invariant semantic source into canonical machine-consumable
artifacts.

AUTHORITATIVE INPUT:
- afritech/constitution/invariants_semantics.yaml

GENERATED OUTPUTS (DO NOT EDIT):
- afritech/constitution/compiled/invariants_ir.json
- afritech/constitution/compiled/invariants_index.py
- afritech/constitution/compiled/invariants_manifest.json

CONSTITUTIONAL RULE:
No runtime, CI, replay, or proof code may interpret
raw semantic YAML directly. All enforcement MUST bind
to compiled Semantic IR.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import yaml


# ---------------------------------------------------------------------
# PATHS (CANONICAL)
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

SEMANTIC_SOURCE = ROOT / "afritech" / "constitution" / "invariants_semantics.yaml"
COMPILED_DIR = ROOT / "afritech" / "constitution" / "compiled"

IR_OUTPUT = COMPILED_DIR / "invariants_ir.json"
INDEX_OUTPUT = COMPILED_DIR / "invariants_index.py"
MANIFEST_OUTPUT = COMPILED_DIR / "invariants_manifest.json"


# ---------------------------------------------------------------------
# FAILURE HELPERS
# ---------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"[INVARIANT COMPILER ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------
# HASHING
# ---------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: Any) -> bytes:
    """
    Deterministic JSON serialization for hashing.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


# ---------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------

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


def validate_invariant(inv_id: str, inv: Dict[str, Any]) -> None:
    missing = REQUIRED_INVARIANT_FIELDS - inv.keys()
    if missing:
        fail(f"Invariant {inv_id} missing required fields: {sorted(missing)}")

    if not isinstance(inv["formal_name"], str):
        fail(f"Invariant {inv_id}.formal_name must be string")

    if not isinstance(inv["category"], str):
        fail(f"Invariant {inv_id}.category must be string")

    if "description" not in inv["intent"]:
        fail(f"Invariant {inv_id}.intent.description missing")

    if not isinstance(inv["preconditions"], list):
        fail(f"Invariant {inv_id}.preconditions must be list")

    if not isinstance(inv["prohibited_actions"], list):
        fail(f"Invariant {inv_id}.prohibited_actions must be list")

    if not isinstance(inv["required_postconditions"], list):
        fail(f"Invariant {inv_id}.required_postconditions must be list")

    if not isinstance(inv["enforcement_points"], dict):
        fail(f"Invariant {inv_id}.enforcement_points must be dict")

    if not isinstance(inv["witnesses"], dict):
        fail(f"Invariant {inv_id}.witnesses must be dict")

    if "class" not in inv["failure"] or "response" not in inv["failure"]:
        fail(f"Invariant {inv_id}.failure must define class and response")


# ---------------------------------------------------------------------
# COMPILATION
# ---------------------------------------------------------------------

def compile_invariants() -> None:
    if not SEMANTIC_SOURCE.exists():
        fail(f"Semantic source not found: {SEMANTIC_SOURCE}")

    raw_yaml = SEMANTIC_SOURCE.read_text(encoding="utf-8")
    source_hash = sha256_bytes(raw_yaml.encode("utf-8"))

    data = yaml.safe_load(raw_yaml)

    if not isinstance(data, dict):
        fail("Semantic source must be a YAML mapping")

    if "invariants" not in data:
        fail("Semantic source missing 'invariants' root key")

    invariants = data["invariants"]

    if not isinstance(invariants, dict):
        fail("'invariants' must be a mapping")

    compiled: Dict[str, Any] = {}

    for inv_id, inv_def in invariants.items():
        if not inv_id.startswith("I"):
            fail(f"Invariant id {inv_id} must start with 'I'")

        validate_invariant(inv_id, inv_def)

        compiled[inv_id] = inv_def

    COMPILED_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Write IR
    # -----------------------------------------------------------------

    ir_payload = {
        "schema": "afritech.constitution.invariants.ir.v1",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_hash": source_hash,
        "invariants": compiled,
    }

    IR_OUTPUT.write_text(
        json.dumps(ir_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Write Python index
    # -----------------------------------------------------------------

    index_lines = [
        "# AUTO-GENERATED — DO NOT EDIT",
        "# Generated by compile_invariants.py",
        "",
    ]

    for inv_id in sorted(compiled.keys()):
        index_lines.append(f'{inv_id} = "{inv_id}"')

    INDEX_OUTPUT.write_text(
        "\n".join(index_lines) + "\n",
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Write manifest
    # -----------------------------------------------------------------

    manifest = {
        "semantic_version": data.get("version"),
        "source_hash": source_hash,
        "generated_at": ir_payload["generated_at"],
        "invariant_count": len(compiled),
        "outputs": {
            "ir": str(IR_OUTPUT.relative_to(ROOT)),
            "index": str(INDEX_OUTPUT.relative_to(ROOT)),
        },
    }

    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("[OK] Invariant semantics compiled successfully")
    print(f"     Invariants: {len(compiled)}")
    print(f"     Source hash: {source_hash}")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    compile_invariants()