"""Authorization helpers for API platform endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ApiEndpointDefinition
from .errors import ApiAuthorizationError
from .request_context import RequestContext


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason: str = ""


class AuthorizationPolicy:
    def authorize(self, definition: ApiEndpointDefinition, context: RequestContext) -> AuthorizationDecision:
        required_roles = set(definition.required_roles)
        required_permissions = set(definition.required_permissions)
        if required_roles and not required_roles.intersection(context.roles):
            raise ApiAuthorizationError("required_role_missing")
        if required_permissions and not required_permissions.intersection(context.permissions):
            raise ApiAuthorizationError("required_permission_missing")
        return AuthorizationDecision(True)
