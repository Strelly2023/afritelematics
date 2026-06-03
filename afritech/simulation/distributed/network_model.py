from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from afritech.simulation.distributed.message_scheduler import MessageScheduler
from afritech.simulation.distributed.network_trace import NetworkTrace


class NetworkModel:
    """Seed-controlled deterministic SEND -> DELAY -> REORDER -> DELIVER model."""

    def __init__(self, seed: int, *, delay_window: int = 5) -> None:
        if delay_window <= 0:
            raise ValueError("delay_window must be positive")
        self.seed = int(seed)
        self.delay_window = int(delay_window)
        self.scheduler = MessageScheduler()

    def transmit(
        self,
        messages: Iterable[Mapping[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        scheduled = tuple(self._apply_delay(message) for message in messages)
        reordered = self._reorder(scheduled)
        return tuple(dict(message["payload"]) for message in reordered)

    def trace(
        self,
        messages: Iterable[Mapping[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        scheduled = tuple(self._apply_delay(message) for message in messages)
        return self._reorder(scheduled)

    def trace_hash(self, messages: Iterable[Mapping[str, Any]]) -> str:
        return NetworkTrace.hash_trace(self.trace(messages))

    def _apply_delay(self, message: Mapping[str, Any]) -> dict[str, Any]:
        msg_id = str(message["id"])
        timestamp = int(message["timestamp"])
        delay = (
            NetworkTrace.stable_int(
                {
                    "delay_window": self.delay_window,
                    "message_id": msg_id,
                    "seed": self.seed,
                }
            )
            % self.delay_window
        )

        payload = dict(message)
        return {
            "payload": payload,
            "message_id": msg_id,
            "sent_time": timestamp,
            "delay": delay,
            "scheduled_time": timestamp + delay,
            "network_seed": self.seed,
        }

    def _reorder(
        self,
        scheduled_messages: Iterable[Mapping[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        return tuple(
            dict(message)
            for message in sorted(
                scheduled_messages,
                key=lambda message: (
                    int(message["scheduled_time"]),
                    NetworkTrace.hash_trace(message["payload"]),
                    str(message["message_id"]),
                ),
            )
        )

    def canonical_delivery(
        self,
        messages: Iterable[Mapping[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        return self.scheduler.schedule(self.transmit(messages))
