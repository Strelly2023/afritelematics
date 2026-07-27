from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import IdentityStatus, identifier, utcnow


@dataclass(frozen=True)
class IdentityLifecycleEvent:
    event_id: str
    event_type: str
    tenant_id: str
    identity_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    previous_status: IdentityStatus | None
    current_status: IdentityStatus
    identity_version: int
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


def lifecycle_event(
    *,
    event_type: str,
    tenant_id: str,
    identity_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    previous_status: IdentityStatus | None,
    current_status: IdentityStatus,
    identity_version: int,
    metadata: dict[str, Any] | None = None,
) -> IdentityLifecycleEvent:
    return IdentityLifecycleEvent(
        event_id=identifier(),
        event_type=event_type,
        tenant_id=tenant_id,
        identity_id=identity_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        previous_status=previous_status,
        current_status=current_status,
        identity_version=identity_version,
        metadata=dict(metadata or {}),
    )
