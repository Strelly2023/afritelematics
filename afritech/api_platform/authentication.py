"""Authentication helpers for API platform endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .request_context import RequestContext


@dataclass(frozen=True, slots=True)
class ApiPrincipal:
    tenant_id: str
    organization_id: str
    actor_id: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]


def authenticate_headers(headers: Mapping[str, str], *, product_code: str, audience: str = "INTERNAL") -> tuple[ApiPrincipal, RequestContext]:
    context = RequestContext.from_headers(product_code, headers, audience=audience)
    principal = ApiPrincipal(
        tenant_id=context.tenant_id,
        organization_id=context.organization_id,
        actor_id=context.actor_id,
        roles=context.roles,
        permissions=context.permissions,
    )
    return principal, context
