from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from afritech.afripay.certification_fraud import (
    ALLOWED,
    BLOCKED,
    NovaPayFraudCertificationEngine,
    NovaPayTrustContext,
)
from afritech.afripay.compliance import ComplianceDecision
from afritech.afripay.models import Transaction, new_id
from afritech.afripay.money import Money


def _transaction(
    *,
    reference: str = "novapay.cert.001",
    amount: str = "80.00",
    channel: str = "mobile",
    payee_id: str = "merchant.001",
) -> Transaction:
    return Transaction(
        transaction_id=new_id("tx"),
        reference=reference,
        payer_id="customer.001",
        payee_id=payee_id,
        amount=Money.of(amount, "AUD"),
        transaction_type="payment",
        metadata={"channel": channel},
    )


def _context(**overrides) -> NovaPayTrustContext:
    base = {
        "organization_id": "org-novapay",
        "actor_id": "customer.001",
        "tenant_aligned": True,
        "identity_bound": True,
        "scope_valid": True,
        "resource_owner_valid": True,
        "trust_score": 92,
        "proof_coverage": 95,
    }
    base.update(overrides)
    return NovaPayTrustContext(**base)


def test_certification_issues_clean_tier_for_low_risk_payment() -> None:
    engine = NovaPayFraudCertificationEngine()

    assessment = engine.assess(_transaction(), context=_context())
    certification = engine.certify(assessment, issuer_role="VERIFIER")

    assert assessment.decision == ALLOWED
    assert assessment.fraud_level == "LOW"
    assert assessment.assessment_hash
    assert certification.tier == "NOVAPAY_CERTIFIED"
    assert certification.status == "issued"
    assert certification.controls["identity_bound"] is True
    assert certification.controls["tenant_aligned"] is True
    assert certification.certification_hash == engine.certify(assessment, issuer_role="VERIFIER").certification_hash


def test_assessment_fails_closed_on_authority_boundary_failure() -> None:
    engine = NovaPayFraudCertificationEngine()

    assessment = engine.assess(
        _transaction(),
        context=_context(tenant_aligned=False, resource_owner_valid=False),
    )
    certification = engine.certify(assessment, issuer_role="VERIFIER")

    assert assessment.decision == BLOCKED
    assert "tenant_mismatch" in assessment.reasons
    assert "resource_owner_invalid" in assessment.reasons
    assert certification.tier == "NOVAPAY_BLOCKED"
    assert certification.status == "blocked"
    assert certification.controls["tenant_aligned"] is False
    assert certification.controls["ownership_valid"] is False


def test_critical_fraud_velocity_blocks_certification() -> None:
    engine = NovaPayFraudCertificationEngine()
    transaction = _transaction(amount="6000.00", channel="offline", payee_id="merchant.velocity")
    recent = tuple(
        _transaction(reference=f"novapay.velocity.{index}", amount="20.00", payee_id="merchant.velocity")
        for index in range(5)
    )

    assessment = engine.assess(transaction, context=_context(), recent_transactions=recent)
    certification = engine.certify(assessment, issuer_role="VERIFIER")

    assert assessment.decision == BLOCKED
    assert assessment.fraud_score == Decimal("0.85")
    assert assessment.fraud_level == "CRITICAL"
    assert "large_amount" in assessment.reasons
    assert "large_offline_payment" in assessment.reasons
    assert "repeated_payee_velocity" in assessment.reasons
    assert certification.tier == "NOVAPAY_BLOCKED"


def test_compliance_high_party_risk_blocks_certification() -> None:
    engine = NovaPayFraudCertificationEngine()
    compliance = ComplianceDecision(
        allowed=False,
        reasons=("high_party_risk",),
        required_kyc_level=3,
    )

    assessment = engine.assess(_transaction(), context=_context(), compliance=compliance)
    certification = engine.certify(assessment, issuer_role="VERIFIER")

    assert assessment.decision == BLOCKED
    assert "compliance:high_party_risk" in assessment.reasons
    assert certification.tier == "NOVAPAY_BLOCKED"


def test_design_document_binds_required_controls() -> None:
    text = Path("docs/technical/NOVAPAY_CERTIFICATION_FRAUD_DETECTION_LAYER.md").read_text(encoding="utf-8")

    required_terms = [
        "tenant_aligned",
        "identity_bound",
        "scope_valid",
        "resource_owner_valid",
        "NOVAPAY_CERTIFIED",
        "NOVAPAY_REVIEW_CONTROLLED",
        "NOVAPAY_PROVISIONAL",
        "NOVAPAY_BLOCKED",
        "NovaPower",
        "NovaTrust",
        "assessment_hash",
        "certification_hash",
        "No NovaPay certification may define financial truth.",
    ]
    for term in required_terms:
        assert term in text
