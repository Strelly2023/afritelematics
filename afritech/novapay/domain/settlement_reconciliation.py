"""Canonical NovaPay settlement-reconciliation domain primitives.

This module defines immutable identifiers, classifications, statuses, source
types, evidence types, and metadata used by the Settlement Reconciliation
domain.

The module is intentionally authority-limited. It does not execute settlement,
mutate wallets, post ledger entries, submit to providers, reconcile external
systems, or persist records.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Final, Self

from .settlement_batch import SettlementBatchId


_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$"
)

_ENUM_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[^a-z0-9]+"
)

_METADATA_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_]{0,63}$"
)

_MAX_IDENTIFIER_LENGTH: Final[int] = 160
_MAX_METADATA_DEPTH: Final[int] = 8
_MAX_METADATA_ITEMS: Final[int] = 128
_MAX_METADATA_STRING_LENGTH: Final[int] = 4096

_PROHIBITED_METADATA_KEYS: Final[frozenset[str]] = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "card_number",
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

    if len(normalized) > _MAX_IDENTIFIER_LENGTH:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{_MAX_IDENTIFIER_LENGTH} characters"
        )

    if _IDENTIFIER_PATTERN.fullmatch(normalized) is None:
        raise ValueError(
            f"{field_name} contains invalid characters"
        )

    return normalized


def _normalize_enum_token(
    value: object,
    *,
    field_name: str,
) -> str:
    if isinstance(value, Enum):
        value = value.value

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    normalized = _ENUM_TOKEN_PATTERN.sub(
        "_",
        value.strip().lower(),
    ).strip("_")

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    return normalized


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


def _normalize_non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field_name} must be an integer"
        )

    if value < 0:
        raise ValueError(
            f"{field_name} must not be negative"
        )

    return value


def _normalize_positive_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    normalized = _normalize_non_negative_integer(
        value,
        field_name=field_name,
    )

    if normalized == 0:
        raise ValueError(
            f"{field_name} must be greater than zero"
        )

    return normalized


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


def _normalize_optional_currency_code(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=3,
    ).upper()

    if (
        len(normalized) != 3
        or not normalized.isalpha()
        or not normalized.isascii()
    ):
        raise ValueError(
            f"{field_name} must be a three-letter "
            "alphabetic currency code"
        )

    return normalized


def _normalize_digest(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=256,
    ).lower()

    if re.fullmatch(
        r"[a-f0-9]{32,256}",
        normalized,
    ) is None:
        raise ValueError(
            f"{field_name} must contain 32 to 256 "
            "lowercase hexadecimal characters"
        )

    return normalized


def _normalize_identifier_tuple(
    value: object,
    *,
    identifier_type: type,
    field_name: str,
) -> tuple:
    if isinstance(value, (str, bytes)):
        raise TypeError(
            f"{field_name} must be iterable"
        )

    try:
        items = tuple(value)
    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be iterable"
        ) from exc

    normalized = tuple(
        identifier_type.of(item)
        for item in items
    )

    values = [
        item.value
        for item in normalized
    ]

    if len(values) != len(set(values)):
        raise ValueError(
            f"{field_name} must not contain duplicate identifiers"
        )

    return tuple(
        sorted(
            normalized,
            key=lambda item: item.value,
        )
    )


class _CanonicalStringEnum(str, Enum):
    """String enum with normalized parsing and deterministic serialization."""

    @classmethod
    def parse(
        cls,
        value: object,
    ) -> Self:
        if isinstance(value, cls):
            return value

        token = _normalize_enum_token(
            value,
            field_name=cls.__name__,
        )

        for member in cls:
            if member.value == token:
                return member

        allowed = ", ".join(
            member.value
            for member in cls
        )

        raise ValueError(
            f"unsupported {cls.__name__}: {token}; "
            f"expected one of: {allowed}"
        )

    def canonical_value(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class SettlementReconciliationId:
    """Canonical identifier for one settlement reconciliation aggregate."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="settlement reconciliation id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="settlement reconciliation id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ReconciliationItemId:
    """Canonical identifier for one reconciliation item."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="reconciliation item id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="reconciliation item id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ReconciliationObservationId:
    """Canonical identifier for one reconciliation observation."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="reconciliation observation id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="reconciliation observation id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ReconciliationDifferenceId:
    """Canonical identifier for one reconciliation difference."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="reconciliation difference id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="reconciliation difference id",
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ReconciliationEvidenceId:
    """Canonical identifier for one reconciliation evidence record."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="reconciliation evidence id",
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
    ) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_identifier(
                value,
                field_name="reconciliation evidence id",
            )
        )

    def __str__(self) -> str:
        return self.value


class ReconciliationType(_CanonicalStringEnum):
    """Business scope being reconciled."""

    SETTLEMENT_BATCH = "settlement_batch"
    SETTLEMENT_ENTRY = "settlement_entry"
    SETTLEMENT_INSTRUCTION = "settlement_instruction"
    PROVIDER_REPORT = "provider_report"
    BANK_STATEMENT = "bank_statement"
    LEDGER_CHECKPOINT = "ledger_checkpoint"
    TREASURY_POSITION = "treasury_position"
    OPERATIONAL_REPORT = "operational_report"


