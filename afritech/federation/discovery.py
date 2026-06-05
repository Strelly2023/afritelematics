from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from afritech.models import NodeAnnouncementRecord
from afritech.trust_kernel.hashing import canonical_json


class NodeDiscoveryError(ValueError):
    """Raised when node discovery data cannot be trusted."""


@dataclass(frozen=True)
class NodeAnnouncement:
    node_id: str
    public_key: str
    region: str
    capabilities: tuple[str, ...]
    endpoint: str
    governance_version: str
    signature: str

    def signing_payload(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "public_key": self.public_key,
            "region": self.region,
            "capabilities": list(self.capabilities),
            "endpoint": self.endpoint,
            "governance_version": self.governance_version,
        }


def accept_node_announcement(
    announcement: NodeAnnouncement,
) -> NodeAnnouncementRecord:
    _verify_announcement_signature(announcement)
    _guard_capabilities(announcement.capabilities)
    record, _ = NodeAnnouncementRecord.objects.update_or_create(
        node_id=announcement.node_id,
        governance_version=announcement.governance_version,
        defaults={
            "public_key": announcement.public_key,
            "region": announcement.region,
            "capabilities": list(announcement.capabilities),
            "endpoint": announcement.endpoint,
            "signature": announcement.signature,
            "verified": True,
        },
    )
    return record


def peer_exchange_records() -> list[dict[str, Any]]:
    return [
        {
            "node_id": row.node_id,
            "region": row.region,
            "capabilities": row.capabilities,
            "endpoint": row.endpoint,
            "governance_version": row.governance_version,
            "verified": row.verified,
        }
        for row in NodeAnnouncementRecord.objects.filter(verified=True).order_by(
            "region",
            "node_id",
        )
    ]


def _verify_announcement_signature(announcement: NodeAnnouncement) -> None:
    try:
        key = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(announcement.public_key.encode("ascii"), validate=True)
        )
        key.verify(
            base64.b64decode(announcement.signature.encode("ascii"), validate=True),
            canonical_json(announcement.signing_payload()).encode("utf-8"),
        )
    except (InvalidSignature, ValueError) as exc:
        raise NodeDiscoveryError("node announcement signature invalid") from exc


def _guard_capabilities(capabilities: tuple[str, ...]) -> None:
    if not capabilities:
        raise NodeDiscoveryError("node capabilities are required")
    for capability in capabilities:
        if not isinstance(capability, str) or not capability.strip():
            raise NodeDiscoveryError("node capability must be non-empty text")
