"""PostgreSQL repositories for NovaRide trip and dispatch aggregates."""

from __future__ import annotations

from typing import Any, Mapping

from psycopg.types.json import Jsonb

from afritech.novaride_runtime.models import (
    AddressRef,
    DriverBid,
    DriverOffer,
    Money,
    OfferState,
    Trip,
    TripState,
)
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


def _json_mapping(
    value: Any,
    *,
    field: str,
) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, Jsonb):
        value = value.obj

    if isinstance(value, Mapping):
        return dict(value)

    raise ValueError(
        f"postgres_{field}_invalid:{type(value).__name__}"
    )


def _money_to_json(
    value: Money,
) -> dict[str, str]:
    return {
        "amount": str(value.amount),
        "currency": value.currency,
    }


def _money_from_json(
    value: Any,
    *,
    field: str,
) -> Money:
    payload = _json_mapping(
        value,
        field=field,
    )

    if "amount" not in payload:
        raise ValueError(
            f"postgres_{field}_missing_amount"
        )

    if "currency" not in payload:
        raise ValueError(
            f"postgres_{field}_missing_currency"
        )

    return Money.of(
        str(payload["amount"]),
        str(payload["currency"]),
    )


def _address_to_json(
    value: AddressRef | None,
) -> dict[str, Any] | None:
    if value is None:
        return None

    return {
        "label": value.label,
        "point": (
            None
            if value.point is None
            else value.point.as_dict()
        ),
        "landmark": value.landmark,
        "airport_terminal": value.airport_terminal,
    }


def _address_from_json(
    value: Any,
    *,
    field: str,
) -> AddressRef | None:
    if value is None:
        return None

    payload = _json_mapping(
        value,
        field=field,
    )

    label = payload.get("label")

    if label is None:
        raise ValueError(
            f"postgres_{field}_missing_label"
        )

    point_payload = payload.get("point")
    point = None

    if point_payload is not None:
        point_mapping = _json_mapping(
            point_payload,
            field=f"{field}_point",
        )

        if "lat" not in point_mapping:
            raise ValueError(
                f"postgres_{field}_point_missing_lat"
            )

        if "lng" not in point_mapping:
            raise ValueError(
                f"postgres_{field}_point_missing_lng"
            )

        from afritech.novaride_runtime.common.geography import GeoPoint

        point = GeoPoint(
            lat=float(point_mapping["lat"]),
            lng=float(point_mapping["lng"]),
        )

    return AddressRef(
        label=str(label),
        point=point,
        landmark=(
            None
            if payload.get("landmark") is None
            else str(payload["landmark"])
        ),
        airport_terminal=(
            None
            if payload.get("airport_terminal") is None
            else str(payload["airport_terminal"])
        ),
    )


def _encode_trip(
    trip: Trip,
) -> Mapping[str, Any]:
    return {
        "trip_id": trip.id,
        "tenant_id": trip.tenant_id,
        "organization_id": trip.organization_id,
        "region_code": trip.region_code,
        "booking_id": trip.booking_id,
        "rider_id": trip.rider_id,
        "driver_id": trip.driver_id,
        "vehicle_id": trip.vehicle_id,
        "service_type": trip.service_type,
        "lifecycle_state": (
            trip.lifecycle_state.value
        ),
        "payment_reference": (
            trip.payment_reference
        ),
        "evidence_reference": (
            trip.evidence_reference
        ),
        "payload": Jsonb({
            "schema_version": (
                trip.schema_version
            ),
            "pickup": _address_to_json(
                trip.pickup
            ),
            "destination": _address_to_json(
                trip.destination
            ),
            "fare_reference": (
                trip.fare_reference
            ),
            "safety_state": (
                trip.safety_state
            ),
        }),
        "aggregate_version": (
            trip.aggregate_version
        ),
        "created_at": trip.created_at,
        "updated_at": trip.updated_at,
    }