class ReconciliationStatus(_CanonicalStringEnum):
    """Lifecycle status for a reconciliation aggregate."""

    DRAFT = "draft"
    OPEN = "open"
    COLLECTING = "collecting"
    COMPARING = "comparing"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    EXCEPTION = "exception"
    REVIEW_REQUIRED = "review_required"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"


class ReconciliationItemStatus(_CanonicalStringEnum):
    """Classification status for one reconciliation item."""

    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    MISSING_EXPECTED = "missing_expected"
    MISSING_OBSERVED = "missing_observed"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    EXCLUDED = "excluded"
    REVIEW_REQUIRED = "review_required"


class ReconciliationObservationSource(_CanonicalStringEnum):
    """Origin of a read-only reconciliation observation."""

    SETTLEMENT_BATCH = "settlement_batch"
    SETTLEMENT_ENTRY = "settlement_entry"
    SETTLEMENT_INSTRUCTION = "settlement_instruction"
    PROVIDER = "provider"
    BANK = "bank"
    LEDGER = "ledger"
    TREASURY = "treasury"
    AUDIT_EVENT = "audit_event"
    OPERATIONS = "operations"
    EXTERNAL_REPORT = "external_report"


class ReconciliationDifferenceType(_CanonicalStringEnum):
    """Canonical difference category discovered during comparison."""

    AMOUNT = "amount"
    CURRENCY = "currency"
    STATUS = "status"
    COUNT = "count"
    REFERENCE = "reference"
    TIMESTAMP = "timestamp"
    PARTICIPANT = "participant"
    MISSING_EXPECTED = "missing_expected"
    MISSING_OBSERVED = "missing_observed"
    DUPLICATE = "duplicate"
    DATA_QUALITY = "data_quality"
    OTHER = "other"


class ReconciliationEvidenceType(_CanonicalStringEnum):
    """Canonical evidence type supporting a reconciliation conclusion."""

    SETTLEMENT_RESULT = "settlement_result"
    SETTLEMENT_SUMMARY = "settlement_summary"
    PROVIDER_REPORT = "provider_report"
    BANK_STATEMENT = "bank_statement"
    LEDGER_CHECKPOINT = "ledger_checkpoint"
    TREASURY_REPORT = "treasury_report"
    AUDIT_EVENT = "audit_event"
    RECEIPT = "receipt"
    HASH = "hash"
    SIGNATURE = "signature"
    EXTERNAL_REFERENCE = "external_reference"
    OPERATIONAL_NOTE = "operational_note"


def _normalize_metadata_key(
    value: object,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "reconciliation metadata keys must be strings"
        )

    normalized = _ENUM_TOKEN_PATTERN.sub(
        "_",
        value.strip().lower(),
    ).strip("_")

    if not normalized:
        raise ValueError(
            "reconciliation metadata keys must not be empty"
        )

    if _METADATA_KEY_PATTERN.fullmatch(normalized) is None:
        raise ValueError(
            "reconciliation metadata key must begin with "
            "a lowercase letter and contain only lowercase "
            "letters, digits, and underscores"
        )

    if normalized in _PROHIBITED_METADATA_KEYS:
        raise ValueError(
            "reconciliation metadata contains prohibited "
            f"sensitive key: {normalized}"
        )

    return normalized


def _freeze_metadata_value(
    value: object,
    *,
    depth: int,
) -> object:
    if depth > _MAX_METADATA_DEPTH:
        raise ValueError(
            "reconciliation metadata exceeds maximum depth"
        )

    if value is None or isinstance(
        value,
        (bool, int, float, str),
    ):
        if (
            isinstance(value, str)
            and len(value) > _MAX_METADATA_STRING_LENGTH
        ):
            raise ValueError(
                "reconciliation metadata string exceeds "
                f"{_MAX_METADATA_STRING_LENGTH} characters"
            )

        return value

    if isinstance(value, Enum):
        enum_value = value.value

        if not isinstance(enum_value, str):
            raise TypeError(
                "reconciliation metadata enum values "
                "must serialize to strings"
            )

        return enum_value

    if isinstance(value, Mapping):
        if len(value) > _MAX_METADATA_ITEMS:
            raise ValueError(
                "reconciliation metadata mapping exceeds "
                f"{_MAX_METADATA_ITEMS} items"
            )

        frozen: dict[str, object] = {}

        for raw_key, raw_value in value.items():
            key = _normalize_metadata_key(raw_key)

            if key in frozen:
                raise ValueError(
                    "reconciliation metadata contains duplicate "
                    f"normalized key: {key}"
                )

            frozen[key] = _freeze_metadata_value(
                raw_value,
                depth=depth + 1,
            )

        return MappingProxyType(
            dict(
                sorted(
                    frozen.items(),
                    key=lambda item: item[0],
                )
            )
        )

    if isinstance(value, (list, tuple)):
        if len(value) > _MAX_METADATA_ITEMS:
            raise ValueError(
                "reconciliation metadata sequence exceeds "
                f"{_MAX_METADATA_ITEMS} items"
            )

        return tuple(
            _freeze_metadata_value(
                item,
                depth=depth + 1,
            )
            for item in value
        )

    if isinstance(value, (set, frozenset)):
        raise TypeError(
            "reconciliation metadata sets are not supported"
        )

    raise TypeError(
        "unsupported reconciliation metadata value type: "
        f"{type(value).__name__}"
    )


