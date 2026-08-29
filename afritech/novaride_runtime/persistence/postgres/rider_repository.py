"""PostgreSQL repository for NovaRide rider profiles."""

from __future__ import annotations

from typing import Any, Mapping

from psycopg.types.json import Jsonb

from afritech.novaride_runtime.models import RiderProfile
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


def _payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, Mapping):
        return dict(value)

    raise ValueError(
        f"postgres_rider_payload_invalid:{type(value).__name__}"
    )


def _encode_rider(
    rider: RiderProfile,
) -> Mapping[str, Any]:
    return {
        "rider_id": rider.id,
        "tenant_id": rider.tenant_id,
        "organization_id": rider.organization_id,
        "region_code": rider.region_code,
        "identity_id": rider.identity_id,
        "display_name": rider.display_name,
        "payload": Jsonb({
            "schema_version": rider.schema_version,
            "locale": rider.locale,
            "currency": rider.currency,
            "trust_status": rider.trust_status,
        }),
        "aggregate_version": rider.aggregate_version,
        "created_at": rider.created_at,
        "updated_at": rider.updated_at,
    }


def _decode_rider(
    row: Mapping[str, Any],
) -> RiderProfile:
    payload = _payload(row.get("payload"))

    return RiderProfile(
        id=str(row["rider_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=int(row["aggregate_version"]),
        schema_version=str(
            payload.get(
                "schema_version",
                "2026.2",
            )
        ),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        identity_id=str(row["identity_id"]),
        display_name=str(row["display_name"]),
        locale=str(
            payload.get(
                "locale",
                "en",
            )
        ),
        currency=str(
            payload.get(
                "currency",
                "AUD",
            )
        ),
        trust_status=str(
            payload.get(
                "trust_status",
                "BASIC",
            )
        ),
    )


class PostgresRiderRepository(
    PostgresAggregateRepository[RiderProfile]
):
    """Synchronous PostgreSQL RiderProfile repository."""

    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="rider_profiles",
            id_column="rider_id",
            to_record=_encode_rider,
            from_record=_decode_rider,
        )


__all__ = [
    "PostgresRiderRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
