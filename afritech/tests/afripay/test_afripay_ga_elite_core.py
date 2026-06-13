from __future__ import annotations

from decimal import Decimal

import pytest

from afritech.afripay.api import AfriPayService
from afritech.afripay.billing import BillingService
from afritech.afripay.compliance import ComplianceEngine
from afritech.afripay.escrow import EscrowService
from afritech.afripay.exceptions import DuplicateReference, GuardViolation, InsufficientFunds
from afritech.afripay.fx import default_fx_engine
from afritech.afripay.guards import guard_journal_balances
from afritech.afripay.intelligence import FraudDetector, LiquidityEngine
from afritech.afripay.ledger import DoubleEntryLedger, credit, debit
from afritech.afripay.models import EntryLine, Party, PayoutItem, Transaction, WalletType, new_id
from afritech.afripay.money import Money
from afritech.afripay.orchestration import PaymentOrchestrator
from afritech.afripay.payouts import BulkPayoutService, payout_item
from afritech.afripay.treasury import TreasuryEngine
from afritech.afripay.wallet import WalletService


def test_payment_orchestrator_splits_routes_and_posts_balanced_ledger() -> None:
    orchestrator = PaymentOrchestrator()

    result = orchestrator.process_payment(
        payer_id="diaspora.user.001",
        payee_id="burundi.merchant.001",
        amount=Money.of("100.00", "AUD"),
        reference="pay.ref.001",
        preference="balanced",
        metadata={"channel": "api"},
    )

    assert result.transaction.status.value == "success"
    assert len(result.routes) >= 2
    assert sum(route.amount.amount for route in result.routes) == Decimal("100.00")
    assert result.journal_reference == "journal.pay.ref.001"
    assert orchestrator.ledger.verify_balanced() is True
    assert any(route.rail == "mobile_money" for route in result.routes)
    assert any(route.rail == "bank" for route in result.routes)
    assert orchestrator.treasury.available("mtn_mobile_money", "AUD") == Money.of("0.00", "AUD")
    assert orchestrator.metrics.snapshot()["counters"]["afripay.payment.completed"] == 1


def test_payment_orchestrator_rejects_duplicate_reference() -> None:
    orchestrator = PaymentOrchestrator()
    payload = {
        "payer_id": "payer",
        "payee_id": "payee",
        "amount": Money.of("12.00", "AUD"),
        "reference": "dup.ref.001",
    }

    orchestrator.process_payment(**payload)

    with pytest.raises(DuplicateReference):
        orchestrator.process_payment(**payload)


def test_payment_orchestrator_rejects_provider_authority_fields() -> None:
    orchestrator = PaymentOrchestrator()

    with pytest.raises(GuardViolation):
        orchestrator.process_payment(
            payer_id="payer",
            payee_id="payee",
            amount=Money.of("12.00", "AUD"),
            reference="bad.authority.001",
            metadata={"provider_truth": "paid"},
        )


def test_treasury_liquidity_controls_route_capacity() -> None:
    treasury = TreasuryEngine()
    treasury.add_pool(
        pool_id="pool.mtn.test",
        provider="mtn_mobile_money",
        balance=Money.of("25.00", "AUD"),
    )
    treasury.add_pool(
        pool_id="pool.bank.test",
        provider="bank_partner",
        balance=Money.of("500.00", "AUD"),
    )
    treasury.add_pool(
        pool_id="pool.stablecoin.test",
        provider="stablecoin_settlement",
        balance=Money.of("0.00", "AUD"),
    )
    orchestrator = PaymentOrchestrator(treasury=treasury)

    result = orchestrator.process_payment(
        payer_id="payer",
        payee_id="payee",
        amount=Money.of("100.00", "AUD"),
        reference="treasury.route.001",
    )

    mobile_route = next(route for route in result.routes if route.provider == "mtn_mobile_money")
    bank_route = next(route for route in result.routes if route.provider == "bank_partner")
    assert mobile_route.amount == Money.of("25.00", "AUD")
    assert bank_route.amount == Money.of("75.00", "AUD")
    assert treasury.available("mtn_mobile_money", "AUD") == Money.of("0.00", "AUD")
    assert treasury.event_store.replay("reserve." + mobile_route.route_id)


def test_wallet_multi_currency_locks_and_geo_balance() -> None:
    service = WalletService()
    wallet = service.create_wallet("user.001", "Australia", WalletType.PERSONAL)

    service.credit(wallet, Money.of("150.00", "AUD"))
    service.lock(wallet, Money.of("40.00", "AUD"))

    assert wallet.account("AUD").available == Money.of("110.00", "AUD")
    assert service.geo_balance(wallet, "Australia") == Money.of("110.00", "AUD")

    with pytest.raises(InsufficientFunds):
        service.debit(wallet, Money.of("120.00", "AUD"))


