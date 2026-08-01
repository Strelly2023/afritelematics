"""Canonical NovaPay ledger-account domain models.

This module defines immutable ledger-account identities, classifications,
lifecycle states, metadata, and aggregate invariants.

It does not:

- post journal entries;
- calculate authoritative balances;
- mutate ledger records;
- execute transfers;
- perform settlement;
- call payment providers;
- replace the existing AfriPay runtime.

Authoritative balances remain derived from balanced ledger entries.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
import re

from .money import Currency


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$"
)

_ACCOUNT_CODE_PATTERN = re.compile(
    r"^[A-Z0-9][A-Z0-9._:-]{1,63}$"
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


def _normalize_account_code(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("ledger account code must be a string")

    normalized = value.strip().upper()

    if not normalized:
        raise ValueError(
            "ledger account code must not be empty"
        )

    if not _ACCOUNT_CODE_PATTERN.fullmatch(normalized):
        raise ValueError(
            "ledger account code must be 2 to 64 characters and "
            "contain only uppercase letters, numbers, periods, "
            "underscores, colons, or hyphens"
        )

    return normalized


def _normalize_name(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("ledger account name must be a string")

    normalized = " ".join(value.split())

    if not normalized:
        raise ValueError(
            "ledger account name must not be empty"
        )

    if len(normalized) > 160:
        raise ValueError(
            "ledger account name must not exceed 160 characters"
        )

    return normalized


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


def _freeze_metadata(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise TypeError(
            "ledger account metadata must be a mapping"
        )

    copied: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(
                "ledger account metadata keys must be strings"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "ledger account metadata keys must not be empty"
            )

        copied[normalized_key] = item

    return MappingProxyType(copied)


class LedgerAccountType(str, Enum):
    """Canonical double-entry ledger account classifications."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"
    CONTRA_ASSET = "contra_asset"
    CONTRA_LIABILITY = "contra_liability"
    CONTRA_EQUITY = "contra_equity"
    CONTRA_REVENUE = "contra_revenue"
    CONTRA_EXPENSE = "contra_expense"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> LedgerAccountType:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "ledger account type must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "ledger account type must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                item.value for item in cls
            )

            raise ValueError(
                f"unsupported ledger account type: {normalized}; "
                f"supported values: {supported}"
            ) from exc


class NormalBalanceSide(str, Enum):
    """Normal balance side for a double-entry ledger account."""

    DEBIT = "debit"
    CREDIT = "credit"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> NormalBalanceSide:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "normal balance side must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "normal balance side must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported normal balance side: {normalized}; "
                "supported values: debit, credit"
            ) from exc


class LedgerAccountStatus(str, Enum):
    """Canonical ledger-account lifecycle states."""

    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    CLOSED = "closed"

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> LedgerAccountStatus:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "ledger account status must be a string"
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "ledger account status must not be empty"
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                item.value for item in cls
            )

            raise ValueError(
                f"unsupported ledger account status: {normalized}; "
                f"supported values: {supported}"
            ) from exc


_DEFAULT_NORMAL_BALANCE: Mapping[
    LedgerAccountType,
    NormalBalanceSide,
] = MappingProxyType(
    {
        LedgerAccountType.ASSET: NormalBalanceSide.DEBIT,
        LedgerAccountType.LIABILITY: NormalBalanceSide.CREDIT,
        LedgerAccountType.EQUITY: NormalBalanceSide.CREDIT,
        LedgerAccountType.REVENUE: NormalBalanceSide.CREDIT,
        LedgerAccountType.EXPENSE: NormalBalanceSide.DEBIT,
        LedgerAccountType.CONTRA_ASSET: NormalBalanceSide.CREDIT,
        LedgerAccountType.CONTRA_LIABILITY: NormalBalanceSide.DEBIT,
        LedgerAccountType.CONTRA_EQUITY: NormalBalanceSide.DEBIT,
        LedgerAccountType.CONTRA_REVENUE: NormalBalanceSide.DEBIT,
        LedgerAccountType.CONTRA_EXPENSE: NormalBalanceSide.CREDIT,
    }
)


