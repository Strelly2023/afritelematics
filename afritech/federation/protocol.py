"""Federated verification protocol primitives."""

from __future__ import annotations

import base64
from collections import Counter
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from afritech.models import (
    CrossNodeEventShare,
    FederatedPolicyRecord,
    FederationNode,
)
from afritech.trust_kernel.hashing import canonical_json, sha256_payload


class FederationProtocolError(ValueError):
    """Raised when federation data fails validation."""


MAX_CLOCK_SKEW_SECONDS = 30
MESSAGE_EXPIRY_SECONDS = 60


@dataclass(frozen=True)
class FederationMessage:
    message_id: str
    sender_node_id: str
    receiver_node_id: str
    timestamp: int
    payload: dict[str, Any]
    payload_hash: str
    signature: str
    public_key: str


def register_federation_node(
    *,
    node_id: str,
    region: str,
    public_key: str,
    endpoint: str,
    node_type: str = "regional",
) -> FederationNode:
    _require_text(node_id, "node_id")
    _require_text(region, "region")
    _require_text(public_key, "public_key")
    _require_text(endpoint, "endpoint")
    node, _ = FederationNode.objects.update_or_create(
        node_id=node_id,
        defaults={
            "region": region,
            "public_key": public_key,
            "endpoint": endpoint,
            "node_type": node_type,
            "is_active": True,
        },
    )
    return node


def federation_message_payload_hash(payload: dict[str, Any]) -> str:
    return sha256_payload(payload)


def verify_federation_message(
    message: FederationMessage,
    *,
    now: int,
    allowed_clock_skew_seconds: int = MAX_CLOCK_SKEW_SECONDS,
    message_expiry_seconds: int = MESSAGE_EXPIRY_SECONDS,
) -> None:
    sender = FederationNode.objects.filter(
        node_id=message.sender_node_id,
        is_active=True,
    ).first()
    if sender is None:
        raise FederationProtocolError("sender_node_id is not registered")
    if sender.public_key != message.public_key:
        raise FederationProtocolError("message public_key does not match registered node")
    if message.timestamp > now + allowed_clock_skew_seconds:
        raise FederationProtocolError("federation message timestamp outside allowed window")
    if now - message.timestamp > message_expiry_seconds:
        raise FederationProtocolError("federation message timestamp expired")
    expected_hash = federation_message_payload_hash(message.payload)
    if expected_hash != message.payload_hash:
        raise FederationProtocolError("federation message payload_hash mismatch")
    _verify_ed25519(
        public_key=message.public_key,
        signature=message.signature,
        message=message.payload_hash.encode("utf-8"),
    )


def event_share_from_message(
    message: FederationMessage,
    *,
    now: int,
    independently_verified: bool,
    verification_notes: str = "",
) -> CrossNodeEventShare:
    verify_federation_message(message, now=now)
    payload = message.payload
    return share_remote_event(
        source_node_id=message.sender_node_id,
        remote_event_id=str(payload.get("event_id") or ""),
        remote_event_hash=str(payload.get("event_hash") or ""),
        remote_bundle_root=str(payload.get("bundle_root") or ""),
        remote_state_hash=str(payload.get("state_hash") or ""),
        signature=message.signature,
        independently_verified=independently_verified,
        verification_notes=verification_notes,
    )


def share_remote_event(
    *,
    source_node_id: str,
    remote_event_id: str,
    remote_event_hash: str,
    remote_bundle_root: str,
    remote_state_hash: str,
    signature: str,
    independently_verified: bool,
    verification_notes: str = "",
) -> CrossNodeEventShare:
    node = FederationNode.objects.get(node_id=source_node_id, is_active=True)
    _require_hash(remote_event_hash, "remote_event_hash")
    _require_hash(remote_bundle_root, "remote_bundle_root")
    _require_hash(remote_state_hash, "remote_state_hash")
    _require_text(signature, "signature")
    if not independently_verified:
        raise FederationProtocolError("remote event must be independently replay-verified")
    return CrossNodeEventShare.objects.create(
        source_node=node,
        remote_event_id=remote_event_id,
        remote_event_hash=remote_event_hash,
        remote_bundle_root=remote_bundle_root,
        remote_state_hash=remote_state_hash,
        signature=signature,
        independently_verified=True,
        verification_notes=verification_notes,
    )


def federated_state_agreement(minimum_nodes: int = 2) -> dict[str, object]:
    shares = CrossNodeEventShare.objects.filter(independently_verified=True).select_related(
        "source_node"
    )
    latest_by_node: dict[str, CrossNodeEventShare] = {}
    for share in shares.order_by("-created_at", "id"):
        latest_by_node.setdefault(share.source_node.node_id, share)

    counts = Counter(share.remote_state_hash for share in latest_by_node.values())
    if not counts:
        return {
            "accepted": False,
            "state_hash": None,
            "agreement_count": 0,
            "minimum_nodes": minimum_nodes,
        }
    state_hash, agreement_count = counts.most_common(1)[0]
    return {
        "accepted": agreement_count >= minimum_nodes,
        "state_hash": state_hash,
        "agreement_count": agreement_count,
        "minimum_nodes": minimum_nodes,
    }


def apply_federated_policy(
    *,
    policy_id: str,
    version: str,
    rules: dict[str, Any],
    issuing_authority: str,
    signature: str,
    public_key: str,
) -> FederatedPolicyRecord:
    payload = {
        "policy_id": policy_id,
        "version": version,
        "rules": rules,
        "issuing_authority": issuing_authority,
    }
    _verify_ed25519(
        public_key=public_key,
        signature=signature,
        message=canonical_json(payload).encode("utf-8"),
    )
    record, _ = FederatedPolicyRecord.objects.update_or_create(
        policy_id=policy_id,
        version=version,
        defaults={
            "rules": rules,
            "issuing_authority": issuing_authority,
            "signature": signature,
            "public_key": public_key,
            "verified": True,
        },
    )
    return record


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FederationProtocolError(f"{field} is required")


def _require_hash(value: str, field: str) -> None:
    _require_text(value, field)
    if len(value) != 64:
        raise FederationProtocolError(f"{field} must be a 64-character hash")


def _verify_ed25519(*, public_key: str, signature: str, message: bytes) -> None:
    _require_text(public_key, "public_key")
    _require_text(signature, "signature")
    try:
        key = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(public_key.encode("ascii"), validate=True)
        )
        key.verify(
            base64.b64decode(signature.encode("ascii"), validate=True),
            message,
        )
    except (InvalidSignature, ValueError) as exc:
        raise FederationProtocolError("federation signature invalid") from exc
