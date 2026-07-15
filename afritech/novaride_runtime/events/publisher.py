"""Event publisher abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field

from afritech.novaride_runtime.events.envelope import MobilityEvent


@dataclass(slots=True)
class InMemoryEventPublisher:
    published: list[MobilityEvent] = field(default_factory=list)
    dead_letters: list[dict[str, object]] = field(default_factory=list)

    def publish(self, event: MobilityEvent) -> None:
        self.published.append(event)

    def dead_letter(self, event: MobilityEvent, reason: str) -> None:
        self.dead_letters.append({"event": event.as_dict(), "reason": reason})
