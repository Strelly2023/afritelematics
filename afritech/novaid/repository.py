"""SQLite-backed NovaID record repository."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any


TABLE_NAME = "novaid_records"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _load(payload: str) -> dict[str, Any]:
    return json.loads(payload)


@dataclass(frozen=True)
class NovaIDRecord:
    record_type: str
    record_id: str
    organization_id: str
    status: str
    payload: dict[str, Any]
    created_at: str
    updated_at: str


class NovaIDRepository:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._lock = RLock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    record_type TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (record_type, record_id)
                )
                """
            )
            self._conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_organization_status ON {TABLE_NAME}(organization_id, status)"
            )

    def upsert(
        self,
        record_type: str,
        *,
        record_id: str,
        organization_id: str,
        status: str,
        payload: dict[str, Any],
    ) -> NovaIDRecord:
        now = _now()
        existing = self.get(record_type, record_id)
        created_at = existing.created_at if existing else now
        row_payload = dict(payload)
        row_payload.setdefault("record_type", record_type)
        row_payload.setdefault("record_id", record_id)
        row_payload.setdefault("organization_id", organization_id)
        row_payload.setdefault("status", status)
        with self._lock, self._conn:
            self._conn.execute(
                f"""
                INSERT OR REPLACE INTO {TABLE_NAME} (
                    record_type, record_id, organization_id, status,
                    payload_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_type,
                    record_id,
                    organization_id,
                    status,
                    _dump(row_payload),
                    created_at,
                    now,
                ),
            )
        return NovaIDRecord(
            record_type=record_type,
            record_id=record_id,
            organization_id=organization_id,
            status=status,
            payload=row_payload,
            created_at=created_at,
            updated_at=now,
        )

    def get(self, record_type: str, record_id: str) -> NovaIDRecord | None:
        row = self._conn.execute(
            f"SELECT * FROM {TABLE_NAME} WHERE record_type = ? AND record_id = ?",
            (record_type, record_id),
        ).fetchone()
        if row is None:
            return None
        return NovaIDRecord(
            record_type=str(row["record_type"]),
            record_id=str(row["record_id"]),
            organization_id=str(row["organization_id"]),
            status=str(row["status"]),
            payload=_load(str(row["payload_json"])),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def list(
        self,
        record_type: str,
        *,
        organization_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[NovaIDRecord]:
        query = f"SELECT * FROM {TABLE_NAME} WHERE record_type = ?"
        params: list[Any] = [record_type]
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [
            NovaIDRecord(
                record_type=str(row["record_type"]),
                record_id=str(row["record_id"]),
                organization_id=str(row["organization_id"]),
                status=str(row["status"]),
                payload=_load(str(row["payload_json"])),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    def record_types(self) -> tuple[str, ...]:
        return ("novaid_identities", "novaid_credentials", "novaid_consents", "novaid_devices", "novaid_passkeys", "novaid_sessions", "novaid_oauth_clients", "novaid_risk_events", "novaid_directory_entries", "novaid_trust_events", "novaid_biometric_events", "novaid_recovery_events")
