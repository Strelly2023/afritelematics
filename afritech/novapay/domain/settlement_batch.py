from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Mapping, Self

from .money import Money


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$"
)

_METADATA_KEY_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]{0,63}$"
)

_PROHIBITED_METADATA_TOKENS = {
    "access_token",
    "api_key",
    "authorization",
    "credential",
    "credentials",
    "password",
    "pin",
    "private_key",
    "secret",
    "security_code",
    "token",
}


def _normalize_required_text(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = " ".join(value.strip().split())

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    if len(normalized) > maximum_length:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum_length} characters"
        )

    return normalized


def _normalize_identifier(
    value: object,
    *,
    field_name: str,
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=128,
    )

    if not _IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"{field_name} contains invalid characters"
        )

    return normalized


def _normalize_code(
    value: object,
    *,
    field_name: str,
    maximum_length: int = 32,
) -> str:
    normalized = (
        _normalize_required_text(
            value,
            field_name=field_name,
            maximum_length=maximum_length,
        )
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if not re.fullmatch(
        r"[a-z][a-z0-9_]*",
        normalized,
    ):
        raise ValueError(
            f"{field_name} contains invalid characters"
        )

    return normalized


def _normalize_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )

    normalized = value.astimezone(timezone.utc)

    if normalized.utcoffset() is None:
        raise ValueError(
            f"{field_name} must have a valid timezone"
        )

    return normalized


def _normalize_metadata_key(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "settlement metadata keys must be strings"
        )

    normalized = (
        value.strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if not _METADATA_KEY_PATTERN.fullmatch(normalized):
        raise ValueError(
            "settlement metadata key is invalid"
        )

    for prohibited in _PROHIBITED_METADATA_TOKENS:
        if (
            normalized == prohibited
            or normalized.endswith(f"_{prohibited}")
            or normalized.startswith(f"{prohibited}_")
        ):
            raise ValueError(
                "settlement metadata contains prohibited "
                f"sensitive key: {normalized}"
            )

    return normalized


def _normalize_metadata_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if value != value:
            raise ValueError(
                "settlement metadata float must not be NaN"
            )

        if value in (float("inf"), float("-inf")):
            raise ValueError(
                "settlement metadata float must be finite"
            )

        return value

    if isinstance(value, str):
        return _normalize_required_text(
            value,
            field_name="settlement metadata value",
            maximum_length=512,
        )

    if isinstance(value, datetime):
        return _normalize_datetime(
            value,
            field_name="settlement metadata datetime",
        ).isoformat()

    if isinstance(value, Mapping):
        normalized_items = {
            _normalize_metadata_key(key):
            _normalize_metadata_value(item)
            for key, item in value.items()
        }

        return MappingProxyType(
            dict(sorted(normalized_items.items()))
        )

    if isinstance(value, (tuple, list)):
        return tuple(
            _normalize_metadata_value(item)
            for item in value
        )

    raise TypeError(
        "unsupported settlement metadata value type"
    )


def _money_currency_code(
    value: Money,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, Money):
        raise TypeError(f"{field_name} must be Money")

    direct = getattr(value, "currency_code", None)

    if callable(direct):
        direct = direct()

    if isinstance(direct, str):
        normalized = direct.strip().upper()

        if re.fullmatch(r"[A-Z]{3}", normalized):
            return normalized

    currency = getattr(value, "currency", None)

    if currency is not None:
        for attribute in (
            "code",
            "currency_code",
            "value",
        ):
            candidate = getattr(currency, attribute, None)

            if callable(candidate):
                candidate = candidate()

            if isinstance(candidate, str):
                normalized = candidate.strip().upper()

                if re.fullmatch(r"[A-Z]{3}", normalized):
                    return normalized

        candidate = str(currency).strip().upper()

        if re.fullmatch(r"[A-Z]{3}", candidate):
            return candidate

    raise ValueError(
        f"{field_name} currency code could not be resolved"
    )


def _money_amount_decimal(
    value: Money,
    *,
    field_name: str,
) -> Decimal:
    if not isinstance(value, Money):
        raise TypeError(f"{field_name} must be Money")

    amount = getattr(value, "amount", None)

    if callable(amount):
        amount = amount()

    if amount is None:
        amount = getattr(value, "value", None)

        if callable(amount):
            amount = amount()

    try:
        normalized = Decimal(str(amount))
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"{field_name} amount could not be resolved"
        ) from exc

    if not normalized.is_finite():
        raise ValueError(
            f"{field_name} amount must be finite"
        )

    return normalized


def _require_non_negative_money(
    value: Money,
    *,
    field_name: str,
) -> Money:
    amount = _money_amount_decimal(
        value,
        field_name=field_name,
    )

    if amount < 0:
        raise ValueError(
            f"{field_name} must not be negative"
        )

    return value


def _money_canonical_dict(
    value: Money,
) -> dict[str, Any]:
    canonical = getattr(value, "canonical_dict", None)

    if callable(canonical):
        payload = canonical()

        if isinstance(payload, Mapping):
            return dict(payload)

    to_dict = getattr(value, "to_dict", None)

    if callable(to_dict):
        payload = to_dict()

        if isinstance(payload, Mapping):
            return dict(payload)

    return {
        "amount": str(
            _money_amount_decimal(
                value,
                field_name="money",
            )
        ),
        "currency_code": _money_currency_code(
            value,
            field_name="money",
        ),
    }


def _normalize_version(
    value: object,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "settlement batch version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "settlement batch version must be at least one"
        )

    return value


def _normalize_entry_count(
    value: object,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "settlement batch entry count must be an integer"
        )

    if value < 0:
        raise ValueError(
            "settlement batch entry count must not be negative"
        )

    return value


class _NormalizedEnum(str, Enum):
    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_code(
            value,
            field_name=f"{cls.__name__} value",
        )

        aliases = {
            "in_progress": "processing",
            "completed": "complete",
            "cancelled": "canceled",
            "failed": "failure",
            "daily_batch": "daily",
            "intraday_batch": "intraday",
            "manual_batch": "manual",
            "automatic_batch": "automatic",
            "net": "netting",
            "gross": "gross_settlement",
        }

        normalized = aliases.get(
            normalized,
            normalized,
        )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported {cls.__name__} value: "
                f"{normalized}"
            ) from exc


class SettlementBatchStatus(_NormalizedEnum):
    DRAFT = "draft"
    OPEN = "open"
    VALIDATED = "validated"
    READY = "ready"
    PROCESSING = "processing"
    COMPLETE = "complete"
    PARTIALLY_COMPLETE = "partially_complete"
    FAILURE = "failure"
    CANCELED = "canceled"
    EXPIRED = "expired"
    RECONCILED = "reconciled"


class SettlementBatchType(_NormalizedEnum):
    GROSS_SETTLEMENT = "gross_settlement"
    NETTING = "netting"
    DAILY = "daily"
    INTRADAY = "intraday"
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    PROVIDER = "provider"
    CORRIDOR = "corridor"
    CURRENCY = "currency"
    MERCHANT = "merchant"


