"""Retrying idempotent worker for the durable mobile push outbox."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
import time
from typing import Any, Protocol
from urllib.request import Request, urlopen


class PushOutboxRepository(Protocol):
    def claim_pending(self, limit: int) -> list[dict[str, Any]]: ...
    def mark_delivered(self, outbox_id: str) -> None: ...
    def mark_failed(self, outbox_id: str, error: str) -> None: ...
    def devices_for(self, actor_id: str) -> list[dict[str, Any]]: ...


class MobilePushWorker:
    def __init__(self, repository: PushOutboxRepository,
                 deliver: Callable[[str, str, dict[str, Any]], None]) -> None:
        self.repository = repository
        self.deliver = deliver

    def run_once(self, *, limit: int = 100) -> dict[str, int]:
        delivered = failed = 0
        for record in self.repository.claim_pending(limit):
            try:
                self.deliver(
                    str(record["actor_id"]),
                    str(record["event_type"]),
                    dict(record["payload"]),
                )
                self.repository.mark_delivered(str(record["outbox_id"]))
                delivered += 1
            except Exception as exc:
                self.repository.mark_failed(
                    str(record["outbox_id"]), f"{type(exc).__name__}:{exc}"
                )
                failed += 1
        return {"delivered": delivered, "failed": failed}


class ExpoPushProvider:
    def __init__(self, repository: PushOutboxRepository) -> None:
        self.repository = repository

    def __call__(self, actor_id: str, event_type: str, data: dict[str, Any]) -> None:
        if os.environ.get("AFRIRIDE_PUSH_DELIVERY_ENABLED", "").lower() != "true":
            raise RuntimeError("push_delivery_disabled")
        devices = self.repository.devices_for(actor_id)
        if not devices:
            raise RuntimeError("push_device_not_registered")
        for device in devices:
            message = {
                "to": device["token"],
                "title": "Driver assigned" if event_type == "driver_assigned" else "Ride update",
                "body": "Your driver is on the way." if event_type == "driver_assigned" else "Your ride has an update.",
                "data": data,
                "sound": "default",
                "priority": "high",
            }
            request = Request(
                "https://exp.host/--/api/v2/push/send",
                data=json.dumps(message).encode(),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=5) as response:
                if response.status >= 300:
                    raise RuntimeError(f"push_provider_status:{response.status}")


def main() -> None:
    from importlib import import_module

    repository = import_module("afriride_system.api.dependencies.runtime").get_gateway().push_outbox_repository
    worker = MobilePushWorker(repository, ExpoPushProvider(repository))
    interval = max(1, int(os.environ.get("AFRIRIDE_PUSH_WORKER_INTERVAL_SECONDS", "5")))
    while True:
        worker.run_once()
        time.sleep(interval)


if __name__ == "__main__":
    main()
