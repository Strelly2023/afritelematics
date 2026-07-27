from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .identity_events import IdentityLifecycleEvent, lifecycle_event
from .models import (
    Identity,
    IdentityStatus,
    RequestContext,
)
from .tenant_boundary import TenantBoundaryService


@dataclass(frozen=True)
class IdentityLifecycleResult:
    identity: Identity
    event: IdentityLifecycleEvent


class IdentityLifecycleService:
    def __init__(
        self,
        boundary: TenantBoundaryService | None = None,
    ) -> None:
        self.boundary = boundary or TenantBoundaryService()

    _EVENT_TYPES = {
        IdentityStatus.ACTIVE: "IDENTITY_ACTIVATED",
        IdentityStatus.LOCKED: "IDENTITY_LOCKED",
        IdentityStatus.SUSPENDED: "IDENTITY_SUSPENDED",
        IdentityStatus.DISABLED: "IDENTITY_DISABLED",
        IdentityStatus.DELETED: "IDENTITY_DELETED",
    }

    def transition(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        target: IdentityStatus,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityLifecycleResult:
        self.boundary.assert_identity_access(
            context,
            identity,
        )
        self.boundary.assert_expected_version(
            actual_version=identity.version,
            expected_version=expected_version,
        )

        previous_status = identity.status
        transitioned = identity.transition(target)

        event_type = self._EVENT_TYPES.get(target)
        if event_type is None:
            raise ValueError("UNSUPPORTED_IDENTITY_LIFECYCLE_TARGET")

        event = lifecycle_event(
            event_type=event_type,
            tenant_id=identity.tenant_id,
            identity_id=identity.identity_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            previous_status=previous_status,
            current_status=transitioned.status,
            identity_version=transitioned.version,
            metadata=metadata,
        )

        return IdentityLifecycleResult(
            identity=transitioned,
            event=event,
        )

    def activate(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityLifecycleResult:
        return self.transition(
            context=context,
            identity=identity,
            target=IdentityStatus.ACTIVE,
            expected_version=expected_version,
            metadata=metadata,
        )

    def lock(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityLifecycleResult:
        return self.transition(
            context=context,
            identity=identity,
            target=IdentityStatus.LOCKED,
            expected_version=expected_version,
            metadata=metadata,
        )

    def suspend(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityLifecycleResult:
        return self.transition(
            context=context,
            identity=identity,
            target=IdentityStatus.SUSPENDED,
            expected_version=expected_version,
            metadata=metadata,
        )

    def disable(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityLifecycleResult:
        return self.transition(
            context=context,
            identity=identity,
            target=IdentityStatus.DISABLED,
            expected_version=expected_version,
            metadata=metadata,
        )

    def delete(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityLifecycleResult:
        return self.transition(
            context=context,
            identity=identity,
            target=IdentityStatus.DELETED,
            expected_version=expected_version,
            metadata=metadata,
        )
