"""Run field disputes through replay authority."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.replay_authority.engine import DisputeClaim, build_audit_packet, resolve_dispute


@dataclass(frozen=True)
class FieldDisputeResult:
    claim: DisputeClaim
    audit_packet: Mapping[str, Any]
    admitted: bool
    reason: str

    @property
    def dispute_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload = {
            "admitted": self.admitted,
            "audit_packet": self.audit_packet,
            "claim": self.claim.canonical_dict(),
            "reason": self.reason,
        }
        if include_hash:
            payload["dispute_hash"] = self.dispute_hash
        return payload


def run_dispute(
    authoritative_trace: Iterable[Mapping[str, Any]],
    claim: DisputeClaim,
) -> FieldDisputeResult:
    dispute = resolve_dispute(authoritative_trace, (claim,))
    audit_packet = build_audit_packet(dispute).canonical_dict()
    resolution = dispute.resolutions[0]
    return FieldDisputeResult(
        admitted=resolution.admitted,
        audit_packet=audit_packet,
        claim=claim,
        reason=resolution.reason,
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

