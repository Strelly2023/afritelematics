# afritech/tools/reconcile_index.py

"""
AfriTech Documentary Reconciliation Tool

Purpose:
Ensure that all documentary files (e.g. INDEX.yaml)
are strictly derived from the authoritative registry.

This eliminates:
- drift
- manual inconsistency
- stale documentation

Modes:
- reconcile (write)
- verify (CI check)
- dry_run (preview only)
"""

import os
import sys
import yaml
import hashlib
from typing import Dict, Any


REGISTRY_PATH = "afritech/registry/registry.yaml"
INDEX_PATH = "afritech/governance/INDEX.yaml"


class ReconciliationError(Exception):
    pass


# ---------------------------------------------------------------------
# FILE IO
# ---------------------------------------------------------------------

def load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise ReconciliationError(f"missing_file: {path}")

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise ReconciliationError(f"invalid_yaml: {path} → {e}")

    if not isinstance(data, dict):
        raise ReconciliationError(f"invalid_yaml_structure: {path}")

    return data


def save_yaml(path: str, data: Dict[str, Any]):
    with open(path, "w") as f:
        yaml.dump(data, f, sort_keys=True)


# ---------------------------------------------------------------------
# HASH (OPTIONAL INTEGRITY CHECK)
# ---------------------------------------------------------------------

def compute_hash(data: Dict[str, Any]) -> str:
    serialized = yaml.dump(data, sort_keys=True).encode()
    return hashlib.sha256(serialized).hexdigest()


# ---------------------------------------------------------------------
# INDEX GENERATION (AUTHORITATIVE LOGIC)
# ---------------------------------------------------------------------

def generate_index(registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic transformation:
    Registry → INDEX

    Only registry is authoritative.
    """

    required_fields = ["epoch"]

    for field in required_fields:
        if field not in registry:
            raise ReconciliationError(f"missing_registry_field: {field}")

    index = {
        "schema": "afritech.governance.index.v1",
        "generated_from": "registry.yaml",
        "epoch": registry["epoch"],

        # Optional registry fields passed through
        "surfaces": sorted(registry.get("surfaces", [])),

        "meta": {
            "deterministic": True,
            "source_of_truth": "registry",
        }
    }

    return index


# ---------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------

def validate_consistency(registry: Dict[str, Any], index: Dict[str, Any]):
    if registry.get("epoch") != index.get("epoch"):
        raise ReconciliationError("epoch_mismatch")

    # Surface alignment
    reg_surfaces = sorted(registry.get("surfaces", []))
    idx_surfaces = sorted(index.get("surfaces", []))

    if reg_surfaces != idx_surfaces:
        raise ReconciliationError("surface_mismatch")


# ---------------------------------------------------------------------
# EXECUTION MODES
# ---------------------------------------------------------------------

def reconcile(write: bool = True):
    registry = load_yaml(REGISTRY_PATH)
    new_index = generate_index(registry)

    if write:
        save_yaml(INDEX_PATH, new_index)
        print("[RECONCILE] ✅ INDEX.yaml regenerated")
    else:
        return new_index


def verify():
    registry = load_yaml(REGISTRY_PATH)
    current_index = load_yaml(INDEX_PATH)
    expected_index = generate_index(registry)

    if compute_hash(current_index) != compute_hash(expected_index):
        raise ReconciliationError("index_out_of_sync")

    validate_consistency(registry, current_index)

    print("[VERIFY] ✅ INDEX.yaml is consistent")


def dry_run():
    new_index = reconcile(write=False)

    print("[DRY RUN] Generated INDEX.yaml:\n")
    print(yaml.dump(new_index, sort_keys=True))


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":

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

    except ReconciliationError as e:
        print(f"[RECONCILE] ❌ FAILURE: {str(e)}")
        sys.exit(1)

    except Exception as e:
        print(f"[RECONCILE] ❌ UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)

    sys.exit(0)