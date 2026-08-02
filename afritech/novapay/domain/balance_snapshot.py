from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Self

from .customer import CustomerId
from .financial_account import FinancialAccountId
from .journal_entry import JournalEntryId
from .ledger_account import LedgerAccountId
from .money import Currency, Money
from .wallet import WalletId


_MAX_IDENTIFIER_LENGTH = 128
_MAX_METADATA_KEY_LENGTH = 128
_MAX_METADATA_STRING_LENGTH = 1000
_MAX_POSITION_SOURCE_LENGTH = 128

_PROHIBITED_METADATA_KEYS = frozenset(
    {
        "access_token",
        "account_number",
        "api_key",
        "authorization",
        "card_number",
        "cvv",
        "password",
        "pin",
        "private_key",
        "refresh_token",
        "secret",
        "security_code",
        "token",
    }
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


def _normalize_non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")

    if value < 0:
        raise ValueError(
            f"{field_name} must be greater than or equal to 0"
        )

    return value


def _normalize_decimal(
    value: object,
    *,
    field_name: str,
) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be numeric")

    if isinstance(value, Decimal):
        normalized = value
    elif isinstance(value, (str, int)):
        try:
            normalized = Decimal(str(value).strip())
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be a valid decimal"
            ) from exc
    elif isinstance(value, float):
        raise TypeError(
            f"{field_name} must not be constructed from float"
        )
    else:
        raise TypeError(f"{field_name} must be numeric")

    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return normalized


def _normalize_metadata_value(
    value: object,
    *,
    field_name: str,
) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        if len(value) > _MAX_METADATA_STRING_LENGTH:
            raise ValueError(
                f"{field_name} string value is too long"
            )

        return value

    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(
                f"{field_name} decimal value must be finite"
            )

        return str(value)

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
        return MappingProxyType(
            _normalize_metadata_mapping(value)
        )

    raise TypeError(
        f"{field_name} contains an unsupported value type"
    )


def _normalize_metadata_mapping(
    value: Mapping[object, object],
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    for raw_key, raw_value in value.items():
        key = _normalize_required_text(
            raw_key,
            field_name="balance snapshot metadata key",
            maximum_length=_MAX_METADATA_KEY_LENGTH,
        ).lower().replace(" ", "_")

        if key in _PROHIBITED_METADATA_KEYS:
            raise ValueError(
                "balance snapshot metadata contains prohibited "
                f"sensitive key: {key}"
            )

        if key in normalized:
            raise ValueError(
                "duplicate normalized balance snapshot "
                f"metadata key: {key}"
            )

        normalized[key] = _normalize_metadata_value(
            raw_value,
            field_name=f"balance snapshot metadata {key}",
        )

    return dict(sorted(normalized.items()))


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


def _normalize_version(
    value: object,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "balance snapshot version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "balance snapshot version must be "
            "greater than or equal to 1"
        )

    return value


def _normalize_optional_identifier(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    return _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=_MAX_IDENTIFIER_LENGTH,
    )


class BalanceSnapshotType(str, Enum):
    WALLET = "wallet"
    FINANCIAL_ACCOUNT = "financial_account"
    LEDGER_ACCOUNT = "ledger_account"
    CUSTOMER = "customer"
    TREASURY = "treasury"
    SETTLEMENT = "settlement"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_required_text(
            value,
            field_name="balance snapshot type",
            maximum_length=64,
        ).lower().replace("-", "_").replace(" ", "_")

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported balance snapshot type: {normalized}"
            ) from exc


class BalanceSnapshotStatus(str, Enum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    STALE = "stale"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    INVALIDATED = "invalidated"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_required_text(
            value,
            field_name="balance snapshot status",
            maximum_length=64,
        ).lower().replace("-", "_").replace(" ", "_")

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported balance snapshot status: {normalized}"
            ) from exc


class BalanceComponentType(str, Enum):
    POSTED = "posted"
    AVAILABLE = "available"
    PENDING_DEBIT = "pending_debit"
    PENDING_CREDIT = "pending_credit"
    RESERVED = "reserved"
    HOLD = "hold"
    OVERDRAFT = "overdraft"
    UNCLEARED = "uncleared"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_required_text(
            value,
            field_name="balance component type",
            maximum_length=64,
        ).lower().replace("-", "_").replace(" ", "_")

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported balance component type: {normalized}"
            ) from exc


