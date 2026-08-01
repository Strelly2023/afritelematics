"""Canonical NovaPay wallet domain models.

This module defines immutable wallet-domain values and aggregates.

It does not:

- persist wallet records;
- calculate authoritative balances;
- post ledger entries;
- execute transfers;
- call payment providers;
- perform settlement;
- mutate the existing AfriPay runtime.

Authoritative monetary balances remain derived from the canonical ledger.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
import re

from .money import Currency


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")


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
        raise TypeError("wallet metadata must be a mapping")

    copied: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(
                "wallet metadata keys must be strings"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "wallet metadata keys must not be empty"
            )

        copied[normalized_key] = item

    return MappingProxyType(copied)


class WalletType(str, Enum):
    """Supported canonical NovaPay wallet categories."""

    CONSUMER = "consumer"
    AGENT = "agent"
    MERCHANT = "merchant"
    BUSINESS = "business"
    DRIVER = "driver"
    FLEET = "fleet"
    PLATFORM = "platform"
    TREASURY = "treasury"
    ESCROW = "escrow"
    SETTLEMENT = "settlement"

    @classmethod
    def parse(cls, value: object) -> WalletType:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError("wallet type must be a string")

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("wallet type must not be empty")

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(item.value for item in cls)
            raise ValueError(
                f"unsupported wallet type: {normalized}; "
                f"supported values: {supported}"
            ) from exc


class WalletStatus(str, Enum):
    """Canonical wallet lifecycle states."""

    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    CLOSED = "closed"

    @classmethod
    def parse(cls, value: object) -> WalletStatus:
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError("wallet status must be a string")

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("wallet status must not be empty")

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(item.value for item in cls)
            raise ValueError(
                f"unsupported wallet status: {normalized}; "
                f"supported values: {supported}"
            ) from exc


_ALLOWED_TRANSITIONS: Mapping[
    WalletStatus,
    frozenset[WalletStatus],
] = MappingProxyType(
    {
        WalletStatus.PENDING: frozenset(
            {
                WalletStatus.ACTIVE,
                WalletStatus.RESTRICTED,
                WalletStatus.CLOSED,
            }
        ),
        WalletStatus.ACTIVE: frozenset(
            {
                WalletStatus.RESTRICTED,
                WalletStatus.SUSPENDED,
                WalletStatus.CLOSED,
            }
        ),
        WalletStatus.RESTRICTED: frozenset(
            {
                WalletStatus.ACTIVE,
                WalletStatus.SUSPENDED,
                WalletStatus.CLOSED,
            }
        ),
        WalletStatus.SUSPENDED: frozenset(
            {
                WalletStatus.ACTIVE,
                WalletStatus.RESTRICTED,
                WalletStatus.CLOSED,
            }
        ),
        WalletStatus.CLOSED: frozenset(),
    }
)


@dataclass(frozen=True, slots=True, order=True)
class WalletId:
    """Strongly typed canonical wallet identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="wallet id",
            ),
        )

    @classmethod
    def of(cls, value: object) -> WalletId:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="wallet id",
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class WalletMetadata:
    """Immutable wallet metadata wrapper."""

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
        value: Mapping[str, Any] | WalletMetadata | None,
    ) -> WalletMetadata:
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
    ) -> WalletMetadata:
        if not isinstance(key, str):
            raise TypeError("wallet metadata key must be a string")

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "wallet metadata key must not be empty"
            )

        updated = dict(self.values)
        updated[normalized_key] = value

        return WalletMetadata(updated)

    def without(
        self,
        key: str,
    ) -> WalletMetadata:
        if not isinstance(key, str):
            raise TypeError("wallet metadata key must be a string")

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "wallet metadata key must not be empty"
            )

        updated = dict(self.values)
        updated.pop(normalized_key, None)

        return WalletMetadata(updated)


