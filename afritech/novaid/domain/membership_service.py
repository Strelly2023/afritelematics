from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .membership_events import MembershipLifecycleEvent, membership_lifecycle_event
from .models import MembershipStatus, RequestContext, TenantMembership


@dataclass(frozen=True)
class MembershipLifecycleResult:
    membership: TenantMembership
    event: MembershipLifecycleEvent


class MembershipLifecycleService:
    def transition(
        self,
        *,
        context: RequestContext,
        membership: TenantMembership,
        target: MembershipStatus | str,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> MembershipLifecycleResult:
        if context.tenant_id != membership.tenant_id:
            raise PermissionError("TENANT_ACCESS_DENIED")
        if expected_version < 1:
            raise ValueError("INVALID_EXPECTED_VERSION")
        if membership.version != expected_version:
            raise RuntimeError("CONCURRENCY_CONFLICT")
        previous = membership.status
        transitioned = membership.transition(target)
        return MembershipLifecycleResult(
            membership=transitioned,
            event=membership_lifecycle_event(
                membership_id=transitioned.membership_id,
                tenant_id=transitioned.tenant_id,
                identity_id=transitioned.identity_id,
                actor_identity_id=context.actor_identity_id,
                correlation_id=context.correlation_id,
                request_id=context.request_id,
                previous_status=previous,
                current_status=transitioned.status,
                membership_version=transitioned.version,
                metadata=metadata,
            ),
        )

    def activate(self, **kwargs: Any) -> MembershipLifecycleResult:
        return self.transition(target=MembershipStatus.ACTIVE, **kwargs)

    def suspend(self, **kwargs: Any) -> MembershipLifecycleResult:
        return self.transition(target=MembershipStatus.SUSPENDED, **kwargs)

    def revoke(self, **kwargs: Any) -> MembershipLifecycleResult:
        return self.transition(target=MembershipStatus.REVOKED, **kwargs)

    def expire(self, **kwargs: Any) -> MembershipLifecycleResult:
        return self.transition(target=MembershipStatus.EXPIRED, **kwargs)
