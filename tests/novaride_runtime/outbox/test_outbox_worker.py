from __future__ import annotations

from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.events.outbox import InMemoryOutboxStore, OutboxState
from afritech.novaride_runtime.events.outbox_worker import OutboxWorker
from afritech.novaride_runtime.events.publisher import InMemoryEventPublisher


def test_outbox_claim_publish_and_duplicate_tolerance() -> None:
    outbox = InMemoryOutboxStore()
    publisher = InMemoryEventPublisher()
    event = MobilityEvent(
        event_type="BookingCreated",
        aggregate_id="booking_1",
        aggregate_type="Booking",
        aggregate_version=1,
        tenant_id="tenant",
        region="AU",
        actor_type="SYSTEM",
        actor_id="system",
        correlation_id="corr",
        causation_id=None,
        payload={"booking_id": "booking_1"},
    )

    outbox.append(event)
    outbox.append(event)
    result = OutboxWorker("worker_1", outbox, publisher).run_once()

    assert result.claimed == 1
    assert result.published == 1
    assert outbox.records[event.event_id].state == OutboxState.PUBLISHED
    assert len(publisher.published) == 1
