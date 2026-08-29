"""PostgreSQL authority for durable NovaRide Operations Workspace records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from psycopg.types.json import Jsonb

from afritech.novaride_runtime.persistence.postgres.connection import (
    PostgresConnectionProtocol,
)


@dataclass(frozen=True, slots=True)
class OperationsWorkspaceRecord:
    record_id: str
    tenant_id: str
    region_id: str
    record_type: str
    record_key: str
    state: str
    payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime


def _record_from_row(
    row: Mapping[str, Any],
) -> OperationsWorkspaceRecord:
    return OperationsWorkspaceRecord(
        record_id=str(row["record_id"]),
        tenant_id=str(row["tenant_id"]),
        region_id=str(row["region_id"]),
        record_type=str(row["record_type"]),
        record_key=str(row["record_key"]),
        state=str(row["state"]),
        payload=dict(row.get("payload") or {}),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresOperationsWorkspaceRepository:
    """Tenant-scoped Operations Workspace persistence."""

    table = "novaride_operations_records"

    def __init__(
        self,
        connection: PostgresConnectionProtocol,
    ) -> None:
        self.connection = connection

    def save_values(
        self,
        *,
        record_id: str,
        tenant_id: str,
        region_id: str,
        record_type: str,
        record_key: str,
        state: str,
        payload: dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
    ) -> OperationsWorkspaceRecord:
        return self.save(
            OperationsWorkspaceRecord(
                record_id=record_id,
                tenant_id=tenant_id,
                region_id=region_id,
                record_type=record_type,
                record_key=record_key,
                state=state,
                payload=payload,
                created_at=created_at,
                updated_at=updated_at,
            )
        )

    def save(
        self,
        record: OperationsWorkspaceRecord,
    ) -> OperationsWorkspaceRecord:
        self.connection.execute(
            """
            INSERT INTO novaride_operations_records (
                record_id,
                tenant_id,
                region_id,
                record_type,
                record_key,
                state,
                payload,
                created_at,
                updated_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (
                tenant_id,
                record_type,
                record_key
            )
            DO UPDATE SET
                region_id = EXCLUDED.region_id,
                state = EXCLUDED.state,
                payload = EXCLUDED.payload,
                updated_at = EXCLUDED.updated_at
            """,
            (
                record.record_id,
                record.tenant_id,
                record.region_id,
                record.record_type,
                record.record_key,
                record.state,
                Jsonb(record.payload),
                record.created_at,
                record.updated_at,
            ),
        )

        return record

    def get(
        self,
        *,
        tenant_id: str,
        record_type: str,
        record_key: str,
    ) -> OperationsWorkspaceRecord | None:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_operations_records
            WHERE tenant_id = %s
              AND record_type = %s
              AND record_key = %s
            """,
            (
                tenant_id,
                record_type,
                record_key,
            ),
        )

        row = cursor.fetchone()

        return (
            _record_from_row(row)
            if row is not None
            else None
        )

    def list(
        self,
        *,
        tenant_id: str,
        record_type: str | None = None,
        region_id: str | None = None,
        limit: int = 100,
    ) -> list[OperationsWorkspaceRecord]:
        if limit < 1:
            return []

        clauses = [
            "tenant_id = %s",
        ]

        params: list[object] = [
            tenant_id,
        ]

        if record_type is not None:
            clauses.append(
                "record_type = %s"
            )
            params.append(
                record_type
            )

        if region_id is not None:
            clauses.append(
                "region_id = %s"
            )
            params.append(
                region_id
            )

        params.append(
            limit
        )

        cursor = self.connection.execute(
            f"""
            SELECT *
            FROM novaride_operations_records
            WHERE {" AND ".join(clauses)}
            ORDER BY updated_at DESC, record_id
            LIMIT %s
            """,
            tuple(params),
        )

        return [
            _record_from_row(row)
            for row in cursor.fetchall()
        ]


__all__ = [
    "OperationsWorkspaceRecord",
    "PostgresOperationsWorkspaceRepository",
]
