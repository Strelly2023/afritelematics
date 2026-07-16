"""Audit recording for the API platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AuditEvent:
    action: str
    product_code: str
    endpoint_id: str
    request_id: str
    correlation_id: str
    actor_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditRecorder:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)
