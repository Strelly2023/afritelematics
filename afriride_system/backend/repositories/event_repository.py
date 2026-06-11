"""Ride event persistence repository."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from afriride_system.backend.storage import AfriRideStorage, decode_json_value


class EventRepository:
    def __init__(self, storage: AfriRideStorage) -> None:
        self.storage = storage

    def append(self, ride_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """
                INSERT INTO ride_events (ride_id, event_type, created_at, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    ride_id,
                    event_type,
                    datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                    json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str),
                ),
            )

    def events_for_ride(self, ride_id: str) -> tuple[dict[str, Any], ...]:
        with self.storage.connect() as connection:
            rows = connection.execute(
                """
                SELECT event_type, created_at, payload_json
                FROM ride_events
                WHERE ride_id = ?
                ORDER BY event_id
                """,
                (ride_id,),
            ).fetchall()
        return tuple(
            {
                "event_type": str(row["event_type"]),
                "created_at": str(row["created_at"]),
                "payload": decode_json_value(row["payload_json"]),
            }
            for row in rows
        )
