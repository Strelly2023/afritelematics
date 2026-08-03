"""Canonical NovaPay transfer-domain primitives.

This module defines immutable identifiers, classifications, references,
and metadata for the transfer domain.

It deliberately contains no wallet mutation, ledger posting, settlement,
provider-network, exchange-rate acquisition, or persistence authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Self

from afritech.novapay.domain.money import Money


_MAX_IDENTIFIER_LENGTH = 128
_MAX_REFERENCE_LENGTH = 256
_MAX_PARTY_REFERENCE_LENGTH = 256
_MAX_ACCOUNT_REFERENCE_LENGTH = 256
_MAX_METADATA_KEYS = 64
_MAX_METADATA_KEY_LENGTH = 128
_MAX_METADATA_TEXT_LENGTH = 4096

_PROHIBITED_METADATA_KEY_PARTS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "credential",
        "credentials",
        "cvv",
        "password",
        "pin",
        "private_key",
        "secret",
        "security_code",
        "token",
    }
)

_ENUM_ALIASES: Mapping[str, str] = {}


def _normalize_datetime(
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


def _normalize_version(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "transfer version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "transfer version must be greater than 0"
        )

    return value


def _money_amount_decimal(
    value: Money,
    *,
    field_name: str,
) -> Decimal:
    if not isinstance(value, Money):
        raise TypeError(
            f"{field_name} must be Money"
        )

    raw_amount = getattr(value, "amount", None)

    try:
        normalized = Decimal(str(raw_amount))
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
) -> Money:
    amount = _money_amount_decimal(
        value,
        field_name=field_name,
    )

    if amount < Decimal("0"):
        raise ValueError(
            f"{field_name} amount must not be negative"
        )

    _money_currency_code(
        value,
        field_name=field_name,
    )

    return value


def _money_currency_code(
    value: Money,
    *,
    field_name: str,
) -> str:
    currency = getattr(value, "currency", None)

    if currency is None:
        raise ValueError(
            f"{field_name} must expose a currency"
        )

    if isinstance(currency, str):
        code = currency
    else:
        code = getattr(currency, "code", None)

        if code is None:
            code = getattr(currency, "value", None)

    if not isinstance(code, str):
        raise ValueError(
            f"{field_name} currency must expose a code"
        )

    normalized = code.strip().upper()

    if (
        len(normalized) != 3
        or not normalized.isalpha()
    ):
        raise ValueError(
            f"{field_name} currency code must be a "
            "three-letter alphabetic code"
        )

    return normalized


def _money_canonical_dict(
    value: Money,
) -> Mapping[str, Any]:
    canonical_method = getattr(
        value,
        "canonical_dict",
        None,
    )

    if callable(canonical_method):
        payload = canonical_method()

        if isinstance(payload, Mapping):
            return dict(payload)

    amount = getattr(value, "amount", None)
    currency_code = _money_currency_code(
        value,
        field_name="transfer money",
    )

    return {
        "amount": str(amount),
        "currency": currency_code,
    }


def _normalize_required_text(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} is required")

    if len(normalized) > maximum_length:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum_length} characters"
        )

    return normalized


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str | None:
    if value is None:
        return None

    return _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=maximum_length,
    )


def _normalize_metadata_key(value: object) -> str:
    normalized = _normalize_required_text(
        value,
        field_name="transfer metadata key",
        maximum_length=_MAX_METADATA_KEY_LENGTH,
    ).lower()

    normalized = normalized.replace("-", "_").replace(" ", "_")

    if any(
        prohibited in normalized
        for prohibited in _PROHIBITED_METADATA_KEY_PARTS
    ):
        raise ValueError(
            "transfer metadata contains prohibited sensitive key: "
            f"{normalized}"
        )

    return normalized


def _normalize_metadata_value(
    value: object,
    *,
    field_name: str,
) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        return _normalize_required_text(
            value,
            field_name=field_name,
            maximum_length=_MAX_METADATA_TEXT_LENGTH,
        )

    if isinstance(value, tuple):
        return tuple(
            _normalize_metadata_value(
                item,
                field_name=field_name,
            )
            for item in value
        )

    if isinstance(value, list):
        return tuple(
            _normalize_metadata_value(
                item,
                field_name=field_name,
            )
            for item in value
        )

    if isinstance(value, Mapping):
        normalized_mapping: dict[str, Any] = {}

        for raw_key, raw_value in value.items():
            key = _normalize_metadata_key(raw_key)

            if key in normalized_mapping:
                raise ValueError(
                    "transfer metadata contains duplicate "
                    f"normalized key: {key}"
                )

            normalized_mapping[key] = (
                _normalize_metadata_value(
                    raw_value,
                    field_name=(
                        f"{field_name}.{key}"
                    ),
                )
            )

        return MappingProxyType(
            dict(sorted(normalized_mapping.items()))
        )

    raise TypeError(
        f"{field_name} contains unsupported value type: "
        f"{type(value).__name__}"
    )


class _NormalizedEnum(str, Enum):
    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_required_text(
            value,
            field_name=cls.__name__,
            maximum_length=64,
        ).lower()

        normalized = normalized.replace("-", "_").replace(" ", "_")
        normalized = _ENUM_ALIASES.get(normalized, normalized)

        try:
            return cls(normalized)
        except ValueError as exc:
            allowed = ", ".join(
                item.value
                for item in cls
            )

            raise ValueError(
                f"invalid {cls.__name__}: {value!r}; "
                f"allowed values: {allowed}"
            ) from exc


class TransferStatus(_NormalizedEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    AUTHORIZED = "authorized"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    EXPIRED = "expired"


class TransferType(_NormalizedEnum):
    INTERNAL = "internal"
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"
    REMITTANCE = "remittance"
    BUSINESS_PAYMENT = "business_payment"
    MERCHANT_PAYMENT = "merchant_payment"
    PAYOUT = "payout"
    REFUND = "refund"
    REVERSAL = "reversal"


class TransferDirection(_NormalizedEnum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"
    INTERNAL = "internal"


class TransferPurpose(_NormalizedEnum):
    GENERAL = "general"
    FAMILY_SUPPORT = "family_support"
    EDUCATION = "education"
    MEDICAL = "medical"
    GOODS_AND_SERVICES = "goods_and_services"
    SALARY = "salary"
    BUSINESS = "business"
    SAVINGS = "savings"
    EMERGENCY = "emergency"
    CHARITY = "charity"
    GOVERNMENT = "government"
    REFUND = "refund"


class TransferPriority(_NormalizedEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(frozen=True, slots=True, order=True)
class TransferId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="transfer id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name="transfer id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class TransferReference:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="transfer reference",
                maximum_length=_MAX_REFERENCE_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name="transfer reference",
                maximum_length=_MAX_REFERENCE_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class TransferPartyReference:
    party_id: str
    party_type: str
    display_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "party_id",
            _normalize_required_text(
                self.party_id,
                field_name="transfer party id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "party_type",
            _normalize_required_text(
                self.party_type,
                field_name="transfer party type",
                maximum_length=64,
            ).lower().replace("-", "_").replace(" ", "_"),
        )
        object.__setattr__(
            self,
            "display_name",
            _normalize_optional_text(
                self.display_name,
                field_name="transfer party display name",
                maximum_length=_MAX_PARTY_REFERENCE_LENGTH,
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
        *,
        party_type: object | None = None,
        display_name: object | None = None,
    ) -> Self:
        if isinstance(value, cls):
            if party_type is not None or display_name is not None:
                raise ValueError(
                    "party_type and display_name must not be "
                    "provided with TransferPartyReference"
                )

            return value

        if isinstance(value, Mapping):
            return cls(
                party_id=value.get("party_id"),  # type: ignore[arg-type]
                party_type=value.get("party_type"),  # type: ignore[arg-type]
                display_name=value.get("display_name"),  # type: ignore[arg-type]
            )

        if party_type is None:
            raise ValueError(
                "transfer party type is required"
            )

        return cls(
            party_id=_normalize_required_text(
                value,
                field_name="transfer party id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
            party_type=_normalize_required_text(
                party_type,
                field_name="transfer party type",
                maximum_length=64,
            ),
            display_name=_normalize_optional_text(
                display_name,
                field_name="transfer party display name",
                maximum_length=_MAX_PARTY_REFERENCE_LENGTH,
            ),
        )

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "party_id": self.party_id,
            "party_type": self.party_type,
            "display_name": self.display_name,
        }


@dataclass(frozen=True, slots=True, order=True)
class TransferAccountReference:
    account_id: str
    account_type: str
    currency_code: str | None = None
    institution_reference: str | None = None

    def __post_init__(self) -> None:
        normalized_currency = _normalize_optional_text(
            self.currency_code,
            field_name="transfer account currency code",
            maximum_length=3,
        )

        if normalized_currency is not None:
            normalized_currency = normalized_currency.upper()

            if (
                len(normalized_currency) != 3
                or not normalized_currency.isalpha()
            ):
                raise ValueError(
                    "transfer account currency code must be "
                    "a three-letter alphabetic code"
                )

        object.__setattr__(
            self,
            "account_id",
            _normalize_required_text(
                self.account_id,
                field_name="transfer account id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "account_type",
            _normalize_required_text(
                self.account_type,
                field_name="transfer account type",
                maximum_length=64,
            ).lower().replace("-", "_").replace(" ", "_"),
        )
        object.__setattr__(
            self,
            "currency_code",
            normalized_currency,
        )
        object.__setattr__(
            self,
            "institution_reference",
            _normalize_optional_text(
                self.institution_reference,
                field_name=(
                    "transfer account institution reference"
                ),
                maximum_length=_MAX_ACCOUNT_REFERENCE_LENGTH,
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
        *,
        account_type: object | None = None,
        currency_code: object | None = None,
        institution_reference: object | None = None,
    ) -> Self:
        if isinstance(value, cls):
            if any(
                item is not None
                for item in (
                    account_type,
                    currency_code,
                    institution_reference,
                )
            ):
                raise ValueError(
                    "additional fields must not be provided with "
                    "TransferAccountReference"
                )

            return value

        if isinstance(value, Mapping):
            return cls(
                account_id=value.get("account_id"),  # type: ignore[arg-type]
                account_type=value.get("account_type"),  # type: ignore[arg-type]
                currency_code=value.get("currency_code"),  # type: ignore[arg-type]
                institution_reference=value.get(
                    "institution_reference"
                ),  # type: ignore[arg-type]
            )

        if account_type is None:
            raise ValueError(
                "transfer account type is required"
            )

        return cls(
            account_id=_normalize_required_text(
                value,
                field_name="transfer account id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
            account_type=_normalize_required_text(
                account_type,
                field_name="transfer account type",
                maximum_length=64,
            ),
            currency_code=_normalize_optional_text(
                currency_code,
                field_name="transfer account currency code",
                maximum_length=3,
            ),
            institution_reference=_normalize_optional_text(
                institution_reference,
                field_name=(
                    "transfer account institution reference"
                ),
                maximum_length=_MAX_ACCOUNT_REFERENCE_LENGTH,
            ),
        )

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "account_id": self.account_id,
            "account_type": self.account_type,
            "currency_code": self.currency_code,
            "institution_reference": (
                self.institution_reference
            ),
        }


@dataclass(frozen=True, slots=True)
class TransferMetadata:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        try:
            source = dict(self.values)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "transfer metadata must be a mapping"
            ) from exc

        if len(source) > _MAX_METADATA_KEYS:
            raise ValueError(
                "transfer metadata contains too many keys"
            )

        normalized: dict[str, Any] = {}

        for raw_key, raw_value in source.items():
            key = _normalize_metadata_key(raw_key)

            if key in normalized:
                raise ValueError(
                    "transfer metadata contains duplicate "
                    f"normalized key: {key}"
                )

            normalized[key] = _normalize_metadata_value(
                raw_value,
                field_name=f"transfer metadata value {key}",
            )

        object.__setattr__(
            self,
            "values",
            MappingProxyType(
                dict(sorted(normalized.items()))
            ),
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls({})

        if not isinstance(value, Mapping):
            raise TypeError(
                "transfer metadata must be a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> Mapping[str, Any]:
        return self.values


class TransferFeeType(_NormalizedEnum):
    SERVICE = "service"
    PROCESSING = "processing"
    NETWORK = "network"
    DELIVERY = "delivery"
    COMPLIANCE = "compliance"
    FX_MARGIN = "fx_margin"
    AGENT = "agent"
    PARTNER = "partner"
    TAX = "tax"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class TransferPricingMetadata:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        normalized = TransferMetadata.of(self.values)

        object.__setattr__(
            self,
            "values",
            normalized.values,
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls({})

        if isinstance(value, TransferMetadata):
            return cls(value.values)

        if not isinstance(value, Mapping):
            raise TypeError(
                "transfer pricing metadata must be a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> Mapping[str, Any]:
        return self.values


@dataclass(frozen=True, slots=True)
class TransferFee:
    fee_type: TransferFeeType
    amount: Money
    description: str | None = None
    refundable: bool = False
    metadata: TransferPricingMetadata = (
        TransferPricingMetadata({})
    )

    def __post_init__(self) -> None:
        normalized_fee_type = TransferFeeType.parse(
            self.fee_type
        )

        if not isinstance(self.refundable, bool):
            raise TypeError(
                "transfer fee refundable must be a boolean"
            )

        _require_non_negative_money(
            self.amount,
            field_name="transfer fee amount",
        )

        object.__setattr__(
            self,
            "fee_type",
            normalized_fee_type,
        )
        object.__setattr__(
            self,
            "description",
            _normalize_optional_text(
                self.description,
                field_name="transfer fee description",
                maximum_length=512,
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            TransferPricingMetadata.of(
                self.metadata
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        fee_type: object,
        amount: Money,
        description: object = None,
        refundable: bool = False,
        metadata: object = None,
    ) -> Self:
        return cls(
            fee_type=TransferFeeType.parse(fee_type),
            amount=amount,
            description=_normalize_optional_text(
                description,
                field_name="transfer fee description",
                maximum_length=512,
            ),
            refundable=refundable,
            metadata=TransferPricingMetadata.of(
                metadata
            ),
        )

    @property
    def currency_code(self) -> str:
        return _money_currency_code(
            self.amount,
            field_name="transfer fee amount",
        )

    @property
    def amount_decimal(self) -> Decimal:
        return _money_amount_decimal(
            self.amount,
            field_name="transfer fee amount",
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "fee_type": self.fee_type.value,
            "amount": dict(
                _money_canonical_dict(self.amount)
            ),
            "description": self.description,
            "refundable": self.refundable,
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class TransferCharge:
    charge_code: str
    amount: Money
    description: str | None = None
    third_party: bool = False
    metadata: TransferPricingMetadata = (
        TransferPricingMetadata({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.third_party, bool):
            raise TypeError(
                "transfer charge third_party must be a boolean"
            )

        _require_non_negative_money(
            self.amount,
            field_name="transfer charge amount",
        )

        object.__setattr__(
            self,
            "charge_code",
            _normalize_required_text(
                self.charge_code,
                field_name="transfer charge code",
                maximum_length=64,
            ).lower().replace("-", "_").replace(" ", "_"),
        )
        object.__setattr__(
            self,
            "description",
            _normalize_optional_text(
                self.description,
                field_name="transfer charge description",
                maximum_length=512,
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            TransferPricingMetadata.of(
                self.metadata
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        charge_code: object,
        amount: Money,
        description: object = None,
        third_party: bool = False,
        metadata: object = None,
    ) -> Self:
        return cls(
            charge_code=_normalize_required_text(
                charge_code,
                field_name="transfer charge code",
                maximum_length=64,
            ),
            amount=amount,
            description=_normalize_optional_text(
                description,
                field_name="transfer charge description",
                maximum_length=512,
            ),
            third_party=third_party,
            metadata=TransferPricingMetadata.of(
                metadata
            ),
        )

    @property
    def currency_code(self) -> str:
        return _money_currency_code(
            self.amount,
            field_name="transfer charge amount",
        )

    @property
    def amount_decimal(self) -> Decimal:
        return _money_amount_decimal(
            self.amount,
            field_name="transfer charge amount",
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "charge_code": self.charge_code,
            "amount": dict(
                _money_canonical_dict(self.amount)
            ),
            "description": self.description,
            "third_party": self.third_party,
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class TransferAmountBreakdown:
    source_amount: Money
    destination_amount: Money
    fees: tuple[TransferFee, ...]
    charges: tuple[TransferCharge, ...]
    fee_total: Money
    charge_total: Money
    total_debit_amount: Money
    metadata: TransferPricingMetadata = (
        TransferPricingMetadata({})
    )

    def __post_init__(self) -> None:
        _require_non_negative_money(
            self.source_amount,
            field_name="transfer breakdown source amount",
        )
        _require_non_negative_money(
            self.destination_amount,
            field_name=(
                "transfer breakdown destination amount"
            ),
        )
        _require_non_negative_money(
            self.fee_total,
            field_name="transfer breakdown fee total",
        )
        _require_non_negative_money(
            self.charge_total,
            field_name="transfer breakdown charge total",
        )
        _require_non_negative_money(
            self.total_debit_amount,
            field_name=(
                "transfer breakdown total debit amount"
            ),
        )

        normalized_fees = tuple(self.fees)
        normalized_charges = tuple(self.charges)

        if not all(
            isinstance(item, TransferFee)
            for item in normalized_fees
        ):
            raise TypeError(
                "transfer breakdown fees must contain "
                "TransferFee values"
            )

        if not all(
            isinstance(item, TransferCharge)
            for item in normalized_charges
        ):
            raise TypeError(
                "transfer breakdown charges must contain "
                "TransferCharge values"
            )

        source_currency = _money_currency_code(
            self.source_amount,
            field_name="transfer breakdown source amount",
        )

        for fee in normalized_fees:
            if fee.currency_code != source_currency:
                raise ValueError(
                    "transfer fee currency must match "
                    "source amount currency"
                )

        for charge in normalized_charges:
            if charge.currency_code != source_currency:
                raise ValueError(
                    "transfer charge currency must match "
                    "source amount currency"
                )

        for total_name, total_value in (
            ("fee total", self.fee_total),
            ("charge total", self.charge_total),
            ("total debit amount", self.total_debit_amount),
        ):
            if (
                _money_currency_code(
                    total_value,
                    field_name=(
                        f"transfer breakdown {total_name}"
                    ),
                )
                != source_currency
            ):
                raise ValueError(
                    f"transfer breakdown {total_name} currency "
                    "must match source amount currency"
                )

        expected_fee_total = sum(
            (
                fee.amount_decimal
                for fee in normalized_fees
            ),
            Decimal("0"),
        )
        expected_charge_total = sum(
            (
                charge.amount_decimal
                for charge in normalized_charges
            ),
            Decimal("0"),
        )

        actual_fee_total = _money_amount_decimal(
            self.fee_total,
            field_name="transfer breakdown fee total",
        )
        actual_charge_total = _money_amount_decimal(
            self.charge_total,
            field_name="transfer breakdown charge total",
        )

        if actual_fee_total != expected_fee_total:
            raise ValueError(
                "transfer breakdown fee total does not "
                "match fee items"
            )

        if actual_charge_total != expected_charge_total:
            raise ValueError(
                "transfer breakdown charge total does not "
                "match charge items"
            )

        expected_debit_total = (
            _money_amount_decimal(
                self.source_amount,
                field_name=(
                    "transfer breakdown source amount"
                ),
            )
            + expected_fee_total
            + expected_charge_total
        )
        actual_debit_total = _money_amount_decimal(
            self.total_debit_amount,
            field_name=(
                "transfer breakdown total debit amount"
            ),
        )

        if actual_debit_total != expected_debit_total:
            raise ValueError(
                "transfer breakdown total debit amount does "
                "not match source amount plus fees and charges"
            )

        object.__setattr__(
            self,
            "fees",
            normalized_fees,
        )
        object.__setattr__(
            self,
            "charges",
            normalized_charges,
        )
        object.__setattr__(
            self,
            "metadata",
            TransferPricingMetadata.of(
                self.metadata
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        source_amount: Money,
        destination_amount: Money,
        fees: object = (),
        charges: object = (),
        fee_total: Money,
        charge_total: Money,
        total_debit_amount: Money,
        metadata: object = None,
    ) -> Self:
        try:
            normalized_fees = tuple(fees)  # type: ignore[arg-type]
        except TypeError as exc:
            raise TypeError(
                "transfer breakdown fees must be iterable"
            ) from exc

        try:
            normalized_charges = tuple(
                charges  # type: ignore[arg-type]
            )
        except TypeError as exc:
            raise TypeError(
                "transfer breakdown charges must be iterable"
            ) from exc

        return cls(
            source_amount=source_amount,
            destination_amount=destination_amount,
            fees=normalized_fees,
            charges=normalized_charges,
            fee_total=fee_total,
            charge_total=charge_total,
            total_debit_amount=total_debit_amount,
            metadata=TransferPricingMetadata.of(
                metadata
            ),
        )

    @property
    def source_currency_code(self) -> str:
        return _money_currency_code(
            self.source_amount,
            field_name="transfer breakdown source amount",
        )

    @property
    def destination_currency_code(self) -> str:
        return _money_currency_code(
            self.destination_amount,
            field_name=(
                "transfer breakdown destination amount"
            ),
        )

    @property
    def is_cross_currency(self) -> bool:
        return (
            self.source_currency_code
            != self.destination_currency_code
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
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
            "fees": [
                fee.canonical_dict()
                for fee in self.fees
            ],
            "charges": [
                charge.canonical_dict()
                for charge in self.charges
            ],
            "fee_total": dict(
                _money_canonical_dict(
                    self.fee_total
                )
            ),
            "charge_total": dict(
                _money_canonical_dict(
                    self.charge_total
                )
            ),
            "total_debit_amount": dict(
                _money_canonical_dict(
                    self.total_debit_amount
                )
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True, order=True)
class TransferInstructionId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="transfer instruction id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name="transfer instruction id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class TransferFundingReference:
    funding_source_id: str
    funding_source_type: str
    account_reference: TransferAccountReference
    authorization_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "funding_source_id",
            _normalize_required_text(
                self.funding_source_id,
                field_name="transfer funding source id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "funding_source_type",
            _normalize_required_text(
                self.funding_source_type,
                field_name="transfer funding source type",
                maximum_length=64,
            ).lower().replace("-", "_").replace(" ", "_"),
        )
        object.__setattr__(
            self,
            "account_reference",
            TransferAccountReference.of(
                self.account_reference
            ),
        )
        object.__setattr__(
            self,
            "authorization_reference",
            _normalize_optional_text(
                self.authorization_reference,
                field_name=(
                    "transfer funding authorization reference"
                ),
                maximum_length=_MAX_REFERENCE_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        if not isinstance(value, Mapping):
            raise TypeError(
                "transfer funding reference must be a mapping"
            )

        return cls(
            funding_source_id=value.get(
                "funding_source_id"
            ),  # type: ignore[arg-type]
            funding_source_type=value.get(
                "funding_source_type"
            ),  # type: ignore[arg-type]
            account_reference=(
                TransferAccountReference.of(
                    value.get("account_reference")
                )
            ),
            authorization_reference=value.get(
                "authorization_reference"
            ),  # type: ignore[arg-type]
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "funding_source_id": self.funding_source_id,
            "funding_source_type": (
                self.funding_source_type
            ),
            "account_reference": (
                self.account_reference.canonical_dict()
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
        }


@dataclass(frozen=True, slots=True)
class TransferBeneficiaryReference:
    beneficiary_id: str
    beneficiary_type: str
    party_reference: TransferPartyReference
    account_reference: TransferAccountReference
    delivery_method: str
    routing_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "beneficiary_id",
            _normalize_required_text(
                self.beneficiary_id,
                field_name="transfer beneficiary id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "beneficiary_type",
            _normalize_required_text(
                self.beneficiary_type,
                field_name="transfer beneficiary type",
                maximum_length=64,
            ).lower().replace("-", "_").replace(" ", "_"),
        )
        object.__setattr__(
            self,
            "party_reference",
            TransferPartyReference.of(
                self.party_reference
            ),
        )
        object.__setattr__(
            self,
            "account_reference",
            TransferAccountReference.of(
                self.account_reference
            ),
        )
        object.__setattr__(
            self,
            "delivery_method",
            _normalize_required_text(
                self.delivery_method,
                field_name="transfer delivery method",
                maximum_length=64,
            ).lower().replace("-", "_").replace(" ", "_"),
        )
        object.__setattr__(
            self,
            "routing_reference",
            _normalize_optional_text(
                self.routing_reference,
                field_name="transfer routing reference",
                maximum_length=_MAX_REFERENCE_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        if not isinstance(value, Mapping):
            raise TypeError(
                "transfer beneficiary reference must be a mapping"
            )

        return cls(
            beneficiary_id=value.get(
                "beneficiary_id"
            ),  # type: ignore[arg-type]
            beneficiary_type=value.get(
                "beneficiary_type"
            ),  # type: ignore[arg-type]
            party_reference=TransferPartyReference.of(
                value.get("party_reference")
            ),
            account_reference=(
                TransferAccountReference.of(
                    value.get("account_reference")
                )
            ),
            delivery_method=value.get(
                "delivery_method"
            ),  # type: ignore[arg-type]
            routing_reference=value.get(
                "routing_reference"
            ),  # type: ignore[arg-type]
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "beneficiary_id": self.beneficiary_id,
            "beneficiary_type": self.beneficiary_type,
            "party_reference": (
                self.party_reference.canonical_dict()
            ),
            "account_reference": (
                self.account_reference.canonical_dict()
            ),
            "delivery_method": self.delivery_method,
            "routing_reference": self.routing_reference,
        }


@dataclass(frozen=True, slots=True)
class TransferInstructionMetadata:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        normalized = TransferMetadata.of(self.values)

        object.__setattr__(
            self,
            "values",
            normalized.values,
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls({})

        if isinstance(value, TransferMetadata):
            return cls(value.values)

        if not isinstance(value, Mapping):
            raise TypeError(
                "transfer instruction metadata must be a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> Mapping[str, Any]:
        return self.values


@dataclass(frozen=True, slots=True)
class TransferInstruction:
    instruction_id: TransferInstructionId
    transfer_id: TransferId
    funding_reference: TransferFundingReference
    beneficiary_reference: TransferBeneficiaryReference
    requested_source_amount: Money
    expected_destination_amount: Money
    requested_at: datetime
    expires_at: datetime | None
    metadata: TransferInstructionMetadata
    version: int = 1

    def __post_init__(self) -> None:
        normalized_instruction_id = (
            TransferInstructionId.of(
                self.instruction_id
            )
        )
        normalized_transfer_id = TransferId.of(
            self.transfer_id
        )
        normalized_funding = (
            TransferFundingReference.of(
                self.funding_reference
            )
        )
        normalized_beneficiary = (
            TransferBeneficiaryReference.of(
                self.beneficiary_reference
            )
        )

        if not isinstance(
            self.requested_source_amount,
            Money,
        ):
            raise TypeError(
                "requested source amount must be Money"
            )

        if not isinstance(
            self.expected_destination_amount,
            Money,
        ):
            raise TypeError(
                "expected destination amount must be Money"
            )

        source_currency = _money_currency_code(
            self.requested_source_amount,
            field_name="requested source amount",
        )
        destination_currency = _money_currency_code(
            self.expected_destination_amount,
            field_name="expected destination amount",
        )

        funding_currency = (
            normalized_funding
            .account_reference
            .currency_code
        )
        beneficiary_currency = (
            normalized_beneficiary
            .account_reference
            .currency_code
        )

        if (
            funding_currency is not None
            and funding_currency != source_currency
        ):
            raise ValueError(
                "funding account currency must match "
                "requested source amount currency"
            )

        if (
            beneficiary_currency is not None
            and beneficiary_currency
            != destination_currency
        ):
            raise ValueError(
                "beneficiary account currency must match "
                "expected destination amount currency"
            )

        normalized_requested_at = _normalize_datetime(
            self.requested_at,
            field_name="transfer instruction requested_at",
        )

        normalized_expires_at = None

        if self.expires_at is not None:
            normalized_expires_at = _normalize_datetime(
                self.expires_at,
                field_name="transfer instruction expires_at",
            )

            if normalized_expires_at <= normalized_requested_at:
                raise ValueError(
                    "transfer instruction expires_at must be "
                    "later than requested_at"
                )

        normalized_metadata = (
            TransferInstructionMetadata.of(
                self.metadata
            )
        )
        normalized_version = _normalize_version(
            self.version
        )

        object.__setattr__(
            self,
            "instruction_id",
            normalized_instruction_id,
        )
        object.__setattr__(
            self,
            "transfer_id",
            normalized_transfer_id,
        )
        object.__setattr__(
            self,
            "funding_reference",
            normalized_funding,
        )
        object.__setattr__(
            self,
            "beneficiary_reference",
            normalized_beneficiary,
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
        instruction_id: object,
        transfer_id: object,
        funding_reference: object,
        beneficiary_reference: object,
        requested_source_amount: Money,
        expected_destination_amount: Money,
        requested_at: datetime,
        expires_at: datetime | None = None,
        metadata: object = None,
    ) -> Self:
        return cls(
            instruction_id=(
                TransferInstructionId.of(
                    instruction_id
                )
            ),
            transfer_id=TransferId.of(transfer_id),
            funding_reference=(
                TransferFundingReference.of(
                    funding_reference
                )
            ),
            beneficiary_reference=(
                TransferBeneficiaryReference.of(
                    beneficiary_reference
                )
            ),
            requested_source_amount=(
                requested_source_amount
            ),
            expected_destination_amount=(
                expected_destination_amount
            ),
            requested_at=requested_at,
            expires_at=expires_at,
            metadata=(
                TransferInstructionMetadata.of(
                    metadata
                )
            ),
            version=1,
        )

    @property
    def source_currency_code(self) -> str:
        return _money_currency_code(
            self.requested_source_amount,
            field_name="requested source amount",
        )

    @property
    def destination_currency_code(self) -> str:
        return _money_currency_code(
            self.expected_destination_amount,
            field_name="expected destination amount",
        )

    @property
    def is_cross_currency(self) -> bool:
        return (
            self.source_currency_code
            != self.destination_currency_code
        )

    def is_expired(
        self,
        *,
        at: datetime,
    ) -> bool:
        normalized_at = _normalize_datetime(
            at,
            field_name="transfer instruction expiry check",
        )

        return (
            self.expires_at is not None
            and normalized_at >= self.expires_at
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "instruction_id": self.instruction_id.value,
            "transfer_id": self.transfer_id.value,
            "funding_reference": (
                self.funding_reference.canonical_dict()
            ),
            "beneficiary_reference": (
                self.beneficiary_reference.canonical_dict()
            ),
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
                self.expires_at.isoformat()
                if self.expires_at is not None
                else None
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class Transfer:
    """Immutable canonical NovaPay transfer aggregate.

    This aggregate describes transfer intent and state. It does not
    debit wallets, post journal entries, acquire or lock exchange
    rates, invoke payment providers, execute settlement, or persist
    itself.
    """

    transfer_id: TransferId
    reference: TransferReference
    status: TransferStatus
    transfer_type: TransferType
    direction: TransferDirection
    purpose: TransferPurpose
    priority: TransferPriority
    sender: TransferPartyReference
    beneficiary: TransferPartyReference
    source_account: TransferAccountReference
    destination_account: TransferAccountReference
    source_amount: Money
    destination_amount: Money
    metadata: TransferMetadata
    created_at: datetime
    updated_at: datetime
    version: int = 1

    def __post_init__(self) -> None:
        normalized_transfer_id = TransferId.of(
            self.transfer_id
        )
        normalized_reference = TransferReference.of(
            self.reference
        )
        normalized_status = TransferStatus.parse(
            self.status
        )
        normalized_type = TransferType.parse(
            self.transfer_type
        )
        normalized_direction = TransferDirection.parse(
            self.direction
        )
        normalized_purpose = TransferPurpose.parse(
            self.purpose
        )
        normalized_priority = TransferPriority.parse(
            self.priority
        )
        normalized_sender = TransferPartyReference.of(
            self.sender
        )
        normalized_beneficiary = (
            TransferPartyReference.of(
                self.beneficiary
            )
        )
        normalized_source_account = (
            TransferAccountReference.of(
                self.source_account
            )
        )
        normalized_destination_account = (
            TransferAccountReference.of(
                self.destination_account
            )
        )

        if not isinstance(self.source_amount, Money):
            raise TypeError(
                "transfer source amount must be Money"
            )

        if not isinstance(
            self.destination_amount,
            Money,
        ):
            raise TypeError(
                "transfer destination amount must be Money"
            )

        source_currency = _money_currency_code(
            self.source_amount,
            field_name="transfer source amount",
        )
        destination_currency = _money_currency_code(
            self.destination_amount,
            field_name="transfer destination amount",
        )

        if (
            normalized_source_account.currency_code
            is not None
            and normalized_source_account.currency_code
            != source_currency
        ):
            raise ValueError(
                "transfer source account currency must "
                "match source amount currency"
            )

        if (
            normalized_destination_account.currency_code
            is not None
            and normalized_destination_account.currency_code
            != destination_currency
        ):
            raise ValueError(
                "transfer destination account currency must "
                "match destination amount currency"
            )

        if (
            normalized_sender.party_id
            == normalized_beneficiary.party_id
            and normalized_sender.party_type
            == normalized_beneficiary.party_type
            and normalized_source_account.account_id
            == normalized_destination_account.account_id
        ):
            raise ValueError(
                "transfer source and destination must not "
                "refer to the same party and account"
            )

        normalized_metadata = TransferMetadata.of(
            self.metadata
        )
        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name="transfer created_at",
        )
        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name="transfer updated_at",
        )
        normalized_version = _normalize_version(
            self.version
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "transfer updated_at must not be earlier "
                "than created_at"
            )

        object.__setattr__(
            self,
            "transfer_id",
            normalized_transfer_id,
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
            "transfer_type",
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
            "sender",
            normalized_sender,
        )
        object.__setattr__(
            self,
            "beneficiary",
            normalized_beneficiary,
        )
        object.__setattr__(
            self,
            "source_account",
            normalized_source_account,
        )
        object.__setattr__(
            self,
            "destination_account",
            normalized_destination_account,
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
        transfer_id: object,
        reference: object,
        sender: object,
        beneficiary: object,
        source_account: object,
        destination_account: object,
        source_amount: Money,
        destination_amount: Money,
        created_at: datetime,
        transfer_type: object = TransferType.INTERNAL,
        direction: object = TransferDirection.INTERNAL,
        purpose: object = TransferPurpose.GENERAL,
        priority: object = TransferPriority.NORMAL,
        status: object = TransferStatus.DRAFT,
        metadata: object = None,
    ) -> Self:
        normalized_created_at = _normalize_datetime(
            created_at,
            field_name="transfer created_at",
        )

        return cls(
            transfer_id=TransferId.of(transfer_id),
            reference=TransferReference.of(reference),
            status=TransferStatus.parse(status),
            transfer_type=TransferType.parse(
                transfer_type
            ),
            direction=TransferDirection.parse(
                direction
            ),
            purpose=TransferPurpose.parse(purpose),
            priority=TransferPriority.parse(
                priority
            ),
            sender=TransferPartyReference.of(
                sender
            ),
            beneficiary=TransferPartyReference.of(
                beneficiary
            ),
            source_account=(
                TransferAccountReference.of(
                    source_account
                )
            ),
            destination_account=(
                TransferAccountReference.of(
                    destination_account
                )
            ),
            source_amount=source_amount,
            destination_amount=destination_amount,
            metadata=TransferMetadata.of(metadata),
            created_at=normalized_created_at,
            updated_at=normalized_created_at,
            version=1,
        )

    @property
    def source_currency_code(self) -> str:
        return _money_currency_code(
            self.source_amount,
            field_name="transfer source amount",
        )

    @property
    def destination_currency_code(self) -> str:
        return _money_currency_code(
            self.destination_amount,
            field_name="transfer destination amount",
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
            TransferStatus.COMPLETED,
            TransferStatus.FAILED,
            TransferStatus.CANCELLED,
            TransferStatus.REVERSED,
            TransferStatus.EXPIRED,
        }

    def _with_change(
        self,
        *,
        occurred_at: datetime,
        status: object | None = None,
        reference: object | None = None,
        priority: object | None = None,
        metadata: object | None = None,
    ) -> Self:
        normalized_occurred_at = _normalize_datetime(
            occurred_at,
            field_name="transfer change occurred_at",
        )

        if normalized_occurred_at < self.updated_at:
            raise ValueError(
                "transfer change occurred_at must not be "
                "earlier than updated_at"
            )

        next_status = (
            self.status
            if status is None
            else TransferStatus.parse(status)
        )
        next_reference = (
            self.reference
            if reference is None
            else TransferReference.of(reference)
        )
        next_priority = (
            self.priority
            if priority is None
            else TransferPriority.parse(priority)
        )
        next_metadata = (
            self.metadata
            if metadata is None
            else TransferMetadata.of(metadata)
        )

        if (
            next_status == self.status
            and next_reference == self.reference
            and next_priority == self.priority
            and next_metadata == self.metadata
        ):
            raise ValueError(
                "transfer update must change at least one field"
            )

        return replace(
            self,
            status=next_status,
            reference=next_reference,
            priority=next_priority,
            metadata=next_metadata,
            updated_at=normalized_occurred_at,
            version=self.version + 1,
        )

    def _transition_status(
        self,
        target_status: object,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        target = TransferStatus.parse(target_status)

        allowed_transitions: Mapping[
            TransferStatus,
            frozenset[TransferStatus],
        ] = {
            TransferStatus.DRAFT: frozenset(
                {
                    TransferStatus.VALIDATED,
                    TransferStatus.CANCELLED,
                    TransferStatus.EXPIRED,
                }
            ),
            TransferStatus.VALIDATED: frozenset(
                {
                    TransferStatus.AUTHORIZED,
                    TransferStatus.CANCELLED,
                    TransferStatus.EXPIRED,
                }
            ),
            TransferStatus.AUTHORIZED: frozenset(
                {
                    TransferStatus.SUBMITTED,
                    TransferStatus.CANCELLED,
                    TransferStatus.EXPIRED,
                }
            ),
            TransferStatus.SUBMITTED: frozenset(
                {
                    TransferStatus.PROCESSING,
                    TransferStatus.FAILED,
                    TransferStatus.CANCELLED,
                    TransferStatus.EXPIRED,
                }
            ),
            TransferStatus.PROCESSING: frozenset(
                {
                    TransferStatus.COMPLETED,
                    TransferStatus.FAILED,
                    TransferStatus.CANCELLED,
                }
            ),
            TransferStatus.COMPLETED: frozenset(
                {
                    TransferStatus.REVERSED,
                }
            ),
            TransferStatus.FAILED: frozenset(),
            TransferStatus.CANCELLED: frozenset(),
            TransferStatus.REVERSED: frozenset(),
            TransferStatus.EXPIRED: frozenset(),
        }

        allowed = allowed_transitions[self.status]

        if target not in allowed:
            raise ValueError(
                "invalid transfer status transition: "
                f"{self.status.value} -> {target.value}"
            )

        next_metadata = (
            self.metadata
            if metadata is None
            else TransferMetadata.of(metadata)
        )

        return self._with_change(
            occurred_at=occurred_at,
            status=target,
            metadata=next_metadata,
        )

    def validate(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        return self._transition_status(
            TransferStatus.VALIDATED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def authorize(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        return self._transition_status(
            TransferStatus.AUTHORIZED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def submit(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        """Record submission state without invoking a provider."""

        return self._transition_status(
            TransferStatus.SUBMITTED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def mark_processing(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        return self._transition_status(
            TransferStatus.PROCESSING,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def complete(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        """Record completion state without posting or settlement."""

        return self._transition_status(
            TransferStatus.COMPLETED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def fail(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        return self._transition_status(
            TransferStatus.FAILED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def cancel(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        return self._transition_status(
            TransferStatus.CANCELLED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def expire(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        return self._transition_status(
            TransferStatus.EXPIRED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def reverse(
        self,
        *,
        occurred_at: datetime,
        metadata: object | None = None,
    ) -> Self:
        """Record reversal state without ledger reversal authority."""

        return self._transition_status(
            TransferStatus.REVERSED,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def update_reference(
        self,
        reference: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized = TransferReference.of(reference)

        if normalized == self.reference:
            raise ValueError(
                "transfer reference update must change reference"
            )

        if self.status is not TransferStatus.DRAFT:
            raise ValueError(
                "transfer reference may only be changed in draft"
            )

        return self._with_change(
            occurred_at=occurred_at,
            reference=normalized,
        )

    def update_priority(
        self,
        priority: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized = TransferPriority.parse(priority)

        if normalized == self.priority:
            raise ValueError(
                "transfer priority update must change priority"
            )

        if self.is_terminal:
            raise ValueError(
                "terminal transfer priority cannot be changed"
            )

        return self._with_change(
            occurred_at=occurred_at,
            priority=normalized,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized = TransferMetadata.of(metadata)

        if normalized == self.metadata:
            raise ValueError(
                "transfer metadata update must change metadata"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "transfer_id": self.transfer_id.value,
            "reference": self.reference.value,
            "status": self.status.value,
            "transfer_type": self.transfer_type.value,
            "direction": self.direction.value,
            "purpose": self.purpose.value,
            "priority": self.priority.value,
            "sender": self.sender.canonical_dict(),
            "beneficiary": (
                self.beneficiary.canonical_dict()
            ),
            "source_account": (
                self.source_account.canonical_dict()
            ),
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
    "Transfer",
    "TransferAccountReference",
    "TransferAmountBreakdown",
    "TransferBeneficiaryReference",
    "TransferCharge",
    "TransferDirection",
    "TransferFee",
    "TransferFeeType",
    "TransferFundingReference",
    "TransferId",
    "TransferInstruction",
    "TransferInstructionId",
    "TransferInstructionMetadata",
    "TransferMetadata",
    "TransferPartyReference",
    "TransferPricingMetadata",
    "TransferPriority",
    "TransferPurpose",
    "TransferReference",
    "TransferStatus",
    "TransferType",
]
