"""Consumer checkpoint helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ConsumerCheckpoints:
    offsets: dict[str, str] = field(default_factory=dict)

    def mark(self, consumer: str, event_id: str) -> None:
        self.offsets[consumer] = event_id
