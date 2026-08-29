"""PostgreSQL repositories for NovaRide fare quotes and bookings."""

from __future__ import annotations

from typing import Any, Mapping

from psycopg.types.json import Jsonb

from afritech.novaride_runtime.models import (
    AddressRef,
    Booking,
    BookingState,
    FareQuote,
    Money,
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

    return Money.of(
        str(payload["amount"]),
        str(payload["currency"]),
    )


def _address_to_json(
    value: AddressRef | None,
    *,
    field: str,
) -> dict[str, Any]:
    if value is None:
        raise ValueError(
            f"postgres_booking_{field}_required"
        )

    result: dict[str, Any] = {}

    for name in (
        "label",
        "latitude",
        "longitude",
        "place_id",
        "metadata",
    ):
        if hasattr(value, name):
            candidate = getattr(
                value,
                name,
            )

            if candidate is not None:
                result[name] = candidate

    if not result:
        if hasattr(value, "__dict__"):
            result = {
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            }

    if not result:
        result = {
            "label": str(value),
        }

    return result


def _address_from_json(
    value: Any,
    *,
    field: str,
) -> AddressRef:
    payload = _json_mapping(
        value,
        field=f"booking_{field}",
    )

    label = payload.get("label")

    if label is None:
        label = payload.get("address")

    if label is None:
        label = payload.get("name")

    if label is None:
        label = ""

    try:
        return AddressRef(
            label=str(label),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            place_id=payload.get("place_id"),
            metadata=payload.get("metadata", {}),
        )
    except TypeError:
        return AddressRef(
            str(label)
        )


def _encode_fare_quote(
    quote: FareQuote,
) -> Mapping[str, Any]:
    currencies = {
        quote.base_fare.currency,
        quote.distance_fare.currency,
        quote.time_fare.currency,
        quote.taxes.currency,
        quote.tolls.currency,
        quote.local_fees.currency,
        quote.surge.currency,
        quote.discounts.currency,
        quote.estimated_total.currency,
    }

    if len(currencies) != 1:
        raise ValueError(
            "fare_quote_currency_mismatch"
        )

    currency = next(
        iter(currencies)
    )

    return {
        "quote_id": quote.id,
        "tenant_id": quote.tenant_id,
        "organization_id": quote.organization_id,
        "region_code": quote.region_code,
        "service_type": quote.service_type,
        "currency": currency,
        "payload": Jsonb({
            "schema_version": quote.schema_version,
            "base_fare": _money_to_json(
                quote.base_fare
            ),
            "distance_fare": _money_to_json(
                quote.distance_fare
            ),
            "time_fare": _money_to_json(
                quote.time_fare
            ),
            "taxes": _money_to_json(
                quote.taxes
            ),
            "tolls": _money_to_json(
                quote.tolls
            ),
            "local_fees": _money_to_json(
                quote.local_fees
            ),
            "surge": _money_to_json(
                quote.surge
            ),
            "discounts": _money_to_json(
                quote.discounts
            ),
            "estimated_total": _money_to_json(
                quote.estimated_total
            ),
            "pricing_policy_version": (
                quote.pricing_policy_version
            ),
            "payment_methods": list(
                quote.payment_methods
            ),
        }),
        "expires_at": quote.expires_at,
        "aggregate_version": (
            quote.aggregate_version
        ),
        "created_at": quote.created_at,
        "updated_at": quote.updated_at,
    }


def _decode_fare_quote(
    row: Mapping[str, Any],
) -> FareQuote:
    payload = _json_mapping(
        row.get("payload"),
        field="fare_quote_payload",
    )

    return FareQuote(
        id=str(row["quote_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(
            row["organization_id"]
        ),
        region_code=str(row["region_code"]),
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
        service_type=str(
            row["service_type"]
        ),
        base_fare=_money_from_json(
            payload["base_fare"],
            field="base_fare",
        ),
        distance_fare=_money_from_json(
            payload["distance_fare"],
            field="distance_fare",
        ),
        time_fare=_money_from_json(
            payload["time_fare"],
            field="time_fare",
        ),
        taxes=_money_from_json(
            payload["taxes"],
            field="taxes",
        ),
        tolls=_money_from_json(
            payload["tolls"],
            field="tolls",
        ),
        local_fees=_money_from_json(
            payload["local_fees"],
            field="local_fees",
        ),
        surge=_money_from_json(
            payload["surge"],
            field="surge",
        ),
        discounts=_money_from_json(
            payload["discounts"],
            field="discounts",
        ),
        estimated_total=_money_from_json(
            payload["estimated_total"],
            field="estimated_total",
        ),
        pricing_policy_version=str(
            payload.get(
                "pricing_policy_version",
                "pricing-policy-2026.2",
            )
        ),
        payment_methods=tuple(
            str(item)
            for item in payload.get(
                "payment_methods",
                (),
            )
        ),
        expires_at=row["expires_at"],
    )


def _encode_booking(
    booking: Booking,
) -> Mapping[str, Any]:
    return {
        "booking_id": booking.id,
        "tenant_id": booking.tenant_id,
        "organization_id": (
            booking.organization_id
        ),
        "region_code": booking.region_code,
        "rider_id": booking.rider_id,
        "service_type": booking.service_type,
        "state": booking.state.value,
        "fare_quote_id": booking.fare_quote_id,
        "trip_id": booking.trip_id,
        "pickup": Jsonb(
            _address_to_json(
                booking.pickup,
                field="pickup",
            )
        ),
        "destination": Jsonb(
            _address_to_json(
                booking.destination,
                field="destination",
            )
        ),
        "aggregate_version": (
            booking.aggregate_version
        ),
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
    }


def _decode_booking(
    row: Mapping[str, Any],
) -> Booking:
    return Booking(
        id=str(row["booking_id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(
            row["organization_id"]
        ),
        region_code=str(row["region_code"]),
        aggregate_version=int(
            row["aggregate_version"]
        ),
        schema_version="2026.2",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        rider_id=str(row["rider_id"]),
        pickup=_address_from_json(
            row["pickup"],
            field="pickup",
        ),
        destination=_address_from_json(
            row["destination"],
            field="destination",
        ),
        service_type=str(
            row["service_type"]
        ),
        state=BookingState(
            str(row["state"])
        ),
        fare_quote_id=(
            None
            if row.get(
                "fare_quote_id"
            ) is None
            else str(
                row["fare_quote_id"]
            )
        ),
        trip_id=(
            None
            if row.get(
                "trip_id"
            ) is None
            else str(
                row["trip_id"]
            )
        ),
    )


class PostgresFareQuoteRepository(
    PostgresAggregateRepository[FareQuote]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="fare_quotes",
            id_column="quote_id",
            to_record=_encode_fare_quote,
            from_record=_decode_fare_quote,
        )


class PostgresBookingRepository(
    PostgresAggregateRepository[Booking]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="bookings",
            id_column="booking_id",
            to_record=_encode_booking,
            from_record=_decode_booking,
        )


__all__ = [
    "PostgresBookingRepository",
    "PostgresFareQuoteRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
