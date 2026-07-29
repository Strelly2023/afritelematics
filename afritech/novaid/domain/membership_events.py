from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import MembershipStatus, identifier, utcnow


@dataclass(frozen=True)
class MembershipLifecycleEvent:
    event_id: str
    event_type: str
    membership_id: str
    tenant_id: str
    identity_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    previous_status: MembershipStatus
    current_status: MembershipStatus
    membership_version: int
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


def membership_lifecycle_event(
    *,
    membership_id: str,
    tenant_id: str,
    identity_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    previous_status: MembershipStatus,
    current_status: MembershipStatus,
    membership_version: int,
    metadata: dict[str, Any] | None = None,
) -> MembershipLifecycleEvent:
    return MembershipLifecycleEvent(
        event_id=identifier(),
        event_type=f"MEMBERSHIP_{current_status.value}",
        membership_id=membership_id,
        tenant_id=tenant_id,
        identity_id=identity_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        previous_status=previous_status,
        current_status=current_status,
        membership_version=membership_version,
        metadata=dict(metadata or {}),
    )