def _thaw_metadata_value(
    value: object,
) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _thaw_metadata_value(nested)
            for key, nested in value.items()
        }

    if isinstance(value, tuple):
        return [
            _thaw_metadata_value(nested)
            for nested in value
        ]

    return value


@dataclass(frozen=True, slots=True)
class ReconciliationMetadata:
    """Deeply immutable, serialization-safe reconciliation metadata."""

    values: Mapping[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError(
                "reconciliation metadata must be a mapping"
            )

        frozen = _freeze_metadata_value(
            self.values,
            depth=0,
        )

        if not isinstance(frozen, Mapping):
            raise AssertionError(
                "reconciliation metadata normalization failed"
            )

        object.__setattr__(
            self,
            "values",
            frozen,
        )

    @classmethod
    def empty(cls) -> Self:
        return cls({})

    @classmethod
    def of(
        cls,
        value: object = None,
    ) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls.empty()

        if not isinstance(value, Mapping):
            raise TypeError(
                "reconciliation metadata must be a mapping"
            )

        return cls(value)

    def canonical_dict(self) -> dict[str, object]:
        thawed = _thaw_metadata_value(self.values)

        if not isinstance(thawed, dict):
            raise AssertionError(
                "reconciliation metadata serialization failed"
            )

        return thawed

    def __bool__(self) -> bool:
        return bool(self.values)

    def __len__(self) -> int:
        return len(self.values)


_RECONCILIATION_ALLOWED_TRANSITIONS: Final[
    Mapping[
        ReconciliationStatus,
        frozenset[ReconciliationStatus],
    ]
] = MappingProxyType(
    {
        ReconciliationStatus.DRAFT: frozenset(
            {
                ReconciliationStatus.OPEN,
                ReconciliationStatus.CANCELED,
            }
        ),
        ReconciliationStatus.OPEN: frozenset(
            {
                ReconciliationStatus.COLLECTING,
                ReconciliationStatus.CANCELED,
                ReconciliationStatus.EXPIRED,
            }
        ),
        ReconciliationStatus.COLLECTING: frozenset(
            {
                ReconciliationStatus.COMPARING,
                ReconciliationStatus.REVIEW_REQUIRED,
                ReconciliationStatus.CANCELED,
                ReconciliationStatus.EXPIRED,
            }
        ),
        ReconciliationStatus.COMPARING: frozenset(
            {
                ReconciliationStatus.MATCHED,
                ReconciliationStatus.PARTIALLY_MATCHED,
                ReconciliationStatus.UNMATCHED,
                ReconciliationStatus.EXCEPTION,
                ReconciliationStatus.REVIEW_REQUIRED,
                ReconciliationStatus.CANCELED,
                ReconciliationStatus.EXPIRED,
            }
        ),
        ReconciliationStatus.MATCHED: frozenset(
            {
                ReconciliationStatus.CLOSED,
            }
        ),
        ReconciliationStatus.PARTIALLY_MATCHED: frozenset(
            {
                ReconciliationStatus.REVIEW_REQUIRED,
                ReconciliationStatus.CLOSED,
            }
        ),
        ReconciliationStatus.UNMATCHED: frozenset(
            {
                ReconciliationStatus.REVIEW_REQUIRED,
                ReconciliationStatus.CLOSED,
            }
        ),
        ReconciliationStatus.EXCEPTION: frozenset(
            {
                ReconciliationStatus.REVIEW_REQUIRED,
                ReconciliationStatus.CLOSED,
            }
        ),
        ReconciliationStatus.REVIEW_REQUIRED: frozenset(
            {
                ReconciliationStatus.COLLECTING,
                ReconciliationStatus.COMPARING,
                ReconciliationStatus.CLOSED,
                ReconciliationStatus.CANCELED,
                ReconciliationStatus.EXPIRED,
            }
        ),
        ReconciliationStatus.CLOSED: frozenset(),
        ReconciliationStatus.CANCELED: frozenset(),
        ReconciliationStatus.EXPIRED: frozenset(),
    }
)


@dataclass(frozen=True, slots=True)
class SettlementReconciliation:
    """Immutable foundation for one settlement reconciliation process.

    The aggregate records reconciliation intent and structural state only.
    It does not perform matching, settlement execution, ledger mutation,
    provider submission, exception resolution, or persistence.
    """

    reconciliation_id: SettlementReconciliationId
    reconciliation_type: ReconciliationType
    status: ReconciliationStatus
    settlement_batch_id: SettlementBatchId
    expected_entry_count: int
    created_at: datetime
    updated_at: datetime
    version: int
    metadata: ReconciliationMetadata

    def __post_init__(self) -> None:
        reconciliation_id = SettlementReconciliationId.of(
            self.reconciliation_id
        )
        reconciliation_type = ReconciliationType.parse(
            self.reconciliation_type
        )
        status = ReconciliationStatus.parse(
            self.status
        )
        settlement_batch_id = SettlementBatchId.of(
            self.settlement_batch_id
        )
        expected_entry_count = _normalize_non_negative_integer(
            self.expected_entry_count,
            field_name=(
                "settlement reconciliation expected entry count"
            ),
        )
        created_at = _normalize_datetime(
            self.created_at,
            field_name=(
                "settlement reconciliation created_at"
            ),
        )
        updated_at = _normalize_datetime(
            self.updated_at,
            field_name=(
                "settlement reconciliation updated_at"
            ),
        )
        version = _normalize_positive_integer(
            self.version,
            field_name=(
                "settlement reconciliation version"
            ),
        )
        metadata = ReconciliationMetadata.of(
            self.metadata
        )

        if updated_at < created_at:
            raise ValueError(
                "settlement reconciliation updated_at "
                "must not precede created_at"
            )

        object.__setattr__(
            self,
            "reconciliation_id",
            reconciliation_id,
        )
        object.__setattr__(
            self,
            "reconciliation_type",
            reconciliation_type,
        )
        object.__setattr__(
            self,
            "status",
            status,
        )
        object.__setattr__(
            self,
            "settlement_batch_id",
            settlement_batch_id,
        )
        object.__setattr__(
            self,
            "expected_entry_count",
            expected_entry_count,
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
        reconciliation_id: object,
        reconciliation_type: object,
        settlement_batch_id: object,
        expected_entry_count: object,
        created_at: datetime,
        metadata: object = None,
    ) -> Self:
        normalized_created_at = _normalize_datetime(
            created_at,
            field_name=(
                "settlement reconciliation created_at"
            ),
        )

        return cls(
            reconciliation_id=(
                SettlementReconciliationId.of(
                    reconciliation_id
                )
            ),
            reconciliation_type=(
                ReconciliationType.parse(
                    reconciliation_type
                )
            ),
            status=ReconciliationStatus.DRAFT,
            settlement_batch_id=(
                SettlementBatchId.of(
                    settlement_batch_id
                )
            ),
            expected_entry_count=(
                _normalize_non_negative_integer(
                    expected_entry_count,
                    field_name=(
                        "settlement reconciliation "
                        "expected entry count"
                    ),
                )
            ),
            created_at=normalized_created_at,
            updated_at=normalized_created_at,
            version=1,
            metadata=ReconciliationMetadata.of(
                metadata
            ),
        )

    def _normalize_transition_time(
        self,
        value: object,
    ) -> datetime:
        normalized = _normalize_datetime(
            value,
            field_name=(
                "settlement reconciliation transition time"
            ),
        )

        if normalized < self.updated_at:
            raise ValueError(
                "settlement reconciliation transition time "
                "must not precede updated_at"
            )

        return normalized

    def _transition_to(
        self,
        target_status: object,
        *,
        transitioned_at: datetime,
    ) -> Self:
        normalized_target = ReconciliationStatus.parse(
            target_status
        )
        normalized_time = self._normalize_transition_time(
            transitioned_at
        )

        allowed = _RECONCILIATION_ALLOWED_TRANSITIONS[
            self.status
        ]

        if normalized_target not in allowed:
            raise ValueError(
                "invalid settlement reconciliation transition: "
                f"{self.status.value} -> "
                f"{normalized_target.value}"
            )

        return replace(
            self,
            status=normalized_target,
            updated_at=normalized_time,
            version=self.version + 1,
        )

    def open(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.OPEN,
            transitioned_at=transitioned_at,
        )

    def start_collecting(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.COLLECTING,
            transitioned_at=transitioned_at,
        )

    def start_comparing(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.COMPARING,
            transitioned_at=transitioned_at,
        )

    def mark_matched(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.MATCHED,
            transitioned_at=transitioned_at,
        )

    def mark_partially_matched(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.PARTIALLY_MATCHED,
            transitioned_at=transitioned_at,
        )

    def mark_unmatched(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.UNMATCHED,
            transitioned_at=transitioned_at,
        )

    def mark_exception(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.EXCEPTION,
            transitioned_at=transitioned_at,
        )

    def require_review(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.REVIEW_REQUIRED,
            transitioned_at=transitioned_at,
        )

    def close(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.CLOSED,
            transitioned_at=transitioned_at,
        )

    def cancel(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.CANCELED,
            transitioned_at=transitioned_at,
        )

    def expire(
        self,
        *,
        transitioned_at: datetime,
    ) -> Self:
        return self._transition_to(
            ReconciliationStatus.EXPIRED,
            transitioned_at=transitioned_at,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        updated_at: datetime,
    ) -> Self:
        normalized_time = self._normalize_transition_time(
            updated_at
        )
        normalized_metadata = ReconciliationMetadata.of(
            metadata
        )

        return replace(
            self,
            metadata=normalized_metadata,
            updated_at=normalized_time,
            version=self.version + 1,
        )

    @property
    def is_draft(self) -> bool:
        return self.status is ReconciliationStatus.DRAFT

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            ReconciliationStatus.MATCHED,
            ReconciliationStatus.CLOSED,
            ReconciliationStatus.CANCELED,
            ReconciliationStatus.EXPIRED,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {
            "reconciliation_id": (
                self.reconciliation_id.value
            ),
            "reconciliation_type": (
                self.reconciliation_type.value
            ),
            "status": self.status.value,
            "settlement_batch_id": (
                self.settlement_batch_id.value
            ),
            "expected_entry_count": (
                self.expected_entry_count
            ),
            "created_at": (
                self.created_at.isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
            ),
            "version": self.version,
            "metadata": (
                self.metadata.canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationObservation:
    """Immutable read-only observation from one reconciliation source."""

    observation_id: ReconciliationObservationId
    source: ReconciliationObservationSource
    reference: str
    observed_at: datetime
    observed_value: str | None
    currency_code: str | None
    metadata: ReconciliationMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "observation_id",
            ReconciliationObservationId.of(
                self.observation_id
            ),
        )
        object.__setattr__(
            self,
            "source",
            ReconciliationObservationSource.parse(
                self.source
            ),
        )
        object.__setattr__(
            self,
            "reference",
            _normalize_required_text(
                self.reference,
                field_name=(
                    "reconciliation observation reference"
                ),
                maximum_length=256,
            ),
        )
        object.__setattr__(
            self,
            "observed_at",
            _normalize_datetime(
                self.observed_at,
                field_name=(
                    "reconciliation observation observed_at"
                ),
            ),
        )
        object.__setattr__(
            self,
            "observed_value",
            _normalize_optional_text(
                self.observed_value,
                field_name=(
                    "reconciliation observation observed value"
                ),
                maximum_length=4096,
            ),
        )
        object.__setattr__(
            self,
            "currency_code",
            _normalize_optional_currency_code(
                self.currency_code,
                field_name=(
                    "reconciliation observation currency code"
                ),
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            ReconciliationMetadata.of(
                self.metadata
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        observation_id: object,
        source: object,
        reference: object,
        observed_at: datetime,
        observed_value: object = None,
        currency_code: object = None,
        metadata: object = None,
    ) -> Self:
        return cls(
            observation_id=(
                ReconciliationObservationId.of(
                    observation_id
                )
            ),
            source=(
                ReconciliationObservationSource.parse(
                    source
                )
            ),
            reference=reference,
            observed_at=observed_at,
            observed_value=observed_value,
            currency_code=currency_code,
            metadata=ReconciliationMetadata.of(
                metadata
            ),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "observation_id": self.observation_id.value,
            "source": self.source.value,
            "reference": self.reference,
            "observed_at": self.observed_at.isoformat(),
            "observed_value": self.observed_value,
            "currency_code": self.currency_code,
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationDifference:
    """Immutable difference discovered by an external comparison process."""

    difference_id: ReconciliationDifferenceId
    difference_type: ReconciliationDifferenceType
    field_name: str
    expected_value: str | None
    observed_value: str | None
    detected_at: datetime
    metadata: ReconciliationMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "difference_id",
            ReconciliationDifferenceId.of(
                self.difference_id
            ),
        )
        object.__setattr__(
            self,
            "difference_type",
            ReconciliationDifferenceType.parse(
                self.difference_type
            ),
        )
        object.__setattr__(
            self,
            "field_name",
            _normalize_required_text(
                self.field_name,
                field_name=(
                    "reconciliation difference field name"
                ),
                maximum_length=128,
            ),
        )
        object.__setattr__(
            self,
            "expected_value",
            _normalize_optional_text(
                self.expected_value,
                field_name=(
                    "reconciliation difference expected value"
                ),
                maximum_length=4096,
            ),
        )
        object.__setattr__(
            self,
            "observed_value",
            _normalize_optional_text(
                self.observed_value,
                field_name=(
                    "reconciliation difference observed value"
                ),
                maximum_length=4096,
            ),
        )
        object.__setattr__(
            self,
            "detected_at",
            _normalize_datetime(
                self.detected_at,
                field_name=(
                    "reconciliation difference detected_at"
                ),
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            ReconciliationMetadata.of(
                self.metadata
            ),
        )

        if (
            self.expected_value is None
            and self.observed_value is None
        ):
            raise ValueError(
                "reconciliation difference must contain "
                "an expected or observed value"
            )

        if (
            self.expected_value is not None
            and self.observed_value is not None
            and self.expected_value == self.observed_value
        ):
            raise ValueError(
                "reconciliation difference expected and "
                "observed values must differ"
            )

    @classmethod
    def create(
        cls,
        *,
        difference_id: object,
        difference_type: object,
        field_name: object,
        detected_at: datetime,
        expected_value: object = None,
        observed_value: object = None,
        metadata: object = None,
    ) -> Self:
        return cls(
            difference_id=(
                ReconciliationDifferenceId.of(
                    difference_id
                )
            ),
            difference_type=(
                ReconciliationDifferenceType.parse(
                    difference_type
                )
            ),
            field_name=field_name,
            expected_value=expected_value,
            observed_value=observed_value,
            detected_at=detected_at,
            metadata=ReconciliationMetadata.of(
                metadata
            ),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "difference_id": self.difference_id.value,
            "difference_type": self.difference_type.value,
            "field_name": self.field_name,
            "expected_value": self.expected_value,
            "observed_value": self.observed_value,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationEvidence:
    """Immutable reference to evidence supporting a reconciliation record."""

    evidence_id: ReconciliationEvidenceId
    evidence_type: ReconciliationEvidenceType
    reference: str
    recorded_at: datetime
    digest: str | None
    metadata: ReconciliationMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_id",
            ReconciliationEvidenceId.of(
                self.evidence_id
            ),
        )
        object.__setattr__(
            self,
            "evidence_type",
            ReconciliationEvidenceType.parse(
                self.evidence_type
            ),
        )
        object.__setattr__(
            self,
            "reference",
            _normalize_required_text(
                self.reference,
                field_name=(
                    "reconciliation evidence reference"
                ),
                maximum_length=512,
            ),
        )
        object.__setattr__(
            self,
            "recorded_at",
            _normalize_datetime(
                self.recorded_at,
                field_name=(
                    "reconciliation evidence recorded_at"
                ),
            ),
        )
        object.__setattr__(
            self,
            "digest",
            _normalize_digest(
                self.digest,
                field_name=(
                    "reconciliation evidence digest"
                ),
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            ReconciliationMetadata.of(
                self.metadata
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        evidence_id: object,
        evidence_type: object,
        reference: object,
        recorded_at: datetime,
        digest: object = None,
        metadata: object = None,
    ) -> Self:
        return cls(
            evidence_id=(
                ReconciliationEvidenceId.of(
                    evidence_id
                )
            ),
            evidence_type=(
                ReconciliationEvidenceType.parse(
                    evidence_type
                )
            ),
            reference=reference,
            recorded_at=recorded_at,
            digest=digest,
            metadata=ReconciliationMetadata.of(
                metadata
            ),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id.value,
            "evidence_type": self.evidence_type.value,
            "reference": self.reference,
            "recorded_at": self.recorded_at.isoformat(),
            "digest": self.digest,
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationItem:
    """Immutable grouping of reconciliation references and classifications."""

    item_id: ReconciliationItemId
    status: ReconciliationItemStatus
    expected_reference: str
    observed_reference: str | None
    observation_ids: tuple[ReconciliationObservationId, ...]
    difference_ids: tuple[ReconciliationDifferenceId, ...]
    evidence_ids: tuple[ReconciliationEvidenceId, ...]
    metadata: ReconciliationMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "item_id",
            ReconciliationItemId.of(
                self.item_id
            ),
        )
        object.__setattr__(
            self,
            "status",
            ReconciliationItemStatus.parse(
                self.status
            ),
        )
        object.__setattr__(
            self,
            "expected_reference",
            _normalize_required_text(
                self.expected_reference,
                field_name=(
                    "reconciliation item expected reference"
                ),
                maximum_length=256,
            ),
        )
        object.__setattr__(
            self,
            "observed_reference",
            _normalize_optional_text(
                self.observed_reference,
                field_name=(
                    "reconciliation item observed reference"
                ),
                maximum_length=256,
            ),
        )
        object.__setattr__(
            self,
            "observation_ids",
            _normalize_identifier_tuple(
                self.observation_ids,
                identifier_type=(
                    ReconciliationObservationId
                ),
                field_name=(
                    "reconciliation item observation ids"
                ),
            ),
        )
        object.__setattr__(
            self,
            "difference_ids",
            _normalize_identifier_tuple(
                self.difference_ids,
                identifier_type=(
                    ReconciliationDifferenceId
                ),
                field_name=(
                    "reconciliation item difference ids"
                ),
            ),
        )
        object.__setattr__(
            self,
            "evidence_ids",
            _normalize_identifier_tuple(
                self.evidence_ids,
                identifier_type=(
                    ReconciliationEvidenceId
                ),
                field_name=(
                    "reconciliation item evidence ids"
                ),
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            ReconciliationMetadata.of(
                self.metadata
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        item_id: object,
        expected_reference: object,
        observed_reference: object = None,
        status: object = ReconciliationItemStatus.PENDING,
        observation_ids: object = (),
        difference_ids: object = (),
        evidence_ids: object = (),
        metadata: object = None,
    ) -> Self:
        return cls(
            item_id=ReconciliationItemId.of(
                item_id
            ),
            status=ReconciliationItemStatus.parse(
                status
            ),
            expected_reference=expected_reference,
            observed_reference=observed_reference,
            observation_ids=observation_ids,
            difference_ids=difference_ids,
            evidence_ids=evidence_ids,
            metadata=ReconciliationMetadata.of(
                metadata
            ),
        )

    @property
    def has_observations(self) -> bool:
        return bool(self.observation_ids)

    @property
    def has_differences(self) -> bool:
        return bool(self.difference_ids)

    @property
    def has_evidence(self) -> bool:
        return bool(self.evidence_ids)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id.value,
            "status": self.status.value,
            "expected_reference": self.expected_reference,
            "observed_reference": self.observed_reference,
            "observation_ids": [
                value.value
                for value in self.observation_ids
            ],
            "difference_ids": [
                value.value
                for value in self.difference_ids
            ],
            "evidence_ids": [
                value.value
                for value in self.evidence_ids
            ],
            "metadata": self.metadata.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationSummary:
    """Immutable status-count summary for reconciliation items."""

    total_items: int
    pending_items: int
    matched_items: int
    partially_matched_items: int
    unmatched_items: int
    missing_expected_items: int
    missing_observed_items: int
    duplicate_items: int
    conflict_items: int
    excluded_items: int
    review_required_items: int

    def __post_init__(self) -> None:
        field_names = (
            "total_items",
            "pending_items",
            "matched_items",
            "partially_matched_items",
            "unmatched_items",
            "missing_expected_items",
            "missing_observed_items",
            "duplicate_items",
            "conflict_items",
            "excluded_items",
            "review_required_items",
        )

        normalized_values: dict[str, int] = {}

        for field_name in field_names:
            normalized_values[field_name] = (
                _normalize_non_negative_integer(
                    getattr(self, field_name),
                    field_name=(
                        "reconciliation summary "
                        + field_name.replace("_", " ")
                    ),
                )
            )

        classified_total = sum(
            normalized_values[field_name]
            for field_name in field_names
            if field_name != "total_items"
        )

        if classified_total != normalized_values["total_items"]:
            raise ValueError(
                "reconciliation summary item counts "
                "must equal total_items"
            )

        for field_name, value in normalized_values.items():
            object.__setattr__(
                self,
                field_name,
                value,
            )

    @classmethod
    def empty(cls) -> Self:
        return cls(
            total_items=0,
            pending_items=0,
            matched_items=0,
            partially_matched_items=0,
            unmatched_items=0,
            missing_expected_items=0,
            missing_observed_items=0,
            duplicate_items=0,
            conflict_items=0,
            excluded_items=0,
            review_required_items=0,
        )

    @classmethod
    def create(
        cls,
        *,
        total_items: object,
        pending_items: object = 0,
        matched_items: object = 0,
        partially_matched_items: object = 0,
        unmatched_items: object = 0,
        missing_expected_items: object = 0,
        missing_observed_items: object = 0,
        duplicate_items: object = 0,
        conflict_items: object = 0,
        excluded_items: object = 0,
        review_required_items: object = 0,
    ) -> Self:
        return cls(
            total_items=total_items,
            pending_items=pending_items,
            matched_items=matched_items,
            partially_matched_items=(
                partially_matched_items
            ),
            unmatched_items=unmatched_items,
            missing_expected_items=(
                missing_expected_items
            ),
            missing_observed_items=(
                missing_observed_items
            ),
            duplicate_items=duplicate_items,
            conflict_items=conflict_items,
            excluded_items=excluded_items,
            review_required_items=(
                review_required_items
            ),
        )

    @classmethod
    def from_items(
        cls,
        items: object,
    ) -> Self:
        if isinstance(items, (str, bytes)):
            raise TypeError(
                "reconciliation summary items must be iterable"
            )

        try:
            normalized_items = tuple(items)
        except TypeError as exc:
            raise TypeError(
                "reconciliation summary items must be iterable"
            ) from exc

        counts = {
            status: 0
            for status in ReconciliationItemStatus
        }

        for item in normalized_items:
            if not isinstance(item, ReconciliationItem):
                raise TypeError(
                    "reconciliation summary items must contain "
                    "ReconciliationItem values"
                )

            counts[item.status] += 1

        return cls(
            total_items=len(normalized_items),
            pending_items=counts[
                ReconciliationItemStatus.PENDING
            ],
            matched_items=counts[
                ReconciliationItemStatus.MATCHED
            ],
            partially_matched_items=counts[
                ReconciliationItemStatus.PARTIALLY_MATCHED
            ],
            unmatched_items=counts[
                ReconciliationItemStatus.UNMATCHED
            ],
            missing_expected_items=counts[
                ReconciliationItemStatus.MISSING_EXPECTED
            ],
            missing_observed_items=counts[
                ReconciliationItemStatus.MISSING_OBSERVED
            ],
            duplicate_items=counts[
                ReconciliationItemStatus.DUPLICATE
            ],
            conflict_items=counts[
                ReconciliationItemStatus.CONFLICT
            ],
            excluded_items=counts[
                ReconciliationItemStatus.EXCLUDED
            ],
            review_required_items=counts[
                ReconciliationItemStatus.REVIEW_REQUIRED
            ],
        )

    @property
    def discrepancy_items(self) -> int:
        return (
            self.partially_matched_items
            + self.unmatched_items
            + self.missing_expected_items
            + self.missing_observed_items
            + self.duplicate_items
            + self.conflict_items
            + self.review_required_items
        )

    @property
    def resolved_items(self) -> int:
        return (
            self.matched_items
            + self.partially_matched_items
            + self.unmatched_items
            + self.missing_expected_items
            + self.missing_observed_items
            + self.duplicate_items
            + self.conflict_items
            + self.excluded_items
            + self.review_required_items
        )

    @property
    def is_fully_matched(self) -> bool:
        return (
            self.total_items > 0
            and self.matched_items == self.total_items
        )

    @property
    def has_discrepancies(self) -> bool:
        return self.discrepancy_items > 0

    @property
    def is_complete(self) -> bool:
        return self.pending_items == 0

    def canonical_dict(self) -> dict[str, object]:
        return {
            "total_items": self.total_items,
            "pending_items": self.pending_items,
            "matched_items": self.matched_items,
            "partially_matched_items": (
                self.partially_matched_items
            ),
            "unmatched_items": self.unmatched_items,
            "missing_expected_items": (
                self.missing_expected_items
            ),
            "missing_observed_items": (
                self.missing_observed_items
            ),
            "duplicate_items": self.duplicate_items,
            "conflict_items": self.conflict_items,
            "excluded_items": self.excluded_items,
            "review_required_items": (
                self.review_required_items
            ),
            "discrepancy_items": self.discrepancy_items,
            "resolved_items": self.resolved_items,
            "is_fully_matched": self.is_fully_matched,
            "has_discrepancies": self.has_discrepancies,
            "is_complete": self.is_complete,
        }


_RECONCILIATION_RESULT_STATUSES: Final[
    frozenset[ReconciliationStatus]
] = frozenset(
    {
        ReconciliationStatus.MATCHED,
        ReconciliationStatus.PARTIALLY_MATCHED,
        ReconciliationStatus.UNMATCHED,
        ReconciliationStatus.EXCEPTION,
        ReconciliationStatus.REVIEW_REQUIRED,
        ReconciliationStatus.CLOSED,
        ReconciliationStatus.CANCELED,
        ReconciliationStatus.EXPIRED,
    }
)


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Immutable outcome recorded after reconciliation classification."""

    reconciliation_id: SettlementReconciliationId
    status: ReconciliationStatus
    summary: ReconciliationSummary
    completed_at: datetime
    metadata: ReconciliationMetadata

    def __post_init__(self) -> None:
        reconciliation_id = SettlementReconciliationId.of(
            self.reconciliation_id
        )
        status = ReconciliationStatus.parse(
            self.status
        )

        if status not in _RECONCILIATION_RESULT_STATUSES:
            raise ValueError(
                "reconciliation result status must be "
                "a classified or terminal status"
            )

        if not isinstance(
            self.summary,
            ReconciliationSummary,
        ):
            raise TypeError(
                "reconciliation result summary must be "
                "a ReconciliationSummary"
            )

        completed_at = _normalize_datetime(
            self.completed_at,
            field_name=(
                "reconciliation result completed_at"
            ),
        )
        metadata = ReconciliationMetadata.of(
            self.metadata
        )

        if (
            status is ReconciliationStatus.MATCHED
            and not self.summary.is_fully_matched
        ):
            raise ValueError(
                "matched reconciliation result requires "
                "a fully matched summary"
            )

        if (
            status is ReconciliationStatus.PARTIALLY_MATCHED
            and (
                self.summary.matched_items == 0
                or not self.summary.has_discrepancies
            )
        ):
            raise ValueError(
                "partially matched reconciliation result "
                "requires matched and discrepant items"
            )

        if (
            status is ReconciliationStatus.UNMATCHED
            and (
                self.summary.total_items == 0
                or self.summary.matched_items != 0
            )
        ):
            raise ValueError(
                "unmatched reconciliation result requires "
                "items with no matched items"
            )

        object.__setattr__(
            self,
            "reconciliation_id",
            reconciliation_id,
        )
        object.__setattr__(
            self,
            "status",
            status,
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

    @classmethod
    def create(
        cls,
        *,
        reconciliation_id: object,
        status: object,
        summary: ReconciliationSummary,
        completed_at: datetime,
        metadata: object = None,
    ) -> Self:
        return cls(
            reconciliation_id=(
                SettlementReconciliationId.of(
                    reconciliation_id
                )
            ),
            status=ReconciliationStatus.parse(
                status
            ),
            summary=summary,
            completed_at=completed_at,
            metadata=ReconciliationMetadata.of(
                metadata
            ),
        )

    @property
    def is_successful(self) -> bool:
        return self.status in {
            ReconciliationStatus.MATCHED,
            ReconciliationStatus.CLOSED,
        }

    @property
    def requires_attention(self) -> bool:
        return self.status in {
            ReconciliationStatus.PARTIALLY_MATCHED,
            ReconciliationStatus.UNMATCHED,
            ReconciliationStatus.EXCEPTION,
            ReconciliationStatus.REVIEW_REQUIRED,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {
            "reconciliation_id": (
                self.reconciliation_id.value
            ),
            "status": self.status.value,
            "summary": self.summary.canonical_dict(),
            "completed_at": self.completed_at.isoformat(),
            "metadata": self.metadata.canonical_dict(),
            "is_successful": self.is_successful,
            "requires_attention": self.requires_attention,
        }


__all__ = [
    "ReconciliationDifference",
    "ReconciliationDifferenceId",
    "ReconciliationDifferenceType",
    "ReconciliationEvidence",
    "ReconciliationEvidenceId",
    "ReconciliationEvidenceType",
    "ReconciliationItem",
    "ReconciliationItemId",
    "ReconciliationItemStatus",
    "ReconciliationMetadata",
    "ReconciliationObservation",
    "ReconciliationObservationId",
    "ReconciliationObservationSource",
    "ReconciliationResult",
    "ReconciliationStatus",
    "ReconciliationSummary",
    "ReconciliationType",
    "SettlementReconciliation",
    "SettlementReconciliationId",
]