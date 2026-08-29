from __future__ import annotations

from typing import Any, Mapping

from afritech.novaride_runtime.models import (
    TransitJourney,
    TransitLeg,
)
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


def _encode_leg(leg: TransitLeg) -> dict[str, Any]:
    return {
        "mode": leg.mode,
        "from_label": leg.from_label,
        "to_label": leg.to_label,
        "provider": leg.provider,
    }


def _decode_leg(payload: Mapping[str, Any]) -> TransitLeg:
    return TransitLeg(
        mode=str(payload["mode"]),
        from_label=str(payload["from_label"]),
        to_label=str(payload["to_label"]),
        provider=str(payload.get("provider", "provider_neutral")),
    )


def _to_transit_journey_record(
    journey: TransitJourney,
) -> dict[str, Any]:
    return {
        "journey_id": journey.id,
        "tenant_id": journey.tenant_id,
        "organization_id": journey.organization_id,
        "region_code": journey.region_code,
        "rider_id": journey.rider_id,
        "legs": [
            _encode_leg(leg)
            for leg in journey.legs
        ],
        "first_mile_booking_id": journey.first_mile_booking_id,
        "last_mile_booking_id": journey.last_mile_booking_id,
        "aggregate_version": journey.aggregate_version,
        "created_at": journey.created_at,
        "updated_at": journey.updated_at,
    }


def _from_transit_journey_record(
    record: Mapping[str, Any],
) -> TransitJourney:
    raw_legs = record.get("legs") or ()

    return TransitJourney(
        id=str(record["journey_id"]),
        tenant_id=str(record["tenant_id"]),
        organization_id=str(record["organization_id"]),
        region_code=str(record["region_code"]),
        aggregate_version=int(record.get("aggregate_version", 1)),
        created_at=record["created_at"],
        updated_at=record["updated_at"],
        rider_id=str(record["rider_id"]),
        legs=tuple(
            _decode_leg(leg)
            for leg in raw_legs
        ),
        first_mile_booking_id=record.get(
            "first_mile_booking_id"
        ),
        last_mile_booking_id=record.get(
            "last_mile_booking_id"
        ),
    )


class PostgresTransitJourneyRepository(
    PostgresAggregateRepository[TransitJourney]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection,
            table="transit_journeys",
            id_column="journey_id",
            to_record=_to_transit_journey_record,
            from_record=_from_transit_journey_record,
        )


__all__ = [
    "PostgresTransitJourneyRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
