"""Event bus abstraction for NovaPay / NovaTrust events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from typing import Any, Protocol
from uuid import uuid4


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    topic: str
    payload: dict[str, Any]
    transport: str
    published_at: str

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "topic": self.topic,
            "payload": self.payload,
            "transport": self.transport,
            "published_at": self.published_at,
        }


class EventBus(Protocol):
    name: str

    def publish(self, topic: str, payload: dict[str, Any]) -> EventEnvelope:
        ...

    def status(self) -> dict[str, Any]:
        ...


@dataclass
class InMemoryEventBus:
    name: str = "in_memory"
    events: list[EventEnvelope] = field(default_factory=list)

    def publish(self, topic: str, payload: dict[str, Any]) -> EventEnvelope:
        envelope = EventEnvelope(
            event_id=f"evt_{uuid4().hex[:16]}",
            topic=topic,
            payload=dict(payload),
            transport=self.name,
            published_at=datetime.now(timezone.utc).isoformat(),
        )
        self.events.append(envelope)
        return envelope

    def status(self) -> dict[str, Any]:
        return {
            "available": True,
            "backend": self.name,
            "configured": False,
            "ready": True,
            "events_emitted": len(self.events),
        }


@dataclass
class KafkaEventBus:
    brokers: tuple[str, ...]
    topic_prefix: str = "novapay"
    client_id: str = "novatech-core-platform"
    name: str = "kafka"

    def publish(self, topic: str, payload: dict[str, Any]) -> EventEnvelope:
        if not self.brokers:
            raise RuntimeError("kafka_brokers_not_configured")
        try:
            from confluent_kafka import Producer  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - optional deploy dependency
            raise RuntimeError("confluent_kafka_not_installed") from exc

        producer = Producer(
            {
                "bootstrap.servers": ",".join(self.brokers),
                "client.id": self.client_id,
            }
        )
        envelope = EventEnvelope(
            event_id=f"evt_{uuid4().hex[:16]}",
            topic=f"{self.topic_prefix}.{topic}",
            payload=dict(payload),
            transport=self.name,
            published_at=datetime.now(timezone.utc).isoformat(),
        )
        producer.produce(envelope.topic, value=str(envelope.canonical()).encode("utf-8"))
        producer.flush(10)
        return envelope

    def status(self) -> dict[str, Any]:
        return {
            "available": True,
            "backend": self.name,
            "configured": bool(self.brokers),
            "ready": bool(self.brokers),
            "brokers": list(self.brokers),
            "topic_prefix": self.topic_prefix,
        }


def build_event_bus() -> EventBus:
    raw_brokers = [
        broker.strip()
        for broker in os.environ.get("NOVAPAY_EVENT_BUS_KAFKA_BROKERS", "").split(",")
        if broker.strip()
    ]
    backend = os.environ.get("NOVAPAY_EVENT_BUS_BACKEND", "in_memory").strip().lower()
    if backend == "kafka" and raw_brokers:
        return KafkaEventBus(brokers=tuple(raw_brokers))
    return InMemoryEventBus()


def build_event_bus_status() -> dict[str, Any]:
    bus = build_event_bus()
    return {
        "view": "novapay_event_bus_status",
        "event_bus": bus.status(),
        "kafka_ready": isinstance(bus, KafkaEventBus) and bool(bus.brokers),
        "replay_tolerant": True,
    }
