# afritech/security/ed25519.py

"""
AfriTech Ed25519 Cryptographic Module

Provides:
- Key generation
- Deterministic signing
- Signature verification
- Key serialization

Security Goals:
- deterministic behavior
- strict validation
- tamper resistance
- hex-safe encoding

Used by:
- CertificateCompiler
- AdmissionEngine
- Federation verification
"""

from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError
from typing import Tuple


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class CryptoError(Exception):
    """Raised when cryptographic operation fails"""
    pass


# -----------------------------------------------------------------
# KEY GENERATION
# -----------------------------------------------------------------

def generate_keypair() -> Tuple[str, str]:
    """
    Generate a new Ed25519 keypair

    Returns:
        (private_key_hex, public_key_hex)
    """
    try:
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        return (
            signing_key.encode().hex(),
            verify_key.encode().hex(),
        )
    except Exception as e:
        raise CryptoError(f"key_generation_failed: {e}")


# -----------------------------------------------------------------
# LOAD KEYS
# -----------------------------------------------------------------

def load_private_key(private_key_hex: str) -> SigningKey:
    """
    Load signing key from hex
    """
    try:
        return SigningKey(bytes.fromhex(private_key_hex))
    except Exception:
        raise CryptoError("invalid_private_key")


def load_public_key(public_key_hex: str) -> VerifyKey:
    """
    Load verify key from hex
    """
    try:
        return VerifyKey(bytes.fromhex(public_key_hex))
    except Exception:
        raise CryptoError("invalid_public_key")


# -----------------------------------------------------------------
# SIGN
# -----------------------------------------------------------------

def sign(message: bytes, private_key_hex: str) -> str:
    """
    Sign a message

    Args:
        message: raw bytes (already canonicalized)
        private_key_hex: hex-encoded private key

    Returns:
        signature (hex string)
    """

    if not isinstance(message, (bytes, bytearray)):
        raise CryptoError("message_must_be_bytes")

    try:
        signing_key = load_private_key(private_key_hex)
        signed = signing_key.sign(message)

        return signed.signature.hex()

    except Exception as e:
        raise CryptoError(f"signing_failed: {e}")


# -----------------------------------------------------------------
# VERIFY
# -----------------------------------------------------------------

def verify(message: bytes, signature_hex: str, public_key_hex: str) -> bool:
    """
    Verify Ed25519 signature

    Args:
        message: raw bytes
        signature_hex: hex signature
        public_key_hex: hex public key

    Returns:
        True if valid, False otherwise
    """

    if not isinstance(message, (bytes, bytearray)):
        return False

    try:
        verify_key = load_public_key(public_key_hex)

        verify_key.verify(
            message,
            bytes.fromhex(signature_hex)
        )

        return True

    except (BadSignatureError, ValueError):
        return False
    except Exception:
        return False


# -----------------------------------------------------------------
# DETERMINISTIC SIGNING HELPER
# -----------------------------------------------------------------

def sign_canonical_json(data: dict, private_key_hex: str) -> str:
    """
    Deterministic JSON signing

    Ensures:
    - stable ordering
    - consistent encoding
    """

    import json

    try:
        serialized = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

        return sign(serialized, private_key_hex)

    except Exception as e:
        raise CryptoError(f"canonical_sign_failed: {e}")


# -----------------------------------------------------------------
# VERIFY HELPER
# -----------------------------------------------------------------

def verify_canonical_json(
    data: dict,
    signature_hex: str,
    public_key_hex: str
) -> bool:
    """
    Verify canonical JSON signature
    """

    import json

    try:
        serialized = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

        return verify(serialized, signature_hex, public_key_hex)

    except Exception:
        return False


# -----------------------------------------------------------------
# KEY FINGERPRINT
# -----------------------------------------------------------------

def key_fingerprint(public_key_hex: str) -> str:
    """
    Produce stable identifier for public key
    """

    import hashlib

    try:
        return hashlib.sha256(
            bytes.fromhex(public_key_hex)
        ).hexdigest()[:16]

    except Exception:
        raise CryptoError("invalid_key_for_fingerprint")


# -----------------------------------------------------------------
# SELF TEST (OPTIONAL DEBUG)
# -----------------------------------------------------------------

def self_test() -> bool:
    """
    Basic cryptographic self-test

    Ensures:
    - sign → verify cycle works
    """

    try:
        priv, pub = generate_keypair()

        message = b"afritech_test_vector"

        signature = sign(message, priv)

        return verify(message, signature, pub)

    except Exception:
        return False