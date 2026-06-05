from __future__ import annotations

from typing import Any, Dict
import time
import hashlib
import json

from afritech.distributed.contracts.p2p_interface import (
    GossipMessage,
    MessagePayload,
)
from afritech.epoch.compiled.semantic_epoch import EpochType, SemanticEpoch
from afritech.epoch.epoch_snapshot import EpochSnapshot


# ============================================================
# ✅ INTERNAL: DETERMINISTIC HASH
# ============================================================

def _compute_message_id(
    sender_id: str,
    payload: Dict[str, Any],
    timestamp: int,
) -> str:
    """
    Deterministic message identity (hash-based).
    """

    base = json.dumps(
        {
            "sender_id": sender_id,
            "payload": payload,
            "timestamp": timestamp,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(base).hexdigest()


# ============================================================
# ✅ MESSAGE BUILDER (FINAL)
# ============================================================

def build_message(
    msg_type: str,
    payload: Dict[str, Any],
    sender_id: str,
    ttl: int = 5,
    version: str = "1.0",
) -> GossipMessage:

    if not isinstance(msg_type, str):
        raise TypeError("msg_type must be a string")

    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")

    if not isinstance(sender_id, str):
        raise TypeError("sender_id must be a string")

    if not isinstance(ttl, int) or ttl <= 0:
        raise ValueError("ttl must be positive integer")

    if not isinstance(version, str):
        raise TypeError("version must be a string")

    timestamp = int(time.time())

    # ✅ Typed payload (IMPORTANT FIX)
    message_payload = MessagePayload(
        type=msg_type,
        payload=payload,
        ttl=ttl,
        version=version,
    )

    # ✅ Hash uses DICT representation (for serialization)
    message_id = _compute_message_id(
        sender_id,
        {
            "type": msg_type,
            "payload": payload,
            "ttl": ttl,
            "version": version,
        },
        timestamp,
    )

    return GossipMessage(
        message_id=message_id,
        sender_id=sender_id,
        payload=message_payload,
        timestamp=timestamp,
    )


# ============================================================
# ✅ TTL HANDLING (IMMUTABLE)
# ============================================================

def decrement_ttl(message: GossipMessage) -> GossipMessage:
    payload = message.payload

    new_payload = MessagePayload(
        type=payload.type,
        payload=payload.payload,
        ttl=max(0, payload.ttl - 1),
        version=payload.version,
    )

    return GossipMessage(
        message_id=message.message_id,
        sender_id=message.sender_id,
        payload=new_payload,
        timestamp=message.timestamp,
    )


def is_expired(message: GossipMessage) -> bool:
    return message.payload.ttl <= 0


# ============================================================
# ✅ NETWORK CODEC
# ============================================================

def message_to_dict(message: GossipMessage) -> Dict[str, Any]:
    if not validate_message_structure(message):
        raise ValueError("Invalid GossipMessage")

    return {
        "message_id": message.message_id,
        "sender_id": message.sender_id,
        "payload": {
            "type": message.payload.type,
            "payload": _encode_payload(message.payload.payload),
            "ttl": message.payload.ttl,
            "version": message.payload.version,
        },
        "timestamp": message.timestamp,
    }


def message_from_dict(data: Dict[str, Any]) -> GossipMessage:
    if not isinstance(data, dict):
        raise TypeError("message data must be a dictionary")

    payload_root = data.get("payload")
    if not isinstance(payload_root, dict):
        raise ValueError("message payload must be a dictionary")

    payload = MessagePayload(
        type=payload_root.get("type", ""),
        payload=_decode_payload(payload_root.get("payload", {})),
        ttl=payload_root.get("ttl", 0),
        version=payload_root.get("version", ""),
    )

    message = GossipMessage(
        message_id=data.get("message_id", ""),
        sender_id=data.get("sender_id", ""),
        payload=payload,
        timestamp=data.get("timestamp", 0),
    )

    if not validate_message_structure(message):
        raise ValueError("Invalid GossipMessage structure")

    return message


def _encode_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    encoded: Dict[str, Any] = {}

    for key, value in payload.items():
        if isinstance(value, EpochSnapshot):
            encoded[key] = {
                "__type__": "EpochSnapshot",
                "semantic_epoch": value.semantic_epoch.to_dict(),
                "epoch_hash": value.epoch_hash,
            }
        else:
            encoded[key] = value

    return encoded


def _decode_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    decoded: Dict[str, Any] = {}

    for key, value in payload.items():
        if (
            isinstance(value, dict)
            and value.get("__type__") == "EpochSnapshot"
        ):
            decoded[key] = _decode_epoch_snapshot(value)
        else:
            decoded[key] = value

    return decoded


def _decode_epoch_snapshot(data: Dict[str, Any]) -> EpochSnapshot:
    semantic_data = data.get("semantic_epoch")
    if not isinstance(semantic_data, dict):
        raise ValueError("Invalid semantic epoch payload")

    epoch_type = semantic_data.get("epoch_type")
    if isinstance(epoch_type, str):
        try:
            semantic_data = dict(semantic_data)
            semantic_data["epoch_type"] = EpochType[epoch_type].value
        except KeyError:
            pass

    semantic_epoch = SemanticEpoch.from_dict(semantic_data)
    epoch_hash = data.get("epoch_hash")

    if not isinstance(epoch_hash, str) or not epoch_hash:
        raise ValueError("Invalid epoch hash")

    return EpochSnapshot(
        semantic_epoch=semantic_epoch,
        epoch_hash=epoch_hash,
    )


# ============================================================
# ✅ VALIDATION (FINAL)
# ============================================================

def validate_message_structure(message: GossipMessage) -> bool:

    if not isinstance(message, GossipMessage):
        return False

    if not isinstance(message.message_id, str):
        return False

    if not isinstance(message.sender_id, str):
        return False

    if not isinstance(message.payload, MessagePayload):
        return False

    if not isinstance(message.timestamp, int):
        return False

    payload = message.payload

    if not isinstance(payload.type, str):
        return False

    if not isinstance(payload.payload, dict):
        return False

    if not isinstance(payload.ttl, int):
        return False

    if not isinstance(payload.version, str):
        return False

    # ✅ replay/time sanity
    now = int(time.time())
    if abs(now - message.timestamp) > 300:
        return False

    return True
