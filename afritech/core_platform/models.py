"""Core NovaTech platform contracts.

The models here are deliberately small and deterministic. They form a stable
contract between NovaID, NovaPower, NovaPay, NovaTrust, NovaScript, and
NovaProgramming without importing product applications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping


@dataclass(frozen=True)
class Identity:
    identity_id: str
    email: str
    roles: tuple[str, ...]
    organization_id: str
    scopes: tuple[str, ...] = field(default_factory=tuple)
    devices: tuple[str, ...] = field(default_factory=tuple)
    kyc_status: str = "unverified"

    def canonical(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "email": self.email,
            "roles": list(self.roles),
            "organization_id": self.organization_id,
            "scopes": list(self.scopes),
            "devices": list(self.devices),
            "kyc_status": self.kyc_status,
        }


@dataclass(frozen=True)
class AuthorityRequest:
    action: str
    organization_id: str
    required_roles: tuple[str, ...] = field(default_factory=tuple)
    required_scopes: tuple[str, ...] = field(default_factory=tuple)
    resource_owner_id: str | None = None
    risk_score: Decimal = Decimal("0")
    risk_score_max: Decimal = Decimal("0.70")
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "organization_id": self.organization_id,
            "required_roles": list(self.required_roles),
            "required_scopes": list(self.required_scopes),
            "resource_owner_id": self.resource_owner_id,
            "risk_score": str(self.risk_score),
            "risk_score_max": str(self.risk_score_max),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AuthorityDecision:
    decision: str
    reason: str
    trace_id: str
    checks: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.decision == "ALLOW"

    def canonical(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "trace_id": self.trace_id,
            "checks": list(self.checks),
        }


@dataclass(frozen=True)
class PaymentIntent:
    intent_id: str
    actor_id: str
    organization_id: str
    amount: Decimal
    currency: str
    destination: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "actor_id": self.actor_id,
            "organization_id": self.organization_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "destination": self.destination,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PaymentReceipt:
    receipt_id: str
    payment_id: str
    status: str
    actor_id: str
    organization_id: str
    amount: Decimal
    currency: str
    provider: str
    proof_hash: str
    provider_reference: str | None = None
    settlement_status: str = "pending"

    def canonical(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "payment_id": self.payment_id,
            "status": self.status,
            "actor_id": self.actor_id,
            "organization_id": self.organization_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "provider": self.provider,
            "proof_hash": self.proof_hash,
            "provider_reference": self.provider_reference,
            "settlement_status": self.settlement_status,
        }


@dataclass(frozen=True)
class TrustReceipt:
    trust_id: str
    subject_id: str
    organization_id: str
    event_type: str
    event_hash: str
    replay_status: str
    packet: Mapping[str, Any]

    def canonical(self) -> dict[str, Any]:
        return {
            "trust_id": self.trust_id,
            "subject_id": self.subject_id,
            "organization_id": self.organization_id,
            "event_type": self.event_type,
            "event_hash": self.event_hash,
            "replay_status": self.replay_status,
            "packet": dict(self.packet),
        }


@dataclass(frozen=True)
class ScriptExplanation:
    explanation_id: str
    subject: str
    summary: str
    risk_level: str
    recommended_action: str
    evidence_refs: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "subject": self.subject,
            "summary": self.summary,
            "risk_level": self.risk_level,
            "recommended_action": self.recommended_action,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class ProgrammingProposal:
    proposal_id: str
    title: str
    lifecycle_state: str
    validators: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "lifecycle_state": self.lifecycle_state,
            "validators": list(self.validators),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class CorePlatformFlowResult:
    identity: Identity
    decision: AuthorityDecision
    payment: PaymentReceipt | None
    trust: TrustReceipt
    explanation: ScriptExplanation
    proposal: ProgrammingProposal | None

    def canonical(self) -> dict[str, Any]:
        return {
            "identity": self.identity.canonical(),
            "decision": self.decision.canonical(),
            "payment": self.payment.canonical() if self.payment else None,
            "trust": self.trust.canonical(),
            "explanation": self.explanation.canonical(),
            "proposal": self.proposal.canonical() if self.proposal else None,
        }
