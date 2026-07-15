"""Transactional outbox model and local controlled-pilot store."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.events.envelope import MobilityEvent


class OutboxState(StrEnum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    DEAD_LETTERED = "DEAD_LETTERED"


@dataclass(slots=True)
class OutboxRecord:
    event: MobilityEvent
    state: OutboxState = OutboxState.PENDING
    worker_id: str | None = None
    attempts: int = 0
    last_error: str | None = None
    next_attempt_at: datetime = field(default_factory=utc_now)
    claimed_at: datetime | None = None
    published_at: datetime | None = None
    broker_ack: str | None = None

    @property
    def published(self) -> bool:
        return self.state == OutboxState.PUBLISHED


@dataclass(slots=True)
class InMemoryOutboxStore:
    records: dict[str, OutboxRecord] = field(default_factory=dict)

    def append(self, event: MobilityEvent) -> OutboxRecord:
        record = self.records.get(event.event_id)
        if record is not None:
            return record
        record = OutboxRecord(event=event)
        self.records[event.event_id] = record
        return record

    def claim_batch(self, *, worker_id: str, limit: int = 100, now: datetime | None = None) -> list[OutboxRecord]:
        current_time = now or utc_now()
        claimed: list[OutboxRecord] = []
        for record in self.records.values():
            if len(claimed) >= limit:
                break
            if record.state in {OutboxState.PENDING, OutboxState.FAILED} and record.next_attempt_at <= current_time:
                record.state = OutboxState.CLAIMED
                record.worker_id = worker_id
                record.claimed_at = current_time
                claimed.append(record)
        return claimed

    def mark_published(self, event_id: str, *, broker_ack: str) -> None:
        record = self.records[event_id]
        if record.state == OutboxState.PUBLISHED:
            return
        record.state = OutboxState.PUBLISHED
        record.published_at = utc_now()
        record.broker_ack = broker_ack

    def mark_failed(self, event_id: str, *, error: str, max_attempts: int = 5) -> None:
        record = self.records[event_id]
        record.attempts += 1
        record.last_error = error
        if record.attempts >= max_attempts:
            record.state = OutboxState.DEAD_LETTERED
            return
        record.state = OutboxState.FAILED
        record.next_attempt_at = utc_now() + timedelta(seconds=2 ** min(record.attempts, 8))

    def counts(self) -> dict[str, int]:
        return {state.value: sum(1 for record in self.records.values() if record.state == state) for state in OutboxState}
