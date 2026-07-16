"""Tenant resolution and checks for API platform endpoints."""

from __future__ import annotations

from .errors import ApiTenancyError
from .request_context import RequestContext


def require_tenant(context: RequestContext) -> str:
    if not context.tenant_id.strip():
        raise ApiTenancyError("tenant_context_required")
    return context.tenant_id