@dataclass(frozen=True, slots=True, order=True)
class BalanceSnapshotId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="balance snapshot id",
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
                field_name="balance snapshot id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class LedgerPosition:
    sequence: int
    source: str = "canonical_ledger"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sequence",
            _normalize_non_negative_integer(
                self.sequence,
                field_name="ledger position sequence",
            ),
        )
        object.__setattr__(
            self,
            "source",
            _normalize_required_text(
                self.source,
                field_name="ledger position source",
                maximum_length=_MAX_POSITION_SOURCE_LENGTH,
            ).lower().replace(" ", "_"),
        )

    @classmethod
    def of(
        cls,
        value: object,
        *,
        source: object = "canonical_ledger",
    ) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            sequence=_normalize_non_negative_integer(
                value,
                field_name="ledger position sequence",
            ),
            source=_normalize_required_text(
                source,
                field_name="ledger position source",
                maximum_length=_MAX_POSITION_SOURCE_LENGTH,
            ),
        )

    def is_after(self, other: object) -> bool:
        normalized = LedgerPosition.of(other)

        if normalized.source != self.source:
            raise ValueError(
                "ledger positions from different sources "
                "cannot be ordered"
            )

        return self.sequence > normalized.sequence

    def canonical_dict(self) -> dict[str, str | int]:
        return {
            "sequence": self.sequence,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class BalanceSnapshotMetadata:
    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError(
                "balance snapshot metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "values",
            MappingProxyType(
                _normalize_metadata_mapping(self.values)
            ),
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls()

        if not isinstance(value, Mapping):
            raise TypeError(
                "balance snapshot metadata must be a mapping"
            )

        return cls(value)

    def with_updates(
        self,
        updates: Mapping[object, object],
    ) -> Self:
        if not isinstance(updates, Mapping):
            raise TypeError(
                "balance snapshot metadata updates "
                "must be a mapping"
            )

        merged = dict(self.values)
        merged.update(updates)

        return type(self)(merged)

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))


@dataclass(frozen=True, slots=True)
class BalanceComponent:
    component_type: BalanceComponentType
    amount: Money
    ledger_account_id: LedgerAccountId | None = None
    wallet_id: WalletId | None = None
    reference_id: str | None = None
    metadata: BalanceSnapshotMetadata = field(
        default_factory=BalanceSnapshotMetadata
    )

    def __post_init__(self) -> None:
        normalized_type = BalanceComponentType.parse(
            self.component_type
        )

        if not isinstance(self.amount, Money):
            raise TypeError(
                "balance component amount must be Money"
            )

        normalized_ledger_account_id = (
            None
            if self.ledger_account_id is None
            else LedgerAccountId.of(
                self.ledger_account_id
            )
        )

        normalized_wallet_id = (
            None
            if self.wallet_id is None
            else WalletId.of(self.wallet_id)
        )

        normalized_reference_id = (
            None
            if self.reference_id is None
            else _normalize_required_text(
                self.reference_id,
                field_name="balance component reference id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

        normalized_metadata = BalanceSnapshotMetadata.of(
            self.metadata
        )

        object.__setattr__(
            self,
            "component_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "ledger_account_id",
            normalized_ledger_account_id,
        )
        object.__setattr__(
            self,
            "wallet_id",
            normalized_wallet_id,
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
        component_type: object,
        amount: Money,
        ledger_account_id: object = None,
        wallet_id: object = None,
        reference_id: object = None,
        metadata: object = None,
    ) -> Self:
        return cls(
            component_type=BalanceComponentType.parse(
                component_type
            ),
            amount=amount,
            ledger_account_id=(
                None
                if ledger_account_id is None
                else LedgerAccountId.of(
                    ledger_account_id
                )
            ),
            wallet_id=(
                None
                if wallet_id is None
                else WalletId.of(wallet_id)
            ),
            reference_id=(
                None
                if reference_id is None
                else _normalize_required_text(
                    reference_id,
                    field_name="balance component reference id",
                    maximum_length=_MAX_IDENTIFIER_LENGTH,
                )
            ),
            metadata=BalanceSnapshotMetadata.of(metadata),
        )

    @property
    def currency(self) -> Currency:
        return self.amount.currency

    @property
    def decimal_amount(self) -> Decimal:
        return self.amount.amount

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "component_type": self.component_type.value,
            "amount": str(self.amount.amount),
            "currency": self.amount.currency.code,
            "ledger_account_id": (
                None
                if self.ledger_account_id is None
                else self.ledger_account_id.value
            ),
            "wallet_id": (
                None
                if self.wallet_id is None
                else self.wallet_id.value
            ),
            "reference_id": self.reference_id,
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
        }



@dataclass(frozen=True, slots=True)
class BalanceReconciliation:
    """Read-only reconciliation result for one balance snapshot."""

    currency: Currency
    posted: Money
    available: Money
    pending_debit: Money
    pending_credit: Money
    reserved: Money
    hold: Money
    overdraft: Money
    uncleared: Money
    expected_available: Money
    difference: Money

    def __post_init__(self) -> None:
        normalized_currency = Currency.of(self.currency)

        money_fields = (
            "posted",
            "available",
            "pending_debit",
            "pending_credit",
            "reserved",
            "hold",
            "overdraft",
            "uncleared",
            "expected_available",
            "difference",
        )

        for field_name in money_fields:
            value = getattr(self, field_name)

            if not isinstance(value, Money):
                raise TypeError(
                    f"balance reconciliation {field_name} "
                    "must be Money"
                )

            if value.currency != normalized_currency:
                raise ValueError(
                    "all balance reconciliation values must "
                    "use the reconciliation currency"
                )

        object.__setattr__(
            self,
            "currency",
            normalized_currency,
        )

    @property
    def is_reconciled(self) -> bool:
        return self.difference.amount == Decimal("0")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "currency": self.currency.code,
            "posted": str(self.posted.amount),
            "available": str(self.available.amount),
            "pending_debit": str(
                self.pending_debit.amount
            ),
            "pending_credit": str(
                self.pending_credit.amount
            ),
            "reserved": str(self.reserved.amount),
            "hold": str(self.hold.amount),
            "overdraft": str(self.overdraft.amount),
            "uncleared": str(self.uncleared.amount),
            "expected_available": str(
                self.expected_available.amount
            ),
            "difference": str(self.difference.amount),
            "is_reconciled": self.is_reconciled,
        }



