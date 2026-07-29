from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import (
    TenantStatus,
    identifier,
    utcnow,
)


@dataclass(frozen=True)
class TenantLifecycleEvent:
    event_id: str
    event_type: str
    tenant_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    previous_status: TenantStatus
    current_status: TenantStatus
    tenant_version: int
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("TENANT_EVENT_ID_REQUIRED")

        if not self.event_type.strip():
            raise ValueError("TENANT_EVENT_TYPE_REQUIRED")

        if not self.tenant_id.strip():
            raise ValueError("TENANT_ID_REQUIRED")

        if not self.actor_identity_id.strip():
            raise ValueError("ACTOR_IDENTITY_REQUIRED")

        if not self.correlation_id.strip():
            raise ValueError("CORRELATION_ID_REQUIRED")

        if not self.request_id.strip():
            raise ValueError("REQUEST_ID_REQUIRED")

        if self.tenant_version < 1:
            raise ValueError("INVALID_AGGREGATE_VERSION")

        object.__setattr__(
            self,
            "event_id",
            self.event_id.strip(),
        )
        object.__setattr__(
            self,
            "event_type",
            self.event_type.strip().upper(),
        )
        object.__setattr__(
            self,
            "tenant_id",
            self.tenant_id.strip(),
        )
        object.__setattr__(
            self,
            "actor_identity_id",
            self.actor_identity_id.strip(),
        )
        object.__setattr__(
            self,
            "correlation_id",
            self.correlation_id.strip(),
        )
        object.__setattr__(
            self,
            "request_id",
            self.request_id.strip(),
        )
        object.__setattr__(
            self,
            "previous_status",
            TenantStatus(self.previous_status),
        )
        object.__setattr__(
            self,
            "current_status",
            TenantStatus(self.current_status),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


def tenant_lifecycle_event(
    *,
    event_type: str,
    tenant_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    previous_status: TenantStatus,
    current_status: TenantStatus,
    tenant_version: int,
    metadata: dict[str, Any] | None = None,
) -> TenantLifecycleEvent:
    return TenantLifecycleEvent(
        event_id=identifier(),
        event_type=event_type,
        tenant_id=tenant_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        previous_status=previous_status,
        current_status=current_status,
        tenant_version=tenant_version,
        metadata=dict(metadata or {}),
    )
