"""Canonical NovaPay journal-entry and posting-line domain models.

This initial WP-001C4 slice defines the immutable posting-line foundation
used by NovaPay's double-entry ledger.

Posting lines:

- identify a ledger account;
- specify either a debit or credit side;
- contain a strictly positive amount;
- use a canonical currency;
- remain immutable;
- contain no calculated account balance.

The JournalEntry aggregate is added in the next validated slice.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
import re

from .ledger_account import LedgerAccountId
from .money import Currency


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$"
)


def _normalize_identifier(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    if not _IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"{field_name} must be 3 to 128 characters and contain only "
            "letters, numbers, periods, underscores, colons, or hyphens"
        )

    return normalized


def _normalize_optional_identifier(
    value: object | None,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    return _normalize_identifier(
        value,
        field_name=field_name,
    )


def _normalize_amount(value: object) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(
            "posting line amount must be a decimal-compatible value"
        )

    if isinstance(value, float):
        raise TypeError(
            "posting line amount must not be created from float"
        )

    if isinstance(value, Decimal):
        normalized = value
    elif isinstance(value, int):
        normalized = Decimal(value)
    elif isinstance(value, str):
        raw = value.strip()

        if not raw:
            raise ValueError(
                "posting line amount must not be empty"
            )

        try:
            normalized = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError(
                "posting line amount must be a valid decimal"
            ) from exc
    else:
        raise TypeError(
            "posting line amount must be a decimal-compatible value"
        )

    if not normalized.is_finite():
        raise ValueError(
            "posting line amount must be finite"
        )

    if normalized <= Decimal("0"):
        raise ValueError(
            "posting line amount must be greater than zero"
        )

    return normalized


def _canonical_decimal(value: Decimal) -> str:
    rendered = format(value, "f")

    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")

    return rendered or "0"


def _freeze_metadata(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise TypeError(
            "posting line metadata must be a mapping"
        )

    copied: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(
                "posting line metadata keys must be strings"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "posting line metadata keys must not be empty"
            )

        copied[normalized_key] = item

    return MappingProxyType(copied)


class PostingSide(str, Enum):
    """The accounting side of an immutable posting line."""

    DEBIT = "debit"
    CREDIT = "credit"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> PostingSide:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "posting side must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "posting side must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported posting side: {normalized}; "
                "supported values: debit, credit"
            ) from exc


@dataclass(frozen=True, slots=True, order=True)
class PostingLineId:
    """Strongly typed identifier for a journal posting line."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="posting line id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> PostingLineId:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="posting line id",
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PostingLineMetadata:
    """Immutable metadata associated with a posting line."""

    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            _freeze_metadata(self.values),
        )

    @classmethod
    def of(
        cls,
        value: (
            Mapping[str, Any]
            | PostingLineMetadata
            | None
        ),
    ) -> PostingLineMetadata:
        if isinstance(value, cls):
            return value

        return cls(_freeze_metadata(value))

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.values.get(key, default)

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))

    def with_value(
        self,
        key: str,
        value: Any,
    ) -> PostingLineMetadata:
        if not isinstance(key, str):
            raise TypeError(
                "posting line metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "posting line metadata key must not be empty"
            )

        updated = dict(self.values)
        updated[normalized_key] = value

        return PostingLineMetadata(updated)

    def without(
        self,
        key: str,
    ) -> PostingLineMetadata:
        if not isinstance(key, str):
            raise TypeError(
                "posting line metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "posting line metadata key must not be empty"
            )

        updated = dict(self.values)
        updated.pop(normalized_key, None)

        return PostingLineMetadata(updated)


