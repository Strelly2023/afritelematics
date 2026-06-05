from __future__ import annotations

from dataclasses import dataclass


TRUST_KERNEL_V4_STATUS = "DESIGNED_BLOCKED"
TRUST_KERNEL_V4_REASON = "AfriPay has no admissible real transaction evidence."


@dataclass(frozen=True)
class EconomicEvidenceSignals:
    real_paid_transactions_exist: bool = False
    payments_exchanged_between_parties: bool = False
    financial_records_captured: bool = False
    receipts_recorded: bool = False


@dataclass(frozen=True)
class EconomicActivationDecision:
    status: str
    authorized: bool
    reason: str
    missing_evidence: tuple[str, ...]
    allowed_next_action: str


class EconomicActivationBlocked(RuntimeError):
    """Raised when Trust Kernel v4 economic anchoring is requested too early."""


def evaluate_economic_activation(
    signals: EconomicEvidenceSignals | None = None,
) -> EconomicActivationDecision:
    signals = signals or EconomicEvidenceSignals()
    missing = _missing_evidence(signals)
    authorized = not missing
    return EconomicActivationDecision(
        status="ACTIVATION_ELIGIBLE" if authorized else TRUST_KERNEL_V4_STATUS,
        authorized=authorized,
        reason=(
            "Real transaction evidence gate satisfied."
            if authorized
            else TRUST_KERNEL_V4_REASON
        ),
        missing_evidence=missing,
        allowed_next_action=(
            "design wallet and settlement layer"
            if authorized
            else "collect real transaction records only"
        ),
    )


def guard_economic_activation(
    signals: EconomicEvidenceSignals | None = None,
) -> EconomicActivationDecision:
    decision = evaluate_economic_activation(signals)
    if not decision.authorized:
        raise EconomicActivationBlocked(
            "Trust Kernel v4 economic anchoring is blocked until real transaction "
            f"evidence exists: {', '.join(decision.missing_evidence)}"
        )
    return decision


def _missing_evidence(signals: EconomicEvidenceSignals) -> tuple[str, ...]:
    missing: list[str] = []
    if not signals.real_paid_transactions_exist:
        missing.append("real paid transactions")
    if not signals.payments_exchanged_between_parties:
        missing.append("payments exchanged between parties")
    if not signals.financial_records_captured:
        missing.append("captured financial records")
    if not signals.receipts_recorded:
        missing.append("recorded receipts")
    return tuple(missing)
