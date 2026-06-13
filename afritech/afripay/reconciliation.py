"""Audit-grade reconciliation and financial proofing for AfriPay."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from importlib import import_module
from typing import Any, Iterable


AUTHORITY_DISCLAIMER = "reconciliation is evidence-only and does not alter ledger truth"


@dataclass(frozen=True)
class ReconciliationMismatch:
    code: str
    detail: str


@dataclass(frozen=True)
class ReconciliationSnapshot:
    reference: str
    transaction_id: str
    transaction_amount: Decimal
    transaction_currency: str
    journal_reference: str | None
    route_count: int
    provider_transaction_count: int
    event_count: int
    treasury_pool_count: int
    balanced: bool
    ledger_hash: str
    provider_hash: str
    event_hash: str
    treasury_hash: str
    mismatches: tuple[ReconciliationMismatch, ...]
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    @property
    def verified(self) -> bool:
        return (
            self.balanced
            and self.route_count > 0
            and self.provider_transaction_count == self.route_count
            and self.event_count > 0
            and self.treasury_pool_count > 0
            and not self.mismatches
            and len(self.ledger_hash) == 64
            and len(self.provider_hash) == 64
            and len(self.event_hash) == 64
            and len(self.treasury_hash) == 64
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "balanced": self.balanced,
            "event_count": self.event_count,
            "event_hash": self.event_hash,
            "journal_reference": self.journal_reference,
            "ledger_hash": self.ledger_hash,
            "mismatches": [mismatch.__dict__ for mismatch in self.mismatches],
            "provider_hash": self.provider_hash,
            "provider_transaction_count": self.provider_transaction_count,
            "reference": self.reference,
            "route_count": self.route_count,
            "schema": "afritech.afripay.reconciliation_snapshot.v1",
            "transaction_currency": self.transaction_currency,
            "transaction_amount": str(self.transaction_amount),
            "transaction_id": self.transaction_id,
            "treasury_hash": self.treasury_hash,
            "treasury_pool_count": self.treasury_pool_count,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


class LedgerReconciliationEngine:
    def reconcile_transaction(self, reference: str) -> ReconciliationSnapshot:
        models = _afripay_models()
        transaction = models.Transaction.objects.get(reference=reference)
        journal_entries = tuple(models.JournalEntry.objects.filter(transaction=transaction).order_by("journal_id"))
        routes = tuple(models.PaymentRoute.objects.filter(transaction=transaction).order_by("route_id"))
        provider_transactions = tuple(
            models.ProviderTransaction.objects.filter(transaction=transaction).order_by("external_reference")
        )
        events = tuple(models.EventRecord.objects.filter(aggregate_id=reference).order_by("event_id"))
        pools = tuple(
            models.LiquidityPool.objects.filter(provider__in={route.provider for route in routes}).order_by("provider")
        )

        mismatches: list[ReconciliationMismatch] = []
        balanced = _balanced(journal_entries)
        if not journal_entries:
            mismatches.append(ReconciliationMismatch("missing_journal", "no journal entry linked to transaction"))
        elif not balanced:
            mismatches.append(ReconciliationMismatch("imbalanced_journal", "journal lines do not balance by currency"))

        if len(provider_transactions) != len(routes):
            mismatches.append(
                ReconciliationMismatch(
                    "provider_route_mismatch",
                    "provider transaction count does not match persisted routes",
                )
            )
        if sum(Decimal(str(route.amount)) for route in routes) != transaction.amount:
            mismatches.append(
                ReconciliationMismatch(
                    "route_amount_mismatch",
                    "persisted routes do not sum to transaction amount",
                )
            )
        if not events:
            mismatches.append(ReconciliationMismatch("missing_events", "no audit event chain exists for transaction"))
        elif not _event_chain_consistent(events):
            mismatches.append(
                ReconciliationMismatch(
                    "event_chain_invalid",
                    "event hash chain does not replay cleanly",
                )
            )
        if not pools:
            mismatches.append(ReconciliationMismatch("missing_treasury", "no treasury pools exist for routed providers"))
        elif not _pools_consistent(pools):
            mismatches.append(ReconciliationMismatch("treasury_inconsistent", "treasury pool balances are invalid"))

        if _route_mismatch(routes, provider_transactions):
            mismatches.append(
                ReconciliationMismatch(
                    "provider_reference_mismatch",
                    "route and provider references do not align",
                )
            )

        ledger_hash = _canonical_hash(
            {
                "journal_entries": [_journal_entry_payload(entry) for entry in journal_entries],
                "lines": [_entry_line_payload(line) for entry in journal_entries for line in entry.lines.all()],
            }
        )
        provider_hash = _canonical_hash(
            {
                "routes": [_route_payload(route) for route in routes],
                "provider_transactions": [_provider_transaction_payload(tx) for tx in provider_transactions],
            }
        )
        event_hash = _canonical_hash([_event_payload(event) for event in events])
        treasury_hash = _canonical_hash([_treasury_payload(pool) for pool in pools])

        return ReconciliationSnapshot(
            reference=transaction.reference,
            transaction_id=transaction.transaction_id,
            transaction_amount=Decimal(str(transaction.amount)),
            transaction_currency=transaction.currency,
            journal_reference=journal_entries[0].reference if journal_entries else None,
            route_count=len(routes),
            provider_transaction_count=len(provider_transactions),
            event_count=len(events),
            treasury_pool_count=len(pools),
            balanced=balanced,
            ledger_hash=ledger_hash,
            provider_hash=provider_hash,
            event_hash=event_hash,
            treasury_hash=treasury_hash,
            mismatches=tuple(mismatches),
        )


def validate_financial_integrity(reference: str) -> ReconciliationSnapshot:
    report = LedgerReconciliationEngine().reconcile_transaction(reference)
    if not report.verified:
        raise FinancialIntegrityError(report.mismatches)
    return report


class FinancialIntegrityError(RuntimeError):
    def __init__(self, mismatches: Iterable[ReconciliationMismatch]) -> None:
        mismatches = tuple(mismatches)
        message = ", ".join(f"{m.code}:{m.detail}" for m in mismatches) or "financial integrity proof failed"
        super().__init__(message)
        self.mismatches = mismatches


def _balanced(journal_entries) -> bool:
    totals: dict[str, Decimal] = {}
    for entry in journal_entries:
        for line in entry.lines.all():
            totals.setdefault(line.currency, Decimal("0.00"))
            totals[line.currency] += Decimal(str(line.debit)) - Decimal(str(line.credit))
    return all(total == Decimal("0.00") for total in totals.values())


def _pools_consistent(pools) -> bool:
    return all(pool.balance >= 0 and pool.reserved >= 0 and pool.balance >= pool.reserved for pool in pools)


def _route_mismatch(routes, provider_transactions) -> bool:
    if len(routes) != len(provider_transactions):
        return True
    provider_map = {tx.external_reference: tx for tx in provider_transactions}
    for route in routes:
        if route.external_reference not in provider_map:
            return True
        if provider_map[route.external_reference].provider != route.provider:
            return True
    return False


def _journal_entry_payload(entry) -> dict[str, Any]:
    return {
        "journal_id": entry.journal_id,
        "reference": entry.reference,
        "transaction_id": entry.transaction_id,
        "created_at": entry.created_at.isoformat(),
    }


def _entry_line_payload(line) -> dict[str, Any]:
    return {
        "account_id": line.account.account_id,
        "credit": str(line.credit),
        "currency": line.currency,
        "debit": str(line.debit),
        "journal_id": line.journal.journal_id,
    }


def _route_payload(route) -> dict[str, Any]:
    return {
        "amount": str(route.amount),
        "external_reference": route.external_reference,
        "provider": route.provider,
        "rail": route.rail,
        "route_id": route.route_id,
        "status": route.status,
    }


def _provider_transaction_payload(tx) -> dict[str, Any]:
    return {
        "external_reference": tx.external_reference,
        "internal_reference": tx.internal_reference,
        "provider": tx.provider,
        "status": tx.status,
    }


def _event_payload(event) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "hash_chain": event.hash_chain,
        "aggregate_id": event.aggregate_id,
    }


def _event_chain_consistent(events) -> bool:
    previous_hash = "GENESIS"
    for event in events:
        recomputed = _canonical_hash(
            {
                "aggregate_id": event.aggregate_id,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "payload": event.payload,
                "previous_hash": previous_hash,
            }
        )
        if recomputed != event.hash_chain:
            return False
        previous_hash = event.hash_chain
    return True


def _treasury_payload(pool) -> dict[str, Any]:
    return {
        "balance": str(pool.balance),
        "currency": pool.currency,
        "pool_id": pool.pool_id,
        "provider": pool.provider,
        "reserved": str(pool.reserved),
    }


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _afripay_models():
    return import_module("afriride_system.django_app.apps.afripay.models")