@dataclass(frozen=True, slots=True)
class PostingLine:
    """Immutable debit or credit instruction for one ledger account."""

    line_id: PostingLineId
    account_id: LedgerAccountId
    side: PostingSide
    amount: Decimal
    currency: Currency
    description: str | None = None
    reference_id: str | None = None
    metadata: PostingLineMetadata = field(
        default_factory=PostingLineMetadata
    )

    def __post_init__(self) -> None:
        normalized_line_id = PostingLineId.of(
            self.line_id
        )

        normalized_account_id = LedgerAccountId.of(
            self.account_id
        )

        normalized_side = PostingSide.parse(
            self.side
        )

        normalized_amount = _normalize_amount(
            self.amount
        )

        normalized_currency = Currency.of(
            self.currency
        )

        normalized_description: str | None

        if self.description is None:
            normalized_description = None
        else:
            if not isinstance(self.description, str):
                raise TypeError(
                    "posting line description must be a string"
                )

            normalized_description = " ".join(
                self.description.split()
            )

            if not normalized_description:
                raise ValueError(
                    "posting line description must not be empty"
                )

            if len(normalized_description) > 240:
                raise ValueError(
                    "posting line description must not exceed "
                    "240 characters"
                )

        normalized_reference_id = (
            _normalize_optional_identifier(
                self.reference_id,
                field_name="posting line reference id",
            )
        )

        normalized_metadata = PostingLineMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "line_id",
            normalized_line_id,
        )
        object.__setattr__(
            self,
            "account_id",
            normalized_account_id,
        )
        object.__setattr__(
            self,
            "side",
            normalized_side,
        )
        object.__setattr__(
            self,
            "amount",
            normalized_amount,
        )
        object.__setattr__(
            self,
            "currency",
            normalized_currency,
        )
        object.__setattr__(
            self,
            "description",
            normalized_description,
        )
        object.__setattr__(
            self,
            "reference_id",
            normalized_reference_id,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )

    @classmethod
    def create(
        cls,
        *,
        line_id: object,
        account_id: object,
        side: object,
        amount: object,
        currency: object,
        description: str | None = None,
        reference_id: object | None = None,
        metadata: (
            Mapping[str, Any]
            | PostingLineMetadata
            | None
        ) = None,
    ) -> PostingLine:
        return cls(
            line_id=PostingLineId.of(line_id),
            account_id=LedgerAccountId.of(account_id),
            side=PostingSide.parse(side),
            amount=_normalize_amount(amount),
            currency=Currency.of(currency),
            description=description,
            reference_id=_normalize_optional_identifier(
                reference_id,
                field_name="posting line reference id",
            ),
            metadata=PostingLineMetadata.of(metadata),
        )

    @classmethod
    def debit(
        cls,
        *,
        line_id: object,
        account_id: object,
        amount: object,
        currency: object,
        description: str | None = None,
        reference_id: object | None = None,
        metadata: (
            Mapping[str, Any]
            | PostingLineMetadata
            | None
        ) = None,
    ) -> PostingLine:
        return cls.create(
            line_id=line_id,
            account_id=account_id,
            side=PostingSide.DEBIT,
            amount=amount,
            currency=currency,
            description=description,
            reference_id=reference_id,
            metadata=metadata,
        )

    @classmethod
    def credit(
        cls,
        *,
        line_id: object,
        account_id: object,
        amount: object,
        currency: object,
        description: str | None = None,
        reference_id: object | None = None,
        metadata: (
            Mapping[str, Any]
            | PostingLineMetadata
            | None
        ) = None,
    ) -> PostingLine:
        return cls.create(
            line_id=line_id,
            account_id=account_id,
            side=PostingSide.CREDIT,
            amount=amount,
            currency=currency,
            description=description,
            reference_id=reference_id,
            metadata=metadata,
        )

    @property
    def is_debit(self) -> bool:
        return self.side is PostingSide.DEBIT

    @property
    def is_credit(self) -> bool:
        return self.side is PostingSide.CREDIT

    @property
    def signed_amount(self) -> Decimal:
        if self.is_debit:
            return self.amount

        return -self.amount

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "line_id": self.line_id.value,
                "account_id": self.account_id.value,
                "side": self.side.value,
                "amount": _canonical_decimal(self.amount),
                "currency": self.currency.code,
                "description": self.description,
                "reference_id": self.reference_id,
                "metadata": dict(
                    self.metadata.canonical_dict()
                ),
            }
        )



# WP-001C4 Section 2B.1 — Journal entry foundation


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _freeze_journal_metadata(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise TypeError(
            "journal entry metadata must be a mapping"
        )

    copied: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(
                "journal entry metadata keys must be strings"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "journal entry metadata keys must not be empty"
            )

        copied[normalized_key] = item

    return MappingProxyType(copied)


class JournalEntryType(str, Enum):
    """Canonical business classifications for journal entries."""

    TRANSFER = "transfer"
    FUNDING = "funding"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    FEE = "fee"
    REFUND = "refund"
    REVERSAL = "reversal"
    SETTLEMENT = "settlement"
    ADJUSTMENT = "adjustment"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> "JournalEntryType":
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "journal entry type must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "journal entry type must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                item.value for item in cls
            )

            raise ValueError(
                f"unsupported journal entry type: {normalized}; "
                f"supported values: {supported}"
            ) from exc


