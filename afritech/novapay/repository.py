"""NovaPay record repositories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any

try:  # pragma: no cover - optional production dependency
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - exercised when PostgreSQL driver is unavailable
    psycopg = None
    dict_row = None

from .schema import TABLE_NAMES, create_table_sql


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _load(payload: str) -> dict[str, Any]:
    return json.loads(payload)


@dataclass(frozen=True)
class NovaPayRecord:
    record_id: str
    organization_id: str
    status: str
    payload: dict[str, Any]
    created_at: str
    updated_at: str


class NovaPayRepository:
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
            for table_name in TABLE_NAMES:
                self._conn.execute(create_table_sql(table_name))

    def upsert(
        self,
        table_name: str,
        *,
        record_id: str,
        organization_id: str,
        status: str,
        payload: dict[str, Any],
    ) -> NovaPayRecord:
        now = _now()
        existing = self.get(table_name, record_id)
        created_at = existing.created_at if existing else now
        row_payload = dict(payload)
        row_payload.setdefault("record_id", record_id)
        row_payload.setdefault("organization_id", organization_id)
        row_payload.setdefault("status", status)
        with self._lock, self._conn:
            self._conn.execute(
                f"""
                INSERT OR REPLACE INTO {table_name} (
                    record_id, organization_id, status, payload_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    organization_id,
                    status,
                    _dump(row_payload),
                    created_at,
                    now,
                ),
            )
        return NovaPayRecord(
            record_id=record_id,
            organization_id=organization_id,
            status=status,
            payload=row_payload,
            created_at=created_at,
            updated_at=now,
        )

    def get(self, table_name: str, record_id: str) -> NovaPayRecord | None:
        row = self._conn.execute(
            f"SELECT * FROM {table_name} WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return NovaPayRecord(
            record_id=str(row["record_id"]),
            organization_id=str(row["organization_id"]),
            status=str(row["status"]),
            payload=_load(str(row["payload_json"])),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def list(
        self,
        table_name: str,
        *,
        organization_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[NovaPayRecord]:
        query = f"SELECT * FROM {table_name}"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [
            NovaPayRecord(
                record_id=str(row["record_id"]),
                organization_id=str(row["organization_id"]),
                status=str(row["status"]),
                payload=_load(str(row["payload_json"])),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    def table_names(self) -> tuple[str, ...]:
        return TABLE_NAMES


def _runtime_environment() -> str:
    for env_var in ("NOVAPAY_ENVIRONMENT", "AFRITECH_ENV", "ENVIRONMENT"):
        value = os.environ.get(env_var)
        if value:
            return value
    return "development"


def validate_database_runtime(database_url: str | None, environment: str | None = None) -> None:
    runtime = str(environment or _runtime_environment()).strip().lower()
    if runtime not in {"production", "prod"}:
        return
    if not database_url:
        raise RuntimeError("sqlite_not_allowed_in_production")
    if str(database_url).startswith("sqlite"):
        raise RuntimeError("sqlite_not_allowed_in_production")


class PostgresNovaPayRepository:
    """PostgreSQL-backed NovaPay repository with the same record model."""

    def __init__(self, dsn: str) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg_required_for_postgres")
        self.dsn = str(dsn)
        self._conn = psycopg.connect(self.dsn, row_factory=dict_row)
        self._conn.autocommit = True
        self._ensure_schema()

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        for table_name in TABLE_NAMES:
            self._conn.execute(create_table_sql(table_name))

    @staticmethod
    def _row_to_record(row: dict[str, Any]) -> NovaPayRecord:
        payload = _load(str(row["payload_json"]))
        return NovaPayRecord(
            record_id=str(row["record_id"]),
            organization_id=str(row["organization_id"]),
            status=str(row["status"]),
            payload=payload,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def upsert(
        self,
        table_name: str,
        *,
        record_id: str,
        organization_id: str,
        status: str,
        payload: dict[str, Any],
    ) -> NovaPayRecord:
        now = _now()
        row_payload = dict(payload)
        row_payload.setdefault("record_id", record_id)
        row_payload.setdefault("organization_id", organization_id)
        row_payload.setdefault("status", status)
        row = self._conn.execute(
            f"""
            INSERT INTO {table_name} (
                record_id, organization_id, status, payload_json, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (record_id) DO UPDATE SET
                organization_id = EXCLUDED.organization_id,
                status = EXCLUDED.status,
                payload_json = EXCLUDED.payload_json,
                updated_at = EXCLUDED.updated_at
            RETURNING *
            """,
            (
                record_id,
                organization_id,
                status,
                _dump(row_payload),
                now,
                now,
            ),
        ).fetchone()
        if row is None:  # pragma: no cover - defensive branch
            raise RuntimeError("novapay_postgres_upsert_failed")
        return self._row_to_record(row)

    def get(self, table_name: str, record_id: str) -> NovaPayRecord | None:
        row = self._conn.execute(
            f"SELECT * FROM {table_name} WHERE record_id = %s",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list(
        self,
        table_name: str,
        *,
        organization_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[NovaPayRecord]:
        query = f"SELECT * FROM {table_name}"
        params: list[Any] = []
        clauses: list[str] = []
        if organization_id is not None:
            clauses.append("organization_id = %s")
            params.append(organization_id)
        if status is not None:
            clauses.append("status = %s")
            params.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY updated_at DESC LIMIT %s"
        params.append(limit)
        rows = self._conn.execute(query, tuple(params)).fetchall()
        return [self._row_to_record(row) for row in rows]

    def table_names(self) -> tuple[str, ...]:
        return TABLE_NAMES


def build_repository_from_environment() -> NovaPayRepository | PostgresNovaPayRepository:
    runtime = _runtime_environment()
    backend = os.environ.get("NOVAPAY_PERSISTENCE_BACKEND", "sqlite").strip().lower()
    if backend not in {"sqlite", "postgres"}:
        raise RuntimeError("unsupported_novapay_persistence_backend")
    if backend == "postgres":
        database_url = os.environ.get("NOVAPAY_DATABASE_URL") or os.environ.get(
            "NOVAPAY_POSTGRES_DSN"
        )
        if not database_url:
            raise RuntimeError("missing_novapay_postgres_url")
        validate_database_runtime(database_url, runtime)
        return PostgresNovaPayRepository(database_url)
    db_path = Path(os.environ.get("NOVAPAY_DB_PATH", ":memory:"))
    validate_database_runtime(f"sqlite:///{db_path}", runtime)
    return NovaPayRepository(db_path)