_ALLOWED_TRANSITIONS: Mapping[
    LedgerAccountStatus,
    frozenset[LedgerAccountStatus],
] = MappingProxyType(
    {
        LedgerAccountStatus.PENDING: frozenset(
            {
                LedgerAccountStatus.ACTIVE,
                LedgerAccountStatus.RESTRICTED,
                LedgerAccountStatus.CLOSED,
            }
        ),
        LedgerAccountStatus.ACTIVE: frozenset(
            {
                LedgerAccountStatus.RESTRICTED,
                LedgerAccountStatus.SUSPENDED,
                LedgerAccountStatus.CLOSED,
            }
        ),
        LedgerAccountStatus.RESTRICTED: frozenset(
            {
                LedgerAccountStatus.ACTIVE,
                LedgerAccountStatus.SUSPENDED,
                LedgerAccountStatus.CLOSED,
            }
        ),
        LedgerAccountStatus.SUSPENDED: frozenset(
            {
                LedgerAccountStatus.ACTIVE,
                LedgerAccountStatus.RESTRICTED,
                LedgerAccountStatus.CLOSED,
            }
        ),
        LedgerAccountStatus.CLOSED: frozenset(),
    }
)


@dataclass(frozen=True, slots=True, order=True)
class LedgerAccountId:
    """Strongly typed canonical ledger-account identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="ledger account id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> LedgerAccountId:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="ledger account id",
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class LedgerAccountMetadata:
    """Immutable ledger-account metadata wrapper."""

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
            | LedgerAccountMetadata
            | None
        ),
    ) -> LedgerAccountMetadata:
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
    ) -> LedgerAccountMetadata:
        if not isinstance(key, str):
            raise TypeError(
                "ledger account metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "ledger account metadata key must not be empty"
            )

        updated = dict(self.values)
        updated[normalized_key] = value

        return LedgerAccountMetadata(updated)

    def without(
        self,
        key: str,
    ) -> LedgerAccountMetadata:
        if not isinstance(key, str):
            raise TypeError(
                "ledger account metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "ledger account metadata key must not be empty"
            )

        updated = dict(self.values)
        updated.pop(normalized_key, None)

        return LedgerAccountMetadata(updated)


@dataclass(frozen=True, slots=True)
class LedgerAccount:
    """Immutable canonical NovaPay ledger-account aggregate.

    The aggregate defines the identity and classification of an account
    used by the double-entry ledger.

    It intentionally does not contain a mutable or authoritative balance.
    Account balances must be calculated from balanced ledger entries or
    maintained as explicitly non-authoritative projections.
    """

    account_id: LedgerAccountId
    account_code: str
    name: str
    account_type: LedgerAccountType
    normal_balance: NormalBalanceSide
    status: LedgerAccountStatus
    currency: Currency
    created_at: datetime
    updated_at: datetime
    owner_id: str | None = None
    wallet_id: str | None = None
    tenant_id: str | None = None
    parent_account_id: LedgerAccountId | None = None
    metadata: LedgerAccountMetadata = field(
        default_factory=LedgerAccountMetadata
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_account_id = LedgerAccountId.of(
            self.account_id
        )

        normalized_account_code = _normalize_account_code(
            self.account_code
        )

        normalized_name = _normalize_name(self.name)

        normalized_account_type = LedgerAccountType.parse(
            self.account_type
        )

        normalized_normal_balance = NormalBalanceSide.parse(
            self.normal_balance
        )

        expected_normal_balance = _DEFAULT_NORMAL_BALANCE[
            normalized_account_type
        ]

        if normalized_normal_balance is not expected_normal_balance:
            raise ValueError(
                f"ledger account type "
                f"{normalized_account_type.value} requires "
                f"{expected_normal_balance.value} normal balance"
            )

        normalized_status = LedgerAccountStatus.parse(
            self.status
        )

        normalized_currency = Currency.of(self.currency)

        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name="ledger account created_at",
        )

        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name="ledger account updated_at",
        )

        normalized_owner_id = _normalize_optional_identifier(
            self.owner_id,
            field_name="ledger account owner id",
        )

        normalized_wallet_id = _normalize_optional_identifier(
            self.wallet_id,
            field_name="ledger account wallet id",
        )

        normalized_tenant_id = _normalize_optional_identifier(
            self.tenant_id,
            field_name="ledger account tenant id",
        )

        normalized_parent_account_id = (
            None
            if self.parent_account_id is None
            else LedgerAccountId.of(self.parent_account_id)
        )

        if normalized_parent_account_id == normalized_account_id:
            raise ValueError(
                "ledger account cannot be its own parent"
            )

        normalized_metadata = LedgerAccountMetadata.of(
            self.metadata
        )

        if isinstance(self.version, bool):
            raise TypeError(
                "ledger account version must be an integer"
            )

        if not isinstance(self.version, int):
            raise TypeError(
                "ledger account version must be an integer"
            )

        if self.version < 1:
            raise ValueError(
                "ledger account version must be greater than zero"
            )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "ledger account updated_at must not be before "
                "created_at"
            )

        object.__setattr__(
            self,
            "account_id",
            normalized_account_id,
        )
        object.__setattr__(
            self,
            "account_code",
            normalized_account_code,
        )
        object.__setattr__(
            self,
            "name",
            normalized_name,
        )
        object.__setattr__(
            self,
            "account_type",
            normalized_account_type,
        )
        object.__setattr__(
            self,
            "normal_balance",
            normalized_normal_balance,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "currency",
            normalized_currency,
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
            "owner_id",
            normalized_owner_id,
        )
        object.__setattr__(
            self,
            "wallet_id",
            normalized_wallet_id,
        )
        object.__setattr__(
            self,
            "tenant_id",
            normalized_tenant_id,
        )
        object.__setattr__(
            self,
            "parent_account_id",
            normalized_parent_account_id,
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
        account_id: object,
        account_code: object,
        name: object,
        account_type: object,
        currency: object,
        owner_id: object | None = None,
        wallet_id: object | None = None,
        tenant_id: object | None = None,
        parent_account_id: object | None = None,
        metadata: (
            Mapping[str, Any]
            | LedgerAccountMetadata
            | None
        ) = None,
        created_at: datetime | None = None,
    ) -> LedgerAccount:
        normalized_type = LedgerAccountType.parse(
            account_type
        )

        timestamp = (
            _utc_now()
            if created_at is None
            else _normalize_datetime(
                created_at,
                field_name="ledger account created_at",
            )
        )

        return cls(
            account_id=LedgerAccountId.of(account_id),
            account_code=_normalize_account_code(
                account_code
            ),
            name=_normalize_name(name),
            account_type=normalized_type,
            normal_balance=_DEFAULT_NORMAL_BALANCE[
                normalized_type
            ],
            status=LedgerAccountStatus.PENDING,
            currency=Currency.of(currency),
            created_at=timestamp,
            updated_at=timestamp,
            owner_id=_normalize_optional_identifier(
                owner_id,
                field_name="ledger account owner id",
            ),
            wallet_id=_normalize_optional_identifier(
                wallet_id,
                field_name="ledger account wallet id",
            ),
            tenant_id=_normalize_optional_identifier(
                tenant_id,
                field_name="ledger account tenant id",
            ),
            parent_account_id=(
                None
                if parent_account_id is None
                else LedgerAccountId.of(parent_account_id)
            ),
            metadata=LedgerAccountMetadata.of(metadata),
            version=1,
        )

    @property
    def is_pending(self) -> bool:
        return self.status is LedgerAccountStatus.PENDING

    @property
    def is_active(self) -> bool:
        return self.status is LedgerAccountStatus.ACTIVE

    @property
    def is_restricted(self) -> bool:
        return self.status is LedgerAccountStatus.RESTRICTED

    @property
    def is_suspended(self) -> bool:
        return self.status is LedgerAccountStatus.SUSPENDED

    @property
    def is_closed(self) -> bool:
        return self.status is LedgerAccountStatus.CLOSED

    @property
    def can_post(self) -> bool:
        return self.status is LedgerAccountStatus.ACTIVE

    @property
    def is_debit_normal(self) -> bool:
        return self.normal_balance is NormalBalanceSide.DEBIT

    @property
    def is_credit_normal(self) -> bool:
        return self.normal_balance is NormalBalanceSide.CREDIT

    def can_transition_to(
        self,
        target_status: object,
    ) -> bool:
        target = LedgerAccountStatus.parse(target_status)

        return target in _ALLOWED_TRANSITIONS[self.status]

    def transition_to(
        self,
        target_status: object,
        *,
        changed_at: datetime | None = None,
    ) -> LedgerAccount:
        target = LedgerAccountStatus.parse(target_status)

        if target is self.status:
            raise ValueError(
                "ledger account status transition must change "
                "the status"
            )

        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(
                f"ledger account status transition from "
                f"{self.status.value} to {target.value} "
                "is not allowed"
            )

        timestamp = (
            _utc_now()
            if changed_at is None
            else _normalize_datetime(
                changed_at,
                field_name="ledger account changed_at",
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "ledger account changed_at must not be before "
                "updated_at"
            )

        return replace(
            self,
            status=target,
            updated_at=timestamp,
            version=self.version + 1,
        )

    def activate(
        self,
        *,
        changed_at: datetime | None = None,
    ) -> LedgerAccount:
        return self.transition_to(
            LedgerAccountStatus.ACTIVE,
            changed_at=changed_at,
        )

    def restrict(
        self,
        *,
        changed_at: datetime | None = None,
    ) -> LedgerAccount:
        return self.transition_to(
            LedgerAccountStatus.RESTRICTED,
            changed_at=changed_at,
        )

    def suspend(
        self,
        *,
        changed_at: datetime | None = None,
    ) -> LedgerAccount:
        return self.transition_to(
            LedgerAccountStatus.SUSPENDED,
            changed_at=changed_at,
        )

    def close(
        self,
        *,
        changed_at: datetime | None = None,
    ) -> LedgerAccount:
        return self.transition_to(
            LedgerAccountStatus.CLOSED,
            changed_at=changed_at,
        )

    def with_metadata(
        self,
        metadata: (
            Mapping[str, Any]
            | LedgerAccountMetadata
            | None
        ),
        *,
        changed_at: datetime | None = None,
    ) -> LedgerAccount:
        timestamp = (
            _utc_now()
            if changed_at is None
            else _normalize_datetime(
                changed_at,
                field_name="ledger account changed_at",
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "ledger account changed_at must not be before "
                "updated_at"
            )

        normalized_metadata = LedgerAccountMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "ledger account metadata update must change "
                "metadata"
            )

        return replace(
            self,
            metadata=normalized_metadata,
            updated_at=timestamp,
            version=self.version + 1,
        )

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "account_id": self.account_id.value,
                "account_code": self.account_code,
                "name": self.name,
                "account_type": self.account_type.value,
                "normal_balance": self.normal_balance.value,
                "status": self.status.value,
                "currency": self.currency.code,
                "owner_id": self.owner_id,
                "wallet_id": self.wallet_id,
                "tenant_id": self.tenant_id,
                "parent_account_id": (
                    None
                    if self.parent_account_id is None
                    else self.parent_account_id.value
                ),
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "version": self.version,
                "metadata": dict(
                    self.metadata.canonical_dict()
                ),
            }
        )


__all__ = [
    "LedgerAccount",
    "LedgerAccountId",
    "LedgerAccountMetadata",
    "LedgerAccountStatus",
    "LedgerAccountType",
    "NormalBalanceSide",
]
