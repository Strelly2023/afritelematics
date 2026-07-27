from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import identifier, utcnow


@dataclass(frozen=True)
class IdentityMergedEvent:
    event_id: str
    event_type: str
    tenant_id: str
    source_identity_id: str
    target_identity_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    source_version: int
    target_version: int
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


def identity_merged_event(
    *,
    tenant_id: str,
    source_identity_id: str,
    target_identity_id: str,
    actor_identity_id: str,
    correlation_id: str,
    request_id: str,
    source_version: int,
    target_version: int,
    metadata: dict[str, Any] | None = None,
) -> IdentityMergedEvent:
    return IdentityMergedEvent(
        event_id=identifier(),
        event_type="IDENTITY_MERGED",
        tenant_id=tenant_id,
        source_identity_id=source_identity_id,
        target_identity_id=target_identity_id,
        actor_identity_id=actor_identity_id,
        correlation_id=correlation_id,
        request_id=request_id,
        source_version=source_version,
        target_version=target_version,
        metadata=dict(metadata or {}),
    )
