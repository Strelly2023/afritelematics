"""PostgreSQL persistence for active NovaRide Fleet aggregates.

This module deliberately implements only Fleet repository contracts currently
used by RuntimeRepositories and FleetService:

* Fleet
* FleetVehicle
* FleetComplianceState

fleet_drivers and fleet_schedules already exist in the canonical database
schema, but active runtime repository contracts for those tables are not
currently exposed. They therefore remain deferred rather than being invented
by the persistence layer.
"""

from __future__ import annotations

from typing import Any, Mapping

from afritech.novaride_runtime.models import (
    Fleet,
    FleetComplianceState,
    FleetVehicle,
)
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


def _encode_fleet(
    fleet: Fleet,
) -> Mapping[str, Any]:
    return {
        "fleet_id": fleet.id,
        "tenant_id": fleet.tenant_id,
        "organization_id": fleet.organization_id,
        "region_code": fleet.region_code,
        "name": fleet.name,
        "status": fleet.status,
        "aggregate_version": fleet.aggregate_version,
        "created_at": fleet.created_at,
        "updated_at": fleet.updated_at,
    }


def _decode_fleet(
    row: Mapping[str, Any],
) -> Fleet:
    return Fleet(
        id=str(row["fleet_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=int(row["aggregate_version"]),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        name=str(row["name"]),
        status=str(row["status"]),
    )


def _encode_fleet_vehicle(
    vehicle: FleetVehicle,
) -> Mapping[str, Any]:
    return {
        "fleet_vehicle_id": vehicle.id,
        "tenant_id": vehicle.tenant_id,
        "organization_id": vehicle.organization_id,
        "region_code": vehicle.region_code,
        "fleet_id": vehicle.fleet_id,
        "vehicle_id": vehicle.vehicle_id,
        "compliant": vehicle.compliant,
        "fuel_or_ev_state": vehicle.fuel_or_ev_state,
        "aggregate_version": vehicle.aggregate_version,
        "created_at": vehicle.created_at,
        "updated_at": vehicle.updated_at,
    }


def _decode_fleet_vehicle(
    row: Mapping[str, Any],
) -> FleetVehicle:
    return FleetVehicle(
        id=str(row["fleet_vehicle_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=int(row["aggregate_version"]),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        fleet_id=str(row["fleet_id"]),
        vehicle_id=str(row["vehicle_id"]),
        compliant=bool(row["compliant"]),
        fuel_or_ev_state=str(row["fuel_or_ev_state"]),
    )


def _encode_fleet_compliance(
    state: FleetComplianceState,
) -> Mapping[str, Any]:
    return {
        "fleet_compliance_id": state.id,
        "tenant_id": state.tenant_id,
        "organization_id": state.organization_id,
        "region_code": state.region_code,
        "fleet_id": state.fleet_id,
        "compliance_hold": state.compliance_hold,
        "reasons": list(state.reasons),
        "aggregate_version": state.aggregate_version,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }


def _decode_fleet_compliance(
    row: Mapping[str, Any],
) -> FleetComplianceState:
    raw_reasons = row["reasons"]

    return FleetComplianceState(
        id=str(row["fleet_compliance_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=int(row["aggregate_version"]),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        fleet_id=str(row["fleet_id"]),
        compliance_hold=bool(row["compliance_hold"]),
        reasons=tuple(raw_reasons or ()),
    )


class PostgresFleetRepository(
    PostgresAggregateRepository[Fleet]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="fleets",
            id_column="fleet_id",
            to_record=_encode_fleet,
            from_record=_decode_fleet,
        )


class PostgresFleetVehicleRepository(
    PostgresAggregateRepository[FleetVehicle]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="fleet_vehicles",
            id_column="fleet_vehicle_id",
            to_record=_encode_fleet_vehicle,
            from_record=_decode_fleet_vehicle,
        )


class PostgresFleetComplianceRepository(
    PostgresAggregateRepository[FleetComplianceState]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="fleet_compliance",
            id_column="fleet_compliance_id",
            to_record=_encode_fleet_compliance,
            from_record=_decode_fleet_compliance,
        )


__all__ = [
    "PostgresFleetRepository",
    "PostgresFleetVehicleRepository",
    "PostgresFleetComplianceRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
