"""Storage abstraction for the authoritative AfriRide pilot spine."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "pilot_state.sqlite3"
POSTGRES_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "sql" / "afriride_postgres_schema_v1.sql"
)


def default_storage_locator() -> str:
    return str(DEFAULT_DB_PATH)


def is_postgres_locator(locator: str | Path) -> bool:
    if isinstance(locator, Path):
        return False
    lowered = locator.lower()
    return lowered.startswith("postgres://") or lowered.startswith("postgresql://")


class DBResult:
    def __init__(self, cursor) -> None:
        self._cursor = cursor

    def fetchone(self) -> dict[str, Any] | None:
        row = self._cursor.fetchone()
        if row is None:
            return None
        return _row_to_dict(self._cursor, row)

    def fetchall(self) -> tuple[dict[str, Any], ...]:
        rows = self._cursor.fetchall()
        return tuple(_row_to_dict(self._cursor, row) for row in rows)


class DBConnection:
    def __init__(self, raw_connection, backend: str) -> None:
        self._raw_connection = raw_connection
        self.backend = backend

    def __enter__(self) -> DBConnection:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self._raw_connection.commit()
            else:
                self._raw_connection.rollback()
        finally:
            self._raw_connection.close()

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> DBResult:
        cursor = self._raw_connection.cursor()
        cursor.execute(_normalize_query(query, self.backend), tuple(params))
        return DBResult(cursor)

    def executescript(self, script: str) -> None:
        for statement in _split_sql_script(script):
            self.execute(statement)


class AfriRideStorage:
    def __init__(self, db_path: str | Path) -> None:
        self.locator = str(db_path)
        self.backend = "postgres" if is_postgres_locator(self.locator) else "sqlite"
        self.db_path = self.locator
        self._initialize()

    def connect(self) -> DBConnection:
        if self.backend == "sqlite":
            connection = sqlite3.connect(self.locator)
            return DBConnection(connection, self.backend)
        return DBConnection(_connect_postgres(self.locator), self.backend)

    def reset(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                DELETE FROM ride_events;
                DELETE FROM rides;
                DELETE FROM drivers;
                DELETE FROM trace_events;
                DELETE FROM idempotency_records;
                DELETE FROM replay_snapshots;
                DELETE FROM evidence_records;
                DELETE FROM receipt_records;
                """
            )

    def _initialize(self) -> None:
        schema = _sqlite_schema() if self.backend == "sqlite" else POSTGRES_SCHEMA_PATH.read_text()
        with self.connect() as connection:
            connection.executescript(schema)
            _apply_runtime_migrations(connection, self.backend)


def _connect_postgres(locator: str):
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PostgreSQL storage requested but psycopg is not installed. "
            "Install `psycopg[binary]` before using AFRIRIDE_DATABASE_URL."
        ) from exc
    return psycopg.connect(locator)


def _normalize_query(query: str, backend: str) -> str:
    if backend == "sqlite":
        return query
    return query.replace("?", "%s")


def _split_sql_script(script: str) -> tuple[str, ...]:
    statements = []
    for raw in script.split(";"):
        statement = raw.strip()
        if not statement:
            continue
        if statement.upper() in {"BEGIN", "COMMIT"}:
            continue
        statements.append(statement)
    return tuple(statements)


def _row_to_dict(cursor, row) -> dict[str, Any]:
    columns = tuple(description[0] for description in (cursor.description or ()))
    if not columns:
        return {}
    if isinstance(row, sqlite3.Row):
        return {name: _normalize_value(row[name]) for name in columns}
    return {name: _normalize_value(value) for name, value in zip(columns, row)}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC).replace(microsecond=0)
        return normalized.isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _sqlite_schema() -> str:
    return """
        CREATE TABLE IF NOT EXISTS drivers (
            driver_id TEXT PRIMARY KEY,
            online INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rides (
            ride_id TEXT PRIMARY KEY,
            passenger_id TEXT NOT NULL,
            pickup TEXT NOT NULL,
            destination TEXT NOT NULL,
            status TEXT NOT NULL,
            assigned_driver TEXT,
            trace_hash TEXT,
            state_hash TEXT,
            events_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ride_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trace_events (
            trace_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            sequence_id INTEGER NOT NULL UNIQUE,
            device_id TEXT NOT NULL,
            actor_type TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            local_timestamp TEXT NOT NULL,
            normalized_timestamp TEXT NOT NULL,
            app_version TEXT NOT NULL,
            test_mode INTEGER NOT NULL,
            ride_id TEXT,
            transition TEXT,
            previous_hash TEXT,
            authority_hash TEXT,
            event_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS idempotency_records (
            idempotency_key TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            result_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS replay_snapshots (
            ride_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            assigned_driver TEXT,
            passenger_id TEXT,
            transitions_json TEXT NOT NULL
                DEFAULT '[]',
            trace_hash TEXT NOT NULL,
            replay_hash TEXT NOT NULL,
            authority_hash TEXT,
            replay_verified INTEGER NOT NULL,
            generated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS evidence_records (
            ride_id TEXT PRIMARY KEY,
            trace_hash TEXT NOT NULL,
            replay_hash TEXT NOT NULL,
            authority_hash TEXT,
            verification_status TEXT NOT NULL,
            receipt_id TEXT NOT NULL UNIQUE,
            generated_at TEXT NOT NULL,
            replay_snapshot_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS receipt_records (
            receipt_id TEXT PRIMARY KEY,
            ride_id TEXT NOT NULL UNIQUE,
            replay_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            trace_hash TEXT NOT NULL,
            replay_hash TEXT NOT NULL,
            authority_hash TEXT,
            execution_fingerprint TEXT,
            receipt_hash TEXT NOT NULL UNIQUE,
            issued_at TEXT NOT NULL
        );
    """


def _apply_runtime_migrations(connection: DBConnection, backend: str) -> None:
    statements = (
        _sqlite_runtime_migrations(connection)
        if backend == "sqlite"
        else (
            "ALTER TABLE trace_events ADD COLUMN IF NOT EXISTS authority_hash TEXT",
            "ALTER TABLE replay_snapshots ADD COLUMN IF NOT EXISTS authority_hash TEXT",
            "ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS authority_hash TEXT",
            "ALTER TABLE receipt_records ADD COLUMN IF NOT EXISTS authority_hash TEXT",
            "ALTER TABLE receipt_records ADD COLUMN IF NOT EXISTS execution_fingerprint TEXT",
        )
    )
    for statement in statements:
        if statement:
            connection.execute(statement)


def _sqlite_runtime_migrations(connection: DBConnection) -> tuple[str, ...]:
    required = {
        "trace_events": ("authority_hash",),
        "replay_snapshots": ("authority_hash",),
        "evidence_records": ("authority_hash",),
        "receipt_records": ("authority_hash", "execution_fingerprint"),
    }
    statements: list[str] = []
    for table, columns in required.items():
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {str(row["name"]) for row in rows}
        for column in columns:
            if column not in existing:
                statements.append(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
    return tuple(statements)


def decode_json_value(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value
