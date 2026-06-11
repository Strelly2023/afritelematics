"""Persistent idempotency record storage."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from afriride_system.backend.storage import AfriRideStorage, decode_json_value


@dataclass(frozen=True)
class PersistedIdempotencyRecord:
    fingerprint: str
    result: dict[str, Any]


class IdempotencyRepository:
    def __init__(self, storage: AfriRideStorage) -> None:
        self.storage = storage

    def get(self, key: str) -> PersistedIdempotencyRecord | None:
        with self.storage.connect() as connection:
            row = connection.execute(
                """
                SELECT fingerprint, result_json
                FROM idempotency_records
                WHERE idempotency_key = ?
                """,
                (key,),
            ).fetchone()
        if row is None:
            return None
        return PersistedIdempotencyRecord(
            fingerprint=str(row["fingerprint"]),
            result=decode_json_value(row["result_json"]),
        )

    def save(self, key: str, fingerprint: str, result: dict[str, Any]) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """
                INSERT INTO idempotency_records (idempotency_key, fingerprint, result_json)
                VALUES (?, ?, ?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    fingerprint = excluded.fingerprint,
                    result_json = excluded.result_json
                """,
                (
                    key,
                    fingerprint,
                    json.dumps(result, sort_keys=True, separators=(",", ":"), default=str),
                ),
            )

    def clear(self) -> None:
        with self.storage.connect() as connection:
            connection.execute("DELETE FROM idempotency_records")
