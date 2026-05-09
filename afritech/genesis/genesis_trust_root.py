# afritech/genesis/genesis_trust_root.py

"""
AfriTech Genesis Trust Root

Purpose:
Define, derive, and enforce the root of trust for the system.

Guarantees:
- deterministic trust anchor
- binding to all constitutional roots
- replay invariance
- rejection on drift

This module ensures that system trust is:
    derived (not declared)
    complete
    immutable
"""

from typing import Dict, Any, List
import hashlib
import json


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class GenesisTrustError(Exception):
    """Raised when trust root validation fails"""
    pass


# -----------------------------------------------------------------
# CANONICAL JSON
# -----------------------------------------------------------------

def canonical_json(data: Dict[str, Any]) -> str:
    try:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except Exception as e:
        raise GenesisTrustError(f"canonicalization_failed: {e}")


# -----------------------------------------------------------------
# HASH FUNCTION
# -----------------------------------------------------------------

def hash_obj(data: Dict[str, Any]) -> str:
    return hashlib.sha256(
        canonical_json(data).encode()
    ).hexdigest()


# -----------------------------------------------------------------
# REQUIRED TRUST INPUTS
# -----------------------------------------------------------------

REQUIRED_TRUST_FIELDS: List[str] = [
    "registry_origin_hash",
    "invariant_root_hash",
    "constitutional_surface_hash",
    "execution_surface_hash",
]


# -----------------------------------------------------------------
# VALIDATE REQUIRED ROOTS
# -----------------------------------------------------------------

def _validate_required_fields(genesis: Dict[str, Any]):
    for field in REQUIRED_TRUST_FIELDS:
        if field not in genesis:
            raise GenesisTrustError(f"missing_field: {field}")

        value = genesis[field]

        if not isinstance(value, str) or len(value) < 32:
            raise GenesisTrustError(f"invalid_hash_field: {field}")


# -----------------------------------------------------------------
# CORE TRUST ANCHOR (CRITICAL)
# -----------------------------------------------------------------

def compute_trust_anchor(genesis: Dict[str, Any]) -> str:
    """
    Compute canonical trust anchor

    This binds ALL constitutional roots.
    """

    _validate_required_fields(genesis)

    payload = {
        "registry": genesis["registry_origin_hash"],
        "invariants": genesis["invariant_root_hash"],
        "constitutional_surface": genesis["constitutional_surface_hash"],
        "execution_surface": genesis["execution_surface_hash"],
    }

    return hash_obj(payload)


# -----------------------------------------------------------------
# VERIFY TRUST ANCHOR
# -----------------------------------------------------------------

def verify_trust_anchor(genesis: Dict[str, Any]) -> bool:
    """
    Validate stored trust anchor
    """

    if "trust_anchor" not in genesis:
        raise GenesisTrustError("missing_trust_anchor")

    expected = compute_trust_anchor(genesis)

    if genesis["trust_anchor"] != expected:
        raise GenesisTrustError("trust_anchor_mismatch")

    return True


# -----------------------------------------------------------------
# FULL TRUST ROOT (EXTENDED IDENTITY)
# -----------------------------------------------------------------

def compute_extended_trust_root(genesis: Dict[str, Any]) -> str:
    """
    Extended root for global identity

    Includes:
    - core trust anchor
    - system identity fields
    """

    base = {
        "id": genesis.get("id"),
        "constitutional_version": genesis.get("constitutional_version"),
        "authority_seed": genesis.get("authority_seed"),
        "core": compute_trust_anchor(genesis),
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# STRONG TRUST ROOT (FUTURE-PROOF)
# -----------------------------------------------------------------

def compute_strong_trust_root(genesis: Dict[str, Any]) -> str:
    """
    Strong root including additional bindings

    Use for federation and cross-system verification
    """

    base = {
        "core": compute_trust_anchor(genesis),
        "identity": compute_extended_trust_root(genesis),
        "epoch": genesis.get("initial_epoch"),
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# VERIFY EXTENDED ROOT
# -----------------------------------------------------------------

def verify_extended_root(genesis: Dict[str, Any], expected: str) -> bool:
    computed = compute_extended_trust_root(genesis)

    if computed != expected:
        raise GenesisTrustError("extended_root_mismatch")

    return True


# -----------------------------------------------------------------
# VERIFY STRONG ROOT
# -----------------------------------------------------------------

def verify_strong_root(genesis: Dict[str, Any], expected: str) -> bool:
    computed = compute_strong_trust_root(genesis)

    if computed != expected:
        raise GenesisTrustError("strong_root_mismatch")

    return True


# -----------------------------------------------------------------
# TRUST CONSISTENCY CHECK
# -----------------------------------------------------------------

def validate_trust_consistency(genesis: Dict[str, Any]) -> bool:
    """
    Full trust validation

    Includes:
    - anchor correctness
    - no missing roots
    """

    _validate_required_fields(genesis)
    verify_trust_anchor(genesis)

    return True


# -----------------------------------------------------------------
# DRIFT DETECTION
# -----------------------------------------------------------------

def detect_trust_drift(genesis: Dict[str, Any], baseline_anchor: str) -> bool:
    """
    Detect if trust has changed from baseline
    """

    current = compute_trust_anchor(genesis)

    return current != baseline_anchor


# -----------------------------------------------------------------
# FINGERPRINT
# -----------------------------------------------------------------

def trust_fingerprint(genesis: Dict[str, Any]) -> str:
    """
    Short identifier for trust root
    """

    anchor = compute_trust_anchor(genesis)

    return anchor[:16]


# -----------------------------------------------------------------
# DEBUG
# -----------------------------------------------------------------

def __repr__():
    return "<GenesisTrustRoot deterministic>"