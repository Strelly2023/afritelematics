from __future__ import annotations

import pytest

from afritech.ci.trust_kernel_v4_economic_gate_validator import validate
from afritech.trust_kernel.economic_gate import (
    EconomicActivationBlocked,
    EconomicEvidenceSignals,
    evaluate_economic_activation,
    guard_economic_activation,
)


def test_trust_kernel_v4_economic_gate_blocks_by_default():
    decision = evaluate_economic_activation()

    assert decision.authorized is False
    assert decision.status == "DESIGNED_BLOCKED"
    assert decision.allowed_next_action == "collect real transaction records only"
    assert "real paid transactions" in decision.missing_evidence


def test_trust_kernel_v4_guard_rejects_partial_transaction_evidence():
    with pytest.raises(EconomicActivationBlocked, match="captured financial records"):
        guard_economic_activation(
            EconomicEvidenceSignals(
                real_paid_transactions_exist=True,
                payments_exchanged_between_parties=True,
                financial_records_captured=False,
                receipts_recorded=True,
            )
        )


def test_trust_kernel_v4_can_become_eligible_only_after_full_evidence_gate():
    decision = guard_economic_activation(
        EconomicEvidenceSignals(
            real_paid_transactions_exist=True,
            payments_exchanged_between_parties=True,
            financial_records_captured=True,
            receipts_recorded=True,
        )
    )

    assert decision.authorized is True
    assert decision.status == "ACTIVATION_ELIGIBLE"
    assert decision.allowed_next_action == "design wallet and settlement layer"


def test_trust_kernel_v4_economic_gate_validator_passes():
    assert validate() is True
