from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from afritech.novacodepro.platform import NovaCodeProRepository, _event_envelope


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DurableEventBroker(Protocol):
    name: str

    def publish(self, topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def drain(self, limit: int = 100) -> list[dict[str, Any]]:
        ...

    def ack(self, event_id: str) -> None:
        ...


@dataclass
class InMemoryDurableEventBroker:
    name: str = "in_memory"
    events: list[dict[str, Any]] = field(default_factory=list)

    def publish(self, topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "event_id": f"evt_{uuid4().hex[:16]}",
            "topic": topic,
            "payload": dict(payload),
            "published_at": _now(),
            "transport": self.name,
        }
        self.events.append(event)
        return event

    def drain(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.events[:limit]

    def ack(self, event_id: str) -> None:
        self.events = [event for event in self.events if event["event_id"] != event_id]


@dataclass
class RepositoryOutboxBroker:
    repository: NovaCodeProRepository
    name: str = "repository_outbox"

    def publish(self, topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = _event_envelope(
            event_type=topic,
            actor_type=str(payload.get("actor_type") or "service"),
            actor_id=str(payload.get("actor_id") or "broker"),
            tenant_id=str(payload.get("tenant_id") or "novatech"),
            organization_id=str(payload.get("organization_id") or payload.get("tenant_id") or "novatech"),
            project_id=str(payload.get("project_id") or "") or None,
            workflow_id=str(payload.get("workflow_id") or "") or None,
            correlation_id=str(payload.get("correlation_id") or uuid4().hex),
            causation_id=str(payload.get("causation_id") or uuid4().hex),
            data=dict(payload),
        )
        self.repository.append_event(event)
        return event

    def drain(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_outbox(limit=limit)

    def ack(self, event_id: str) -> None:
        self.repository.ack_outbox_event(event_id)


def build_durable_event_broker(repository: NovaCodeProRepository | None = None) -> DurableEventBroker:
    if repository is None:
        return InMemoryDurableEventBroker()
    return RepositoryOutboxBroker(repository=repository)
