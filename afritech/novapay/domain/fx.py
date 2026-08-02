"""Canonical NovaPay foreign-exchange domain primitives.

This module defines stable identifiers and enumerations for exchange-rate
publication and customer-facing FX quotes.

It does not replace:

- AfriPay provider-rate acquisition;
- NovaPay transfer quote generation;
- settlement conversion;
- corridor routing;
- treasury liquidity management.

Those operational components may progressively adopt these canonical types.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Final, Self

from .money import Currency, Money


_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$"
)


def _normalize_identifier(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    if not _IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"{field_name} contains unsupported characters"
        )

    return normalized


class ExchangeRateSource(str, Enum):
    """Origin of a canonical published exchange rate."""

    PROVIDER = "provider"
    TREASURY = "treasury"
    CENTRAL_BANK = "central_bank"
    MARKET_DATA = "market_data"
    PARTNER = "partner"
    MANUAL = "manual"
    DERIVED = "derived"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "exchange rate source must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "exchange rate source must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                member.value
                for member in cls
            )

            raise ValueError(
                f"unsupported exchange rate source: "
                f"{normalized}; supported values: {supported}"
            ) from exc


class ExchangeRateStatus(str, Enum):
    """Publication lifecycle of a canonical exchange rate."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "exchange rate status must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "exchange rate status must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                member.value
                for member in cls
            )

            raise ValueError(
                f"unsupported exchange rate status: "
                f"{normalized}; supported values: {supported}"
            ) from exc


class FXQuoteStatus(str, Enum):
    """Lifecycle state of a customer or transaction FX quote."""

    PENDING = "pending"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "FX quote status must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "FX quote status must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                member.value
                for member in cls
            )

            raise ValueError(
                f"unsupported FX quote status: "
                f"{normalized}; supported values: {supported}"
            ) from exc



_SENSITIVE_METADATA_KEY_FRAGMENTS: Final[tuple[str, ...]] = (
    "access_token",
    "api_key",
    "authorization",
    "card_number",
    "credential",
    "cvv",
    "document_image",
    "identity_document",
    "password",
    "passcode",
    "pin",
    "private_key",
    "refresh_token",
    "secret",
    "security_answer",
    "token",
)


def _normalize_positive_decimal(
    value: object,
    *,
    field_name: str,
) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise TypeError(
            f"{field_name} must be numeric"
        ) from exc

    if not normalized.is_finite():
        raise ValueError(
            f"{field_name} must be finite"
        )

    if normalized <= Decimal("0"):
        raise ValueError(
            f"{field_name} must be greater than zero"
        )

    return normalized


def _normalize_non_negative_decimal(
    value: object,
    *,
    field_name: str,
) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise TypeError(
            f"{field_name} must be numeric"
        ) from exc

    if not normalized.is_finite():
        raise ValueError(
            f"{field_name} must be finite"
        )

    if normalized < Decimal("0"):
        raise ValueError(
            f"{field_name} must not be negative"
        )

    return normalized


def _normalize_fx_datetime(
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


def _normalize_fx_metadata(
    value: object,
) -> MappingProxyType[str, Any]:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise TypeError(
            "FX metadata must be a mapping"
        )

    copied: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(
                "FX metadata keys must be strings"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "FX metadata keys must not be empty"
            )

        lowered_key = normalized_key.casefold()

        if any(
            fragment in lowered_key
            for fragment in _SENSITIVE_METADATA_KEY_FRAGMENTS
        ):
            raise ValueError(
                "FX metadata contains prohibited sensitive key: "
                f"{normalized_key}"
            )

        copied[normalized_key] = deepcopy(item)

    return MappingProxyType(copied)


@dataclass(frozen=True, slots=True, order=True)
class CurrencyPair:
    """Immutable ordered pair of distinct canonical currencies."""

    base_currency: Currency
    quote_currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.base_currency, Currency):
            raise TypeError(
                "currency pair base currency must be a Currency"
            )

        if not isinstance(self.quote_currency, Currency):
            raise TypeError(
                "currency pair quote currency must be a Currency"
            )

        if self.base_currency == self.quote_currency:
            raise ValueError(
                "currency pair currencies must be distinct"
            )

    @classmethod
    def of(
        cls,
        base_currency: object,
        quote_currency: object,
    ) -> Self:
        if (
            isinstance(base_currency, cls)
            and quote_currency is None
        ):
            return base_currency

        return cls(
            base_currency=(
                base_currency
                if isinstance(base_currency, Currency)
                else Currency.of(base_currency)
            ),
            quote_currency=(
                quote_currency
                if isinstance(quote_currency, Currency)
                else Currency.of(quote_currency)
            ),
        )

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "currency pair must be a string"
            )

        normalized = value.strip().upper()

        separator = (
            "/"
            if "/" in normalized
            else "-"
            if "-" in normalized
            else None
        )

        if separator is None:
            raise ValueError(
                "currency pair must use BASE/QUOTE or BASE-QUOTE"
            )

        parts = [
            part.strip()
            for part in normalized.split(separator)
        ]

        if len(parts) != 2 or not all(parts):
            raise ValueError(
                "currency pair must contain exactly two currencies"
            )

        return cls.of(parts[0], parts[1])

    @property
    def symbol(self) -> str:
        return (
            f"{self.base_currency.code}/"
            f"{self.quote_currency.code}"
        )

    def inverse(self) -> Self:
        return type(self)(
            base_currency=self.quote_currency,
            quote_currency=self.base_currency,
        )

    def canonical_dict(self) -> dict[str, str]:
        return {
            "base_currency": self.base_currency.code,
            "quote_currency": self.quote_currency.code,
        }

    def __str__(self) -> str:
        return self.symbol


