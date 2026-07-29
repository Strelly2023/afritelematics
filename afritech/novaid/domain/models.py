#afritech/novaid/domain/models.py
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


class TenantType(StrEnum):
    ORGANISATION = "ORGANISATION"
    GOVERNMENT = "GOVERNMENT"
    BUSINESS = "BUSINESS"
    NON_PROFIT = "NON_PROFIT"
    EDUCATION = "EDUCATION"
    HEALTHCARE = "HEALTHCARE"
    SANDBOX = "SANDBOX"


class TenantTier(StrEnum):
    FREE = "FREE"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"
    GOVERNMENT = "GOVERNMENT"


class TenantStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"


class MembershipStatus(StrEnum):
    INVITED = "INVITED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


MEMBERSHIP_TRANSITIONS = {
    MembershipStatus.INVITED: {
        MembershipStatus.ACTIVE,
        MembershipStatus.REVOKED,
        MembershipStatus.EXPIRED,
    },
    MembershipStatus.ACTIVE: {
        MembershipStatus.SUSPENDED,
        MembershipStatus.REVOKED,
        MembershipStatus.EXPIRED,
    },
    MembershipStatus.SUSPENDED: {
        MembershipStatus.ACTIVE,
        MembershipStatus.REVOKED,
        MembershipStatus.EXPIRED,
    },
    MembershipStatus.REVOKED: set(),
    MembershipStatus.EXPIRED: set(),
}


class AuthenticationStrength(StrEnum):
    PASSWORD = "PASSWORD"
    PASSWORD_OTP = "PASSWORD_OTP"
    MFA = "MFA"
    FIDO2 = "FIDO2"
    PASSKEY = "PASSKEY"
    CERTIFICATE = "CERTIFICATE"
    PHISHING_RESISTANT = "PHISHING_RESISTANT"


AUTHENTICATION_STRENGTH_ORDER = {
    AuthenticationStrength.PASSWORD: 10,
    AuthenticationStrength.PASSWORD_OTP: 20,
    AuthenticationStrength.MFA: 20,
    AuthenticationStrength.FIDO2: 30,
    AuthenticationStrength.PASSKEY: 30,
    AuthenticationStrength.CERTIFICATE: 30,
    AuthenticationStrength.PHISHING_RESISTANT: 40,
}


PHISHING_RESISTANT_STRENGTHS = frozenset(
    {
        AuthenticationStrength.FIDO2,
        AuthenticationStrength.PASSKEY,
        AuthenticationStrength.CERTIFICATE,
        AuthenticationStrength.PHISHING_RESISTANT,
    }
)


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


