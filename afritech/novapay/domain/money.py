"""Canonical NovaPay monetary value objects.

This module contains immutable domain values only. It performs no persistence,
ledger posting, wallet mutation, settlement, provider execution, or external
I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_EVEN,
)
from types import MappingProxyType
from typing import Any, Mapping


DEFAULT_MINOR_UNITS = 2

_CURRENCY_MINOR_UNITS = MappingProxyType(
    {
        "AUD": 2,
        "BIF": 0,
        "CDF": 2,
        "EUR": 2,
        "GBP": 2,
        "KES": 2,
        "TZS": 2,
        "UGX": 0,
        "USD": 2,
        "ZAR": 2,
    }
)


def _normalize_currency_code(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("currency code must be a string")

    normalized = value.strip().upper()

    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError(
            "currency code must contain exactly three alphabetic characters"
        )

    return normalized


def _decimal_from_value(value: object) -> Decimal:
    if isinstance(value, bool):
        raise TypeError("monetary amount cannot be a boolean")

    if isinstance(value, float):
        raise TypeError(
            "floating-point monetary amounts are not accepted; "
            "use Decimal, int, or string"
        )

    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, int):
        amount = Decimal(value)
    elif isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            raise ValueError("monetary amount must not be empty")

        try:
            amount = Decimal(normalized)
        except InvalidOperation as exc:
            raise ValueError("invalid monetary amount") from exc
    else:
        raise TypeError(
            "monetary amount must be Decimal, int, or string"
        )

    if not amount.is_finite():
        raise ValueError("monetary amount must be finite")

    return amount


@dataclass(frozen=True, slots=True, order=True)
class Currency:
    """Normalized three-letter currency code."""

    code: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "code",
            _normalize_currency_code(self.code),
        )

    @classmethod
    def of(cls, value: object) -> Currency:
        if isinstance(value, cls):
            return value

        return cls(_normalize_currency_code(value))

    @property
    def minor_units(self) -> int:
        return _CURRENCY_MINOR_UNITS.get(
            self.code,
            DEFAULT_MINOR_UNITS,
        )

    @property
    def quantum(self) -> Decimal:
        return Decimal(1).scaleb(-self.minor_units)

    def canonical(self) -> str:
        return self.code

    def canonical_dict(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "code": self.code,
                "minor_units": self.minor_units,
            }
        )

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable currency-safe monetary value."""

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        normalized_currency = Currency.of(self.currency)
        normalized_amount = _decimal_from_value(self.amount).quantize(
            normalized_currency.quantum,
            rounding=ROUND_HALF_EVEN,
        )

        object.__setattr__(self, "currency", normalized_currency)
        object.__setattr__(self, "amount", normalized_amount)

    @classmethod
    def of(
        cls,
        amount: object,
        currency: object,
    ) -> Money:
        return cls(
            amount=_decimal_from_value(amount),
            currency=Currency.of(currency),
        )

    @classmethod
    def zero(cls, currency: object) -> Money:
        return cls.of(0, currency)

    @property
    def is_zero(self) -> bool:
        return self.amount == Decimal("0").quantize(
            self.currency.quantum
        )

    @property
    def is_positive(self) -> bool:
        return self.amount > 0

    @property
    def is_negative(self) -> bool:
        return self.amount < 0

    def require_non_negative(self) -> Money:
        if self.is_negative:
            raise ValueError("monetary amount must not be negative")

        return self

    def require_positive(self) -> Money:
        if not self.is_positive:
            raise ValueError("monetary amount must be greater than zero")

        return self

    def canonical_amount(self) -> str:
        return format(self.amount, f".{self.currency.minor_units}f")

    def canonical(self) -> str:
        return f"{self.currency.code} {self.canonical_amount()}"

    def canonical_dict(self) -> Mapping[str, str]:
        return MappingProxyType(
            {
                "amount": self.canonical_amount(),
                "currency": self.currency.code,
            }
        )

    def _require_same_currency(self, other: object) -> Money:
        if not isinstance(other, Money):
            raise TypeError("money operation requires another Money value")

        if self.currency != other.currency:
            raise ValueError(
                "money operation requires matching currencies"
            )

        return other

    def __add__(self, other: object) -> Money:
        validated = self._require_same_currency(other)

        return Money(
            amount=self.amount + validated.amount,
            currency=self.currency,
        )

    def __sub__(self, other: object) -> Money:
        validated = self._require_same_currency(other)

        return Money(
            amount=self.amount - validated.amount,
            currency=self.currency,
        )

    def __neg__(self) -> Money:
        return Money(
            amount=-self.amount,
            currency=self.currency,
        )

    def multiply(self, multiplier: object) -> Money:
        factor = _decimal_from_value(multiplier)

        return Money(
            amount=self.amount * factor,
            currency=self.currency,
        )

    def compare(self, other: object) -> int:
        validated = self._require_same_currency(other)

        if self.amount < validated.amount:
            return -1

        if self.amount > validated.amount:
            return 1

        return 0

    def __str__(self) -> str:
        return self.canonical()


def freeze_money_payload(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Return a defensive immutable copy of monetary metadata."""

    if not isinstance(value, Mapping):
        raise TypeError("money payload must be a mapping")

    return MappingProxyType(dict(value))


__all__ = [
    "Currency",
    "DEFAULT_MINOR_UNITS",
    "Money",
    "freeze_money_payload",
]
