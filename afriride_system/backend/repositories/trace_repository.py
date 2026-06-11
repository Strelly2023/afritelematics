"""Persistent trace event repository with hash-chain lineage."""

from __future__ import annotations

import json
from typing import Any

from afriride_system.backend.storage import AfriRideStorage, decode_json_value


class TraceRepository:
    def __init__(self, storage: AfriRideStorage) -> None:
        self.storage = storage

    def next_sequence_and_previous_hash(self) -> tuple[int, str | None]:
        with self.storage.connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(MAX(sequence_id), 0) + 1 AS next_sequence,
                       (
                           SELECT event_hash
                           FROM trace_events
                           ORDER BY sequence_id DESC
                           LIMIT 1
                       ) AS previous_hash
                FROM trace_events
                """
            ).fetchone()
        return int(row["next_sequence"]), row["previous_hash"]

    def save(self, payload: dict[str, Any]) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """
                INSERT INTO trace_events (
                    event_id,
                    sequence_id,
                    device_id,
                    actor_type,
                    actor_id,
                    action,
                    payload_json,
                    local_timestamp,
                    normalized_timestamp,
                    app_version,
                    test_mode,
                    ride_id,
                    transition,
                    previous_hash,
                    authority_hash,
                    event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["event_id"],
                    payload["sequence_id"],
                    payload["device_id"],
                    payload["actor_type"],
                    payload["actor_id"],
                    payload["action"],
                    json.dumps(payload["payload"], sort_keys=True, separators=(",", ":"), default=str),
                    payload["local_timestamp"],
                    payload["normalized_timestamp"],
                    payload["app_version"],
                    int(payload["test_mode"]),
                    payload["ride_id"],
                    payload["transition"],
                    payload["previous_hash"],
                    payload["authority_hash"],
                    payload["event_hash"],
                ),
            )

    def get_by_event_id(self, event_id: str) -> dict[str, Any] | None:
        with self.storage.connect() as connection:
            row = connection.execute(
                "SELECT * FROM trace_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return None if row is None else self._from_row(row)

    def all(self) -> tuple[dict[str, Any], ...]:
        with self.storage.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM trace_events ORDER BY sequence_id"
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def events_for_ride(self, ride_id: str) -> tuple[dict[str, Any], ...]:
        with self.storage.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM trace_events WHERE ride_id = ? ORDER BY sequence_id",
                (ride_id,),
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def clear(self) -> None:
        with self.storage.connect() as connection:
            connection.execute("DELETE FROM trace_events")

    def _from_row(self, row) -> dict[str, Any]:
        return {
            "event_id": str(row["event_id"]),
            "sequence_id": int(row["sequence_id"]),
            "device_id": str(row["device_id"]),
            "actor_type": str(row["actor_type"]),
            "actor_id": str(row["actor_id"]),
            "action": str(row["action"]),
            "payload": decode_json_value(row["payload_json"]),
            "local_timestamp": str(row["local_timestamp"]),
            "normalized_timestamp": str(row["normalized_timestamp"]),
            "app_version": str(row["app_version"]),
            "test_mode": bool(row["test_mode"]),
            "ride_id": row["ride_id"],
            "transition": row["transition"],
            "previous_hash": row["previous_hash"],
            "authority_hash": row.get("authority_hash"),
            "event_hash": str(row["event_hash"]),
        }