def test_double_entry_ledger_rejects_imbalanced_journal() -> None:
    ledger = DoubleEntryLedger()
    cash = ledger.create_account("cash", "asset", "AUD")
    revenue = ledger.create_account("revenue", "revenue", "AUD")

    with pytest.raises(GuardViolation):
        guard_journal_balances(
            (
                debit(cash, Money.of("10.00", "AUD")),
                credit(revenue, Money.of("9.99", "AUD")),
            )
        )

    ledger.post(
        reference="balanced.001",
        transaction_id="tx.001",
        lines=(debit(cash, Money.of("10.00", "AUD")), credit(revenue, Money.of("10.00", "AUD"))),
    )
    assert ledger.verify_balanced() is True


def test_fx_engine_locks_rate_and_converts() -> None:
    conversion = default_fx_engine().convert(
        transaction_id="tx.fx.001",
        amount=Money.of("10.00", "AUD"),
        to_currency="BIF",
    )

    assert conversion.amount_out == Money.of("19000.00", "BIF")
    assert conversion.rate.locked_reference.startswith("fxlock.")


def test_escrow_release_requires_matching_evidence() -> None:
    service = EscrowService()
    escrow = service.lock(
        transaction_id="tx.escrow.001",
        payer_id="buyer",
        payee_id="seller",
        total=Money.of("25.00", "USD"),
        release_condition="ride.completed.receipt.001",
    )

    with pytest.raises(GuardViolation):
        service.release(escrow.escrow_id, "wrong.evidence")

    released = service.release(escrow.escrow_id, "ride.completed.receipt.001")
    assert released.status == "released"


def test_bulk_payout_requires_unique_references_and_sums_total() -> None:
    service = BulkPayoutService()
    items = (
        payout_item("farmer.001", Money.of("10.00", "USD"), "payout.item.001"),
        payout_item("farmer.002", Money.of("15.50", "USD"), "payout.item.002"),
    )

    batch = service.create_batch(initiated_by="coop.001", items=items)

    assert batch.total == Money.of("25.50", "USD")
    assert service.mark_processed(batch).status == "processed"

    with pytest.raises(DuplicateReference):
        service.create_batch(initiated_by="coop.001", items=items)


def test_billing_creates_active_subscription_and_invoice() -> None:
    billing = BillingService()
    subscription = billing.create_subscription(
        customer_id="merchant.001",
        plan_name="business-suite",
        recurring_amount=Money.of("29.00", "USD"),
    )

    invoice = billing.generate_invoice(subscription)

    assert subscription.status == "active"
    assert invoice.amount == Money.of("29.00", "USD")
    assert invoice.status == "open"


def test_compliance_blocks_large_cross_border_low_kyc() -> None:
    tx = Transaction(
        transaction_id=new_id("tx"),
        reference="compliance.001",
        payer_id="payer",
        payee_id="payee",
        amount=Money.of("1500.00", "USD"),
        transaction_type="payment",
    )
    payer = Party("payer", "AU", kyc_level=1)
    payee = Party("payee", "BI", kyc_level=1)

    decision = ComplianceEngine().assess(tx, payer, payee)

    assert decision.allowed is False
    assert "payer_kyc_below_required" in decision.reasons
    assert "cross_border_large_value_review" in decision.reasons


def test_intelligence_hooks_score_fraud_and_forecast_liquidity() -> None:
    tx = Transaction(
        transaction_id=new_id("tx"),
        reference="risk.001",
        payer_id="payer",
        payee_id="payee",
        amount=Money.of("6000.00", "USD"),
        transaction_type="payment",
        metadata={"channel": "offline"},
    )

    signal = FraudDetector().score(tx)
    forecast = LiquidityEngine().forecast(
        wallet_id="wallet.001",
        current_balance=Money.of("50.00", "USD"),
        average_daily_outflow=Money.of("20.00", "USD"),
    )

    assert signal.score == Decimal("0.60")
    assert signal.reasons == ("large_amount", "large_offline_payment")
    assert forecast.days_until_shortfall == 2
    assert forecast.recommended_topup == Money.of("30.00", "USD")


def test_service_facade_returns_api_contract() -> None:
    service = AfriPayService()

    response = service.create_payment(
        {
            "payer_id": "payer",
            "payee_id": "payee",
            "amount": "80.00",
            "currency": "AUD",
            "reference": "api.payment.001",
        }
    )

    assert response["status"] == "success"
    assert response["journal_reference"] == "journal.api.payment.001"
    assert response["routes"]
    assert service.quote_fx("1.00", "AUD", "USD")["amount_out"] == {
        "amount": "0.66",
        "currency": "USD",
    }
