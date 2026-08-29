"""Production actor, federation, privileged-access, and machine-identity policy.

This module is deliberately protocol and storage agnostic.  It contains the
fail-closed domain rules used by API/persistence adapters; it does not pretend
that an IdP assertion, certificate, or device attestation is valid merely
because a client supplied it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Mapping
from uuid import uuid4

from .models import AssuranceLevel, AuthenticationStrength


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ProductionActorType(StrEnum):
    RIDER = "RIDER"
    DRIVER = "DRIVER"
    FLEET_MANAGER = "FLEET_MANAGER"
    DISPATCHER = "DISPATCHER"
    OPERATOR = "OPERATOR"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    SAFETY_AGENT = "SAFETY_AGENT"
    FINANCE_OFFICER = "FINANCE_OFFICER"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    BUSINESS_CUSTOMER = "BUSINESS_CUSTOMER"
    ADMINISTRATOR = "ADMINISTRATOR"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"
    DEVICE = "DEVICE"

    @property
    def is_machine(self) -> bool:
        return self in {self.SERVICE_ACCOUNT, self.DEVICE}

    @property
    def is_staff(self) -> bool:
        return self in {
            self.DISPATCHER,
            self.OPERATOR,
            self.SUPPORT_AGENT,
            self.SAFETY_AGENT,
            self.FINANCE_OFFICER,
            self.COMPLIANCE_OFFICER,
            self.ADMINISTRATOR,
        }


@dataclass(frozen=True)
class FederatedStaffIdentity:
    """Server-validated SSO result, never a raw client assertion."""

    tenant_id: str
    issuer: str
    subject: str
    audience: str
    actor_type: ProductionActorType
    authenticated_at: datetime
    expires_at: datetime
    assertion_id: str
    signature_verified: bool
    nonce_verified: bool
    groups: frozenset[str] = field(default_factory=frozenset)

    def validate(self, *, expected_tenant_id: str, expected_audience: str, now: datetime | None = None) -> None:
        instant = now or _utcnow()
        if self.tenant_id != expected_tenant_id:
            raise PermissionError("CROSS_TENANT_FEDERATION_DENIED")
        if not self.actor_type.is_staff:
            raise PermissionError("STAFF_SSO_ACTOR_REQUIRED")
        if self.audience != expected_audience:
            raise PermissionError("FEDERATION_AUDIENCE_MISMATCH")
        if not self.signature_verified or not self.nonce_verified:
            raise PermissionError("FEDERATION_PROOF_INVALID")
        if self.authenticated_at > instant or self.expires_at <= instant:
            raise PermissionError("FEDERATION_ASSERTION_EXPIRED")
        if not all((self.issuer.strip(), self.subject.strip(), self.assertion_id.strip())):
            raise PermissionError("FEDERATION_SUBJECT_INVALID")


class PrivilegedAccessStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DENIED = "DENIED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class PrivilegedAccessGrant:
    grant_id: str
    tenant_id: str
    subject_identity_id: str
    requested_by: str
    permission: str
    justification: str
    requested_at: datetime
    expires_at: datetime
    status: PrivilegedAccessStatus = PrivilegedAccessStatus.PENDING
    approved_by: str | None = None
    activated_at: datetime | None = None
    revoked_by: str | None = None
    revocation_reason: str | None = None
    version: int = 1

    @classmethod
    def request(cls, *, tenant_id: str, subject_identity_id: str, requested_by: str,
                permission: str, justification: str, expires_at: datetime,
                now: datetime | None = None) -> "PrivilegedAccessGrant":
        instant = now or _utcnow()
        values = (tenant_id, subject_identity_id, requested_by, permission, justification)
        if not all(value.strip() for value in values):
            raise ValueError("PRIVILEGED_ACCESS_CONTEXT_REQUIRED")
        if expires_at <= instant:
            raise ValueError("PRIVILEGED_ACCESS_EXPIRY_REQUIRED")
        return cls(str(uuid4()), tenant_id, subject_identity_id, requested_by,
                   permission.lower(), justification, instant, expires_at)

    def approve(self, *, approver_identity_id: str, tenant_id: str,
                authentication_strength: AuthenticationStrength,
                assurance_level: AssuranceLevel, trusted_device: bool,
                now: datetime | None = None) -> "PrivilegedAccessGrant":
        instant = now or _utcnow()
        if tenant_id != self.tenant_id:
            raise PermissionError("CROSS_TENANT_PRIVILEGE_DENIED")
        if self.status is not PrivilegedAccessStatus.PENDING or instant >= self.expires_at:
            raise PermissionError("PRIVILEGED_ACCESS_REQUEST_NOT_PENDING")
        if approver_identity_id in {self.requested_by, self.subject_identity_id}:
            raise PermissionError("PRIVILEGED_ACCESS_SELF_APPROVAL_DENIED")
        if AuthenticationStrength(authentication_strength) not in {
            AuthenticationStrength.FIDO2, AuthenticationStrength.PASSKEY,
            AuthenticationStrength.CERTIFICATE, AuthenticationStrength.PHISHING_RESISTANT,
        }:
            raise PermissionError("PRIVILEGED_ACCESS_STEP_UP_REQUIRED")
        if AssuranceLevel(assurance_level) not in {AssuranceLevel.NID_AL3, AssuranceLevel.NID_AL4}:
            raise PermissionError("PRIVILEGED_ACCESS_ASSURANCE_INSUFFICIENT")
        if not trusted_device:
            raise PermissionError("PRIVILEGED_ACCESS_TRUSTED_DEVICE_REQUIRED")
        return replace(self, status=PrivilegedAccessStatus.ACTIVE,
                       approved_by=approver_identity_id, activated_at=instant,
                       version=self.version + 1)

    def is_effective(self, *, tenant_id: str, subject_identity_id: str,
                     permission: str, now: datetime | None = None) -> bool:
        instant = now or _utcnow()
        return (
            self.status is PrivilegedAccessStatus.ACTIVE
            and self.tenant_id == tenant_id
            and self.subject_identity_id == subject_identity_id
            and self.permission == permission.lower()
            and self.activated_at is not None
            and self.activated_at <= instant < self.expires_at
        )

    def revoke(self, *, actor_identity_id: str, reason: str,
               tenant_id: str) -> "PrivilegedAccessGrant":
        if tenant_id != self.tenant_id:
            raise PermissionError("CROSS_TENANT_PRIVILEGE_DENIED")
        if self.status not in {PrivilegedAccessStatus.PENDING, PrivilegedAccessStatus.ACTIVE}:
            raise PermissionError("PRIVILEGED_ACCESS_NOT_REVOCABLE")
        if not actor_identity_id.strip() or not reason.strip():
            raise ValueError("PRIVILEGED_ACCESS_REVOCATION_CONTEXT_REQUIRED")
        return replace(self, status=PrivilegedAccessStatus.REVOKED,
                       revoked_by=actor_identity_id, revocation_reason=reason,
                       version=self.version + 1)


class MachineCredentialStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ROTATED = "ROTATED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class MachineCredential:
    credential_id: str
    tenant_id: str
    actor_id: str
    actor_type: ProductionActorType
    public_key_fingerprint: str
    issued_at: datetime
    expires_at: datetime
    scopes: frozenset[str]
    status: MachineCredentialStatus = MachineCredentialStatus.ACTIVE
    bound_device_id: str | None = None
    replaced_by: str | None = None

    @classmethod
    def issue(cls, *, tenant_id: str, actor_id: str, actor_type: ProductionActorType,
              public_key_der: bytes, scopes: frozenset[str], expires_at: datetime,
              bound_device_id: str | None = None, now: datetime | None = None) -> "MachineCredential":
        instant = now or _utcnow()
        actor_type = ProductionActorType(actor_type)
        if not actor_type.is_machine:
            raise ValueError("MACHINE_ACTOR_REQUIRED")
        if not tenant_id.strip() or not actor_id.strip() or not public_key_der or not scopes:
            raise ValueError("MACHINE_CREDENTIAL_CONTEXT_REQUIRED")
        if expires_at <= instant:
            raise ValueError("MACHINE_CREDENTIAL_EXPIRY_REQUIRED")
        if actor_type is ProductionActorType.DEVICE and not bound_device_id:
            raise ValueError("DEVICE_BINDING_REQUIRED")
        fingerprint = sha256(public_key_der).hexdigest()
        return cls(str(uuid4()), tenant_id, actor_id, actor_type, fingerprint,
                   instant, expires_at, frozenset(scope.lower() for scope in scopes),
                   bound_device_id=bound_device_id)

    def authorize(self, *, tenant_id: str, public_key_der: bytes, scope: str,
                  device_id: str | None = None, now: datetime | None = None) -> None:
        instant = now or _utcnow()
        if self.status is not MachineCredentialStatus.ACTIVE or instant >= self.expires_at:
            raise PermissionError("MACHINE_CREDENTIAL_INACTIVE")
        if tenant_id != self.tenant_id:
            raise PermissionError("CROSS_TENANT_MACHINE_ACCESS_DENIED")
        if sha256(public_key_der).hexdigest() != self.public_key_fingerprint:
            raise PermissionError("MACHINE_PROOF_INVALID")
        if scope.lower() not in self.scopes:
            raise PermissionError("MACHINE_SCOPE_DENIED")
        if self.actor_type is ProductionActorType.DEVICE and device_id != self.bound_device_id:
            raise PermissionError("DEVICE_BINDING_MISMATCH")

    def rotate(self, replacement: "MachineCredential") -> "MachineCredential":
        if replacement.tenant_id != self.tenant_id or replacement.actor_id != self.actor_id:
            raise PermissionError("MACHINE_ROTATION_SUBJECT_MISMATCH")
        if replacement.credential_id == self.credential_id:
            raise ValueError("MACHINE_ROTATION_REQUIRES_NEW_CREDENTIAL")
        return replace(self, status=MachineCredentialStatus.ROTATED,
                       replaced_by=replacement.credential_id)


def actor_role_bindings() -> Mapping[ProductionActorType, frozenset[str]]:
    """Canonical role names; permissions remain tenant-governed and deny by default."""
    return {actor: frozenset({actor.value}) for actor in ProductionActorType}


__all__ = [
    "FederatedStaffIdentity", "MachineCredential", "MachineCredentialStatus",
    "PrivilegedAccessGrant", "PrivilegedAccessStatus", "ProductionActorType",
    "actor_role_bindings",
]
