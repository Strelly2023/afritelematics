"""PostgreSQL repositories for NovaRide driver aggregates."""

from __future__ import annotations

from psycopg.types.json import Jsonb
from typing import Any, Mapping

from afritech.novaride_runtime.models import (
    DriverAvailability,
    DriverAvailabilityState,
    DriverEligibility,
    DriverProfile,
    DriverShift,
)
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
        f"postgres_driver_payload_invalid:{type(value).__name__}"
    )


def _json_array(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)

    raise ValueError(
        f"postgres_driver_json_array_invalid:{type(value).__name__}"
    )


def _encode_driver_profile(
    driver: DriverProfile,
) -> Mapping[str, Any]:
    return {
        "driver_id": driver.id,
        "tenant_id": driver.tenant_id,
        "organization_id": driver.organization_id,
        "region_code": driver.region_code,
        "identity_id": driver.identity_id,
        "display_name": driver.display_name,
        "vehicle_id": driver.vehicle_id,
        "payload": Jsonb({
            "schema_version": driver.schema_version,
            "licence_reference": driver.licence_reference,
            "app_version": driver.app_version,
        }),
        "aggregate_version": driver.aggregate_version,
        "created_at": driver.created_at,
        "updated_at": driver.updated_at,
    }


def _decode_driver_profile(
    row: Mapping[str, Any],
) -> DriverProfile:
    payload = _payload(row.get("payload"))

    licence_reference = payload.get(
        "licence_reference"
    )

    return DriverProfile(
        id=str(row["driver_id"]),
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
        licence_reference=(
            None
            if licence_reference is None
            else str(licence_reference)
        ),
        vehicle_id=(
            None
            if row.get("vehicle_id") is None
            else str(row["vehicle_id"])
        ),
        app_version=str(
            payload.get(
                "app_version",
                "2026.2.0",
            )
        ),
    )


def _encode_driver_eligibility(
    eligibility: DriverEligibility,
) -> Mapping[str, Any]:
    return {
        "eligibility_id": eligibility.id,
        "tenant_id": eligibility.tenant_id,
        "organization_id": eligibility.organization_id,
        "region_code": eligibility.region_code,
        "driver_id": eligibility.driver_id,
        "eligible": eligibility.eligible,
        "reasons": Jsonb(list(eligibility.reasons)),
        "vehicle_compliant": eligibility.vehicle_compliant,
        "safety_hold": eligibility.safety_hold,
        "compliance_hold": eligibility.compliance_hold,
        "aggregate_version": eligibility.aggregate_version,
        "created_at": eligibility.created_at,
        "updated_at": eligibility.updated_at,
    }


def _decode_driver_eligibility(
    row: Mapping[str, Any],
) -> DriverEligibility:
    return DriverEligibility(
        id=str(row["eligibility_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=int(row["aggregate_version"]),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        driver_id=str(row["driver_id"]),
        eligible=bool(row["eligible"]),
        reasons=_json_array(row.get("reasons")),
        vehicle_compliant=bool(
            row["vehicle_compliant"]
        ),
        safety_hold=bool(
            row["safety_hold"]
        ),
        compliance_hold=bool(
            row["compliance_hold"]
        ),
        app_version_supported=True,
    )


def _encode_driver_availability(
    availability: DriverAvailability,
) -> Mapping[str, Any]:
    if availability.id != availability.driver_id:
        raise ValueError(
            "driver_availability_id_must_equal_driver_id"
        )

    return {
        "driver_id": availability.driver_id,
        "tenant_id": availability.tenant_id,
        "organization_id": availability.organization_id,
        "region_code": availability.region_code,
        "requested_state": availability.requested_state.value,
        "authoritative_state": (
            availability.authoritative_state.value
        ),
        "dispatchable": availability.dispatchable,
        "active_shift_id": availability.active_shift_id,
        "vehicle_id": availability.vehicle_id,
        "location_fresh": availability.location_fresh,
        "server_confirmed_at": (
            availability.server_confirmed_at
        ),
        "aggregate_version": availability.aggregate_version,
        "created_at": availability.created_at,
        "updated_at": availability.updated_at,
    }


def _decode_driver_availability(
    row: Mapping[str, Any],
) -> DriverAvailability:
    driver_id = str(row["driver_id"])

    return DriverAvailability(
        id=driver_id,
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=int(row["aggregate_version"]),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        driver_id=driver_id,
        requested_state=DriverAvailabilityState(
            str(row["requested_state"])
        ),
        authoritative_state=DriverAvailabilityState(
            str(row["authoritative_state"])
        ),
        dispatchable=bool(row["dispatchable"]),
        active_shift_id=(
            None
            if row.get("active_shift_id") is None
            else str(row["active_shift_id"])
        ),
        vehicle_id=(
            None
            if row.get("vehicle_id") is None
            else str(row["vehicle_id"])
        ),
        location_fresh=bool(
            row["location_fresh"]
        ),
        server_confirmed_at=row.get(
            "server_confirmed_at"
        ),
    )


def _encode_driver_shift(
    shift: DriverShift,
) -> Mapping[str, Any]:
    return {
        "shift_id": shift.id,
        "tenant_id": shift.tenant_id,
        "organization_id": shift.organization_id,
        "region_code": shift.region_code,
        "driver_id": shift.driver_id,
        "state": shift.state,
        "started_at": shift.started_at,
        "ended_at": shift.ended_at,
        "aggregate_version": shift.aggregate_version,
        "created_at": shift.created_at,
        "updated_at": shift.updated_at,
    }


def _decode_driver_shift(
    row: Mapping[str, Any],
) -> DriverShift:
    return DriverShift(
        id=str(row["shift_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=int(row["aggregate_version"]),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        driver_id=str(row["driver_id"]),
        state=str(row["state"]),
        started_at=row["started_at"],
        ended_at=row.get("ended_at"),
    )


class PostgresDriverProfileRepository(
    PostgresAggregateRepository[DriverProfile]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="driver_profiles",
            id_column="driver_id",
            to_record=_encode_driver_profile,
            from_record=_decode_driver_profile,
        )


class PostgresDriverEligibilityRepository(
    PostgresAggregateRepository[DriverEligibility]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="driver_eligibility",
            id_column="eligibility_id",
            to_record=_encode_driver_eligibility,
            from_record=_decode_driver_eligibility,
        )


class PostgresDriverAvailabilityRepository(
    PostgresAggregateRepository[DriverAvailability]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="driver_availability",
            id_column="driver_id",
            to_record=_encode_driver_availability,
            from_record=_decode_driver_availability,
        )


class PostgresDriverShiftRepository(
    PostgresAggregateRepository[DriverShift]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="driver_shifts",
            id_column="shift_id",
            to_record=_encode_driver_shift,
            from_record=_decode_driver_shift,
        )


__all__ = [
    "PostgresDriverAvailabilityRepository",
    "PostgresDriverEligibilityRepository",
    "PostgresDriverProfileRepository",
    "PostgresDriverShiftRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