TENANT_TRANSITIONS = {
    TenantStatus.ACTIVE: {
        TenantStatus.SUSPENDED,
        TenantStatus.DISABLED,
    },
    TenantStatus.SUSPENDED: {
        TenantStatus.ACTIVE,
        TenantStatus.DISABLED,
    },
    TenantStatus.DISABLED: {
        TenantStatus.ACTIVE,
    },
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
class LegalEntity:
    legal_name: str
    registration_number: str | None = None
    tax_identifier: str | None = None
    country_code: str = "AU"

    def __post_init__(self) -> None:
        legal_name = self.legal_name.strip()

        if not legal_name:
            raise ValueError(
                "LEGAL_ENTITY_NAME_REQUIRED"
            )

        country_code = self.country_code.strip().upper()

        if (
            len(country_code) != 2
            or not country_code.isalpha()
        ):
            raise ValueError(
                "INVALID_COUNTRY_CODE"
            )

        registration_number = (
            self.registration_number.strip()
            if self.registration_number
            else None
        )
        tax_identifier = (
            self.tax_identifier.strip()
            if self.tax_identifier
            else None
        )

        object.__setattr__(
            self,
            "legal_name",
            legal_name,
        )
        object.__setattr__(
            self,
            "registration_number",
            registration_number or None,
        )
        object.__setattr__(
            self,
            "tax_identifier",
            tax_identifier or None,
        )
        object.__setattr__(
            self,
            "country_code",
            country_code,
        )


@dataclass(frozen=True)
class TenantBrand:
    display_name: str
    short_name: str | None = None
    primary_domain: str | None = None
    support_email: str | None = None

    def __post_init__(self) -> None:
        display_name = self.display_name.strip()

        if not display_name:
            raise ValueError(
                "TENANT_BRAND_NAME_REQUIRED"
            )

        short_name = (
            self.short_name.strip()
            if self.short_name
            else None
        )
        primary_domain = (
            self.primary_domain.strip().lower()
            if self.primary_domain
            else None
        )
        support_email = (
            self.support_email.strip().lower()
            if self.support_email
            else None
        )

        object.__setattr__(
            self,
            "display_name",
            display_name,
        )
        object.__setattr__(
            self,
            "short_name",
            short_name or None,
        )
        object.__setattr__(
            self,
            "primary_domain",
            primary_domain or None,
        )
        object.__setattr__(
            self,
            "support_email",
            support_email or None,
        )


@dataclass(frozen=True)
class TenantSettings:
    self_registration_enabled: bool = False
    identity_verification_required: bool = True
    passkeys_enabled: bool = True
    federation_enabled: bool = False
    scim_enabled: bool = False
    api_access_enabled: bool = True
    audit_retention_days: int = 2555
    default_language: str = "en"
    supported_languages: tuple[str, ...] = (
        "en",
        "fr",
        "sw",
    )
    feature_flags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.audit_retention_days < 1:
            raise ValueError(
                "INVALID_AUDIT_RETENTION_DAYS"
            )

        default_language = self.default_language.strip().lower()

        if not default_language:
            raise ValueError(
                "TENANT_DEFAULT_LANGUAGE_REQUIRED"
            )

        supported_languages = tuple(
            dict.fromkeys(
                language.strip().lower()
                for language in self.supported_languages
                if language and language.strip()
            )
        )

        if not supported_languages:
            raise ValueError(
                "TENANT_SUPPORTED_LANGUAGE_REQUIRED"
            )

        if default_language not in supported_languages:
            raise ValueError(
                "TENANT_DEFAULT_LANGUAGE_NOT_SUPPORTED"
            )

        feature_flags = frozenset(
            flag.strip().lower()
            for flag in self.feature_flags
            if flag and flag.strip()
        )

        object.__setattr__(
            self,
            "default_language",
            default_language,
        )
        object.__setattr__(
            self,
            "supported_languages",
            supported_languages,
        )
        object.__setattr__(
            self,
            "feature_flags",
            feature_flags,
        )

    def supports_language(
        self,
        language: str,
    ) -> bool:
        normalized = language.strip().lower()

        return (
            bool(normalized)
            and normalized in self.supported_languages
        )

    def feature_enabled(
        self,
        feature: str,
    ) -> bool:
        normalized = feature.strip().lower()

        return (
            bool(normalized)
            and normalized in self.feature_flags
        )


@dataclass(frozen=True)
class TenantSecurityPolicy:
    minimum_authentication_strength: AuthenticationStrength = (
        AuthenticationStrength.PASSWORD_OTP
    )
    minimum_assurance_level: AssuranceLevel = (
        AssuranceLevel.NID_AL1
    )

    mfa_required: bool = True
    phishing_resistant_authentication_required: bool = False
    device_binding_required: bool = False

    session_idle_timeout_minutes: int = 30
    session_absolute_timeout_minutes: int = 720
    maximum_concurrent_sessions: int = 5
    maximum_registered_devices: int = 10

    minimum_password_length: int = 12
    password_history_count: int = 10
    password_rotation_days: int | None = None

    risk_step_up_threshold: float = 0.60
    risk_lock_threshold: float = 0.90

    audit_logging_required: bool = True
    immutable_audit_required: bool = True
    pii_encryption_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "minimum_authentication_strength",
            AuthenticationStrength(
                self.minimum_authentication_strength
            ),
        )
        object.__setattr__(
            self,
            "minimum_assurance_level",
            AssuranceLevel(
                self.minimum_assurance_level
            ),
        )

        if self.session_idle_timeout_minutes < 1:
            raise ValueError(
                "INVALID_SESSION_IDLE_TIMEOUT"
            )

        if (
            self.session_absolute_timeout_minutes
            < self.session_idle_timeout_minutes
        ):
            raise ValueError(
                "INVALID_SESSION_ABSOLUTE_TIMEOUT"
            )

        if self.maximum_concurrent_sessions < 1:
            raise ValueError(
                "INVALID_MAXIMUM_CONCURRENT_SESSIONS"
            )

        if self.maximum_registered_devices < 1:
            raise ValueError(
                "INVALID_MAXIMUM_REGISTERED_DEVICES"
            )

        if self.minimum_password_length < 8:
            raise ValueError(
                "MINIMUM_PASSWORD_LENGTH_TOO_SHORT"
            )

        if self.password_history_count < 0:
            raise ValueError(
                "INVALID_PASSWORD_HISTORY_COUNT"
            )

        if (
            self.password_rotation_days is not None
            and self.password_rotation_days < 1
        ):
            raise ValueError(
                "INVALID_PASSWORD_ROTATION_DAYS"
            )

        if not 0 <= self.risk_step_up_threshold <= 1:
            raise ValueError(
                "INVALID_RISK_STEP_UP_THRESHOLD"
            )

        if not 0 <= self.risk_lock_threshold <= 1:
            raise ValueError(
                "INVALID_RISK_LOCK_THRESHOLD"
            )

        if self.risk_step_up_threshold >= self.risk_lock_threshold:
            raise ValueError(
                "INVALID_RISK_THRESHOLD_ORDER"
            )

        if (
            self.phishing_resistant_authentication_required
            and self.minimum_authentication_strength
            not in PHISHING_RESISTANT_STRENGTHS
        ):
            raise ValueError(
                "PHISHING_RESISTANT_STRENGTH_REQUIRED"
            )

        if (
            self.mfa_required
            and AUTHENTICATION_STRENGTH_ORDER[
                self.minimum_authentication_strength
            ]
            < AUTHENTICATION_STRENGTH_ORDER[
                AuthenticationStrength.PASSWORD_OTP
            ]
        ):
            raise ValueError(
                "MFA_CAPABLE_STRENGTH_REQUIRED"
            )

    def allows_authentication_strength(
        self,
        authentication_strength: AuthenticationStrength | str,
    ) -> bool:
        try:
            normalized = AuthenticationStrength(
                authentication_strength
            )
        except ValueError:
            return False

        if (
            self.phishing_resistant_authentication_required
            and normalized not in PHISHING_RESISTANT_STRENGTHS
        ):
            return False

        return (
            AUTHENTICATION_STRENGTH_ORDER[normalized]
            >= AUTHENTICATION_STRENGTH_ORDER[
                self.minimum_authentication_strength
            ]
        )

    def requires_step_up(
        self,
        *,
        authentication_strength: AuthenticationStrength | str,
        risk_score: float,
    ) -> bool:
        if not 0 <= risk_score <= 1:
            raise ValueError("INVALID_RISK_SCORE")

        if risk_score >= self.risk_lock_threshold:
            return False

        if risk_score >= self.risk_step_up_threshold:
            return True

        return not self.allows_authentication_strength(
            authentication_strength
        )

    def requires_lock(
        self,
        *,
        risk_score: float,
    ) -> bool:
        if not 0 <= risk_score <= 1:
            raise ValueError("INVALID_RISK_SCORE")

        return risk_score >= self.risk_lock_threshold


