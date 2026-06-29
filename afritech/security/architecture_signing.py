"""Signing helpers for NovaRide architecture publications."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.padding import MGF1, PSS
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_der_public_key

from afritech.core_platform import signing as core_signing
from afritech.core_platform.signing import AuditSignature, signing_key_status


MAX_ARCHITECTURE_SIGNATURE_AGE = timedelta(days=7)


def canonical_architecture_bytes(contract: Mapping[str, Any]) -> bytes:
    """Return the canonical serialized bytes used for architecture signing."""

    return json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_json(value: Any) -> bytes:
    """Backward-compatible internal wrapper for canonical architecture bytes."""

    return canonical_architecture_bytes(value)


def _sha256_b64(payload: bytes) -> str:
    return base64.b64encode(hashlib.sha256(payload).digest()).decode("ascii")


def _trusted_key_registry_env_snapshot() -> str:
    return "\u241f".join(
        [
            os.environ.get("NOVATRUST_TRUSTED_ARCHITECTURE_KEYS_JSON", ""),
            os.environ.get("NOVATRUST_SIGNING_PROVIDER", ""),
            os.environ.get("NOVATRUST_SIGNING_KEY_ID", ""),
            os.environ.get("NOVATRUST_KMS_KEY_ID", ""),
            os.environ.get("NOVATRUST_KMS_SIGNING_ENABLED", ""),
            os.environ.get("NOVATRUST_KMS_SIGNING_ALGORITHM", ""),
            os.environ.get("AFRITECH_ENV", ""),
        ]
    )


def _normalise_trusted_key_entry(raw_entry: Any) -> dict[str, str]:
    if isinstance(raw_entry, Mapping):
        if "public_key" not in raw_entry:
            raise ValueError("trusted key entries must include public_key")
        return {
            "public_key": str(raw_entry["public_key"]),
            "status": str(raw_entry.get("status", "active")).strip().lower() or "active",
        }
    return {"public_key": str(raw_entry), "status": "active"}


def _trusted_key_registry_payload() -> tuple[str, dict[str, dict[str, str]]]:
    trusted_keys_json = os.environ.get("NOVATRUST_TRUSTED_ARCHITECTURE_KEYS_JSON")
    status = signing_key_status()
    if trusted_keys_json:
        parsed = json.loads(trusted_keys_json)
        if not isinstance(parsed, dict):
            raise ValueError("NOVATRUST_TRUSTED_ARCHITECTURE_KEYS_JSON must decode to an object")
        active_key_id = str(parsed.get("active_key_id") or status.active_key_id)
        if "keys" in parsed:
            keys_object = parsed["keys"]
            if not isinstance(keys_object, dict):
                raise ValueError(
                    "NOVATRUST_TRUSTED_ARCHITECTURE_KEYS_JSON.keys must decode to an object"
                )
            registry = {
                str(key_id): _normalise_trusted_key_entry(public_key)
                for key_id, public_key in keys_object.items()
            }
        else:
            registry = {
                str(key_id): _normalise_trusted_key_entry(public_key)
                for key_id, public_key in parsed.items()
                if key_id != "active_key_id"
            }
        return active_key_id, registry

    if status.provider == "local_ed25519":
        private_key = core_signing._load_private_key()
        public_key = private_key.public_key().public_bytes(
            Encoding.Raw,
            PublicFormat.Raw,
        )
        return status.active_key_id, {
            status.active_key_id: {
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "status": "active",
            }
        }
    return status.active_key_id, {}


@lru_cache(maxsize=4)
def _trusted_key_registry_cached(env_snapshot: str) -> tuple[str, dict[str, dict[str, str]]]:
    return _trusted_key_registry_payload()


def _trusted_key_registry() -> dict[str, dict[str, str]]:
    return _trusted_key_registry_cached(_trusted_key_registry_env_snapshot())[1]


def trusted_architecture_key_registry() -> dict[str, Any]:
    active_key_id, registry = _trusted_key_registry_payload()
    return {
        "provider": signing_key_status().provider,
        "active_key_id": active_key_id,
        "rotation_enabled": signing_key_status().rotation_enabled,
        "rotation_interval_days": signing_key_status().rotation_interval_days,
        "trusted_keys": [
            {
                "key_id": key_id,
                "public_key": entry["public_key"],
                "status": entry["status"],
                "active": key_id == active_key_id,
            }
            for key_id, entry in sorted(registry.items(), key=lambda item: item[0])
        ],
    }


def _normalize_signature(signature: Mapping[str, Any] | AuditSignature) -> AuditSignature:
    if isinstance(signature, AuditSignature):
        return signature
    data = dict(signature)
    if "value" not in data and "signature" in data:
        data["value"] = data.pop("signature")
    return AuditSignature(
        scheme=str(data["scheme"]),
        signature=str(data["value"]),
        public_key=str(data["public_key"]),
        payload_hash=str(data["payload_hash"]),
        key_id=str(data["key_id"]),
    )


def _signature_timestamp_is_fresh(signature: Mapping[str, Any] | AuditSignature) -> bool:
    if isinstance(signature, AuditSignature):
        return True
    raw_signed_at = signature.get("signed_at")
    if not raw_signed_at:
        return True
    text = str(raw_signed_at)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    signed_at = datetime.fromisoformat(text)
    if signed_at.tzinfo is None:
        signed_at = signed_at.replace(tzinfo=UTC)
    return datetime.now(UTC) - signed_at <= MAX_ARCHITECTURE_SIGNATURE_AGE


def sign_architecture_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Sign a canonical NovaRide architecture contract payload."""

    status = signing_key_status()
    signed_at = datetime.now(UTC).isoformat()
    signed_payload = {"contract": contract, "signed_at": signed_at}
    payload = canonical_architecture_bytes(signed_payload)

    if core_signing._signing_backend() == "aws_kms":
        signature = core_signing._sign_packet_with_kms(payload)
    else:
        private_key = core_signing._load_private_key()
        raw_signature = private_key.sign(payload)
        public_key = private_key.public_key().public_bytes(
            Encoding.Raw,
            PublicFormat.Raw,
        )
        signature = AuditSignature(
            scheme="ed25519",
            signature=base64.b64encode(raw_signature).decode("ascii"),
            public_key=base64.b64encode(public_key).decode("ascii"),
            payload_hash=_sha256_b64(payload),
            key_id=status.active_key_id,
        )

    return {
        "signature_status": "signed",
        "signature_version": 1,
        "signed_payload": signed_payload,
        "signature": {
            "scheme": signature.scheme,
            "value": signature.signature,
            "public_key": signature.public_key,
            "key_id": signature.key_id,
            "payload_hash": signature.payload_hash,
            "signed_at": signed_at,
        },
        "signing": {
            "algorithm": signature.scheme,
            "key_id": signature.key_id,
            "provider": status.provider,
        },
    }


