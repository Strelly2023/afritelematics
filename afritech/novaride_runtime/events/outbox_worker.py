"""Controlled-pilot transactional outbox worker."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.novaride_runtime.events.outbox import InMemoryOutboxStore
from afritech.novaride_runtime.events.publisher import InMemoryEventPublisher


@dataclass(slots=True)
class OutboxWorkerResult:
    claimed: int
    published: int
    failed: int
    dead_lettered: int


@dataclass(slots=True)
class OutboxWorker:
    worker_id: str
    outbox: InMemoryOutboxStore
    publisher: InMemoryEventPublisher
    max_attempts: int = 5

    def run_once(self, *, limit: int = 100) -> OutboxWorkerResult:
        claimed = self.outbox.claim_batch(worker_id=self.worker_id, limit=limit)
        published = 0
        failed = 0
        for record in claimed:
            try:
                self.publisher.publish(record.event)
                self.outbox.mark_published(record.event.event_id, broker_ack=f"ack:{record.event.event_id}")
                published += 1
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                self.outbox.mark_failed(record.event.event_id, error=str(exc), max_attempts=self.max_attempts)
                failed += 1
        counts = self.outbox.counts()
        return OutboxWorkerResult(
            claimed=len(claimed),
            published=published,
            failed=failed,
            dead_lettered=counts["DEAD_LETTERED"],
        )
