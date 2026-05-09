# afritech/registry/seal.py

"""
AfriTech Registry Reseal Tool
=============================

Lawfully reseals the constitutional registry after an approved mutation.

Guarantees
----------
- Deterministic canonical hashing
- Surface hash recomputation
- Registry identity stability
- Validator-compatible output
- Structural integrity enforcement
- TRACE causality binding

Execution Law
-------------
Must be executed AFTER lawful registry mutation
and BEFORE runtime boot.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "registry" / "registry.yaml"


# ---------------------------------------------------------------------
# EXCEPTIONS
# ---------------------------------------------------------------------

class RegistrySealError(RuntimeError):
    """Raised when registry resealing cannot complete."""


# ---------------------------------------------------------------------
# FILE HASHING (DETERMINISTIC)
# ---------------------------------------------------------------------

def sha256_manifest(root: Path, files: List[str]) -> str:
    """
    Deterministically hash a declared surface.

    File order is authoritative and preserved exactly.
    """

    hasher = hashlib.sha256()

    for rel in files:
        path = root / rel

        if not path.exists():
            raise RegistrySealError(
                f"Declared surface missing: {rel}"
            )

        if not path.is_file():
            raise RegistrySealError(
                f"Declared surface is not a file: {rel}"
            )

        hasher.update(path.read_bytes())

    return hasher.hexdigest()


# ---------------------------------------------------------------------
# SURFACE HASH RECOMPUTATION
# ---------------------------------------------------------------------

def recompute_surface_hashes(registry: Dict[str, Any]) -> None:
    """
    Recompute all attested surface hashes.
    """

    attestation = registry.get("attestation")
    if not attestation:
        raise RegistrySealError("Missing attestation block")

    surfaces = attestation.get("kernel_hashes")
    if not surfaces:
        raise RegistrySealError("Missing kernel_hashes")

    print("🔄 Recomputing constitutional surface hashes...\n")

    for surface_name, surface in surfaces.items():
        files = surface.get("files")

        if not files:
            raise RegistrySealError(
                f"Surface '{surface_name}' has no declared files"
            )

        digest = sha256_manifest(ROOT, files)
        surface["hash"] = digest

        print(f"✅ {surface_name:<20} {digest}")


# ---------------------------------------------------------------------
# CANONICAL REGISTRY HASHING
# ---------------------------------------------------------------------

def canonical_registry_bytes(registry: Dict[str, Any]) -> bytes:
    """
    Produce canonical registry bytes.

    MUST match validator logic exactly.
    """

    # Defensive deep copy via YAML roundtrip
    data = yaml.safe_load(
        yaml.safe_dump(registry, sort_keys=True)
    )

    # Remove documentary / mutable fields
    data.pop("seal_status", None)

    attestation = data.get("attestation", {}).copy()
    attestation.pop("registry_hash", None)
    attestation.pop("seal_status", None)

    data["attestation"] = attestation

    return yaml.safe_dump(
        data,
        sort_keys=True,
        default_flow_style=False,
    ).encode("utf-8")


def compute_registry_hash(registry: Dict[str, Any]) -> str:
    """
    Compute canonical registry digest.
    """

    canonical = canonical_registry_bytes(registry)
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------------
# LOAD / WRITE
# ---------------------------------------------------------------------

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        raise RegistrySealError(
            f"registry.yaml not found at {REGISTRY_PATH}"
        )

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    if not isinstance(registry, dict):
        raise RegistrySealError("Invalid registry format")

    return registry


def write_registry(registry: Dict[str, Any]) -> None:
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            registry,
            f,
            sort_keys=False,
        )


# ---------------------------------------------------------------------
# RESEAL OPERATION
# ---------------------------------------------------------------------

def reseal_registry(
    *,
    trace_hash: Optional[str] = None,
    replay_hash: Optional[str] = None,
) -> None:
    """
    Perform lawful constitutional reseal.

    Optional bindings:
    - trace_hash: binds causality proof
    - replay_hash: binds replay oracle
    """

    registry = load_registry()

    # -------------------------------------------------------------
    # Recompute all surface hashes
    # -------------------------------------------------------------

    recompute_surface_hashes(registry)

    # -------------------------------------------------------------
    # Compute registry canonical digest
    # -------------------------------------------------------------

    digest = compute_registry_hash(registry)

    # -------------------------------------------------------------
    # Update authoritative attestation
    # -------------------------------------------------------------

    registry.setdefault("attestation", {})

    registry["attestation"]["registry_hash"] = digest
    registry["attestation"]["seal_status"] = "SEALED"

    # Optional causal bindings
    if trace_hash:
        registry["attestation"]["trace_hash"] = trace_hash

    if replay_hash:
        registry["attestation"]["replay_hash"] = replay_hash

    # Documentary mirror
    registry["seal_status"] = "SEALED"

    # -------------------------------------------------------------
    # Persist
    # -------------------------------------------------------------

    write_registry(registry)

    # -------------------------------------------------------------
    # Output
    # -------------------------------------------------------------

    print("\n🔏 REGISTRY RESEALED")
    print("✅ surface hashes updated")
    print("✅ attestation.seal_status = SEALED")
    print("✅ registry_hash updated")

    if trace_hash:
        print(f"✅ trace_hash bound: {trace_hash}")

    if replay_hash:
        print(f"✅ replay_hash bound: {replay_hash}")

    print(f"🔐 sha256 = {digest}\n")


# ---------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------

def verify_registry_consistency() -> bool:
    """
    Recompute registry hash and compare with stored value.
    """

    registry = load_registry()

    stored = registry.get("attestation", {}).get("registry_hash")
    computed = compute_registry_hash(registry)

    return stored == computed


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    reseal_registry()