class SettlementEntryStatus(_NormalizedEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    INCLUDED = "included"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILURE = "failure"
    EXCLUDED = "excluded"
    REVERSED = "reversed"


class SettlementParticipantType(_NormalizedEnum):
    WALLET = "wallet"
    CUSTOMER = "customer"
    FINANCIAL_ACCOUNT = "financial_account"
    PROVIDER = "provider"
    MERCHANT = "merchant"
    AGENT = "agent"
    TREASURY = "treasury"
    CLEARING_ACCOUNT = "clearing_account"
    SETTLEMENT_ACCOUNT = "settlement_account"
    EXTERNAL_SYSTEM = "external_system"


class SettlementReferenceType(_NormalizedEnum):
    TRANSACTION = "transaction"
    TRANSFER = "transfer"
    REMITTANCE = "remittance"
    JOURNAL_ENTRY = "journal_entry"
    LEDGER_ACCOUNT = "ledger_account"
    PROVIDER_BATCH = "provider_batch"
    RECONCILIATION = "reconciliation"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True, order=True)
class SettlementBatchId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="settlement batch id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="settlement batch id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class SettlementEntryId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="settlement entry id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="settlement entry id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class SettlementParticipantId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="settlement participant id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="settlement participant id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class SettlementInstructionId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="settlement instruction id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="settlement instruction id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SettlementReference:
    reference_type: SettlementReferenceType
    reference_id: str
    external_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_type",
            SettlementReferenceType.parse(
                self.reference_type
            ),
        )

        object.__setattr__(
            self,
            "reference_id",
            _normalize_identifier(
                self.reference_id,
                field_name="settlement reference id",
            ),
        )

        normalized_external = None

        if self.external_reference is not None:
            normalized_external = (
                _normalize_identifier(
                    self.external_reference,
                    field_name=(
                        "settlement external reference"
                    ),
                )
            )

        object.__setattr__(
            self,
            "external_reference",
            normalized_external,
        )

    @classmethod
    def create(
        cls,
        *,
        reference_type: object,
        reference_id: object,
        external_reference: object = None,
    ) -> Self:
        return cls(
            reference_type=SettlementReferenceType.parse(
                reference_type
            ),
            reference_id=_normalize_identifier(
                reference_id,
                field_name="settlement reference id",
            ),
            external_reference=(
                None
                if external_reference is None
                else _normalize_identifier(
                    external_reference,
                    field_name=(
                        "settlement external reference"
                    ),
                )
            ),
        )

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "reference_type": self.reference_type.value,
            "reference_id": self.reference_id,
            "external_reference": self.external_reference,
        }


@dataclass(frozen=True, slots=True)
class SettlementParticipant:
    participant_id: SettlementParticipantId
    participant_type: SettlementParticipantType
    account_reference: str
    currency_code: str
    jurisdiction_code: str | None = None
    provider_code: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "participant_id",
            SettlementParticipantId.of(
                self.participant_id
            ),
        )

        object.__setattr__(
            self,
            "participant_type",
            SettlementParticipantType.parse(
                self.participant_type
            ),
        )

        object.__setattr__(
            self,
            "account_reference",
            _normalize_identifier(
                self.account_reference,
                field_name=(
                    "settlement participant account reference"
                ),
            ),
        )

        currency = _normalize_required_text(
            self.currency_code,
            field_name=(
                "settlement participant currency code"
            ),
            maximum_length=3,
        ).upper()

        if not re.fullmatch(r"[A-Z]{3}", currency):
            raise ValueError(
                "settlement participant currency code "
                "must be ISO-like three-letter code"
            )

        object.__setattr__(
            self,
            "currency_code",
            currency,
        )

        jurisdiction = None

        if self.jurisdiction_code is not None:
            jurisdiction = _normalize_required_text(
                self.jurisdiction_code,
                field_name=(
                    "settlement participant "
                    "jurisdiction code"
                ),
                maximum_length=3,
            ).upper()

            if not re.fullmatch(
                r"[A-Z]{2,3}",
                jurisdiction,
            ):
                raise ValueError(
                    "settlement participant jurisdiction "
                    "code must contain two or three letters"
                )

        object.__setattr__(
            self,
            "jurisdiction_code",
            jurisdiction,
        )

        provider = None

        if self.provider_code is not None:
            provider = _normalize_code(
                self.provider_code,
                field_name=(
                    "settlement participant provider code"
                ),
                maximum_length=64,
            )

        object.__setattr__(
            self,
            "provider_code",
            provider,
        )

    @classmethod
    def create(
        cls,
        *,
        participant_id: object,
        participant_type: object,
        account_reference: object,
        currency_code: object,
        jurisdiction_code: object = None,
        provider_code: object = None,
    ) -> Self:
        return cls(
            participant_id=SettlementParticipantId.of(
                participant_id
            ),
            participant_type=(
                SettlementParticipantType.parse(
                    participant_type
                )
            ),
            account_reference=_normalize_identifier(
                account_reference,
                field_name=(
                    "settlement participant account reference"
                ),
            ),
            currency_code=_normalize_required_text(
                currency_code,
                field_name=(
                    "settlement participant currency code"
                ),
                maximum_length=3,
            ),
            jurisdiction_code=(
                None
                if jurisdiction_code is None
                else _normalize_required_text(
                    jurisdiction_code,
                    field_name=(
                        "settlement participant "
                        "jurisdiction code"
                    ),
                    maximum_length=3,
                )
            ),
            provider_code=(
                None
                if provider_code is None
                else _normalize_code(
                    provider_code,
                    field_name=(
                        "settlement participant "
                        "provider code"
                    ),
                    maximum_length=64,
                )
            ),
        )

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "participant_id": self.participant_id.value,
            "participant_type": self.participant_type.value,
            "account_reference": self.account_reference,
            "currency_code": self.currency_code,
            "jurisdiction_code": self.jurisdiction_code,
            "provider_code": self.provider_code,
        }


