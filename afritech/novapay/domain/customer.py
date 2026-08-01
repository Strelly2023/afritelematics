"""Canonical NovaPay customer domain primitives.

This module defines the stable identifiers and enumerations used by the
business-facing NovaPay customer aggregate.

The runtime customer records currently present in the wider platform remain
unchanged. They may adopt these canonical primitives through later adapters
and integration work packages.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Final, Self


_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$"
)


def _normalize_identifier(
    value: object,
    *,
    field_name: str,
) -> str:
    """Normalize and validate a canonical domain identifier."""

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


class CustomerType(str, Enum):
    """Canonical commercial role represented by a NovaPay customer."""

    INDIVIDUAL = "individual"
    AGENT = "agent"
    MERCHANT = "merchant"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    SYSTEM = "system"

    @classmethod
    def parse(cls, value: object) -> Self:
        """Return a normalized customer type."""

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError("customer type must be a string")

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("customer type must not be empty")

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(member.value for member in cls)
            raise ValueError(
                f"unsupported customer type: {normalized}; "
                f"supported values: {supported}"
            ) from exc


class CustomerStatus(str, Enum):
    """Lifecycle state of a canonical NovaPay customer."""

    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    CLOSED = "closed"

    @classmethod
    def parse(cls, value: object) -> Self:
        """Return a normalized customer status."""

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError("customer status must be a string")

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("customer status must not be empty")

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(member.value for member in cls)
            raise ValueError(
                f"unsupported customer status: {normalized}; "
                f"supported values: {supported}"
            ) from exc


class CustomerTier(str, Enum):
    """Commercial or assurance tier assigned to a NovaPay customer."""

    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

    @classmethod
    def parse(cls, value: object) -> Self:
        """Return a normalized customer tier."""

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError("customer tier must be a string")

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("customer tier must not be empty")

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(member.value for member in cls)
            raise ValueError(
                f"unsupported customer tier: {normalized}; "
                f"supported values: {supported}"
            ) from exc



_EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)

_PHONE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\+?[0-9][0-9 ()-]{5,31}$"
)

_COUNTRY_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z]{2}$"
)

_POSTAL_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9 .-]{0,19}$"
)

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


def _normalize_email(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("customer email must be a string")

    normalized = value.strip().lower()

    if not normalized:
        raise ValueError("customer email must not be empty")

    if len(normalized) > 254:
        raise ValueError(
            "customer email must not exceed 254 characters"
        )

    if not _EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("customer email format is invalid")

    return normalized


def _normalize_phone(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("customer phone must be a string")

    normalized = " ".join(value.strip().split())

    if not normalized:
        raise ValueError("customer phone must not be empty")

    if not _PHONE_PATTERN.fullmatch(normalized):
        raise ValueError("customer phone format is invalid")

    digits = "".join(character for character in normalized if character.isdigit())

    if len(digits) < 7 or len(digits) > 15:
        raise ValueError(
            "customer phone must contain between 7 and 15 digits"
        )

    return normalized


def _normalize_country_code(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("customer country code must be a string")

    normalized = value.strip().upper()

    if not _COUNTRY_CODE_PATTERN.fullmatch(normalized):
        raise ValueError(
            "customer country code must be a two-letter ISO code"
        )

    return normalized


def _normalize_postal_code(value: object) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError("customer postal code must be a string")

    normalized = " ".join(value.split()).upper()

    if not normalized:
        raise ValueError("customer postal code must not be empty")

    if not _POSTAL_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("customer postal code format is invalid")

    return normalized


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
class CustomerName:
    """Immutable legal and display-name representation."""

    legal_name: str
    display_name: str | None = None

    def __post_init__(self) -> None:
        normalized_legal_name = _normalize_required_text(
            self.legal_name,
            field_name="customer legal name",
            maximum_length=200,
        )

        normalized_display_name = _normalize_optional_text(
            self.display_name,
            field_name="customer display name",
            maximum_length=120,
        )

        object.__setattr__(
            self,
            "legal_name",
            normalized_legal_name,
        )
        object.__setattr__(
            self,
            "display_name",
            normalized_display_name,
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
                    "CustomerName already exists"
                )

            return value

        return cls(
            legal_name=_normalize_required_text(
                value,
                field_name="customer legal name",
                maximum_length=200,
            ),
            display_name=_normalize_optional_text(
                display_name,
                field_name="customer display name",
                maximum_length=120,
            ),
        )

    @property
    def effective_display_name(self) -> str:
        return self.display_name or self.legal_name

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "legal_name": self.legal_name,
            "display_name": self.display_name,
        }


@dataclass(frozen=True, slots=True)
class CustomerContact:
    """Immutable customer contact details."""

    email: str | None = None
    phone: str | None = None

    def __post_init__(self) -> None:
        normalized_email = (
            None
            if self.email is None
            else _normalize_email(self.email)
        )

        normalized_phone = (
            None
            if self.phone is None
            else _normalize_phone(self.phone)
        )

        if normalized_email is None and normalized_phone is None:
            raise ValueError(
                "customer contact requires email or phone"
            )

        object.__setattr__(
            self,
            "email",
            normalized_email,
        )
        object.__setattr__(
            self,
            "phone",
            normalized_phone,
        )

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "email": self.email,
            "phone": self.phone,
        }


@dataclass(frozen=True, slots=True)
class CustomerAddress:
    """Immutable normalized postal address."""

    country_code: str
    address_line_1: str
    locality: str
    address_line_2: str | None = None
    administrative_area: str | None = None
    postal_code: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "country_code",
            _normalize_country_code(self.country_code),
        )
        object.__setattr__(
            self,
            "address_line_1",
            _normalize_required_text(
                self.address_line_1,
                field_name="customer address line 1",
                maximum_length=200,
            ),
        )
        object.__setattr__(
            self,
            "locality",
            _normalize_required_text(
                self.locality,
                field_name="customer locality",
                maximum_length=120,
            ),
        )
        object.__setattr__(
            self,
            "address_line_2",
            _normalize_optional_text(
                self.address_line_2,
                field_name="customer address line 2",
                maximum_length=200,
            ),
        )
        object.__setattr__(
            self,
            "administrative_area",
            _normalize_optional_text(
                self.administrative_area,
                field_name="customer administrative area",
                maximum_length=120,
            ),
        )
        object.__setattr__(
            self,
            "postal_code",
            _normalize_postal_code(self.postal_code),
        )

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "country_code": self.country_code,
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "locality": self.locality,
            "administrative_area": self.administrative_area,
            "postal_code": self.postal_code,
        }


@dataclass(frozen=True, slots=True)
class CustomerPreferences:
    """Immutable customer experience and communication preferences."""

    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            _normalize_mapping(
                self.values,
                field_name="customer preferences",
                reject_sensitive_keys=False,
            ),
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_mapping(
                value,
                field_name="customer preferences",
                reject_sensitive_keys=False,
            )
        )

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        if not isinstance(key, str):
            raise TypeError(
                "customer preference key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "customer preference key must not be empty"
            )

        return self.values.get(normalized_key, default)

    def with_value(
        self,
        key: str,
        value: Any,
    ) -> Self:
        if not isinstance(key, str):
            raise TypeError(
                "customer preference key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "customer preference key must not be empty"
            )

        updated = dict(self.values)
        updated[normalized_key] = value

        return type(self)(updated)

    def without(self, key: str) -> Self:
        if not isinstance(key, str):
            raise TypeError(
                "customer preference key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "customer preference key must not be empty"
            )

        updated = dict(self.values)
        updated.pop(normalized_key, None)

        return type(self)(updated)

    def canonical_dict(self) -> MappingProxyType[str, Any]:
        return MappingProxyType(dict(self.values))


@dataclass(frozen=True, slots=True)
class CustomerMetadata:
    """Immutable non-sensitive customer metadata."""

    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            _normalize_mapping(
                self.values,
                field_name="customer metadata",
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
                field_name="customer metadata",
                reject_sensitive_keys=True,
            )
        )

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        if not isinstance(key, str):
            raise TypeError(
                "customer metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "customer metadata key must not be empty"
            )

        return self.values.get(normalized_key, default)

    def with_value(
        self,
        key: str,
        value: Any,
    ) -> Self:
        updated = dict(self.values)
        updated[key] = value

        return type(self)(updated)

    def without(self, key: str) -> Self:
        if not isinstance(key, str):
            raise TypeError(
                "customer metadata key must be a string"
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "customer metadata key must not be empty"
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
        raise TypeError("customer version must be an integer")

    if value < 1:
        raise ValueError(
            "customer version must be greater than or equal to 1"
        )

    return value


def _normalize_customer_contacts(
    value: object,
) -> tuple[CustomerContact, ...]:
    if value is None:
        return ()

    if isinstance(value, CustomerContact):
        contacts = (value,)
    else:
        if isinstance(value, (str, bytes, Mapping)):
            raise TypeError(
                "customer contacts must be an iterable "
                "of CustomerContact values"
            )

        try:
            contacts = tuple(value)
        except TypeError as exc:
            raise TypeError(
                "customer contacts must be an iterable "
                "of CustomerContact values"
            ) from exc

    normalized: list[CustomerContact] = []
    seen: set[tuple[str | None, str | None]] = set()

    for contact in contacts:
        if not isinstance(contact, CustomerContact):
            raise TypeError(
                "customer contacts must contain "
                "CustomerContact values"
            )

        key = (contact.email, contact.phone)

        if key in seen:
            raise ValueError(
                "customer contacts must not contain duplicates"
            )

        seen.add(key)
        normalized.append(contact)

    return tuple(normalized)


def _normalize_customer_addresses(
    value: object,
) -> tuple[CustomerAddress, ...]:
    if value is None:
        return ()

    if isinstance(value, CustomerAddress):
        addresses = (value,)
    else:
        if isinstance(value, (str, bytes, Mapping)):
            raise TypeError(
                "customer addresses must be an iterable "
                "of CustomerAddress values"
            )

        try:
            addresses = tuple(value)
        except TypeError as exc:
            raise TypeError(
                "customer addresses must be an iterable "
                "of CustomerAddress values"
            ) from exc

    normalized: list[CustomerAddress] = []
    seen: set[
        tuple[
            str,
            str,
            str | None,
            str,
            str | None,
            str | None,
        ]
    ] = set()

    for address in addresses:
        if not isinstance(address, CustomerAddress):
            raise TypeError(
                "customer addresses must contain "
                "CustomerAddress values"
            )

        key = (
            address.country_code,
            address.address_line_1,
            address.address_line_2,
            address.locality,
            address.administrative_area,
            address.postal_code,
        )

        if key in seen:
            raise ValueError(
                "customer addresses must not contain duplicates"
            )

        seen.add(key)
        normalized.append(address)

    return tuple(normalized)

@dataclass(frozen=True, slots=True)
class CustomerId:
    """Immutable canonical NovaPay customer identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_identifier(
                self.value,
                field_name="customer id",
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
                field_name="customer id",
            )
        )

    def __str__(self) -> str:
        return self.value

    def canonical_dict(self) -> dict[str, str]:
        """Return the deterministic serialized representation."""

        return {"value": self.value}



