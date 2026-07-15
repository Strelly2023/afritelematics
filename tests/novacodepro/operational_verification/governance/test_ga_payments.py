from afritech.novacodepro.operational_verification.service import OperationalVerificationService
from afritech.novacodepro.operational_verification.payments import evaluate_payment_activation


def test_ga_and_payment_states_are_separate() -> None:
    service = OperationalVerificationService()

    ga = service.evaluate_ga()
    payments = service.evaluate_payments()

    assert ga["ga_allowed"] is False
    assert ga["real_payments_enabled"] is False
    assert payments["state"] == "DISABLED"
    assert payments["real_payments_enabled"] is False


def test_payment_gate_requires_finance_risk_provider_settlement_reconciliation_and_fraud() -> None:
    blocked = evaluate_payment_activation({"finance_approval": "PASS"})

    assert blocked["current_state"] == "DISABLED"
    assert blocked["real_payments_enabled"] is False
