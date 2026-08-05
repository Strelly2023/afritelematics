"""NovaLogistics identity references and deterministic authorization policies."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

from .domain import Identifier


class SecurityError(RuntimeError): pass
class AuthenticationRequiredError(SecurityError): pass
class InvalidPrincipalError(SecurityError): pass
class MembershipNotFoundError(SecurityError): pass
class MembershipInactiveError(SecurityError): pass
class AuthorizationDeniedError(SecurityError): pass
class PermissionMissingError(AuthorizationDeniedError): pass
class TenantMismatchError(AuthorizationDeniedError): pass
class RoleAssignmentError(SecurityError): pass
class PlatformScopeRequiredError(AuthorizationDeniedError): pass
class ServiceScopeMissingError(AuthorizationDeniedError): pass
class IdentityProviderUnavailableError(SecurityError): pass
class IdentityStatusInvalidError(SecurityError): pass


def _value(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 128 or any(char.isspace() for char in normalized):
        raise SecurityError(f"invalid {label}")
    return normalized


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise SecurityError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, order=True)
class IdentityReference:
    value: str
    authority: str = "novaid"
    contract_version: str = "novaid.identity-reference.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _value(self.value, "identity reference"))
        object.__setattr__(self, "authority", _value(self.authority.lower(), "identity authority"))

    def to_dict(self) -> dict[str, str]:
        return {"authority": self.authority, "contract_version": self.contract_version, "value": self.value}


class Role(str, Enum):
    CUSTOMER="CUSTOMER"; CUSTOMER_ADMINISTRATOR="CUSTOMER_ADMINISTRATOR"; DRIVER="DRIVER"
    DISPATCHER="DISPATCHER"; FLEET_MANAGER="FLEET_MANAGER"; WAREHOUSE_OPERATOR="WAREHOUSE_OPERATOR"
    WAREHOUSE_MANAGER="WAREHOUSE_MANAGER"; CARRIER_USER="CARRIER_USER"; SUPPLIER_USER="SUPPLIER_USER"
    FINANCE_USER="FINANCE_USER"; COMPLIANCE_USER="COMPLIANCE_USER"; SUPPORT_USER="SUPPORT_USER"
    OPERATIONS_MANAGER="OPERATIONS_MANAGER"; TENANT_ADMINISTRATOR="TENANT_ADMINISTRATOR"
    PLATFORM_ADMINISTRATOR="PLATFORM_ADMINISTRATOR"; AUDITOR="AUDITOR"; SERVICE_INTEGRATION="SERVICE_INTEGRATION"


class Permission(str, Enum):
    TENANT_READ="tenant.read"; TENANT_MANAGE="tenant.manage"; MEMBERSHIP_READ="membership.read"; MEMBERSHIP_INVITE="membership.invite"; MEMBERSHIP_ACTIVATE="membership.activate"; MEMBERSHIP_SUSPEND="membership.suspend"; MEMBERSHIP_REVOKE="membership.revoke"; ROLE_READ="role.read"; ROLE_ASSIGN="role.assign"
    CUSTOMER_READ="customer.read"; CUSTOMER_CREATE="customer.create"; CUSTOMER_UPDATE="customer.update"; CUSTOMER_ARCHIVE="customer.archive"; QUOTE_READ="quote.read"; QUOTE_CREATE="quote.create"; QUOTE_UPDATE="quote.update"; ORDER_READ="order.read"; ORDER_CREATE="order.create"; ORDER_UPDATE="order.update"; ORDER_CANCEL="order.cancel"
    SHIPMENT_READ="shipment.read"; SHIPMENT_CREATE="shipment.create"; SHIPMENT_UPDATE="shipment.update"; SHIPMENT_DISPATCH="shipment.dispatch"; SHIPMENT_CANCEL="shipment.cancel"; TRACKING_READ="tracking.read"; DELIVERY_READ="delivery.read"; DELIVERY_EXECUTE="delivery.execute"; DELIVERY_COMPLETE="delivery.complete"; POD_READ="pod.read"; POD_CREATE="pod.create"
    FLEET_READ="fleet.read"; FLEET_MANAGE="fleet.manage"; VEHICLE_READ="vehicle.read"; VEHICLE_MANAGE="vehicle.manage"; DRIVER_READ="driver.read"; DRIVER_MANAGE="driver.manage"; DISPATCH_READ="dispatch.read"; DISPATCH_MANAGE="dispatch.manage"
    WAREHOUSE_READ="warehouse.read"; WAREHOUSE_MANAGE="warehouse.manage"; INVENTORY_READ="inventory.read"; INVENTORY_ADJUST="inventory.adjust"; RECEIVING_EXECUTE="receiving.execute"; PICKING_EXECUTE="picking.execute"; PACKING_EXECUTE="packing.execute"; SHIPPING_EXECUTE="shipping.execute"
    INVOICE_READ="invoice.read"; INVOICE_MANAGE="invoice.manage"; PAYMENT_READ="payment.read"; SETTLEMENT_READ="settlement.read"; SETTLEMENT_MANAGE="settlement.manage"; REFUND_MANAGE="refund.manage"
    COMPLIANCE_READ="compliance.read"; COMPLIANCE_MANAGE="compliance.manage"; INCIDENT_READ="incident.read"; INCIDENT_MANAGE="incident.manage"; CLAIM_READ="claim.read"; CLAIM_MANAGE="claim.manage"; AUDIT_READ="audit.read"; RISK_READ="risk.read"; RISK_MANAGE="risk.manage"
    INTEGRATION_READ="integration.read"; INTEGRATION_MANAGE="integration.manage"; SERVICE_INVOKE="service.invoke"; PLATFORM_READ="platform.read"; PLATFORM_MANAGE="platform.manage"


READ_PERMISSIONS = frozenset(permission for permission in Permission if permission.value.endswith(".read"))
ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.CUSTOMER: frozenset({Permission.CUSTOMER_READ, Permission.CUSTOMER_UPDATE, Permission.QUOTE_READ, Permission.QUOTE_CREATE, Permission.ORDER_READ, Permission.ORDER_CREATE, Permission.SHIPMENT_READ, Permission.TRACKING_READ, Permission.DELIVERY_READ, Permission.POD_READ, Permission.INVOICE_READ, Permission.CLAIM_READ}),
    Role.CUSTOMER_ADMINISTRATOR: frozenset({Permission.CUSTOMER_READ, Permission.CUSTOMER_CREATE, Permission.CUSTOMER_UPDATE, Permission.QUOTE_READ, Permission.QUOTE_CREATE, Permission.QUOTE_UPDATE, Permission.ORDER_READ, Permission.ORDER_CREATE, Permission.ORDER_UPDATE, Permission.ORDER_CANCEL, Permission.SHIPMENT_READ, Permission.SHIPMENT_CREATE, Permission.SHIPMENT_UPDATE, Permission.TRACKING_READ, Permission.POD_READ, Permission.INVOICE_READ}),
    Role.DRIVER: frozenset({Permission.DELIVERY_READ, Permission.DELIVERY_EXECUTE, Permission.DELIVERY_COMPLETE, Permission.POD_CREATE, Permission.SHIPMENT_READ}),
    Role.DISPATCHER: frozenset({Permission.DISPATCH_READ, Permission.DISPATCH_MANAGE, Permission.SHIPMENT_READ, Permission.SHIPMENT_UPDATE, Permission.SHIPMENT_DISPATCH, Permission.DRIVER_READ, Permission.VEHICLE_READ}),
    Role.FLEET_MANAGER: frozenset({Permission.FLEET_READ, Permission.FLEET_MANAGE, Permission.VEHICLE_READ, Permission.VEHICLE_MANAGE, Permission.DRIVER_READ, Permission.DRIVER_MANAGE}),
    Role.WAREHOUSE_OPERATOR: frozenset({Permission.WAREHOUSE_READ, Permission.INVENTORY_READ, Permission.RECEIVING_EXECUTE, Permission.PICKING_EXECUTE, Permission.PACKING_EXECUTE, Permission.SHIPPING_EXECUTE}),
    Role.WAREHOUSE_MANAGER: frozenset({Permission.WAREHOUSE_READ, Permission.WAREHOUSE_MANAGE, Permission.INVENTORY_READ, Permission.INVENTORY_ADJUST, Permission.RECEIVING_EXECUTE, Permission.PICKING_EXECUTE, Permission.PACKING_EXECUTE, Permission.SHIPPING_EXECUTE}),
    Role.CARRIER_USER: frozenset({Permission.SHIPMENT_READ, Permission.DELIVERY_READ, Permission.POD_CREATE, Permission.SETTLEMENT_READ}),
    Role.SUPPLIER_USER: frozenset({Permission.ORDER_READ, Permission.SHIPMENT_READ, Permission.INVOICE_READ}),
    Role.FINANCE_USER: frozenset({Permission.INVOICE_READ, Permission.INVOICE_MANAGE, Permission.PAYMENT_READ, Permission.SETTLEMENT_READ, Permission.SETTLEMENT_MANAGE, Permission.REFUND_MANAGE}),
    Role.COMPLIANCE_USER: frozenset({Permission.COMPLIANCE_READ, Permission.COMPLIANCE_MANAGE, Permission.INCIDENT_READ, Permission.INCIDENT_MANAGE, Permission.CLAIM_READ, Permission.CLAIM_MANAGE, Permission.AUDIT_READ, Permission.RISK_READ}),
    Role.SUPPORT_USER: frozenset({Permission.CUSTOMER_READ, Permission.ORDER_READ, Permission.SHIPMENT_READ, Permission.TRACKING_READ, Permission.INCIDENT_READ}),
    Role.OPERATIONS_MANAGER: frozenset({Permission.SHIPMENT_READ, Permission.SHIPMENT_UPDATE, Permission.SHIPMENT_DISPATCH, Permission.DISPATCH_READ, Permission.DISPATCH_MANAGE, Permission.FLEET_READ, Permission.WAREHOUSE_READ, Permission.INCIDENT_READ}),
    Role.TENANT_ADMINISTRATOR: frozenset({Permission.TENANT_READ, Permission.TENANT_MANAGE, Permission.MEMBERSHIP_READ, Permission.MEMBERSHIP_INVITE, Permission.MEMBERSHIP_ACTIVATE, Permission.MEMBERSHIP_SUSPEND, Permission.MEMBERSHIP_REVOKE, Permission.ROLE_READ, Permission.ROLE_ASSIGN}),
    Role.PLATFORM_ADMINISTRATOR: frozenset({Permission.PLATFORM_READ, Permission.PLATFORM_MANAGE, Permission.AUDIT_READ}),
    Role.AUDITOR: READ_PERMISSIONS,
    Role.SERVICE_INTEGRATION: frozenset({Permission.INTEGRATION_READ, Permission.SERVICE_INVOKE}),
}
PLATFORM_ROLES = frozenset({Role.PLATFORM_ADMINISTRATOR})


class MembershipStatus(str, Enum):
    INVITED="invited"; ACTIVE="active"; SUSPENDED="suspended"; REVOKED="revoked"; EXPIRED="expired"


@dataclass(frozen=True)
class TenantMembership:
    id: Identifier; tenant_id: Identifier; identity: IdentityReference; status: MembershipStatus = MembershipStatus.INVITED
    roles: frozenset[Role] = frozenset(); direct_permissions: frozenset[Permission] = frozenset(); version: int = 0
    invited_at: datetime | None = None; activated_at: datetime | None = None; suspended_at: datetime | None = None
    revoked_at: datetime | None = None; expires_at: datetime | None = None; audit_actor: IdentityReference | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "roles", frozenset(Role(item) for item in self.roles))
        object.__setattr__(self, "direct_permissions", frozenset(Permission(item) for item in self.direct_permissions))
        for name in ("invited_at", "activated_at", "suspended_at", "revoked_at", "expires_at"):
            value = getattr(self, name)
            if value is not None: object.__setattr__(self, name, _utc(value))

    def transition(self, target: MembershipStatus, *, at: datetime, actor: IdentityReference) -> "TenantMembership":
        allowed = {MembershipStatus.INVITED:{MembershipStatus.ACTIVE,MembershipStatus.REVOKED,MembershipStatus.EXPIRED}, MembershipStatus.ACTIVE:{MembershipStatus.SUSPENDED,MembershipStatus.REVOKED,MembershipStatus.EXPIRED}, MembershipStatus.SUSPENDED:{MembershipStatus.ACTIVE,MembershipStatus.REVOKED,MembershipStatus.EXPIRED}}
        target = MembershipStatus(target); moment = _utc(at)
        if target == self.status: return self
        if target not in allowed.get(self.status, set()): raise MembershipInactiveError(f"invalid membership transition: {self.status.value}->{target.value}")
        fields = {"status":target,"version":self.version+1,"audit_actor":actor}
        fields[{MembershipStatus.ACTIVE:"activated_at",MembershipStatus.SUSPENDED:"suspended_at",MembershipStatus.REVOKED:"revoked_at",MembershipStatus.EXPIRED:"expires_at"}[target]] = moment
        return replace(self, **fields)

    @property
    def effective_permissions(self) -> frozenset[Permission]:
        return frozenset().union(*(ROLE_PERMISSIONS[role] for role in self.roles), self.direct_permissions)

    def assign_role(self, role: Role, *, actor_is_platform: bool=False) -> "TenantMembership":
        role = Role(role)
        if self.status is not MembershipStatus.ACTIVE: raise MembershipInactiveError("membership is inactive")
        if role in PLATFORM_ROLES and not actor_is_platform: raise RoleAssignmentError("platform role requires platform authority")
        if role in self.roles: return self
        return replace(self, roles=self.roles|{role}, version=self.version+1)


@dataclass(frozen=True)
class HumanPrincipal:
    identity: IdentityReference; tenant_id: Identifier; membership_id: Identifier; session_id: str; authenticated_at: datetime
    roles: frozenset[Role]; permissions: frozenset[Permission]; request_id: str; correlation_id: str; device_id: str|None=None; platform_scope: bool=False
    def __post_init__(self) -> None: object.__setattr__(self,"authenticated_at",_utc(self.authenticated_at))
    @property
    def principal_id(self)->str: return self.identity.value


class ServiceStatus(str, Enum): ACTIVE="active"; SUSPENDED="suspended"; REVOKED="revoked"
@dataclass(frozen=True)
class ServicePrincipal:
    identity: IdentityReference; service_name: str; scopes: frozenset[str]; request_id: str; correlation_id: str
    tenant_id: Identifier|None=None; platform_scope: bool=False; status: ServiceStatus=ServiceStatus.ACTIVE; credential_reference: str|None=None
    def __post_init__(self)->None:
        object.__setattr__(self,"service_name",_value(self.service_name,"service name")); object.__setattr__(self,"scopes",frozenset(_value(s,"service scope") for s in self.scopes))
    @property
    def principal_id(self)->str: return self.identity.value


@dataclass(frozen=True)
class AnonymousPrincipal:
    request_id: str; correlation_id: str
    @property
    def principal_id(self)->str: return "anonymous"


class DecisionCode(str, Enum):
    ALLOWED="ALLOWED"; UNAUTHENTICATED="UNAUTHENTICATED"; MEMBERSHIP_NOT_FOUND="MEMBERSHIP_NOT_FOUND"; MEMBERSHIP_INACTIVE="MEMBERSHIP_INACTIVE"; TENANT_MISMATCH="TENANT_MISMATCH"; PERMISSION_MISSING="PERMISSION_MISSING"; ROLE_NOT_ASSIGNABLE="ROLE_NOT_ASSIGNABLE"; SERVICE_SCOPE_MISSING="SERVICE_SCOPE_MISSING"; RESOURCE_OWNERSHIP_REQUIRED="RESOURCE_OWNERSHIP_REQUIRED"; PLATFORM_SCOPE_REQUIRED="PLATFORM_SCOPE_REQUIRED"; EXPLICITLY_DENIED="EXPLICITLY_DENIED"


@dataclass(frozen=True)
class AuthorizationRequest:
    permission: Permission; tenant_id: Identifier|None; resource_type: str; resource_id: str|None=None; owner_id: str|None=None; assigned_principal_id: str|None=None; platform_action: bool=False; service_scope: str|None=None
@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool; code: DecisionCode; principal_id: str; tenant_id: str|None; permission: str; resource_type: str; resource_id: str|None; reason_code: str; evaluated_roles: tuple[str,...]; correlation_id: str; request_id: str; decided_at: datetime


class AuthorizationService:
    def decide(self, principal: HumanPrincipal|ServicePrincipal|AnonymousPrincipal, membership: TenantMembership|None, request: AuthorizationRequest, *, at: datetime) -> AuthorizationDecision:
        code=DecisionCode.ALLOWED
        roles:tuple[str,...]=()
        if isinstance(principal, AnonymousPrincipal): code=DecisionCode.UNAUTHENTICATED
        elif isinstance(principal, ServicePrincipal):
            if principal.status is not ServiceStatus.ACTIVE: code=DecisionCode.EXPLICITLY_DENIED
            elif request.platform_action and not principal.platform_scope: code=DecisionCode.PLATFORM_SCOPE_REQUIRED
            elif request.tenant_id != principal.tenant_id and not principal.platform_scope: code=DecisionCode.TENANT_MISMATCH
            elif request.service_scope and request.service_scope not in principal.scopes: code=DecisionCode.SERVICE_SCOPE_MISSING
        else:
            roles=tuple(sorted(role.value for role in principal.roles))
            if membership is None: code=DecisionCode.MEMBERSHIP_NOT_FOUND
            elif membership.status is not MembershipStatus.ACTIVE: code=DecisionCode.MEMBERSHIP_INACTIVE
            elif request.platform_action and not principal.platform_scope: code=DecisionCode.PLATFORM_SCOPE_REQUIRED
            elif request.tenant_id != principal.tenant_id or membership.tenant_id != principal.tenant_id: code=DecisionCode.TENANT_MISMATCH
            elif request.permission not in principal.permissions: code=DecisionCode.PERMISSION_MISSING
            elif request.owner_id is not None and Role.CUSTOMER in principal.roles and request.owner_id != principal.principal_id: code=DecisionCode.RESOURCE_OWNERSHIP_REQUIRED
            elif request.assigned_principal_id is not None and Role.DRIVER in principal.roles and request.assigned_principal_id != principal.principal_id: code=DecisionCode.RESOURCE_OWNERSHIP_REQUIRED
        return AuthorizationDecision(code is DecisionCode.ALLOWED,code,principal.principal_id,str(request.tenant_id) if request.tenant_id else None,request.permission.value,request.resource_type,request.resource_id,code.value,roles,principal.correlation_id,principal.request_id,_utc(at))


@dataclass(frozen=True)
class TenantResolution:
    tenant_id: Identifier; source: str
class TenantResolver:
    def resolve(self, principal: HumanPrincipal|ServicePrincipal, *, token_tenant: Identifier|None, header_tenant: Identifier|None) -> TenantResolution:
        candidates={str(v) for v in (token_tenant,header_tenant,principal.tenant_id) if v is not None}
        if len(candidates)!=1: raise TenantMismatchError("conflicting or absent tenant context")
        tenant=Identifier(candidates.pop())
        if principal.tenant_id!=tenant and not principal.platform_scope: raise TenantMismatchError("tenant not authorized")
        return TenantResolution(tenant,"validated_header" if header_tenant else "validated_claim")


@dataclass(frozen=True)
class IdentityStatusSummary:
    identity: IdentityReference; active: bool; assurance: str; checked_at: datetime; contract_version: str="novalogistics.novaid-status.v1"
class NovaIDAdapter(Protocol):
    def status(self, identity: IdentityReference, *, timeout_seconds: float=2.0)->IdentityStatusSummary: ...
class DeterministicNovaIDAdapter:
    def __init__(self, summaries: dict[str,IdentityStatusSummary]|None=None, *, unavailable: bool=False): self.summaries=summaries or {}; self.unavailable=unavailable
    def status(self, identity: IdentityReference, *, timeout_seconds: float=2.0)->IdentityStatusSummary:
        if timeout_seconds<=0 or self.unavailable: raise IdentityProviderUnavailableError("NovaID unavailable")
        summary=self.summaries.get(identity.value)
        if summary is None or summary.identity!=identity: raise IdentityStatusInvalidError("identity status unavailable or malformed")
        if not summary.active: raise IdentityStatusInvalidError("identity inactive")
        return summary
