"""Runtime control store repositories."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import psycopg
from psycopg.rows import dict_row

from .migrations import DDL
from .models import (
    ActivationRecord,
    ApprovalRecord,
    DeploymentRevisionRecord,
    EvidenceRecord,
    InfrastructurePlanRecord,
    InfrastructureResourceRecord,
    IdempotencyRecord,
    ProductVersionRecord,
    RollbackRunRecord,
    RuntimeInstanceRecord,
    VerificationResultRecord,
    VerificationRunRecord,
    WorkerInstanceRecord,
)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _decode(value: str | None) -> Any:
    if value in {None, ""}:
        return {}
    return json.loads(value)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (list, tuple, dict)):
        return _json(value)
    return value


def _build_insert_sql(table: str, payload: dict[str, Any], dialect: str) -> str:
    columns = ", ".join(payload.keys())
    if dialect == "postgres":
        placeholders = ", ".join([f"%({key})s" for key in payload.keys()])
    else:
        placeholders = ", ".join([":" + key for key in payload.keys()])
    updates = ", ".join([f"{key}=excluded.{key}" for key in payload.keys() if key != "id"])
    return f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}"


def _deserialize_record(data: dict[str, Any]) -> dict[str, Any]:
    for key in ("metadata", "details", "evidence", "approver_roles", "evidence_refs", "conditions", "checks", "actions"):
        if key in data:
            data[key] = _decode(data[key]) if isinstance(data[key], str) else data[key]
            if key in {"approver_roles", "evidence_refs", "conditions", "checks", "actions"} and isinstance(data[key], list):
                data[key] = tuple(data[key])
    return data


@runtime_checkable
class RuntimeControlRepository(Protocol):
    async def save_product_version(self, record: ProductVersionRecord) -> None: ...
    async def get_product_version(self, product_code: str, product_version: str) -> ProductVersionRecord | None: ...
    async def save_activation(self, record: ActivationRecord) -> None: ...
    async def append_activation_transition(self, record: Mapping[str, Any]) -> None: ...
    async def get_activation(self, product_code: str, product_version: str) -> ActivationRecord | None: ...
    async def save_approval(self, record: ApprovalRecord) -> None: ...
    async def get_approval(self, approval_id: str) -> ApprovalRecord | None: ...
    async def save_worker_instance(self, record: WorkerInstanceRecord) -> None: ...
    async def list_worker_instances(self, product_code: str) -> list[WorkerInstanceRecord]: ...
    async def save_infrastructure_plan(self, record: InfrastructurePlanRecord) -> None: ...
    async def save_infrastructure_resource(self, record: InfrastructureResourceRecord) -> None: ...
    async def save_deployment_revision(self, record: DeploymentRevisionRecord) -> None: ...
    async def save_verification_run(self, record: VerificationRunRecord) -> None: ...
    async def save_verification_result(self, record: VerificationResultRecord) -> None: ...
    async def save_rollback_run(self, record: RollbackRunRecord) -> None: ...
    async def save_evidence_record(self, record: EvidenceRecord) -> None: ...
    async def save_idempotency_record(self, record: IdempotencyRecord) -> None: ...
    async def get_idempotency_record(self, product_code: str, idempotency_key: str) -> IdempotencyRecord | None: ...
    async def list_evidence(self, product_code: str) -> list[EvidenceRecord]: ...
    async def list_deployments(self, product_code: str) -> list[DeploymentRevisionRecord]: ...
    async def list_verification_runs(self, product_code: str) -> list[VerificationRunRecord]: ...
    async def list_rollback_runs(self, product_code: str) -> list[RollbackRunRecord]: ...
    async def list_runtime_instances(self, product_code: str) -> list[RuntimeInstanceRecord]: ...


class SQLiteRuntimeControlRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            sqlite_ddl = DDL.replace("CREATE SCHEMA IF NOT EXISTS platform_runtime;\n", "").replace("platform_runtime.", "")
            conn.executescript(sqlite_ddl)
            conn.commit()

    def _table(self, table: str) -> str:
        return table.split(".", 1)[1] if "." in table else table

    async def _run(self, fn):
        return await asyncio.to_thread(fn)

    def _upsert_payload(self, table: str, payload: dict[str, Any]) -> None:
        payload = dict(payload)
        payload.setdefault("created_by", "")
        payload.setdefault("updated_by", "")
        for key, value in list(payload.items()):
            payload[key] = _serialize_value(value)
        columns = ", ".join(payload.keys())
        placeholders = ", ".join([":" + key for key in payload.keys()])
        updates = ", ".join([f"{key}=excluded.{key}" for key in payload.keys() if key != "id"])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}"
        with self._connect() as conn:
            conn.execute(sql, payload)
            conn.commit()

    def _upsert(self, table: str, record: Any) -> None:
        payload = asdict(record)
        self._upsert_payload(self._table(table), payload)

    def _get(self, table: str, record_type, key_name: str, key_value: str):
        with self._connect() as conn:
            row = conn.execute(f"SELECT * FROM {self._table(table)} WHERE {key_name} = ?", (key_value,)).fetchone()
            if row is None:
                return None
            data = _deserialize_record(dict(row))
            return record_type(**data)

    def _get_by_product_version(self, table: str, record_type, product_code: str, product_version: str):
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT * FROM {self._table(table)} WHERE product_code = ? AND product_version = ? ORDER BY created_at DESC LIMIT 1",
                (product_code, product_version),
            ).fetchone()
            if row is None:
                return None
            return record_type(**_deserialize_record(dict(row)))

    async def save_product_version(self, record: ProductVersionRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.products", record))
    async def get_product_version(self, product_code: str, product_version: str) -> ProductVersionRecord | None: return await self._run(lambda: self._get_by_product_version("platform_runtime.products", ProductVersionRecord, product_code, product_version))
    async def save_activation(self, record: ActivationRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.activations", record))
    async def append_activation_transition(self, record: Mapping[str, Any]) -> None:
        await self._run(lambda: self._upsert_payload(
            "activation_transitions",
            {
                "id": record.get("id") or f"{record.get('product_code', '')}:{record.get('to_state', '')}:{record.get('correlation_id', '')}",
                "product_code": record.get("product_code", ""),
                "product_version": record.get("product_version", ""),
                "environment": record.get("environment", ""),
                "region": record.get("region", ""),
                "tenant_id": record.get("tenant_id", ""),
                "status": record.get("status", "RECORDED"),
                "version": int(record.get("version", 1)),
                "created_at": record.get("created_at", ""),
                "created_by": record.get("created_by", ""),
                "updated_at": record.get("updated_at", ""),
                "updated_by": record.get("updated_by", ""),
                "correlation_id": record.get("correlation_id", ""),
                "checksum": record.get("checksum", ""),
                "from_state": record.get("from_state", ""),
                "to_state": record.get("to_state", ""),
                "reason": record.get("reason", ""),
                "metadata": record.get("metadata", {}),
            },
        ))
    async def get_activation(self, product_code: str, product_version: str) -> ActivationRecord | None: return await self._run(lambda: self._get_by_product_version("platform_runtime.activations", ActivationRecord, product_code, product_version))
    async def save_approval(self, record: ApprovalRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.approvals", record))
    async def get_approval(self, approval_id: str) -> ApprovalRecord | None: return await self._run(lambda: self._get("platform_runtime.approvals", ApprovalRecord, "id", approval_id))
    async def save_worker_instance(self, record: WorkerInstanceRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.worker_instances", record))
    async def list_worker_instances(self, product_code: str) -> list[WorkerInstanceRecord]: return await self._run(lambda: self._list_records("platform_runtime.worker_instances", WorkerInstanceRecord, product_code))
    async def save_infrastructure_plan(self, record: InfrastructurePlanRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.infrastructure_plans", record))
    async def save_infrastructure_resource(self, record: InfrastructureResourceRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.infrastructure_resources", record))
    async def save_deployment_revision(self, record: DeploymentRevisionRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.deployment_revisions", record))
    async def save_verification_run(self, record: VerificationRunRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.verification_runs", record))
    async def save_verification_result(self, record: VerificationResultRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.verification_results", record))
    async def save_rollback_run(self, record: RollbackRunRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.rollback_runs", record))
    async def save_evidence_record(self, record: EvidenceRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.evidence_records", record))
    async def save_idempotency_record(self, record: IdempotencyRecord) -> None: await self._run(lambda: self._upsert("platform_runtime.idempotency_records", record))
    async def get_idempotency_record(self, product_code: str, idempotency_key: str) -> IdempotencyRecord | None: return await self._run(lambda: self._get("platform_runtime.idempotency_records", IdempotencyRecord, "id", f"{product_code}:{idempotency_key}"))
    async def list_evidence(self, product_code: str) -> list[EvidenceRecord]: return await self._run(lambda: self._list_records("platform_runtime.evidence_records", EvidenceRecord, product_code))
    async def list_deployments(self, product_code: str) -> list[DeploymentRevisionRecord]: return await self._run(lambda: self._list_records("platform_runtime.deployment_revisions", DeploymentRevisionRecord, product_code))
    async def list_verification_runs(self, product_code: str) -> list[VerificationRunRecord]: return await self._run(lambda: self._list_records("platform_runtime.verification_runs", VerificationRunRecord, product_code))
    async def list_rollback_runs(self, product_code: str) -> list[RollbackRunRecord]: return await self._run(lambda: self._list_records("platform_runtime.rollback_runs", RollbackRunRecord, product_code))
    async def list_runtime_instances(self, product_code: str) -> list[RuntimeInstanceRecord]: return await self._run(lambda: self._list_records("platform_runtime.runtime_instances", RuntimeInstanceRecord, product_code))

    def _list_records(self, table: str, record_type, product_code: str):
        with self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM {self._table(table)} WHERE product_code = ? ORDER BY created_at DESC", (product_code,)).fetchall()
            items = []
            for row in rows:
                items.append(record_type(**_deserialize_record(dict(row))))
            return items


class PostgresRuntimeControlRepository(SQLiteRuntimeControlRepository):
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("postgres_dsn_required")
        self.dsn = dsn

    def _connect(self):
        return psycopg.connect(self.dsn)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(DDL)
            conn.commit()

    def _upsert_payload(self, table: str, payload: dict[str, Any]) -> None:
        payload = dict(payload)
        payload.setdefault("created_by", "")
        payload.setdefault("updated_by", "")
        for key, value in list(payload.items()):
            payload[key] = _serialize_value(value)
        sql = _build_insert_sql(table, payload, "postgres")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, payload)
            conn.commit()

    def _get(self, table: str, record_type, key_name: str, key_value: str):
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(f"SELECT * FROM {self._table(table)} WHERE {key_name} = %s", (key_value,))
                row = cur.fetchone()
            if row is None:
                return None
            return record_type(**_deserialize_record(dict(row)))

    def _get_by_product_version(self, table: str, record_type, product_code: str, product_version: str):
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"SELECT * FROM {self._table(table)} WHERE product_code = %s AND product_version = %s ORDER BY created_at DESC LIMIT 1",
                    (product_code, product_version),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return record_type(**_deserialize_record(dict(row)))

    def _list_records(self, table: str, record_type, product_code: str):
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(f"SELECT * FROM {self._table(table)} WHERE product_code = %s ORDER BY created_at DESC", (product_code,))
                rows = cur.fetchall() or []
            return [record_type(**_deserialize_record(dict(row))) for row in rows]


def build_runtime_control_repository(dsn: str | None = None, sqlite_path: Path | None = None):
    if dsn:
        return PostgresRuntimeControlRepository(dsn)
    if sqlite_path is not None:
        return SQLiteRuntimeControlRepository(sqlite_path)
    raise ValueError("runtime_control_repository_required")
