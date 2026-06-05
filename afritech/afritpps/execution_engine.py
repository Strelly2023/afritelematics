"""Trust-bound AfriTPPS execution engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from afritech.afritpps.constants import (
    AFRITPPS_COMPONENT,
    AFRITPPS_PILLAR,
    assert_afritpps_constitution,
)
from afritech.models import EvidenceBundle
from afritech.trust_kernel.events import process_client_command, process_command
from afritech.trust_kernel.policy import Command
from afritech.trust_kernel.projections import get_subject_projection, projection_hash
from afritech.trust_kernel.signatures import SIGNATURE_MODE_ED25519


AFRITPPS_EVENT_TYPE = "AfriTPPSOperationExecuted"


class AfriTPPSExecutionError(RuntimeError):
    """Raised when AfriTPPS cannot produce a verified execution outcome."""


@dataclass(frozen=True)
class AfriTPPSOperationIntent:
    operation_id: str
    domain: str
    actor_id: str
    subject_id: str
    action: str
    expected_outcome: str
    payload: dict[str, Any]
    signature: dict[str, Any]
    witnesses: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def command_payload(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "domain": self.domain,
            "action": self.action,
            "expected_outcome": self.expected_outcome,
            "payload": self.payload,
            "status": "executed",
        }


@dataclass(frozen=True)
class AfriTPPSExecutionOutcome:
    operation_id: str
    domain: str
    action: str
    event_id: str
    event_hash: str
    evidence_bundle_hash: str
    evidence_bundle_root: str
    replay_state_hash: str
    subject_projection: dict[str, Any] | None
    verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "component": AFRITPPS_COMPONENT,
            "pillar": AFRITPPS_PILLAR,
            "operation_id": self.operation_id,
            "domain": self.domain,
            "action": self.action,
            "event_id": self.event_id,
            "event_hash": self.event_hash,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "evidence_bundle_root": self.evidence_bundle_root,
            "replay_state_hash": self.replay_state_hash,
            "subject_projection": self.subject_projection,
            "verified": self.verified,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


def execute_operation(
    intent: AfriTPPSOperationIntent,
    *,
    require_client_signature: bool = False,
) -> AfriTPPSExecutionOutcome:
    assert_afritpps_constitution()
    _guard_intent(intent)
    command = Command(
        event_type=AFRITPPS_EVENT_TYPE,
        actor_id=intent.actor_id,
        subject_id=intent.subject_id,
        payload=intent.command_payload(),
        signature=intent.signature,
        witnesses=intent.witnesses,
    )
    event = (
        process_client_command(command)
        if require_client_signature
        else process_command(command)
    )
    bundle = EvidenceBundle.objects.filter(event=event).first()
    if bundle is None:
        raise AfriTPPSExecutionError("AfriTPPS execution produced no evidence bundle")

    bundle_root = bundle.receipts.get("bundle_root")
    if not isinstance(bundle_root, str) or len(bundle_root) != 64:
        raise AfriTPPSExecutionError("AfriTPPS execution produced invalid bundle root")

    outcome = AfriTPPSExecutionOutcome(
        operation_id=intent.operation_id,
        domain=intent.domain,
        action=intent.action,
        event_id=str(event.event_id),
        event_hash=event.event_hash,
        evidence_bundle_hash=bundle.bundle_hash,
        evidence_bundle_root=bundle_root,
        replay_state_hash=projection_hash(),
        subject_projection=get_subject_projection(intent.subject_id),
        verified=True,
    )
    if not outcome.verified:
        raise AfriTPPSExecutionError("AfriTPPS claimed an unverified outcome")
    return outcome


def _guard_intent(intent: AfriTPPSOperationIntent) -> None:
    for field_name in (
        "operation_id",
        "domain",
        "actor_id",
        "subject_id",
        "action",
        "expected_outcome",
    ):
        value = getattr(intent, field_name)
        if not isinstance(value, str) or not value.strip():
            raise AfriTPPSExecutionError(f"{field_name} is required")
    if not isinstance(intent.payload, dict):
        raise AfriTPPSExecutionError("payload must be a dictionary")
    if not isinstance(intent.signature, dict):
        raise AfriTPPSExecutionError("signature must be a dictionary")


def is_client_signed(intent: AfriTPPSOperationIntent) -> bool:
    return intent.signature.get("signature_mode") == SIGNATURE_MODE_ED25519
