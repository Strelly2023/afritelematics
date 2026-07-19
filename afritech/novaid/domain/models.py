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
