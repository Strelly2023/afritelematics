"""PostgreSQL persistence for NovaRide derived read-model projections.

Projection persistence is explicitly non-authoritative.

NovaRide domain aggregates remain the source of business truth. Projection
state is derived from the mobility event stream and must remain rebuildable
through the replay subsystem.

The projection-state table uses a composite identity:

    projection_name + tenant_id + region_code

and is therefore intentionally implemented as a specialised repository rather
than being forced into the generic single-id PostgresAggregateRepository.

Projection version rows are immutable derived-history evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from afritech.novaride_runtime.read_models.projections import (
    ProjectionRecord,
)
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    SyncPostgresConnection,
)


@dataclass(frozen=True, slots=True)
class ProjectionVersionRecord:
    projection_version_id: str
    projection_name: str
    tenant_id: str
    region: str
    state_hash: str
    payload: dict[str, Any]
    created_at: datetime


def _projection_from_row(
    row: Mapping[str, Any],
) -> ProjectionRecord:
    last_timestamp = row.get(
        "last_event_timestamp"
    )

    if (
        last_timestamp is not None
        and not isinstance(last_timestamp, str)
    ):
        last_timestamp = (
            last_timestamp.isoformat()
            if hasattr(last_timestamp, "isoformat")
            else str(last_timestamp)
        )

    return ProjectionRecord(
        projection_name=str(
            row["projection_name"]
        ),
        tenant_id=str(
            row["tenant_id"]
        ),
        region=str(
            row["region_code"]
        ),
        schema_version=str(
            row["schema_version"]
        ),
        checkpoint=int(
            row.get("checkpoint", 0)
        ),
        last_event_id=(
            None
            if row.get("last_event_id") is None
            else str(row["last_event_id"])
        ),
        last_event_timestamp=last_timestamp,
        state_hash=(
            None
            if row.get("state_hash") is None
            else str(row["state_hash"])
        ),
        rebuild_status=str(
            row["rebuild_status"]
        ),
        lag_seconds=float(
            row.get("lag_seconds", 0)
        ),
    )


def _projection_version_from_row(
    row: Mapping[str, Any],
) -> ProjectionVersionRecord:
    return ProjectionVersionRecord(
        projection_version_id=str(
            row["projection_version_id"]
        ),
        projection_name=str(
            row["projection_name"]
        ),
        tenant_id=str(
            row["tenant_id"]
        ),
        region=str(
            row["region_code"]
        ),
        state_hash=str(
            row["state_hash"]
        ),
        payload=dict(
            row.get("payload") or {}
        ),
        created_at=row["created_at"],
    )


class PostgresProjectionStateRepository:
    """Synchronous persistence for current derived projection state."""

    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        self.connection = connection

    def save(
        self,
        record: ProjectionRecord,
        *,
        payload: Mapping[str, Any] | None = None,
    ) -> ProjectionRecord:
        self.connection.execute(
            """
            INSERT INTO novaride_projection_state (
                projection_name,
                tenant_id,
                region_code,
                schema_version,
                checkpoint,
                last_event_id,
                last_event_timestamp,
                state_hash,
                rebuild_status,
                lag_seconds,
                payload,
                updated_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, now()
            )
            ON CONFLICT (
                projection_name,
                tenant_id,
                region_code
            )
            DO UPDATE SET
                schema_version = EXCLUDED.schema_version,
                checkpoint = EXCLUDED.checkpoint,
                last_event_id = EXCLUDED.last_event_id,
                last_event_timestamp = EXCLUDED.last_event_timestamp,
                state_hash = EXCLUDED.state_hash,
                rebuild_status = EXCLUDED.rebuild_status,
                lag_seconds = EXCLUDED.lag_seconds,
                payload = EXCLUDED.payload,
                updated_at = now()
            """,
            (
                record.projection_name,
                record.tenant_id,
                record.region,
                record.schema_version,
                record.checkpoint,
                record.last_event_id,
                record.last_event_timestamp,
                record.state_hash,
                record.rebuild_status,
                record.lag_seconds,
                dict(payload or {}),
            ),
        )

        return record

    def get(
        self,
        *,
        projection_name: str,
        tenant_id: str,
        region: str,
    ) -> ProjectionRecord | None:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_projection_state
            WHERE projection_name = %s
              AND tenant_id = %s
              AND region_code = %s
            """,
            (
                projection_name,
                tenant_id,
                region,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return _projection_from_row(
            dict(row)
        )

    def list(
        self,
        *,
        tenant_id: str,
        region: str | None = None,
    ) -> list[ProjectionRecord]:
        params: list[Any] = [
            tenant_id,
        ]

        query = (
            "SELECT * "
            "FROM novaride_projection_state "
            "WHERE tenant_id = %s"
        )

        if region is not None:
            query += (
                " AND region_code = %s"
            )
            params.append(region)

        query += (
            " ORDER BY projection_name, region_code"
        )

        cursor = self.connection.execute(
            query,
            tuple(params),
        )

        return [
            _projection_from_row(
                dict(row)
            )
            for row in cursor.fetchall()
        ]

    def delete(
        self,
        *,
        projection_name: str,
        tenant_id: str,
        region: str,
    ) -> None:
        self.connection.execute(
            """
            DELETE FROM novaride_projection_state
            WHERE projection_name = %s
              AND tenant_id = %s
              AND region_code = %s
            """,
            (
                projection_name,
                tenant_id,
                region,
            ),
        )


class PostgresProjectionVersionRepository:
    """Immutable history for derived projection versions."""

    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        self.connection = connection

    def append(
        self,
        record: ProjectionVersionRecord,
    ) -> ProjectionVersionRecord:
        self.connection.execute(
            """
            INSERT INTO novaride_projection_versions (
                projection_version_id,
                projection_name,
                tenant_id,
                region_code,
                state_hash,
                payload,
                created_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                record.projection_version_id,
                record.projection_name,
                record.tenant_id,
                record.region,
                record.state_hash,
                record.payload,
                record.created_at,
            ),
        )

        return record

    def get(
        self,
        projection_version_id: str,
    ) -> ProjectionVersionRecord | None:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_projection_versions
            WHERE projection_version_id = %s
            """,
            (
                projection_version_id,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return _projection_version_from_row(
            dict(row)
        )

    def list(
        self,
        *,
        projection_name: str,
        tenant_id: str,
        region: str,
    ) -> list[ProjectionVersionRecord]:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_projection_versions
            WHERE projection_name = %s
              AND tenant_id = %s
              AND region_code = %s
            ORDER BY created_at DESC,
                     projection_version_id DESC
            """,
            (
                projection_name,
                tenant_id,
                region,
            ),
        )

        return [
            _projection_version_from_row(
                dict(row)
            )
            for row in cursor.fetchall()
        ]


__all__ = [
    "PostgresProjectionStateRepository",
    "PostgresProjectionVersionRepository",
    "ProjectionVersionRecord",
]
