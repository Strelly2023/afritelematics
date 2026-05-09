# afritech/registry/loader.py

"""
AfriTech Registry Loader
=======================

Read-only loader for the constitutional registry.

Purpose:
- Load registry.yaml deterministically
- Perform minimal structural validation
- Provide a stable object for replay, admission, and auditing

CONSTITUTIONAL GUARANTEES:
- Read-only
- No mutation
- No reseal
- No side effects
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Any
import yaml


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "registry" / "registry.yaml"


# ---------------------------------------------------------------------
# ERROR
# ---------------------------------------------------------------------

class RegistryLoadError(RuntimeError):
    """Raised when registry loading fails."""


# ---------------------------------------------------------------------
# LOAD REGISTRY
# ---------------------------------------------------------------------

def load_registry() -> Dict[str, Any]:
    """
    Load the constitutional registry in a deterministic, read-only way.

    Returns:
        Parsed registry dictionary

    Raises:
        RegistryLoadError on any structural or IO failure
    """

    if not REGISTRY_PATH.exists():
        raise RegistryLoadError(
            f"registry.yaml not found at {REGISTRY_PATH}"
        )

    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = yaml.safe_load(f)
    except Exception as e:
        raise RegistryLoadError(
            f"failed to load registry.yaml: {e}"
        )

    if not isinstance(registry, dict):
        raise RegistryLoadError(
            "invalid registry format: expected mapping"
        )

    _validate_registry_structure(registry)

    return registry


# ---------------------------------------------------------------------
# MINIMAL STRUCTURAL VALIDATION
# ---------------------------------------------------------------------

def _validate_registry_structure(registry: Dict[str, Any]) -> None:
    """
    Perform minimal, non-authoritative structural validation.

    This does NOT enforce invariants.
    It only ensures the registry is readable and well-formed.
    """

    if "epoch" not in registry:
        raise RegistryLoadError("missing 'epoch' block")

    if "attestation" not in registry:
        raise RegistryLoadError("missing 'attestation' block")

    epoch = registry["epoch"]
    attestation = registry["attestation"]

    if not isinstance(epoch, dict):
        raise RegistryLoadError("'epoch' must be a mapping")

    if not isinstance(attestation, dict):
        raise RegistryLoadError("'attestation' must be a mapping")

    if "current" not in epoch:
        raise RegistryLoadError("missing epoch.current")

    if "kernel_hashes" not in attestation:
        raise RegistryLoadError("missing attestation.kernel_hashes")

    kernel_hashes = attestation["kernel_hashes"]

    if not isinstance(kernel_hashes, dict):
        raise RegistryLoadError(
            "attestation.kernel_hashes must be a mapping"
        )

    # Do not validate hashes here — replay/seal does that.


# ---------------------------------------------------------------------
# DEBUG
# ---------------------------------------------------------------------

def __repr__() -> str:
    return "<RegistryLoader read-only>"

# ---------------------------------------------------------------------
# LOAD REGISTRY (CANONICAL FORM)
# ---------------------------------------------------------------------

def load_registry_canonical() -> bytes:
    """
    Load the constitutional registry in canonical byte form.

    Purpose:
    - Produce a deterministic, hash-stable representation
    - Match registry sealing and validator logic exactly
    - Support replay verification and external auditing

    Guarantees:
    - Read-only
    - No mutation
    - Deterministic output
    - Validator-compatible

    Returns:
        Canonical UTF-8 encoded bytes of the registry
    """

    registry = load_registry()

    # -------------------------------------------------------------
    # Defensive deep copy via YAML round-trip
    # -------------------------------------------------------------

    data = yaml.safe_load(
        yaml.safe_dump(registry, sort_keys=True)
    )

    # -------------------------------------------------------------
    # Remove documentary / mutable fields
    # (MUST match seal.py logic exactly)
    # -------------------------------------------------------------

    data.pop("seal_status", None)

    attestation = data.get("attestation", {}).copy()
    attestation.pop("registry_hash", None)
    attestation.pop("seal_status", None)

    data["attestation"] = attestation

    # -------------------------------------------------------------
    # Canonical serialization
    # -------------------------------------------------------------

    canonical_yaml = yaml.safe_dump(
        data,
        sort_keys=True,
        default_flow_style=False,
    )

    return canonical_yaml.encode("utf-8")

# ---------------------------------------------------------------------
# COMPUTE REGISTRY HASH (CANONICAL)
# ---------------------------------------------------------------------

def compute_registry_hash_canonical() -> str:
    """
    Compute the canonical registry hash directly from canonical bytes.

    Purpose:
    - Provide a single-source-of-truth registry digest
    - Match registry sealing and replay verification exactly
    - Enable external and internal cryptographic comparison

    Guarantees:
    - Deterministic
    - Read-only
    - Seal-compatible
    - Replay-compatible

    Returns:
        SHA256 hex digest of canonical registry bytes
    """

    canonical_bytes = load_registry_canonical()
    return hashlib.sha256(canonical_bytes).hexdigest()