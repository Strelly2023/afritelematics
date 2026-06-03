from dataclasses import FrozenInstanceError

import pytest

from ecosystems.afriride.domain.models.canonical_ride import (
    Ride,
    RideModelViolation,
)
from ecosystems.afriride.domain.state.ride_state import RideStatus


def declared_ride(**overrides):
    payload = {
        "id": "RIDE-001",
        "passenger_id": "PASSENGER-001",
        "pickup_location": {"zone": "ZONE-A", "lat": -37.8136, "lng": 144.9631},
        "dropoff_location": {"zone": "ZONE-B", "lat": -37.8200, "lng": 144.9700},
        "requested_at": "2026-05-25T09:00:00Z",
    }
    payload.update(overrides)
    return Ride(**payload)


def test_ride_accepts_declared_required_fields_only():
    ride = declared_ride()

    assert ride.status == RideStatus.REQUESTED
    assert ride.assigned_driver is None
    assert ride.route_plan is None
    assert ride.price_plan is None


def test_ride_canonical_json_is_stable_across_mapping_order():
    first = declared_ride(
        pickup_location={"zone": "ZONE-A", "lat": -37.8136, "lng": 144.9631}
    )
    second = declared_ride(
        pickup_location={"lng": 144.9631, "zone": "ZONE-A", "lat": -37.8136}
    )

    assert first.canonical_json() == second.canonical_json()
    assert first.ride_hash() == second.ride_hash()


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("id", ""),
        ("passenger_id", " "),
        ("requested_at", None),
    ],
)
def test_ride_rejects_undeclared_text_fields(field_name, value):
    with pytest.raises(RideModelViolation):
        declared_ride(**{field_name: value})


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("pickup_location", {}),
        ("dropoff_location", "ZONE-A"),
        ("route_plan", []),
        ("price_plan", ""),
    ],
)
def test_ride_rejects_invalid_structured_fields(field_name, value):
    with pytest.raises(RideModelViolation):
        declared_ride(**{field_name: value})


def test_ride_normalizes_status_from_text():
    ride = declared_ride(status="ASSIGNED", assigned_driver="DRIVER-001")

    assert ride.status == RideStatus.ASSIGNED


def test_ride_rejects_unknown_status():
    with pytest.raises(RideModelViolation):
        declared_ride(status="DISPATCHED")


def test_ride_model_is_immutable():
    ride = declared_ride()

    with pytest.raises(FrozenInstanceError):
        ride.status = RideStatus.ASSIGNED


def test_ride_allows_declared_optional_plans_without_creating_logic():
    ride = declared_ride(
        assigned_driver="DRIVER-001",
        route_plan={"route_id": "ROUTE-001", "distance_km": 4.2},
        price_plan={"currency": "AUD", "amount": 12.50},
        status=RideStatus.ASSIGNED,
    )

    assert ride.assigned_driver == "DRIVER-001"
    assert ride.route_plan == {"distance_km": 4.2, "route_id": "ROUTE-001"}
    assert ride.price_plan == {"amount": 12.50, "currency": "AUD"}