@dataclass(frozen=True, slots=True)
class SettlementWindow:
    opens_at: datetime
    closes_at: datetime
    cutoff_at: datetime | None = None
    timezone_name: str = "UTC"

    def __post_init__(self) -> None:
        opens_at = _normalize_datetime(
            self.opens_at,
            field_name="settlement window opens_at",
        )

        closes_at = _normalize_datetime(
            self.closes_at,
            field_name="settlement window closes_at",
        )

        if closes_at <= opens_at:
            raise ValueError(
                "settlement window closes_at must be "
                "after opens_at"
            )

        cutoff_at = None

        if self.cutoff_at is not None:
            cutoff_at = _normalize_datetime(
                self.cutoff_at,
                field_name="settlement window cutoff_at",
            )

            if not (
                opens_at <= cutoff_at <= closes_at
            ):
                raise ValueError(
                    "settlement window cutoff_at must be "
                    "within the settlement window"
                )

        timezone_name = _normalize_required_text(
            self.timezone_name,
            field_name="settlement window timezone name",
            maximum_length=64,
        )

        object.__setattr__(
            self,
            "opens_at",
            opens_at,
        )
        object.__setattr__(
            self,
            "closes_at",
            closes_at,
        )
        object.__setattr__(
            self,
            "cutoff_at",
            cutoff_at,
        )
        object.__setattr__(
            self,
            "timezone_name",
            timezone_name,
        )

    @property
    def duration_seconds(self) -> int:
        return int(
            (
                self.closes_at
                - self.opens_at
            ).total_seconds()
        )

    def contains(self, value: datetime) -> bool:
        normalized = _normalize_datetime(
            value,
            field_name="settlement window timestamp",
        )

        return (
            self.opens_at
            <= normalized
            <= self.closes_at
        )

    def canonical_dict(self) -> dict[str, str | int | None]:
        return {
            "opens_at": self.opens_at.isoformat(),
            "closes_at": self.closes_at.isoformat(),
            "cutoff_at": (
                None
                if self.cutoff_at is None
                else self.cutoff_at.isoformat()
            ),
            "timezone_name": self.timezone_name,
            "duration_seconds": self.duration_seconds,
        }


