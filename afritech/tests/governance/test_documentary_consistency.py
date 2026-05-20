# afritech/tests/test_documentary_consistency.py

"""
Documentary Consistency Tests
=============================

Purpose
-------
Ensure that all documentary artifacts are:

- fully derived from registry authority
- structurally valid
- deterministic
- replay-safe
- constitutionally admissible
- free from undocumented mutation

These tests MUST fail on:

- epoch mismatch
- surface mismatch
- schema drift
- undocumented mutation
- deterministic hash drift
- authority divergence
- replay-unsafe structure

Constitutional Guarantees
-------------------------

registry.yaml
    = authoritative source of truth

INDEX.yaml
    = deterministic derived artifact

No documentary artifact may introduce
semantic information absent from the registry.
"""

import os
import yaml
import hashlib

from typing import Any, Dict


# ============================================================
# PATHS
# ============================================================

REGISTRY_PATH = "afritech/registry/registry.yaml"
INDEX_PATH = "afritech/governance/INDEX.yaml"


# ============================================================
# UTILITIES
# ============================================================

def load_yaml(path: str) -> Dict[str, Any]:
    assert os.path.exists(path), f"Missing file: {path}"

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), f"Invalid YAML structure: {path}"

    return data


def canonical_yaml(data: Dict[str, Any]) -> bytes:
    """
    Deterministic replay-safe serialization.
    """
    serialized = yaml.safe_dump(
        data,
        sort_keys=True,
        allow_unicode=True,
    )
    return serialized.encode("utf-8")


def compute_hash(data: Dict[str, Any]) -> str:
    """
    Canonical deterministic hash.
    """
    return hashlib.sha256(
        canonical_yaml(data)
    ).hexdigest()


# ============================================================
# CORE EXISTENCE TESTS
# ============================================================

def test_files_exist():
    assert os.path.exists(REGISTRY_PATH), "registry.yaml not found"
    assert os.path.exists(INDEX_PATH), "INDEX.yaml not found"


# ============================================================
# EPOCH CONSISTENCY
# ============================================================

def test_epoch_alignment():
    registry = load_yaml(REGISTRY_PATH)
    index = load_yaml(INDEX_PATH)

    assert "epoch" in registry, "registry missing epoch"
    assert "epoch" in index, "INDEX missing epoch"

    assert registry["epoch"] == index["epoch"], (
        f"Epoch mismatch:\n"
        f"registry={registry['epoch']}\n"
        f"index={index['epoch']}"
    )


# ============================================================
# SURFACE CONSISTENCY
# ============================================================

def test_surface_alignment():
    registry = load_yaml(REGISTRY_PATH)
    index = load_yaml(INDEX_PATH)

    reg_surfaces = sorted(
        registry.get("surfaces", {})
        if isinstance(registry.get("surfaces", {}), dict)
        else registry.get("surfaces", [])
    )

    idx_surfaces = sorted(
        index.get("surfaces", {})
        if isinstance(index.get("surfaces", {}), dict)
        else index.get("surfaces", [])
    )

    assert reg_surfaces == idx_surfaces, (
        f"Surface mismatch:\n"
        f"registry={reg_surfaces}\n"
        f"index={idx_surfaces}"
    )


# ============================================================
# SCHEMA VALIDATION
# ============================================================

def test_schema_integrity():
    index = load_yaml(INDEX_PATH)

    assert "schema" in index, "INDEX missing schema"

    assert index["schema"] == "afritech.index.v2", (
        "Invalid INDEX schema"
    )


# ============================================================
# SOURCE AUTHORITY
# ============================================================

def test_generated_from_marker():
    index = load_yaml(INDEX_PATH)

    assert "generated_from" in index, (
        "INDEX missing generated_from"
    )

    generated_from = index["generated_from"]

    assert isinstance(
        generated_from,
        list,
    ), "generated_from must be list"

    assert any(
        "registry.yaml" in item
        for item in generated_from
    ), (
        "INDEX must declare registry.yaml as authority"
    )


# ============================================================
# DETERMINISTIC RECONCILIATION
# ============================================================

def test_index_is_deterministic():
    """
    Recompute expected INDEX and compare canonical hashes.
    """

    from afritech.tools.reconcile_index import generate_index

    registry = load_yaml(REGISTRY_PATH)
    current_index = load_yaml(INDEX_PATH)

    expected_index = generate_index(registry)

    current_hash = compute_hash(current_index)
    expected_hash = compute_hash(expected_index)

    assert current_hash == expected_hash, (
        "INDEX drift detected:\n"
        f"current_hash={current_hash}\n"
        f"expected_hash={expected_hash}"
    )


# ============================================================
# STRUCTURAL IMMUTABILITY
# ============================================================

def test_no_extra_fields_in_index():
    """
    Prevent undocumented mutation of INDEX structure.
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
        f"Unexpected fields in INDEX: {sorted(extra_fields)}"
    )


# ============================================================
# REGISTRY AUTHORITY
# ============================================================

def test_registry_is_authority():
    """
    Ensure INDEX never introduces undeclared surfaces.
    """

    registry = load_yaml(REGISTRY_PATH)
    index = load_yaml(INDEX_PATH)

    registry_surfaces = set(
        registry.get("surfaces", {}).keys()
        if isinstance(registry.get("surfaces", {}), dict)
        else registry.get("surfaces", [])
    )

    index_surfaces = set(
        index.get("surfaces", {}).keys()
        if isinstance(index.get("surfaces", {}), dict)
        else index.get("surfaces", [])
    )

    undeclared = index_surfaces - registry_surfaces

    assert not undeclared, (
        f"INDEX contains undeclared surfaces: {sorted(undeclared)}"
    )


# ============================================================
# META VALIDATION
# ============================================================

def test_meta_integrity():
    index = load_yaml(INDEX_PATH)
    meta = index.get("meta", {})

    assert isinstance(meta, dict), "INDEX meta must be mapping"

    assert meta.get("deterministic") is True, (
        "INDEX meta must declare deterministic=True"
    )

    assert meta.get("replay_safe") is True, (
        "INDEX meta must declare replay_safe=True"
    )

    assert meta.get("generated_by") == "reconcile_index.py", (
        "INDEX meta must declare canonical generator"
    )


# ============================================================
# REPLAY-SAFE ORDERING
# ============================================================

def test_index_ordering_is_deterministic():
    """
    Ensure deterministic ordering of surfaces.
    """

    index = load_yaml(INDEX_PATH)

    surfaces = index.get("surfaces", {})

    if isinstance(surfaces, dict):
        keys = list(surfaces.keys())

        assert keys == sorted(keys), (
            "INDEX surfaces must be deterministically ordered"
        )


# ============================================================
# HASH STABILITY
# ============================================================

def test_hash_is_stable():
    index = load_yaml(INDEX_PATH)

    h1 = compute_hash(index)
    h2 = compute_hash(index)

    assert h1 == h2, (
        "Canonical hash must be stable"
    )