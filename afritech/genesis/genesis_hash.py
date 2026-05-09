# afritech/genesis/genesis_hash.py

"""
AfriTech Genesis Hashing Module

Purpose:
Provide canonical hashing for:
- genesis payload (excluding signature)
- full genesis identity (optional extended hash)

Guarantees:
- deterministic canonical serialization
- strict payload isolation
- replay consistency
- cryptographic binding

Used by:
- genesis_signature
- genesis_validator
- genesis_trust_root
"""

import json
import hashlib
from typing import Dict, Any


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class GenesisHashError(Exception):
    """Raised when hashing or canonicalization fails"""
    pass


# -----------------------------------------------------------------
# CANONICAL JSON (CRITICAL)
# -----------------------------------------------------------------

def canonical_json(data: Dict[str, Any]) -> str:
    """
    Deterministic JSON serialization

    RULES:
    - sorted keys
    - compact separators
    - UTF-8 encoding
    """

    try:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except Exception as e:
        raise GenesisHashError(f"canonicalization_failed: {e}")


# -----------------------------------------------------------------
# GENERIC HASH
# -----------------------------------------------------------------

def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(data: Dict[str, Any]) -> str:
    return hash_bytes(canonical_json(data).encode())


# -----------------------------------------------------------------
# CORE PAYLOAD (CRITICAL)
# -----------------------------------------------------------------

def compute_genesis_payload(genesis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract canonical payload (EXCLUDES signature block)

    This is the ONLY content that is signed.
    """

    if not isinstance(genesis, dict):
        raise GenesisHashError("invalid_genesis_structure")

    return {
        k: v
        for k, v in genesis.items()
        if k != "epoch_zero_signature"
    }


# -----------------------------------------------------------------
# PAYLOAD HASH (PRIMARY IDENTITY)
# -----------------------------------------------------------------

def compute_genesis_hash(genesis: Dict[str, Any]) -> str:
    """
    Compute canonical payload hash

    This MUST match:
        signature.payload_hash
    """

    payload = compute_genesis_payload(genesis)
    return hash_obj(payload)


# -----------------------------------------------------------------
# VALIDATE PAYLOAD HASH
# -----------------------------------------------------------------

def validate_payload_hash(genesis: Dict[str, Any]) -> bool:
    """
    Ensure payload_hash matches computed value
    """

    if "epoch_zero_signature" not in genesis:
        raise GenesisHashError("missing_signature_block")

    sig = genesis["epoch_zero_signature"]

    if "payload_hash" not in sig:
        raise GenesisHashError("missing_payload_hash")

    computed = compute_genesis_hash(genesis)

    if sig["payload_hash"] != computed:
        raise GenesisHashError("payload_hash_mismatch")

    return True


# -----------------------------------------------------------------
# EXTENDED GENESIS HASH (OPTIONAL)
# -----------------------------------------------------------------

def compute_extended_genesis_hash(genesis: Dict[str, Any]) -> str:
    """
    Extended identity hash

    Includes:
        - payload hash
        - signature
        - public key

    Useful for:
        - system identity
        - external referencing
    """

    if "epoch_zero_signature" not in genesis:
        raise GenesisHashError("missing_signature_block")

    payload_hash = compute_genesis_hash(genesis)

    sig = genesis["epoch_zero_signature"]

    base = {
        "payload_hash": payload_hash,
        "signature": sig.get("signature"),
        "public_key": sig.get("public_key"),
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# FULL GENESIS HASH (STRICT)
# -----------------------------------------------------------------

def compute_full_genesis_hash(genesis: Dict[str, Any]) -> str:
    """
    Hash entire genesis object (including metadata)

    NOTE:
    This is NOT used for signing (only payload is signed)
    """

    return hash_obj(genesis)


# -----------------------------------------------------------------
# DETECT TAMPERING
# -----------------------------------------------------------------

def is_tampered(genesis: Dict[str, Any]) -> bool:
    """
    Detect if genesis structure is corrupted
    """

    try:
        validate_payload_hash(genesis)
        return False
    except Exception:
        return True