def _decode_trip(
    row: Mapping[str, Any],
) -> Trip:
    payload = _json_mapping(
        row.get("payload"),
        field="trip_payload",
    )

    return Trip(
        id=str(row["trip_id"]),
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
        schema_version=str(
            payload.get(
                "schema_version",
                "2026.2",
            )
        ),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        booking_id=str(
            row["booking_id"]
        ),
        rider_id=str(
            row["rider_id"]
        ),
        driver_id=(
            None
            if row.get("driver_id") is None
            else str(row["driver_id"])
        ),
        vehicle_id=(
            None
            if row.get("vehicle_id") is None
            else str(row["vehicle_id"])
        ),
        service_type=str(
            row["service_type"]
        ),
        pickup=_address_from_json(
            payload.get("pickup"),
            field="trip_pickup",
        ),
        destination=_address_from_json(
            payload.get("destination"),
            field="trip_destination",
        ),
        fare_reference=(
            None
            if payload.get(
                "fare_reference"
            ) is None
            else str(
                payload["fare_reference"]
            )
        ),
        payment_reference=(
            None
            if row.get(
                "payment_reference"
            ) is None
            else str(
                row["payment_reference"]
            )
        ),
        safety_state=str(
            payload.get(
                "safety_state",
                "NORMAL",
            )
        ),
        lifecycle_state=TripState(
            str(
                row["lifecycle_state"]
            )
        ),
        evidence_reference=(
            None
            if row.get(
                "evidence_reference"
            ) is None
            else str(
                row["evidence_reference"]
            )
        ),
    )


def _encode_driver_offer(
    offer: DriverOffer,
) -> Mapping[str, Any]:
    return {
        "offer_id": offer.id,
        "tenant_id": offer.tenant_id,
        "organization_id": (
            offer.organization_id
        ),
        "region_code": offer.region_code,
        "driver_id": offer.driver_id,
        "trip_id": offer.trip_id,
        "state": offer.state.value,
        "estimated_earnings": Jsonb(
            _money_to_json(
                offer.estimated_earnings
            )
        ),
        "expires_at": offer.expires_at,
        "aggregate_version": (
            offer.aggregate_version
        ),
        "created_at": offer.created_at,
        "updated_at": offer.updated_at,
    }


def _decode_driver_offer(
    row: Mapping[str, Any],
) -> DriverOffer:
    return DriverOffer(
        id=str(row["offer_id"]),
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
        driver_id=str(
            row["driver_id"]
        ),
        trip_id=str(
            row["trip_id"]
        ),
        estimated_earnings=(
            _money_from_json(
                row["estimated_earnings"],
                field="estimated_earnings",
            )
        ),
        state=OfferState(
            str(row["state"])
        ),
        expires_at=row.get(
            "expires_at"
        ),
    )


def _encode_driver_bid(
    bid: DriverBid,
) -> Mapping[str, Any]:
    return {
        "bid_id": bid.id,
        "tenant_id": bid.tenant_id,
        "organization_id": (
            bid.organization_id
        ),
        "region_code": bid.region_code,
        "driver_id": bid.driver_id,
        "offer_id": bid.offer_id,
        "amount": _money_to_json(
            bid.amount
        ),
        "aggregate_version": (
            bid.aggregate_version
        ),
        "created_at": bid.created_at,
        "updated_at": bid.updated_at,
    }


def _decode_driver_bid(
    row: Mapping[str, Any],
) -> DriverBid:
    return DriverBid(
        id=str(row["bid_id"]),
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
        driver_id=str(
            row["driver_id"]
        ),
        offer_id=str(
            row["offer_id"]
        ),
        amount=_money_from_json(
            row["amount"],
            field="driver_bid_amount",
        ),
    )


class PostgresTripRepository(
    PostgresAggregateRepository[Trip]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="trips",
            id_column="trip_id",
            to_record=_encode_trip,
            from_record=_decode_trip,
        )


class PostgresDriverOfferRepository(
    PostgresAggregateRepository[DriverOffer]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="driver_offers",
            id_column="offer_id",
            to_record=_encode_driver_offer,
            from_record=_decode_driver_offer,
        )


class PostgresDriverBidRepository(
    PostgresAggregateRepository[DriverBid]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="driver_bids",
            id_column="bid_id",
            to_record=_encode_driver_bid,
            from_record=_decode_driver_bid,
        )


__all__ = [
    "PostgresDriverBidRepository",
    "PostgresDriverOfferRepository",
    "PostgresTripRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
