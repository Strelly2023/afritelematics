from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


def utcnow() -> datetime:
    return datetime.now(UTC)


def identifier(value: str | None = None) -> str:
    candidate = value or str(uuid4())
    UUID(candidate)
    return candidate


class IdentityType(StrEnum):
    PERSON = "PERSON"
    ORGANISATION = "ORGANISATION"
    BUSINESS = "BUSINESS"
    GOVERNMENT_ENTITY = "GOVERNMENT_ENTITY"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"
    DEPENDENT = "DEPENDENT"


class VerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AssuranceLevel(StrEnum):
    NID_AL0 = "NID-AL0"
    NID_AL1 = "NID-AL1"
    NID_AL2 = "NID-AL2"
    NID_AL3 = "NID-AL3"
    NID_AL4 = "NID-AL4"


class NameType(StrEnum):
    LEGAL = "LEGAL"
    PREFERRED = "PREFERRED"
    FORMER = "FORMER"
    TRANSLITERATED = "TRANSLITERATED"
    PROFESSIONAL = "PROFESSIONAL"


class ContactPointType(StrEnum):
    EMAIL = "EMAIL"
    MOBILE = "MOBILE"
    PHONE = "PHONE"


class AddressType(StrEnum):
    RESIDENTIAL = "RESIDENTIAL"
    POSTAL = "POSTAL"
    BUSINESS = "BUSINESS"


class IdentifierType(StrEnum):
    NOVAID = "NOVAID"
    PASSPORT_NUMBER = "PASSPORT_NUMBER"
    DRIVER_LICENCE_NUMBER = "DRIVER_LICENCE_NUMBER"
    NATIONAL_ID = "NATIONAL_ID"
    EMPLOYEE_ID = "EMPLOYEE_ID"
    CUSTOMER_REFERENCE = "CUSTOMER_REFERENCE"
    EXTERNAL_SUBJECT_ID = "EXTERNAL_SUBJECT_ID"


@dataclass(frozen=True)
class LegalName:
    given_names: tuple[str, ...]
    family_name: str
    middle_names: tuple[str, ...] = ()
    honorific: str | None = None
    suffix: str | None = None

    def __post_init__(self) -> None:
        if not self.given_names or not all(
            value.strip() for value in self.given_names
        ):
            raise ValueError("LEGAL_GIVEN_NAME_REQUIRED")
        if not self.family_name.strip():
            raise ValueError("LEGAL_FAMILY_NAME_REQUIRED")


@dataclass(frozen=True)
class IdentityName:
    name_type: NameType
    display_name: str
    source: str | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None

    def __post_init__(self) -> None:
        if not self.display_name.strip():
            raise ValueError("IDENTITY_NAME_REQUIRED")
        if (
            self.effective_from is not None
            and self.effective_until is not None
            and self.effective_until <= self.effective_from
        ):
            raise ValueError("INVALID_IDENTITY_NAME_PERIOD")


@dataclass(frozen=True)
class ContactPoint:
    contact_type: ContactPointType
    value: str
    verified: bool = False
    primary: bool = False

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("CONTACT_POINT_VALUE_REQUIRED")
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class IdentityAddress:
    address_type: AddressType
    line1: str
    locality: str
    country_code: str
    line2: str | None = None
    region: str | None = None
    postal_code: str | None = None

    def __post_init__(self) -> None:
        if not self.line1.strip() or not self.locality.strip():
            raise ValueError("IDENTITY_ADDRESS_REQUIRED")
        country_code = self.country_code.strip().upper()
        if len(country_code) != 2:
            raise ValueError("INVALID_COUNTRY_CODE")
        object.__setattr__(self, "country_code", country_code)


@dataclass(frozen=True)
class IdentityIdentifier:
    identifier_type: IdentifierType
    value: str
    issuer: str | None = None
    jurisdiction: str | None = None
    primary: bool = False
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("IDENTITY_IDENTIFIER_REQUIRED")
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until <= self.valid_from
        ):
            raise ValueError("INVALID_IDENTIFIER_PERIOD")
        object.__setattr__(self, "value", normalized)


