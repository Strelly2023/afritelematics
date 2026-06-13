"""AfriPay async tasks."""

from __future__ import annotations

from uuid import uuid4

from afritech.afripay.celery_app import shared_task


@shared_task(name="afripay.process_payment")
def process_payment_task(payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
    from afritech.afripay.persistence import PersistentIdempotencyStore
    from afritech.afripay.operations import create_payment_sync

    response = create_payment_sync(payload)
    PersistentIdempotencyStore().store_response(idempotency_key, response)
    return response


@shared_task(name="afripay.process_provider_webhook")
def process_provider_webhook_task(provider: str, payload: dict[str, object]) -> dict[str, object]:
    from afritech.afripay.operations import append_event

    aggregate_id = str(payload.get("reference") or payload.get("transaction_id") or provider)
    event = append_event(
        "afripay.provider.webhook.received",
        aggregate_id,
        {"provider": provider, "payload": payload},
    )
    return {"event_id": event.event_id, "status": "recorded"}


@shared_task(name="afripay.prune_idempotency_keys")
def prune_idempotency_keys_task() -> dict[str, object]:
    from afritech.afripay.persistence import PersistentIdempotencyStore

    return {"deleted": PersistentIdempotencyStore().prune_expired()}


def enqueue_payment_processing(payload: dict[str, object], idempotency_key: str) -> dict[str, str]:
    result = process_payment_task.delay(payload, idempotency_key)
    return {"task_id": getattr(result, "id", "local-" + uuid4().hex)}


def enqueue_webhook_processing(provider: str, payload: dict[str, object]) -> dict[str, str]:
    result = process_provider_webhook_task.delay(provider, payload)
    return {"task_id": getattr(result, "id", "local-" + uuid4().hex)}
