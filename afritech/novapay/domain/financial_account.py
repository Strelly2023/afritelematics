"""Canonical NovaPay financial-account domain primitives.

A FinancialAccount represents a customer-facing or operational financial
product account. It is distinct from:

- Wallet, which is a stored-value or payment interaction container;
- LedgerAccount, which is an authoritative double-entry accounting account;
- provider-specific bank or mobile-money records;
- journal entries, transactions, settlement, and reconciliation records.

This initial module contains only stable identifiers and enumerations.
The immutable aggregate and integration references are added in later
WP-001E sections.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Final, Self

from .customer import CustomerId
from .ledger_account import LedgerAccountId
from .money import Currency
from .wallet import WalletId


_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$"
)


def _normalize_identifier(
    value: object,
    *,
    field_name: str,
) -> str:
    """Normalize and validate a canonical financial-account identifier."""

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    if not _IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"{field_name} contains unsupported characters"
        )

    return normalized


class FinancialAccountType(str, Enum):
    """Canonical financial-product account categories."""

    CURRENT = "current"
    SAVINGS = "savings"
    MERCHANT = "merchant"
    AGENT_FLOAT = "agent_float"
    SETTLEMENT = "settlement"
    TREASURY = "treasury"
    ESCROW = "escrow"
    PAYROLL = "payroll"
    BENEFIT = "benefit"
    LOAN = "loan"
    INVESTMENT = "investment"
    CLEARING = "clearing"

    @classmethod
    def parse(cls, value: object) -> Self:
        """Return a normalized financial-account type."""

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "financial account type must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "financial account type must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                member.value
                for member in cls
            )

            raise ValueError(
                f"unsupported financial account type: "
                f"{normalized}; supported values: {supported}"
            ) from exc


class FinancialAccountStatus(str, Enum):
    """Lifecycle state of a canonical financial account."""

    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    DORMANT = "dormant"
    CLOSED = "closed"

    @classmethod
    def parse(cls, value: object) -> Self:
        """Return a normalized financial-account status."""

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "financial account status must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "financial account status must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                member.value
                for member in cls
            )

            raise ValueError(
                f"unsupported financial account status: "
                f"{normalized}; supported values: {supported}"
            ) from exc


class FinancialAccountPurpose(str, Enum):
    """Declared business purpose of a financial account."""

    EVERYDAY_PAYMENTS = "everyday_payments"
    SAVINGS = "savings"
    MERCHANT_COLLECTIONS = "merchant_collections"
    AGENT_LIQUIDITY = "agent_liquidity"
    SETTLEMENT = "settlement"
    TREASURY = "treasury"
    ESCROW = "escrow"
    PAYROLL = "payroll"
    BENEFIT_DISBURSEMENT = "benefit_disbursement"
    CREDIT = "credit"
    INVESTMENT = "investment"
    CLEARING = "clearing"

    @classmethod
    def parse(cls, value: object) -> Self:
        """Return a normalized financial-account purpose."""

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "financial account purpose must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "financial account purpose must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                member.value
                for member in cls
            )

            raise ValueError(
                f"unsupported financial account purpose: "
                f"{normalized}; supported values: {supported}"
            ) from exc



_SENSITIVE_KEY_FRAGMENTS: Final[tuple[str, ...]] = (
    "access_token",
    "api_key",
    "authorization",
    "biometric",
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


def _normalize_required_text(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
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


def _normalize_non_negative_decimal(
    value: object,
    *,
    field_name: str,
) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be numeric")

    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
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


def _normalize_optional_positive_integer(
    value: object,
    *,
    field_name: str,
) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field_name} must be an integer"
        )

    if value < 1:
        raise ValueError(
            f"{field_name} must be greater than or equal to 1"
        )

    return value


def _normalize_string_tuple(
    value: object,
    *,
    field_name: str,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(value)
        except TypeError as exc:
            raise TypeError(
                f"{field_name} must be an iterable of strings"
            ) from exc

    normalized: list[str] = []
    seen: set[str] = set()

    for item in values:
        normalized_item = _normalize_required_text(
            item,
            field_name=f"{field_name} item",
            maximum_length=80,
        ).lower()

        if normalized_item in seen:
            raise ValueError(
                f"{field_name} must not contain duplicates"
            )

        seen.add(normalized_item)
        normalized.append(normalized_item)

    return tuple(normalized)


def _normalize_mapping(
    value: object,
    *,
    field_name: str,
    reject_sensitive_keys: bool,
) -> MappingProxyType[str, Any]:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    copied: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(
                f"{field_name} keys must be strings"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                f"{field_name} keys must not be empty"
            )

        lowered_key = normalized_key.casefold()

        if reject_sensitive_keys and any(
            fragment in lowered_key
            for fragment in _SENSITIVE_KEY_FRAGMENTS
        ):
            raise ValueError(
                f"{field_name} contains prohibited sensitive key: "
                f"{normalized_key}"
            )

        copied[normalized_key] = item

    return MappingProxyType(copied)


@dataclass(frozen=True, slots=True)
class FinancialAccountName:
    """Immutable financial-account product and display name."""

    product_name: str
    display_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "product_name",
            _normalize_required_text(
                self.product_name,
                field_name="financial account product name",
                maximum_length=160,
            ),
        )
        object.__setattr__(
            self,
            "display_name",
            _normalize_optional_text(
                self.display_name,
                field_name="financial account display name",
                maximum_length=120,
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
        *,
        display_name: object = None,
    ) -> Self:
        if isinstance(value, cls):
            if display_name is not None:
                raise ValueError(
                    "display name must not be supplied when "
                    "FinancialAccountName already exists"
                )

            return value

        return cls(
            product_name=_normalize_required_text(
                value,
                field_name="financial account product name",
                maximum_length=160,
            ),
            display_name=_normalize_optional_text(
                display_name,
                field_name="financial account display name",
                maximum_length=120,
            ),
        )

    @property
    def effective_display_name(self) -> str:
        return self.display_name or self.product_name

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "product_name": self.product_name,
            "display_name": self.display_name,
        }


@dataclass(frozen=True, slots=True)
class FinancialAccountTerms:
    """Immutable product terms without calculating balances or interest."""

    minimum_balance: Decimal = Decimal("0")
    overdraft_limit: Decimal = Decimal("0")
    interest_rate_percent: Decimal = Decimal("0")
    maintenance_fee: Decimal = Decimal("0")
    notice_period_days: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "minimum_balance",
            _normalize_non_negative_decimal(
                self.minimum_balance,
                field_name="financial account minimum balance",
            ),
        )
        object.__setattr__(
            self,
            "overdraft_limit",
            _normalize_non_negative_decimal(
                self.overdraft_limit,
                field_name="financial account overdraft limit",
            ),
        )
        object.__setattr__(
            self,
            "interest_rate_percent",
            _normalize_non_negative_decimal(
                self.interest_rate_percent,
                field_name="financial account interest rate",
            ),
        )
        object.__setattr__(
            self,
            "maintenance_fee",
            _normalize_non_negative_decimal(
                self.maintenance_fee,
                field_name="financial account maintenance fee",
            ),
        )
        object.__setattr__(
            self,
            "notice_period_days",
            _normalize_optional_positive_integer(
                self.notice_period_days,
                field_name="financial account notice period days",
            ),
        )

        if self.interest_rate_percent > Decimal("100"):
            raise ValueError(
                "financial account interest rate must not exceed 100"
            )

    def canonical_dict(self) -> dict[str, str | int | None]:
        return {
            "minimum_balance": str(self.minimum_balance),
            "overdraft_limit": str(self.overdraft_limit),
            "interest_rate_percent": str(
                self.interest_rate_percent
            ),
            "maintenance_fee": str(self.maintenance_fee),
            "notice_period_days": self.notice_period_days,
        }


@dataclass(frozen=True, slots=True)
class FinancialAccountRestrictions:
    """Immutable product-level operational restrictions."""

    debit_blocked: bool = False
    credit_blocked: bool = False
    cash_withdrawal_blocked: bool = False
    international_transfer_blocked: bool = False
    allowed_channels: tuple[str, ...] = ()
    allowed_countries: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "debit_blocked",
            "credit_blocked",
            "cash_withdrawal_blocked",
            "international_transfer_blocked",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, bool):
                raise TypeError(
                    f"financial account {field_name.replace('_', ' ')} "
                    "must be a boolean"
                )

        normalized_channels = _normalize_string_tuple(
            self.allowed_channels,
            field_name="financial account allowed channels",
        )
        normalized_countries = _normalize_string_tuple(
            self.allowed_countries,
            field_name="financial account allowed countries",
        )

        for country in normalized_countries:
            if len(country) != 2 or not country.isalpha():
                raise ValueError(
                    "financial account allowed countries must contain "
                    "two-letter country codes"
                )

        object.__setattr__(
            self,
            "allowed_channels",
            normalized_channels,
        )
        object.__setattr__(
            self,
            "allowed_countries",
            tuple(
                country.upper()
                for country in normalized_countries
            ),
        )

    @property
    def fully_blocked(self) -> bool:
        return self.debit_blocked and self.credit_blocked

    def canonical_dict(
        self,
    ) -> dict[str, bool | list[str]]:
        return {
            "debit_blocked": self.debit_blocked,
            "credit_blocked": self.credit_blocked,
            "cash_withdrawal_blocked": (
                self.cash_withdrawal_blocked
            ),
            "international_transfer_blocked": (
                self.international_transfer_blocked
            ),
            "allowed_channels": list(self.allowed_channels),
            "allowed_countries": list(self.allowed_countries),
        }


@dataclass(frozen=True, slots=True)
class FinancialAccountMetadata:
    """Immutable non-sensitive financial-account metadata."""

    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            _normalize_mapping(
                self.values,
                field_name="financial account metadata",
                reject_sensitive_keys=True,
            ),
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_mapping(
                value,
                field_name="financial account metadata",
                reject_sensitive_keys=True,
            )
        )

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        normalized_key = _normalize_required_text(
            key,
            field_name="financial account metadata key",
            maximum_length=120,
        )

        return self.values.get(normalized_key, default)

    def with_value(
        self,
        key: str,
        value: Any,
    ) -> Self:
        normalized_key = _normalize_required_text(
            key,
            field_name="financial account metadata key",
            maximum_length=120,
        )

        updated = dict(self.values)
        updated[normalized_key] = value

        return type(self)(updated)

    def without(self, key: str) -> Self:
        normalized_key = _normalize_required_text(
            key,
            field_name="financial account metadata key",
            maximum_length=120,
        )

        updated = dict(self.values)
        updated.pop(normalized_key, None)

        return type(self)(updated)

    def canonical_dict(self) -> MappingProxyType[str, Any]:
        return MappingProxyType(dict(self.values))


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


def _normalize_version(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "financial account version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "financial account version must be greater than or equal to 1"
        )

    return value


def _normalize_optional_wallet_id(
    value: object,
) -> WalletId | None:
    if value is None:
        return None

    return WalletId.of(value)


def _normalize_optional_ledger_account_id(
    value: object,
) -> LedgerAccountId | None:
    if value is None:
        return None

    return LedgerAccountId.of(value)

@dataclass(frozen=True, slots=True, order=True)
class FinancialAccountId:
    """Immutable canonical NovaPay financial-account identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="financial account id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        """Return an existing identifier or create a normalized one."""

        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="financial account id",
            )
        )

    def canonical(self) -> str:
        """Return the canonical scalar identifier."""

        return self.value

    def canonical_dict(self) -> dict[str, str]:
        """Return deterministic structured serialization."""

        return {
            "value": self.value,
        }

    def __str__(self) -> str:
        return self.value



@dataclass(frozen=True, slots=True)
class FinancialAccount:
    """Immutable canonical NovaPay financial-product account.

    This aggregate represents account ownership, classification, terms,
    restrictions, and links to wallet and ledger identities.

    It does not store or calculate authoritative balances.
    """

    account_id: FinancialAccountId
    customer_id: CustomerId
    tenant_id: str
    account_type: FinancialAccountType
    purpose: FinancialAccountPurpose
    status: FinancialAccountStatus
    currency: Currency
    name: FinancialAccountName
    wallet_id: WalletId | None = None
    ledger_account_id: LedgerAccountId | None = None
    terms: FinancialAccountTerms = field(
        default_factory=FinancialAccountTerms
    )
    restrictions: FinancialAccountRestrictions = field(
        default_factory=FinancialAccountRestrictions
    )
    metadata: FinancialAccountMetadata = field(
        default_factory=FinancialAccountMetadata
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_account_id = FinancialAccountId.of(
            self.account_id
        )
        normalized_customer_id = CustomerId.of(
            self.customer_id
        )
        normalized_tenant_id = _normalize_identifier(
            self.tenant_id,
            field_name="financial account tenant id",
        )
        normalized_account_type = FinancialAccountType.parse(
            self.account_type
        )
        normalized_purpose = FinancialAccountPurpose.parse(
            self.purpose
        )
        normalized_status = FinancialAccountStatus.parse(
            self.status
        )

        if not isinstance(self.currency, Currency):
            raise TypeError(
                "financial account currency must be a Currency"
            )

        if not isinstance(self.name, FinancialAccountName):
            raise TypeError(
                "financial account name must be "
                "a FinancialAccountName"
            )

        normalized_wallet_id = _normalize_optional_wallet_id(
            self.wallet_id
        )
        normalized_ledger_account_id = (
            _normalize_optional_ledger_account_id(
                self.ledger_account_id
            )
        )

        normalized_terms = (
            self.terms
            if isinstance(self.terms, FinancialAccountTerms)
            else FinancialAccountTerms(**self.terms)
            if isinstance(self.terms, Mapping)
            else None
        )

        if normalized_terms is None:
            raise TypeError(
                "financial account terms must be "
                "FinancialAccountTerms or a mapping"
            )

        normalized_restrictions = (
            self.restrictions
            if isinstance(
                self.restrictions,
                FinancialAccountRestrictions,
            )
            else FinancialAccountRestrictions(
                **self.restrictions
            )
            if isinstance(self.restrictions, Mapping)
            else None
        )

        if normalized_restrictions is None:
            raise TypeError(
                "financial account restrictions must be "
                "FinancialAccountRestrictions or a mapping"
            )

        normalized_metadata = FinancialAccountMetadata.of(
            self.metadata
        )

        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name="financial account created at",
        )
        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name="financial account updated at",
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "financial account updated at must not be earlier "
                "than created at"
            )

        normalized_version = _normalize_version(
            self.version
        )

        if (
            normalized_account_type
            in {
                FinancialAccountType.CURRENT,
                FinancialAccountType.SAVINGS,
                FinancialAccountType.MERCHANT,
                FinancialAccountType.AGENT_FLOAT,
                FinancialAccountType.PAYROLL,
                FinancialAccountType.BENEFIT,
            }
            and normalized_wallet_id is None
        ):
            raise ValueError(
                f"{normalized_account_type.value} financial account "
                "requires a wallet id"
            )

        if (
            normalized_account_type
            in {
                FinancialAccountType.SETTLEMENT,
                FinancialAccountType.TREASURY,
                FinancialAccountType.ESCROW,
                FinancialAccountType.CLEARING,
                FinancialAccountType.LOAN,
                FinancialAccountType.INVESTMENT,
            }
            and normalized_ledger_account_id is None
        ):
            raise ValueError(
                f"{normalized_account_type.value} financial account "
                "requires a ledger account id"
            )

        expected_purposes = {
            FinancialAccountType.CURRENT: {
                FinancialAccountPurpose.EVERYDAY_PAYMENTS,
            },
            FinancialAccountType.SAVINGS: {
                FinancialAccountPurpose.SAVINGS,
            },
            FinancialAccountType.MERCHANT: {
                FinancialAccountPurpose.MERCHANT_COLLECTIONS,
            },
            FinancialAccountType.AGENT_FLOAT: {
                FinancialAccountPurpose.AGENT_LIQUIDITY,
            },
            FinancialAccountType.SETTLEMENT: {
                FinancialAccountPurpose.SETTLEMENT,
            },
            FinancialAccountType.TREASURY: {
                FinancialAccountPurpose.TREASURY,
            },
            FinancialAccountType.ESCROW: {
                FinancialAccountPurpose.ESCROW,
            },
            FinancialAccountType.PAYROLL: {
                FinancialAccountPurpose.PAYROLL,
            },
            FinancialAccountType.BENEFIT: {
                FinancialAccountPurpose.BENEFIT_DISBURSEMENT,
            },
            FinancialAccountType.LOAN: {
                FinancialAccountPurpose.CREDIT,
            },
            FinancialAccountType.INVESTMENT: {
                FinancialAccountPurpose.INVESTMENT,
            },
            FinancialAccountType.CLEARING: {
                FinancialAccountPurpose.CLEARING,
            },
        }

        if normalized_purpose not in expected_purposes[
            normalized_account_type
        ]:
            raise ValueError(
                "financial account purpose is incompatible "
                f"with account type {normalized_account_type.value}"
            )

        if (
            normalized_account_type
            is not FinancialAccountType.CURRENT
            and normalized_terms.overdraft_limit
            > Decimal("0")
        ):
            raise ValueError(
                "only current financial accounts may define "
                "an overdraft limit"
            )

        if (
            normalized_account_type
            is FinancialAccountType.SAVINGS
            and normalized_terms.notice_period_days is None
            and normalized_terms.interest_rate_percent
            == Decimal("0")
        ):
            raise ValueError(
                "savings financial account requires an interest "
                "rate or notice period"
            )

        if (
            normalized_status
            is FinancialAccountStatus.CLOSED
            and not normalized_restrictions.fully_blocked
        ):
            raise ValueError(
                "closed financial account must block both "
                "debits and credits"
            )

        object.__setattr__(
            self,
            "account_id",
            normalized_account_id,
        )
        object.__setattr__(
            self,
            "customer_id",
            normalized_customer_id,
        )
        object.__setattr__(
            self,
            "tenant_id",
            normalized_tenant_id,
        )
        object.__setattr__(
            self,
            "account_type",
            normalized_account_type,
        )
        object.__setattr__(
            self,
            "purpose",
            normalized_purpose,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "wallet_id",
            normalized_wallet_id,
        )
        object.__setattr__(
            self,
            "ledger_account_id",
            normalized_ledger_account_id,
        )
        object.__setattr__(
            self,
            "terms",
            normalized_terms,
        )
        object.__setattr__(
            self,
            "restrictions",
            normalized_restrictions,
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
        account_id: object,
        customer_id: object,
        tenant_id: object,
        account_type: object,
        purpose: object,
        currency: Currency,
        name: FinancialAccountName,
        wallet_id: object = None,
        ledger_account_id: object = None,
        status: object = FinancialAccountStatus.PENDING,
        terms: object = None,
        restrictions: object = None,
        metadata: object = None,
        occurred_at: datetime | None = None,
    ) -> Self:
        timestamp = (
            datetime.now(timezone.utc)
            if occurred_at is None
            else _normalize_datetime(
                occurred_at,
                field_name="financial account occurred at",
            )
        )

        normalized_terms = (
            FinancialAccountTerms()
            if terms is None
            else terms
        )
        normalized_restrictions = (
            FinancialAccountRestrictions()
            if restrictions is None
            else restrictions
        )

        return cls(
            account_id=FinancialAccountId.of(account_id),
            customer_id=CustomerId.of(customer_id),
            tenant_id=_normalize_identifier(
                tenant_id,
                field_name="financial account tenant id",
            ),
            account_type=FinancialAccountType.parse(
                account_type
            ),
            purpose=FinancialAccountPurpose.parse(
                purpose
            ),
            status=FinancialAccountStatus.parse(status),
            currency=currency,
            name=name,
            wallet_id=_normalize_optional_wallet_id(
                wallet_id
            ),
            ledger_account_id=(
                _normalize_optional_ledger_account_id(
                    ledger_account_id
                )
            ),
            terms=normalized_terms,
            restrictions=normalized_restrictions,
            metadata=FinancialAccountMetadata.of(metadata),
            created_at=timestamp,
            updated_at=timestamp,
            version=1,
        )

    def _normalize_change_time(
        self,
        occurred_at: datetime | None,
    ) -> datetime:
        timestamp = (
            datetime.now(timezone.utc)
            if occurred_at is None
            else _normalize_datetime(
                occurred_at,
                field_name="financial account occurred at",
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "financial account occurred at must not be earlier "
                "than current updated at"
            )

        return timestamp

    def _require_open(self) -> None:
        if self.status is FinancialAccountStatus.CLOSED:
            raise ValueError(
                "closed financial account does not permit "
                "further changes"
            )

    def _metadata_with_reason(
        self,
        *,
        action: str,
        reason: object = None,
    ) -> FinancialAccountMetadata:
        updated = dict(self.metadata.values)
        updated["lifecycle_action"] = action

        if reason is not None:
            updated["lifecycle_reason"] = (
                _normalize_required_text(
                    reason,
                    field_name=(
                        "financial account lifecycle reason"
                    ),
                    maximum_length=500,
                )
            )

        return FinancialAccountMetadata.of(updated)

    def _with_change(
        self,
        *,
        occurred_at: datetime | None,
        status: FinancialAccountStatus | None = None,
        name: FinancialAccountName | None = None,
        wallet_id: WalletId | None = None,
        preserve_wallet: bool = True,
        ledger_account_id: LedgerAccountId | None = None,
        preserve_ledger_account: bool = True,
        terms: FinancialAccountTerms | None = None,
        restrictions: FinancialAccountRestrictions | None = None,
        metadata: FinancialAccountMetadata | None = None,
    ) -> Self:
        timestamp = self._normalize_change_time(
            occurred_at
        )

        return replace(
            self,
            status=self.status if status is None else status,
            name=self.name if name is None else name,
            wallet_id=(
                self.wallet_id
                if preserve_wallet
                else wallet_id
            ),
            ledger_account_id=(
                self.ledger_account_id
                if preserve_ledger_account
                else ledger_account_id
            ),
            terms=self.terms if terms is None else terms,
            restrictions=(
                self.restrictions
                if restrictions is None
                else restrictions
            ),
            metadata=(
                self.metadata
                if metadata is None
                else metadata
            ),
            updated_at=timestamp,
            version=self.version + 1,
        )

    def activate(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Activate a pending financial account."""

        self._require_open()

        if self.status is not FinancialAccountStatus.PENDING:
            raise ValueError(
                "financial account activation requires "
                "pending status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=FinancialAccountStatus.ACTIVE,
            metadata=self._metadata_with_reason(
                action="activate",
                reason=reason,
            ),
        )

    def restrict(
        self,
        *,
        reason: object,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Restrict an active financial account."""

        self._require_open()

        if self.status is not FinancialAccountStatus.ACTIVE:
            raise ValueError(
                "financial account restriction requires "
                "active status"
            )

        restrictions = replace(
            self.restrictions,
            debit_blocked=True,
        )

        return self._with_change(
            occurred_at=occurred_at,
            status=FinancialAccountStatus.RESTRICTED,
            restrictions=restrictions,
            metadata=self._metadata_with_reason(
                action="restrict",
                reason=reason,
            ),
        )

    def suspend(
        self,
        *,
        reason: object,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Suspend an active or restricted financial account."""

        self._require_open()

        if self.status not in {
            FinancialAccountStatus.ACTIVE,
            FinancialAccountStatus.RESTRICTED,
        }:
            raise ValueError(
                "financial account suspension requires "
                "active or restricted status"
            )

        restrictions = replace(
            self.restrictions,
            debit_blocked=True,
            credit_blocked=True,
        )

        return self._with_change(
            occurred_at=occurred_at,
            status=FinancialAccountStatus.SUSPENDED,
            restrictions=restrictions,
            metadata=self._metadata_with_reason(
                action="suspend",
                reason=reason,
            ),
        )

    def mark_dormant(
        self,
        *,
        reason: object = None,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Mark an active financial account dormant."""

        self._require_open()

        if self.status is not FinancialAccountStatus.ACTIVE:
            raise ValueError(
                "financial account dormancy requires active status"
            )

        restrictions = replace(
            self.restrictions,
            debit_blocked=True,
        )

        return self._with_change(
            occurred_at=occurred_at,
            status=FinancialAccountStatus.DORMANT,
            restrictions=restrictions,
            metadata=self._metadata_with_reason(
                action="mark_dormant",
                reason=reason,
            ),
        )

    def reactivate(
        self,
        *,
        reason: object = None,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Return a restricted, suspended, or dormant account to active."""

        self._require_open()

        if self.status not in {
            FinancialAccountStatus.RESTRICTED,
            FinancialAccountStatus.SUSPENDED,
            FinancialAccountStatus.DORMANT,
        }:
            raise ValueError(
                "financial account reactivation requires "
                "restricted, suspended, or dormant status"
            )

        restrictions = replace(
            self.restrictions,
            debit_blocked=False,
            credit_blocked=False,
        )

        return self._with_change(
            occurred_at=occurred_at,
            status=FinancialAccountStatus.ACTIVE,
            restrictions=restrictions,
            metadata=self._metadata_with_reason(
                action="reactivate",
                reason=reason,
            ),
        )

    def close(
        self,
        *,
        reason: object,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Close a non-closed financial account permanently."""

        self._require_open()

        restrictions = replace(
            self.restrictions,
            debit_blocked=True,
            credit_blocked=True,
            cash_withdrawal_blocked=True,
            international_transfer_blocked=True,
        )

        return self._with_change(
            occurred_at=occurred_at,
            status=FinancialAccountStatus.CLOSED,
            restrictions=restrictions,
            metadata=self._metadata_with_reason(
                action="close",
                reason=reason,
            ),
        )

    def rename(
        self,
        name: FinancialAccountName,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Return a new account with a changed name."""

        self._require_open()

        if not isinstance(name, FinancialAccountName):
            raise TypeError(
                "financial account name must be "
                "a FinancialAccountName"
            )

        if name == self.name:
            raise ValueError(
                "financial account name update must change name"
            )

        return self._with_change(
            occurred_at=occurred_at,
            name=name,
        )

    def change_terms(
        self,
        terms: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Return a new account with changed product terms."""

        self._require_open()

        normalized_terms = (
            terms
            if isinstance(terms, FinancialAccountTerms)
            else FinancialAccountTerms(**terms)
            if isinstance(terms, Mapping)
            else None
        )

        if normalized_terms is None:
            raise TypeError(
                "financial account terms must be "
                "FinancialAccountTerms or a mapping"
            )

        if normalized_terms == self.terms:
            raise ValueError(
                "financial account terms update must change terms"
            )

        return self._with_change(
            occurred_at=occurred_at,
            terms=normalized_terms,
        )

    def change_restrictions(
        self,
        restrictions: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Return a new account with changed restrictions."""

        self._require_open()

        normalized_restrictions = (
            restrictions
            if isinstance(
                restrictions,
                FinancialAccountRestrictions,
            )
            else FinancialAccountRestrictions(
                **restrictions
            )
            if isinstance(restrictions, Mapping)
            else None
        )

        if normalized_restrictions is None:
            raise TypeError(
                "financial account restrictions must be "
                "FinancialAccountRestrictions or a mapping"
            )

        if normalized_restrictions == self.restrictions:
            raise ValueError(
                "financial account restriction update "
                "must change restrictions"
            )

        return self._with_change(
            occurred_at=occurred_at,
            restrictions=normalized_restrictions,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace non-sensitive account metadata immutably."""

        self._require_open()
        normalized_metadata = FinancialAccountMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "financial account metadata update "
                "must change metadata"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized_metadata,
        )

    def link_wallet(
        self,
        wallet_id: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Link or replace the account wallet reference."""

        self._require_open()
        normalized_wallet_id = WalletId.of(wallet_id)

        if normalized_wallet_id == self.wallet_id:
            raise ValueError(
                "financial account wallet update "
                "must change wallet id"
            )

        return self._with_change(
            occurred_at=occurred_at,
            wallet_id=normalized_wallet_id,
            preserve_wallet=False,
        )

    def link_ledger_account(
        self,
        ledger_account_id: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Link or replace the authoritative ledger-account reference."""

        self._require_open()
        normalized_ledger_id = LedgerAccountId.of(
            ledger_account_id
        )

        if normalized_ledger_id == self.ledger_account_id:
            raise ValueError(
                "financial account ledger update "
                "must change ledger account id"
            )

        return self._with_change(
            occurred_at=occurred_at,
            ledger_account_id=normalized_ledger_id,
            preserve_ledger_account=False,
        )

    def canonical_dict(self) -> dict[str, Any]:
        """Return deterministic account serialization."""

        return {
            "account_id": self.account_id.value,
            "customer_id": self.customer_id.value,
            "tenant_id": self.tenant_id,
            "account_type": self.account_type.value,
            "purpose": self.purpose.value,
            "status": self.status.value,
            "currency": self.currency.code,
            "name": self.name.canonical_dict(),
            "wallet_id": (
                None
                if self.wallet_id is None
                else self.wallet_id.value
            ),
            "ledger_account_id": (
                None
                if self.ledger_account_id is None
                else self.ledger_account_id.value
            ),
            "terms": self.terms.canonical_dict(),
            "restrictions": self.restrictions.canonical_dict(),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


__all__ = [
    "FinancialAccount",
    "FinancialAccountId",
    "FinancialAccountMetadata",
    "FinancialAccountName",
    "FinancialAccountPurpose",
    "FinancialAccountRestrictions",
    "FinancialAccountStatus",
    "FinancialAccountTerms",
    "FinancialAccountType",
]
