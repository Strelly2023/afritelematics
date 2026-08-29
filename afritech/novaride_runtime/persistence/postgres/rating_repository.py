"""PostgreSQL repository for NovaRide trip ratings."""

from __future__ import annotations

from typing import Any

from afritech.novaride_runtime.models import Rating
from afritech.novaride_runtime.persistence.postgres.connection import (
    PostgresConnectionProtocol,
)


def _rating_from_row(row: Any) -> Rating:
    if row is None:
        raise ValueError("rating_row_required")

    if hasattr(row, "keys"):
        data = dict(row)
    elif isinstance(row, dict):
        data = row
    else:
        raise TypeError("rating_row_mapping_required")

    return Rating(
        id=str(data["rating_id"]),
        tenant_id=str(data["tenant_id"]),
        organization_id=str(data["organization_id"]),
        region_code=str(data["region_code"]),
        aggregate_version=int(data.get("aggregate_version", 1)),
        schema_version=int(data.get("schema_version", 1)),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        trip_id=str(data["trip_id"]),
        score=int(data["score"]),
        comment=data.get("comment"),
    )


class PostgresRatingRepository:
    """Transaction-scoped PostgreSQL Rating repository.

    Transaction ownership remains with the caller/UoW.
    This repository never commits or rolls back.
    """

    def __init__(
        self,
        connection: PostgresConnectionProtocol,
    ) -> None:
        self.connection = connection

    def save(
        self,
        rating: Rating,
    ) -> Rating:
        cursor = self.connection.execute(
            """
            INSERT INTO trip_ratings (
                rating_id,
                tenant_id,
                organization_id,
                region_code,
                aggregate_version,
                schema_version,
                created_at,
                updated_at,
                trip_id,
                score,
                comment
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (rating_id)
            DO UPDATE SET
                aggregate_version = EXCLUDED.aggregate_version,
                schema_version = EXCLUDED.schema_version,
                updated_at = EXCLUDED.updated_at,
                score = EXCLUDED.score,
                comment = EXCLUDED.comment
            RETURNING *
            """.strip(),
            (
                rating.id,
                rating.tenant_id,
                rating.organization_id,
                rating.region_code,
                rating.aggregate_version,
                rating.schema_version,
                rating.created_at,
                rating.updated_at,
                rating.trip_id,
                rating.score,
                rating.comment,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return rating

        return _rating_from_row(row)

    def get(
        self,
        rating_id: str,
    ) -> Rating | None:
        cursor = self.connection.execute(
            (
                "SELECT * FROM trip_ratings "
                "WHERE rating_id = %s"
            ),
            (rating_id,),
        )

        row = cursor.fetchone()

        return (
            _rating_from_row(row)
            if row is not None
            else None
        )

    def get_by_trip(
        self,
        trip_id: str,
        *,
        tenant_id: str | None = None,
    ) -> Rating | None:
        if tenant_id is None:
            cursor = self.connection.execute(
                (
                    "SELECT * FROM trip_ratings "
                    "WHERE trip_id = %s "
                    "ORDER BY rating_id "
                    "LIMIT 1"
                ),
                (trip_id,),
            )
        else:
            cursor = self.connection.execute(
                (
                    "SELECT * FROM trip_ratings "
                    "WHERE trip_id = %s "
                    "AND tenant_id = %s "
                    "ORDER BY rating_id "
                    "LIMIT 1"
                ),
                (
                    trip_id,
                    tenant_id,
                ),
            )

        row = cursor.fetchone()

        return (
            _rating_from_row(row)
            if row is not None
            else None
        )

    def list(
        self,
        *,
        tenant_id: str | None = None,
    ) -> list[Rating]:
        if tenant_id is None:
            cursor = self.connection.execute(
                (
                    "SELECT * FROM trip_ratings "
                    "ORDER BY rating_id"
                ),
                (),
            )
        else:
            cursor = self.connection.execute(
                (
                    "SELECT * FROM trip_ratings "
                    "WHERE tenant_id = %s "
                    "ORDER BY rating_id"
                ),
                (tenant_id,),
            )

        return [
            _rating_from_row(row)
            for row in cursor.fetchall()
        ]


__all__ = [
    "PostgresRatingRepository",
]
