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

from .schema import TABLE_NAMES, create_postgres_table_sql, create_table_sql


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
            self._conn.execute(create_postgres_table_sql(table_name))

    @staticmethod
    def _extract_json_payload(payload: dict[str, Any], key: str, default: Any) -> str:
        value = payload.get(key, default)
        return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)

    @classmethod
    def _table_columns_and_values(
        cls,
        table_name: str,
        *,
        record_id: str,
        organization_id: str,
        status: str,
        payload: dict[str, Any],
        now: str,
    ) -> tuple[list[str], list[Any]]:
        columns = ["record_id", "organization_id", "status", "version", "idempotency_key", "payload_json", "created_at", "updated_at"]
        values: list[Any] = [record_id, organization_id, status, 1, payload.get("idempotency_key"), _dump({**payload, "record_id": record_id, "organization_id": organization_id, "status": status}), now, now]
        table_specific: dict[str, list[tuple[str, Any]]] = {
            "novapay_wallets": [
                ("wallet_id", payload.get("wallet_id", record_id)),
                ("owner_id", payload.get("owner_id")),
                ("owner_type", payload.get("owner_type")),
                ("currency", payload.get("currency")),
                ("balance", payload.get("balance", "0.00")),
                ("metadata_json", cls._extract_json_payload(payload, "metadata", {})),
            ],
            "novapay_accounts": [
                ("wallet_id", payload.get("wallet_id")),
                ("account_type", payload.get("account_type")),
                ("currency", payload.get("currency")),
                ("owner_id", payload.get("owner_id")),
                ("balance", payload.get("balance", "0.00")),
                ("metadata_json", cls._extract_json_payload(payload, "metadata", {})),
            ],
            "novapay_ledger_entries": [
                ("transaction_id", payload.get("transaction_id")),
                ("wallet_id", payload.get("wallet_id")),
                ("entry_type", payload.get("entry_type")),
                ("amount", payload.get("amount")),
                ("currency", payload.get("currency")),
                ("posted_at", now),
            ],
            "novapay_transactions": [
                ("transaction_id", payload.get("transaction_id", record_id)),
                ("transfer_id", payload.get("transfer_id")),
                ("actor_id", payload.get("actor_id")),
                ("actor_role", payload.get("actor_role")),
                ("sender_wallet_id", payload.get("sender_wallet_id")),
                ("receiver_wallet_id", payload.get("receiver_wallet_id")),
                ("amount", payload.get("amount")),
                ("currency", payload.get("currency")),
                ("transfer_type", payload.get("transfer_type")),
                ("provider", payload.get("provider")),
                ("metadata_json", cls._extract_json_payload(payload, "metadata", {})),
            ],
            "novapay_transfers": [
                ("transaction_id", payload.get("transaction_id")),
                ("transfer_id", payload.get("transfer_id", record_id)),
                ("actor_id", payload.get("actor_id")),
                ("actor_role", payload.get("actor_role")),
                ("sender_wallet_id", payload.get("sender_wallet_id")),
                ("receiver_wallet_id", payload.get("receiver_wallet_id")),
                ("amount", payload.get("amount")),
                ("currency", payload.get("currency")),
                ("transfer_type", payload.get("transfer_type")),
                ("provider", payload.get("provider")),
                ("sender_after_json", cls._extract_json_payload(payload, "sender_after", {})),
                ("receiver_after_json", cls._extract_json_payload(payload, "receiver_after", {})),
            ],
            "novapay_qr_codes": [
                ("qr_code", payload.get("qr_code", record_id)),
                ("merchant_wallet_id", payload.get("merchant_wallet_id")),
                ("currency", payload.get("currency")),
                ("metadata_json", cls._extract_json_payload(payload, "metadata", {})),
            ],
            "novapay_merchants": [
                ("merchant_id", payload.get("merchant_id", record_id)),
                ("wallet_id", payload.get("wallet_id")),
                ("currency", payload.get("currency")),
                ("metadata_json", cls._extract_json_payload(payload, "metadata", {})),
            ],
            "novapay_agents": [
                ("movement_id", payload.get("movement_id", record_id)),
                ("wallet_id", payload.get("wallet_id")),
                ("direction", payload.get("direction")),
                ("amount", payload.get("amount")),
                ("currency", payload.get("currency")),
                ("wallet_after_json", cls._extract_json_payload(payload, "wallet_after", {})),
            ],
            "novapay_settlements": [
                ("settlement_id", payload.get("settlement_id", record_id)),
                ("transaction_id", payload.get("transaction_id")),
                ("provider_reference", payload.get("provider_reference")),
                ("settlement_amount", payload.get("settlement_amount")),
                ("currency", payload.get("currency")),
            ],
            "novapay_reconciliation_batches": [
                ("batch_id", payload.get("batch_id", record_id)),
                ("batch_name", payload.get("batch_name")),
                ("transaction_count", payload.get("transaction_count", 0)),
                ("gross_amount", payload.get("gross_amount", "0.00")),
            ],
            "novapay_refunds": [
                ("refund_id", payload.get("refund_id", record_id)),
                ("transaction_id", payload.get("transaction_id")),
                ("reason", payload.get("reason")),
                ("amount", payload.get("amount")),
                ("currency", payload.get("currency")),
                ("approval_status", payload.get("approval_status")),
            ],
            "novapay_disputes": [
                ("dispute_id", payload.get("dispute_id", record_id)),
                ("transaction_id", payload.get("transaction_id")),
                ("reason", payload.get("reason")),
                ("opened_by", payload.get("opened_by")),
                ("opened_role", payload.get("opened_role")),
            ],
            "novapay_payouts": [
                ("payout_id", payload.get("payout_id", record_id)),
                ("source_wallet_id", payload.get("source_wallet_id")),
                ("destination_reference", payload.get("destination_reference")),
                ("amount", payload.get("amount")),
                ("currency", payload.get("currency")),
                ("scheduled_for", payload.get("scheduled_for")),
                ("actor_id", payload.get("actor_id")),
                ("actor_role", payload.get("actor_role")),
            ],
            "novapay_invoices": [
                ("invoice_id", payload.get("invoice_id", record_id)),
                ("customer_wallet_id", payload.get("customer_wallet_id")),
                ("amount", payload.get("amount")),
                ("currency", payload.get("currency")),
                ("reference", payload.get("reference")),
                ("due_date", payload.get("due_date")),
                ("actor_id", payload.get("actor_id")),
                ("actor_role", payload.get("actor_role")),
            ],
            "novapay_receipts": [
                ("receipt_id", payload.get("receipt_id", record_id)),
                ("transaction_id", payload.get("transaction_id")),
                ("actor_id", payload.get("actor_id")),
                ("actor_role", payload.get("actor_role")),
                ("trust_hash", payload.get("trust_hash")),
                ("signature_json", cls._extract_json_payload(payload, "signature", {})),
            ],
            "novapay_provider_events": [
                ("provider", payload.get("provider")),
                ("event_type", payload.get("event_type")),
                ("transaction_id", payload.get("transaction_id")),
                ("receipt_id", payload.get("receipt_id")),
            ],
            "novapay_audit_events": [
                ("actor_id", payload.get("actor_id")),
                ("role", payload.get("role")),
                ("action", payload.get("action")),
                ("transaction_id", payload.get("transaction_id")),
                ("receipt_id", payload.get("receipt_id")),
            ],
            "novapay_policy_approvals": [
                ("decision_id", payload.get("decision_id", record_id)),
                ("request_id", payload.get("request_id")),
                ("subject_id", payload.get("subject_id")),
                ("role", payload.get("role")),
                ("action", payload.get("action")),
                ("amount", payload.get("amount")),
                ("limit_amount", payload.get("limit_amount")),
                ("approved", bool(payload.get("approved", False))),
                ("requires_manual_review", bool(payload.get("requires_manual_review", False))),
                ("workflow", payload.get("workflow")),
                ("reason", payload.get("reason")),
                ("metadata_json", cls._extract_json_payload(payload, "metadata", {})),
            ],
            "novapay_developer_apps": [
                ("app_id", payload.get("app_id", record_id)),
                ("developer_id", payload.get("developer_id")),
                ("app_name", payload.get("app_name")),
                ("api_key_hash", payload.get("api_key_hash")),
                ("metadata_json", cls._extract_json_payload(payload, "metadata", {})),
            ],
            "novapay_webhooks": [
                ("webhook_id", payload.get("webhook_id", record_id)),
                ("app_id", payload.get("app_id")),
                ("developer_id", payload.get("developer_id")),
                ("webhook_url", payload.get("webhook_url")),
                ("event_types_json", cls._extract_json_payload(payload, "event_types", [])),
                ("secret_hint", payload.get("secret_hint")),
                ("delivery_status", payload.get("delivery_status", "pending")),
                ("metadata_json", cls._extract_json_payload(payload, "metadata", {})),
            ],
        }
        for column, value in table_specific.get(table_name, []):
            columns.append(column)
            values.append(value)
        return columns, values

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
        columns, values = self._table_columns_and_values(
            table_name,
            record_id=record_id,
            organization_id=organization_id,
            status=status,
            payload=row_payload,
            now=now,
        )
        column_sql = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        update_sql = ",\n                ".join(
            f"{column} = EXCLUDED.{column}"
            for column in columns
            if column not in {"record_id", "created_at"}
        )
        row = self._conn.execute(
            f"""
            INSERT INTO {table_name} (
                {column_sql}
            ) VALUES ({placeholders})
            ON CONFLICT (record_id) DO UPDATE SET
                {update_sql}
            RETURNING *
            """,
            tuple(values),
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
