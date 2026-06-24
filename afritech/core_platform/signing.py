"""Cryptographic signing helpers for NovaTrust audit packets."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)


_DEV_PRIVATE_KEY_SEED = b"NovaTechCorePlatformDevSigning!!"[:32]


@dataclass(frozen=True)
class AuditSignature:
    scheme: str
    signature: str
    public_key: str
    payload_hash: str
    key_id: str

    def canonical(self) -> dict[str, str]:
        return {
            "scheme": self.scheme,
            "signature": self.signature,
            "public_key": self.public_key,
            "payload_hash": self.payload_hash,
            "key_id": self.key_id,
        }


@dataclass(frozen=True)
class SigningKeyStatus:
    active_key_id: str
    provider: str
    kms_key_id: str | None
    rotation_enabled: bool
    rotation_interval_days: int

    def canonical(self) -> dict[str, object]:
        return {
            "active_key_id": self.active_key_id,
            "provider": self.provider,
            "kms_key_id": self.kms_key_id,
            "rotation_enabled": self.rotation_enabled,
            "rotation_interval_days": self.rotation_interval_days,
        }


def canonical_bytes(packet: Mapping[str, Any]) -> bytes:
    return json.dumps(packet, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sign_packet(packet: Mapping[str, Any]) -> AuditSignature:
    payload = canonical_bytes(packet)
    private_key = _load_private_key()
    signature = private_key.sign(payload)
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    signature_b64 = base64.b64encode(signature).decode("ascii")
    public_key_b64 = base64.b64encode(public_bytes).decode("ascii")
    return AuditSignature(
        scheme="ed25519",
        signature=signature_b64,
        public_key=public_key_b64,
        payload_hash=_sha256_b64(payload),
        key_id=signing_key_status().active_key_id,
    )


def verify_packet_signature(packet: Mapping[str, Any], signature: AuditSignature | Mapping[str, str]) -> bool:
    sig = signature if isinstance(signature, AuditSignature) else AuditSignature(**dict(signature))
    public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(sig.public_key))
    try:
        public_key.verify(base64.b64decode(sig.signature), canonical_bytes(packet))
    except InvalidSignature:
        return False
    return sig.payload_hash == _sha256_b64(canonical_bytes(packet))


def _load_private_key() -> Ed25519PrivateKey:
    encoded = os.environ.get("NOVATRUST_ED25519_PRIVATE_KEY_B64")
    if encoded:
        raw = base64.b64decode(encoded)
        if len(raw) != 32:
            raise ValueError("NOVATRUST_ED25519_PRIVATE_KEY_B64 must decode to 32 bytes")
        return Ed25519PrivateKey.from_private_bytes(raw)
    environment = os.environ.get("AFRITECH_ENV", "development").lower()
    if environment in {"production", "prod"}:
        raise RuntimeError("production_novatrust_signing_key_required")
    return Ed25519PrivateKey.from_private_bytes(_DEV_PRIVATE_KEY_SEED)


def signing_key_status() -> SigningKeyStatus:
    kms_key_id = os.environ.get("NOVATRUST_KMS_KEY_ID")
    configured_key_id = os.environ.get("NOVATRUST_SIGNING_KEY_ID")
    return SigningKeyStatus(
        active_key_id=configured_key_id or ("novatrust-kms-ed25519" if kms_key_id else "novatrust-dev-ed25519"),
        provider="aws_kms_metadata_only" if kms_key_id else "local_ed25519",
        kms_key_id=kms_key_id,
        rotation_enabled=os.environ.get("NOVATRUST_KEY_ROTATION_ENABLED", "true").lower() in {"1", "true", "yes"},
        rotation_interval_days=int(os.environ.get("NOVATRUST_KEY_ROTATION_DAYS", "90")),
    )


def signing_key_ready() -> bool:
    environment = os.environ.get("AFRITECH_ENV", "development").lower()
    if environment not in {"production", "prod"}:
        return True
    return bool(os.environ.get("NOVATRUST_ED25519_PRIVATE_KEY_B64"))


def build_key_rotation_plan() -> dict[str, object]:
    status = signing_key_status()
    return {
        "view": "novatrust_key_rotation_plan",
        "status": status.canonical(),
        "steps": [
            "Generate or select next Ed25519/KMS signing key",
            "Publish next public key to verifier metadata",
            "Dual-sign audit packets during transition window",
            "Promote next key after external verifier acceptance",
            "Retire previous key after retention window",
        ],
        "kms_ready": status.provider == "aws_kms",
    }


def _sha256_b64(payload: bytes) -> str:
    import hashlib

    return base64.b64encode(hashlib.sha256(payload).digest()).decode("ascii")