@dataclass(frozen=True)
class Tenant:
    # Existing positional fields remain in this order for compatibility.
    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 1

    # Canonical tenant fields are appended.
    tenant_type: TenantType = TenantType.ORGANISATION
    tier: TenantTier = TenantTier.STANDARD

    legal_entity: LegalEntity | None = None
    brand: TenantBrand | None = None
    settings: TenantSettings = field(
        default_factory=TenantSettings
    )
    security_policy: TenantSecurityPolicy = field(
        default_factory=TenantSecurityPolicy
    )

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        tenant_id = self.tenant_id.strip()
        name = self.name.strip()

        if not tenant_id:
            raise ValueError("TENANT_ID_REQUIRED")

        if not name:
            raise ValueError("TENANT_NAME_REQUIRED")

        if self.version < 1:
            raise ValueError("INVALID_AGGREGATE_VERSION")

        object.__setattr__(
            self,
            "tenant_id",
            tenant_id,
        )
        object.__setattr__(
            self,
            "name",
            name,
        )
        object.__setattr__(
            self,
            "status",
            TenantStatus(self.status),
        )
        object.__setattr__(
            self,
            "tenant_type",
            TenantType(self.tenant_type),
        )
        object.__setattr__(
            self,
            "tier",
            TenantTier(self.tier),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    def transition(
        self,
        target: TenantStatus,
    ) -> "Tenant":
        normalized_target = TenantStatus(target)

        if normalized_target not in TENANT_TRANSITIONS[self.status]:
            raise ValueError("INVALID_TENANT_TRANSITION")

        return replace(
            self,
            status=normalized_target,
            updated_at=utcnow(),
            version=self.version + 1,
        )


@dataclass(frozen=True)
class TenantMembership:
    membership_id: str
    tenant_id: str
    identity_id: str
    role: str
    status: MembershipStatus = MembershipStatus.ACTIVE
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 1
    roles: frozenset[str] = field(default_factory=frozenset)
    direct_permissions: frozenset[str] = field(default_factory=frozenset)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, reason in (
            (self.membership_id, "MEMBERSHIP_ID_REQUIRED"),
            (self.tenant_id, "TENANT_ID_REQUIRED"),
            (self.identity_id, "IDENTITY_ID_REQUIRED"),
            (self.role, "MEMBERSHIP_ROLE_REQUIRED"),
        ):
            if not value.strip():
                raise ValueError(reason)
        if self.version < 1:
            raise ValueError("INVALID_AGGREGATE_VERSION")
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("INVALID_MEMBERSHIP_VALIDITY")
        normalized_roles = frozenset(
            {self.role.strip().upper()}
            | {role.strip().upper() for role in self.roles if role.strip()}
        )
        object.__setattr__(self, "membership_id", self.membership_id.strip())
        object.__setattr__(self, "tenant_id", self.tenant_id.strip())
        object.__setattr__(self, "identity_id", self.identity_id.strip())
        object.__setattr__(self, "role", self.role.strip().upper())
        object.__setattr__(self, "status", MembershipStatus(self.status))
        object.__setattr__(self, "roles", normalized_roles)
        object.__setattr__(
            self,
            "direct_permissions",
            frozenset(
                permission.strip().lower()
                for permission in self.direct_permissions
                if permission.strip()
            ),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    def transition(
        self,
        target: MembershipStatus | str,
        *,
        now: datetime | None = None,
    ) -> "TenantMembership":
        normalized_target = MembershipStatus(target)
        if normalized_target not in MEMBERSHIP_TRANSITIONS[self.status]:
            raise ValueError("INVALID_MEMBERSHIP_TRANSITION")
        transition_time = now or utcnow()
        return replace(
            self,
            status=normalized_target,
            updated_at=transition_time,
            version=self.version + 1,
        )

    def is_effective(self, *, now: datetime | None = None) -> bool:
        evaluation_time = now or utcnow()
        return (
            self.status is MembershipStatus.ACTIVE
            and (self.valid_from is None or evaluation_time >= self.valid_from)
            and (self.valid_until is None or evaluation_time < self.valid_until)
        )


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
