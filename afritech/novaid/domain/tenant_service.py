from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import (
    RequestContext,
    Tenant,
    TenantStatus,
)
from .tenant_events import (
    TenantLifecycleEvent,
    tenant_lifecycle_event,
)


TENANT_EVENT_TYPES: dict[TenantStatus, str] = {
    TenantStatus.SUSPENDED: "TENANT_SUSPENDED",
    TenantStatus.ACTIVE: "TENANT_REACTIVATED",
    TenantStatus.DISABLED: "TENANT_DISABLED",
}


@dataclass(frozen=True)
class TenantLifecycleResult:
    tenant: Tenant
    event: TenantLifecycleEvent


class TenantLifecycleService:
    """Apply tenant lifecycle transitions and emit immutable events."""

    def transition(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        target: TenantStatus | str,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> TenantLifecycleResult:
        self._assert_tenant_boundary(
            context=context,
            tenant=tenant,
        )
        self._assert_version(
            tenant=tenant,
            expected_version=expected_version,
        )

        normalized_target = TenantStatus(target)
        previous_status = tenant.status

        transitioned = tenant.transition(
            normalized_target,
        )

        event_type = TENANT_EVENT_TYPES.get(
            normalized_target,
        )

        if event_type is None:
            raise ValueError(
                "UNSUPPORTED_TENANT_LIFECYCLE_EVENT"
            )

        event = tenant_lifecycle_event(
            event_type=event_type,
            tenant_id=transitioned.tenant_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            previous_status=previous_status,
            current_status=transitioned.status,
            tenant_version=transitioned.version,
            metadata=metadata,
        )

        return TenantLifecycleResult(
            tenant=transitioned,
            event=event,
        )

    def suspend(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> TenantLifecycleResult:
        return self.transition(
            context=context,
            tenant=tenant,
            target=TenantStatus.SUSPENDED,
            expected_version=expected_version,
            metadata=metadata,
        )

    def reactivate(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> TenantLifecycleResult:
        return self.transition(
            context=context,
            tenant=tenant,
            target=TenantStatus.ACTIVE,
            expected_version=expected_version,
            metadata=metadata,
        )

    def disable(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> TenantLifecycleResult:
        return self.transition(
            context=context,
            tenant=tenant,
            target=TenantStatus.DISABLED,
            expected_version=expected_version,
            metadata=metadata,
        )

    @staticmethod
    def _assert_tenant_boundary(
        *,
        context: RequestContext,
        tenant: Tenant,
    ) -> None:
        if context.tenant_id != tenant.tenant_id:
            raise PermissionError(
                "TENANT_ACCESS_DENIED"
            )

    @staticmethod
    def _assert_version(
        *,
        tenant: Tenant,
        expected_version: int,
    ) -> None:
        if expected_version < 1:
            raise ValueError(
                "INVALID_EXPECTED_VERSION"
            )

        if tenant.version != expected_version:
            raise RuntimeError(
                "CONCURRENCY_CONFLICT"
            )
