"""Kafka event fabric adapter with injectable producer boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from afritech.novaride_runtime.config import KafkaSettings
from afritech.novaride_runtime.events.envelope import MobilityEvent


class KafkaProducerClient(Protocol):
    def send(
        self, *, topic: str, key: bytes, value: bytes, headers: list[tuple[str, bytes]]
    ) -> str: ...


@dataclass(slots=True)
class KafkaPublishResult:
    topic: str
    key: str
    ack: str


@dataclass(slots=True)
class KafkaEventPublisher:
    settings: KafkaSettings
    producer: KafkaProducerClient

    def validate_topics(self) -> None:
        required = {
            "runtime",
            "resilience",
            "mobile_sync",
            "provider_health",
            "failover",
            "evidence",
            "deadletter",
        }
        missing = required.difference(self.settings.topics)
        if missing:
            raise ValueError("missing_kafka_topics:" + ",".join(sorted(missing)))

    def publish(self, event: MobilityEvent, *, topic_key: str = "runtime") -> KafkaPublishResult:
        self.validate_topics()
        topic = self.settings.topics[topic_key]
        payload = event.as_dict()
        key = f"{event.tenant_id}:{event.region}:{event.aggregate_type}:{event.aggregate_id}"
        headers = [
            ("event_id", event.event_id.encode()),
            ("correlation_id", event.correlation_id.encode()),
            ("tenant_id", event.tenant_id.encode()),
            ("region", event.region.encode()),
            ("schema_version", event.schema_version.encode()),
            ("integrity_hash", event.integrity_hash.encode()),
        ]
        import json

        ack = self.producer.send(
            topic=topic,
            key=key.encode(),
            value=json.dumps(payload, sort_keys=True, default=str).encode(),
            headers=headers,
        )
        return KafkaPublishResult(topic=topic, key=key, ack=ack)


@dataclass(slots=True)
class InMemoryKafkaProducer:
    sent: list[dict[str, Any]]

    def send(
        self, *, topic: str, key: bytes, value: bytes, headers: list[tuple[str, bytes]]
    ) -> str:
        self.sent.append({"topic": topic, "key": key.decode(), "value": value, "headers": headers})
        return f"ack:{topic}:{key.decode()}"
