"""PostgreSQL repositories for NovaRide-owned safety workflow aggregates.

This module persists NovaRide mobility-operation state only:

* EmergencyCase
* Incident

Broader fraud, trust, compliance, reputation, and external risk evidence remain
outside this repository boundary and belong to NovaTrust integrations.
"""

from __future__ import annotations

from typing import Any, Mapping

from afritech.novaride_runtime.models import (
    ActorType,
    EmergencyCase,
    EmergencyState,
    Incident,
    IncidentState,
)
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


def _encode_emergency(
    emergency: EmergencyCase,
) -> Mapping[str, Any]:
    return {
        "emergency_id": emergency.id,
        "tenant_id": emergency.tenant_id,
        "organization_id": emergency.organization_id,
        "region_code": emergency.region_code,
        "source": emergency.source.value,
        "source_id": emergency.source_id,
        "trip_id": emergency.trip_id,
        "state": emergency.state.value,
        "evidence_locked": emergency.evidence_locked,
        "visible_reference": emergency.visible_reference,
        "aggregate_version": emergency.aggregate_version,
        "created_at": emergency.created_at,
        "updated_at": emergency.updated_at,
    }


def _decode_emergency(
    row: Mapping[str, Any],
) -> EmergencyCase:
    return EmergencyCase(
        id=str(row["emergency_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(
            row["organization_id"]
        ),
        region_code=str(
            row["region_code"]
        ),
        aggregate_version=int(
            row["aggregate_version"]
        ),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        source=ActorType(
            str(row["source"])
        ),
        source_id=str(
            row["source_id"]
        ),
        trip_id=(
            None
            if row.get("trip_id") is None
            else str(row["trip_id"])
        ),
        state=EmergencyState(
            str(row["state"])
        ),
        evidence_locked=bool(
            row["evidence_locked"]
        ),
        visible_reference=str(
            row["visible_reference"]
        ),
    )


def _encode_incident(
    incident: Incident,
) -> Mapping[str, Any]:
    return {
        "incident_id": incident.id,
        "tenant_id": incident.tenant_id,
        "organization_id": incident.organization_id,
        "region_code": incident.region_code,
        "category": incident.category,
        "state": incident.state.value,
        "severity": incident.severity,
        "owner_id": incident.owner_id,
        "aggregate_version": incident.aggregate_version,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
    }


def _decode_incident(
    row: Mapping[str, Any],
) -> Incident:
    return Incident(
        id=str(row["incident_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(
            row["organization_id"]
        ),
        region_code=str(
            row["region_code"]
        ),
        aggregate_version=int(
            row["aggregate_version"]
        ),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        category=str(
            row["category"]
        ),
        state=IncidentState(
            str(row["state"])
        ),
        severity=str(
            row["severity"]
        ),
        owner_id=(
            None
            if row.get("owner_id") is None
            else str(row["owner_id"])
        ),
    )


class PostgresEmergencyRepository(
    PostgresAggregateRepository[EmergencyCase]
):
    """Synchronous repository for NovaRide emergency workflow state."""

    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="emergencies",
            id_column="emergency_id",
            to_record=_encode_emergency,
            from_record=_decode_emergency,
        )


class PostgresIncidentRepository(
    PostgresAggregateRepository[Incident]
):
    """Synchronous repository for NovaRide incident workflow state."""

    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="incidents",
            id_column="incident_id",
            to_record=_encode_incident,
            from_record=_decode_incident,
        )


__all__ = [
    "PostgresEmergencyRepository",
    "PostgresIncidentRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