@dataclass(frozen=True, slots=True)
class Customer:
    """Immutable canonical NovaPay customer aggregate.

    NovaID remains authoritative for identity, credentials, authentication,
    biometrics, and identity verification data. This aggregate stores only
    the normalized NovaID identity reference.
    """

    customer_id: CustomerId
    customer_type: CustomerType
    status: CustomerStatus
    tier: CustomerTier
    name: CustomerName
    novaid_identity_id: str
    tenant_id: str
    contacts: tuple[CustomerContact, ...] = ()
    addresses: tuple[CustomerAddress, ...] = ()
    preferences: CustomerPreferences = field(
        default_factory=CustomerPreferences
    )
    metadata: CustomerMetadata = field(
        default_factory=CustomerMetadata
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_customer_id = CustomerId.of(
            self.customer_id
        )
        normalized_customer_type = CustomerType.parse(
            self.customer_type
        )
        normalized_status = CustomerStatus.parse(
            self.status
        )
        normalized_tier = CustomerTier.parse(
            self.tier
        )

        if not isinstance(self.name, CustomerName):
            raise TypeError(
                "customer name must be a CustomerName"
            )

        normalized_novaid_identity_id = _normalize_identifier(
            self.novaid_identity_id,
            field_name="NovaID identity id",
        )
        normalized_tenant_id = _normalize_identifier(
            self.tenant_id,
            field_name="customer tenant id",
        )

        normalized_contacts = _normalize_customer_contacts(
            self.contacts
        )
        normalized_addresses = _normalize_customer_addresses(
            self.addresses
        )

        normalized_preferences = CustomerPreferences.of(
            self.preferences
        )
        normalized_metadata = CustomerMetadata.of(
            self.metadata
        )

        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name="customer created at",
        )
        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name="customer updated at",
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "customer updated at must not be earlier "
                "than created at"
            )

        normalized_version = _normalize_version(
            self.version
        )

        if (
            normalized_customer_type
            is CustomerType.INDIVIDUAL
            and not normalized_contacts
        ):
            raise ValueError(
                "individual customer requires at least one contact"
            )

        if (
            normalized_customer_type
            in {
                CustomerType.AGENT,
                CustomerType.MERCHANT,
                CustomerType.BUSINESS,
                CustomerType.ENTERPRISE,
            }
            and not normalized_addresses
        ):
            raise ValueError(
                f"{normalized_customer_type.value} customer "
                "requires at least one address"
            )

        if (
            normalized_customer_type
            is CustomerType.SYSTEM
            and normalized_contacts
        ):
            raise ValueError(
                "system customer must not contain personal contacts"
            )

        object.__setattr__(
            self,
            "customer_id",
            normalized_customer_id,
        )
        object.__setattr__(
            self,
            "customer_type",
            normalized_customer_type,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "tier",
            normalized_tier,
        )
        object.__setattr__(
            self,
            "novaid_identity_id",
            normalized_novaid_identity_id,
        )
        object.__setattr__(
            self,
            "tenant_id",
            normalized_tenant_id,
        )
        object.__setattr__(
            self,
            "contacts",
            normalized_contacts,
        )
        object.__setattr__(
            self,
            "addresses",
            normalized_addresses,
        )
        object.__setattr__(
            self,
            "preferences",
            normalized_preferences,
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
        customer_id: object,
        customer_type: object,
        name: CustomerName,
        novaid_identity_id: object,
        tenant_id: object,
        contacts: object = None,
        addresses: object = None,
        status: object = CustomerStatus.PENDING,
        tier: object = CustomerTier.BASIC,
        preferences: object = None,
        metadata: object = None,
        occurred_at: datetime | None = None,
    ) -> Self:
        timestamp = (
            datetime.now(timezone.utc)
            if occurred_at is None
            else _normalize_datetime(
                occurred_at,
                field_name="customer occurred at",
            )
        )

        return cls(
            customer_id=CustomerId.of(customer_id),
            customer_type=CustomerType.parse(customer_type),
            status=CustomerStatus.parse(status),
            tier=CustomerTier.parse(tier),
            name=name,
            novaid_identity_id=_normalize_identifier(
                novaid_identity_id,
                field_name="NovaID identity id",
            ),
            tenant_id=_normalize_identifier(
                tenant_id,
                field_name="customer tenant id",
            ),
            contacts=_normalize_customer_contacts(contacts),
            addresses=_normalize_customer_addresses(addresses),
            preferences=CustomerPreferences.of(preferences),
            metadata=CustomerMetadata.of(metadata),
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
                field_name="customer occurred at",
            )
        )

        if timestamp < self.updated_at:
            raise ValueError(
                "customer occurred at must not be earlier "
                "than current updated at"
            )

        return timestamp

    def _require_open(self) -> None:
        if self.status is CustomerStatus.CLOSED:
            raise ValueError(
                "closed customer does not permit further changes"
            )

    def _with_change(
        self,
        *,
        occurred_at: datetime | None,
        status: CustomerStatus | None = None,
        tier: CustomerTier | None = None,
        name: CustomerName | None = None,
        contacts: tuple[CustomerContact, ...] | None = None,
        addresses: tuple[CustomerAddress, ...] | None = None,
        preferences: CustomerPreferences | None = None,
        metadata: CustomerMetadata | None = None,
    ) -> Self:
        timestamp = self._normalize_change_time(occurred_at)

        return replace(
            self,
            status=self.status if status is None else status,
            tier=self.tier if tier is None else tier,
            name=self.name if name is None else name,
            contacts=self.contacts if contacts is None else contacts,
            addresses=self.addresses if addresses is None else addresses,
            preferences=(
                self.preferences
                if preferences is None
                else preferences
            ),
            metadata=self.metadata if metadata is None else metadata,
            updated_at=timestamp,
            version=self.version + 1,
        )

    def _metadata_with_reason(
        self,
        *,
        action: str,
        reason: object = None,
    ) -> CustomerMetadata:
        updated = dict(self.metadata.values)
        updated["lifecycle_action"] = action

        if reason is not None:
            normalized_reason = _normalize_required_text(
                reason,
                field_name="customer lifecycle reason",
                maximum_length=500,
            )
            updated["lifecycle_reason"] = normalized_reason

        return CustomerMetadata.of(updated)

    def activate(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Activate a newly created pending customer."""

        self._require_open()

        if self.status is not CustomerStatus.PENDING:
            raise ValueError(
                "customer activation requires pending status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=CustomerStatus.ACTIVE,
            metadata=self._metadata_with_reason(
                action="activate",
                reason=reason,
            ),
        )

    def restrict(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object,
    ) -> Self:
        """Restrict an active customer."""

        self._require_open()

        if self.status is not CustomerStatus.ACTIVE:
            raise ValueError(
                "customer restriction requires active status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=CustomerStatus.RESTRICTED,
            metadata=self._metadata_with_reason(
                action="restrict",
                reason=reason,
            ),
        )

    def suspend(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object,
    ) -> Self:
        """Suspend an active or restricted customer."""

        self._require_open()

        if self.status not in {
            CustomerStatus.ACTIVE,
            CustomerStatus.RESTRICTED,
        }:
            raise ValueError(
                "customer suspension requires active "
                "or restricted status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=CustomerStatus.SUSPENDED,
            metadata=self._metadata_with_reason(
                action="suspend",
                reason=reason,
            ),
        )

    def reinstate(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object = None,
    ) -> Self:
        """Return a restricted or suspended customer to active status."""

        self._require_open()

        if self.status not in {
            CustomerStatus.RESTRICTED,
            CustomerStatus.SUSPENDED,
        }:
            raise ValueError(
                "customer reinstatement requires restricted "
                "or suspended status"
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=CustomerStatus.ACTIVE,
            metadata=self._metadata_with_reason(
                action="reinstate",
                reason=reason,
            ),
        )

    def close(
        self,
        *,
        occurred_at: datetime | None = None,
        reason: object,
    ) -> Self:
        """Close a non-closed customer permanently."""

        self._require_open()

        return self._with_change(
            occurred_at=occurred_at,
            status=CustomerStatus.CLOSED,
            metadata=self._metadata_with_reason(
                action="close",
                reason=reason,
            ),
        )

    def change_tier(
        self,
        tier: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Return a new customer with a changed commercial tier."""

        self._require_open()
        normalized_tier = CustomerTier.parse(tier)

        if normalized_tier is self.tier:
            raise ValueError(
                "customer tier update must change tier"
            )

        return self._with_change(
            occurred_at=occurred_at,
            tier=normalized_tier,
        )

    def rename(
        self,
        name: CustomerName,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Return a new customer with a changed canonical name."""

        self._require_open()

        if not isinstance(name, CustomerName):
            raise TypeError(
                "customer name must be a CustomerName"
            )

        if name == self.name:
            raise ValueError(
                "customer name update must change name"
            )

        return self._with_change(
            occurred_at=occurred_at,
            name=name,
        )

    def replace_contacts(
        self,
        contacts: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace the complete immutable customer contact collection."""

        self._require_open()
        normalized_contacts = _normalize_customer_contacts(
            contacts
        )

        if normalized_contacts == self.contacts:
            raise ValueError(
                "customer contact update must change contacts"
            )

        return self._with_change(
            occurred_at=occurred_at,
            contacts=normalized_contacts,
        )

    def replace_addresses(
        self,
        addresses: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace the complete immutable customer address collection."""

        self._require_open()
        normalized_addresses = _normalize_customer_addresses(
            addresses
        )

        if normalized_addresses == self.addresses:
            raise ValueError(
                "customer address update must change addresses"
            )

        return self._with_change(
            occurred_at=occurred_at,
            addresses=normalized_addresses,
        )

    def update_preferences(
        self,
        preferences: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace customer preferences immutably."""

        self._require_open()
        normalized_preferences = CustomerPreferences.of(
            preferences
        )

        if normalized_preferences == self.preferences:
            raise ValueError(
                "customer preference update must change preferences"
            )

        return self._with_change(
            occurred_at=occurred_at,
            preferences=normalized_preferences,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        occurred_at: datetime | None = None,
    ) -> Self:
        """Replace non-sensitive customer metadata immutably."""

        self._require_open()
        normalized_metadata = CustomerMetadata.of(metadata)

        if normalized_metadata == self.metadata:
            raise ValueError(
                "customer metadata update must change metadata"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized_metadata,
        )

    def canonical_dict(self) -> dict[str, Any]:
        """Return deterministic business-facing serialization."""

        return {
            "customer_id": self.customer_id.value,
            "customer_type": self.customer_type.value,
            "status": self.status.value,
            "tier": self.tier.value,
            "name": self.name.canonical_dict(),
            "novaid_identity_id": self.novaid_identity_id,
            "tenant_id": self.tenant_id,
            "contacts": [
                contact.canonical_dict()
                for contact in self.contacts
            ],
            "addresses": [
                address.canonical_dict()
                for address in self.addresses
            ],
            "preferences": dict(
                self.preferences.canonical_dict()
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


__all__ = [
    "Customer",
    "CustomerAddress",
    "CustomerContact",
    "CustomerId",
    "CustomerMetadata",
    "CustomerName",
    "CustomerPreferences",
    "CustomerStatus",
    "CustomerTier",
    "CustomerType",
]
