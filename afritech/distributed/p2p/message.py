from __future__ import annotations

from typing import Any, Dict
import uuid
import time


# ---------------------------------------------------------
# Message Builder
# ---------------------------------------------------------

def build_message(
    msg_type: str,
    payload: Dict[str, Any],
    sender_id: str,
    ttl: int = 5,
    version: str = "1.0",
) -> Dict[str, Any]:
    """
    Build a P2P network message.

    Structure:
    {
        "id": str,
        "type": str,
        "sender": str,
        "payload": dict,
        "timestamp": float,
        "ttl": int,
        "version": str
    }

    Features:
    - Unique message ID (UUID)
    - TTL for gossip propagation control
    - Timestamp for ordering/debugging
    - Versioning for protocol evolution
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

    # ✅ Build message
    message: Dict[str, Any] = {
        "id": str(uuid.uuid4()),          # unique message ID
        "type": msg_type,
        "sender": sender_id,
        "payload": payload,
        "timestamp": time.time(),         # seconds since epoch
        "ttl": ttl,                       # hop limit
        "version": version,
    }

    return message


# ---------------------------------------------------------
# TTL handling (gossip support)
# ---------------------------------------------------------

def decrement_ttl(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decrease message TTL for gossip propagation.

    Prevents infinite network loops.
    """

    new_msg = message.copy()

    ttl = new_msg.get("ttl", 0)

    if not isinstance(ttl, int):
        ttl = 0

    new_msg["ttl"] = max(0, ttl - 1)

    return new_msg


def is_expired(message: Dict[str, Any]) -> bool:
    """
    Check if message TTL expired.
    """

    ttl = message.get("ttl", 0)
    return not isinstance(ttl, int) or ttl <= 0


# ---------------------------------------------------------
# Message validation (zero-trust layer)
# ---------------------------------------------------------

def validate_message_structure(message: Dict[str, Any]) -> bool:
    """
    Validate basic message structure before processing.
    """

    required_fields = {
        "id",
        "type",
        "sender",
        "payload",
        "timestamp",
        "ttl",
        "version",
    }

    if not isinstance(message, dict):
        return False

    if not required_fields.issubset(message.keys()):
        return False

    if not isinstance(message["id"], str):
        return False

    if not isinstance(message["type"], str):
        return False

    if not isinstance(message["sender"], str):
        return False

    if not isinstance(message["payload"], dict):
        return False

    if not isinstance(message["timestamp"], (int, float)):
        return False

    if not isinstance(message["ttl"], int):
        return False

    if not isinstance(message["version"], str):
        return False

    return True
