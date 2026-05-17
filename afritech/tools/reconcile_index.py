# afritech/tools/reconcile_index.py

"""
AfriTech Documentary Reconciliation Tool
========================================

Purpose
-------
Generate and verify INDEX.yaml as a deterministic,
replay-safe projection of registry.yaml.

This enforces:

- zero drift
- zero undocumented mutation
- canonical structure
- replay-safe determinism

Contract
--------
INDEX = canonical_projection(REGISTRY)
"""

from __future__ import annotations

import os
import sys
import yaml
import hashlib

from typing import Dict, Any


# ============================================================
# PATHS
# ============================================================

REGISTRY_PATH = "afritech/registry/registry.yaml"
INDEX_PATH = "afritech/governance/INDEX.yaml"


# ============================================================
# ERROR
# ============================================================

class ReconciliationError(Exception):
    pass


# ============================================================
# YAML IO
# ============================================================

def load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise ReconciliationError(f"missing_file: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise ReconciliationError(f"invalid_yaml: {path} -> {e}")

    if not isinstance(data, dict):
        raise ReconciliationError(f"invalid_yaml_structure: {path}")

    return data


def save_yaml(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=True,
            allow_unicode=True,
        )


# ============================================================
# CANONICAL HASH
# ============================================================

def canonical_yaml(data: Dict[str, Any]) -> bytes:
    return yaml.safe_dump(
        data,
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")


def compute_hash(data: Dict[str, Any]) -> str:
    return hashlib.sha256(
        canonical_yaml(data)
    ).hexdigest()


# ============================================================
# GENERATOR (AUTHORITATIVE)
# ============================================================

def generate_index(registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic canonical projection:

        registry.yaml → INDEX.yaml

    RULES
    -----
    - No transformation of meaning
    - No additional semantics
    - Fully deterministic
    """

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------
    if "epoch" not in registry:
        raise ReconciliationError("missing_registry_epoch")

    # --------------------------------------------------------
    # SURFACES (deterministic ordering)
    # --------------------------------------------------------
    surfaces = registry.get("surfaces", {})

    if isinstance(surfaces, dict):
        surfaces = {
            key: surfaces[key]
            for key in sorted(surfaces.keys())
        }
    elif isinstance(surfaces, list):
        surfaces = sorted(surfaces)
    else:
        surfaces = {}

    # --------------------------------------------------------
    # INDEX (STRICT STRUCTURE)
    # --------------------------------------------------------
    index = {

        # ✅ Schema identity
        "schema": "afritech.index.v2",

        # ✅ Authority source
        "generated_from": [
            "afritech/registry/registry.yaml"
        ],

        # ✅ MUST MATCH EXACTLY (no reshaping)
        "epoch": registry["epoch"],

        # ✅ Deterministic projection
        "surfaces": surfaces,

        # ✅ Meta guarantees
        "meta": {
            "deterministic": True,
            "replay_safe": True,
            "generated_by": "reconcile_index.py",
        },
    }

    return index


# ============================================================
# VALIDATION
# ============================================================

def validate_consistency(
    registry: Dict[str, Any],
    index: Dict[str, Any],
) -> None:

    expected = generate_index(registry)

    if compute_hash(index) != compute_hash(expected):
        raise ReconciliationError("index_out_of_sync")

    # Exact epoch equality
    if registry["epoch"] != index.get("epoch"):
        raise ReconciliationError("epoch_mismatch")

    # Surface equality
    reg_surfaces = set(
        registry.get("surfaces", {}).keys()
        if isinstance(registry.get("surfaces", {}), dict)
        else registry.get("surfaces", [])
    )

    idx_surfaces = set(
        index.get("surfaces", {}).keys()
        if isinstance(index.get("surfaces", {}), dict)
        else index.get("surfaces", [])
    )

    if reg_surfaces != idx_surfaces:
        raise ReconciliationError("surface_mismatch")


# ============================================================
# EXECUTION MODES
# ============================================================

def reconcile(write: bool = True) -> Dict[str, Any]:

    registry = load_yaml(REGISTRY_PATH)

    new_index = generate_index(registry)

    if write:
        save_yaml(INDEX_PATH, new_index)

        print("✅ INDEX.yaml regenerated (canonical)")

    return new_index


def verify() -> None:

    registry = load_yaml(REGISTRY_PATH)
    current_index = load_yaml(INDEX_PATH)

    validate_consistency(registry, current_index)

    print("✅ INDEX.yaml is consistent")


def dry_run() -> None:

    registry = load_yaml(REGISTRY_PATH)
    index = generate_index(registry)

    print("=== DRY RUN (INDEX preview) ===\n")

    print(
        yaml.safe_dump(
            index,
            sort_keys=True,
            allow_unicode=True,
        )
    )


# ============================================================
# CLI ENTRYPOINT
# ============================================================

def main() -> int:

    mode = "reconcile"

    if len(sys.argv) > 1:
        mode = sys.argv[1]

    try:

        if mode == "reconcile":
            reconcile(write=True)

        elif mode == "verify":
            verify()

        elif mode == "dry_run":
            dry_run()

        else:
            raise ReconciliationError(f"invalid_mode: {mode}")

        return 0

    except ReconciliationError as e:
        print(f"❌ RECONCILIATION FAILED: {e}")
        return 1

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())