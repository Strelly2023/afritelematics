# afritech/tests/test_documentary_consistency.py

"""
Documentary Consistency Tests

Purpose:
Ensure that all documentary files (INDEX.yaml) are:

- fully derived from registry.yaml
- structurally valid
- consistent with authoritative data
- deterministic (no hidden drift)

These tests MUST fail on:
- epoch mismatch
- surface mismatch
- schema violation
- undocumented mutation
"""

import os
import yaml
import hashlib


REGISTRY_PATH = "afritech/registry/registry.yaml"
INDEX_PATH = "afritech/governance/INDEX.yaml"


# ---------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------

def load_yaml(path):
    assert os.path.exists(path), f"Missing file: {path}"

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), f"Invalid YAML structure: {path}"

    return data


def compute_hash(data):
    serialized = yaml.dump(data, sort_keys=True).encode()
    return hashlib.sha256(serialized).hexdigest()


# ---------------------------------------------------------------------
# CORE TESTS
# ---------------------------------------------------------------------

def test_files_exist():
    assert os.path.exists(REGISTRY_PATH), "registry.yaml not found"
    assert os.path.exists(INDEX_PATH), "INDEX.yaml not found"


def test_epoch_alignment():
    registry = load_yaml(REGISTRY_PATH)
    index = load_yaml(INDEX_PATH)

    assert "epoch" in registry, "registry missing epoch"
    assert "epoch" in index, "INDEX missing epoch"

    assert registry["epoch"] == index["epoch"], (
        f"Epoch mismatch: registry={registry['epoch']} index={index['epoch']}"
    )


def test_surface_alignment():
    registry = load_yaml(REGISTRY_PATH)
    index = load_yaml(INDEX_PATH)

    reg_surfaces = sorted(registry.get("surfaces", []))
    idx_surfaces = sorted(index.get("surfaces", []))

    assert reg_surfaces == idx_surfaces, (
        f"Surface mismatch:\nregistry={reg_surfaces}\nindex={idx_surfaces}"
    )


def test_schema_integrity():
    index = load_yaml(INDEX_PATH)

    assert "schema" in index, "INDEX missing schema"
    assert index["schema"] == "afritech.governance.index.v1", (
        "Invalid INDEX schema"
    )


def test_generated_from_marker():
    index = load_yaml(INDEX_PATH)

    assert "generated_from" in index, "INDEX missing generated_from"
    assert index["generated_from"] == "registry.yaml", (
        "INDEX must be derived from registry.yaml"
    )


# ---------------------------------------------------------------------
# DETERMINISM TEST
# ---------------------------------------------------------------------

def test_index_is_deterministic():
    """
    Recompute expected INDEX and compare hashes
    """

    from afritech.tools.reconcile_index import generate_index

    registry = load_yaml(REGISTRY_PATH)
    current_index = load_yaml(INDEX_PATH)

    expected_index = generate_index(registry)

    current_hash = compute_hash(current_index)
    expected_hash = compute_hash(expected_index)

    assert current_hash == expected_hash, (
        f"INDEX drift detected:\n"
        f"current_hash={current_hash}\nexpected_hash={expected_hash}"
    )


# ---------------------------------------------------------------------
# NEGATIVE SAFETY TESTS
# ---------------------------------------------------------------------

def test_no_extra_fields_in_index():
    """
    Prevent undocumented mutation of INDEX structure
    """

    allowed_fields = {
        "schema",
        "generated_from",
        "epoch",
        "surfaces",
        "meta",
    }

    index = load_yaml(INDEX_PATH)

    extra_fields = set(index.keys()) - allowed_fields

    assert not extra_fields, (
        f"Unexpected fields in INDEX: {extra_fields}"
    )


def test_registry_is_authority():
    """
    Ensure INDEX never contains data not present in registry
    """

    registry = load_yaml(REGISTRY_PATH)
    index = load_yaml(INDEX_PATH)

    # Surfaces must originate from registry
    for surface in index.get("surfaces", []):
        assert surface in registry.get("surfaces", []), (
            f"INDEX contains undeclared surface: {surface}"
        )


# ---------------------------------------------------------------------
# FUTURE EXTENSION HOOK
# ---------------------------------------------------------------------

def test_meta_integrity():
    """
    Optional metadata validation
    """

    index = load_yaml(INDEX_PATH)
    meta = index.get("meta", {})

    assert meta.get("deterministic", False) is True, (
        "INDEX meta must declare deterministic=True"
    )

    assert meta.get("source_of_truth") == "registry", (
        "INDEX meta must declare registry as source_of_truth"
    )
