"""Offline-capable event buffer for field validation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afriride.field_validation.device_logger import DeviceLogEntry


@dataclass(frozen=True)
class EventBuffer:
    entries: tuple[DeviceLogEntry, ...] = ()

    def append(self, entry: DeviceLogEntry) -> "EventBuffer":
        return EventBuffer(entries=(*self.entries, entry))

    def extend(self, entries: tuple[DeviceLogEntry, ...]) -> "EventBuffer":
        return EventBuffer(entries=(*self.entries, *entries))

    def synced_events(self) -> tuple[dict[str, object], ...]:
        return tuple(
            dict(entry.event)
            for entry in sorted(
                self.entries,
                key=lambda item: (
                    int(item.event.get("received_order", item.event.get("sequence", 0))),
                    item.log_hash,
                ),
            )
        )

    @property
    def buffer_hash(self) -> str:
        return _canonical_hash([entry.canonical_dict() for entry in self.entries])


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

