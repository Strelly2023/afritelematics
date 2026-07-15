from __future__ import annotations

from .enums import GADecision, PaymentState


def invariant_status() -> dict[str, object]:
    return {
        "GA_ALLOWED": False,
        "GA_APPROVAL": "PENDING",
        "REAL_PAYMENTS_ENABLED": False,
        "REAL_PAYMENT_APPROVAL": "PENDING",
        "NOVA_AI_AUTHORITY": "ADVISORY_ONLY",
        "PRR_APPROVAL_REQUIRES_HUMAN": True,
        "EXECUTIVE_APPROVAL_REQUIRES_HUMAN": True,
        "PAYMENT_ACTIVATION_REQUIRES_SEPARATE_FINANCIAL_GOVERNANCE": True,
        "ga_decision": GADecision.GA_BLOCKED.value,
        "payment_state": PaymentState.DISABLED.value,
    }
