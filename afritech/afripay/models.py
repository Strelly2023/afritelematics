"""AfriPay GA Elite in-memory domain model.

These dataclasses are intentionally framework-neutral. They can back Django
models, FastAPI handlers, queues, or tests without giving provider callbacks or
client payloads authority over financial truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from afritech.afripay.money import Money


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class WalletType(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    COMMUNITY = "community"
    SAVINGS = "savings"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    ROUTED = "routed"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class RouteStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    CONFIRMED = "confirmed"
    FAILED = "failed"


@dataclass(frozen=True)
class Party:
    party_id: str
    country: str
    kyc_level: int = 0
    risk_score: Decimal = Decimal("0.00")


@dataclass
class CurrencyAccount:
    account_id: str
    currency: str
    balance: Money
    locked: Money
    updated_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(cls, currency: str) -> "CurrencyAccount":
        return cls(new_id("curacct"), currency.upper(), Money.of("0.00", currency), Money.of("0.00", currency))

    @property
    def available(self) -> Money:
        return self.balance - self.locked


@dataclass
class Wallet:
    wallet_id: str
    owner_id: str
    wallet_type: WalletType
    home_country: str
    active: bool = True
    accounts: dict[str, CurrencyAccount] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def account(self, currency: str) -> CurrencyAccount:
        normalized = currency.upper()
        if normalized not in self.accounts:
            self.accounts[normalized] = CurrencyAccount.create(normalized)
        return self.accounts[normalized]


@dataclass(frozen=True)
class LedgerAccount:
    account_id: str
    name: str
    account_type: str
    currency: str


@dataclass(frozen=True)
class EntryLine:
    account_id: str
    debit: Money
    credit: Money


@dataclass(frozen=True)
class JournalEntry:
    journal_id: str
    reference: str
    transaction_id: str
    lines: tuple[EntryLine, ...]
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Transaction:
    transaction_id: str
    reference: str
    payer_id: str
    payee_id: str
    amount: Money
    transaction_type: str
    status: TransactionStatus = TransactionStatus.PENDING
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class ProviderQuote:
    provider: str
    rail: str
    amount: Money
    fee: Money
    estimated_latency_ms: int
    reliability: Decimal
    supports_offline_fallback: bool = False


@dataclass
class PaymentRoute:
    route_id: str
    transaction_id: str
    provider: str
    rail: str
    amount: Money
    fee: Money
    status: RouteStatus = RouteStatus.QUEUED
    latency_ms: int | None = None
    external_reference: str | None = None


@dataclass(frozen=True)
class FXRate:
    base_currency: str
    quote_currency: str
    rate: Decimal
    provider: str
    locked_reference: str
    locked_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class FXConversion:
    conversion_id: str
    transaction_id: str
    amount_in: Money
    amount_out: Money
    rate: FXRate


@dataclass
class Escrow:
    escrow_id: str
    transaction_id: str
    payer_id: str
    payee_id: str
    total: Money
    release_condition: str
    status: str = "locked"
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class PayoutItem:
    recipient_id: str
    amount: Money
    reference: str
    status: str = "pending"


@dataclass(frozen=True)
class PayoutBatch:
    payout_id: str
    initiated_by: str
    items: tuple[PayoutItem, ...]
    total: Money
    status: str = "queued"


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    customer_id: str
    amount: Money
    status: str
    due_at: datetime


@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    event_type: str
    payload: Mapping[str, Any]
    created_at: datetime = field(default_factory=utc_now)
