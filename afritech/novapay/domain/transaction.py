"""Canonical NovaPay transaction domain foundation.

This module defines the canonical identifiers and classifications used by
NovaPay business-facing financial transactions.

It intentionally does not replace:

- the existing AfriPay operational Transaction model;
- NovaPay transaction persistence records;
- NovaPay runtime services;
- transfer, settlement, or payment-provider implementations.

Those components will progressively integrate with this canonical domain
contract through later compatibility work packages.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
import re

from .journal_entry import JournalEntryId
from .money import Money
from .wallet import WalletId


_TRANSACTION_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$"
)


def _normalize_transaction_identifier(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    if not _TRANSACTION_IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"{field_name} must be 3 to 128 characters and contain only "
            "letters, numbers, periods, underscores, colons, or hyphens"
        )

    return normalized


class TransactionType(str, Enum):
    """Business classification of a NovaPay financial transaction."""

    TRANSFER = "transfer"
    PAYMENT = "payment"
    FUNDING = "funding"
    WITHDRAWAL = "withdrawal"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    MERCHANT_PAYMENT = "merchant_payment"
    BILL_PAYMENT = "bill_payment"
    PAYROLL = "payroll"
    PAYOUT = "payout"
    REFUND = "refund"
    REVERSAL = "reversal"
    FEE = "fee"
    FX_CONVERSION = "fx_conversion"
    SETTLEMENT = "settlement"
    ADJUSTMENT = "adjustment"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> "TransactionType":
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "transaction type must be a string"
            )

        normalized = value.strip().lower().replace("-", "_")

        if not normalized:
            raise ValueError(
                "transaction type must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                item.value
                for item in cls
            )

            raise ValueError(
                f"unsupported transaction type: {normalized}; "
                f"supported values: {supported}"
            ) from exc


class TransactionStatus(str, Enum):
    """Lifecycle status of a canonical NovaPay transaction."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> "TransactionStatus":
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "transaction status must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "transaction status must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                item.value
                for item in cls
            )

            raise ValueError(
                f"unsupported transaction status: {normalized}; "
                f"supported values: {supported}"
            ) from exc

    @property
    def is_terminal(self) -> bool:
        return self in {
            TransactionStatus.COMPLETED,
            TransactionStatus.FAILED,
            TransactionStatus.CANCELLED,
            TransactionStatus.REVERSED,
        }

    @property
    def is_successful(self) -> bool:
        return self is TransactionStatus.COMPLETED


