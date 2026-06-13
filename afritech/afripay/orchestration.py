"""AfriPay payment orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from afritech.afripay.config import EnvironmentConfig
from afritech.afripay.events import EventOutbox
from afritech.afripay.exceptions import DuplicateReference, ProviderFailure
from afritech.afripay.guards import guard_transaction
from afritech.afripay.ledger import DoubleEntryLedger, credit, debit
from afritech.afripay.models import RouteStatus, Transaction, TransactionStatus, new_id
from afritech.afripay.money import Money
from afritech.afripay.providers import PaymentProvider, default_provider_set
from afritech.afripay.routing import AdaptiveRoutingEngine
from afritech.afripay.treasury import TreasuryEngine, default_treasury_engine
from afritech.afripay.observability import MetricsRegistry, Tracer


@dataclass(frozen=True)
class PaymentResult:
    transaction: Transaction
    routes: tuple[object, ...]
    journal_reference: str
    event_count: int


class PaymentOrchestrator:
    def __init__(
        self,
        *,
        ledger: DoubleEntryLedger | None = None,
        providers: tuple[PaymentProvider, ...] | None = None,
        outbox: EventOutbox | None = None,
        treasury: TreasuryEngine | None = None,
        config: EnvironmentConfig | None = None,
        metrics: MetricsRegistry | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.ledger = ledger or DoubleEntryLedger()
        self.providers = providers or default_provider_set()
        self.treasury = treasury or default_treasury_engine()
        self.router = AdaptiveRoutingEngine(self.providers, self.treasury)
        self.outbox = outbox or EventOutbox()
        self.config = config or EnvironmentConfig.from_env()
        self.metrics = metrics or MetricsRegistry()
        self.tracer = tracer or Tracer()
        self._transactions_by_reference: dict[str, Transaction] = {}
        self._route_index = {provider.name: provider for provider in self.providers}

    def process_payment(
        self,
        *,
        payer_id: str,
        payee_id: str,
        amount: Money,
        reference: str,
        preference: str = "balanced",
        metadata: dict[str, object] | None = None,
    ) -> PaymentResult:
        started_at = perf_counter()
        self.config.require_live_activation()
        if reference in self._transactions_by_reference:
            raise DuplicateReference(f"duplicate payment reference: {reference}")
        transaction = Transaction(
            transaction_id=new_id("tx"),
            reference=reference,
            payer_id=payer_id,
            payee_id=payee_id,
            amount=amount,
            transaction_type="payment",
            metadata=metadata or {},
        )
        guard_transaction(transaction)
        routes = list(
            self.router.plan_routes(
                transaction_id=transaction.transaction_id,
                amount=amount,
                preference=preference,
            )
        )
        transaction.status = TransactionStatus.ROUTED
        self.outbox.emit(
            "afripay.payment.routed",
            {
                "reference": reference,
                "route_count": len(routes),
                "transaction_id": transaction.transaction_id,
            },
        )
        for route in routes:
            provider = self._route_index[route.provider]
            reservation_id = f"reserve.{route.route_id}"
            self.treasury.reserve(route.provider, route.amount, reservation_id)
            try:
                result = provider.send(route)
            except ProviderFailure:
                self.treasury.release(reservation_id)
                route.status = RouteStatus.FAILED
                transaction.status = TransactionStatus.FAILED
                self.outbox.emit("afripay.payment.failed", {"reference": reference, "provider": route.provider})
                self.metrics.increment("afripay.payment.failed")
                raise
            route.status = RouteStatus.CONFIRMED
            route.external_reference = result.external_reference
            route.latency_ms = result.latency_ms
            self.treasury.settle(reservation_id)
            self.metrics.observe("afripay.route.latency_ms", result.latency_ms)
        transaction.status = TransactionStatus.SUCCESS
        journal_reference = self._post_settlement_journal(transaction)
        self._transactions_by_reference[reference] = transaction
        self.outbox.emit(
            "afripay.payment.completed",
            {
                "amount": amount.canonical(),
                "journal_reference": journal_reference,
                "reference": reference,
                "transaction_id": transaction.transaction_id,
            },
        )
        self.metrics.increment("afripay.payment.completed")
        self.tracer.record(
            "afripay.process_payment",
            started_at,
            reference=reference,
            route_count=len(routes),
            status=transaction.status.value,
        )
        return PaymentResult(transaction, tuple(routes), journal_reference, len(self.outbox.all()))

    def _post_settlement_journal(self, transaction: Transaction) -> str:
        cash = self.ledger.create_account("AfriPay settlement cash", "asset", transaction.amount.currency)
        payable = self.ledger.create_account("Merchant payable", "liability", transaction.amount.currency)
        reference = f"journal.{transaction.reference}"
        self.ledger.post(
            reference=reference,
            transaction_id=transaction.transaction_id,
            lines=(debit(cash, transaction.amount), credit(payable, transaction.amount)),
        )
        return reference
