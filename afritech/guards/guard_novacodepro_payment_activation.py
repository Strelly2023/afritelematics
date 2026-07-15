from __future__ import annotations


REQUIRED = {"finance_approval", "risk_approval", "provider_certification", "settlement_validation", "reconciliation_validation", "fraud_validation"}


def verify_payment_activation_requires_financial_governance(evidence: dict[str, str]) -> bool:
    return all(evidence.get(item) == "PASS" for item in REQUIRED)
