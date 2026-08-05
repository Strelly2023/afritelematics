"""Canonical NovaPay Receipt domain primitives.

This module defines immutable identifiers, enumerations, metadata, and
reference records used by the NovaPay Receipt domain.

The module intentionally has no authority to:

- execute payments, transfers, remittances, or settlements;
- mutate wallets;
- post ledger entries;
- submit instructions to providers;
- execute reconciliation;
- persist data;
- deliver receipts;
- create cryptographic signatures; or
- invoke external verification services.

Aggregate behavior, monetary records, lifecycle transitions, integrity
evidence, verification results, presentation summaries, and public package
exports are introduced by later WP-001O sections.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Mapping

from .money import Money


__all__ = [
    "Receipt",
    "ReceiptAdjustment",
    "ReceiptAdjustmentId",
    "ReceiptAdjustmentType",
    "ReceiptFormat",
    "ReceiptId",
    "ReceiptIntegrityEvidence",
    "ReceiptIntegrityEvidenceType",
    "ReceiptLineItem",
    "ReceiptLineItemId",
    "ReceiptLineItemType",
    "ReceiptMetadata",
    "ReceiptMonetarySummary",
    "ReceiptParty",
    "ReceiptPartyId",
    "ReceiptPartyType",
    "ReceiptReference",
    "ReceiptReferenceType",
    "ReceiptStatus",
    "ReceiptTax",
    "ReceiptTaxId",
    "ReceiptTaxType",
    "ReceiptType",
    "ReceiptVerificationResult",
    "ReceiptVerificationStatus",
]

_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._:/-]{0,126}[A-Za-z0-9])?$"
)

_METADATA_KEY_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]{0,62}$"
)

_MAX_REFERENCE_VALUE_LENGTH = 256
_MAX_METADATA_ITEMS = 64
_MAX_METADATA_DEPTH = 8


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

    normalized = " ".join(
        value.strip().split()
    )

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
            f"{field_name} contains unsupported characters"
        )

    return normalized


def _normalize_enum_token(
    value: object,
    *,
    field_name: str,
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=64,
    )

    return normalized.lower().replace(
        "-",
        "_",
    ).replace(
        " ",
        "_",
    )


def _normalize_metadata_key(
    value: object,
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name="receipt metadata key",
        maximum_length=64,
    ).lower().replace(
        "-",
        "_",
    ).replace(
        " ",
        "_",
    )

    if not _METADATA_KEY_PATTERN.fullmatch(
        normalized
    ):
        raise ValueError(
            "receipt metadata key must use lowercase "
            "letters, digits, and underscores"
        )

    return normalized


def _normalize_metadata_value(
    value: object,
    *,
    depth: int,
) -> Any:
    if depth > _MAX_METADATA_DEPTH:
        raise ValueError(
            "receipt metadata nesting exceeds "
            f"{_MAX_METADATA_DEPTH} levels"
        )

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return deepcopy(value)

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}

        for raw_key, raw_value in value.items():
            key = _normalize_metadata_key(
                raw_key
            )

            if key in normalized:
                raise ValueError(
                    "receipt metadata contains duplicate "
                    f"normalized key: {key}"
                )

            normalized[key] = (
                _normalize_metadata_value(
                    raw_value,
                    depth=depth + 1,
                )
            )

        return normalized

    if isinstance(value, (list, tuple)):
        return [
            _normalize_metadata_value(
                item,
                depth=depth + 1,
            )
            for item in value
        ]

    raise TypeError(
        "receipt metadata values must be JSON-compatible"
    )


_CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


def _normalize_currency_code(
    value: object,
    *,
    field_name: str = "receipt currency code",
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=3,
    ).upper()

    if not _CURRENCY_CODE_PATTERN.fullmatch(
        normalized
    ):
        raise ValueError(
            f"{field_name} must be a three-letter "
            "alphabetic currency code"
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


def _normalize_optional_aware_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime | None:
    if value is None:
        return None

    return _normalize_aware_datetime(
        value,
        field_name=field_name,
    )


def _normalize_positive_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field_name} must be an integer"
        )

    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero"
        )

    return value


def _normalize_identifier_tuple(
    values: object,
    *,
    identifier_type: type,
    field_name: str,
) -> tuple:
    if not isinstance(values, (tuple, list)):
        raise TypeError(
            f"{field_name} must be a tuple or list"
        )

    normalized = tuple(
        identifier_type.of(value)
        for value in values
    )

    identifiers = [
        item.value
        for item in normalized
    ]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError(
            f"{field_name} must not contain duplicates"
        )

    return normalized


def _normalize_reference_tuple(
    values: object,
) -> tuple[ReceiptReference, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(
            "receipt references must be a tuple or list"
        )

    normalized: list[ReceiptReference] = []

    for value in values:
        if not isinstance(value, ReceiptReference):
            raise TypeError(
                "receipt references must contain "
                "ReceiptReference values"
            )

        normalized.append(value)

    keys = [
        item.canonical_key
        for item in normalized
    ]

    if len(keys) != len(set(keys)):
        raise ValueError(
            "receipt references must not contain duplicates"
        )

    return tuple(normalized)


def _normalize_evidence_reference_tuple(
    values: object,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(
            "receipt integrity evidence must be a tuple or list"
        )

    normalized = tuple(
        _normalize_identifier(
            value,
            field_name="receipt integrity evidence reference",
        )
        for value in values
    )

    if len(normalized) != len(set(normalized)):
        raise ValueError(
            "receipt integrity evidence must not contain duplicates"
        )

    return normalized


def _money_amount(
    value: Money,
    *,
    field_name: str,
):
    if not isinstance(value, Money):
        raise TypeError(
            f"{field_name} must be a Money value"
        )

    if not hasattr(value, "amount"):
        raise TypeError(
            "canonical Money must expose amount"
        )

    return value.amount


def _money_currency(
    value: Money,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, Money):
        raise TypeError(
            f"{field_name} must be a Money value"
        )

    raw_currency = None

    for attribute in (
        "currency_code",
        "currency",
    ):
        if hasattr(value, attribute):
            raw_currency = getattr(
                value,
                attribute,
            )
            break

    if raw_currency is None:
        raise TypeError(
            "canonical Money must expose currency "
            "or currency_code"
        )

    visited: set[int] = set()

    while not isinstance(raw_currency, str):
        identity = id(raw_currency)

        if identity in visited:
            raise TypeError(
                f"{field_name} currency could not be normalized"
            )

        visited.add(identity)

        extracted = None

        for attribute in (
            "value",
            "code",
            "currency_code",
            "alpha_code",
            "iso_code",
        ):
            if hasattr(raw_currency, attribute):
                candidate = getattr(
                    raw_currency,
                    attribute,
                )

                if candidate is not None:
                    extracted = candidate
                    break

        if extracted is None:
            if isinstance(raw_currency, Enum):
                extracted = raw_currency.value
            else:
                text = str(raw_currency).strip()

                if (
                    len(text) == 3
                    and text.isalpha()
                ):
                    extracted = text
                else:
                    raise TypeError(
                        f"{field_name} currency must expose "
                        "a three-letter currency code"
                    )

        raw_currency = extracted

    return _normalize_currency_code(
        raw_currency,
        field_name=f"{field_name} currency",
    )


def _money_canonical_dict(
    value: Money,
) -> dict[str, Any]:
    if not isinstance(value, Money):
        raise TypeError(
            "money serialization requires a Money value"
        )

    for method_name in (
        "canonical_dict",
        "to_dict",
    ):
        method = getattr(
            value,
            method_name,
            None,
        )

        if callable(method):
            payload = method()

            if not isinstance(payload, Mapping):
                raise TypeError(
                    "Money serialization must return a mapping"
                )

            return deepcopy(
                dict(payload)
            )

    return {
        "amount": str(
            _money_amount(
                value,
                field_name="money",
            )
        ),
        "currency_code": _money_currency(
            value,
            field_name="money",
        ),
    }


def _require_non_negative_money(
    value: Money,
    *,
    field_name: str,
    currency_code: str | None = None,
) -> Money:
    amount = _money_amount(
        value,
        field_name=field_name,
    )

    if amount < 0:
        raise ValueError(
            f"{field_name} must not be negative"
        )

    actual_currency = _money_currency(
        value,
        field_name=field_name,
    )

    if (
        currency_code is not None
        and actual_currency != currency_code
    ):
        raise ValueError(
            f"{field_name} currency must be "
            f"{currency_code}"
        )

    return value


def _require_positive_decimal(
    value: object,
    *,
    field_name: str,
):
    from decimal import Decimal, InvalidOperation

    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    try:
        normalized = Decimal(
            str(value)
        )
    except (InvalidOperation, ValueError):
        raise TypeError(
            f"{field_name} must be numeric"
        ) from None

    if not normalized.is_finite():
        raise ValueError(
            f"{field_name} must be finite"
        )

    if normalized <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero"
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


def _normalize_record_tuple(
    values: object,
    *,
    record_type: type,
    identifier_attribute: str,
    field_name: str,
) -> tuple:
    if not isinstance(values, (tuple, list)):
        raise TypeError(
            f"{field_name} must be a tuple or list"
        )

    normalized = []

    for value in values:
        if not isinstance(value, record_type):
            raise TypeError(
                f"{field_name} must contain "
                f"{record_type.__name__} values"
            )

        normalized.append(value)

    identifiers = [
        getattr(
            item,
            identifier_attribute,
        ).value
        for item in normalized
    ]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError(
            f"{field_name} must not contain duplicate identifiers"
        )

    return tuple(normalized)


class _ReceiptStringEnum(str, Enum):
    @classmethod
    def parse(
        cls,
        value: object,
    ) -> "_ReceiptStringEnum":
        if isinstance(value, cls):
            return value

        token = _normalize_enum_token(
            value,
            field_name=cls.__name__,
        )

        for member in cls:
            if member.value == token:
                return member

        supported = ", ".join(
            item.value
            for item in cls
        )

        raise ValueError(
            f"unsupported {cls.__name__}: "
            f"{value!r}; expected one of: {supported}"
        )


class ReceiptType(_ReceiptStringEnum):
    PAYMENT = "payment"
    TRANSFER = "transfer"
    REMITTANCE = "remittance"
    REFUND = "refund"
    REVERSAL = "reversal"
    SETTLEMENT = "settlement"
    FEE = "fee"
    ADJUSTMENT = "adjustment"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    MERCHANT_PAYMENT = "merchant_payment"
    BILL_PAYMENT = "bill_payment"


class ReceiptStatus(_ReceiptStringEnum):
    DRAFT = "draft"
    PREPARED = "prepared"
    ISSUED = "issued"
    DELIVERED = "delivered"
    VOIDED = "voided"
    CANCELED = "canceled"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"

    @property
    def is_terminal(self) -> bool:
        return self in {
            ReceiptStatus.VOIDED,
            ReceiptStatus.CANCELED,
            ReceiptStatus.EXPIRED,
            ReceiptStatus.SUPERSEDED,
        }

    @property
    def is_issued(self) -> bool:
        return self in {
            ReceiptStatus.ISSUED,
            ReceiptStatus.DELIVERED,
            ReceiptStatus.VOIDED,
            ReceiptStatus.SUPERSEDED,
        }


class ReceiptFormat(_ReceiptStringEnum):
    STRUCTURED = "structured"
    TEXT = "text"
    HTML = "html"
    PDF = "pdf"
    QR = "qr"
    DIGITAL_WALLET = "digital_wallet"


class ReceiptPartyType(_ReceiptStringEnum):
    ISSUER = "issuer"
    PAYER = "payer"
    PAYEE = "payee"
    SENDER = "sender"
    RECIPIENT = "recipient"
    AGENT = "agent"
    MERCHANT = "merchant"
    BUSINESS = "business"
    PROVIDER = "provider"
    PLATFORM = "platform"


class ReceiptReferenceType(_ReceiptStringEnum):
    TRANSACTION = "transaction"
    TRANSFER = "transfer"
    REMITTANCE = "remittance"
    SETTLEMENT_BATCH = "settlement_batch"
    SETTLEMENT_RECONCILIATION = (
        "settlement_reconciliation"
    )
    JOURNAL_ENTRY = "journal_entry"
    WALLET = "wallet"
    PROVIDER = "provider"
    EXTERNAL = "external"
    ORIGINAL_RECEIPT = "original_receipt"
    SUPERSEDING_RECEIPT = "superseding_receipt"


class ReceiptLineItemType(_ReceiptStringEnum):
    PRINCIPAL = "principal"
    PRODUCT = "product"
    SERVICE = "service"
    FEE = "fee"
    COMMISSION = "commission"
    TAX = "tax"
    DISCOUNT = "discount"
    ADJUSTMENT = "adjustment"
    ROUNDING = "rounding"
    OTHER = "other"


class ReceiptAdjustmentType(_ReceiptStringEnum):
    DISCOUNT = "discount"
    REBATE = "rebate"
    SURCHARGE = "surcharge"
    ROUNDING = "rounding"
    CREDIT = "credit"
    DEBIT = "debit"
    PROMOTION = "promotion"
    CORRECTION = "correction"

    @property
    def reduces_total(self) -> bool:
        return self in {
            ReceiptAdjustmentType.DISCOUNT,
            ReceiptAdjustmentType.REBATE,
            ReceiptAdjustmentType.CREDIT,
            ReceiptAdjustmentType.PROMOTION,
        }

    @property
    def increases_total(self) -> bool:
        return self in {
            ReceiptAdjustmentType.SURCHARGE,
            ReceiptAdjustmentType.DEBIT,
        }


class ReceiptTaxType(_ReceiptStringEnum):
    GST = "gst"
    VAT = "vat"
    SALES_TAX = "sales_tax"
    WITHHOLDING = "withholding"
    EXCISE = "excise"
    DUTY = "duty"
    OTHER = "other"


class ReceiptIntegrityEvidenceType(
    _ReceiptStringEnum
):
    SHA256_DIGEST = "sha256_digest"
    DIGITAL_SIGNATURE = "digital_signature"
    PROVIDER_REFERENCE = "provider_reference"
    LEDGER_REFERENCE = "ledger_reference"
    CHAIN_ANCHOR = "chain_anchor"
    QR_PAYLOAD = "qr_payload"
    VERIFICATION_TOKEN = "verification_token"


class ReceiptVerificationStatus(
    _ReceiptStringEnum
):
    NOT_VERIFIED = "not_verified"
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    FAILED = "failed"
    EXPIRED = "expired"
    REVOKED = "revoked"

    @property
    def is_successful(self) -> bool:
        return self is ReceiptVerificationStatus.VERIFIED

    @property
    def requires_attention(self) -> bool:
        return self in {
            ReceiptVerificationStatus.PARTIALLY_VERIFIED,
            ReceiptVerificationStatus.FAILED,
            ReceiptVerificationStatus.EXPIRED,
            ReceiptVerificationStatus.REVOKED,
        }


@dataclass(frozen=True, slots=True)
class ReceiptId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="receipt id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> "ReceiptId":
        if isinstance(value, cls):
            return value

        return cls(value=value)  # type: ignore[arg-type]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ReceiptPartyId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="receipt party id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> "ReceiptPartyId":
        if isinstance(value, cls):
            return value

        return cls(value=value)  # type: ignore[arg-type]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ReceiptLineItemId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="receipt line-item id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> "ReceiptLineItemId":
        if isinstance(value, cls):
            return value

        return cls(value=value)  # type: ignore[arg-type]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ReceiptAdjustmentId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="receipt adjustment id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> "ReceiptAdjustmentId":
        if isinstance(value, cls):
            return value

        return cls(value=value)  # type: ignore[arg-type]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ReceiptTaxId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="receipt tax id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> "ReceiptTaxId":
        if isinstance(value, cls):
            return value

        return cls(value=value)  # type: ignore[arg-type]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ReceiptMetadata:
    _values: Mapping[str, Any] = field(
        default_factory=dict,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self._values, Mapping):
            raise TypeError(
                "receipt metadata must be a mapping"
            )

        if len(self._values) > _MAX_METADATA_ITEMS:
            raise ValueError(
                "receipt metadata must not contain more "
                f"than {_MAX_METADATA_ITEMS} entries"
            )

        normalized: dict[str, Any] = {}

        for raw_key, raw_value in self._values.items():
            key = _normalize_metadata_key(
                raw_key
            )

            if key in normalized:
                raise ValueError(
                    "receipt metadata contains duplicate "
                    f"normalized key: {key}"
                )

            normalized[key] = (
                _normalize_metadata_value(
                    raw_value,
                    depth=1,
                )
            )

        ordered = {
            key: normalized[key]
            for key in sorted(normalized)
        }

        object.__setattr__(
            self,
            "_values",
            MappingProxyType(ordered),
        )

    @classmethod
    def empty(cls) -> "ReceiptMetadata":
        return cls()

    @classmethod
    def of(
        cls,
        value: object = None,
    ) -> "ReceiptMetadata":
        if isinstance(value, cls):
            return value

        if value is None:
            return cls.empty()

        if not isinstance(value, Mapping):
            raise TypeError(
                "receipt metadata must be a mapping"
            )

        return cls(_values=value)

    def canonical_dict(self) -> dict[str, Any]:
        return deepcopy(dict(self._values))

    def __len__(self) -> int:
        return len(self._values)

    def __bool__(self) -> bool:
        return bool(self._values)

    def __contains__(
        self,
        key: object,
    ) -> bool:
        if not isinstance(key, str):
            return False

        try:
            normalized = _normalize_metadata_key(
                key
            )
        except (TypeError, ValueError):
            return False

        return normalized in self._values

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        normalized = _normalize_metadata_key(
            key
        )

        if normalized not in self._values:
            return deepcopy(default)

        return deepcopy(
            self._values[normalized]
        )


@dataclass(frozen=True, slots=True)
class ReceiptReference:
    reference_type: ReceiptReferenceType
    reference_value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_type",
            ReceiptReferenceType.parse(
                self.reference_type
            ),
        )

        object.__setattr__(
            self,
            "reference_value",
            _normalize_required_text(
                self.reference_value,
                field_name="receipt reference value",
                maximum_length=(
                    _MAX_REFERENCE_VALUE_LENGTH
                ),
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        reference_type: object,
        reference_value: object,
    ) -> "ReceiptReference":
        return cls(
            reference_type=(
                ReceiptReferenceType.parse(
                    reference_type
                )
            ),
            reference_value=(
                _normalize_required_text(
                    reference_value,
                    field_name=(
                        "receipt reference value"
                    ),
                    maximum_length=(
                        _MAX_REFERENCE_VALUE_LENGTH
                    ),
                )
            ),
        )

    @property
    def canonical_key(self) -> tuple[str, str]:
        return (
            self.reference_type.value,
            self.reference_value,
        )

    def canonical_dict(self) -> dict[str, str]:
        return {
            "reference_type": (
                self.reference_type.value
            ),
            "reference_value": (
                self.reference_value
            ),
        }



def _normalize_factory_party(
    value: object,
    *,
    party_type: ReceiptPartyType,
    field_name: str,
    optional: bool,
) -> ReceiptParty | None:
    if value is None:
        if optional:
            return None

        raise TypeError(
            f"{field_name} must not be None"
        )

    if isinstance(value, ReceiptParty):
        if value.party_type is not party_type:
            raise ValueError(
                f"{field_name} party type must be "
                f"{party_type.value}"
            )

        return value

    party_id = ReceiptPartyId.of(value)

    return ReceiptParty(
        party_id=party_id,
        party_type=party_type,
        display_name=party_id.value,
        external_reference=None,
        metadata=ReceiptMetadata.empty(),
    )


@dataclass(
    frozen=True,
    slots=True,
)
class ReceiptIntegrityEvidence:
    evidence_type: ReceiptIntegrityEvidenceType
    value: str
    created_at: datetime
    issuer: str | None = None
    expires_at: datetime | None = None
    metadata: ReceiptMetadata = field(
        default_factory=ReceiptMetadata,
    )

    def __post_init__(self) -> None:
        evidence_type = (
            ReceiptIntegrityEvidenceType.parse(
                self.evidence_type
            )
        )

        value = _normalize_required_text(
            self.value,
            field_name=(
                "receipt integrity evidence value"
            ),
            maximum_length=4096,
        )

        created_at = _normalize_aware_datetime(
            self.created_at,
            field_name=(
                "receipt integrity evidence created at"
            ),
        )

        issuer = _normalize_optional_text(
            self.issuer,
            field_name=(
                "receipt integrity evidence issuer"
            ),
            maximum_length=512,
        )

        expires_at = (
            _normalize_optional_aware_datetime(
                self.expires_at,
                field_name=(
                    "receipt integrity evidence expires at"
                ),
            )
        )

        if (
            expires_at is not None
            and expires_at < created_at
        ):
            raise ValueError(
                "receipt integrity evidence expiry "
                "must not precede creation"
            )

        metadata = ReceiptMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "evidence_type",
            evidence_type,
        )

        object.__setattr__(
            self,
            "value",
            value,
        )

        object.__setattr__(
            self,
            "created_at",
            created_at,
        )

        object.__setattr__(
            self,
            "issuer",
            issuer,
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

    @property
    def is_expiring(self) -> bool:
        return self.expires_at is not None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False

        return (
            self.expires_at
            <= datetime.now(timezone.utc)
        )

    def is_expired_at(
        self,
        value: datetime,
    ) -> bool:
        normalized = _normalize_aware_datetime(
            value,
            field_name=(
                "receipt integrity evidence "
                "evaluation time"
            ),
        )

        if self.expires_at is None:
            return False

        return self.expires_at <= normalized

    def canonical_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "evidence_type": (
                self.evidence_type.value
            ),
            "value": self.value,
            "created_at": (
                self.created_at.isoformat()
            ),
            "issuer": self.issuer,
            "expires_at": (
                None
                if self.expires_at is None
                else self.expires_at.isoformat()
            ),
            "metadata": (
                self.metadata.canonical_dict()
            ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class ReceiptVerificationResult:
    status: ReceiptVerificationStatus
    verified_at: datetime
    verifier: str | None = None
    reason: str | None = None
    integrity_evidence: tuple[
        ReceiptIntegrityEvidence,
        ...,
    ] = ()
    metadata: ReceiptMetadata = field(
        default_factory=ReceiptMetadata,
    )

    def __post_init__(self) -> None:
        status = ReceiptVerificationStatus.parse(
            self.status
        )

        verified_at = _normalize_aware_datetime(
            self.verified_at,
            field_name=(
                "receipt verification result "
                "verified at"
            ),
        )

        verifier = _normalize_optional_text(
            self.verifier,
            field_name=(
                "receipt verification result verifier"
            ),
            maximum_length=512,
        )

        reason = _normalize_optional_text(
            self.reason,
            field_name=(
                "receipt verification result reason"
            ),
            maximum_length=2048,
        )

        if not isinstance(
            self.integrity_evidence,
            (tuple, list),
        ):
            raise TypeError(
                "receipt verification result "
                "integrity evidence must be "
                "a tuple or list"
            )

        normalized_evidence = []

        for value in self.integrity_evidence:
            if not isinstance(
                value,
                ReceiptIntegrityEvidence,
            ):
                raise TypeError(
                    "receipt verification result "
                    "integrity evidence must contain "
                    "ReceiptIntegrityEvidence values"
                )

            normalized_evidence.append(value)

        metadata = ReceiptMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "status",
            status,
        )

        object.__setattr__(
            self,
            "verified_at",
            verified_at,
        )

        object.__setattr__(
            self,
            "verifier",
            verifier,
        )

        object.__setattr__(
            self,
            "reason",
            reason,
        )

        object.__setattr__(
            self,
            "integrity_evidence",
            tuple(normalized_evidence),
        )

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    @property
    def evidence_count(self) -> int:
        return len(self.integrity_evidence)

    def canonical_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "verified_at": (
                self.verified_at.isoformat()
            ),
            "verifier": self.verifier,
            "reason": self.reason,
            "integrity_evidence": [
                value.canonical_dict()
                for value
                in self.integrity_evidence
            ],
            "metadata": (
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class Receipt:
    receipt_id: ReceiptId
    receipt_type: ReceiptType
    status: ReceiptStatus
    format: ReceiptFormat
    issuer: ReceiptParty
    recipient: ReceiptParty | None
    currency_code: str
    line_items: tuple[ReceiptLineItem, ...]
    adjustments: tuple[ReceiptAdjustment, ...]
    taxes: tuple[ReceiptTax, ...]
    monetary_summary: ReceiptMonetarySummary | None
    references: tuple[ReceiptReference, ...]
    integrity_evidence: tuple[str, ...]
    issued_at: datetime | None
    delivered_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
    metadata: ReceiptMetadata

    def __post_init__(self) -> None:
        receipt_id = ReceiptId.of(
            self.receipt_id
        )
        receipt_type = ReceiptType.parse(
            self.receipt_type
        )
        status = ReceiptStatus.parse(
            self.status
        )
        receipt_format = ReceiptFormat.parse(
            self.format
        )
        if not isinstance(
            self.issuer,
            ReceiptParty,
        ):
            raise TypeError(
                "receipt issuer must be a ReceiptParty"
            )

        issuer = self.issuer

        if self.recipient is None:
            recipient = None
        elif isinstance(
            self.recipient,
            ReceiptParty,
        ):
            recipient = self.recipient
        else:
            raise TypeError(
                "receipt recipient must be a ReceiptParty or None"
            )

        if (
            recipient is not None
            and recipient.party_id == issuer.party_id
        ):
            raise ValueError(
                "receipt recipient must differ from issuer"
            )

        if issuer.party_type is not ReceiptPartyType.ISSUER:
            raise ValueError(
                "receipt issuer party type must be issuer"
            )

        currency_code = _normalize_currency_code(
            self.currency_code
        )

        line_items = _normalize_record_tuple(
            self.line_items,
            record_type=ReceiptLineItem,
            identifier_attribute="line_item_id",
            field_name="receipt line items",
        )

        adjustments = _normalize_record_tuple(
            self.adjustments,
            record_type=ReceiptAdjustment,
            identifier_attribute="adjustment_id",
            field_name="receipt adjustments",
        )

        taxes = _normalize_record_tuple(
            self.taxes,
            record_type=ReceiptTax,
            identifier_attribute="tax_id",
            field_name="receipt taxes",
        )

        if self.monetary_summary is None:
            monetary_summary = None
        elif isinstance(
            self.monetary_summary,
            ReceiptMonetarySummary,
        ):
            monetary_summary = self.monetary_summary
        else:
            raise TypeError(
                "receipt monetary summary must be a "
                "ReceiptMonetarySummary or None"
            )

        for item in line_items:
            if item.currency_code != currency_code:
                raise ValueError(
                    "receipt line-item currency must match "
                    "receipt currency"
                )

        for adjustment in adjustments:
            if adjustment.currency_code != currency_code:
                raise ValueError(
                    "receipt adjustment currency must match "
                    "receipt currency"
                )

        for tax in taxes:
            if tax.currency_code != currency_code:
                raise ValueError(
                    "receipt tax currency must match receipt currency"
                )

        if (
            monetary_summary is not None
            and monetary_summary.currency_code != currency_code
        ):
            raise ValueError(
                "receipt monetary summary currency must match "
                "receipt currency"
            )

        references = _normalize_reference_tuple(
            self.references
        )

        integrity_evidence = (
            _normalize_evidence_reference_tuple(
                self.integrity_evidence
            )
        )

        created_at = _normalize_aware_datetime(
            self.created_at,
            field_name="receipt created_at",
        )
        updated_at = _normalize_aware_datetime(
            self.updated_at,
            field_name="receipt updated_at",
        )
        issued_at = _normalize_optional_aware_datetime(
            self.issued_at,
            field_name="receipt issued_at",
        )
        delivered_at = _normalize_optional_aware_datetime(
            self.delivered_at,
            field_name="receipt delivered_at",
        )
        expires_at = _normalize_optional_aware_datetime(
            self.expires_at,
            field_name="receipt expires_at",
        )

        if updated_at < created_at:
            raise ValueError(
                "receipt updated_at must not precede created_at"
            )

        if issued_at is not None and issued_at < created_at:
            raise ValueError(
                "receipt issued_at must not precede created_at"
            )

        if delivered_at is not None:
            if issued_at is None:
                raise ValueError(
                    "receipt delivered_at requires issued_at"
                )

            if delivered_at < issued_at:
                raise ValueError(
                    "receipt delivered_at must not precede issued_at"
                )

        if expires_at is not None and expires_at <= created_at:
            raise ValueError(
                "receipt expires_at must be after created_at"
            )

        if status in {
            ReceiptStatus.DRAFT,
            ReceiptStatus.PREPARED,
            ReceiptStatus.CANCELED,
        }:
            if issued_at is not None:
                raise ValueError(
                    f"{status.value} receipt must not have issued_at"
                )

            if delivered_at is not None:
                raise ValueError(
                    f"{status.value} receipt must not have delivered_at"
                )

        if status.is_issued and issued_at is None:
            raise ValueError(
                f"{status.value} receipt requires issued_at"
            )

        if (
            status is ReceiptStatus.DELIVERED
            and delivered_at is None
        ):
            raise ValueError(
                "delivered receipt requires delivered_at"
            )

        version = _normalize_positive_integer(
            self.version,
            field_name="receipt version",
        )

        metadata = ReceiptMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "receipt_id",
            receipt_id,
        )
        object.__setattr__(
            self,
            "receipt_type",
            receipt_type,
        )
        object.__setattr__(
            self,
            "status",
            status,
        )
        object.__setattr__(
            self,
            "format",
            receipt_format,
        )
        object.__setattr__(
            self,
            "issuer",
            issuer,
        )
        object.__setattr__(
            self,
            "recipient",
            recipient,
        )
        object.__setattr__(
            self,
            "currency_code",
            currency_code,
        )
        object.__setattr__(
            self,
            "line_items",
            line_items,
        )
        object.__setattr__(
            self,
            "adjustments",
            adjustments,
        )
        object.__setattr__(
            self,
            "taxes",
            taxes,
        )
        object.__setattr__(
            self,
            "monetary_summary",
            monetary_summary,
        )
        object.__setattr__(
            self,
            "references",
            references,
        )
        object.__setattr__(
            self,
            "integrity_evidence",
            integrity_evidence,
        )
        object.__setattr__(
            self,
            "issued_at",
            issued_at,
        )
        object.__setattr__(
            self,
            "delivered_at",
            delivered_at,
        )
        object.__setattr__(
            self,
            "expires_at",
            expires_at,
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
        receipt_id: object,
        receipt_type: object,
        format: object,
        issuer: object,
        currency_code: object,
        created_at: object,
        recipient: object = None,
        expires_at: object = None,
        references: tuple[ReceiptReference, ...]
        | list[ReceiptReference] = (),
        metadata: object = None,
    ) -> "Receipt":
        created = _normalize_aware_datetime(
            created_at,
            field_name="receipt created_at",
        )

        return cls(
            receipt_id=ReceiptId.of(
                receipt_id
            ),
            receipt_type=ReceiptType.parse(
                receipt_type
            ),
            status=ReceiptStatus.DRAFT,
            format=ReceiptFormat.parse(
                format
            ),
            issuer=_normalize_factory_party(
                issuer,
                party_type=ReceiptPartyType.ISSUER,
                field_name="receipt issuer",
                optional=False,
            ),
            recipient=_normalize_factory_party(
                recipient,
                party_type=ReceiptPartyType.RECIPIENT,
                field_name="receipt recipient",
                optional=True,
            ),
            currency_code=(
                _normalize_currency_code(
                    currency_code
                )
            ),
            line_items=(),
            adjustments=(),
            taxes=(),
            monetary_summary=None,
            references=_normalize_reference_tuple(
                references
            ),
            integrity_evidence=(),
            issued_at=None,
            delivered_at=None,
            expires_at=(
                _normalize_optional_aware_datetime(
                    expires_at,
                    field_name="receipt expires_at",
                )
            ),
            created_at=created,
            updated_at=created,
            version=1,
            metadata=ReceiptMetadata.of(
                metadata
            ),
        )

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    def _transition(
        self,
        *,
        target_status: ReceiptStatus | str,
        allowed_statuses: tuple[ReceiptStatus, ...],
        updated_at: datetime | None = None,
        issued_at: datetime | None = None,
        delivered_at: datetime | None = None,
        expires_at: datetime | None = None,
        metadata: ReceiptMetadata | Mapping[str, Any] | None = None,
    ) -> "Receipt":
        if self.status not in allowed_statuses:
            allowed = ", ".join(
                status.value
                for status in allowed_statuses
            )

            raise ValueError(
                "receipt status transition from "
                f"{self.status.value} is not allowed; "
                f"expected one of: {allowed}"
            )

        normalized_target = ReceiptStatus.parse(
            target_status
        )

        transition_time = _normalize_aware_datetime(
            updated_at or datetime.now(timezone.utc),
            field_name="receipt transition time",
        )

        if transition_time < self.updated_at:
            raise ValueError(
                "receipt transition time must not precede "
                "the current updated time"
            )

        next_issued_at = (
            self.issued_at
            if issued_at is None
            else _normalize_aware_datetime(
                issued_at,
                field_name="receipt issued at",
            )
        )

        next_delivered_at = (
            self.delivered_at
            if delivered_at is None
            else _normalize_aware_datetime(
                delivered_at,
                field_name="receipt delivered at",
            )
        )

        next_expires_at = (
            self.expires_at
            if expires_at is None
            else _normalize_aware_datetime(
                expires_at,
                field_name="receipt expires at",
            )
        )

        next_metadata = (
            self.metadata
            if metadata is None
            else ReceiptMetadata.of(metadata)
        )

        return replace(
            self,
            status=normalized_target,
            issued_at=next_issued_at,
            delivered_at=next_delivered_at,
            expires_at=next_expires_at,
            updated_at=transition_time,
            version=self.version + 1,
            metadata=next_metadata,
        )

    def prepare(
        self,
        *,
        updated_at: datetime | None = None,
    ) -> "Receipt":
        return self._transition(
            target_status=ReceiptStatus.PREPARED,
            allowed_statuses=(
                ReceiptStatus.DRAFT,
            ),
            updated_at=updated_at,
        )

    def issue(
        self,
        *,
        issued_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> "Receipt":
        effective_issued_at = (
            issued_at
            or updated_at
            or datetime.now(timezone.utc)
        )

        return self._transition(
            target_status=ReceiptStatus.ISSUED,
            allowed_statuses=(
                ReceiptStatus.PREPARED,
            ),
            issued_at=effective_issued_at,
            updated_at=(
                updated_at
                or effective_issued_at
            ),
        )

    def mark_delivered(
        self,
        *,
        delivered_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> "Receipt":
        effective_delivered_at = (
            delivered_at
            or updated_at
            or datetime.now(timezone.utc)
        )

        return self._transition(
            target_status=ReceiptStatus.DELIVERED,
            allowed_statuses=(
                ReceiptStatus.ISSUED,
            ),
            delivered_at=effective_delivered_at,
            updated_at=(
                updated_at
                or effective_delivered_at
            ),
        )

    def cancel(
        self,
        *,
        updated_at: datetime | None = None,
    ) -> "Receipt":
        return self._transition(
            target_status=ReceiptStatus.CANCELED,
            allowed_statuses=(
                ReceiptStatus.DRAFT,
                ReceiptStatus.PREPARED,
            ),
            updated_at=updated_at,
        )

    def void(
        self,
        *,
        updated_at: datetime | None = None,
    ) -> "Receipt":
        return self._transition(
            target_status=ReceiptStatus.VOIDED,
            allowed_statuses=(
                ReceiptStatus.ISSUED,
                ReceiptStatus.DELIVERED,
            ),
            updated_at=updated_at,
        )

    def expire(
        self,
        *,
        expired_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> "Receipt":
        effective_expired_at = (
            expired_at
            or updated_at
            or datetime.now(timezone.utc)
        )

        return self._transition(
            target_status=ReceiptStatus.EXPIRED,
            allowed_statuses=(
                ReceiptStatus.ISSUED,
            ),
            expires_at=effective_expired_at,
            updated_at=(
                updated_at
                or effective_expired_at
            ),
        )

    def supersede(
        self,
        *,
        updated_at: datetime | None = None,
    ) -> "Receipt":
        return self._transition(
            target_status=ReceiptStatus.SUPERSEDED,
            allowed_statuses=(
                ReceiptStatus.ISSUED,
                ReceiptStatus.DELIVERED,
            ),
            updated_at=updated_at,
        )

    def update_metadata(
        self,
        metadata: ReceiptMetadata | Mapping[str, Any],
        *,
        updated_at: datetime | None = None,
    ) -> "Receipt":
        if self.status.is_terminal:
            raise ValueError(
                "terminal receipt metadata cannot be updated"
            )

        return self._transition(
            target_status=self.status,
            allowed_statuses=(
                self.status,
            ),
            metadata=metadata,
            updated_at=updated_at,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id.value,
            "receipt_type": self.receipt_type.value,
            "status": self.status.value,
            "format": self.format.value,
            "issuer": self.issuer.canonical_dict(),
            "recipient": (
                None
                if self.recipient is None
                else self.recipient.canonical_dict()
            ),
            "currency_code": self.currency_code,
            "line_items": [
                item.canonical_dict()
                for item in self.line_items
            ],
            "adjustments": [
                item.canonical_dict()
                for item in self.adjustments
            ],
            "taxes": [
                item.canonical_dict()
                for item in self.taxes
            ],
            "monetary_summary": (
                None
                if self.monetary_summary is None
                else self.monetary_summary.canonical_dict()
            ),
            "references": [
                item.canonical_dict()
                for item in self.references
            ],
            "integrity_evidence": list(
                self.integrity_evidence
            ),
            "issued_at": (
                None
                if self.issued_at is None
                else self.issued_at.isoformat()
            ),
            "delivered_at": (
                None
                if self.delivered_at is None
                else self.delivered_at.isoformat()
            ),
            "expires_at": (
                None
                if self.expires_at is None
                else self.expires_at.isoformat()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReceiptParty:
    party_id: ReceiptPartyId
    party_type: ReceiptPartyType
    display_name: str
    external_reference: str | None
    metadata: ReceiptMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "party_id",
            ReceiptPartyId.of(
                self.party_id
            ),
        )
        object.__setattr__(
            self,
            "party_type",
            ReceiptPartyType.parse(
                self.party_type
            ),
        )
        object.__setattr__(
            self,
            "display_name",
            _normalize_required_text(
                self.display_name,
                field_name="receipt party display name",
                maximum_length=256,
            ),
        )
        object.__setattr__(
            self,
            "external_reference",
            _normalize_optional_text(
                self.external_reference,
                field_name=(
                    "receipt party external reference"
                ),
                maximum_length=256,
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            ReceiptMetadata.of(
                self.metadata
            ),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "party_id": self.party_id.value,
            "party_type": self.party_type.value,
            "display_name": self.display_name,
            "external_reference": self.external_reference,
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReceiptLineItem:
    line_item_id: ReceiptLineItemId
    line_item_type: ReceiptLineItemType
    description: str
    quantity: Any
    unit_amount: Money
    total_amount: Money
    product_reference: str | None
    metadata: ReceiptMetadata

    def __post_init__(self) -> None:
        line_item_id = ReceiptLineItemId.of(
            self.line_item_id
        )
        line_item_type = ReceiptLineItemType.parse(
            self.line_item_type
        )
        description = _normalize_required_text(
            self.description,
            field_name="receipt line-item description",
            maximum_length=512,
        )
        quantity = _require_positive_decimal(
            self.quantity,
            field_name="receipt line-item quantity",
        )
        unit_amount = _require_non_negative_money(
            self.unit_amount,
            field_name="receipt line-item unit amount",
        )
        currency_code = _money_currency(
            unit_amount,
            field_name="receipt line-item unit amount",
        )
        total_amount = _require_non_negative_money(
            self.total_amount,
            field_name="receipt line-item total amount",
            currency_code=currency_code,
        )

        expected_total = (
            _money_amount(
                unit_amount,
                field_name="receipt line-item unit amount",
            )
            * quantity
        )

        if (
            _money_amount(
                total_amount,
                field_name="receipt line-item total amount",
            )
            != expected_total
        ):
            raise ValueError(
                "receipt line-item total amount must equal "
                "quantity multiplied by unit amount"
            )

        object.__setattr__(
            self,
            "line_item_id",
            line_item_id,
        )
        object.__setattr__(
            self,
            "line_item_type",
            line_item_type,
        )
        object.__setattr__(
            self,
            "description",
            description,
        )
        object.__setattr__(
            self,
            "quantity",
            quantity,
        )
        object.__setattr__(
            self,
            "unit_amount",
            unit_amount,
        )
        object.__setattr__(
            self,
            "total_amount",
            total_amount,
        )
        object.__setattr__(
            self,
            "product_reference",
            _normalize_optional_text(
                self.product_reference,
                field_name=(
                    "receipt line-item product reference"
                ),
                maximum_length=256,
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            ReceiptMetadata.of(
                self.metadata
            ),
        )

    @property
    def currency_code(self) -> str:
        return _money_currency(
            self.total_amount,
            field_name="receipt line-item total amount",
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "line_item_id": self.line_item_id.value,
            "line_item_type": self.line_item_type.value,
            "description": self.description,
            "quantity": str(self.quantity),
            "unit_amount": _money_canonical_dict(
                self.unit_amount
            ),
            "total_amount": _money_canonical_dict(
                self.total_amount
            ),
            "product_reference": self.product_reference,
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReceiptAdjustment:
    adjustment_id: ReceiptAdjustmentId
    adjustment_type: ReceiptAdjustmentType
    description: str
    amount: Money
    metadata: ReceiptMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "adjustment_id",
            ReceiptAdjustmentId.of(
                self.adjustment_id
            ),
        )
        object.__setattr__(
            self,
            "adjustment_type",
            ReceiptAdjustmentType.parse(
                self.adjustment_type
            ),
        )
        object.__setattr__(
            self,
            "description",
            _normalize_required_text(
                self.description,
                field_name="receipt adjustment description",
                maximum_length=512,
            ),
        )
        object.__setattr__(
            self,
            "amount",
            _require_non_negative_money(
                self.amount,
                field_name="receipt adjustment amount",
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            ReceiptMetadata.of(
                self.metadata
            ),
        )

    @property
    def currency_code(self) -> str:
        return _money_currency(
            self.amount,
            field_name="receipt adjustment amount",
        )

    @property
    def signed_amount(self):
        amount = _money_amount(
            self.amount,
            field_name="receipt adjustment amount",
        )

        if self.adjustment_type.reduces_total:
            return -amount

        return amount

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "adjustment_id": self.adjustment_id.value,
            "adjustment_type": self.adjustment_type.value,
            "description": self.description,
            "amount": _money_canonical_dict(
                self.amount
            ),
            "signed_amount": str(
                self.signed_amount
            ),
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReceiptTax:
    tax_id: ReceiptTaxId
    tax_type: ReceiptTaxType
    description: str
    jurisdiction: str | None
    rate: Any | None
    amount: Money
    metadata: ReceiptMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tax_id",
            ReceiptTaxId.of(
                self.tax_id
            ),
        )
        object.__setattr__(
            self,
            "tax_type",
            ReceiptTaxType.parse(
                self.tax_type
            ),
        )
        object.__setattr__(
            self,
            "description",
            _normalize_required_text(
                self.description,
                field_name="receipt tax description",
                maximum_length=512,
            ),
        )
        object.__setattr__(
            self,
            "jurisdiction",
            _normalize_optional_text(
                self.jurisdiction,
                field_name="receipt tax jurisdiction",
                maximum_length=128,
            ),
        )

        if self.rate is None:
            normalized_rate = None
        else:
            normalized_rate = _require_positive_decimal(
                self.rate,
                field_name="receipt tax rate",
            )

        object.__setattr__(
            self,
            "rate",
            normalized_rate,
        )
        object.__setattr__(
            self,
            "amount",
            _require_non_negative_money(
                self.amount,
                field_name="receipt tax amount",
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            ReceiptMetadata.of(
                self.metadata
            ),
        )

    @property
    def currency_code(self) -> str:
        return _money_currency(
            self.amount,
            field_name="receipt tax amount",
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "tax_id": self.tax_id.value,
            "tax_type": self.tax_type.value,
            "description": self.description,
            "jurisdiction": self.jurisdiction,
            "rate": (
                None
                if self.rate is None
                else str(self.rate)
            ),
            "amount": _money_canonical_dict(
                self.amount
            ),
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReceiptMonetarySummary:
    currency_code: str
    subtotal: Money
    adjustment_total: Money
    tax_total: Money
    gross_total: Money
    net_total: Money
    paid_amount: Money
    outstanding_amount: Money

    def __post_init__(self) -> None:
        currency_code = _normalize_currency_code(
            self.currency_code
        )

        values = {
            "subtotal": _require_non_negative_money(
                self.subtotal,
                field_name="receipt subtotal",
                currency_code=currency_code,
            ),
            "adjustment_total": _require_non_negative_money(
                self.adjustment_total,
                field_name="receipt adjustment total",
                currency_code=currency_code,
            ),
            "tax_total": _require_non_negative_money(
                self.tax_total,
                field_name="receipt tax total",
                currency_code=currency_code,
            ),
            "gross_total": _require_non_negative_money(
                self.gross_total,
                field_name="receipt gross total",
                currency_code=currency_code,
            ),
            "net_total": _require_non_negative_money(
                self.net_total,
                field_name="receipt net total",
                currency_code=currency_code,
            ),
            "paid_amount": _require_non_negative_money(
                self.paid_amount,
                field_name="receipt paid amount",
                currency_code=currency_code,
            ),
            "outstanding_amount": _require_non_negative_money(
                self.outstanding_amount,
                field_name="receipt outstanding amount",
                currency_code=currency_code,
            ),
        }

        net_amount = _money_amount(
            values["net_total"],
            field_name="receipt net total",
        )
        paid_amount = _money_amount(
            values["paid_amount"],
            field_name="receipt paid amount",
        )
        outstanding_amount = _money_amount(
            values["outstanding_amount"],
            field_name="receipt outstanding amount",
        )

        if paid_amount > net_amount:
            raise ValueError(
                "receipt paid amount must not exceed net total"
            )

        if paid_amount + outstanding_amount != net_amount:
            raise ValueError(
                "receipt paid amount plus outstanding amount "
                "must equal net total"
            )

        object.__setattr__(
            self,
            "currency_code",
            currency_code,
        )

        for name, value in values.items():
            object.__setattr__(
                self,
                name,
                value,
            )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "currency_code": self.currency_code,
            "subtotal": _money_canonical_dict(
                self.subtotal
            ),
            "adjustment_total": _money_canonical_dict(
                self.adjustment_total
            ),
            "tax_total": _money_canonical_dict(
                self.tax_total
            ),
            "gross_total": _money_canonical_dict(
                self.gross_total
            ),
            "net_total": _money_canonical_dict(
                self.net_total
            ),
            "paid_amount": _money_canonical_dict(
                self.paid_amount
            ),
            "outstanding_amount": _money_canonical_dict(
                self.outstanding_amount
            ),
        }
