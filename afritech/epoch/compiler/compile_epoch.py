# afritech/epoch/compiler/compile_epoch.py

"""
AfriTech Epoch Semantic Compiler
================================

This compiler transforms the authoritative human-authored
epoch semantic source into canonical machine-consumable
epoch law artifacts.

AUTHORITATIVE INPUT:
- afritech/epoch/epoch_semantics.yaml

GENERATED OUTPUTS (DO NOT EDIT):
- afritech/epoch/compiled/semantic_epoch.py
- afritech/epoch/compiled/epoch_ir.json
- afritech/epoch/compiled/epoch_manifest.json

CONSTITUTIONAL RULE:
No runtime, replay, CI, or proof code may interpret
epoch YAML directly. All epoch meaning MUST be derived
from compiled artifacts.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import yaml


# ---------------------------------------------------------------------
# PATHS (CANONICAL)
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

SEMANTIC_SOURCE = ROOT / "afritech" / "epoch" / "epoch_semantics.yaml"
COMPILED_DIR = ROOT / "afritech" / "epoch" / "compiled"

IR_OUTPUT = COMPILED_DIR / "epoch_ir.json"
PY_OUTPUT = COMPILED_DIR / "semantic_epoch.py"
MANIFEST_OUTPUT = COMPILED_DIR / "epoch_manifest.json"


# ---------------------------------------------------------------------
# FAILURE HANDLING
# ---------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"[EPOCH COMPILER ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------
# HASHING
# ---------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: Any) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


# ---------------------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------------------

REQUIRED_TOP_LEVEL_KEYS = {
    "schema",
    "version",
    "metadata",
    "global_law",
    "epoch_types",
    "transition_rules",
    "reseal_requirements",
    "replay_admissibility",
    "compiler_contract",
    "migration",
    "lineage",
    "acceptance",
}


def validate_top_level(data: Dict[str, Any]) -> None:
    missing = REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        fail(f"Epoch semantics missing top-level keys: {sorted(missing)}")


def validate_epoch_types(epoch_types: Dict[str, Any]) -> None:
    if not epoch_types:
        fail("epoch_types must not be empty")

    for name, spec in epoch_types.items():
        if "description" not in spec:
            fail(f"Epoch type {name} missing description")
        if "permits" not in spec or "prohibits" not in spec:
            fail(f"Epoch type {name} must define permits and prohibits")
        if "reseal_required" not in spec:
            fail(f"Epoch type {name} missing reseal_required flag")


def validate_transition_rules(
    epoch_types: Dict[str, Any],
    transitions: Dict[str, Any],
) -> None:
    for src, rule in transitions.items():
        if src not in epoch_types:
            fail(f"Transition rule references unknown epoch type: {src}")
        allowed = rule.get("allowed_successors", [])
        for dst in allowed:
            if dst not in epoch_types:
                fail(f"Transition rule {src} → {dst} references unknown epoch type")


def validate_lineage(
    epoch_types: Dict[str, Any],
    lineage: Dict[str, Any],
) -> None:
    epochs = lineage.get("epochs", [])
    seen_numbers = set()

    for entry in epochs:
        number = entry.get("number")
        etype = entry.get("type")
        parent = entry.get("parent")

        if number in seen_numbers:
            fail(f"Duplicate epoch number in lineage: {number}")
        seen_numbers.add(number)

        if etype not in epoch_types:
            fail(f"Lineage references unknown epoch type: {etype}")

        if number == 0 and parent is not None:
            fail("Genesis epoch must not have a parent")

        if number != 0 and parent is None:
            fail(f"Epoch {number} missing parent")


# ---------------------------------------------------------------------
# COMPILATION
# ---------------------------------------------------------------------

def compile_epoch_semantics() -> None:
    if not SEMANTIC_SOURCE.exists():
        fail(f"Epoch semantic source not found: {SEMANTIC_SOURCE}")

    raw_yaml = SEMANTIC_SOURCE.read_text(encoding="utf-8")
    source_hash = sha256_bytes(raw_yaml.encode("utf-8"))

    data = yaml.safe_load(raw_yaml)

    if not isinstance(data, dict):
        fail("Epoch semantic source must be a YAML mapping")

    validate_top_level(data)

    epoch_types = data["epoch_types"]
    transition_rules = data["transition_rules"]
    lineage = data["lineage"]

    validate_epoch_types(epoch_types)
    validate_transition_rules(epoch_types, transition_rules)
    validate_lineage(epoch_types, lineage)

    COMPILED_DIR.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.utcnow().isoformat() + "Z"

    # -----------------------------------------------------------------
    # Emit IR
    # -----------------------------------------------------------------

    ir_payload = {
        "schema": "afritech.epoch.semantic.ir.v1",
        "generated_at": generated_at,
        "source_hash": source_hash,
        "global_law": data["global_law"],
        "epoch_types": epoch_types,
        "transition_rules": transition_rules,
        "reseal_requirements": data["reseal_requirements"],
        "replay_admissibility": data["replay_admissibility"],
        "lineage": lineage,
    }

    IR_OUTPUT.write_text(
        json.dumps(ir_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Emit Python law types
    # -----------------------------------------------------------------

    py_lines: List[str] = [
        "# AUTO-GENERATED — DO NOT EDIT",
        "# Generated by compile_epoch.py",
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from enum import Enum",
        "",
        "",
        "class EpochType(Enum):",
    ]

    for name in sorted(epoch_types.keys()):
        py_lines.append(f'    {name} = "{name}"')

    py_lines.extend([
        "",
        "",
        "@dataclass(frozen=True)",
        "class SemanticEpoch:",
        "    number: int",
        "    parent: int | None",
        "    epoch_type: EpochType",
        "    reseal_required: bool",
        "",
    ])

    PY_OUTPUT.write_text("\n".join(py_lines) + "\n", encoding="utf-8")

    # -----------------------------------------------------------------
    # Emit manifest
    # -----------------------------------------------------------------

    manifest = {
        "schema": "afritech.epoch.semantic.manifest.v1",
        "semantic_version": data.get("version"),
        "source_hash": source_hash,
        "generated_at": generated_at,
        "epoch_type_count": len(epoch_types),
        "outputs": {
            "ir": str(IR_OUTPUT.relative_to(ROOT)),
            "python": str(PY_OUTPUT.relative_to(ROOT)),
        },
    }

    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("[OK] Epoch semantics compiled successfully")
    print(f"     Epoch types: {len(epoch_types)}")
    print(f"     Source hash: {source_hash}")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    compile_epoch_semantics()