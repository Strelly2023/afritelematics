"""Ed25519 signing for registry verification."""

from __future__ import annotations

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from afritech.security.key_manager import SigningProvider, default_signing_provider


def public_key_hex(provider: SigningProvider | None = None) -> str:
    resolved_provider = provider or default_signing_provider()
    return resolved_provider.public_key().hex()


def signer_id(provider: SigningProvider | None = None) -> str:
    resolved_provider = provider or default_signing_provider()
    return resolved_provider.signer_id


def sign_registry(hash_value: str, provider: SigningProvider | None = None) -> str:
    resolved_provider = provider or default_signing_provider()
    return resolved_provider.sign(hash_value.encode("utf-8")).hex()


def verify_signature(public_key: str, signature: str, message: str) -> bool:
    try:
        VerifyKey(bytes.fromhex(public_key)).verify(
            message.encode("utf-8"),
            bytes.fromhex(signature),
        )
    except (BadSignatureError, ValueError):
        return False
    return True


__all__ = [
    "public_key_hex",
    "sign_registry",
    "signer_id",
    "verify_signature",
]