@dataclass(frozen=True, slots=True, order=True)
class ExchangeRateValue:
    """Immutable positive finite exchange-rate value."""

    rate: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rate",
            _normalize_positive_decimal(
                self.rate,
                field_name="exchange rate",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_positive_decimal(
                value,
                field_name="exchange rate",
            )
        )

    def inverse(self) -> Self:
        return type(self)(
            Decimal("1") / self.rate
        )

    def apply(self, amount: object) -> Decimal:
        normalized_amount = _normalize_non_negative_decimal(
            amount,
            field_name="FX conversion amount",
        )

        return normalized_amount * self.rate

    def canonical(self) -> str:
        return format(self.rate, "f")

    def canonical_dict(self) -> dict[str, str]:
        return {
            "rate": self.canonical(),
        }

    def __str__(self) -> str:
        return self.canonical()


@dataclass(frozen=True, slots=True, order=True)
class RateSpread:
    """Immutable FX spread expressed in basis points."""

    basis_points: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        normalized = _normalize_non_negative_decimal(
            self.basis_points,
            field_name="FX spread basis points",
        )

        if normalized > Decimal("10000"):
            raise ValueError(
                "FX spread basis points must not exceed 10000"
            )

        object.__setattr__(
            self,
            "basis_points",
            normalized,
        )

    @classmethod
    def of(cls, value: object = 0) -> Self:
        if isinstance(value, cls):
            return value

        return cls(value)

    @property
    def fraction(self) -> Decimal:
        return (
            self.basis_points
            / Decimal("10000")
        )

    @property
    def percentage(self) -> Decimal:
        return (
            self.basis_points
            / Decimal("100")
        )

    def add_to(
        self,
        rate: ExchangeRateValue,
    ) -> ExchangeRateValue:
        if not isinstance(rate, ExchangeRateValue):
            raise TypeError(
                "FX spread requires an ExchangeRateValue"
            )

        return ExchangeRateValue(
            rate.rate
            * (
                Decimal("1")
                + self.fraction
            )
        )

    def subtract_from(
        self,
        rate: ExchangeRateValue,
    ) -> ExchangeRateValue:
        if not isinstance(rate, ExchangeRateValue):
            raise TypeError(
                "FX spread requires an ExchangeRateValue"
            )

        multiplier = (
            Decimal("1")
            - self.fraction
        )

        if multiplier <= Decimal("0"):
            raise ValueError(
                "FX spread would produce a non-positive rate"
            )

        return ExchangeRateValue(
            rate.rate * multiplier
        )

    def canonical_dict(self) -> dict[str, str]:
        return {
            "basis_points": format(
                self.basis_points,
                "f",
            ),
        }


@dataclass(frozen=True, slots=True)
class FXValidityWindow:
    """Immutable timezone-aware FX validity interval."""

    valid_from: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        normalized_valid_from = _normalize_fx_datetime(
            self.valid_from,
            field_name="FX valid from",
        )
        normalized_expires_at = _normalize_fx_datetime(
            self.expires_at,
            field_name="FX expires at",
        )

        if normalized_expires_at <= normalized_valid_from:
            raise ValueError(
                "FX expires at must be later than valid from"
            )

        object.__setattr__(
            self,
            "valid_from",
            normalized_valid_from,
        )
        object.__setattr__(
            self,
            "expires_at",
            normalized_expires_at,
        )

    def is_active_at(
        self,
        value: datetime,
    ) -> bool:
        timestamp = _normalize_fx_datetime(
            value,
            field_name="FX evaluation time",
        )

        return (
            self.valid_from
            <= timestamp
            < self.expires_at
        )

    def is_expired_at(
        self,
        value: datetime,
    ) -> bool:
        timestamp = _normalize_fx_datetime(
            value,
            field_name="FX evaluation time",
        )

        return timestamp >= self.expires_at

    @property
    def duration_seconds(self) -> Decimal:
        return Decimal(
            str(
                (
                    self.expires_at
                    - self.valid_from
                ).total_seconds()
            )
        )

    def canonical_dict(self) -> dict[str, str]:
        return {
            "valid_from": self.valid_from.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class FXMetadata:
    """Immutable non-sensitive FX metadata."""

    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            _normalize_fx_metadata(self.values),
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_fx_metadata(value)
        )

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        if not isinstance(key, str):
            raise TypeError(
                "FX metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "FX metadata key must not be empty"
            )

        return self.values.get(
            normalized_key,
            default,
        )

    def with_value(
        self,
        key: str,
        value: Any,
    ) -> Self:
        if not isinstance(key, str):
            raise TypeError(
                "FX metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "FX metadata key must not be empty"
            )

        updated = dict(self.values)
        updated[normalized_key] = deepcopy(value)

        return type(self)(updated)

    def without(
        self,
        key: str,
    ) -> Self:
        if not isinstance(key, str):
            raise TypeError(
                "FX metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "FX metadata key must not be empty"
            )

        updated = dict(self.values)
        updated.pop(normalized_key, None)

        return type(self)(updated)

    def canonical_dict(
        self,
    ) -> MappingProxyType[str, Any]:
        return MappingProxyType(
            deepcopy(dict(self.values))
        )


def _normalize_fx_text(
    value: object,
    *,
    field_name: str,
    maximum_length: int = 255,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    normalized = " ".join(value.split())

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    if len(normalized) > maximum_length:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum_length} characters"
        )

    return normalized



