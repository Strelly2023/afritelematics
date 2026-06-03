"""Audit packets for replay authority decisions."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.replay_authority.engine.dispute_resolver import DisputeResolution


@dataclass(frozen=True)
class AuditPacket:
    dispute: DisputeResolution

    @property
    def audit_hash(self) -> str:
        return _canonical_hash(
            {
                "claims_hash": self.dispute.claims_hash,
                "decisions_hash": self.dispute.reconstruction.decisions_hash,
                "replay_authority_hash": (
                    self.dispute.reconstruction.replay_authority_hash
                ),
                "resolution_hash": self.dispute.resolution_hash,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "audit_hash": self.audit_hash,
            "claims_hash": self.dispute.claims_hash,
            "decisions_hash": self.dispute.reconstruction.decisions_hash,
            "dispute": self.dispute.canonical_dict(),
            "replay_authority_hash": self.dispute.reconstruction.replay_authority_hash,
            "resolution_hash": self.dispute.resolution_hash,
            "schema": "afritech.replay_authority.audit_packet.v1",
            "verified": self.dispute.verified,
        }


def build_audit_packet(dispute: DisputeResolution) -> AuditPacket:
    return AuditPacket(dispute=dispute)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

