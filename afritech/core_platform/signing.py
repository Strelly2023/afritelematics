"""Cryptographic signing helpers for NovaTrust audit packets."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.padding import MGF1, PSS
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_der_public_key,
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


@dataclass(frozen=True)
class KmsSigningStatus:
    provider: str
    kms_key_id: str | None
    algorithm: str
    ready: bool
    message: str

    def canonical(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "kms_key_id": self.kms_key_id,
            "algorithm": self.algorithm,
            "ready": self.ready,
            "message": self.message,
        }


def canonical_bytes(packet: Mapping[str, Any]) -> bytes:
    return json.dumps(packet, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )


def sign_packet(packet: Mapping[str, Any]) -> AuditSignature:
    payload = canonical_bytes(packet)
    if _signing_backend() == "aws_kms":
        return _sign_packet_with_kms(payload)
    private_key = _load_private_key()
    signature = private_key.sign(payload)
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return AuditSignature(
        scheme="ed25519",
        signature=base64.b64encode(signature).decode("ascii"),
        public_key=base64.b64encode(public_bytes).decode("ascii"),
        payload_hash=_sha256_b64(payload),
        key_id=signing_key_status().active_key_id,
    )


def verify_packet_signature(
    packet: Mapping[str, Any],
    signature: AuditSignature | Mapping[str, str],
) -> bool:
    sig = signature if isinstance(signature, AuditSignature) else AuditSignature(**dict(signature))
    payload = canonical_bytes(packet)
    try:
        if sig.scheme == "ed25519":
            public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(sig.public_key))
            public_key.verify(base64.b64decode(sig.signature), payload)
        elif sig.scheme.startswith("aws_kms_"):
            public_key = load_der_public_key(base64.b64decode(sig.public_key))
            raw_signature = base64.b64decode(sig.signature)
            if isinstance(public_key, ec.EllipticCurvePublicKey):
                public_key.verify(raw_signature, payload, ec.ECDSA(hashes.SHA256()))
            elif isinstance(public_key, rsa.RSAPublicKey):
                public_key.verify(
                    raw_signature,
                    payload,
                    PSS(mgf=MGF1(hashes.SHA256()), salt_length=PSS.MAX_LENGTH),
                    hashes.SHA256(),
                )
            else:
                return False
        else:
            return False
    except InvalidSignature:
        return False
    return sig.payload_hash == _sha256_b64(payload)


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


def _signing_backend() -> str:
    explicit = os.environ.get("NOVATRUST_SIGNING_PROVIDER", "").strip().lower()
    if explicit in {"aws_kms", "kms"}:
        return "aws_kms"
    if os.environ.get("NOVATRUST_KMS_KEY_ID") and os.environ.get(
        "NOVATRUST_KMS_SIGNING_ENABLED", "false"
    ).lower() in {"1", "true", "yes"}:
        return "aws_kms"
    return "ed25519"


def _sign_packet_with_kms(payload: bytes) -> AuditSignature:
    kms_key_id = os.environ.get("NOVATRUST_KMS_KEY_ID")
    if not kms_key_id:
        raise RuntimeError("novatrust_kms_key_id_required")
    if find_spec("boto3") is None:
        raise RuntimeError("boto3_required_for_aws_kms_signing")
    import boto3  # type: ignore[import-not-found]

    algorithm = os.environ.get("NOVATRUST_KMS_SIGNING_ALGORITHM", "ECDSA_SHA_256")
    if algorithm not in {"ECDSA_SHA_256", "RSASSA_PSS_SHA_256"}:
        raise ValueError("unsupported_kms_signing_algorithm")
    client = boto3.client("kms", region_name=os.environ.get("AWS_REGION"))
    response = client.sign(
        KeyId=kms_key_id,
        Message=payload,
        MessageType="RAW",
        SigningAlgorithm=algorithm,
    )
    public_key_response = client.get_public_key(KeyId=response["KeyId"])
    public_key = public_key_response["PublicKey"]
    return AuditSignature(
        scheme=f"aws_kms_{algorithm.lower()}",
        signature=base64.b64encode(response["Signature"]).decode("ascii"),
        public_key=base64.b64encode(public_key).decode("ascii"),
        payload_hash=_sha256_b64(payload),
        key_id=str(response["KeyId"]),
    )


def signing_key_status() -> SigningKeyStatus:
    kms_key_id = os.environ.get("NOVATRUST_KMS_KEY_ID")
    configured_key_id = os.environ.get("NOVATRUST_SIGNING_KEY_ID")
    provider = "aws_kms" if _signing_backend() == "aws_kms" else "local_ed25519"
    return SigningKeyStatus(
        active_key_id=configured_key_id
        or ("novatrust-kms-ed25519" if kms_key_id else "novatrust-dev-ed25519"),
        provider=provider,
        kms_key_id=kms_key_id,
        rotation_enabled=os.environ.get("NOVATRUST_KEY_ROTATION_ENABLED", "true").lower()
        in {"1", "true", "yes"},
        rotation_interval_days=int(os.environ.get("NOVATRUST_KEY_ROTATION_DAYS", "90")),
    )


def kms_signing_status() -> KmsSigningStatus:
    kms_key_id = os.environ.get("NOVATRUST_KMS_KEY_ID")
    algorithm = os.environ.get("NOVATRUST_KMS_SIGNING_ALGORITHM", "ECDSA_SHA_256")
    backend = _signing_backend()
    ready = backend == "aws_kms" and kms_key_id is not None and find_spec("boto3") is not None
    if backend != "aws_kms":
        return KmsSigningStatus(
            provider="local_ed25519",
            kms_key_id=kms_key_id,
            algorithm="ED25519",
            ready=False,
            message="local Ed25519 signing active",
        )
    return KmsSigningStatus(
        provider="aws_kms",
        kms_key_id=kms_key_id,
        algorithm=algorithm,
        ready=ready,
        message=(
            "AWS KMS signing active"
            if ready
            else "AWS KMS signing is configured but not ready"
        ),
    )


def signing_key_ready() -> bool:
    environment = os.environ.get("AFRITECH_ENV", "development").lower()
    if environment not in {"production", "prod"}:
        return True
    if _signing_backend() == "aws_kms":
        return bool(os.environ.get("NOVATRUST_KMS_KEY_ID")) and find_spec("boto3") is not None
    return bool(os.environ.get("NOVATRUST_ED25519_PRIVATE_KEY_B64"))


def build_key_rotation_plan() -> dict[str, object]:
    status = signing_key_status()
    return {
        "view": "novatrust_key_rotation_plan",
        "status": status.canonical(),
        "kms": kms_signing_status().canonical(),
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
