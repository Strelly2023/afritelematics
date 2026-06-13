"""AfriPay governance guards."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Mapping

from afritech.afripay.exceptions import GuardViolation
from afritech.afripay.models import EntryLine, ProviderQuote, Transaction
from afritech.afripay.money import Money, SUPPORTED_CURRENCIES


FORBIDDEN_AUTHORITY_FIELDS = frozenset(
    {
        "authoritative_fare",
        "authoritative_order",
        "final_authority",
        "ledger_truth",
        "provider_truth",
        "replay_truth",
        "settlement_truth",
        "trip_legitimacy",
    }
)


def guard_transaction(transaction: Transaction) -> None:
    transaction.amount.require_positive()
    if transaction.amount.currency not in SUPPORTED_CURRENCIES:
        raise GuardViolation("unsupported transaction currency")
    if not transaction.reference:
        raise GuardViolation("transaction reference is required")
    reject_authority_fields(transaction.metadata)


def guard_journal_balances(lines: Iterable[EntryLine]) -> None:
    totals: dict[str, dict[str, Decimal]] = {}
    for line in lines:
        if line.debit.currency != line.credit.currency:
            raise GuardViolation("journal line currency mismatch")
        currency = line.debit.currency
        totals.setdefault(currency, {"debit": Decimal("0.00"), "credit": Decimal("0.00")})
        totals[currency]["debit"] += line.debit.amount
        totals[currency]["credit"] += line.credit.amount
        if line.debit.amount > 0 and line.credit.amount > 0:
            raise GuardViolation("journal line cannot debit and credit simultaneously")
    if not totals:
        raise GuardViolation("journal must have lines")
    for currency, total in totals.items():
        if total["debit"] != total["credit"]:
            raise GuardViolation(f"ledger imbalance for {currency}")


def guard_quote(quote: ProviderQuote) -> None:
    quote.amount.require_positive()
    if quote.fee.currency != quote.amount.currency:
        raise GuardViolation("provider quote fee currency mismatch")
    if quote.estimated_latency_ms <= 0:
        raise GuardViolation("provider latency must be positive")
    if quote.reliability < Decimal("0.00") or quote.reliability > Decimal("1.00"):
        raise GuardViolation("provider reliability must be 0..1")


def reject_authority_fields(payload: Mapping[str, object]) -> None:
    injected = FORBIDDEN_AUTHORITY_FIELDS.intersection(payload.keys())
    if injected:
        raise GuardViolation(f"forbidden authority field: {sorted(injected)[0]}")
    for value in payload.values():
        if isinstance(value, Mapping):
            reject_authority_fields(value)


def require_same_currency(amounts: Iterable[Money]) -> str:
    currencies = {amount.currency for amount in amounts}
    if len(currencies) != 1:
        raise GuardViolation("amounts must share a currency")
    return next(iter(currencies))
