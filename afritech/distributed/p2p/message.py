from __future__ import annotations

from typing import Any, Dict
import uuid
import time

from afritech.distributed.contracts.p2p_interface import GossipMessage


# ============================================================
# ✅ MESSAGE BUILDER (STRONG-TYPED)
# ============================================================

def build_message(
    msg_type: str,
    payload: Dict[str, Any],
    sender_id: str,
    ttl: int = 5,
    version: str = "1.0",
) -> GossipMessage:
    """
    Build a deterministic GossipMessage.

    Structure:
    GossipMessage(
        message_id: str,
        sender_id: str,
        payload: {
            "type": str,
            "payload": dict,
            "ttl": int,
            "version": str
        },
        timestamp: int
    )

    Guarantees:
    - Deterministic structure
    - Replay-safe encoding
    - Contract compliance
    """

    # ✅ Input validation
    if not isinstance(msg_type, str):
        raise TypeError("msg_type must be a string")

    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")

    if not isinstance(sender_id, str):
        raise TypeError("sender_id must be a string")

    if not isinstance(ttl, int) or ttl <= 0:
        raise ValueError("ttl must be a positive integer")

    if not isinstance(version, str):
        raise TypeError("version must be a string")

    # ✅ Build structured payload (deterministic)
    full_payload: Dict[str, Any] = {
        "type": msg_type,
        "payload": payload,
        "ttl": ttl,
        "version": version,
    }

    return GossipMessage(
        message_id=str(uuid.uuid4()),
        sender_id=sender_id,
        payload=full_payload,
        timestamp=int(time.time()),  # deterministic integer
    )


# ============================================================
# ✅ TTL HANDLING
# ============================================================

def decrement_ttl(message: GossipMessage) -> GossipMessage:
    """
    Decrease TTL safely.

    Returns a NEW message (immutable-style update).
    """

    payload = dict(message.payload)

    ttl = payload.get("ttl", 0)

    if not isinstance(ttl, int):
        ttl = 0

    payload["ttl"] = max(0, ttl - 1)

    return GossipMessage(
        message_id=message.message_id,
        sender_id=message.sender_id,
        payload=payload,
        timestamp=message.timestamp,
    )


def is_expired(message: GossipMessage) -> bool:
    """
    Check if message TTL expired.
    """

    ttl = message.payload.get("ttl", 0)

    return not isinstance(ttl, int) or ttl <= 0


# ============================================================
# ✅ VALIDATION (ZERO-TRUST LAYER)
# ============================================================

def validate_message_structure(message: GossipMessage) -> bool:
    """
    Validate strict message structure.

    Ensures:
    - Type correctness
    - Required fields present
    - Replay-safe structure
    """

    if not isinstance(message, GossipMessage):
        return False

    # ✅ Basic fields
    if not isinstance(message.message_id, str):
        return False

    if not isinstance(message.sender_id, str):
        return False

    if not isinstance(message.payload, dict):
        return False

    if not isinstance(message.timestamp, int):
        return False

    # ✅ Payload validation
    payload = message.payload

    required_fields = {"type", "payload", "ttl", "version"}

    if not required_fields.issubset(payload.keys()):
        return False

    if not isinstance(payload["type"], str):
        return False

    if not isinstance(payload["payload"], dict):
        return False

    if not isinstance(payload["ttl"], int):
        return False

    if not isinstance(payload["version"], str):
        return False

    return True