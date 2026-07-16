"""Audit records for integration operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass(frozen=True, slots=True)
class IntegrationAuditEvent:
    action: str
    product_code: str
    provider_id: str
    actor_id: str
    timestamp: float
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class IntegrationAuditRecorder:
    events: list[IntegrationAuditEvent] = field(default_factory=list)

    def record(self, action: str, *, product_code: str, provider_id: str, actor_id: str, metadata: dict[str, object] | None = None) -> IntegrationAuditEvent:
        event = IntegrationAuditEvent(
            action=action,
            product_code=product_code,
            provider_id=provider_id,
            actor_id=actor_id,
            timestamp=time(),
            metadata=dict(metadata or {}),
        )
        self.events.append(event)
        return event

