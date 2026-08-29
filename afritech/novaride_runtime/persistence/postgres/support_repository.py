"""PostgreSQL repository for rider and driver support cases."""

from __future__ import annotations

from typing import Any

from afritech.novaride_runtime.models import ActorType, SupportCase
from afritech.novaride_runtime.persistence.postgres.connection import PostgresConnectionProtocol


def _support_case_from_row(row: Any) -> SupportCase:
    data = dict(row)
    return SupportCase(
        id=str(data["case_id"]),
        tenant_id=str(data["tenant_id"]),
        organization_id=str(data["organization_id"]),
        region_code=str(data["region_code"]),
        aggregate_version=int(data.get("aggregate_version", 1)),
        schema_version=int(data.get("schema_version", 1)),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        subject_id=str(data["subject_id"]),
        case_type=str(data["case_type"]),
        status=str(data["status"]),
        actor_type=ActorType(str(data["actor_type"])),
        actor_id=str(data["actor_id"]),
        trip_id=data.get("trip_id"),
        description=str(data.get("description") or ""),
    )


class PostgresSupportCaseRepository:
    def __init__(self, connection: PostgresConnectionProtocol) -> None:
        self.connection = connection

    def save(self, case: SupportCase) -> SupportCase:
        cursor = self.connection.execute(
            """
            INSERT INTO support_cases (
                case_id, tenant_id, organization_id, region_code,
                aggregate_version, schema_version, created_at, updated_at,
                subject_id, case_type, status, actor_type, actor_id, trip_id, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (case_id) DO UPDATE SET
                aggregate_version = EXCLUDED.aggregate_version,
                schema_version = EXCLUDED.schema_version,
                updated_at = EXCLUDED.updated_at,
                status = EXCLUDED.status,
                description = EXCLUDED.description
            RETURNING *
            """.strip(),
            (
                case.id, case.tenant_id, case.organization_id, case.region_code,
                case.aggregate_version, case.schema_version, case.created_at, case.updated_at,
                case.subject_id, case.case_type, case.status, case.actor_type.value,
                case.actor_id, case.trip_id, case.description,
            ),
        )
        row = cursor.fetchone()
        return _support_case_from_row(row) if row is not None else case

    def get(self, case_id: str) -> SupportCase | None:
        row = self.connection.execute(
            "SELECT * FROM support_cases WHERE case_id = %s", (case_id,)
        ).fetchone()
        return _support_case_from_row(row) if row is not None else None

    def list(self, *, tenant_id: str | None = None) -> list[SupportCase]:
        if tenant_id is None:
            cursor = self.connection.execute("SELECT * FROM support_cases ORDER BY created_at", ())
        else:
            cursor = self.connection.execute(
                "SELECT * FROM support_cases WHERE tenant_id = %s ORDER BY created_at", (tenant_id,)
            )
        return [_support_case_from_row(row) for row in cursor.fetchall()]


__all__ = ["PostgresSupportCaseRepository"]
