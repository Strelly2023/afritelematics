from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from afritech.novacodepro.platform import NovaCodeProPlatform
from afritech.novacodepro.distributed.broker import DurableEventBroker, build_durable_event_broker


@dataclass
class OutboxWorker:
    platform: NovaCodeProPlatform
    broker: DurableEventBroker | None = None

    def __post_init__(self) -> None:
        if self.broker is None:
            self.broker = build_durable_event_broker(self.platform.repository)

    def run_once(self, limit: int = 100) -> dict[str, int]:
        broker = self.broker or build_durable_event_broker(self.platform.repository)
        drained = broker.drain(limit=limit)
        published = 0
        for event in drained:
            try:
                broker.ack(event["event_id"])
                published += 1
            except Exception as exc:  # pragma: no cover - defensive path
                self.platform.repository.fail_outbox_event(event["event_id"], str(exc))
        return {"published": published, "pending": len(broker.drain(limit=limit))}

    def run_forever(self, interval_seconds: float = 1.0) -> None:
        while True:
            self.run_once()
            time.sleep(interval_seconds)


@dataclass
class AgentExecutionWorker:
    platform: NovaCodeProPlatform

    def run_once(self, limit: int = 25) -> dict[str, int]:
        processed = 0
        for execution in self.platform.pending_agent_executions(limit=limit):
            self.platform.complete_agent_execution(
                execution["id"],
                output={
                    **dict(execution.get("output") or {}),
                    "result": "completed",
                    "processed_by": "agent-worker",
                },
                actor="agent-worker",
            )
            processed += 1
        return {"processed": processed, "pending": len(self.platform.pending_agent_executions(limit=limit))}

    def run_forever(self, interval_seconds: float = 1.0) -> None:
        while True:
            self.run_once()
            time.sleep(interval_seconds)
