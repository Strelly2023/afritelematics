from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from afritech.api.auth.jwt_device_auth import JWTClaims, get_current_claims


@dataclass(frozen=True, slots=True)
class NovaRideRuntimeContext:
    subject_id: str
    tenant_id: str
    organization_id: str
    workspace_id: str | None
    roles: frozenset[str]
    permissions: frozenset[str]
    region: str


ROLE_ALIASES = {
    "ADMIN": "PLATFORM_ADMIN",
    "SYSTEM_ADMIN": "PLATFORM_ADMIN",
    "SUPER_ADMIN": "PLATFORM_OWNER",
}


def normalize_role(role: str) -> str:
    normalized = role.strip().upper()
    return ROLE_ALIASES.get(normalized, normalized)


def _collect_roles(claims: JWTClaims) -> frozenset[str]:
    role_values: set[str] = {normalize_role(getattr(claims, "role", ""))}
    for attribute in ("roles", "assigned_roles"):
        for role in getattr(claims, attribute, []) or []:
            role_values.add(normalize_role(str(role)))
    return frozenset(role_values)


def _collect_permissions(claims: JWTClaims) -> frozenset[str]:
    permissions: set[str] = set()
    for attribute in ("permissions", "scopes"):
        for permission in getattr(claims, attribute, []) or []:
            permissions.add(str(permission).strip())
    return frozenset(permission for permission in permissions if permission)


def require_runtime_context(
    request: Request,
    claims: Annotated[JWTClaims, Depends(get_current_claims)],
) -> NovaRideRuntimeContext:
    tenant_id = getattr(claims, "tenant_id", None)
    organization_id = getattr(claims, "organization_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant_context_required",
        )

    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="organization_context_required",
        )

    context = NovaRideRuntimeContext(
        subject_id=claims.sub,
        tenant_id=str(tenant_id),
        organization_id=str(organization_id),
        workspace_id=getattr(claims, "workspace_id", None),
        roles=_collect_roles(claims),
        permissions=_collect_permissions(claims),
        region=getattr(claims, "region", None) or "australia-southeast",
    )
    request.state.novaride_runtime_context = context
    return context


def get_runtime_context(request: Request) -> NovaRideRuntimeContext:
    context = getattr(request.state, "novaride_runtime_context", None)
    if context is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bearer token required")
    return context


def require_permissions(
    *required_permissions: str,
    allowed_roles: set[str] | None = None,
) -> Callable:
    allowed_roles = {normalize_role(role) for role in (allowed_roles or set())}
    required_permissions = tuple(permission.strip() for permission in required_permissions if permission.strip())

    def dependency(
        context: Annotated[NovaRideRuntimeContext, Depends(get_runtime_context)],
    ) -> NovaRideRuntimeContext:
        role_allowed = bool(context.roles.intersection(allowed_roles)) if allowed_roles else False
        permissions_allowed = all(
            permission in context.permissions for permission in required_permissions
        ) if required_permissions else False

        if allowed_roles or required_permissions:
            if not role_allowed and not permissions_allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "novaride_runtime_permission_denied",
                        "required_permissions": list(required_permissions),
                    },
                )
        return context

    return dependency


def require_driver_ownership_or_operations(
    *,
    context: NovaRideRuntimeContext,
    driver_identity_id: str,
) -> None:
    owns_driver = context.subject_id == driver_identity_id
    operations_override = bool(
        context.roles.intersection(
            {
                "PLATFORM_ADMIN",
                "OPERATIONS_TEAM",
                "INCIDENT_RESPONSE_TEAM",
            }
        )
    )

    if not owns_driver and not operations_override:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="driver_resource_not_owned",
        )


def require_role_membership(context: NovaRideRuntimeContext, *roles: str) -> None:
    allowed = {normalize_role(role) for role in roles}
    if not context.roles.intersection(allowed):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient_role")
