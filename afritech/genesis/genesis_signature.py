# afritech/genesis/genesis_signature.py

"""
AfriTech Genesis Signature Module

Purpose:
Provide cryptographic signing and verification for Genesis.

Guarantees:
- payload-only signing (no circular dependency)
- deterministic canonical serialization
- Ed25519 authenticity
- replay-safe verification

Used by:
- genesis_validator
- genesis_loader
"""

from typing import Dict, Any, Tuple

from afritech.genesis.genesis_hash import (
    canonical_json,
    compute_genesis_hash,
)
from afritech.security.ed25519 import (
    sign,
    verify,
    generate_keypair,
)


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class GenesisSignatureError(Exception):
    """Raised when signing or verification fails"""
    pass


# -----------------------------------------------------------------
# INTERNAL PAYLOAD EXTRACTION
# -----------------------------------------------------------------

def _extract_payload_bytes(genesis: Dict[str, Any]) -> bytes:
    """
    Extract canonical payload (EXCLUDING signature)

    This MUST exactly match hashing logic.
    """

    if not isinstance(genesis, dict):
        raise GenesisSignatureError("invalid_genesis_structure")

    payload = {
        k: v
        for k, v in genesis.items()
        if k != "epoch_zero_signature"
    }

    return canonical_json(payload).encode()


# -----------------------------------------------------------------
# SIGN GENESIS (PRIMARY)
# -----------------------------------------------------------------

def sign_genesis(
    genesis: Dict[str, Any],
    private_key_hex: str,
    public_key_hex: str,
) -> Dict[str, Any]:
    """
    Sign genesis payload using Ed25519

    Returns:
        signature block
    """

    try:
        payload_bytes = _extract_payload_bytes(genesis)

        # ✅ Compute payload hash (MUST match validator)
        payload_hash = compute_genesis_hash(genesis)

        # ✅ Sign canonical payload
        signature_hex = sign(payload_bytes, private_key_hex)

        return {
            "algorithm": "ED25519",
            "payload_hash": payload_hash,
            "signature": signature_hex,
            "public_key": public_key_hex,
            "version": "v1",
        }

    except Exception as e:
        raise GenesisSignatureError(f"signing_failed: {e}")


# -----------------------------------------------------------------
# VERIFY SIGNATURE (PRIMARY)
# -----------------------------------------------------------------

def verify_genesis_signature(genesis: Dict[str, Any]) -> bool:
    """
    Verify Ed25519 signature for genesis
    """

    if "epoch_zero_signature" not in genesis:
        raise GenesisSignatureError("missing_signature_block")

    sig = genesis["epoch_zero_signature"]

    required_fields = [
        "payload_hash",
        "signature",
        "public_key",
    ]

    for field in required_fields:
        if field not in sig:
            raise GenesisSignatureError(f"missing_signature_field: {field}")

    # Reject placeholders / unresolved values
    if any(
        not str(sig[field]) or "<" in str(sig[field]) or ">" in str(sig[field])
        for field in required_fields
    ):
        raise GenesisSignatureError("invalid_signature_fields")

    try:
        payload_bytes = _extract_payload_bytes(genesis)
        computed_hash = compute_genesis_hash(genesis)

        # ✅ Verify payload hash consistency
        if sig["payload_hash"] != computed_hash:
            raise GenesisSignatureError("payload_hash_mismatch")

        # ✅ Verify cryptographic signature
        valid = verify(
            payload_bytes,
            sig["signature"],
            sig["public_key"],
        )

        return valid

    except Exception as e:
        raise GenesisSignatureError(f"verification_failed: {e}")


# -----------------------------------------------------------------
# GENERATE NEW SIGNED GENESIS
# -----------------------------------------------------------------

def generate_signed_genesis(
    genesis: Dict[str, Any],
) -> Tuple[Dict[str, Any], str]:
    """
    Convenience function:

    - generates keypair
    - signs genesis
    - returns signed genesis + private key

    NOTE:
    private key MUST be stored securely (not persisted in runtime)
    """

    private_key, public_key = generate_keypair()

    signature_block = sign_genesis(
        genesis,
        private_key,
        public_key,
    )

    genesis["epoch_zero_signature"] = signature_block

    return genesis, private_key


# -----------------------------------------------------------------
# VALIDATE SIGNED GENESIS (STRICT HELPER)
# -----------------------------------------------------------------

def validate_signed_genesis(genesis: Dict[str, Any]) -> bool:
    """
    Full signature validation wrapper
    """

    try:
        return verify_genesis_signature(genesis)
    except GenesisSignatureError:
        return False


# -----------------------------------------------------------------
# SIGNATURE FINGERPRINT
# -----------------------------------------------------------------

def signature_fingerprint(genesis: Dict[str, Any]) -> str:
    """
    Generate fingerprint for identity tracking
    """

    import hashlib

    sig = genesis.get("epoch_zero_signature")

    if not sig:
        raise GenesisSignatureError("missing_signature")

    base = {
        "payload_hash": sig.get("payload_hash"),
        "public_key": sig.get("public_key"),
    }

    return hashlib.sha256(
        canonical_json(base).encode()
    ).hexdigest()[:16]


# -----------------------------------------------------------------
# DEBUG
# -----------------------------------------------------------------

def __repr__():
    return "<GenesisSignature ed25519>"