def verify_architecture_signature(
    contract: Mapping[str, Any],
    signature: Mapping[str, Any] | AuditSignature,
) -> bool:
    """Verify a canonical NovaRide architecture contract signature."""

    sig = _normalize_signature(signature)
    trusted_entry = _trusted_key_registry().get(sig.key_id)
    if not trusted_entry or trusted_entry.get("public_key") != sig.public_key:
        return False
    if trusted_entry.get("status", "active") not in {"active", "deprecated"}:
        return False
    signed_at = None
    if isinstance(contract, Mapping) and "contract" in contract and "signed_at" in contract:
        signed_payload = {
            "contract": contract["contract"],
            "signed_at": contract["signed_at"],
        }
        signed_at = contract["signed_at"]
    else:
        if isinstance(signature, Mapping):
            signed_at = signature.get("signed_at")
        if not signed_at:
            return False
        signed_payload = {
            "contract": contract,
            "signed_at": signed_at,
        }
    payload = canonical_architecture_bytes(signed_payload)
    if not _signature_timestamp_is_fresh(signature):
        return False
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
    expected_hash = _sha256_b64(payload)
    if sig.payload_hash != expected_hash:
        return False
    if isinstance(signature, Mapping) and str(signature.get("payload_hash", "")) != expected_hash:
        return False
    return True


__all__ = [
    "canonical_architecture_bytes",
    "trusted_architecture_key_registry",
    "sign_architecture_contract",
    "verify_architecture_signature",
]
