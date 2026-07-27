from __future__ import annotations

from dataclasses import dataclass

from .models import Identity, RequestContext


@dataclass(frozen=True)
class TenantBoundaryService:
    def assert_valid_context(
        self,
        context: RequestContext,
    ) -> None:
        if not context.tenant_id:
            raise ValueError("TENANT_CONTEXT_REQUIRED")

        if (
            not context.actor_identity_id
            or not context.actor_membership_id
        ):
            raise ValueError("ACTOR_CONTEXT_REQUIRED")

        if not context.correlation_id or not context.request_id:
            raise ValueError("TENANT_CONTEXT_REQUIRED")

        if not context.authentication_strength:
            raise ValueError("ACTOR_CONTEXT_REQUIRED")

    def assert_same_tenant(
        self,
        context: RequestContext,
        tenant_id: str,
    ) -> None:
        self.assert_valid_context(context)

        if context.tenant_id != tenant_id:
            raise PermissionError("TENANT_ACCESS_DENIED")

    def assert_identity_access(
        self,
        context: RequestContext,
        identity: Identity,
    ) -> None:
        self.assert_same_tenant(
            context,
            identity.tenant_id,
        )

    def assert_expected_version(
        self,
        *,
        actual_version: int,
        expected_version: int,
    ) -> None:
        if actual_version != expected_version:
            raise RuntimeError("CONCURRENCY_CONFLICT")
