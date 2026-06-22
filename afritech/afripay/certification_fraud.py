"""NovaPay certification and fraud assessment layer.

The layer is deterministic and projection-only: it scores payment risk and
emits certification evidence, but it does not mutate ledger or settlement
state.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from afritech.afripay.compliance import ComplianceDecision
from afritech.afripay.events import canonical_hash
from afritech.afripay.intelligence import FraudDetector, FraudSignal
from afritech.afripay.models import Transaction


BLOCKED = "blocked"
REVIEW = "review"
ALLOWED = "allowed"


@dataclass(frozen=True)
class NovaPayTrustContext:
    organization_id: str
    actor_id: str
    tenant_aligned: bool
    identity_bound: bool
    scope_valid: bool
    resource_owner_valid: bool
    trust_score: int = 80
    proof_coverage: int = 80

    def canonical(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "actor_id": self.actor_id,
            "tenant_aligned": self.tenant_aligned,
            "identity_bound": self.identity_bound,
            "scope_valid": self.scope_valid,
            "resource_owner_valid": self.resource_owner_valid,
            "trust_score": int(self.trust_score),
            "proof_coverage": int(self.proof_coverage),
        }


@dataclass(frozen=True)
class NovaPayFraudAssessment:
    transaction_reference: str
    organization_id: str
    fraud_score: Decimal
    fraud_level: str
    decision: str
    reasons: tuple[str, ...]
    trust_score: int
    proof_coverage: int
    assessment_hash: str

    def canonical(self) -> dict[str, Any]:
        return {
            "transaction_reference": self.transaction_reference,
            "organization_id": self.organization_id,
            "fraud_score": str(self.fraud_score),
            "fraud_level": self.fraud_level,
            "decision": self.decision,
            "reasons": list(self.reasons),
            "trust_score": int(self.trust_score),
            "proof_coverage": int(self.proof_coverage),
            "assessment_hash": self.assessment_hash,
        }


@dataclass(frozen=True)
class NovaPayCertificationEvidence:
    certification_id: str
    organization_id: str
    transaction_reference: str
    tier: str
    status: str
    issuer_role: str
    assessment_hash: str
    certification_hash: str
    controls: Mapping[str, bool]

    def canonical(self) -> dict[str, Any]:
        return {
            "certification_id": self.certification_id,
            "organization_id": self.organization_id,
            "transaction_reference": self.transaction_reference,
            "tier": self.tier,
            "status": self.status,
            "issuer_role": self.issuer_role,
            "assessment_hash": self.assessment_hash,
            "certification_hash": self.certification_hash,
            "controls": dict(self.controls),
            "read_only": True,
            "projection_only": True,
        }


class NovaPayFraudCertificationEngine:
    def __init__(self, fraud_detector: FraudDetector | None = None) -> None:
        self.fraud_detector = fraud_detector or FraudDetector()

    def assess(
        self,
        transaction: Transaction,
        *,
        context: NovaPayTrustContext,
        compliance: ComplianceDecision | None = None,
        recent_transactions: tuple[Transaction, ...] = (),
    ) -> NovaPayFraudAssessment:
        signal = self.fraud_detector.score(transaction, recent_transactions=recent_transactions)
        reasons = list(signal.reasons)
        reasons.extend(_context_reasons(context))
        if compliance is not None and not compliance.allowed:
            reasons.extend(f"compliance:{reason}" for reason in compliance.reasons)

        decision = _decision(signal, context, compliance, reasons)
        fraud_level = _fraud_level(signal.score)
        payload = {
            "transaction_reference": transaction.reference,
            "organization_id": context.organization_id,
            "fraud_score": str(signal.score),
            "fraud_level": fraud_level,
            "decision": decision,
            "reasons": reasons,
            "trust_score": context.trust_score,
            "proof_coverage": context.proof_coverage,
        }
        return NovaPayFraudAssessment(
            transaction_reference=transaction.reference,
            organization_id=context.organization_id,
            fraud_score=signal.score,
            fraud_level=fraud_level,
            decision=decision,
            reasons=tuple(reasons),
            trust_score=context.trust_score,
            proof_coverage=context.proof_coverage,
            assessment_hash=canonical_hash(payload),
        )

    def certify(
        self,
        assessment: NovaPayFraudAssessment,
        *,
        issuer_role: str,
    ) -> NovaPayCertificationEvidence:
        tier = _certification_tier(assessment)
        controls = {
            "identity_bound": "identity_not_bound" not in assessment.reasons,
            "tenant_aligned": "tenant_mismatch" not in assessment.reasons,
            "scope_valid": "scope_invalid" not in assessment.reasons,
            "ownership_valid": "resource_owner_invalid" not in assessment.reasons,
            "fraud_reviewed": assessment.decision in {ALLOWED, REVIEW, BLOCKED},
            "proof_ready": assessment.proof_coverage >= 75,
        }
        status = "issued" if tier in {"NOVAPAY_CERTIFIED", "NOVAPAY_REVIEW_CONTROLLED"} else "blocked"
        payload = {
            "organization_id": assessment.organization_id,
            "transaction_reference": assessment.transaction_reference,
            "tier": tier,
            "status": status,
            "issuer_role": issuer_role,
            "assessment_hash": assessment.assessment_hash,
            "controls": controls,
        }
        certification_hash = canonical_hash(payload)
        return NovaPayCertificationEvidence(
            certification_id=f"novapay-cert-{certification_hash[:12]}",
            organization_id=assessment.organization_id,
            transaction_reference=assessment.transaction_reference,
            tier=tier,
            status=status,
            issuer_role=issuer_role,
            assessment_hash=assessment.assessment_hash,
            certification_hash=certification_hash,
            controls=controls,
        )


def _context_reasons(context: NovaPayTrustContext) -> list[str]:
    reasons: list[str] = []
    if not context.tenant_aligned:
        reasons.append("tenant_mismatch")
    if not context.identity_bound:
        reasons.append("identity_not_bound")
    if not context.scope_valid:
        reasons.append("scope_invalid")
    if not context.resource_owner_valid:
        reasons.append("resource_owner_invalid")
    if context.trust_score < 70:
        reasons.append("trust_score_below_execution_threshold")
    if context.proof_coverage < 75:
        reasons.append("proof_coverage_below_certification_threshold")
    return reasons


def _decision(
    signal: FraudSignal,
    context: NovaPayTrustContext,
    compliance: ComplianceDecision | None,
    reasons: list[str],
) -> str:
    fail_closed_reasons = {
        "tenant_mismatch",
        "identity_not_bound",
        "scope_invalid",
        "resource_owner_invalid",
    }
    if any(reason in fail_closed_reasons for reason in reasons):
        return BLOCKED
    if signal.score >= Decimal("0.85"):
        return BLOCKED
    if compliance is not None and not compliance.allowed and "high_party_risk" in compliance.reasons:
        return BLOCKED
    if signal.score >= Decimal("0.60") or context.trust_score < 70 or context.proof_coverage < 75:
        return REVIEW
    if compliance is not None and not compliance.allowed:
        return REVIEW
    return ALLOWED


def _fraud_level(score: Decimal) -> str:
    if score >= Decimal("0.85"):
        return "CRITICAL"
    if score >= Decimal("0.60"):
        return "HIGH"
    if score >= Decimal("0.30"):
        return "MEDIUM"
    return "LOW"


def _certification_tier(assessment: NovaPayFraudAssessment) -> str:
    if assessment.decision == BLOCKED:
        return "NOVAPAY_BLOCKED"
    if (
        assessment.decision == ALLOWED
        and assessment.trust_score >= 85
        and assessment.proof_coverage >= 90
        and assessment.fraud_score < Decimal("0.30")
    ):
        return "NOVAPAY_CERTIFIED"
    if assessment.trust_score >= 70 and assessment.proof_coverage >= 75:
        return "NOVAPAY_REVIEW_CONTROLLED"
    return "NOVAPAY_PROVISIONAL"


__all__ = [
    "ALLOWED",
    "BLOCKED",
    "REVIEW",
    "NovaPayCertificationEvidence",
    "NovaPayFraudAssessment",
    "NovaPayFraudCertificationEngine",
    "NovaPayTrustContext",
]
