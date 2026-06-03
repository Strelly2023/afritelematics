"""External workflow consumers for replay authority audit packets."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from afritech.trust_lock.engine.dependency_model import ExternalDependency


@dataclass(frozen=True)
class WorkflowResult:
    consumer_id: str
    workflow: str
    accepted: bool
    reason: str
    evidence_hash: str | None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "consumer_id": self.consumer_id,
            "evidence_hash": self.evidence_hash,
            "reason": self.reason,
            "workflow": self.workflow,
        }


def consume_audit_packet(
    dependency: ExternalDependency,
    audit_packet: Mapping[str, Any] | None,
) -> WorkflowResult:
    if audit_packet is None:
        return WorkflowResult(
            accepted=False,
            consumer_id=dependency.consumer_id,
            evidence_hash=None,
            reason="missing_replay_authority_packet",
            workflow=dependency.workflow,
        )
    missing = tuple(
        field for field in dependency.required_evidence if not audit_packet.get(field)
    )
    if missing:
        return WorkflowResult(
            accepted=False,
            consumer_id=dependency.consumer_id,
            evidence_hash=None,
            reason=f"missing_required_evidence:{','.join(missing)}",
            workflow=dependency.workflow,
        )
    if audit_packet.get("verified") is not True:
        return WorkflowResult(
            accepted=False,
            consumer_id=dependency.consumer_id,
            evidence_hash=None,
            reason="audit_packet_not_verified",
            workflow=dependency.workflow,
        )
    return WorkflowResult(
        accepted=True,
        consumer_id=dependency.consumer_id,
        evidence_hash=_canonical_hash(
            {field: audit_packet[field] for field in dependency.required_evidence}
        ),
        reason="accepted_replay_authority_evidence",
        workflow=dependency.workflow,
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