class JournalEntryStatus(str, Enum):
    """Lifecycle status of an immutable journal entry."""

    DRAFT = "draft"
    POSTED = "posted"
    REVERSED = "reversed"
    VOIDED = "voided"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> "JournalEntryStatus":
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "journal entry status must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "journal entry status must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                item.value for item in cls
            )

            raise ValueError(
                f"unsupported journal entry status: {normalized}; "
                f"supported values: {supported}"
            ) from exc


@dataclass(frozen=True, slots=True, order=True)
class JournalEntryId:
    """Strongly typed canonical journal-entry identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="journal entry id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> "JournalEntryId":
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="journal entry id",
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class JournalEntryMetadata:
    """Immutable metadata attached to a journal entry."""

    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            _freeze_journal_metadata(self.values),
        )

    @classmethod
    def of(
        cls,
        value: (
            Mapping[str, Any]
            | "JournalEntryMetadata"
            | None
        ),
    ) -> "JournalEntryMetadata":
        if isinstance(value, cls):
            return value

        return cls(_freeze_journal_metadata(value))

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.values.get(key, default)

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))

    def with_value(
        self,
        key: str,
        value: Any,
    ) -> "JournalEntryMetadata":
        if not isinstance(key, str):
            raise TypeError(
                "journal entry metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "journal entry metadata key must not be empty"
            )

        updated = dict(self.values)
        updated[normalized_key] = value

        return JournalEntryMetadata(updated)

    def without(
        self,
        key: str,
    ) -> "JournalEntryMetadata":
        if not isinstance(key, str):
            raise TypeError(
                "journal entry metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "journal entry metadata key must not be empty"
            )

        updated = dict(self.values)
        updated.pop(normalized_key, None)

        return JournalEntryMetadata(updated)


# WP-001C4 Section 2B.2A — JournalEntry aggregate


def _normalize_optional_description(
    value: object | None,
    *,
    field_name: str,
    maximum_length: int = 500,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = " ".join(value.split())

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    if len(normalized) > maximum_length:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum_length} characters"
        )

    return normalized


def _normalize_version(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "journal entry version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "journal entry version must be at least 1"
        )

    return value


def _normalize_posting_lines(
    value: object,
) -> tuple[PostingLine, ...]:
    if isinstance(value, (str, bytes, Mapping)):
        raise TypeError(
            "journal entry lines must be an iterable "
            "of PostingLine instances"
        )

    try:
        lines = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(
            "journal entry lines must be an iterable "
            "of PostingLine instances"
        ) from exc

    if len(lines) < 2:
        raise ValueError(
            "journal entry must contain at least "
            "two posting lines"
        )

    for line in lines:
        if not isinstance(line, PostingLine):
            raise TypeError(
                "journal entry lines must contain "
                "only PostingLine instances"
            )

    line_ids = [line.line_id.value for line in lines]

    if len(line_ids) != len(set(line_ids)):
        raise ValueError(
            "journal entry must not contain duplicate "
            "posting line identifiers"
        )

    currencies = {
        line.currency.code
        for line in lines
    }

    if len(currencies) != 1:
        raise ValueError(
            "all journal entry posting lines must use "
            "the same currency"
        )

    total_debits = sum(
        (
            line.amount
            for line in lines
            if line.side is PostingSide.DEBIT
        ),
        Decimal("0"),
    )

    total_credits = sum(
        (
            line.amount
            for line in lines
            if line.side is PostingSide.CREDIT
        ),
        Decimal("0"),
    )

    if total_debits == Decimal("0"):
        raise ValueError(
            "journal entry must contain at least "
            "one debit posting line"
        )

    if total_credits == Decimal("0"):
        raise ValueError(
            "journal entry must contain at least "
            "one credit posting line"
        )

    if total_debits != total_credits:
        raise ValueError(
            "journal entry is not balanced: "
            f"debits={_canonical_decimal(total_debits)}, "
            f"credits={_canonical_decimal(total_credits)}"
        )

    return lines



# WP-001C4 Section 2B.2B — JournalEntry lifecycle


_ALLOWED_JOURNAL_ENTRY_TRANSITIONS: Mapping[
    JournalEntryStatus,
    frozenset[JournalEntryStatus],
] = MappingProxyType(
    {
        JournalEntryStatus.DRAFT: frozenset(
            {
                JournalEntryStatus.POSTED,
                JournalEntryStatus.VOIDED,
            }
        ),
        JournalEntryStatus.POSTED: frozenset(
            {
                JournalEntryStatus.REVERSED,
            }
        ),
        JournalEntryStatus.REVERSED: frozenset(),
        JournalEntryStatus.VOIDED: frozenset(),
    }
)

@dataclass(frozen=True, slots=True)
class JournalEntry:
    """Immutable and balanced NovaPay double-entry journal record.

    Journal entries describe accounting movements but never store an
    authoritative account balance. Account balances must be derived from
    posted journal lines or maintained by a dedicated ledger projection.
    """

    entry_id: JournalEntryId
    entry_type: JournalEntryType
    status: JournalEntryStatus
    lines: tuple[PostingLine, ...]
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    reference_id: str | None = None
    idempotency_key: str | None = None
    metadata: JournalEntryMetadata = field(
        default_factory=JournalEntryMetadata
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_entry_id = JournalEntryId.of(
            self.entry_id
        )
        normalized_entry_type = JournalEntryType.parse(
            self.entry_type
        )
        normalized_status = JournalEntryStatus.parse(
            self.status
        )
        normalized_lines = _normalize_posting_lines(
            self.lines
        )
        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name="journal entry created_at",
        )
        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name="journal entry updated_at",
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "journal entry updated_at must not be "
                "earlier than created_at"
            )

        normalized_description = (
            _normalize_optional_description(
                self.description,
                field_name="journal entry description",
            )
        )
        normalized_reference_id = (
            _normalize_optional_identifier(
                self.reference_id,
                field_name="journal entry reference id",
            )
        )
        normalized_idempotency_key = (
            _normalize_optional_identifier(
                self.idempotency_key,
                field_name="journal entry idempotency key",
            )
        )
        normalized_metadata = JournalEntryMetadata.of(
            self.metadata
        )
        normalized_version = _normalize_version(
            self.version
        )

        object.__setattr__(
            self,
            "entry_id",
            normalized_entry_id,
        )
        object.__setattr__(
            self,
            "entry_type",
            normalized_entry_type,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "lines",
            normalized_lines,
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
            "reference_id",
            normalized_reference_id,
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
        entry_id: object,
        entry_type: object,
        lines: object,
        description: object | None = None,
        reference_id: object | None = None,
        idempotency_key: object | None = None,
        metadata: (
            Mapping[str, Any]
            | JournalEntryMetadata
            | None
        ) = None,
        occurred_at: datetime | None = None,
    ) -> "JournalEntry":
        timestamp = (
            _utc_now()
            if occurred_at is None
            else _normalize_datetime(
                occurred_at,
                field_name="journal entry occurred_at",
            )
        )

        return cls(
            entry_id=JournalEntryId.of(entry_id),
            entry_type=JournalEntryType.parse(
                entry_type
            ),
            status=JournalEntryStatus.DRAFT,
            lines=_normalize_posting_lines(lines),
            created_at=timestamp,
            updated_at=timestamp,
            description=_normalize_optional_description(
                description,
                field_name="journal entry description",
            ),
            reference_id=_normalize_optional_identifier(
                reference_id,
                field_name="journal entry reference id",
            ),
            idempotency_key=(
                _normalize_optional_identifier(
                    idempotency_key,
                    field_name=(
                        "journal entry idempotency key"
                    ),
                )
            ),
            metadata=JournalEntryMetadata.of(metadata),
            version=1,
        )

    @property
    def currency(self) -> Currency:
        return self.lines[0].currency

    @property
    def total_debits(self) -> Decimal:
        return sum(
            (
                line.amount
                for line in self.lines
                if line.side is PostingSide.DEBIT
            ),
            Decimal("0"),
        )

    @property
    def total_credits(self) -> Decimal:
        return sum(
            (
                line.amount
                for line in self.lines
                if line.side is PostingSide.CREDIT
            ),
            Decimal("0"),
        )

    @property
    def is_balanced(self) -> bool:
        return (
            self.total_debits == self.total_credits
            and self.total_debits > Decimal("0")
        )

    @property
    def debit_lines(self) -> tuple[PostingLine, ...]:
        return tuple(
            line
            for line in self.lines
            if line.side is PostingSide.DEBIT
        )

    @property
    def credit_lines(self) -> tuple[PostingLine, ...]:
        return tuple(
            line
            for line in self.lines
            if line.side is PostingSide.CREDIT
        )

    @property
    def account_ids(self) -> tuple[LedgerAccountId, ...]:
        return tuple(
            dict.fromkeys(
                line.account_id
                for line in self.lines
            )
        )

    @property
    def is_draft(self) -> bool:
        return self.status is JournalEntryStatus.DRAFT

    @property
    def is_posted(self) -> bool:
        return self.status is JournalEntryStatus.POSTED

    @property
    def is_reversed(self) -> bool:
        return self.status is JournalEntryStatus.REVERSED

    @property
    def is_voided(self) -> bool:
        return self.status is JournalEntryStatus.VOIDED


    # WP-001C4 Section 2B.2B — lifecycle methods

    def can_transition_to(
        self,
        target_status: object,
    ) -> bool:
        """Return whether the requested lifecycle transition is legal."""

        normalized_target = JournalEntryStatus.parse(
            target_status
        )

        return normalized_target in (
            _ALLOWED_JOURNAL_ENTRY_TRANSITIONS[
                self.status
            ]
        )

    def _transition_to(
        self,
        target_status: object,
        *,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | JournalEntryMetadata
            | None
        ) = None,
    ) -> "JournalEntry":
        """Create the next immutable journal-entry lifecycle state."""

        normalized_target = JournalEntryStatus.parse(
            target_status
        )

        if normalized_target is self.status:
            raise ValueError(
                "journal entry is already in status "
                f"{self.status.value}"
            )

        if not self.can_transition_to(normalized_target):
            raise ValueError(
                "invalid journal entry transition: "
                f"{self.status.value} -> "
                f"{normalized_target.value}"
            )

        timestamp = (
            _utc_now()
            if occurred_at is None
            else _normalize_datetime(
                occurred_at,
                field_name=(
                    "journal entry transition occurred_at"
                ),
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "journal entry transition occurred_at "
                "must not be earlier than updated_at"
            )

        next_metadata = (
            self.metadata
            if metadata is None
            else JournalEntryMetadata.of(metadata)
        )

        return replace(
            self,
            status=normalized_target,
            updated_at=timestamp,
            metadata=next_metadata,
            version=self.version + 1,
        )

    def post(
        self,
        *,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | JournalEntryMetadata
            | None
        ) = None,
    ) -> "JournalEntry":
        """Post a balanced draft journal entry."""

        if not self.is_balanced:
            raise ValueError(
                "only a balanced journal entry can be posted"
            )

        return self._transition_to(
            JournalEntryStatus.POSTED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def reverse(
        self,
        *,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | JournalEntryMetadata
            | None
        ) = None,
    ) -> "JournalEntry":
        """Mark a posted entry as reversed.

        This lifecycle operation does not mutate or negate the original
        posting lines. A separate reversing journal entry should carry
        the compensating debit and credit lines.
        """

        return self._transition_to(
            JournalEntryStatus.REVERSED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def void(
        self,
        *,
        occurred_at: datetime | None = None,
        metadata: (
            Mapping[str, Any]
            | JournalEntryMetadata
            | None
        ) = None,
    ) -> "JournalEntry":
        """Void an unposted draft journal entry."""

        return self._transition_to(
            JournalEntryStatus.VOIDED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def with_metadata(
        self,
        metadata: (
            Mapping[str, Any]
            | JournalEntryMetadata
        ),
        *,
        occurred_at: datetime | None = None,
    ) -> "JournalEntry":
        """Return an immutable copy with replacement metadata."""

        timestamp = (
            _utc_now()
            if occurred_at is None
            else _normalize_datetime(
                occurred_at,
                field_name=(
                    "journal entry metadata occurred_at"
                ),
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "journal entry metadata occurred_at "
                "must not be earlier than updated_at"
            )

        return replace(
            self,
            metadata=JournalEntryMetadata.of(metadata),
            updated_at=timestamp,
            version=self.version + 1,
        )

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "entry_id": self.entry_id.value,
                "entry_type": self.entry_type.value,
                "status": self.status.value,
                "currency": self.currency.code,
                "total_debits": _canonical_decimal(
                    self.total_debits
                ),
                "total_credits": _canonical_decimal(
                    self.total_credits
                ),
                "description": self.description,
                "reference_id": self.reference_id,
                "idempotency_key": self.idempotency_key,
                "created_at": (
                    self.created_at.isoformat()
                ),
                "updated_at": (
                    self.updated_at.isoformat()
                ),
                "version": self.version,
                "metadata": dict(
                    self.metadata.canonical_dict()
                ),
                "lines": [
                    dict(line.canonical_dict())
                    for line in self.lines
                ],
            }
        )

__all__ = [
    "JournalEntry",
    "JournalEntryId",
    "JournalEntryMetadata",
    "JournalEntryStatus",
    "JournalEntryType",
    "PostingLine",
    "PostingLineId",
    "PostingLineMetadata",
    "PostingSide",
]
