"""Production-oriented outbox publishing service."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.novaride_runtime.events.outbox import InMemoryOutboxStore
from afritech.novaride_runtime.kafka import KafkaEventPublisher


@dataclass(slots=True)
class OutboxPublishSummary:
    claimed: int
    published: int
    failed: int
    dead_lettered: int


@dataclass(slots=True)
class ProductionOutboxPublisher:
    outbox: InMemoryOutboxStore
    publisher: KafkaEventPublisher
    worker_id: str
    max_attempts: int = 5

    def run_once(self, *, limit: int = 100) -> OutboxPublishSummary:
        claimed = self.outbox.claim_batch(worker_id=self.worker_id, limit=limit)
        published = 0
        failed = 0
        for record in claimed:
            try:
                topic_key = (
                    "resilience" if "Resilience" in record.event.aggregate_type else "runtime"
                )
                result = self.publisher.publish(record.event, topic_key=topic_key)
                self.outbox.mark_published(record.event.event_id, broker_ack=result.ack)
                published += 1
            except Exception as exc:
                self.outbox.mark_failed(
                    record.event.event_id, error=str(exc), max_attempts=self.max_attempts
                )
                failed += 1
        counts = self.outbox.counts()
        return OutboxPublishSummary(
            claimed=len(claimed),
            published=published,
            failed=failed,
            dead_lettered=counts["DEAD_LETTERED"],
        )
