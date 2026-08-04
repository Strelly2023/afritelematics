from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Self

from .money import Money
from .transfer import (
    TransferAccountReference,
    TransferPartyReference,
)


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
)

_REFERENCE_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}$"
)

_METADATA_KEY_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]{0,63}$"
)

_SENSITIVE_METADATA_FRAGMENTS = (
    "access_token",
    "api_key",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "cvv",
    "password",
    "pin",
    "private_key",
    "refresh_token",
    "secret",
    "security_code",
    "session_token",
    "token",
)


def _normalize_required_text(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    normalized = " ".join(value.strip().split())

    if not normalized:
        raise ValueError(
            f"{field_name} is required"
        )

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

    if not _IDENTIFIER_PATTERN.fullmatch(
        normalized
    ):
        raise ValueError(
            f"{field_name} contains invalid characters"
        )

    return normalized


def _normalize_reference(
    value: object,
    *,
    field_name: str,
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=192,
    )

    if not _REFERENCE_PATTERN.fullmatch(
        normalized
    ):
        raise ValueError(
            f"{field_name} contains invalid characters"
        )

    return normalized


def _normalize_aware_datetime(
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


def _normalize_version(
    value: object,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "remittance version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "remittance version must be greater than 0"
        )

    return value


def _money_currency_code(
    value: Money,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, Money):
        raise TypeError(
            f"{field_name} must be Money"
        )

    currency_value = getattr(value, "currency", None)

    if currency_value is None:
        raise ValueError(
            f"{field_name} must expose currency"
        )

    code = getattr(currency_value, "code", currency_value)

    if not isinstance(code, str):
        raise ValueError(
            f"{field_name} currency must expose a code"
        )

    normalized = code.strip().upper()

    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError(
            f"{field_name} currency code must be ISO-4217"
        )

    return normalized


def _money_amount_decimal(
    value: Money,
    *,
    field_name: str,
) -> Decimal:
    if not isinstance(value, Money):
        raise TypeError(
            f"{field_name} must be Money"
        )

    amount = getattr(value, "amount", None)

    if amount is None:
        payload_method = getattr(
            value,
            "canonical_dict",
            None,
        )

        if callable(payload_method):
            payload = payload_method()

            if isinstance(payload, Mapping):
                amount = payload.get("amount")

    try:
        normalized = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must expose a decimal amount"
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
) -> Decimal:
    amount = _money_amount_decimal(
        value,
        field_name=field_name,
    )

    if amount < 0:
        raise ValueError(
            f"{field_name} must not be negative"
        )

    return amount


def _require_positive_money(
    value: Money,
    *,
    field_name: str,
) -> Decimal:
    amount = _money_amount_decimal(
        value,
        field_name=field_name,
    )

    if amount <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero"
        )

    return amount


def _money_canonical_dict(
    value: Money,
) -> Mapping[str, Any]:
    if not isinstance(value, Money):
        raise TypeError(
            "remittance amount must be Money"
        )

    canonical = getattr(value, "canonical_dict", None)

    if callable(canonical):
        payload = canonical()

        if not isinstance(payload, Mapping):
            raise TypeError(
                "Money canonical_dict must return a mapping"
            )

        return dict(payload)

    amount = getattr(value, "amount", None)

    return {
        "amount": str(amount),
        "currency": _money_currency_code(
            value,
            field_name="remittance amount",
        ),
    }


def _normalize_country_code(
    value: object,
    *,
    field_name: str,
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=2,
    ).upper()

    if len(normalized) != 2 or not normalized.isalpha():
        raise ValueError(
            f"{field_name} must be an ISO-3166 alpha-2 code"
        )

    return normalized


def _normalize_currency_code(
    value: object,
    *,
    field_name: str,
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=3,
    ).upper()

    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError(
            f"{field_name} must be an ISO-4217 code"
        )

    return normalized


def _normalize_optional_reference(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    return _normalize_reference(
        value,
        field_name=field_name,
    )


def _normalize_metadata_key(
    value: object,
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name="remittance metadata key",
        maximum_length=64,
    )

    normalized = (
        normalized
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if not _METADATA_KEY_PATTERN.fullmatch(
        normalized
    ):
        raise ValueError(
            "remittance metadata key contains "
            "invalid characters"
        )

    for fragment in _SENSITIVE_METADATA_FRAGMENTS:
        if fragment in normalized:
            raise ValueError(
                "remittance metadata contains "
                f"prohibited sensitive key: {normalized}"
            )

    return normalized


def _normalize_metadata_value(
    value: object,
    *,
    depth: int = 0,
) -> Any:
    if depth > 8:
        raise ValueError(
            "remittance metadata nesting is too deep"
        )

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float, str)):
        return value

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}

        for raw_key, raw_value in value.items():
            key = _normalize_metadata_key(raw_key)

            if key in normalized:
                raise ValueError(
                    "duplicate normalized remittance "
                    f"metadata key: {key}"
                )

            normalized[key] = _normalize_metadata_value(
                raw_value,
                depth=depth + 1,
            )

        return MappingProxyType(normalized)

    if isinstance(value, (list, tuple)):
        return tuple(
            _normalize_metadata_value(
                item,
                depth=depth + 1,
            )
            for item in value
        )

    raise TypeError(
        "remittance metadata values must be "
        "JSON-compatible"
    )


