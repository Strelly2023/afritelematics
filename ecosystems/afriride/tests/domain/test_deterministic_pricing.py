from dataclasses import FrozenInstanceError

import pytest

from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_matching import match_driver
from ecosystems.afriride.domain.optimization.deterministic_pricing import (
    PricingConfig,
    PricingViolation,
    compute_price,
)
from ecosystems.afriride.domain.optimization.deterministic_routing import compute_route


def ride(**overrides):
    payload = {
        "id": "RIDE-001",
        "passenger_id": "PASSENGER-001",
        "pickup_location": {"zone": "ZONE-A", "node_id": "A", "lat": 0.0, "lng": 0.0},
        "dropoff_location": {"zone": "ZONE-B", "node_id": "D", "lat": 1.0, "lng": 1.0},
        "requested_at": "2026-05-25T09:00:00Z",
    }
    payload.update(overrides)
    return Ride(**payload)


def drivers():
    return [{"id": "DRIVER-001", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0}]


def graph():
    return {
        "nodes": {"A": {"zone": "ZONE-A"}, "B": {}, "D": {"zone": "ZONE-B"}},
        "edges": [
            {"from": "A", "to": "B", "distance": 2.0, "estimated_time": 3.0},
            {"from": "B", "to": "D", "distance": 3.0, "estimated_time": 7.0},
        ],
    }


def config(**overrides):
    payload = {
        "base_fare": "4.00",
        "per_distance_rate": "1.50",
        "per_time_rate": "0.25",
        "currency": "AUD",
    }
    payload.update(overrides)
    return PricingConfig(**payload)


def artifacts(declared_ride=None):
    declared_ride = declared_ride or ride()
    assignment = match_driver(declared_ride, drivers())
    route = compute_route(declared_ride, graph())
    return declared_ride, assignment, route


def test_pricing_computes_declared_cost_components():
    declared_ride, assignment, route = artifacts()
    price = compute_price(declared_ride, assignment, route, config())

    assert str(price.base_fare) == "4.00"
    assert str(price.distance_cost) == "7.50"
    assert str(price.time_cost) == "2.50"
    assert str(price.total_cost) == "14.00"
    assert price.currency == "AUD"


def test_pricing_representation_and_hash_are_stable():
    declared_ride, assignment, route = artifacts()
    first = compute_price(declared_ride, assignment, route, config())
    second = compute_price(declared_ride, assignment, route, config())

    assert first.canonical_json() == second.canonical_json()
    assert first.price_hash() == second.price_hash()
    assert first.pricing_config_hash == config().config_hash()


def test_pricing_output_is_immutable():
    declared_ride, assignment, route = artifacts()
    price = compute_price(declared_ride, assignment, route, config())

    with pytest.raises(FrozenInstanceError):
        price.total_cost = "0.00"


def test_pricing_rejects_assignment_for_different_ride():
    declared_ride = ride()
    other_ride, other_assignment, _ = artifacts(ride(id="RIDE-002"))
    route = compute_route(declared_ride, graph())

    assert other_ride.id == "RIDE-002"
    with pytest.raises(PricingViolation):
        compute_price(declared_ride, other_assignment, route, config())


def test_pricing_rejects_route_for_different_ride():
    declared_ride, assignment, _ = artifacts()
    other_route = compute_route(ride(id="RIDE-002"), graph())

    with pytest.raises(PricingViolation):
        compute_price(declared_ride, assignment, other_route, config())


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("base_fare", "-1.00"),
        ("per_distance_rate", True),
        ("per_time_rate", "not-money"),
        ("currency", ""),
    ],
)
def test_pricing_rejects_undeclared_config_values(field_name, value):
    with pytest.raises(PricingViolation):
        config(**{field_name: value})