@dataclass(frozen=True, slots=True)
class Wallet:
    """Immutable canonical NovaPay wallet aggregate.

    The aggregate describes wallet identity, ownership, type, lifecycle,
    currency, timestamps, and metadata.

    It intentionally does not contain a mutable or authoritative balance.
    Wallet balances must be calculated from the ledger or maintained as
    explicitly non-authoritative projections.
    """

    wallet_id: WalletId
    owner_id: str
    wallet_type: WalletType
    status: WalletStatus
    home_currency: Currency
    created_at: datetime
    updated_at: datetime
    tenant_id: str | None = None
    external_reference: str | None = None
    metadata: WalletMetadata = field(
        default_factory=WalletMetadata
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_wallet_id = WalletId.of(self.wallet_id)

        normalized_owner_id = _normalize_identifier(
            self.owner_id,
            field_name="wallet owner id",
        )

        normalized_wallet_type = WalletType.parse(
            self.wallet_type
        )

        normalized_status = WalletStatus.parse(self.status)

        normalized_currency = Currency.of(
            self.home_currency
        )

        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name="wallet created_at",
        )

        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name="wallet updated_at",
        )

        normalized_tenant_id = _normalize_optional_identifier(
            self.tenant_id,
            field_name="wallet tenant id",
        )

        normalized_external_reference = (
            _normalize_optional_identifier(
                self.external_reference,
                field_name="wallet external reference",
            )
        )

        normalized_metadata = WalletMetadata.of(
            self.metadata
        )

        if isinstance(self.version, bool):
            raise TypeError("wallet version must be an integer")

        if not isinstance(self.version, int):
            raise TypeError("wallet version must be an integer")

        if self.version < 1:
            raise ValueError(
                "wallet version must be greater than zero"
            )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "wallet updated_at must not be before created_at"
            )

        object.__setattr__(
            self,
            "wallet_id",
            normalized_wallet_id,
        )
        object.__setattr__(
            self,
            "owner_id",
            normalized_owner_id,
        )
        object.__setattr__(
            self,
            "wallet_type",
            normalized_wallet_type,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "home_currency",
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
            "tenant_id",
            normalized_tenant_id,
        )
        object.__setattr__(
            self,
            "external_reference",
            normalized_external_reference,
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
        wallet_id: object,
        owner_id: object,
        wallet_type: object,
        home_currency: object,
        tenant_id: object | None = None,
        external_reference: object | None = None,
        metadata: Mapping[str, Any] | WalletMetadata | None = None,
        created_at: datetime | None = None,
    ) -> Wallet:
        timestamp = (
            _utc_now()
            if created_at is None
            else _normalize_datetime(
                created_at,
                field_name="wallet created_at",
            )
        )

        return cls(
            wallet_id=WalletId.of(wallet_id),
            owner_id=_normalize_identifier(
                owner_id,
                field_name="wallet owner id",
            ),
            wallet_type=WalletType.parse(wallet_type),
            status=WalletStatus.PENDING,
            home_currency=Currency.of(home_currency),
            tenant_id=_normalize_optional_identifier(
                tenant_id,
                field_name="wallet tenant id",
            ),
            external_reference=(
                _normalize_optional_identifier(
                    external_reference,
                    field_name="wallet external reference",
                )
            ),
            metadata=WalletMetadata.of(metadata),
            created_at=timestamp,
            updated_at=timestamp,
            version=1,
        )

    @property
    def is_pending(self) -> bool:
        return self.status is WalletStatus.PENDING

    @property
    def is_active(self) -> bool:
        return self.status is WalletStatus.ACTIVE

    @property
    def is_restricted(self) -> bool:
        return self.status is WalletStatus.RESTRICTED

    @property
    def is_suspended(self) -> bool:
        return self.status is WalletStatus.SUSPENDED

    @property
    def is_closed(self) -> bool:
        return self.status is WalletStatus.CLOSED

    @property
    def can_transact(self) -> bool:
        return self.status is WalletStatus.ACTIVE

    def can_transition_to(
        self,
        target_status: object,
    ) -> bool:
        target = WalletStatus.parse(target_status)

        return target in _ALLOWED_TRANSITIONS[self.status]

    def transition_to(
        self,
        target_status: object,
        *,
        changed_at: datetime | None = None,
    ) -> Wallet:
        target = WalletStatus.parse(target_status)

        if target is self.status:
            raise ValueError(
                "wallet status transition must change the status"
            )

        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(
                f"wallet status transition from "
                f"{self.status.value} to {target.value} "
                "is not allowed"
            )

        timestamp = (
            _utc_now()
            if changed_at is None
            else _normalize_datetime(
                changed_at,
                field_name="wallet changed_at",
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "wallet changed_at must not be before updated_at"
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
    ) -> Wallet:
        return self.transition_to(
            WalletStatus.ACTIVE,
            changed_at=changed_at,
        )

    def restrict(
        self,
        *,
        changed_at: datetime | None = None,
    ) -> Wallet:
        return self.transition_to(
            WalletStatus.RESTRICTED,
            changed_at=changed_at,
        )

    def suspend(
        self,
        *,
        changed_at: datetime | None = None,
    ) -> Wallet:
        return self.transition_to(
            WalletStatus.SUSPENDED,
            changed_at=changed_at,
        )

    def close(
        self,
        *,
        changed_at: datetime | None = None,
    ) -> Wallet:
        return self.transition_to(
            WalletStatus.CLOSED,
            changed_at=changed_at,
        )

    def with_metadata(
        self,
        metadata: Mapping[str, Any] | WalletMetadata | None,
        *,
        changed_at: datetime | None = None,
    ) -> Wallet:
        timestamp = (
            _utc_now()
            if changed_at is None
            else _normalize_datetime(
                changed_at,
                field_name="wallet changed_at",
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "wallet changed_at must not be before updated_at"
            )

        normalized_metadata = WalletMetadata.of(metadata)

        if normalized_metadata == self.metadata:
            raise ValueError(
                "wallet metadata update must change metadata"
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
                "wallet_id": self.wallet_id.value,
                "owner_id": self.owner_id,
                "wallet_type": self.wallet_type.value,
                "status": self.status.value,
                "home_currency": self.home_currency.code,
                "tenant_id": self.tenant_id,
                "external_reference": self.external_reference,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "version": self.version,
                "metadata": dict(
                    self.metadata.canonical_dict()
                ),
            }
        )


__all__ = [
    "Wallet",
    "WalletId",
    "WalletMetadata",
    "WalletStatus",
    "WalletType",
]