class _NormalizedEnum(str, Enum):
    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                f"{cls.__name__} must be a string"
            )

        normalized = (
            value
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        aliases = _ENUM_ALIASES.get(
            cls.__name__,
            {},
        )

        normalized = aliases.get(
            normalized,
            normalized,
        )

        try:
            return cls(normalized)
        except ValueError as exc:
            allowed = ", ".join(
                item.value
                for item in cls
            )

            raise ValueError(
                f"invalid {cls.__name__}: {value!r}; "
                f"expected one of: {allowed}"
            ) from exc


_ENUM_ALIASES: dict[str, dict[str, str]] = {
    "RemittanceStatus": {
        "in_progress": "processing",
        "complete": "completed",
        "canceled": "cancelled",
    },
    "RemittanceType": {
        "international_transfer": "international",
        "domestic_transfer": "domestic",
        "cross_border": "international",
    },
    "RemittanceDirection": {
        "send": "outbound",
        "sent": "outbound",
        "receive": "inbound",
        "received": "inbound",
    },
    "RemittancePurpose": {
        "family": "family_support",
        "education_fee": "education",
        "medical": "healthcare",
        "business": "business_payment",
    },
    "RemittancePriority": {
        "standard": "normal",
        "express": "urgent",
    },
}


class RemittanceStatus(_NormalizedEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    AUTHORIZED = "authorized"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REVERSED = "reversed"


class RemittanceType(_NormalizedEnum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"
    CASH_PICKUP = "cash_pickup"
    BANK_DEPOSIT = "bank_deposit"
    MOBILE_WALLET = "mobile_wallet"
    CARD_TO_CARD = "card_to_card"
    WALLET_TO_WALLET = "wallet_to_wallet"


class RemittanceDirection(_NormalizedEnum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class RemittancePurpose(_NormalizedEnum):
    FAMILY_SUPPORT = "family_support"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    BUSINESS_PAYMENT = "business_payment"
    GOODS_AND_SERVICES = "goods_and_services"
    SAVINGS = "savings"
    EMERGENCY = "emergency"
    CHARITABLE = "charitable"
    OTHER = "other"


class RemittancePriority(_NormalizedEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(frozen=True, slots=True, order=True)
class RemittanceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="remittance id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="remittance id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class RemittanceReference:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_reference(
                self.value,
                field_name="remittance reference",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_reference(
                value,
                field_name="remittance reference",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RemittanceMetadata:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError(
                "remittance metadata must be a mapping"
            )

        normalized: dict[str, Any] = {}

        for raw_key, raw_value in self.values.items():
            key = _normalize_metadata_key(raw_key)

            if key in normalized:
                raise ValueError(
                    "duplicate normalized remittance "
                    f"metadata key: {key}"
                )

            normalized[key] = _normalize_metadata_value(
                raw_value,
                depth=1,
            )

        object.__setattr__(
            self,
            "values",
            MappingProxyType(normalized),
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
                "remittance metadata must be a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> Mapping[str, Any]:
        return self.values



class RemittanceFeeType(_NormalizedEnum):
    SERVICE = "service"
    TRANSFER = "transfer"
    PROVIDER = "provider"
    NETWORK = "network"
    COMPLIANCE = "compliance"
    FUNDING = "funding"
    DELIVERY = "delivery"
    FX_MARGIN = "fx_margin"
    TAX = "tax"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class RemittanceFee:
    fee_type: RemittanceFeeType
    amount: Money
    description: str | None = None
    refundable: bool = False

    def __post_init__(self) -> None:
        normalized_type = RemittanceFeeType.parse(
            self.fee_type
        )

        _require_non_negative_money(
            self.amount,
            field_name="remittance fee amount",
        )

        normalized_description = None

        if self.description is not None:
            normalized_description = _normalize_required_text(
                self.description,
                field_name="remittance fee description",
                maximum_length=256,
            )

        if not isinstance(self.refundable, bool):
            raise TypeError(
                "remittance fee refundable must be boolean"
            )

        object.__setattr__(
            self,
            "fee_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "description",
            normalized_description,
        )

    @classmethod
    def create(
        cls,
        *,
        fee_type: object,
        amount: Money,
        description: object = None,
        refundable: bool = False,
    ) -> Self:
        return cls(
            fee_type=RemittanceFeeType.parse(fee_type),
            amount=amount,
            description=(
                None
                if description is None
                else _normalize_required_text(
                    description,
                    field_name="remittance fee description",
                    maximum_length=256,
                )
            ),
            refundable=refundable,
        )

    @property
    def currency_code(self) -> str:
        return _money_currency_code(
            self.amount,
            field_name="remittance fee amount",
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "fee_type": self.fee_type.value,
            "amount": dict(
                _money_canonical_dict(self.amount)
            ),
            "description": self.description,
            "refundable": self.refundable,
        }


@dataclass(frozen=True, slots=True)
class RemittanceCharge:
    charge_id: str
    charge_type: str
    amount: Money
    description: str | None = None

    def __post_init__(self) -> None:
        normalized_id = _normalize_identifier(
            self.charge_id,
            field_name="remittance charge id",
        )

        normalized_type = (
            _normalize_required_text(
                self.charge_type,
                field_name="remittance charge type",
                maximum_length=64,
            )
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        _require_non_negative_money(
            self.amount,
            field_name="remittance charge amount",
        )

        normalized_description = None

        if self.description is not None:
            normalized_description = _normalize_required_text(
                self.description,
                field_name="remittance charge description",
                maximum_length=256,
            )

        object.__setattr__(
            self,
            "charge_id",
            normalized_id,
        )
        object.__setattr__(
            self,
            "charge_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "description",
            normalized_description,
        )

    @classmethod
    def create(
        cls,
        *,
        charge_id: object,
        charge_type: object,
        amount: Money,
        description: object = None,
    ) -> Self:
        return cls(
            charge_id=_normalize_identifier(
                charge_id,
                field_name="remittance charge id",
            ),
            charge_type=_normalize_required_text(
                charge_type,
                field_name="remittance charge type",
                maximum_length=64,
            ),
            amount=amount,
            description=(
                None
                if description is None
                else _normalize_required_text(
                    description,
                    field_name="remittance charge description",
                    maximum_length=256,
                )
            ),
        )

    @property
    def currency_code(self) -> str:
        return _money_currency_code(
            self.amount,
            field_name="remittance charge amount",
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "charge_id": self.charge_id,
            "charge_type": self.charge_type,
            "amount": dict(
                _money_canonical_dict(self.amount)
            ),
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class RemittancePricingMetadata:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        normalized = RemittanceMetadata.of(
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

        if isinstance(value, RemittanceMetadata):
            return cls(value.values)

        if not isinstance(value, Mapping):
            raise TypeError(
                "remittance pricing metadata must be a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> Mapping[str, Any]:
        return self.values


@dataclass(frozen=True, slots=True)
class RemittanceAmountBreakdown:
    principal_amount: Money
    fees: tuple[RemittanceFee, ...]
    charges: tuple[RemittanceCharge, ...]
    fx_cost: Money
    total_debit_amount: Money
    destination_amount: Money
    metadata: RemittancePricingMetadata

    def __post_init__(self) -> None:
        principal_value = _require_positive_money(
            self.principal_amount,
            field_name="remittance principal amount",
        )

        if not isinstance(self.fees, tuple):
            object.__setattr__(
                self,
                "fees",
                tuple(self.fees),
            )

        if not isinstance(self.charges, tuple):
            object.__setattr__(
                self,
                "charges",
                tuple(self.charges),
            )

        for fee in self.fees:
            if not isinstance(fee, RemittanceFee):
                raise TypeError(
                    "remittance fees must contain "
                    "RemittanceFee values"
                )

        for charge in self.charges:
            if not isinstance(charge, RemittanceCharge):
                raise TypeError(
                    "remittance charges must contain "
                    "RemittanceCharge values"
                )

        source_currency = _money_currency_code(
            self.principal_amount,
            field_name="remittance principal amount",
        )

        fee_total = Decimal("0")

        for fee in self.fees:
            if fee.currency_code != source_currency:
                raise ValueError(
                    "remittance fee currency must match "
                    "principal currency"
                )

            fee_total += _money_amount_decimal(
                fee.amount,
                field_name="remittance fee amount",
            )

        charge_total = Decimal("0")

        for charge in self.charges:
            if charge.currency_code != source_currency:
                raise ValueError(
                    "remittance charge currency must match "
                    "principal currency"
                )

            charge_total += _money_amount_decimal(
                charge.amount,
                field_name="remittance charge amount",
            )

        if (
            _money_currency_code(
                self.fx_cost,
                field_name="remittance FX cost",
            )
            != source_currency
        ):
            raise ValueError(
                "remittance FX cost currency must match "
                "principal currency"
            )

        fx_cost_value = _require_non_negative_money(
            self.fx_cost,
            field_name="remittance FX cost",
        )

        if (
            _money_currency_code(
                self.total_debit_amount,
                field_name="remittance total debit amount",
            )
            != source_currency
        ):
            raise ValueError(
                "remittance total debit currency must match "
                "principal currency"
            )

        total_debit_value = _require_positive_money(
            self.total_debit_amount,
            field_name="remittance total debit amount",
        )

        expected_total = (
            principal_value
            + fee_total
            + charge_total
            + fx_cost_value
        )

        if total_debit_value != expected_total:
            raise ValueError(
                "remittance total debit amount must equal "
                "principal plus fees, charges, and FX cost"
            )

        _require_positive_money(
            self.destination_amount,
            field_name="remittance destination amount",
        )

        object.__setattr__(
            self,
            "metadata",
            RemittancePricingMetadata.of(
                self.metadata
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        principal_amount: Money,
        fees: (
            tuple[RemittanceFee, ...]
            | list[RemittanceFee]
        ) = (),
        charges: (
            tuple[RemittanceCharge, ...]
            | list[RemittanceCharge]
        ) = (),
        fx_cost: Money,
        total_debit_amount: Money,
        destination_amount: Money,
        metadata: object = None,
    ) -> Self:
        return cls(
            principal_amount=principal_amount,
            fees=tuple(fees),
            charges=tuple(charges),
            fx_cost=fx_cost,
            total_debit_amount=total_debit_amount,
            destination_amount=destination_amount,
            metadata=RemittancePricingMetadata.of(
                metadata
            ),
        )

    @property
    def source_currency_code(self) -> str:
        return _money_currency_code(
            self.principal_amount,
            field_name="remittance principal amount",
        )

    @property
    def destination_currency_code(self) -> str:
        return _money_currency_code(
            self.destination_amount,
            field_name="remittance destination amount",
        )

    @property
    def fee_total(self) -> Decimal:
        return sum(
            (
                _money_amount_decimal(
                    fee.amount,
                    field_name="remittance fee amount",
                )
                for fee in self.fees
            ),
            Decimal("0"),
        )

    @property
    def charge_total(self) -> Decimal:
        return sum(
            (
                _money_amount_decimal(
                    charge.amount,
                    field_name="remittance charge amount",
                )
                for charge in self.charges
            ),
            Decimal("0"),
        )

    @property
    def fx_cost_total(self) -> Decimal:
        return _money_amount_decimal(
            self.fx_cost,
            field_name="remittance FX cost",
        )

    @property
    def is_cross_currency(self) -> bool:
        return (
            self.source_currency_code
            != self.destination_currency_code
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "principal_amount": dict(
                _money_canonical_dict(
                    self.principal_amount
                )
            ),
            "fees": [
                fee.canonical_dict()
                for fee in self.fees
            ],
            "charges": [
                charge.canonical_dict()
                for charge in self.charges
            ],
            "fx_cost": dict(
                _money_canonical_dict(
                    self.fx_cost
                )
            ),
            "total_debit_amount": dict(
                _money_canonical_dict(
                    self.total_debit_amount
                )
            ),
            "destination_amount": dict(
                _money_canonical_dict(
                    self.destination_amount
                )
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True, order=True)
class RemittanceInstructionId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="remittance instruction id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="remittance instruction id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RemittanceFundingReference:
    funding_source_id: str
    funding_source_type: str
    account_reference: TransferAccountReference
    authorization_reference: str | None = None

    def __post_init__(self) -> None:
        normalized_id = _normalize_identifier(
            self.funding_source_id,
            field_name="remittance funding source id",
        )

        normalized_type = (
            _normalize_required_text(
                self.funding_source_type,
                field_name="remittance funding source type",
                maximum_length=64,
            )
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not isinstance(
            self.account_reference,
            TransferAccountReference,
        ):
            raise TypeError(
                "remittance funding account reference must be "
                "TransferAccountReference"
            )

        normalized_authorization_reference = (
            _normalize_optional_reference(
                self.authorization_reference,
                field_name=(
                    "remittance funding authorization reference"
                ),
            )
        )

        object.__setattr__(
            self,
            "funding_source_id",
            normalized_id,
        )
        object.__setattr__(
            self,
            "funding_source_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "authorization_reference",
            normalized_authorization_reference,
        )

    @classmethod
    def create(
        cls,
        *,
        funding_source_id: object,
        funding_source_type: object,
        account_reference: TransferAccountReference,
        authorization_reference: object = None,
    ) -> Self:
        return cls(
            funding_source_id=_normalize_identifier(
                funding_source_id,
                field_name="remittance funding source id",
            ),
            funding_source_type=_normalize_required_text(
                funding_source_type,
                field_name="remittance funding source type",
                maximum_length=64,
            ),
            account_reference=account_reference,
            authorization_reference=(
                _normalize_optional_reference(
                    authorization_reference,
                    field_name=(
                        "remittance funding "
                        "authorization reference"
                    ),
                )
            ),
        )

    @property
    def currency_code(self) -> str | None:
        value = getattr(
            self.account_reference,
            "currency_code",
            None,
        )

        if value is None:
            return None

        return _normalize_currency_code(
            value,
            field_name="remittance funding currency",
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "funding_source_id": self.funding_source_id,
            "funding_source_type": self.funding_source_type,
            "account_reference": dict(
                self.account_reference.canonical_dict()
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
        }


@dataclass(frozen=True, slots=True)
class RemittanceRecipientReference:
    recipient_id: str
    recipient_type: str
    party_reference: TransferPartyReference
    account_reference: TransferAccountReference
    delivery_method: str
    routing_reference: str | None = None

    def __post_init__(self) -> None:
        normalized_id = _normalize_identifier(
            self.recipient_id,
            field_name="remittance recipient id",
        )

        normalized_type = (
            _normalize_required_text(
                self.recipient_type,
                field_name="remittance recipient type",
                maximum_length=64,
            )
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not isinstance(
            self.party_reference,
            TransferPartyReference,
        ):
            raise TypeError(
                "remittance recipient party reference must be "
                "TransferPartyReference"
            )

        if not isinstance(
            self.account_reference,
            TransferAccountReference,
        ):
            raise TypeError(
                "remittance recipient account reference must be "
                "TransferAccountReference"
            )

        normalized_delivery_method = (
            _normalize_required_text(
                self.delivery_method,
                field_name="remittance delivery method",
                maximum_length=64,
            )
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        normalized_routing_reference = (
            _normalize_optional_reference(
                self.routing_reference,
                field_name="remittance routing reference",
            )
        )

        object.__setattr__(
            self,
            "recipient_id",
            normalized_id,
        )
        object.__setattr__(
            self,
            "recipient_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "delivery_method",
            normalized_delivery_method,
        )
        object.__setattr__(
            self,
            "routing_reference",
            normalized_routing_reference,
        )

    @classmethod
    def create(
        cls,
        *,
        recipient_id: object,
        recipient_type: object,
        party_reference: TransferPartyReference,
        account_reference: TransferAccountReference,
        delivery_method: object,
        routing_reference: object = None,
    ) -> Self:
        return cls(
            recipient_id=_normalize_identifier(
                recipient_id,
                field_name="remittance recipient id",
            ),
            recipient_type=_normalize_required_text(
                recipient_type,
                field_name="remittance recipient type",
                maximum_length=64,
            ),
            party_reference=party_reference,
            account_reference=account_reference,
            delivery_method=_normalize_required_text(
                delivery_method,
                field_name="remittance delivery method",
                maximum_length=64,
            ),
            routing_reference=(
                _normalize_optional_reference(
                    routing_reference,
                    field_name="remittance routing reference",
                )
            ),
        )

    @property
    def currency_code(self) -> str | None:
        value = getattr(
            self.account_reference,
            "currency_code",
            None,
        )

        if value is None:
            return None

        return _normalize_currency_code(
            value,
            field_name="remittance recipient currency",
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "recipient_id": self.recipient_id,
            "recipient_type": self.recipient_type,
            "party_reference": dict(
                self.party_reference.canonical_dict()
            ),
            "account_reference": dict(
                self.account_reference.canonical_dict()
            ),
            "delivery_method": self.delivery_method,
            "routing_reference": self.routing_reference,
        }


@dataclass(frozen=True, slots=True)
class RemittanceCorridor:
    source_country_code: str
    destination_country_code: str
    source_currency_code: str
    destination_currency_code: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_country_code",
            _normalize_country_code(
                self.source_country_code,
                field_name="remittance source country code",
            ),
        )
        object.__setattr__(
            self,
            "destination_country_code",
            _normalize_country_code(
                self.destination_country_code,
                field_name=(
                    "remittance destination country code"
                ),
            ),
        )
        object.__setattr__(
            self,
            "source_currency_code",
            _normalize_currency_code(
                self.source_currency_code,
                field_name="remittance source currency code",
            ),
        )
        object.__setattr__(
            self,
            "destination_currency_code",
            _normalize_currency_code(
                self.destination_currency_code,
                field_name=(
                    "remittance destination currency code"
                ),
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        source_country_code: object,
        destination_country_code: object,
        source_currency_code: object,
        destination_currency_code: object,
    ) -> Self:
        return cls(
            source_country_code=_normalize_country_code(
                source_country_code,
                field_name="remittance source country code",
            ),
            destination_country_code=(
                _normalize_country_code(
                    destination_country_code,
                    field_name=(
                        "remittance destination country code"
                    ),
                )
            ),
            source_currency_code=_normalize_currency_code(
                source_currency_code,
                field_name="remittance source currency code",
            ),
            destination_currency_code=(
                _normalize_currency_code(
                    destination_currency_code,
                    field_name=(
                        "remittance destination currency code"
                    ),
                )
            ),
        )

    @property
    def is_cross_border(self) -> bool:
        return (
            self.source_country_code
            != self.destination_country_code
        )

    @property
    def is_cross_currency(self) -> bool:
        return (
            self.source_currency_code
            != self.destination_currency_code
        )

    @property
    def code(self) -> str:
        return (
            f"{self.source_country_code}-"
            f"{self.destination_country_code}"
        )

    def canonical_dict(self) -> dict[str, str]:
        return {
            "source_country_code": self.source_country_code,
            "destination_country_code": (
                self.destination_country_code
            ),
            "source_currency_code": self.source_currency_code,
            "destination_currency_code": (
                self.destination_currency_code
            ),
        }


@dataclass(frozen=True, slots=True)
class RemittanceInstructionMetadata:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        normalized = RemittanceMetadata.of(
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

        if isinstance(value, RemittanceMetadata):
            return cls(value.values)

        if not isinstance(value, Mapping):
            raise TypeError(
                "remittance instruction metadata must be "
                "a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> Mapping[str, Any]:
        return self.values


@dataclass(frozen=True, slots=True)
class RemittanceInstruction:
    instruction_id: RemittanceInstructionId
    remittance_id: RemittanceId
    funding_reference: RemittanceFundingReference
    recipient_reference: RemittanceRecipientReference
    corridor: RemittanceCorridor
    requested_source_amount: Money
    expected_destination_amount: Money
    requested_at: datetime
    expires_at: datetime | None
    metadata: RemittanceInstructionMetadata
    version: int

    def __post_init__(self) -> None:
        normalized_instruction_id = (
            RemittanceInstructionId.of(
                self.instruction_id
            )
        )
        normalized_remittance_id = RemittanceId.of(
            self.remittance_id
        )

        if not isinstance(
            self.funding_reference,
            RemittanceFundingReference,
        ):
            raise TypeError(
                "remittance instruction funding reference "
                "must be RemittanceFundingReference"
            )

        if not isinstance(
            self.recipient_reference,
            RemittanceRecipientReference,
        ):
            raise TypeError(
                "remittance instruction recipient reference "
                "must be RemittanceRecipientReference"
            )

        if not isinstance(
            self.corridor,
            RemittanceCorridor,
        ):
            raise TypeError(
                "remittance instruction corridor must be "
                "RemittanceCorridor"
            )

        source_currency = _money_currency_code(
            self.requested_source_amount,
            field_name=(
                "remittance instruction requested source amount"
            ),
        )
        destination_currency = _money_currency_code(
            self.expected_destination_amount,
            field_name=(
                "remittance instruction expected "
                "destination amount"
            ),
        )

        if source_currency != self.corridor.source_currency_code:
            raise ValueError(
                "remittance instruction source amount currency "
                "must match corridor source currency"
            )

        if (
            destination_currency
            != self.corridor.destination_currency_code
        ):
            raise ValueError(
                "remittance instruction destination amount "
                "currency must match corridor destination currency"
            )

        funding_currency = (
            self.funding_reference.currency_code
        )

        if (
            funding_currency is not None
            and funding_currency != source_currency
        ):
            raise ValueError(
                "remittance instruction funding currency must "
                "match requested source amount currency"
            )

        recipient_currency = (
            self.recipient_reference.currency_code
        )

        if (
            recipient_currency is not None
            and recipient_currency != destination_currency
        ):
            raise ValueError(
                "remittance instruction recipient currency must "
                "match expected destination amount currency"
            )

        normalized_requested_at = _normalize_aware_datetime(
            self.requested_at,
            field_name="remittance instruction requested_at",
        )

        normalized_expires_at = None

        if self.expires_at is not None:
            normalized_expires_at = (
                _normalize_aware_datetime(
                    self.expires_at,
                    field_name=(
                        "remittance instruction expires_at"
                    ),
                )
            )

            if normalized_expires_at <= normalized_requested_at:
                raise ValueError(
                    "remittance instruction expires_at must be "
                    "later than requested_at"
                )

        object.__setattr__(
            self,
            "instruction_id",
            normalized_instruction_id,
        )
        object.__setattr__(
            self,
            "remittance_id",
            normalized_remittance_id,
        )
        object.__setattr__(
            self,
            "requested_at",
            normalized_requested_at,
        )
        object.__setattr__(
            self,
            "expires_at",
            normalized_expires_at,
        )
        object.__setattr__(
            self,
            "metadata",
            RemittanceInstructionMetadata.of(
                self.metadata
            ),
        )
        object.__setattr__(
            self,
            "version",
            _normalize_version(self.version),
        )

    @classmethod
    def create(
        cls,
        *,
        instruction_id: object,
        remittance_id: object,
        funding_reference: RemittanceFundingReference,
        recipient_reference: RemittanceRecipientReference,
        corridor: RemittanceCorridor,
        requested_source_amount: Money,
        expected_destination_amount: Money,
        requested_at: datetime,
        expires_at: datetime | None = None,
        metadata: object = None,
        version: int = 1,
    ) -> Self:
        return cls(
            instruction_id=RemittanceInstructionId.of(
                instruction_id
            ),
            remittance_id=RemittanceId.of(
                remittance_id
            ),
            funding_reference=funding_reference,
            recipient_reference=recipient_reference,
            corridor=corridor,
            requested_source_amount=requested_source_amount,
            expected_destination_amount=(
                expected_destination_amount
            ),
            requested_at=_normalize_aware_datetime(
                requested_at,
                field_name=(
                    "remittance instruction requested_at"
                ),
            ),
            expires_at=(
                None
                if expires_at is None
                else _normalize_aware_datetime(
                    expires_at,
                    field_name=(
                        "remittance instruction expires_at"
                    ),
                )
            ),
            metadata=RemittanceInstructionMetadata.of(
                metadata
            ),
            version=version,
        )

    @property
    def source_currency_code(self) -> str:
        return _money_currency_code(
            self.requested_source_amount,
            field_name=(
                "remittance instruction requested source amount"
            ),
        )

    @property
    def destination_currency_code(self) -> str:
        return _money_currency_code(
            self.expected_destination_amount,
            field_name=(
                "remittance instruction expected "
                "destination amount"
            ),
        )

    @property
    def is_cross_border(self) -> bool:
        return self.corridor.is_cross_border

    @property
    def is_cross_currency(self) -> bool:
        return self.corridor.is_cross_currency

    def is_expired(
        self,
        *,
        at: datetime,
    ) -> bool:
        normalized_at = _normalize_aware_datetime(
            at,
            field_name="remittance instruction expiry check",
        )

        if self.expires_at is None:
            return False

        return normalized_at >= self.expires_at

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "instruction_id": self.instruction_id.value,
            "remittance_id": self.remittance_id.value,
            "funding_reference": (
                self.funding_reference.canonical_dict()
            ),
            "recipient_reference": (
                self.recipient_reference.canonical_dict()
            ),
            "corridor": self.corridor.canonical_dict(),
            "requested_source_amount": dict(
                _money_canonical_dict(
                    self.requested_source_amount
                )
            ),
            "expected_destination_amount": dict(
                _money_canonical_dict(
                    self.expected_destination_amount
                )
            ),
            "requested_at": self.requested_at.isoformat(),
            "expires_at": (
                None
                if self.expires_at is None
                else self.expires_at.isoformat()
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class Remittance:
    remittance_id: RemittanceId
    reference: RemittanceReference
    status: RemittanceStatus
    remittance_type: RemittanceType
    direction: RemittanceDirection
    purpose: RemittancePurpose
    priority: RemittancePriority
    sender: TransferPartyReference
    beneficiary: TransferPartyReference
    source_account: TransferAccountReference
    destination_account: TransferAccountReference
    source_amount: Money
    destination_amount: Money
    metadata: RemittanceMetadata
    created_at: datetime
    updated_at: datetime
    version: int

    def __post_init__(self) -> None:
        normalized_id = RemittanceId.of(
            self.remittance_id
        )
        normalized_reference = RemittanceReference.of(
            self.reference
        )
        normalized_status = RemittanceStatus.parse(
            self.status
        )
        normalized_type = RemittanceType.parse(
            self.remittance_type
        )
        normalized_direction = RemittanceDirection.parse(
            self.direction
        )
        normalized_purpose = RemittancePurpose.parse(
            self.purpose
        )
        normalized_priority = RemittancePriority.parse(
            self.priority
        )

        if not isinstance(
            self.sender,
            TransferPartyReference,
        ):
            raise TypeError(
                "remittance sender must be "
                "TransferPartyReference"
            )

        if not isinstance(
            self.beneficiary,
            TransferPartyReference,
        ):
            raise TypeError(
                "remittance beneficiary must be "
                "TransferPartyReference"
            )

        if self.sender == self.beneficiary:
            raise ValueError(
                "remittance sender and beneficiary "
                "must be different"
            )

        if not isinstance(
            self.source_account,
            TransferAccountReference,
        ):
            raise TypeError(
                "remittance source account must be "
                "TransferAccountReference"
            )

        if not isinstance(
            self.destination_account,
            TransferAccountReference,
        ):
            raise TypeError(
                "remittance destination account must be "
                "TransferAccountReference"
            )

        if self.source_account == self.destination_account:
            raise ValueError(
                "remittance source and destination accounts "
                "must be different"
            )

        source_currency = _money_currency_code(
            self.source_amount,
            field_name="remittance source amount",
        )
        destination_currency = _money_currency_code(
            self.destination_amount,
            field_name="remittance destination amount",
        )

        source_account_currency = getattr(
            self.source_account,
            "currency_code",
            None,
        )
        destination_account_currency = getattr(
            self.destination_account,
            "currency_code",
            None,
        )

        if (
            source_account_currency is not None
            and str(source_account_currency).upper()
            != source_currency
        ):
            raise ValueError(
                "remittance source amount currency must match "
                "source account currency"
            )

        if (
            destination_account_currency is not None
            and str(destination_account_currency).upper()
            != destination_currency
        ):
            raise ValueError(
                "remittance destination amount currency must "
                "match destination account currency"
            )

        normalized_created_at = _normalize_aware_datetime(
            self.created_at,
            field_name="remittance created_at",
        )
        normalized_updated_at = _normalize_aware_datetime(
            self.updated_at,
            field_name="remittance updated_at",
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "remittance updated_at must not be earlier "
                "than created_at"
            )

        normalized_version = _normalize_version(
            self.version
        )

        object.__setattr__(
            self,
            "remittance_id",
            normalized_id,
        )
        object.__setattr__(
            self,
            "reference",
            normalized_reference,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "remittance_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "direction",
            normalized_direction,
        )
        object.__setattr__(
            self,
            "purpose",
            normalized_purpose,
        )
        object.__setattr__(
            self,
            "priority",
            normalized_priority,
        )
        object.__setattr__(
            self,
            "metadata",
            RemittanceMetadata.of(
                self.metadata
            ),
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
        remittance_id: object,
        reference: object,
        status: object = RemittanceStatus.DRAFT,
        remittance_type: object,
        direction: object,
        purpose: object,
        priority: object = RemittancePriority.NORMAL,
        sender: TransferPartyReference,
        beneficiary: TransferPartyReference,
        source_account: TransferAccountReference,
        destination_account: TransferAccountReference,
        source_amount: Money,
        destination_amount: Money,
        metadata: object = None,
        created_at: datetime,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> Self:
        normalized_created_at = _normalize_aware_datetime(
            created_at,
            field_name="remittance created_at",
        )

        return cls(
            remittance_id=RemittanceId.of(
                remittance_id
            ),
            reference=RemittanceReference.of(
                reference
            ),
            status=RemittanceStatus.parse(
                status
            ),
            remittance_type=RemittanceType.parse(
                remittance_type
            ),
            direction=RemittanceDirection.parse(
                direction
            ),
            purpose=RemittancePurpose.parse(
                purpose
            ),
            priority=RemittancePriority.parse(
                priority
            ),
            sender=sender,
            beneficiary=beneficiary,
            source_account=source_account,
            destination_account=destination_account,
            source_amount=source_amount,
            destination_amount=destination_amount,
            metadata=RemittanceMetadata.of(
                metadata
            ),
            created_at=normalized_created_at,
            updated_at=(
                normalized_created_at
                if updated_at is None
                else _normalize_aware_datetime(
                    updated_at,
                    field_name="remittance updated_at",
                )
            ),
            version=version,
        )

    @property
    def source_currency_code(self) -> str:
        return _money_currency_code(
            self.source_amount,
            field_name="remittance source amount",
        )

    @property
    def destination_currency_code(self) -> str:
        return _money_currency_code(
            self.destination_amount,
            field_name="remittance destination amount",
        )

    @property
    def is_cross_currency(self) -> bool:
        return (
            self.source_currency_code
            != self.destination_currency_code
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            RemittanceStatus.COMPLETED,
            RemittanceStatus.FAILED,
            RemittanceStatus.CANCELLED,
            RemittanceStatus.EXPIRED,
            RemittanceStatus.REVERSED,
        }

    def _with_change(
        self,
        *,
        occurred_at: datetime,
        status: RemittanceStatus | None = None,
        reference: RemittanceReference | None = None,
        priority: RemittancePriority | None = None,
        metadata: RemittanceMetadata | None = None,
    ) -> Self:
        normalized_occurred_at = _normalize_aware_datetime(
            occurred_at,
            field_name="remittance occurred_at",
        )

        if normalized_occurred_at < self.updated_at:
            raise ValueError(
                "remittance occurred_at must not be earlier "
                "than updated_at"
            )

        if self.is_terminal:
            raise ValueError(
                "terminal remittance cannot be updated"
            )

        updated = replace(
            self,
            status=(
                self.status
                if status is None
                else RemittanceStatus.parse(status)
            ),
            reference=(
                self.reference
                if reference is None
                else RemittanceReference.of(reference)
            ),
            priority=(
                self.priority
                if priority is None
                else RemittancePriority.parse(priority)
            ),
            metadata=(
                self.metadata
                if metadata is None
                else RemittanceMetadata.of(metadata)
            ),
            updated_at=normalized_occurred_at,
            version=self.version + 1,
        )

        if updated == self:
            raise ValueError(
                "remittance update must change state"
            )

        return updated

    def _transition_status(
        self,
        *,
        target_status: RemittanceStatus,
        allowed_from: frozenset[RemittanceStatus],
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        normalized_target = RemittanceStatus.parse(
            target_status
        )

        if self.status not in allowed_from:
            allowed = ", ".join(
                sorted(
                    status.value
                    for status in allowed_from
                )
            )

            raise ValueError(
                "invalid remittance transition from "
                f"{self.status.value} to "
                f"{normalized_target.value}; "
                f"allowed source statuses: {allowed}"
            )

        if normalized_target is self.status:
            raise ValueError(
                "remittance transition must change status"
            )

        transition_metadata = (
            self.metadata
            if metadata is None
            else RemittanceMetadata.of(metadata)
        )

        normalized_occurred_at = _normalize_aware_datetime(
            occurred_at,
            field_name="remittance occurred_at",
        )

        if normalized_occurred_at < self.updated_at:
            raise ValueError(
                "remittance occurred_at must not be earlier "
                "than updated_at"
            )

        return replace(
            self,
            status=normalized_target,
            metadata=transition_metadata,
            updated_at=normalized_occurred_at,
            version=self.version + 1,
        )

    def validate(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=RemittanceStatus.VALIDATED,
            allowed_from=frozenset({
                RemittanceStatus.DRAFT,
            }),
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def authorize(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=RemittanceStatus.AUTHORIZED,
            allowed_from=frozenset({
                RemittanceStatus.VALIDATED,
            }),
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def submit(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=RemittanceStatus.SUBMITTED,
            allowed_from=frozenset({
                RemittanceStatus.AUTHORIZED,
            }),
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def mark_processing(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=RemittanceStatus.PROCESSING,
            allowed_from=frozenset({
                RemittanceStatus.SUBMITTED,
            }),
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def complete(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=RemittanceStatus.COMPLETED,
            allowed_from=frozenset({
                RemittanceStatus.PROCESSING,
            }),
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def fail(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=RemittanceStatus.FAILED,
            allowed_from=frozenset({
                RemittanceStatus.SUBMITTED,
                RemittanceStatus.PROCESSING,
            }),
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def cancel(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=RemittanceStatus.CANCELLED,
            allowed_from=frozenset({
                RemittanceStatus.DRAFT,
                RemittanceStatus.VALIDATED,
                RemittanceStatus.AUTHORIZED,
                RemittanceStatus.SUBMITTED,
            }),
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def expire(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target_status=RemittanceStatus.EXPIRED,
            allowed_from=frozenset({
                RemittanceStatus.DRAFT,
                RemittanceStatus.VALIDATED,
                RemittanceStatus.AUTHORIZED,
                RemittanceStatus.SUBMITTED,
            }),
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def reverse(
        self,
        *,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        if self.status is not RemittanceStatus.COMPLETED:
            raise ValueError(
                "only completed remittance can be reversed"
            )

        normalized_occurred_at = _normalize_aware_datetime(
            occurred_at,
            field_name="remittance occurred_at",
        )

        if normalized_occurred_at < self.updated_at:
            raise ValueError(
                "remittance occurred_at must not be earlier "
                "than updated_at"
            )

        return replace(
            self,
            status=RemittanceStatus.REVERSED,
            metadata=(
                self.metadata
                if metadata is None
                else RemittanceMetadata.of(metadata)
            ),
            updated_at=normalized_occurred_at,
            version=self.version + 1,
        )

    def update_reference(
        self,
        *,
        reference: object,
        occurred_at: datetime,
    ) -> Self:
        if self.status is not RemittanceStatus.DRAFT:
            raise ValueError(
                "remittance reference can only be updated "
                "while draft"
            )

        normalized_reference = RemittanceReference.of(
            reference
        )

        if normalized_reference == self.reference:
            raise ValueError(
                "remittance reference update must change value"
            )

        return self._with_change(
            occurred_at=occurred_at,
            reference=normalized_reference,
        )

    def update_priority(
        self,
        *,
        priority: object,
        occurred_at: datetime,
    ) -> Self:
        normalized_priority = RemittancePriority.parse(
            priority
        )

        if normalized_priority is self.priority:
            raise ValueError(
                "remittance priority update must change value"
            )

        return self._with_change(
            occurred_at=occurred_at,
            priority=normalized_priority,
        )

    def update_metadata(
        self,
        *,
        metadata: object,
        occurred_at: datetime,
    ) -> Self:
        normalized_metadata = RemittanceMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "remittance metadata update must change value"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized_metadata,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "remittance_id": self.remittance_id.value,
            "reference": self.reference.value,
            "status": self.status.value,
            "remittance_type": self.remittance_type.value,
            "direction": self.direction.value,
            "purpose": self.purpose.value,
            "priority": self.priority.value,
            "sender": self.sender.canonical_dict(),
            "beneficiary": self.beneficiary.canonical_dict(),
            "source_account": self.source_account.canonical_dict(),
            "destination_account": (
                self.destination_account.canonical_dict()
            ),
            "source_amount": dict(
                _money_canonical_dict(
                    self.source_amount
                )
            ),
            "destination_amount": dict(
                _money_canonical_dict(
                    self.destination_amount
                )
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


__all__ = [
    "Remittance",
    "RemittanceAmountBreakdown",
    "RemittanceCharge",
    "RemittanceCorridor",
    "RemittanceDirection",
    "RemittanceFee",
    "RemittanceFeeType",
    "RemittanceFundingReference",
    "RemittanceId",
    "RemittanceInstruction",
    "RemittanceInstructionId",
    "RemittanceInstructionMetadata",
    "RemittanceMetadata",
    "RemittancePricingMetadata",
    "RemittancePriority",
    "RemittancePurpose",
    "RemittanceRecipientReference",
    "RemittanceReference",
    "RemittanceStatus",
    "RemittanceType",
]