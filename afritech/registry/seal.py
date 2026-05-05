from __future__ import annotations

"""
AfriTech Registry Reseal Tool
============================

Performs a lawful cryptographic reseal of the registry after
authorized mutation.

This tool:
- DOES NOT advance epochs
- DOES NOT change authority
- DOES NOT modify history
- ONLY recomputes the registry hash and reseals

Execution of this tool is REQUIRED before runtime boot
after any registry-affecting change.
"""

import hashlib
import yaml
from pathlib import Path


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "registry" / "registry.yaml"


# ---------------------------------------------------------------------
# Canonical hashing
# ---------------------------------------------------------------------

def canonical_registry_bytes(registry: dict) -> bytes:
    """
    Produce canonical bytes for registry hashing.

    Excludes seal metadata so the hash is stable and reproducible.
    """
    data = registry.copy()

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


# ---------------------------------------------------------------------
# Reseal operation
# ---------------------------------------------------------------------

def reseal_registry() -> None:
    if not REGISTRY_PATH.exists():
        raise RuntimeError("registry.yaml not found")

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    # Compute canonical hash
    canonical_bytes = canonical_registry_bytes(registry)
    digest = hashlib.sha256(canonical_bytes).hexdigest()

    # -----------------------------------------------------------------
    # Authoritative seal location (enforced by runtime)
    # -----------------------------------------------------------------
    registry.setdefault("attestation", {})
    registry["attestation"]["registry_hash"] = digest
    registry["attestation"]["seal_status"] = "SEALED"

    # -----------------------------------------------------------------
    # Documentary mirror (non-authoritative)
    # -----------------------------------------------------------------
    registry["seal_status"] = "SEALED"

    # Write back
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(registry, f, sort_keys=False)

    print("🔏 REGISTRY RESEALED")
    print("✅ attestation.seal_status = SEALED")
    print("✅ attestation.registry_hash updated")
    print(f"🔐 sha256 = {digest}")


# ---------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------

if __name__ == "__main__":
    reseal_registry()
