from __future__ import annotations

import base64
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from afritech.models import DeviceKey, EventRecord
from afritech.trust_kernel.hashing import canonical_json


SIGNATURE_MODE_ED25519 = "ed25519"
SIGNATURE_MODE_DEVELOPMENT_ADAPTER = "development_adapter"


def command_signature_message(
    *,
    event_type: str,
    actor_id: str,
    subject_id: str,
    payload: dict[str, Any],
) -> bytes:
    return canonical_json(
        {
            "event_type": event_type,
            "actor_id": actor_id,
            "subject_id": subject_id,
            "payload": payload,
        }
    ).encode("utf-8")


def verify_command_signature(
    *,
    event_type: str,
    actor_id: str,
    subject_id: str,
    payload: dict[str, Any],
    signature: dict[str, Any],
) -> None:
    mode = signature.get("signature_mode")
    if mode == SIGNATURE_MODE_DEVELOPMENT_ADAPTER:
        _guard_development_signature_not_registered(actor_id, signature)
        return
    if mode != SIGNATURE_MODE_ED25519:
        raise ValueError("UNSUPPORTED_SIGNATURE_MODE")

    device_id = signature.get("device_id")
    signature_value = signature.get("signature")
    if not isinstance(device_id, str) or not device_id.strip():
        raise ValueError("signature.device_id is required")
    if not isinstance(signature_value, str) or not signature_value.strip():
        raise ValueError("signature.signature is required")

    device_key = DeviceKey.objects.filter(
        actor_id=actor_id,
        device_id=device_id,
        is_active=True,
    ).first()
    if device_key is None:
        raise ValueError("ACTIVE_DEVICE_KEY_NOT_FOUND")

    public_key = Ed25519PublicKey.from_public_bytes(_decode_b64(device_key.public_key))
    try:
        public_key.verify(
            _decode_b64(signature_value),
            command_signature_message(
                event_type=event_type,
                actor_id=actor_id,
                subject_id=subject_id,
                payload=payload,
            ),
        )
    except InvalidSignature as exc:
        raise ValueError("EVENT_SIGNATURE_INVALID") from exc


def stored_event_signature_verified(event: EventRecord) -> bool:
    try:
        verify_command_signature(
            event_type=event.event_type,
            actor_id=event.actor_id,
            subject_id=event.subject_id,
            payload=event.payload,
            signature=event.signature,
        )
    except Exception:
        return False
    return event.signature.get("signature_mode") == SIGNATURE_MODE_ED25519


def _guard_development_signature_not_registered(
    actor_id: str,
    signature: dict[str, Any],
) -> None:
    device_id = signature.get("device_id")
    query = DeviceKey.objects.filter(actor_id=actor_id, is_active=True)
    if isinstance(device_id, str) and device_id.strip():
        query = query.filter(device_id=device_id)
    if query.exists():
        raise ValueError("REGISTERED_DEVICE_REQUIRES_CRYPTOGRAPHIC_SIGNATURE")


def _decode_b64(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:
        raise ValueError("INVALID_BASE64_SIGNATURE_MATERIAL") from exc