@dataclass(frozen=True, slots=True)
class SettlementMetadata:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError(
                "settlement metadata must be a mapping"
            )

        normalized = {
            _normalize_metadata_key(key):
            _normalize_metadata_value(value)
            for key, value in self.values.items()
        }

        object.__setattr__(
            self,
            "values",
            MappingProxyType(
                dict(sorted(normalized.items()))
            ),
        )

    @classmethod
    def of(
        cls,
        value: object = None,
    ) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls({})

        if not isinstance(value, Mapping):
            raise TypeError(
                "settlement metadata must be a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> Mapping[str, Any]:
        return self.values




@dataclass(frozen=True, slots=True)
class SettlementInstructionMetadata:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        normalized = SettlementMetadata.of(
            self.values
        )

        object.__setattr__(
            self,
            "values",
            normalized.values,
        )

    @classmethod
    def of(
        cls,
        value: object = None,
    ) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls({})

        if isinstance(value, SettlementMetadata):
            return cls(value.values)

        if not isinstance(value, Mapping):
            raise TypeError(
                "settlement instruction metadata "
                "must be a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> Mapping[str, Any]:
        return self.values


@dataclass(frozen=True, slots=True)
class SettlementEntry:
    entry_id: SettlementEntryId
    batch_id: SettlementBatchId
    status: SettlementEntryStatus
    amount: Money
    settlement_currency_code: str
    source_participant_id: SettlementParticipantId
    destination_participant_id: SettlementParticipantId
    reference: SettlementReference
    created_at: datetime
    metadata: SettlementMetadata

    def __post_init__(self) -> None:
        entry_id = SettlementEntryId.of(
            self.entry_id
        )

        batch_id = SettlementBatchId.of(
            self.batch_id
        )

        status = SettlementEntryStatus.parse(
            self.status
        )

        amount = _require_non_negative_money(
            self.amount,
            field_name="settlement entry amount",
        )

        currency_code = _normalize_required_text(
            self.settlement_currency_code,
            field_name=(
                "settlement entry currency code"
            ),
            maximum_length=3,
        ).upper()

        if not re.fullmatch(
            r"[A-Z]{3}",
            currency_code,
        ):
            raise ValueError(
                "settlement entry currency code must be "
                "ISO-like three-letter code"
            )

        amount_currency = _money_currency_code(
            amount,
            field_name="settlement entry amount",
        )

        if amount_currency != currency_code:
            raise ValueError(
                "settlement entry amount currency must "
                "match settlement currency"
            )

        source_participant_id = (
            SettlementParticipantId.of(
                self.source_participant_id
            )
        )

        destination_participant_id = (
            SettlementParticipantId.of(
                self.destination_participant_id
            )
        )

        if (
            source_participant_id
            == destination_participant_id
        ):
            raise ValueError(
                "settlement entry source and destination "
                "participants must be different"
            )

        if not isinstance(
            self.reference,
            SettlementReference,
        ):
            raise TypeError(
                "settlement entry reference must be "
                "SettlementReference"
            )

        created_at = _normalize_datetime(
            self.created_at,
            field_name="settlement entry created_at",
        )

        metadata = SettlementMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "entry_id",
            entry_id,
        )
        object.__setattr__(
            self,
            "batch_id",
            batch_id,
        )
        object.__setattr__(
            self,
            "status",
            status,
        )
        object.__setattr__(
            self,
            "amount",
            amount,
        )
        object.__setattr__(
            self,
            "settlement_currency_code",
            currency_code,
        )
        object.__setattr__(
            self,
            "source_participant_id",
            source_participant_id,
        )
        object.__setattr__(
            self,
            "destination_participant_id",
            destination_participant_id,
        )
        object.__setattr__(
            self,
            "created_at",
            created_at,
        )
        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    @classmethod
    def create(
        cls,
        *,
        entry_id: object,
        batch_id: object,
        amount: Money,
        settlement_currency_code: object,
        source_participant_id: object,
        destination_participant_id: object,
        reference: SettlementReference,
        created_at: datetime,
        metadata: object = None,
    ) -> Self:
        return cls(
            entry_id=SettlementEntryId.of(
                entry_id
            ),
            batch_id=SettlementBatchId.of(
                batch_id
            ),
            status=SettlementEntryStatus.PENDING,
            amount=amount,
            settlement_currency_code=(
                _normalize_required_text(
                    settlement_currency_code,
                    field_name=(
                        "settlement entry currency code"
                    ),
                    maximum_length=3,
                )
            ),
            source_participant_id=(
                SettlementParticipantId.of(
                    source_participant_id
                )
            ),
            destination_participant_id=(
                SettlementParticipantId.of(
                    destination_participant_id
                )
            ),
            reference=reference,
            created_at=_normalize_datetime(
                created_at,
                field_name=(
                    "settlement entry created_at"
                ),
            ),
            metadata=SettlementMetadata.of(
                metadata
            ),
        )

    @property
    def amount_value(self) -> Decimal:
        return _money_amount_decimal(
            self.amount,
            field_name="settlement entry amount",
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            SettlementEntryStatus.COMPLETE,
            SettlementEntryStatus.FAILURE,
            SettlementEntryStatus.EXCLUDED,
            SettlementEntryStatus.REVERSED,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id.value,
            "batch_id": self.batch_id.value,
            "status": self.status.value,
            "amount": _money_canonical_dict(
                self.amount
            ),
            "settlement_currency_code": (
                self.settlement_currency_code
            ),
            "source_participant_id": (
                self.source_participant_id.value
            ),
            "destination_participant_id": (
                self.destination_participant_id.value
            ),
            "reference": self.reference.canonical_dict(),
            "created_at": self.created_at.isoformat(),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class SettlementInstruction:
    instruction_id: SettlementInstructionId
    batch_id: SettlementBatchId
    source_participant_id: SettlementParticipantId
    destination_participant_id: SettlementParticipantId
    amount: Money
    settlement_currency_code: str
    reference: SettlementReference
    requested_at: datetime
    effective_at: datetime
    expires_at: datetime | None
    metadata: SettlementInstructionMetadata

    def __post_init__(self) -> None:
        instruction_id = SettlementInstructionId.of(
            self.instruction_id
        )

        batch_id = SettlementBatchId.of(
            self.batch_id
        )

        source_participant_id = (
            SettlementParticipantId.of(
                self.source_participant_id
            )
        )

        destination_participant_id = (
            SettlementParticipantId.of(
                self.destination_participant_id
            )
        )

        if (
            source_participant_id
            == destination_participant_id
        ):
            raise ValueError(
                "settlement instruction source and "
                "destination participants must be different"
            )

        amount = _require_non_negative_money(
            self.amount,
            field_name=(
                "settlement instruction amount"
            ),
        )

        currency_code = _normalize_required_text(
            self.settlement_currency_code,
            field_name=(
                "settlement instruction currency code"
            ),
            maximum_length=3,
        ).upper()

        if not re.fullmatch(
            r"[A-Z]{3}",
            currency_code,
        ):
            raise ValueError(
                "settlement instruction currency code "
                "must be ISO-like three-letter code"
            )

        amount_currency = _money_currency_code(
            amount,
            field_name=(
                "settlement instruction amount"
            ),
        )

        if amount_currency != currency_code:
            raise ValueError(
                "settlement instruction amount currency "
                "must match settlement currency"
            )

        if not isinstance(
            self.reference,
            SettlementReference,
        ):
            raise TypeError(
                "settlement instruction reference must be "
                "SettlementReference"
            )

        requested_at = _normalize_datetime(
            self.requested_at,
            field_name=(
                "settlement instruction requested_at"
            ),
        )

        effective_at = _normalize_datetime(
            self.effective_at,
            field_name=(
                "settlement instruction effective_at"
            ),
        )

        if effective_at < requested_at:
            raise ValueError(
                "settlement instruction effective_at must "
                "not precede requested_at"
            )

        expires_at = None

        if self.expires_at is not None:
            expires_at = _normalize_datetime(
                self.expires_at,
                field_name=(
                    "settlement instruction expires_at"
                ),
            )

            if expires_at <= effective_at:
                raise ValueError(
                    "settlement instruction expires_at must "
                    "be after effective_at"
                )

        metadata = SettlementInstructionMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "instruction_id",
            instruction_id,
        )
        object.__setattr__(
            self,
            "batch_id",
            batch_id,
        )
        object.__setattr__(
            self,
            "source_participant_id",
            source_participant_id,
        )
        object.__setattr__(
            self,
            "destination_participant_id",
            destination_participant_id,
        )
        object.__setattr__(
            self,
            "amount",
            amount,
        )
        object.__setattr__(
            self,
            "settlement_currency_code",
            currency_code,
        )
        object.__setattr__(
            self,
            "requested_at",
            requested_at,
        )
        object.__setattr__(
            self,
            "effective_at",
            effective_at,
        )
        object.__setattr__(
            self,
            "expires_at",
            expires_at,
        )
        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    @classmethod
    def create(
        cls,
        *,
        instruction_id: object,
        batch_id: object,
        source_participant_id: object,
        destination_participant_id: object,
        amount: Money,
        settlement_currency_code: object,
        reference: SettlementReference,
        requested_at: datetime,
        effective_at: datetime | None = None,
        expires_at: datetime | None = None,
        metadata: object = None,
    ) -> Self:
        normalized_requested_at = _normalize_datetime(
            requested_at,
            field_name=(
                "settlement instruction requested_at"
            ),
        )

        normalized_effective_at = (
            normalized_requested_at
            if effective_at is None
            else _normalize_datetime(
                effective_at,
                field_name=(
                    "settlement instruction effective_at"
                ),
            )
        )

        return cls(
            instruction_id=SettlementInstructionId.of(
                instruction_id
            ),
            batch_id=SettlementBatchId.of(
                batch_id
            ),
            source_participant_id=(
                SettlementParticipantId.of(
                    source_participant_id
                )
            ),
            destination_participant_id=(
                SettlementParticipantId.of(
                    destination_participant_id
                )
            ),
            amount=amount,
            settlement_currency_code=(
                _normalize_required_text(
                    settlement_currency_code,
                    field_name=(
                        "settlement instruction "
                        "currency code"
                    ),
                    maximum_length=3,
                )
            ),
            reference=reference,
            requested_at=normalized_requested_at,
            effective_at=normalized_effective_at,
            expires_at=expires_at,
            metadata=(
                SettlementInstructionMetadata.of(
                    metadata
                )
            ),
        )

    @property
    def amount_value(self) -> Decimal:
        return _money_amount_decimal(
            self.amount,
            field_name=(
                "settlement instruction amount"
            ),
        )

    def is_expired(
        self,
        *,
        at: datetime,
    ) -> bool:
        if self.expires_at is None:
            return False

        normalized_at = _normalize_datetime(
            at,
            field_name=(
                "settlement instruction expiry check"
            ),
        )

        return normalized_at >= self.expires_at

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "instruction_id": self.instruction_id.value,
            "batch_id": self.batch_id.value,
            "source_participant_id": (
                self.source_participant_id.value
            ),
            "destination_participant_id": (
                self.destination_participant_id.value
            ),
            "amount": _money_canonical_dict(
                self.amount
            ),
            "settlement_currency_code": (
                self.settlement_currency_code
            ),
            "reference": self.reference.canonical_dict(),
            "requested_at": self.requested_at.isoformat(),
            "effective_at": self.effective_at.isoformat(),
            "expires_at": (
                None
                if self.expires_at is None
                else self.expires_at.isoformat()
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }



@dataclass(frozen=True, slots=True)
class SettlementFailure:
    failure_code: str
    message: str
    occurred_at: datetime
    entry_id: SettlementEntryId | None = None
    retryable: bool = False
    metadata: SettlementMetadata = SettlementMetadata({})

    def __post_init__(self) -> None:
        failure_code = _normalize_code(
            self.failure_code,
            field_name="settlement failure code",
            maximum_length=64,
        )

        message = _normalize_required_text(
            self.message,
            field_name="settlement failure message",
            maximum_length=512,
        )

        occurred_at = _normalize_datetime(
            self.occurred_at,
            field_name="settlement failure occurred_at",
        )

        entry_id = None

        if self.entry_id is not None:
            entry_id = SettlementEntryId.of(
                self.entry_id
            )

        if not isinstance(self.retryable, bool):
            raise TypeError(
                "settlement failure retryable must be boolean"
            )

        metadata = SettlementMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "failure_code",
            failure_code,
        )
        object.__setattr__(
            self,
            "message",
            message,
        )
        object.__setattr__(
            self,
            "occurred_at",
            occurred_at,
        )
        object.__setattr__(
            self,
            "entry_id",
            entry_id,
        )
        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    @classmethod
    def create(
        cls,
        *,
        failure_code: object,
        message: object,
        occurred_at: datetime,
        entry_id: object = None,
        retryable: bool = False,
        metadata: object = None,
    ) -> Self:
        return cls(
            failure_code=_normalize_code(
                failure_code,
                field_name="settlement failure code",
                maximum_length=64,
            ),
            message=_normalize_required_text(
                message,
                field_name="settlement failure message",
                maximum_length=512,
            ),
            occurred_at=_normalize_datetime(
                occurred_at,
                field_name=(
                    "settlement failure occurred_at"
                ),
            ),
            entry_id=(
                None
                if entry_id is None
                else SettlementEntryId.of(entry_id)
            ),
            retryable=retryable,
            metadata=SettlementMetadata.of(metadata),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "failure_code": self.failure_code,
            "message": self.message,
            "occurred_at": self.occurred_at.isoformat(),
            "entry_id": (
                None
                if self.entry_id is None
                else self.entry_id.value
            ),
            "retryable": self.retryable,
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class SettlementResult:
    batch_id: SettlementBatchId
    status: SettlementBatchStatus
    gross_amount: Money
    net_amount: Money
    settlement_currency_code: str
    successful_entry_count: int
    failed_entry_count: int
    excluded_entry_count: int
    failures: tuple[SettlementFailure, ...]
    completed_at: datetime
    metadata: SettlementMetadata

    def __post_init__(self) -> None:
        batch_id = SettlementBatchId.of(
            self.batch_id
        )

        status = SettlementBatchStatus.parse(
            self.status
        )

        if status not in {
            SettlementBatchStatus.COMPLETE,
            SettlementBatchStatus.PARTIALLY_COMPLETE,
            SettlementBatchStatus.FAILURE,
            SettlementBatchStatus.RECONCILED,
        }:
            raise ValueError(
                "settlement result status must be terminal "
                "completion, failure, or reconciliation status"
            )

        gross_amount = _require_non_negative_money(
            self.gross_amount,
            field_name="settlement result gross amount",
        )

        net_amount = _require_non_negative_money(
            self.net_amount,
            field_name="settlement result net amount",
        )

        currency_code = _normalize_required_text(
            self.settlement_currency_code,
            field_name=(
                "settlement result currency code"
            ),
            maximum_length=3,
        ).upper()

        if not re.fullmatch(
            r"[A-Z]{3}",
            currency_code,
        ):
            raise ValueError(
                "settlement result currency code must be "
                "ISO-like three-letter code"
            )

        if (
            _money_currency_code(
                gross_amount,
                field_name=(
                    "settlement result gross amount"
                ),
            )
            != currency_code
        ):
            raise ValueError(
                "settlement result gross amount currency "
                "must match settlement currency"
            )

        if (
            _money_currency_code(
                net_amount,
                field_name=(
                    "settlement result net amount"
                ),
            )
            != currency_code
        ):
            raise ValueError(
                "settlement result net amount currency "
                "must match settlement currency"
            )

        gross_value = _money_amount_decimal(
            gross_amount,
            field_name="settlement result gross amount",
        )

        net_value = _money_amount_decimal(
            net_amount,
            field_name="settlement result net amount",
        )

        if net_value > gross_value:
            raise ValueError(
                "settlement result net amount must not "
                "exceed gross amount"
            )

        successful_entry_count = _normalize_entry_count(
            self.successful_entry_count
        )

        failed_entry_count = _normalize_entry_count(
            self.failed_entry_count
        )

        excluded_entry_count = _normalize_entry_count(
            self.excluded_entry_count
        )

        try:
            failures = tuple(self.failures)
        except TypeError as exc:
            raise TypeError(
                "settlement result failures must be iterable"
            ) from exc

        for failure in failures:
            if not isinstance(
                failure,
                SettlementFailure,
            ):
                raise TypeError(
                    "settlement result failures must contain "
                    "SettlementFailure values"
                )

        if failed_entry_count < len(failures):
            raise ValueError(
                "settlement result failed entry count must "
                "not be lower than failure count"
            )

        if (
            status is SettlementBatchStatus.COMPLETE
            and failed_entry_count != 0
        ):
            raise ValueError(
                "complete settlement result must not contain "
                "failed entries"
            )

        if (
            status is SettlementBatchStatus.FAILURE
            and successful_entry_count != 0
        ):
            raise ValueError(
                "failed settlement result must not contain "
                "successful entries"
            )

        if (
            status
            is SettlementBatchStatus.PARTIALLY_COMPLETE
            and (
                successful_entry_count == 0
                or failed_entry_count == 0
            )
        ):
            raise ValueError(
                "partially complete settlement result must "
                "contain successful and failed entries"
            )

        completed_at = _normalize_datetime(
            self.completed_at,
            field_name=(
                "settlement result completed_at"
            ),
        )

        metadata = SettlementMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "batch_id",
            batch_id,
        )
        object.__setattr__(
            self,
            "status",
            status,
        )
        object.__setattr__(
            self,
            "gross_amount",
            gross_amount,
        )
        object.__setattr__(
            self,
            "net_amount",
            net_amount,
        )
        object.__setattr__(
            self,
            "settlement_currency_code",
            currency_code,
        )
        object.__setattr__(
            self,
            "successful_entry_count",
            successful_entry_count,
        )
        object.__setattr__(
            self,
            "failed_entry_count",
            failed_entry_count,
        )
        object.__setattr__(
            self,
            "excluded_entry_count",
            excluded_entry_count,
        )
        object.__setattr__(
            self,
            "failures",
            failures,
        )
        object.__setattr__(
            self,
            "completed_at",
            completed_at,
        )
        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    @property
    def total_entry_count(self) -> int:
        return (
            self.successful_entry_count
            + self.failed_entry_count
            + self.excluded_entry_count
        )

    @property
    def gross_amount_value(self) -> Decimal:
        return _money_amount_decimal(
            self.gross_amount,
            field_name="settlement result gross amount",
        )

    @property
    def net_amount_value(self) -> Decimal:
        return _money_amount_decimal(
            self.net_amount,
            field_name="settlement result net amount",
        )

    @property
    def difference_amount_value(self) -> Decimal:
        return (
            self.gross_amount_value
            - self.net_amount_value
        )

    @property
    def has_failures(self) -> bool:
        return (
            self.failed_entry_count > 0
            or bool(self.failures)
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id.value,
            "status": self.status.value,
            "gross_amount": _money_canonical_dict(
                self.gross_amount
            ),
            "net_amount": _money_canonical_dict(
                self.net_amount
            ),
            "settlement_currency_code": (
                self.settlement_currency_code
            ),
            "successful_entry_count": (
                self.successful_entry_count
            ),
            "failed_entry_count": (
                self.failed_entry_count
            ),
            "excluded_entry_count": (
                self.excluded_entry_count
            ),
            "total_entry_count": self.total_entry_count,
            "failures": [
                failure.canonical_dict()
                for failure in self.failures
            ],
            "completed_at": self.completed_at.isoformat(),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class SettlementSummary:
    batch_id: SettlementBatchId
    status: SettlementBatchStatus
    settlement_currency_code: str
    gross_amount: Money
    net_amount: Money
    total_entry_count: int
    successful_entry_count: int
    failed_entry_count: int
    excluded_entry_count: int
    participant_count: int
    opened_at: datetime
    closed_at: datetime
    metadata: SettlementMetadata

    def __post_init__(self) -> None:
        batch_id = SettlementBatchId.of(
            self.batch_id
        )

        status = SettlementBatchStatus.parse(
            self.status
        )

        currency_code = _normalize_required_text(
            self.settlement_currency_code,
            field_name=(
                "settlement summary currency code"
            ),
            maximum_length=3,
        ).upper()

        if not re.fullmatch(
            r"[A-Z]{3}",
            currency_code,
        ):
            raise ValueError(
                "settlement summary currency code must be "
                "ISO-like three-letter code"
            )

        gross_amount = _require_non_negative_money(
            self.gross_amount,
            field_name="settlement summary gross amount",
        )

        net_amount = _require_non_negative_money(
            self.net_amount,
            field_name="settlement summary net amount",
        )

        for value, field_name in (
            (
                gross_amount,
                "settlement summary gross amount",
            ),
            (
                net_amount,
                "settlement summary net amount",
            ),
        ):
            if (
                _money_currency_code(
                    value,
                    field_name=field_name,
                )
                != currency_code
            ):
                raise ValueError(
                    f"{field_name} currency must match "
                    "settlement currency"
                )

        if (
            _money_amount_decimal(
                net_amount,
                field_name=(
                    "settlement summary net amount"
                ),
            )
            >
            _money_amount_decimal(
                gross_amount,
                field_name=(
                    "settlement summary gross amount"
                ),
            )
        ):
            raise ValueError(
                "settlement summary net amount must not "
                "exceed gross amount"
            )

        total_entry_count = _normalize_entry_count(
            self.total_entry_count
        )

        successful_entry_count = _normalize_entry_count(
            self.successful_entry_count
        )

        failed_entry_count = _normalize_entry_count(
            self.failed_entry_count
        )

        excluded_entry_count = _normalize_entry_count(
            self.excluded_entry_count
        )

        participant_count = _normalize_entry_count(
            self.participant_count
        )

        calculated_total = (
            successful_entry_count
            + failed_entry_count
            + excluded_entry_count
        )

        if calculated_total != total_entry_count:
            raise ValueError(
                "settlement summary entry counts must "
                "equal total entry count"
            )

        opened_at = _normalize_datetime(
            self.opened_at,
            field_name="settlement summary opened_at",
        )

        closed_at = _normalize_datetime(
            self.closed_at,
            field_name="settlement summary closed_at",
        )

        if closed_at < opened_at:
            raise ValueError(
                "settlement summary closed_at must not "
                "precede opened_at"
            )

        metadata = SettlementMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "batch_id",
            batch_id,
        )
        object.__setattr__(
            self,
            "status",
            status,
        )
        object.__setattr__(
            self,
            "settlement_currency_code",
            currency_code,
        )
        object.__setattr__(
            self,
            "gross_amount",
            gross_amount,
        )
        object.__setattr__(
            self,
            "net_amount",
            net_amount,
        )
        object.__setattr__(
            self,
            "total_entry_count",
            total_entry_count,
        )
        object.__setattr__(
            self,
            "successful_entry_count",
            successful_entry_count,
        )
        object.__setattr__(
            self,
            "failed_entry_count",
            failed_entry_count,
        )
        object.__setattr__(
            self,
            "excluded_entry_count",
            excluded_entry_count,
        )
        object.__setattr__(
            self,
            "participant_count",
            participant_count,
        )
        object.__setattr__(
            self,
            "opened_at",
            opened_at,
        )
        object.__setattr__(
            self,
            "closed_at",
            closed_at,
        )
        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    @property
    def gross_amount_value(self) -> Decimal:
        return _money_amount_decimal(
            self.gross_amount,
            field_name=(
                "settlement summary gross amount"
            ),
        )

    @property
    def net_amount_value(self) -> Decimal:
        return _money_amount_decimal(
            self.net_amount,
            field_name=(
                "settlement summary net amount"
            ),
        )

    @property
    def difference_amount_value(self) -> Decimal:
        return (
            self.gross_amount_value
            - self.net_amount_value
        )

    @property
    def success_rate(self) -> Decimal:
        if self.total_entry_count == 0:
            return Decimal("0")

        return (
            Decimal(self.successful_entry_count)
            / Decimal(self.total_entry_count)
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id.value,
            "status": self.status.value,
            "settlement_currency_code": (
                self.settlement_currency_code
            ),
            "gross_amount": _money_canonical_dict(
                self.gross_amount
            ),
            "net_amount": _money_canonical_dict(
                self.net_amount
            ),
            "total_entry_count": self.total_entry_count,
            "successful_entry_count": (
                self.successful_entry_count
            ),
            "failed_entry_count": (
                self.failed_entry_count
            ),
            "excluded_entry_count": (
                self.excluded_entry_count
            ),
            "participant_count": self.participant_count,
            "opened_at": self.opened_at.isoformat(),
            "closed_at": self.closed_at.isoformat(),
            "success_rate": str(self.success_rate),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class SettlementBatch:
    batch_id: SettlementBatchId
    batch_type: SettlementBatchType
    status: SettlementBatchStatus
    window: SettlementWindow
    settlement_currency_code: str
    gross_amount: Money
    net_amount: Money
    participants: tuple[SettlementParticipant, ...]
    references: tuple[SettlementReference, ...]
    entry_count: int
    created_at: datetime
    updated_at: datetime
    version: int
    metadata: SettlementMetadata

    def __post_init__(self) -> None:
        batch_id = SettlementBatchId.of(
            self.batch_id
        )

        batch_type = SettlementBatchType.parse(
            self.batch_type
        )

        status = SettlementBatchStatus.parse(
            self.status
        )

        if not isinstance(
            self.window,
            SettlementWindow,
        ):
            raise TypeError(
                "settlement batch window must be "
                "SettlementWindow"
            )

        currency_code = _normalize_required_text(
            self.settlement_currency_code,
            field_name=(
                "settlement batch currency code"
            ),
            maximum_length=3,
        ).upper()

        if not re.fullmatch(
            r"[A-Z]{3}",
            currency_code,
        ):
            raise ValueError(
                "settlement batch currency code must be "
                "ISO-like three-letter code"
            )

        gross_amount = _require_non_negative_money(
            self.gross_amount,
            field_name=(
                "settlement batch gross amount"
            ),
        )

        net_amount = _require_non_negative_money(
            self.net_amount,
            field_name=(
                "settlement batch net amount"
            ),
        )

        gross_currency = _money_currency_code(
            gross_amount,
            field_name=(
                "settlement batch gross amount"
            ),
        )

        net_currency = _money_currency_code(
            net_amount,
            field_name=(
                "settlement batch net amount"
            ),
        )

        if gross_currency != currency_code:
            raise ValueError(
                "settlement batch gross amount currency "
                "must match settlement currency"
            )

        if net_currency != currency_code:
            raise ValueError(
                "settlement batch net amount currency "
                "must match settlement currency"
            )

        gross_value = _money_amount_decimal(
            gross_amount,
            field_name=(
                "settlement batch gross amount"
            ),
        )

        net_value = _money_amount_decimal(
            net_amount,
            field_name=(
                "settlement batch net amount"
            ),
        )

        if net_value > gross_value:
            raise ValueError(
                "settlement batch net amount must not "
                "exceed gross amount"
            )

        try:
            participants = tuple(
                self.participants
            )
        except TypeError as exc:
            raise TypeError(
                "settlement batch participants must be iterable"
            ) from exc

        for participant in participants:
            if not isinstance(
                participant,
                SettlementParticipant,
            ):
                raise TypeError(
                    "settlement batch participants must "
                    "contain SettlementParticipant values"
                )

            if (
                participant.currency_code
                != currency_code
            ):
                raise ValueError(
                    "settlement batch participant currency "
                    "must match settlement currency"
                )

        participant_ids = [
            participant.participant_id.value
            for participant in participants
        ]

        if len(participant_ids) != len(
            set(participant_ids)
        ):
            raise ValueError(
                "settlement batch participant ids "
                "must be unique"
            )

        try:
            references = tuple(self.references)
        except TypeError as exc:
            raise TypeError(
                "settlement batch references must be iterable"
            ) from exc

        for reference in references:
            if not isinstance(
                reference,
                SettlementReference,
            ):
                raise TypeError(
                    "settlement batch references must "
                    "contain SettlementReference values"
                )

        reference_keys = [
            (
                reference.reference_type.value,
                reference.reference_id,
                reference.external_reference,
            )
            for reference in references
        ]

        if len(reference_keys) != len(
            set(reference_keys)
        ):
            raise ValueError(
                "settlement batch references "
                "must be unique"
            )

        entry_count = _normalize_entry_count(
            self.entry_count
        )

        if entry_count < len(references):
            raise ValueError(
                "settlement batch entry count must not "
                "be lower than reference count"
            )

        created_at = _normalize_datetime(
            self.created_at,
            field_name=(
                "settlement batch created_at"
            ),
        )

        updated_at = _normalize_datetime(
            self.updated_at,
            field_name=(
                "settlement batch updated_at"
            ),
        )

        if updated_at < created_at:
            raise ValueError(
                "settlement batch updated_at must not "
                "precede created_at"
            )

        if created_at > self.window.closes_at:
            raise ValueError(
                "settlement batch created_at must not be "
                "after the settlement window closes"
            )

        version = _normalize_version(
            self.version
        )

        metadata = SettlementMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "batch_id",
            batch_id,
        )
        object.__setattr__(
            self,
            "batch_type",
            batch_type,
        )
        object.__setattr__(
            self,
            "status",
            status,
        )
        object.__setattr__(
            self,
            "settlement_currency_code",
            currency_code,
        )
        object.__setattr__(
            self,
            "gross_amount",
            gross_amount,
        )
        object.__setattr__(
            self,
            "net_amount",
            net_amount,
        )
        object.__setattr__(
            self,
            "participants",
            participants,
        )
        object.__setattr__(
            self,
            "references",
            references,
        )
        object.__setattr__(
            self,
            "entry_count",
            entry_count,
        )
        object.__setattr__(
            self,
            "created_at",
            created_at,
        )
        object.__setattr__(
            self,
            "updated_at",
            updated_at,
        )
        object.__setattr__(
            self,
            "version",
            version,
        )
        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    @classmethod
    def create(
        cls,
        *,
        batch_id: object,
        batch_type: object,
        window: SettlementWindow,
        settlement_currency_code: object,
        gross_amount: Money,
        net_amount: Money,
        participants: object = (),
        references: object = (),
        entry_count: object = 0,
        created_at: datetime,
        metadata: object = None,
    ) -> Self:
        normalized_created_at = _normalize_datetime(
            created_at,
            field_name=(
                "settlement batch created_at"
            ),
        )

        return cls(
            batch_id=SettlementBatchId.of(
                batch_id
            ),
            batch_type=SettlementBatchType.parse(
                batch_type
            ),
            status=SettlementBatchStatus.DRAFT,
            window=window,
            settlement_currency_code=(
                _normalize_required_text(
                    settlement_currency_code,
                    field_name=(
                        "settlement batch currency code"
                    ),
                    maximum_length=3,
                )
            ),
            gross_amount=gross_amount,
            net_amount=net_amount,
            participants=participants,
            references=references,
            entry_count=_normalize_entry_count(
                entry_count
            ),
            created_at=normalized_created_at,
            updated_at=normalized_created_at,
            version=1,
            metadata=SettlementMetadata.of(
                metadata
            ),
        )

    @property
    def participant_count(self) -> int:
        return len(self.participants)

    @property
    def reference_count(self) -> int:
        return len(self.references)

    @property
    def gross_amount_value(self) -> Decimal:
        return _money_amount_decimal(
            self.gross_amount,
            field_name=(
                "settlement batch gross amount"
            ),
        )

    @property
    def net_amount_value(self) -> Decimal:
        return _money_amount_decimal(
            self.net_amount,
            field_name=(
                "settlement batch net amount"
            ),
        )

    @property
    def difference_amount_value(self) -> Decimal:
        return (
            self.gross_amount_value
            - self.net_amount_value
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            SettlementBatchStatus.COMPLETE,
            SettlementBatchStatus.PARTIALLY_COMPLETE,
            SettlementBatchStatus.FAILURE,
            SettlementBatchStatus.CANCELED,
            SettlementBatchStatus.EXPIRED,
            SettlementBatchStatus.RECONCILED,
        }

    @property
    def is_cross_jurisdictional(self) -> bool:
        jurisdictions = {
            participant.jurisdiction_code
            for participant in self.participants
            if participant.jurisdiction_code
            is not None
        }

        return len(jurisdictions) > 1

    @property
    def is_empty(self) -> bool:
        return self.entry_count == 0


    def _with_change(
        self,
        *,
        changed_at: datetime,
        status: SettlementBatchStatus | None = None,
        window: SettlementWindow | None = None,
        metadata: SettlementMetadata | None = None,
    ) -> Self:
        normalized_changed_at = _normalize_datetime(
            changed_at,
            field_name="settlement batch changed_at",
        )

        if normalized_changed_at < self.updated_at:
            raise ValueError(
                "settlement batch changed_at must not "
                "precede updated_at"
            )

        next_status = (
            self.status
            if status is None
            else SettlementBatchStatus.parse(status)
        )

        next_window = (
            self.window
            if window is None
            else window
        )

        if not isinstance(next_window, SettlementWindow):
            raise TypeError(
                "settlement batch window must be "
                "SettlementWindow"
            )

        next_metadata = (
            self.metadata
            if metadata is None
            else SettlementMetadata.of(metadata)
        )

        if (
            next_status is self.status
            and next_window == self.window
            and next_metadata == self.metadata
        ):
            raise ValueError(
                "settlement batch change must modify "
                "at least one field"
            )

        return replace(
            self,
            status=next_status,
            window=next_window,
            metadata=next_metadata,
            updated_at=normalized_changed_at,
            version=self.version + 1,
        )

    def _transition_status(
        self,
        *,
        target_status: SettlementBatchStatus,
        allowed_from: set[SettlementBatchStatus],
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        if self.status not in allowed_from:
            allowed_values = ", ".join(
                sorted(
                    status.value
                    for status in allowed_from
                )
            )

            raise ValueError(
                "invalid settlement batch transition "
                f"from {self.status.value} to "
                f"{target_status.value}; allowed from: "
                f"{allowed_values}"
            )

        transition_metadata = self.metadata

        if metadata is not None:
            supplied = SettlementMetadata.of(metadata)

            merged = dict(
                self.metadata.canonical_dict()
            )
            merged.update(
                supplied.canonical_dict()
            )

            transition_metadata = SettlementMetadata.of(
                merged
            )

        return self._with_change(
            changed_at=changed_at,
            status=target_status,
            metadata=transition_metadata,
        )

    def validate(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=SettlementBatchStatus.VALIDATED,
            allowed_from={
                SettlementBatchStatus.DRAFT,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def open(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=SettlementBatchStatus.OPEN,
            allowed_from={
                SettlementBatchStatus.VALIDATED,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def mark_ready(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=SettlementBatchStatus.READY,
            allowed_from={
                SettlementBatchStatus.OPEN,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def mark_processing(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=SettlementBatchStatus.PROCESSING,
            allowed_from={
                SettlementBatchStatus.READY,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def complete(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=SettlementBatchStatus.COMPLETE,
            allowed_from={
                SettlementBatchStatus.PROCESSING,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def partially_complete(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=(
                SettlementBatchStatus.PARTIALLY_COMPLETE
            ),
            allowed_from={
                SettlementBatchStatus.PROCESSING,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def fail(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=SettlementBatchStatus.FAILURE,
            allowed_from={
                SettlementBatchStatus.PROCESSING,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def cancel(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=SettlementBatchStatus.CANCELED,
            allowed_from={
                SettlementBatchStatus.DRAFT,
                SettlementBatchStatus.VALIDATED,
                SettlementBatchStatus.OPEN,
                SettlementBatchStatus.READY,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def expire(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        normalized_changed_at = _normalize_datetime(
            changed_at,
            field_name="settlement batch changed_at",
        )

        if normalized_changed_at < self.window.closes_at:
            raise ValueError(
                "settlement batch cannot expire before "
                "the settlement window closes"
            )

        return self._transition_status(
            target_status=SettlementBatchStatus.EXPIRED,
            allowed_from={
                SettlementBatchStatus.DRAFT,
                SettlementBatchStatus.VALIDATED,
                SettlementBatchStatus.OPEN,
                SettlementBatchStatus.READY,
                SettlementBatchStatus.PROCESSING,
            },
            changed_at=normalized_changed_at,
            metadata=metadata,
        )

    def reconcile(
        self,
        *,
        changed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=SettlementBatchStatus.RECONCILED,
            allowed_from={
                SettlementBatchStatus.COMPLETE,
                SettlementBatchStatus.PARTIALLY_COMPLETE,
            },
            changed_at=changed_at,
            metadata=metadata,
        )

    def update_metadata(
        self,
        *,
        metadata: object,
        changed_at: datetime,
    ) -> Self:
        if self.is_terminal:
            raise ValueError(
                "terminal settlement batch metadata "
                "cannot be updated"
            )

        supplied = SettlementMetadata.of(metadata)

        merged = dict(
            self.metadata.canonical_dict()
        )
        merged.update(
            supplied.canonical_dict()
        )

        next_metadata = SettlementMetadata.of(
            merged
        )

        if next_metadata == self.metadata:
            raise ValueError(
                "settlement batch metadata update "
                "must change at least one value"
            )

        return self._with_change(
            changed_at=changed_at,
            metadata=next_metadata,
        )

    def update_window(
        self,
        *,
        window: SettlementWindow,
        changed_at: datetime,
    ) -> Self:
        if self.status not in {
            SettlementBatchStatus.DRAFT,
            SettlementBatchStatus.VALIDATED,
            SettlementBatchStatus.OPEN,
            SettlementBatchStatus.READY,
        }:
            raise ValueError(
                "settlement batch window can only be "
                "updated before processing"
            )

        if not isinstance(window, SettlementWindow):
            raise TypeError(
                "settlement batch window must be "
                "SettlementWindow"
            )

        if window == self.window:
            raise ValueError(
                "settlement batch window update "
                "must change the window"
            )

        if self.created_at > window.closes_at:
            raise ValueError(
                "updated settlement window must not close "
                "before batch creation"
            )

        return self._with_change(
            changed_at=changed_at,
            window=window,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id.value,
            "batch_type": self.batch_type.value,
            "status": self.status.value,
            "window": self.window.canonical_dict(),
            "settlement_currency_code": (
                self.settlement_currency_code
            ),
            "gross_amount": _money_canonical_dict(
                self.gross_amount
            ),
            "net_amount": _money_canonical_dict(
                self.net_amount
            ),
            "participants": [
                participant.canonical_dict()
                for participant in self.participants
            ],
            "references": [
                reference.canonical_dict()
                for reference in self.references
            ],
            "entry_count": self.entry_count,
            "participant_count": self.participant_count,
            "reference_count": self.reference_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


__all__ = [
    "SettlementBatch",
    "SettlementBatchId",
    "SettlementBatchStatus",
    "SettlementBatchType",
    "SettlementEntry",
    "SettlementEntryId",
    "SettlementEntryStatus",
    "SettlementFailure",
    "SettlementInstruction",
    "SettlementInstructionId",
    "SettlementInstructionMetadata",
    "SettlementMetadata",
    "SettlementParticipant",
    "SettlementParticipantId",
    "SettlementParticipantType",
    "SettlementReference",
    "SettlementReferenceType",
    "SettlementResult",
    "SettlementSummary",
    "SettlementWindow",
]