class TransactionDirection(str, Enum):
    """Direction of a transaction relative to the referenced wallet."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> "TransactionDirection":
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "transaction direction must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "transaction direction must not be empty"
            )

        aliases = {
            "credit": cls.INBOUND,
            "incoming": cls.INBOUND,
            "debit": cls.OUTBOUND,
            "outgoing": cls.OUTBOUND,
            "self": cls.INTERNAL,
        }

        if normalized in aliases:
            return aliases[normalized]

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                item.value
                for item in cls
            )

            raise ValueError(
                f"unsupported transaction direction: {normalized}; "
                f"supported values: {supported}"
            ) from exc


@dataclass(frozen=True, slots=True, order=True)
class TransactionId:
    """Strongly typed canonical NovaPay transaction identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_transaction_identifier(
                self.value,
                field_name="transaction id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> "TransactionId":
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_transaction_identifier(
                value,
                field_name="transaction id",
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value



# WP-001C5 Section 2B — Transaction metadata foundation


def _freeze_transaction_metadata(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise TypeError(
            "transaction metadata must be a mapping"
        )

    copied: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(
                "transaction metadata keys must be strings"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "transaction metadata keys must not be empty"
            )

        copied[normalized_key] = item

    return MappingProxyType(copied)


@dataclass(frozen=True, slots=True)
class TransactionMetadata:
    """Immutable metadata associated with a NovaPay transaction."""

    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            _freeze_transaction_metadata(self.values),
        )

    @classmethod
    def of(
        cls,
        value: (
            Mapping[str, Any]
            | "TransactionMetadata"
            | None
        ),
    ) -> "TransactionMetadata":
        if isinstance(value, cls):
            return value

        return cls(
            _freeze_transaction_metadata(value)
        )

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.values.get(key, default)

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(
            dict(self.values)
        )

    def with_value(
        self,
        key: str,
        value: Any,
    ) -> "TransactionMetadata":
        if not isinstance(key, str):
            raise TypeError(
                "transaction metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "transaction metadata key must not be empty"
            )

        updated = dict(self.values)
        updated[normalized_key] = value

        return TransactionMetadata(updated)

    def without(
        self,
        key: str,
    ) -> "TransactionMetadata":
        if not isinstance(key, str):
            raise TypeError(
                "transaction metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "transaction metadata key must not be empty"
            )

        updated = dict(self.values)
        updated.pop(normalized_key, None)

        return TransactionMetadata(updated)


# WP-001C5 Section 2C — Transaction aggregate


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_transaction_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _normalize_transaction_version(
    value: object,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "transaction version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "transaction version must be at least 1"
        )

    return value


def _normalize_optional_transaction_identifier(
    value: object | None,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    return _normalize_transaction_identifier(
        value,
        field_name=field_name,
    )


def _normalize_optional_transaction_description(
    value: object | None,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(
            "transaction description must be a string"
        )

    normalized = " ".join(value.split())

    if not normalized:
        raise ValueError(
            "transaction description must not be empty"
        )

    if len(normalized) > 500:
        raise ValueError(
            "transaction description must not exceed "
            "500 characters"
        )

    return normalized


def _validate_transaction_wallet_references(
    *,
    direction: TransactionDirection,
    source_wallet_id: WalletId | None,
    destination_wallet_id: WalletId | None,
) -> None:
    if direction is TransactionDirection.INBOUND:
        if destination_wallet_id is None:
            raise ValueError(
                "inbound transaction requires "
                "destination_wallet_id"
            )

    elif direction is TransactionDirection.OUTBOUND:
        if source_wallet_id is None:
            raise ValueError(
                "outbound transaction requires "
                "source_wallet_id"
            )

    elif direction is TransactionDirection.INTERNAL:
        if source_wallet_id is None:
            raise ValueError(
                "internal transaction requires "
                "source_wallet_id"
            )

        if destination_wallet_id is None:
            raise ValueError(
                "internal transaction requires "
                "destination_wallet_id"
            )

        if source_wallet_id == destination_wallet_id:
            raise ValueError(
                "internal transaction source and "
                "destination wallets must differ"
            )



# WP-001C5 Section 2D — Transaction lifecycle


_ALLOWED_TRANSACTION_TRANSITIONS: Mapping[
    TransactionStatus,
    frozenset[TransactionStatus],
] = MappingProxyType(
    {
        TransactionStatus.PENDING: frozenset(
            {
                TransactionStatus.AUTHORIZED,
                TransactionStatus.CANCELLED,
                TransactionStatus.FAILED,
            }
        ),
        TransactionStatus.AUTHORIZED: frozenset(
            {
                TransactionStatus.PROCESSING,
                TransactionStatus.CANCELLED,
                TransactionStatus.FAILED,
            }
        ),
        TransactionStatus.PROCESSING: frozenset(
            {
                TransactionStatus.COMPLETED,
                TransactionStatus.FAILED,
            }
        ),
        TransactionStatus.COMPLETED: frozenset(
            {
                TransactionStatus.REVERSED,
            }
        ),
        TransactionStatus.FAILED: frozenset(),
        TransactionStatus.CANCELLED: frozenset(),
        TransactionStatus.REVERSED: frozenset(),
    }
)

@dataclass(frozen=True, slots=True)
class Transaction:
    """Canonical business-facing NovaPay financial transaction.

    The Transaction aggregate represents customer-visible financial
    activity. It does not replace the authoritative JournalEntry used
    by the double-entry ledger, and it never stores wallet balances.
    """

    transaction_id: TransactionId
    transaction_type: TransactionType
    status: TransactionStatus
    direction: TransactionDirection
    amount: Money
    created_at: datetime
    updated_at: datetime
    source_wallet_id: WalletId | None = None
    destination_wallet_id: WalletId | None = None
    journal_entry_id: JournalEntryId | None = None
    description: str | None = None
    external_reference: str | None = None
    idempotency_key: str | None = None
    metadata: TransactionMetadata = field(
        default_factory=TransactionMetadata
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_transaction_id = TransactionId.of(
            self.transaction_id
        )
        normalized_type = TransactionType.parse(
            self.transaction_type
        )
        normalized_status = TransactionStatus.parse(
            self.status
        )
        normalized_direction = TransactionDirection.parse(
            self.direction
        )

        if not isinstance(self.amount, Money):
            raise TypeError(
                "transaction amount must be Money"
            )

        normalized_source_wallet_id = (
            None
            if self.source_wallet_id is None
            else WalletId.of(self.source_wallet_id)
        )
        normalized_destination_wallet_id = (
            None
            if self.destination_wallet_id is None
            else WalletId.of(self.destination_wallet_id)
        )
        normalized_journal_entry_id = (
            None
            if self.journal_entry_id is None
            else JournalEntryId.of(self.journal_entry_id)
        )

        _validate_transaction_wallet_references(
            direction=normalized_direction,
            source_wallet_id=normalized_source_wallet_id,
            destination_wallet_id=(
                normalized_destination_wallet_id
            ),
        )

        normalized_created_at = (
            _normalize_transaction_datetime(
                self.created_at,
                field_name="transaction created_at",
            )
        )
        normalized_updated_at = (
            _normalize_transaction_datetime(
                self.updated_at,
                field_name="transaction updated_at",
            )
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "transaction updated_at must not be "
                "earlier than created_at"
            )

        normalized_description = (
            _normalize_optional_transaction_description(
                self.description
            )
        )
        normalized_external_reference = (
            _normalize_optional_transaction_identifier(
                self.external_reference,
                field_name=(
                    "transaction external reference"
                ),
            )
        )
        normalized_idempotency_key = (
            _normalize_optional_transaction_identifier(
                self.idempotency_key,
                field_name=(
                    "transaction idempotency key"
                ),
            )
        )
        normalized_metadata = TransactionMetadata.of(
            self.metadata
        )
        normalized_version = (
            _normalize_transaction_version(
                self.version
            )
        )

        object.__setattr__(
            self,
            "transaction_id",
            normalized_transaction_id,
        )
        object.__setattr__(
            self,
            "transaction_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "direction",
            normalized_direction,
        )
        object.__setattr__(
            self,
            "source_wallet_id",
            normalized_source_wallet_id,
        )
        object.__setattr__(
            self,
            "destination_wallet_id",
            normalized_destination_wallet_id,
        )
        object.__setattr__(
            self,
            "journal_entry_id",
            normalized_journal_entry_id,
        )
        object.__setattr__(
            self,
            "created_at",
            normalized_created_at,
        )
        object.__setattr__(
            self,
            "updated_at",
            normalized_updated_at,
        )
        object.__setattr__(
            self,
            "description",
            normalized_description,
        )
        object.__setattr__(
            self,
            "external_reference",
            normalized_external_reference,
        )
        object.__setattr__(
            self,
            "idempotency_key",
            normalized_idempotency_key,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )
        object.__setattr__(
            self,
            "version",
            normalized_version,
        )

    @classmethod
    def create(
        cls,
        *,
        transaction_id: object,
        transaction_type: object,
        direction: object,
        amount: Money,
        source_wallet_id: object | None = None,
        destination_wallet_id: object | None = None,
        description: object | None = None,
        external_reference: object | None = None,
        idempotency_key: object | None = None,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
            | None
        ) = None,
        occurred_at: datetime | None = None,
    ) -> "Transaction":
        timestamp = (
            _utc_now()
            if occurred_at is None
            else _normalize_transaction_datetime(
                occurred_at,
                field_name="transaction occurred_at",
            )
        )

        return cls(
            transaction_id=TransactionId.of(
                transaction_id
            ),
            transaction_type=TransactionType.parse(
                transaction_type
            ),
            status=TransactionStatus.PENDING,
            direction=TransactionDirection.parse(
                direction
            ),
            amount=amount,
            source_wallet_id=(
                None
                if source_wallet_id is None
                else WalletId.of(source_wallet_id)
            ),
            destination_wallet_id=(
                None
                if destination_wallet_id is None
                else WalletId.of(destination_wallet_id)
            ),
            journal_entry_id=None,
            created_at=timestamp,
            updated_at=timestamp,
            description=(
                _normalize_optional_transaction_description(
                    description
                )
            ),
            external_reference=(
                _normalize_optional_transaction_identifier(
                    external_reference,
                    field_name=(
                        "transaction external reference"
                    ),
                )
            ),
            idempotency_key=(
                _normalize_optional_transaction_identifier(
                    idempotency_key,
                    field_name=(
                        "transaction idempotency key"
                    ),
                )
            ),
            metadata=TransactionMetadata.of(metadata),
            version=1,
        )

    @property
    def currency(self):
        return self.amount.currency

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    @property
    def is_successful(self) -> bool:
        return self.status.is_successful

    @property
    def has_journal_entry(self) -> bool:
        return self.journal_entry_id is not None


    # WP-001C5 Section 2D — lifecycle methods

    def can_transition_to(
        self,
        target_status: object,
    ) -> bool:
        normalized_target = TransactionStatus.parse(
            target_status
        )

        return normalized_target in (
            _ALLOWED_TRANSACTION_TRANSITIONS[
                self.status
            ]
        )

    def _transition_to(
        self,
        target_status: object,
        *,
        occurred_at: datetime | None = None,
        journal_entry_id: object | None = None,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
            | None
        ) = None,
    ) -> "Transaction":
        normalized_target = TransactionStatus.parse(
            target_status
        )

        if normalized_target is self.status:
            raise ValueError(
                "transaction is already in status "
                f"{self.status.value}"
            )

        if not self.can_transition_to(normalized_target):
            raise ValueError(
                "invalid transaction transition: "
                f"{self.status.value} -> "
                f"{normalized_target.value}"
            )

        timestamp = (
            _utc_now()
            if occurred_at is None
            else _normalize_transaction_datetime(
                occurred_at,
                field_name=(
                    "transaction transition occurred_at"
                ),
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "transaction transition occurred_at "
                "must not be earlier than updated_at"
            )

        next_journal_entry_id = (
            self.journal_entry_id
            if journal_entry_id is None
            else JournalEntryId.of(journal_entry_id)
        )

        if (
            normalized_target
            is TransactionStatus.COMPLETED
            and next_journal_entry_id is None
        ):
            raise ValueError(
                "completed transaction requires "
                "journal_entry_id"
            )

        next_metadata = (
            self.metadata
            if metadata is None
            else TransactionMetadata.of(metadata)
        )

        return replace(
            self,
            status=normalized_target,
            journal_entry_id=next_journal_entry_id,
            updated_at=timestamp,
            metadata=next_metadata,
            version=self.version + 1,
        )

    def authorize(
        self,
        *,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
            | None
        ) = None,
    ) -> "Transaction":
        return self._transition_to(
            TransactionStatus.AUTHORIZED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def start_processing(
        self,
        *,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
            | None
        ) = None,
    ) -> "Transaction":
        return self._transition_to(
            TransactionStatus.PROCESSING,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def complete(
        self,
        *,
        journal_entry_id: object,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
            | None
        ) = None,
    ) -> "Transaction":
        return self._transition_to(
            TransactionStatus.COMPLETED,
            occurred_at=occurred_at,
            journal_entry_id=journal_entry_id,
            metadata=metadata,
        )

    def fail(
        self,
        *,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
            | None
        ) = None,
    ) -> "Transaction":
        return self._transition_to(
            TransactionStatus.FAILED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def cancel(
        self,
        *,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
            | None
        ) = None,
    ) -> "Transaction":
        return self._transition_to(
            TransactionStatus.CANCELLED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def reverse(
        self,
        *,
        journal_entry_id: object,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
            | None
        ) = None,
    ) -> "Transaction":
        return self._transition_to(
            TransactionStatus.REVERSED,
            occurred_at=occurred_at,
            journal_entry_id=journal_entry_id,
            metadata=metadata,
        )

    def with_metadata(
        self,
        metadata: (
            Mapping[str, Any]
            | TransactionMetadata
        ),
        *,
        occurred_at: datetime | None = None,
    ) -> "Transaction":
        timestamp = (
            _utc_now()
            if occurred_at is None
            else _normalize_transaction_datetime(
                occurred_at,
                field_name=(
                    "transaction metadata occurred_at"
                ),
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "transaction metadata occurred_at "
                "must not be earlier than updated_at"
            )

        return replace(
            self,
            metadata=TransactionMetadata.of(metadata),
            updated_at=timestamp,
            version=self.version + 1,
        )

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "transaction_id": (
                    self.transaction_id.value
                ),
                "transaction_type": (
                    self.transaction_type.value
                ),
                "status": self.status.value,
                "direction": self.direction.value,
                "amount": str(self.amount.amount),
                "currency": self.amount.currency.code,
                "source_wallet_id": (
                    None
                    if self.source_wallet_id is None
                    else self.source_wallet_id.value
                ),
                "destination_wallet_id": (
                    None
                    if self.destination_wallet_id is None
                    else self.destination_wallet_id.value
                ),
                "journal_entry_id": (
                    None
                    if self.journal_entry_id is None
                    else self.journal_entry_id.value
                ),
                "description": self.description,
                "external_reference": (
                    self.external_reference
                ),
                "idempotency_key": (
                    self.idempotency_key
                ),
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "metadata": dict(
                    self.metadata.canonical_dict()
                ),
                "version": self.version,
            }
        )

__all__ = [
    "Transaction",
    "TransactionDirection",
    "TransactionId",
    "TransactionMetadata",
    "TransactionStatus",
    "TransactionType",
]
