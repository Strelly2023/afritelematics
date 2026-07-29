from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from fnmatch import fnmatchcase

from .models import (
    AUTHENTICATION_STRENGTH_ORDER,
    AssuranceLevel,
    AuthenticationStrength,
    MembershipStatus,
    TenantMembership,
    utcnow,
)


ASSURANCE_LEVEL_ORDER = {
    AssuranceLevel.NID_AL0: 0,
    AssuranceLevel.NID_AL1: 10,
    AssuranceLevel.NID_AL2: 20,
    AssuranceLevel.NID_AL3: 30,
    AssuranceLevel.NID_AL4: 40,
}


class PermissionEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class AuthorizationOutcome(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_STEP_UP = "REQUIRE_STEP_UP"


@dataclass(frozen=True, order=True)
class Permission:
    resource: str
    action: str
    effect: PermissionEffect = PermissionEffect.ALLOW
    tenant_id: str | None = None
    resource_owner_only: bool = False
    require_trusted_device: bool = False
    minimum_assurance_level: AssuranceLevel = AssuranceLevel.NID_AL0
    minimum_authentication_strength: AuthenticationStrength = AuthenticationStrength.PASSWORD

    def __post_init__(self) -> None:
        if not self.resource.strip() or not self.action.strip():
            raise ValueError("INVALID_PERMISSION")
        object.__setattr__(self, "resource", self.resource.strip().lower())
        object.__setattr__(self, "action", self.action.strip().lower())
        object.__setattr__(self, "effect", PermissionEffect(self.effect))
        object.__setattr__(
            self, "minimum_assurance_level", AssuranceLevel(self.minimum_assurance_level)
        )
        object.__setattr__(
            self,
            "minimum_authentication_strength",
            AuthenticationStrength(self.minimum_authentication_strength),
        )

    @property
    def key(self) -> str:
        return f"{self.resource}:{self.action}"

    def matches(self, resource: str, action: str) -> bool:
        return fnmatchcase(resource.lower(), self.resource) and fnmatchcase(
            action.lower(), self.action
        )


@dataclass(frozen=True)
class Role:
    role_id: str
    tenant_id: str
    name: str
    permissions: frozenset[Permission] = field(default_factory=frozenset)
    enabled: bool = True
    version: int = 1

    def __post_init__(self) -> None:
        if not self.role_id.strip() or not self.tenant_id.strip() or not self.name.strip():
            raise ValueError("INVALID_ROLE")
        if self.version < 1:
            raise ValueError("INVALID_AGGREGATE_VERSION")
        object.__setattr__(self, "role_id", self.role_id.strip())
        object.__setattr__(self, "tenant_id", self.tenant_id.strip())
        object.__setattr__(self, "name", self.name.strip().upper())
        object.__setattr__(self, "permissions", frozenset(self.permissions))


@dataclass(frozen=True)
class AuthorizationContext:
    tenant_id: str
    actor_identity_id: str
    actor_membership_id: str
    resource: str
    action: str
    correlation_id: str
    request_id: str
    authentication_strength: AuthenticationStrength
    assurance_level: AssuranceLevel = AssuranceLevel.NID_AL0
    resource_tenant_id: str | None = None
    resource_owner_id: str | None = None
    device_trusted: bool = False
    risk_score: float = 0.0
    evaluated_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        required = (
            self.tenant_id,
            self.actor_identity_id,
            self.actor_membership_id,
            self.resource,
            self.action,
            self.correlation_id,
            self.request_id,
        )
        if not all(value and value.strip() for value in required):
            raise ValueError("AUTHORIZATION_CONTEXT_REQUIRED")
        if not 0 <= self.risk_score <= 1:
            raise ValueError("INVALID_RISK_SCORE")
        object.__setattr__(
            self, "authentication_strength", AuthenticationStrength(self.authentication_strength)
        )
        object.__setattr__(self, "assurance_level", AssuranceLevel(self.assurance_level))


@dataclass(frozen=True)
class AuthorizationDecision:
    outcome: AuthorizationOutcome
    reason_codes: tuple[str, ...]
    policy_version: str
    matched_permissions: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.outcome is AuthorizationOutcome.ALLOW


@dataclass(frozen=True)
class AuthorizationPolicyEngine:
    policy_version: str = "NID-P1-002.1"
    deny_risk_threshold: float = 0.9
    step_up_risk_threshold: float = 0.6

    def evaluate(
        self,
        *,
        context: AuthorizationContext,
        membership: TenantMembership | None,
        roles: tuple[Role, ...] = (),
    ) -> AuthorizationDecision:
        if membership is None:
            return self._deny("MEMBERSHIP_NOT_FOUND")
        if context.resource_tenant_id not in (None, context.tenant_id):
            return self._deny("CROSS_TENANT_RESOURCE")
        if membership.tenant_id != context.tenant_id:
            return self._deny("CROSS_TENANT_MEMBERSHIP")
        if membership.identity_id != context.actor_identity_id:
            return self._deny("ACTOR_MEMBERSHIP_MISMATCH")
        if membership.membership_id != context.actor_membership_id:
            return self._deny("MEMBERSHIP_CONTEXT_MISMATCH")
        if membership.status is not MembershipStatus.ACTIVE:
            return self._deny(f"MEMBERSHIP_{membership.status.value}")
        if not membership.is_effective(now=context.evaluated_at):
            return self._deny("MEMBERSHIP_NOT_EFFECTIVE")
        if context.risk_score >= self.deny_risk_threshold:
            return self._deny("CRITICAL_RISK")

        active_roles = tuple(
            role
            for role in roles
            if role.enabled
            and role.tenant_id == context.tenant_id
            and role.name in membership.roles
        )
        permissions = {
            permission
            for role in active_roles
            for permission in role.permissions
            if permission.tenant_id in (None, context.tenant_id)
            and permission.matches(context.resource, context.action)
        }
        for key in membership.direct_permissions:
            if ":" not in key:
                continue
            direct_permission = Permission(*key.split(":", 1))
            if direct_permission.matches(context.resource, context.action):
                permissions.add(direct_permission)
        if any(permission.effect is PermissionEffect.DENY for permission in permissions):
            return self._deny(
                "EXPLICIT_DENY",
                matched=tuple(sorted(permission.key for permission in permissions)),
            )
        allowed = tuple(
            permission
            for permission in permissions
            if permission.effect is PermissionEffect.ALLOW
        )
        if not allowed:
            return self._deny("PERMISSION_NOT_GRANTED")
        if context.risk_score >= self.step_up_risk_threshold:
            return self._step_up("ELEVATED_RISK", allowed)
        trusted_device_required = any(
            permission.require_trusted_device for permission in allowed
        )
        if trusted_device_required and not context.device_trusted:
            return self._step_up("TRUSTED_DEVICE_REQUIRED", allowed)
        if any(
            ASSURANCE_LEVEL_ORDER[context.assurance_level]
            < ASSURANCE_LEVEL_ORDER[permission.minimum_assurance_level]
            for permission in allowed
        ):
            return self._step_up("ASSURANCE_LEVEL_INSUFFICIENT", allowed)
        if any(
            AUTHENTICATION_STRENGTH_ORDER[context.authentication_strength]
            < AUTHENTICATION_STRENGTH_ORDER[permission.minimum_authentication_strength]
            for permission in allowed
        ):
            return self._step_up("AUTHENTICATION_STRENGTH_INSUFFICIENT", allowed)
        owner_permissions = tuple(
            permission for permission in allowed if permission.resource_owner_only
        )
        if owner_permissions and context.resource_owner_id != context.actor_identity_id:
            return self._deny(
                "RESOURCE_OWNERSHIP_REQUIRED",
                matched=tuple(sorted(permission.key for permission in owner_permissions)),
            )
        return AuthorizationDecision(
            outcome=AuthorizationOutcome.ALLOW,
            reason_codes=("PERMISSION_GRANTED",),
            policy_version=self.policy_version,
            matched_permissions=tuple(sorted(permission.key for permission in allowed)),
        )

    def _deny(
        self, reason: str, *, matched: tuple[str, ...] = ()
    ) -> AuthorizationDecision:
        return AuthorizationDecision(
            AuthorizationOutcome.DENY, (reason,), self.policy_version, matched
        )

    def _step_up(
        self, reason: str, permissions: tuple[Permission, ...]
    ) -> AuthorizationDecision:
        return AuthorizationDecision(
            AuthorizationOutcome.REQUIRE_STEP_UP,
            (reason,),
            self.policy_version,
            tuple(sorted(permission.key for permission in permissions)),
        )
