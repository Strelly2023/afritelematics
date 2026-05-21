from __future__ import annotations

from typing import Any


class SyncEngine:
    def reconcile(self, events: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
        deduped: dict[tuple[str, str], dict[str, Any]] = {}
        for event in events:
            key = (str(event["device_id"]), str(event["event_id"]))
            current = deduped.get(key)
            if current is None or self._sort_key(event) < self._sort_key(current):
                deduped[key] = event

        return tuple(sorted(deduped.values(), key=self._sort_key))

    def _sort_key(self, event: dict[str, Any]) -> tuple[int, str, str]:
        return (
            int(event["timestamp"]),
            str(event["device_id"]),
            str(event["event_id"]),
        )