class IdentityStatus(StrEnum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"
    DELETED = "DELETED"


TRANSITIONS = {
    IdentityStatus.PENDING_VERIFICATION: {IdentityStatus.ACTIVE},
    IdentityStatus.ACTIVE: {
        IdentityStatus.LOCKED,
        IdentityStatus.SUSPENDED,
        IdentityStatus.DISABLED,
    },
    IdentityStatus.LOCKED: {IdentityStatus.ACTIVE, IdentityStatus.DISABLED},
    IdentityStatus.SUSPENDED: {IdentityStatus.ACTIVE, IdentityStatus.DISABLED},
    IdentityStatus.DISABLED: {IdentityStatus.DELETED},
    IdentityStatus.DELETED: set(),
}


@dataclass(frozen=True)
class RequestContext:
    tenant_id: str
    actor_identity_id: str
    actor_membership_id: str
    correlation_id: str
    request_id: str
    authentication_strength: str

    def __post_init__(self) -> None:
        if not all(vars(self).values()):
            raise ValueError("TENANT_CONTEXT_REQUIRED")


@dataclass(frozen=True)
class Identity:
    identity_id: str
    tenant_id: str
    normalized_email: str
    status: IdentityStatus = IdentityStatus.PENDING_VERIFICATION
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 1

    identity_type: IdentityType = IdentityType.PERSON
    legal_name: LegalName | None = None
    preferred_name: str | None = None
    alternative_names: tuple[IdentityName, ...] = ()
    contact_points: tuple[ContactPoint, ...] = ()
    addresses: tuple[IdentityAddress, ...] = ()
    identifiers: tuple[IdentityIdentifier, ...] = ()
    verification_status: VerificationStatus = (
        VerificationStatus.UNVERIFIED
    )
    assurance_level: AssuranceLevel = AssuranceLevel.NID_AL0
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition(self, target: IdentityStatus) -> "Identity":
        if target not in TRANSITIONS[self.status]:
            raise ValueError("INVALID_IDENTITY_TRANSITION")
        return replace(self, status=target, updated_at=utcnow(), version=self.version + 1)


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    name: str
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 1


@dataclass(frozen=True)
class TenantMembership:
    membership_id: str
    tenant_id: str
    identity_id: str
    role: str
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 1


@dataclass(frozen=True)
class SecurityEvent:
    event_id: str
    event_type: str
    severity: str
    tenant_id: str
    actor_identity_id: str
    subject_identity_id: str
    correlation_id: str
    request_id: str
    outcome: str
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=utcnow)
    recorded_at: datetime = field(default_factory=utcnow)
    schema_version: int = 1


class AuthenticationDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_MFA = "REQUIRE_MFA"
    REQUIRE_STEP_UP = "REQUIRE_STEP_UP"
    LOCK_IDENTITY = "LOCK_IDENTITY"
    LOCK_SESSION = "LOCK_SESSION"
    REQUIRE_RECOVERY = "REQUIRE_RECOVERY"


@dataclass(frozen=True)
class AuthenticationPolicy:
    policy_version: str = "2026-07-18.1"

    def evaluate(
        self,
        *,
        identity_status: IdentityStatus | None,
        membership_active: bool | None,
        credential_active: bool | None,
        risk_score: float | None,
        authentication_strength: str | None,
    ) -> tuple[AuthenticationDecision, tuple[str, ...]]:
        if None in {identity_status, membership_active, credential_active, risk_score}:
            return AuthenticationDecision.DENY, ("MALFORMED_CONTEXT",)
        if identity_status is not IdentityStatus.ACTIVE:
            return AuthenticationDecision.DENY, (f"IDENTITY_{identity_status}",)
        if not membership_active or not credential_active:
            return AuthenticationDecision.DENY, ("INACTIVE_SECURITY_BINDING",)
        if risk_score >= 0.9:
            return AuthenticationDecision.LOCK_IDENTITY, ("CRITICAL_RISK",)
        if risk_score >= 0.6:
            return AuthenticationDecision.REQUIRE_STEP_UP, ("ELEVATED_RISK",)
        if authentication_strength == "PASSWORD":
            return AuthenticationDecision.REQUIRE_MFA, ("MFA_REQUIRED",)
        return AuthenticationDecision.ALLOW, ("CONTROLS_SATISFIED",)