def _normalize_optional_fx_reference(
    value: object,
    *,
    field_name: str,
    maximum_length: int = 255,
) -> str | None:
    if value is None:
        return None

    return _normalize_fx_text(
        value,
        field_name=field_name,
        maximum_length=maximum_length,
    )


def _normalize_fx_version(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "exchange rate version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "exchange rate version must be greater than "
            "or equal to 1"
        )

    return value

@dataclass(frozen=True, slots=True, order=True)
class ExchangeRateId:
    """Immutable canonical exchange-rate identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="exchange rate id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="exchange rate id",
            )
        )

    def canonical(self) -> str:
        return self.value

    def canonical_dict(self) -> dict[str, str]:
        return {
            "value": self.value,
        }

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class FXQuoteId:
    """Immutable canonical foreign-exchange quote identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="FX quote id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="FX quote id",
            )
        )

    def canonical(self) -> str:
        return self.value

    def canonical_dict(self) -> dict[str, str]:
        return {
            "value": self.value,
        }

    def __str__(self) -> str:
        return self.value



@dataclass(frozen=True, slots=True)
class ExchangeRate:
    """Immutable canonical NovaPay exchange-rate publication.

    The aggregate represents a published or draft rate between two
    canonical currencies. It does not acquire provider rates, execute
    settlement, post ledger entries, or replace AfriPay FXEngine.
    """

    exchange_rate_id: ExchangeRateId
    pair: CurrencyPair
    rate: ExchangeRateValue
    spread: RateSpread
    source: ExchangeRateSource
    status: ExchangeRateStatus
    provider: str
    provider_reference: str
    validity: FXValidityWindow
    metadata: FXMetadata = field(
        default_factory=FXMetadata
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_id = ExchangeRateId.of(
            self.exchange_rate_id
        )

        normalized_pair = (
            self.pair
            if isinstance(self.pair, CurrencyPair)
            else CurrencyPair.parse(self.pair)
            if isinstance(self.pair, str)
            else None
        )

        if normalized_pair is None:
            raise TypeError(
                "exchange rate pair must be a CurrencyPair "
                "or pair string"
            )

        normalized_rate = ExchangeRateValue.of(
            self.rate
        )
        normalized_spread = RateSpread.of(
            self.spread
        )
        normalized_source = ExchangeRateSource.parse(
            self.source
        )
        normalized_status = ExchangeRateStatus.parse(
            self.status
        )
        normalized_provider = _normalize_fx_text(
            self.provider,
            field_name="exchange rate provider",
            maximum_length=120,
        )
        normalized_provider_reference = _normalize_fx_text(
            self.provider_reference,
            field_name="exchange rate provider reference",
            maximum_length=255,
        )

        if not isinstance(self.validity, FXValidityWindow):
            raise TypeError(
                "exchange rate validity must be "
                "an FXValidityWindow"
            )

        normalized_metadata = FXMetadata.of(
            self.metadata
        )
        normalized_created_at = _normalize_fx_datetime(
            self.created_at,
            field_name="exchange rate created at",
        )
        normalized_updated_at = _normalize_fx_datetime(
            self.updated_at,
            field_name="exchange rate updated at",
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "exchange rate updated at must not be earlier "
                "than created at"
            )

        normalized_version = _normalize_fx_version(
            self.version
        )

        if (
            normalized_status
            is ExchangeRateStatus.ACTIVE
            and not self.validity.is_active_at(
                normalized_updated_at
            )
        ):
            raise ValueError(
                "active exchange rate must be valid at "
                "its updated timestamp"
            )

        if (
            normalized_status
            is ExchangeRateStatus.EXPIRED
            and not self.validity.is_expired_at(
                normalized_updated_at
            )
        ):
            raise ValueError(
                "expired exchange rate must be expired at "
                "its updated timestamp"
            )

        object.__setattr__(
            self,
            "exchange_rate_id",
            normalized_id,
        )
        object.__setattr__(
            self,
            "pair",
            normalized_pair,
        )
        object.__setattr__(
            self,
            "rate",
            normalized_rate,
        )
        object.__setattr__(
            self,
            "spread",
            normalized_spread,
        )
        object.__setattr__(
            self,
            "source",
            normalized_source,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "provider",
            normalized_provider,
        )
        object.__setattr__(
            self,
            "provider_reference",
            normalized_provider_reference,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
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
            "version",
            normalized_version,
        )

    @classmethod
    def create(
        cls,
        *,
        exchange_rate_id: object,
        pair: object,
        rate: object,
        source: object,
        provider: object,
        provider_reference: object,
        validity: FXValidityWindow,
        spread: object = 0,
        status: object = ExchangeRateStatus.DRAFT,
        metadata: object = None,
        occurred_at: datetime | None = None,
    ) -> Self:
        timestamp = (
            datetime.now(timezone.utc)
            if occurred_at is None
            else _normalize_fx_datetime(
                occurred_at,
                field_name="exchange rate occurred at",
            )
        )

        normalized_pair = (
            pair
            if isinstance(pair, CurrencyPair)
            else CurrencyPair.parse(pair)
            if isinstance(pair, str)
            else None
        )

        if normalized_pair is None:
            raise TypeError(
                "exchange rate pair must be a CurrencyPair "
                "or pair string"
            )

        return cls(
            exchange_rate_id=ExchangeRateId.of(
                exchange_rate_id
            ),
            pair=normalized_pair,
            rate=ExchangeRateValue.of(rate),
            spread=RateSpread.of(spread),
            source=ExchangeRateSource.parse(source),
            status=ExchangeRateStatus.parse(status),
            provider=_normalize_fx_text(
                provider,
                field_name="exchange rate provider",
                maximum_length=120,
            ),
            provider_reference=_normalize_fx_text(
                provider_reference,
                field_name="exchange rate provider reference",
                maximum_length=255,
            ),
            validity=validity,
            metadata=FXMetadata.of(metadata),
            created_at=timestamp,
            updated_at=timestamp,
            version=1,
        )

    @property
    def customer_rate(self) -> ExchangeRateValue:
        """Return the published rate after applying the spread."""

        return self.spread.add_to(self.rate)

    @property
    def inverse_rate(self) -> ExchangeRateValue:
        """Return the mathematical inverse of the customer rate."""

        return self.customer_rate.inverse()

    def is_active_at(
        self,
        value: datetime,
    ) -> bool:
        """Return whether this rate is active and valid at a time."""

        return (
            self.status is ExchangeRateStatus.ACTIVE
            and self.validity.is_active_at(value)
        )

    def is_expired_at(
        self,
        value: datetime,
    ) -> bool:
        """Return whether this publication is expired at a time."""

        return (
            self.status is ExchangeRateStatus.EXPIRED
            or self.validity.is_expired_at(value)
        )

    def convert_base_amount(
        self,
        amount: object,
    ) -> Decimal:
        """Convert a non-negative base amount using customer rate."""

        return self.customer_rate.apply(amount)

    def convert_quote_amount(
        self,
        amount: object,
    ) -> Decimal:
        """Convert a non-negative quote amount back to base."""

        return self.inverse_rate.apply(amount)

    def _normalize_change_time(
        self,
        occurred_at: datetime | None,
    ) -> datetime:
        timestamp = (
            datetime.now(timezone.utc)
            if occurred_at is None
            else _normalize_fx_datetime(
                occurred_at,
                field_name="exchange rate occurred at",
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "exchange rate occurred at must not be earlier "
                "than current updated at"
            )

        return timestamp

    def _require_non_terminal(self) -> None:
        if self.status in {
            ExchangeRateStatus.SUPERSEDED,
            ExchangeRateStatus.EXPIRED,
            ExchangeRateStatus.REVOKED,
        }:
            raise ValueError(
                "terminal exchange rate does not permit "
                "further changes"
            )

    def _require_draft(self) -> None:
        self._require_non_terminal()

        if self.status is not ExchangeRateStatus.DRAFT:
            raise ValueError(
                "exchange rate pricing updates require "
                "draft status"
            )

    def _metadata_with_lifecycle(
        self,
        *,
        action: str,
        reason: object = None,
    ) -> FXMetadata:
        updated = dict(self.metadata.values)
        updated["lifecycle_action"] = action

        if reason is not None:
            updated["lifecycle_reason"] = _normalize_fx_text(
                reason,
                field_name="exchange rate lifecycle reason",
                maximum_length=500,
            )

        return FXMetadata.of(updated)

    def _with_change(
        self,
        *,
        occurred_at: datetime | None,
        status: ExchangeRateStatus | None = None,
        rate: ExchangeRateValue | None = None,
        spread: RateSpread | None = None,
        validity: FXValidityWindow | None = None,
        provider_reference: str | None = None,
        metadata: FXMetadata | None = None,
    ) -> Self:
        timestamp = self._normalize_change_time(
            occurred_at
        )

        return replace(
            self,
            status=self.status if status is None else status,
            rate=self.rate if rate is None else rate,
            spread=self.spread if spread is None else spread,
            validity=(
                self.validity
                if validity is None
                else validity
            ),
            provider_reference=(
                self.provider_reference
                if provider_reference is None
                else provider_reference
            ),
            metadata=(
                self.metadata
                if metadata is None
                else metadata
            ),
            updated_at=timestamp,
            version=self.version + 1,
        )

    def publish(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Publish a draft rate as active."""

        self._require_non_terminal()

        if self.status is not ExchangeRateStatus.DRAFT:
            raise ValueError(
                "exchange rate publication requires draft status"
            )

        timestamp = self._normalize_change_time(
            occurred_at
        )

        if not self.validity.is_active_at(timestamp):
            raise ValueError(
                "exchange rate publication requires an active "
                "validity window"
            )

        return self._with_change(
            occurred_at=timestamp,
            status=ExchangeRateStatus.ACTIVE,
            metadata=self._metadata_with_lifecycle(
                action="publish",
                reason=reason,
            ),
        )

    def suspend(
        self,
        *,
        reason: object,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Suspend an active rate publication."""

        self._require_non_terminal()

        if self.status is not ExchangeRateStatus.ACTIVE:
            raise ValueError(
                "exchange rate suspension requires active status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=ExchangeRateStatus.SUSPENDED,
            metadata=self._metadata_with_lifecycle(
                action="suspend",
                reason=reason,
            ),
        )

    def resume(
        self,
        *,
        reason: object = None,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Return a suspended rate to active status."""

        self._require_non_terminal()

        if self.status is not ExchangeRateStatus.SUSPENDED:
            raise ValueError(
                "exchange rate resume requires suspended status"
            )

        timestamp = self._normalize_change_time(
            occurred_at
        )

        if not self.validity.is_active_at(timestamp):
            raise ValueError(
                "exchange rate resume requires an active "
                "validity window"
            )

        return self._with_change(
            occurred_at=timestamp,
            status=ExchangeRateStatus.ACTIVE,
            metadata=self._metadata_with_lifecycle(
                action="resume",
                reason=reason,
            ),
        )

    def supersede(
        self,
        *,
        reason: object,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Mark an active rate as replaced by a newer publication."""

        self._require_non_terminal()

        if self.status is not ExchangeRateStatus.ACTIVE:
            raise ValueError(
                "exchange rate supersession requires active status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=ExchangeRateStatus.SUPERSEDED,
            metadata=self._metadata_with_lifecycle(
                action="supersede",
                reason=reason,
            ),
        )

    def expire(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Mark a non-terminal rate expired after its validity window."""

        self._require_non_terminal()

        timestamp = self._normalize_change_time(
            occurred_at
        )

        if not self.validity.is_expired_at(timestamp):
            raise ValueError(
                "exchange rate cannot expire before "
                "its validity window ends"
            )

        return self._with_change(
            occurred_at=timestamp,
            status=ExchangeRateStatus.EXPIRED,
            metadata=self._metadata_with_lifecycle(
                action="expire",
                reason=reason,
            ),
        )

    def revoke(
        self,
        *,
        reason: object,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Revoke a draft, active, or suspended rate."""

        self._require_non_terminal()

        if self.status not in {
            ExchangeRateStatus.DRAFT,
            ExchangeRateStatus.ACTIVE,
            ExchangeRateStatus.SUSPENDED,
        }:
            raise ValueError(
                "exchange rate revocation requires draft, "
                "active, or suspended status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=ExchangeRateStatus.REVOKED,
            metadata=self._metadata_with_lifecycle(
                action="revoke",
                reason=reason,
            ),
        )

    def update_rate(
        self,
        rate: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace the draft base exchange rate."""

        self._require_draft()
        normalized_rate = ExchangeRateValue.of(rate)

        if normalized_rate == self.rate:
            raise ValueError(
                "exchange rate update must change rate"
            )

        return self._with_change(
            occurred_at=occurred_at,
            rate=normalized_rate,
        )

    def update_spread(
        self,
        spread: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace the draft customer spread."""

        self._require_draft()
        normalized_spread = RateSpread.of(spread)

        if normalized_spread == self.spread:
            raise ValueError(
                "exchange rate update must change spread"
            )

        return self._with_change(
            occurred_at=occurred_at,
            spread=normalized_spread,
        )

    def update_validity(
        self,
        validity: FXValidityWindow,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace the draft validity window."""

        self._require_draft()

        if not isinstance(validity, FXValidityWindow):
            raise TypeError(
                "exchange rate validity must be "
                "an FXValidityWindow"
            )

        if validity == self.validity:
            raise ValueError(
                "exchange rate update must change validity"
            )

        return self._with_change(
            occurred_at=occurred_at,
            validity=validity,
        )

    def update_provider_reference(
        self,
        provider_reference: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace the draft provider reference."""

        self._require_draft()

        normalized_reference = _normalize_fx_text(
            provider_reference,
            field_name="exchange rate provider reference",
            maximum_length=255,
        )

        if normalized_reference == self.provider_reference:
            raise ValueError(
                "exchange rate update must change "
                "provider reference"
            )

        return self._with_change(
            occurred_at=occurred_at,
            provider_reference=normalized_reference,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace non-sensitive metadata on a non-terminal rate."""

        self._require_non_terminal()
        normalized_metadata = FXMetadata.of(metadata)

        if normalized_metadata == self.metadata:
            raise ValueError(
                "exchange rate update must change metadata"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized_metadata,
        )

    def canonical_dict(self) -> dict[str, Any]:
        """Return deterministic canonical rate serialization."""

        return {
            "exchange_rate_id": (
                self.exchange_rate_id.value
            ),
            "pair": self.pair.canonical_dict(),
            "rate": self.rate.canonical(),
            "spread": self.spread.canonical_dict(),
            "customer_rate": (
                self.customer_rate.canonical()
            ),
            "inverse_rate": (
                self.inverse_rate.canonical()
            ),
            "source": self.source.value,
            "status": self.status.value,
            "provider": self.provider,
            "provider_reference": (
                self.provider_reference
            ),
            "validity": self.validity.canonical_dict(),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }



@dataclass(frozen=True, slots=True)
class FXQuote:
    """Immutable canonical foreign-exchange quote.

    The aggregate captures a time-bound commercial offer derived from a
    canonical ExchangeRate. It does not execute a payment, mutate a wallet,
    post a ledger entry, or replace AfriPay FXConversion.
    """

    fx_quote_id: FXQuoteId
    exchange_rate_id: ExchangeRateId
    pair: CurrencyPair
    source_amount: Money
    destination_amount: Money
    rate: ExchangeRateValue
    spread: RateSpread
    status: FXQuoteStatus
    provider: str
    provider_reference: str
    validity: FXValidityWindow
    customer_id: str | None = None
    transaction_id: str | None = None
    metadata: FXMetadata = field(
        default_factory=FXMetadata
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_quote_id = FXQuoteId.of(
            self.fx_quote_id
        )
        normalized_exchange_rate_id = ExchangeRateId.of(
            self.exchange_rate_id
        )

        normalized_pair = (
            self.pair
            if isinstance(self.pair, CurrencyPair)
            else CurrencyPair.parse(self.pair)
            if isinstance(self.pair, str)
            else None
        )

        if normalized_pair is None:
            raise TypeError(
                "FX quote pair must be a CurrencyPair "
                "or pair string"
            )

        if not isinstance(self.source_amount, Money):
            raise TypeError(
                "FX quote source amount must be Money"
            )

        if not isinstance(self.destination_amount, Money):
            raise TypeError(
                "FX quote destination amount must be Money"
            )

        normalized_rate = ExchangeRateValue.of(
            self.rate
        )
        normalized_spread = RateSpread.of(
            self.spread
        )
        normalized_status = FXQuoteStatus.parse(
            self.status
        )
        normalized_provider = _normalize_fx_text(
            self.provider,
            field_name="FX quote provider",
            maximum_length=120,
        )
        normalized_provider_reference = _normalize_fx_text(
            self.provider_reference,
            field_name="FX quote provider reference",
            maximum_length=255,
        )

        if not isinstance(self.validity, FXValidityWindow):
            raise TypeError(
                "FX quote validity must be an FXValidityWindow"
            )

        normalized_customer_id = _normalize_optional_fx_reference(
            self.customer_id,
            field_name="FX quote customer id",
            maximum_length=128,
        )
        normalized_transaction_id = (
            _normalize_optional_fx_reference(
                self.transaction_id,
                field_name="FX quote transaction id",
                maximum_length=128,
            )
        )
        normalized_metadata = FXMetadata.of(
            self.metadata
        )
        normalized_created_at = _normalize_fx_datetime(
            self.created_at,
            field_name="FX quote created at",
        )
        normalized_updated_at = _normalize_fx_datetime(
            self.updated_at,
            field_name="FX quote updated at",
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "FX quote updated at must not be earlier "
                "than created at"
            )

        normalized_version = _normalize_fx_version(
            self.version
        )

        if (
            self.source_amount.currency
            != normalized_pair.base_currency
        ):
            raise ValueError(
                "FX quote source amount currency must match "
                "pair base currency"
            )

        if (
            self.destination_amount.currency
            != normalized_pair.quote_currency
        ):
            raise ValueError(
                "FX quote destination amount currency must match "
                "pair quote currency"
            )

        if self.source_amount.amount < Decimal("0"):
            raise ValueError(
                "FX quote source amount must not be negative"
            )

        if self.destination_amount.amount < Decimal("0"):
            raise ValueError(
                "FX quote destination amount must not be negative"
            )

        expected_destination = Money.of(
            self.source_amount.amount
            * normalized_rate.rate,
            normalized_pair.quote_currency,
        )

        if (
            self.destination_amount
            != expected_destination
        ):
            raise ValueError(
                "FX quote destination amount must equal "
                "the canonical Money result of source amount "
                "multiplied by locked rate"
            )

        if (
            normalized_status
            in {
                FXQuoteStatus.OFFERED,
                FXQuoteStatus.ACCEPTED,
            }
            and not self.validity.is_active_at(
                normalized_updated_at
            )
        ):
            raise ValueError(
                "offered or accepted FX quote must be valid "
                "at its updated timestamp"
            )

        if (
            normalized_status
            is FXQuoteStatus.EXPIRED
            and not self.validity.is_expired_at(
                normalized_updated_at
            )
        ):
            raise ValueError(
                "expired FX quote must be expired at "
                "its updated timestamp"
            )

        if (
            normalized_status
            is FXQuoteStatus.CONSUMED
            and normalized_transaction_id is None
        ):
            raise ValueError(
                "consumed FX quote requires transaction id"
            )

        object.__setattr__(
            self,
            "fx_quote_id",
            normalized_quote_id,
        )
        object.__setattr__(
            self,
            "exchange_rate_id",
            normalized_exchange_rate_id,
        )
        object.__setattr__(
            self,
            "pair",
            normalized_pair,
        )
        object.__setattr__(
            self,
            "rate",
            normalized_rate,
        )
        object.__setattr__(
            self,
            "spread",
            normalized_spread,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "provider",
            normalized_provider,
        )
        object.__setattr__(
            self,
            "provider_reference",
            normalized_provider_reference,
        )
        object.__setattr__(
            self,
            "customer_id",
            normalized_customer_id,
        )
        object.__setattr__(
            self,
            "transaction_id",
            normalized_transaction_id,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
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
            "version",
            normalized_version,
        )

    @classmethod
    def create(
        cls,
        *,
        fx_quote_id: object,
        exchange_rate: ExchangeRate,
        source_amount: Money,
        status: object = FXQuoteStatus.OFFERED,
        customer_id: object = None,
        transaction_id: object = None,
        metadata: object = None,
        occurred_at: datetime | None = None,
    ) -> Self:
        if not isinstance(exchange_rate, ExchangeRate):
            raise TypeError(
                "FX quote exchange rate must be an ExchangeRate"
            )

        if not isinstance(source_amount, Money):
            raise TypeError(
                "FX quote source amount must be Money"
            )

        timestamp = (
            datetime.now(timezone.utc)
            if occurred_at is None
            else _normalize_fx_datetime(
                occurred_at,
                field_name="FX quote occurred at",
            )
        )

        if source_amount.currency != exchange_rate.pair.base_currency:
            raise ValueError(
                "FX quote source amount currency must match "
                "exchange-rate base currency"
            )

        if not exchange_rate.is_active_at(timestamp):
            raise ValueError(
                "FX quote requires an active exchange rate"
            )

        locked_rate = exchange_rate.customer_rate
        destination_amount = Money.of(
            source_amount.amount * locked_rate.rate,
            exchange_rate.pair.quote_currency,
        )

        return cls(
            fx_quote_id=FXQuoteId.of(fx_quote_id),
            exchange_rate_id=(
                exchange_rate.exchange_rate_id
            ),
            pair=exchange_rate.pair,
            source_amount=source_amount,
            destination_amount=destination_amount,
            rate=locked_rate,
            spread=exchange_rate.spread,
            status=FXQuoteStatus.parse(status),
            provider=exchange_rate.provider,
            provider_reference=(
                exchange_rate.provider_reference
            ),
            validity=exchange_rate.validity,
            customer_id=customer_id,
            transaction_id=transaction_id,
            metadata=FXMetadata.of(metadata),
            created_at=timestamp,
            updated_at=timestamp,
            version=1,
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            FXQuoteStatus.CONSUMED,
            FXQuoteStatus.EXPIRED,
            FXQuoteStatus.CANCELLED,
            FXQuoteStatus.REJECTED,
        }

    def is_active_at(
        self,
        value: datetime,
    ) -> bool:
        return (
            self.status
            in {
                FXQuoteStatus.PENDING,
                FXQuoteStatus.OFFERED,
                FXQuoteStatus.ACCEPTED,
            }
            and self.validity.is_active_at(value)
        )

    def is_expired_at(
        self,
        value: datetime,
    ) -> bool:
        return (
            self.status is FXQuoteStatus.EXPIRED
            or self.validity.is_expired_at(value)
        )

    def quote_base_amount(
        self,
        amount: object,
    ) -> Money:
        normalized_amount = _normalize_non_negative_decimal(
            amount,
            field_name="FX quote base amount",
        )

        return Money.of(
            normalized_amount * self.rate.rate,
            self.pair.quote_currency,
        )

    def quote_destination_amount(
        self,
        amount: object,
    ) -> Money:
        normalized_amount = _normalize_non_negative_decimal(
            amount,
            field_name="FX quote destination amount",
        )

        return Money.of(
            normalized_amount / self.rate.rate,
            self.pair.base_currency,
        )

    def _normalize_change_time(
        self,
        occurred_at: datetime | None,
    ) -> datetime:
        timestamp = (
            datetime.now(timezone.utc)
            if occurred_at is None
            else _normalize_fx_datetime(
                occurred_at,
                field_name="FX quote occurred at",
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "FX quote occurred at must not be earlier "
                "than current updated at"
            )

        return timestamp

    def _require_non_terminal(self) -> None:
        if self.is_terminal:
            raise ValueError(
                "terminal FX quote does not permit "
                "further changes"
            )

    def _metadata_with_lifecycle(
        self,
        *,
        action: str,
        reason: object = None,
    ) -> FXMetadata:
        updated = dict(self.metadata.values)
        updated["lifecycle_action"] = action

        if reason is not None:
            updated["lifecycle_reason"] = _normalize_fx_text(
                reason,
                field_name="FX quote lifecycle reason",
                maximum_length=500,
            )

        return FXMetadata.of(updated)

    def _with_change(
        self,
        *,
        occurred_at: datetime | None,
        status: FXQuoteStatus | None = None,
        customer_id: str | None | object = ...,
        transaction_id: str | None | object = ...,
        metadata: FXMetadata | None = None,
    ) -> Self:
        timestamp = self._normalize_change_time(
            occurred_at
        )

        next_customer_id = (
            self.customer_id
            if customer_id is ...
            else customer_id
        )
        next_transaction_id = (
            self.transaction_id
            if transaction_id is ...
            else transaction_id
        )

        return replace(
            self,
            status=(
                self.status
                if status is None
                else status
            ),
            customer_id=next_customer_id,
            transaction_id=next_transaction_id,
            metadata=(
                self.metadata
                if metadata is None
                else metadata
            ),
            updated_at=timestamp,
            version=self.version + 1,
        )

    def offer(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Move a pending quote into the offered state."""

        self._require_non_terminal()

        if self.status is not FXQuoteStatus.PENDING:
            raise ValueError(
                "FX quote offer requires pending status"
            )

        timestamp = self._normalize_change_time(
            occurred_at
        )

        if not self.validity.is_active_at(timestamp):
            raise ValueError(
                "FX quote offer requires an active "
                "validity window"
            )

        return self._with_change(
            occurred_at=timestamp,
            status=FXQuoteStatus.OFFERED,
            metadata=self._metadata_with_lifecycle(
                action="offer",
                reason=reason,
            ),
        )

    def accept(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Accept an offered quote."""

        self._require_non_terminal()

        if self.status is not FXQuoteStatus.OFFERED:
            raise ValueError(
                "FX quote acceptance requires offered status"
            )

        timestamp = self._normalize_change_time(
            occurred_at
        )

        if not self.validity.is_active_at(timestamp):
            raise ValueError(
                "FX quote acceptance requires an active "
                "validity window"
            )

        return self._with_change(
            occurred_at=timestamp,
            status=FXQuoteStatus.ACCEPTED,
            metadata=self._metadata_with_lifecycle(
                action="accept",
                reason=reason,
            ),
        )

    def consume(
        self,
        *,
        transaction_id: object,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Consume an accepted quote for a transaction."""

        self._require_non_terminal()

        if self.status is not FXQuoteStatus.ACCEPTED:
            raise ValueError(
                "FX quote consumption requires accepted status"
            )

        timestamp = self._normalize_change_time(
            occurred_at
        )

        if not self.validity.is_active_at(timestamp):
            raise ValueError(
                "FX quote consumption requires an active "
                "validity window"
            )

        normalized_transaction_id = (
            _normalize_optional_fx_reference(
                transaction_id,
                field_name="FX quote transaction id",
                maximum_length=128,
            )
        )

        if normalized_transaction_id is None:
            raise ValueError(
                "FX quote consumption requires transaction id"
            )

        if (
            self.transaction_id is not None
            and self.transaction_id
            != normalized_transaction_id
        ):
            raise ValueError(
                "FX quote is already bound to a different "
                "transaction id"
            )

        return self._with_change(
            occurred_at=timestamp,
            status=FXQuoteStatus.CONSUMED,
            transaction_id=normalized_transaction_id,
            metadata=self._metadata_with_lifecycle(
                action="consume",
                reason=reason,
            ),
        )

    def expire(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Expire a pending, offered, or accepted quote."""

        self._require_non_terminal()

        if self.status not in {
            FXQuoteStatus.PENDING,
            FXQuoteStatus.OFFERED,
            FXQuoteStatus.ACCEPTED,
        }:
            raise ValueError(
                "FX quote expiry requires pending, offered, "
                "or accepted status"
            )

        timestamp = self._normalize_change_time(
            occurred_at
        )

        if not self.validity.is_expired_at(timestamp):
            raise ValueError(
                "FX quote cannot expire before "
                "its validity window ends"
            )

        return self._with_change(
            occurred_at=timestamp,
            status=FXQuoteStatus.EXPIRED,
            metadata=self._metadata_with_lifecycle(
                action="expire",
                reason=reason,
            ),
        )

    def cancel(
        self,
        *,
        reason: object,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Cancel a pending, offered, or accepted quote."""

        self._require_non_terminal()

        if self.status not in {
            FXQuoteStatus.PENDING,
            FXQuoteStatus.OFFERED,
            FXQuoteStatus.ACCEPTED,
        }:
            raise ValueError(
                "FX quote cancellation requires pending, "
                "offered, or accepted status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=FXQuoteStatus.CANCELLED,
            metadata=self._metadata_with_lifecycle(
                action="cancel",
                reason=reason,
            ),
        )

    def reject(
        self,
        *,
        reason: object,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Reject a pending or offered quote."""

        self._require_non_terminal()

        if self.status not in {
            FXQuoteStatus.PENDING,
            FXQuoteStatus.OFFERED,
        }:
            raise ValueError(
                "FX quote rejection requires pending "
                "or offered status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=FXQuoteStatus.REJECTED,
            metadata=self._metadata_with_lifecycle(
                action="reject",
                reason=reason,
            ),
        )

    def update_customer_reference(
        self,
        customer_id: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Set or replace a customer reference before termination."""

        self._require_non_terminal()

        normalized_customer_id = (
            _normalize_optional_fx_reference(
                customer_id,
                field_name="FX quote customer id",
                maximum_length=128,
            )
        )

        if normalized_customer_id is None:
            raise ValueError(
                "FX quote customer id must not be empty"
            )

        if normalized_customer_id == self.customer_id:
            raise ValueError(
                "FX quote update must change customer id"
            )

        return self._with_change(
            occurred_at=occurred_at,
            customer_id=normalized_customer_id,
        )

    def update_transaction_reference(
        self,
        transaction_id: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Bind an accepted quote to a transaction before consumption."""

        self._require_non_terminal()

        if self.status is not FXQuoteStatus.ACCEPTED:
            raise ValueError(
                "FX quote transaction reference update "
                "requires accepted status"
            )

        normalized_transaction_id = (
            _normalize_optional_fx_reference(
                transaction_id,
                field_name="FX quote transaction id",
                maximum_length=128,
            )
        )

        if normalized_transaction_id is None:
            raise ValueError(
                "FX quote transaction id must not be empty"
            )

        if normalized_transaction_id == self.transaction_id:
            raise ValueError(
                "FX quote update must change transaction id"
            )

        if (
            self.transaction_id is not None
            and self.transaction_id
            != normalized_transaction_id
        ):
            raise ValueError(
                "FX quote transaction id cannot be rebound"
            )

        return self._with_change(
            occurred_at=occurred_at,
            transaction_id=normalized_transaction_id,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace non-sensitive metadata on a non-terminal quote."""

        self._require_non_terminal()
        normalized_metadata = FXMetadata.of(metadata)

        if normalized_metadata == self.metadata:
            raise ValueError(
                "FX quote update must change metadata"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized_metadata,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "fx_quote_id": self.fx_quote_id.value,
            "exchange_rate_id": (
                self.exchange_rate_id.value
            ),
            "pair": self.pair.canonical_dict(),
            "source_amount": {
                "amount": format(
                    self.source_amount.amount,
                    "f",
                ),
                "currency": (
                    self.source_amount.currency.code
                ),
            },
            "destination_amount": {
                "amount": format(
                    self.destination_amount.amount,
                    "f",
                ),
                "currency": (
                    self.destination_amount.currency.code
                ),
            },
            "rate": self.rate.canonical(),
            "spread": self.spread.canonical_dict(),
            "status": self.status.value,
            "provider": self.provider,
            "provider_reference": (
                self.provider_reference
            ),
            "validity": self.validity.canonical_dict(),
            "customer_id": self.customer_id,
            "transaction_id": self.transaction_id,
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


__all__ = [
    "CurrencyPair",
    "ExchangeRate",
    "ExchangeRateId",
    "ExchangeRateSource",
    "ExchangeRateStatus",
    "ExchangeRateValue",
    "FXMetadata",
    "FXQuote",
    "FXQuoteId",
    "FXQuoteStatus",
    "FXValidityWindow",
    "RateSpread",
]
