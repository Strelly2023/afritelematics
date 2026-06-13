"""KYC, AML, and audit-grade compliance checks."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from afritech.afripay.exceptions import GuardViolation
from afritech.afripay.models import Party, Transaction


@dataclass(frozen=True)
class KYCProfile:
    party_id: str
    level: int
    document_type: str | None = None
    verified: bool = False
    risk_score: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class ComplianceDecision:
    allowed: bool
    reasons: tuple[str, ...]
    required_kyc_level: int


class ComplianceEngine:
    def assess(self, transaction: Transaction, payer: Party, payee: Party) -> ComplianceDecision:
        reasons: list[str] = []
        required_kyc = self.required_kyc_level(transaction)
        jurisdiction = jurisdiction_rules(payer.country, payee.country)
        if payer.kyc_level < required_kyc:
            reasons.append("payer_kyc_below_required")
        if payee.kyc_level < min(required_kyc, 2):
            reasons.append("payee_kyc_below_required")
        if payer.risk_score >= Decimal("0.80") or payee.risk_score >= Decimal("0.80"):
            reasons.append("high_party_risk")
        if payer.country != payee.country and transaction.amount.amount >= jurisdiction["max_without_review"]:
            reasons.append("cross_border_large_value_review")
        return ComplianceDecision(not reasons, tuple(reasons), required_kyc)

    def require_allowed(self, transaction: Transaction, payer: Party, payee: Party) -> None:
        decision = self.assess(transaction, payer, payee)
        if not decision.allowed:
            raise GuardViolation(f"compliance blocked: {decision.reasons[0]}")

    def required_kyc_level(self, transaction: Transaction) -> int:
        if transaction.amount.amount < Decimal("100.00"):
            return 1
        if transaction.amount.amount < Decimal("1000.00"):
            return 2
        return 3


def jurisdiction_rules(source_country: str, destination_country: str) -> dict[str, Decimal]:
    pair = (source_country.upper(), destination_country.upper())
    if pair in {("AU", "BI"), ("AUS", "BDI"), ("AUSTRALIA", "BURUNDI")}:
        return {"max_without_review": Decimal("500.00")}
    if source_country.upper() != destination_country.upper():
        return {"max_without_review": Decimal("1000.00")}
    return {"max_without_review": Decimal("5000.00")}