@dataclass(frozen=True, slots=True)
class BalanceSnapshot:
    """Immutable projection of ledger-derived balances.

    BalanceSnapshot records values produced by an authoritative ledger
    projection. It does not post entries, mutate ledger state, calculate
    authoritative balances, execute provider operations, or settle funds.
    """

    snapshot_id: BalanceSnapshotId
    snapshot_type: BalanceSnapshotType
    status: BalanceSnapshotStatus
    currency: Currency
    components: tuple[BalanceComponent, ...]
    ledger_position: LedgerPosition
    as_of: datetime
    captured_at: datetime
    customer_id: CustomerId | None = None
    financial_account_id: FinancialAccountId | None = None
    wallet_id: WalletId | None = None
    ledger_account_id: LedgerAccountId | None = None
    source_journal_entry_id: JournalEntryId | None = None
    source_reference_id: str | None = None
    metadata: BalanceSnapshotMetadata = field(
        default_factory=BalanceSnapshotMetadata
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_snapshot_id = BalanceSnapshotId.of(
            self.snapshot_id
        )
        normalized_snapshot_type = BalanceSnapshotType.parse(
            self.snapshot_type
        )
        normalized_status = BalanceSnapshotStatus.parse(
            self.status
        )
        normalized_currency = Currency.of(self.currency)

        try:
            raw_components = tuple(self.components)
        except TypeError as exc:
            raise TypeError(
                "balance snapshot components must be iterable"
            ) from exc

        if not raw_components:
            raise ValueError(
                "balance snapshot requires at least one component"
            )

        normalized_components: list[BalanceComponent] = []

        for component in raw_components:
            if not isinstance(component, BalanceComponent):
                raise TypeError(
                    "balance snapshot components must contain "
                    "BalanceComponent values"
                )

            if component.currency != normalized_currency:
                raise ValueError(
                    "all balance snapshot components must use "
                    "the snapshot currency"
                )

            normalized_components.append(component)

        component_types = [
            component.component_type
            for component in normalized_components
        ]

        if len(component_types) != len(set(component_types)):
            raise ValueError(
                "balance snapshot component types must be unique"
            )

        required_component_types = {
            BalanceComponentType.POSTED,
            BalanceComponentType.AVAILABLE,
        }

        missing_types = (
            required_component_types - set(component_types)
        )

        if missing_types:
            missing = ", ".join(
                sorted(
                    item.value
                    for item in missing_types
                )
            )

            raise ValueError(
                "balance snapshot is missing required "
                f"component types: {missing}"
            )

        ordered_components = tuple(
            sorted(
                normalized_components,
                key=lambda component: (
                    component.component_type.value,
                    (
                        ""
                        if component.reference_id is None
                        else component.reference_id
                    ),
                ),
            )
        )

        normalized_ledger_position = LedgerPosition.of(
            self.ledger_position
        )
        normalized_as_of = _normalize_datetime(
            self.as_of,
            field_name="balance snapshot as_of",
        )
        normalized_captured_at = _normalize_datetime(
            self.captured_at,
            field_name="balance snapshot captured_at",
        )

        if normalized_captured_at < normalized_as_of:
            raise ValueError(
                "balance snapshot captured_at must not be "
                "earlier than as_of"
            )

        normalized_customer_id = (
            None
            if self.customer_id is None
            else CustomerId.of(self.customer_id)
        )
        normalized_financial_account_id = (
            None
            if self.financial_account_id is None
            else FinancialAccountId.of(
                self.financial_account_id
            )
        )
        normalized_wallet_id = (
            None
            if self.wallet_id is None
            else WalletId.of(self.wallet_id)
        )
        normalized_ledger_account_id = (
            None
            if self.ledger_account_id is None
            else LedgerAccountId.of(
                self.ledger_account_id
            )
        )
        normalized_journal_entry_id = (
            None
            if self.source_journal_entry_id is None
            else JournalEntryId.of(
                self.source_journal_entry_id
            )
        )
        normalized_source_reference_id = (
            _normalize_optional_identifier(
                self.source_reference_id,
                field_name=(
                    "balance snapshot source reference id"
                ),
            )
        )
        normalized_metadata = BalanceSnapshotMetadata.of(
            self.metadata
        )
        normalized_version = _normalize_version(
            self.version
        )

        self._validate_ownership(
            snapshot_type=normalized_snapshot_type,
            customer_id=normalized_customer_id,
            financial_account_id=(
                normalized_financial_account_id
            ),
            wallet_id=normalized_wallet_id,
            ledger_account_id=(
                normalized_ledger_account_id
            ),
        )

        for component in ordered_components:
            if (
                component.wallet_id is not None
                and normalized_wallet_id is not None
                and component.wallet_id
                != normalized_wallet_id
            ):
                raise ValueError(
                    "balance component wallet id must match "
                    "the snapshot wallet id"
                )

            if (
                component.ledger_account_id is not None
                and normalized_ledger_account_id is not None
                and component.ledger_account_id
                != normalized_ledger_account_id
            ):
                raise ValueError(
                    "balance component ledger account id must "
                    "match the snapshot ledger account id"
                )

        object.__setattr__(
            self,
            "snapshot_id",
            normalized_snapshot_id,
        )
        object.__setattr__(
            self,
            "snapshot_type",
            normalized_snapshot_type,
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
            "components",
            ordered_components,
        )
        object.__setattr__(
            self,
            "ledger_position",
            normalized_ledger_position,
        )
        object.__setattr__(
            self,
            "as_of",
            normalized_as_of,
        )
        object.__setattr__(
            self,
            "captured_at",
            normalized_captured_at,
        )
        object.__setattr__(
            self,
            "customer_id",
            normalized_customer_id,
        )
        object.__setattr__(
            self,
            "financial_account_id",
            normalized_financial_account_id,
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
            "source_journal_entry_id",
            normalized_journal_entry_id,
        )
        object.__setattr__(
            self,
            "source_reference_id",
            normalized_source_reference_id,
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

    @staticmethod
    def _validate_ownership(
        *,
        snapshot_type: BalanceSnapshotType,
        customer_id: CustomerId | None,
        financial_account_id: FinancialAccountId | None,
        wallet_id: WalletId | None,
        ledger_account_id: LedgerAccountId | None,
    ) -> None:
        if (
            snapshot_type is BalanceSnapshotType.WALLET
            and wallet_id is None
        ):
            raise ValueError(
                "wallet balance snapshot requires wallet id"
            )

        if (
            snapshot_type
            is BalanceSnapshotType.FINANCIAL_ACCOUNT
            and financial_account_id is None
        ):
            raise ValueError(
                "financial-account balance snapshot requires "
                "financial account id"
            )

        if (
            snapshot_type
            is BalanceSnapshotType.LEDGER_ACCOUNT
            and ledger_account_id is None
        ):
            raise ValueError(
                "ledger-account balance snapshot requires "
                "ledger account id"
            )

        if (
            snapshot_type is BalanceSnapshotType.CUSTOMER
            and customer_id is None
        ):
            raise ValueError(
                "customer balance snapshot requires customer id"
            )

    @classmethod
    def create(
        cls,
        *,
        snapshot_id: object,
        snapshot_type: object,
        currency: object,
        components: object,
        ledger_position: object,
        as_of: datetime,
        captured_at: datetime | None = None,
        status: object = BalanceSnapshotStatus.CURRENT,
        customer_id: object = None,
        financial_account_id: object = None,
        wallet_id: object = None,
        ledger_account_id: object = None,
        source_journal_entry_id: object = None,
        source_reference_id: object = None,
        metadata: object = None,
    ) -> Self:
        try:
            normalized_components = tuple(
                components  # type: ignore[arg-type]
            )
        except TypeError as exc:
            raise TypeError(
                "balance snapshot components must be iterable"
            ) from exc

        normalized_as_of = _normalize_datetime(
            as_of,
            field_name="balance snapshot as_of",
        )
        normalized_captured_at = (
            normalized_as_of
            if captured_at is None
            else _normalize_datetime(
                captured_at,
                field_name="balance snapshot captured_at",
            )
        )

        return cls(
            snapshot_id=BalanceSnapshotId.of(snapshot_id),
            snapshot_type=BalanceSnapshotType.parse(
                snapshot_type
            ),
            status=BalanceSnapshotStatus.parse(status),
            currency=Currency.of(currency),
            components=normalized_components,
            ledger_position=LedgerPosition.of(
                ledger_position
            ),
            as_of=normalized_as_of,
            captured_at=normalized_captured_at,
            customer_id=(
                None
                if customer_id is None
                else CustomerId.of(customer_id)
            ),
            financial_account_id=(
                None
                if financial_account_id is None
                else FinancialAccountId.of(
                    financial_account_id
                )
            ),
            wallet_id=(
                None
                if wallet_id is None
                else WalletId.of(wallet_id)
            ),
            ledger_account_id=(
                None
                if ledger_account_id is None
                else LedgerAccountId.of(
                    ledger_account_id
                )
            ),
            source_journal_entry_id=(
                None
                if source_journal_entry_id is None
                else JournalEntryId.of(
                    source_journal_entry_id
                )
            ),
            source_reference_id=(
                _normalize_optional_identifier(
                    source_reference_id,
                    field_name=(
                        "balance snapshot source reference id"
                    ),
                )
            ),
            metadata=BalanceSnapshotMetadata.of(metadata),
            version=1,
        )

    @property
    def is_current(self) -> bool:
        return self.status is BalanceSnapshotStatus.CURRENT

    @property
    def component_types(
        self,
    ) -> tuple[BalanceComponentType, ...]:
        return tuple(
            component.component_type
            for component in self.components
        )

    def get_component(
        self,
        component_type: object,
    ) -> BalanceComponent | None:
        normalized_type = BalanceComponentType.parse(
            component_type
        )

        for component in self.components:
            if component.component_type is normalized_type:
                return component

        return None

    def require_component(
        self,
        component_type: object,
    ) -> BalanceComponent:
        normalized_type = BalanceComponentType.parse(
            component_type
        )
        component = self.get_component(normalized_type)

        if component is None:
            raise KeyError(
                "balance snapshot component not found: "
                f"{normalized_type.value}"
            )

        return component

    @property
    def posted(self) -> Money:
        return self.require_component(
            BalanceComponentType.POSTED
        ).amount

    @property
    def available(self) -> Money:
        return self.require_component(
            BalanceComponentType.AVAILABLE
        ).amount

    def _transition_status(
        self,
        *,
        target: BalanceSnapshotStatus,
        reason: object,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        normalized_target = BalanceSnapshotStatus.parse(
            target
        )
        normalized_reason = _normalize_required_text(
            reason,
            field_name="balance snapshot lifecycle reason",
            maximum_length=_MAX_METADATA_STRING_LENGTH,
        )
        normalized_occurred_at = _normalize_datetime(
            occurred_at,
            field_name=(
                "balance snapshot lifecycle occurred_at"
            ),
        )

        if normalized_occurred_at < self.captured_at:
            raise ValueError(
                "balance snapshot lifecycle occurred_at "
                "must not be earlier than captured_at"
            )

        allowed: dict[
            BalanceSnapshotStatus,
            frozenset[BalanceSnapshotStatus],
        ] = {
            BalanceSnapshotStatus.CURRENT: frozenset(
                {
                    BalanceSnapshotStatus.SUPERSEDED,
                    BalanceSnapshotStatus.STALE,
                    BalanceSnapshotStatus.RECONCILIATION_REQUIRED,
                    BalanceSnapshotStatus.INVALIDATED,
                }
            ),
            BalanceSnapshotStatus.STALE: frozenset(
                {
                    BalanceSnapshotStatus.RECONCILIATION_REQUIRED,
                    BalanceSnapshotStatus.INVALIDATED,
                }
            ),
            BalanceSnapshotStatus.RECONCILIATION_REQUIRED: frozenset(
                {
                    BalanceSnapshotStatus.INVALIDATED,
                }
            ),
            BalanceSnapshotStatus.SUPERSEDED: frozenset(),
            BalanceSnapshotStatus.INVALIDATED: frozenset(),
        }

        if normalized_target not in allowed[self.status]:
            raise ValueError(
                "invalid balance snapshot status transition: "
                f"{self.status.value} -> "
                f"{normalized_target.value}"
            )

        lifecycle_metadata = dict(
            self.metadata.canonical_dict()
        )
        lifecycle_metadata.update(
            {
                "lifecycle_reason": normalized_reason,
                "lifecycle_occurred_at": (
                    normalized_occurred_at.isoformat()
                ),
                "previous_status": self.status.value,
                "current_status": normalized_target.value,
            }
        )

        if metadata is not None:
            extra_metadata = BalanceSnapshotMetadata.of(
                metadata
            )
            lifecycle_metadata.update(
                extra_metadata.canonical_dict()
            )

        return replace(
            self,
            status=normalized_target,
            metadata=BalanceSnapshotMetadata.of(
                lifecycle_metadata
            ),
            version=self.version + 1,
        )

    def mark_superseded(
        self,
        *,
        reason: object,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=BalanceSnapshotStatus.SUPERSEDED,
            reason=reason,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def mark_stale(
        self,
        *,
        reason: object,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=BalanceSnapshotStatus.STALE,
            reason=reason,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def mark_reconciliation_required(
        self,
        *,
        reason: object,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=(
                BalanceSnapshotStatus.RECONCILIATION_REQUIRED
            ),
            reason=reason,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def invalidate(
        self,
        *,
        reason: object,
        occurred_at: datetime,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=BalanceSnapshotStatus.INVALIDATED,
            reason=reason,
            occurred_at=occurred_at,
            metadata=metadata,
        )

    def update_metadata(
        self,
        metadata: object,
    ) -> Self:
        normalized_metadata = BalanceSnapshotMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "balance snapshot metadata update "
                "must change metadata"
            )

        return replace(
            self,
            metadata=normalized_metadata,
            version=self.version + 1,
        )

    def component_amount(
        self,
        component_type: object,
    ) -> Money:
        """Return a component amount or canonical zero."""

        normalized_type = BalanceComponentType.parse(
            component_type
        )
        component = self.get_component(normalized_type)

        if component is None:
            return Money.of(
                "0",
                self.currency,
            )

        return component.amount

    @property
    def pending_debit(self) -> Money:
        return self.component_amount(
            BalanceComponentType.PENDING_DEBIT
        )

    @property
    def pending_credit(self) -> Money:
        return self.component_amount(
            BalanceComponentType.PENDING_CREDIT
        )

    @property
    def reserved(self) -> Money:
        return self.component_amount(
            BalanceComponentType.RESERVED
        )

    @property
    def hold(self) -> Money:
        return self.component_amount(
            BalanceComponentType.HOLD
        )

    @property
    def overdraft(self) -> Money:
        return self.component_amount(
            BalanceComponentType.OVERDRAFT
        )

    @property
    def uncleared(self) -> Money:
        return self.component_amount(
            BalanceComponentType.UNCLEARED
        )

    @property
    def expected_available(self) -> Money:
        expected = (
            self.posted.amount
            - self.pending_debit.amount
            + self.pending_credit.amount
            - self.reserved.amount
            - self.hold.amount
            + self.overdraft.amount
        )

        return Money.of(
            str(expected),
            self.currency,
        )

    @property
    def reconciliation_difference(self) -> Money:
        difference = (
            self.available.amount
            - self.expected_available.amount
        )

        return Money.of(
            str(difference),
            self.currency,
        )

    @property
    def is_reconciled(self) -> bool:
        return (
            self.reconciliation_difference.amount
            == Decimal("0")
        )

    def reconcile(self) -> BalanceReconciliation:
        """Build a read-only reconciliation report."""

        return BalanceReconciliation(
            currency=self.currency,
            posted=self.posted,
            available=self.available,
            pending_debit=self.pending_debit,
            pending_credit=self.pending_credit,
            reserved=self.reserved,
            hold=self.hold,
            overdraft=self.overdraft,
            uncleared=self.uncleared,
            expected_available=self.expected_available,
            difference=self.reconciliation_difference,
        )

    def require_reconciled(
        self,
    ) -> BalanceReconciliation:
        result = self.reconcile()

        if not result.is_reconciled:
            raise ValueError(
                "balance snapshot reconciliation failed: "
                f"difference={result.difference.amount} "
                f"{self.currency.code}"
            )

        return result

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id.value,
            "snapshot_type": self.snapshot_type.value,
            "status": self.status.value,
            "currency": self.currency.code,
            "components": [
                component.canonical_dict()
                for component in self.components
            ],
            "ledger_position": (
                self.ledger_position.canonical_dict()
            ),
            "as_of": self.as_of.isoformat(),
            "captured_at": self.captured_at.isoformat(),
            "customer_id": (
                None
                if self.customer_id is None
                else self.customer_id.value
            ),
            "financial_account_id": (
                None
                if self.financial_account_id is None
                else self.financial_account_id.value
            ),
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
            "source_journal_entry_id": (
                None
                if self.source_journal_entry_id is None
                else self.source_journal_entry_id.value
            ),
            "source_reference_id": (
                self.source_reference_id
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "version": self.version,
        }



@dataclass(frozen=True, slots=True, order=True)
class BalanceSnapshotHistoryId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="balance snapshot history id",
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
                field_name="balance snapshot history id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class BalanceSnapshotHistory:
    """Immutable timeline of snapshots for one balance owner."""

    history_id: BalanceSnapshotHistoryId
    snapshots: tuple[BalanceSnapshot, ...]
    metadata: BalanceSnapshotMetadata = field(
        default_factory=BalanceSnapshotMetadata
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_history_id = BalanceSnapshotHistoryId.of(
            self.history_id
        )

        try:
            raw_snapshots = tuple(self.snapshots)
        except TypeError as exc:
            raise TypeError(
                "balance snapshot history snapshots "
                "must be iterable"
            ) from exc

        if not raw_snapshots:
            raise ValueError(
                "balance snapshot history requires "
                "at least one snapshot"
            )

        for snapshot in raw_snapshots:
            if not isinstance(snapshot, BalanceSnapshot):
                raise TypeError(
                    "balance snapshot history must contain "
                    "BalanceSnapshot values"
                )

        ordered = tuple(
            sorted(
                raw_snapshots,
                key=lambda snapshot: (
                    snapshot.ledger_position.source,
                    snapshot.ledger_position.sequence,
                    snapshot.as_of,
                    snapshot.snapshot_id.value,
                ),
            )
        )

        snapshot_ids = [
            snapshot.snapshot_id.value
            for snapshot in ordered
        ]

        if len(snapshot_ids) != len(set(snapshot_ids)):
            raise ValueError(
                "balance snapshot history contains "
                "duplicate snapshot ids"
            )

        snapshot_types = {
            snapshot.snapshot_type
            for snapshot in ordered
        }

        if len(snapshot_types) != 1:
            raise ValueError(
                "balance snapshot history requires "
                "one snapshot type"
            )

        currencies = {
            snapshot.currency
            for snapshot in ordered
        }

        if len(currencies) != 1:
            raise ValueError(
                "balance snapshot history requires "
                "one canonical currency"
            )

        ledger_sources = {
            snapshot.ledger_position.source
            for snapshot in ordered
        }

        if len(ledger_sources) != 1:
            raise ValueError(
                "balance snapshot history requires "
                "one ledger-position source"
            )

        owner_keys = {
            self._owner_key(snapshot)
            for snapshot in ordered
        }

        if len(owner_keys) != 1:
            raise ValueError(
                "balance snapshot history requires "
                "one balance owner"
            )

        positions = [
            snapshot.ledger_position.sequence
            for snapshot in ordered
        ]

        if len(positions) != len(set(positions)):
            raise ValueError(
                "balance snapshot history contains "
                "duplicate ledger positions"
            )

        for previous, current in zip(
            ordered,
            ordered[1:],
            strict=False,
        ):
            if (
                current.ledger_position.sequence
                <= previous.ledger_position.sequence
            ):
                raise ValueError(
                    "balance snapshot history ledger positions "
                    "must increase"
                )

            if current.as_of < previous.as_of:
                raise ValueError(
                    "balance snapshot history as_of timestamps "
                    "must not move backwards"
                )

        current_snapshots = [
            snapshot
            for snapshot in ordered
            if snapshot.status
            is BalanceSnapshotStatus.CURRENT
        ]

        if len(current_snapshots) > 1:
            raise ValueError(
                "balance snapshot history permits "
                "at most one current snapshot"
            )

        if (
            current_snapshots
            and current_snapshots[0] is not ordered[-1]
        ):
            raise ValueError(
                "current balance snapshot must be "
                "the latest history entry"
            )

        normalized_metadata = BalanceSnapshotMetadata.of(
            self.metadata
        )
        normalized_version = _normalize_version(
            self.version
        )

        object.__setattr__(
            self,
            "history_id",
            normalized_history_id,
        )
        object.__setattr__(
            self,
            "snapshots",
            ordered,
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

    @staticmethod
    def _owner_key(
        snapshot: BalanceSnapshot,
    ) -> tuple[str | None, ...]:
        return (
            (
                None
                if snapshot.customer_id is None
                else snapshot.customer_id.value
            ),
            (
                None
                if snapshot.financial_account_id is None
                else snapshot.financial_account_id.value
            ),
            (
                None
                if snapshot.wallet_id is None
                else snapshot.wallet_id.value
            ),
            (
                None
                if snapshot.ledger_account_id is None
                else snapshot.ledger_account_id.value
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        history_id: object,
        snapshots: object,
        metadata: object = None,
    ) -> Self:
        try:
            normalized_snapshots = tuple(
                snapshots  # type: ignore[arg-type]
            )
        except TypeError as exc:
            raise TypeError(
                "balance snapshot history snapshots "
                "must be iterable"
            ) from exc

        return cls(
            history_id=BalanceSnapshotHistoryId.of(
                history_id
            ),
            snapshots=normalized_snapshots,
            metadata=BalanceSnapshotMetadata.of(metadata),
            version=1,
        )

    @property
    def size(self) -> int:
        return len(self.snapshots)

    @property
    def latest(self) -> BalanceSnapshot:
        return self.snapshots[-1]

    @property
    def current(self) -> BalanceSnapshot | None:
        if (
            self.latest.status
            is BalanceSnapshotStatus.CURRENT
        ):
            return self.latest

        return None

    @property
    def snapshot_type(self) -> BalanceSnapshotType:
        return self.latest.snapshot_type

    @property
    def currency(self) -> Currency:
        return self.latest.currency

    @property
    def ledger_source(self) -> str:
        return self.latest.ledger_position.source

    def __len__(self) -> int:
        return self.size

    def __iter__(self):
        return iter(self.snapshots)

    def get_by_id(
        self,
        snapshot_id: object,
    ) -> BalanceSnapshot | None:
        normalized_id = BalanceSnapshotId.of(snapshot_id)

        for snapshot in self.snapshots:
            if snapshot.snapshot_id == normalized_id:
                return snapshot

        return None

    def require_by_id(
        self,
        snapshot_id: object,
    ) -> BalanceSnapshot:
        snapshot = self.get_by_id(snapshot_id)

        if snapshot is None:
            normalized_id = BalanceSnapshotId.of(snapshot_id)

            raise KeyError(
                "balance snapshot not found: "
                f"{normalized_id.value}"
            )

        return snapshot

    def at_position(
        self,
        position: object,
    ) -> BalanceSnapshot | None:
        normalized_position = LedgerPosition.of(
            position,
            source=self.ledger_source,
        )

        for snapshot in self.snapshots:
            if (
                snapshot.ledger_position
                == normalized_position
            ):
                return snapshot

        return None

    def at_or_before(
        self,
        *,
        position: object | None = None,
        as_of: datetime | None = None,
    ) -> BalanceSnapshot | None:
        if (position is None) == (as_of is None):
            raise ValueError(
                "provide exactly one of position or as_of"
            )

        if position is not None:
            normalized_position = LedgerPosition.of(
                position,
                source=self.ledger_source,
            )

            matches = [
                snapshot
                for snapshot in self.snapshots
                if (
                    snapshot.ledger_position.sequence
                    <= normalized_position.sequence
                )
            ]
        else:
            normalized_as_of = _normalize_datetime(
                as_of,
                field_name=(
                    "balance snapshot history as_of"
                ),
            )

            matches = [
                snapshot
                for snapshot in self.snapshots
                if snapshot.as_of <= normalized_as_of
            ]

        if not matches:
            return None

        return matches[-1]

    def between_positions(
        self,
        *,
        start: object,
        end: object,
    ) -> tuple[BalanceSnapshot, ...]:
        normalized_start = LedgerPosition.of(
            start,
            source=self.ledger_source,
        )
        normalized_end = LedgerPosition.of(
            end,
            source=self.ledger_source,
        )

        if normalized_end.sequence < normalized_start.sequence:
            raise ValueError(
                "balance snapshot history position range "
                "end must not precede start"
            )

        return tuple(
            snapshot
            for snapshot in self.snapshots
            if (
                normalized_start.sequence
                <= snapshot.ledger_position.sequence
                <= normalized_end.sequence
            )
        )

    def between_times(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> tuple[BalanceSnapshot, ...]:
        normalized_start = _normalize_datetime(
            start,
            field_name=(
                "balance snapshot history start"
            ),
        )
        normalized_end = _normalize_datetime(
            end,
            field_name=(
                "balance snapshot history end"
            ),
        )

        if normalized_end < normalized_start:
            raise ValueError(
                "balance snapshot history time range "
                "end must not precede start"
            )

        return tuple(
            snapshot
            for snapshot in self.snapshots
            if normalized_start <= snapshot.as_of <= normalized_end
        )

    def advance(
        self,
        snapshot: BalanceSnapshot,
        *,
        occurred_at: datetime | None = None,
        reason: object = "superseded by newer snapshot",
        metadata: object = None,
    ) -> Self:
        if not isinstance(snapshot, BalanceSnapshot):
            raise TypeError(
                "balance snapshot history advancement "
                "requires a BalanceSnapshot"
            )

        if snapshot.status is not BalanceSnapshotStatus.CURRENT:
            raise ValueError(
                "incoming balance snapshot must be current"
            )

        if snapshot.snapshot_type is not self.snapshot_type:
            raise ValueError(
                "incoming balance snapshot type must match "
                "the history"
            )

        if snapshot.currency != self.currency:
            raise ValueError(
                "incoming balance snapshot currency must match "
                "the history"
            )

        if (
            snapshot.ledger_position.source
            != self.ledger_source
        ):
            raise ValueError(
                "incoming balance snapshot ledger source "
                "must match the history"
            )

        if (
            self._owner_key(snapshot)
            != self._owner_key(self.latest)
        ):
            raise ValueError(
                "incoming balance snapshot owner must match "
                "the history"
            )

        if self.get_by_id(snapshot.snapshot_id) is not None:
            raise ValueError(
                "incoming balance snapshot id already exists"
            )

        if (
            snapshot.ledger_position.sequence
            <= self.latest.ledger_position.sequence
        ):
            raise ValueError(
                "incoming balance snapshot ledger position "
                "must be greater than the latest position"
            )

        if snapshot.as_of < self.latest.as_of:
            raise ValueError(
                "incoming balance snapshot as_of timestamp "
                "must not move backwards"
            )

        transition_time = (
            snapshot.captured_at
            if occurred_at is None
            else _normalize_datetime(
                occurred_at,
                field_name=(
                    "balance snapshot history advancement "
                    "occurred_at"
                ),
            )
        )

        if transition_time > snapshot.captured_at:
            raise ValueError(
                "history advancement occurred_at must not be "
                "later than the incoming captured_at"
            )

        snapshots = list(self.snapshots)

        if (
            snapshots[-1].status
            is BalanceSnapshotStatus.CURRENT
        ):
            snapshots[-1] = snapshots[-1].mark_superseded(
                reason=reason,
                occurred_at=transition_time,
                metadata={
                    "superseded_by_snapshot_id": (
                        snapshot.snapshot_id.value
                    ),
                    "superseded_by_ledger_position": (
                        snapshot.ledger_position.sequence
                    ),
                },
            )

        snapshots.append(snapshot)

        history_metadata = dict(
            self.metadata.canonical_dict()
        )

        if metadata is not None:
            history_metadata.update(
                BalanceSnapshotMetadata.of(
                    metadata
                ).canonical_dict()
            )

        history_metadata.update(
            {
                "latest_snapshot_id": (
                    snapshot.snapshot_id.value
                ),
                "latest_ledger_position": (
                    snapshot.ledger_position.sequence
                ),
            }
        )

        return replace(
            self,
            snapshots=tuple(snapshots),
            metadata=BalanceSnapshotMetadata.of(
                history_metadata
            ),
            version=self.version + 1,
        )

    def update_metadata(
        self,
        metadata: object,
    ) -> Self:
        normalized_metadata = BalanceSnapshotMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "balance snapshot history metadata update "
                "must change metadata"
            )

        return replace(
            self,
            metadata=normalized_metadata,
            version=self.version + 1,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "history_id": self.history_id.value,
            "snapshot_type": self.snapshot_type.value,
            "currency": self.currency.code,
            "ledger_source": self.ledger_source,
            "snapshots": [
                snapshot.canonical_dict()
                for snapshot in self.snapshots
            ],
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "version": self.version,
        }


__all__ = [
    "BalanceComponent",
    "BalanceComponentType",
    "BalanceReconciliation",
    "BalanceSnapshot",
    "BalanceSnapshotHistory",
    "BalanceSnapshotHistoryId",
    "BalanceSnapshotId",
    "BalanceSnapshotMetadata",
    "BalanceSnapshotStatus",
    "BalanceSnapshotType",
    "LedgerPosition",
]
