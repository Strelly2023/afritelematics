from afritech.guards.guard_novacodepro_ga_activation import verify_ga_separate_from_payments
from afritech.guards.guard_novacodepro_operational_verification import verify_no_production_claim_from_ci
from afritech.guards.guard_novacodepro_payment_activation import verify_payment_activation_requires_financial_governance


def test_ci_only_evidence_cannot_claim_production_verification() -> None:
    assert verify_no_production_claim_from_ci({"environment": "ci", "verified": True}) is False


def test_ga_does_not_enable_payment_activation() -> None:
    assert verify_ga_separate_from_payments({"ga_allowed": True, "real_payments_enabled": True}) is False


def test_payment_activation_requires_financial_governance() -> None:
    assert verify_payment_activation_requires_financial_governance({"finance_approval": "PASS"}) is False
