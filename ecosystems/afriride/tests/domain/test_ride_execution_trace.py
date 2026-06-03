from dataclasses import replace

import pytest

from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.execution.ride_execution_engine import (
    TransitionRequest,
    execute_lifecycle,
)
from ecosystems.afriride.domain.optimization.deterministic_matching import match_driver
from ecosystems.afriride.domain.optimization.deterministic_pricing import (
    PricingConfig,
    compute_price,
)
from ecosystems.afriride.domain.optimization.deterministic_routing import compute_route
from ecosystems.afriride.domain.state.ride_lifecycle_dag import dag_hash
from ecosystems.afriride.domain.trace.ride_execution_trace import (
    RideExecutionTraceViolation,
    build_ride_execution_trace,
    verify_ride_execution_trace,
)


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
    return [
        {"id": "DRIVER-002", "zone": "ZONE-A", "lat": 0.2, "lng": 0.0},
        {"id": "DRIVER-001", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0},
    ]


def graph():
    return {
        "nodes": {
            "A": {"zone": "ZONE-A"},
            "B": {"zone": "ZONE-A"},
            "D": {"zone": "ZONE-B"},
        },
        "edges": [
            {"from": "A", "to": "B", "distance": 1.0, "estimated_time": 1.0},
            {"from": "B", "to": "D", "distance": 1.0, "estimated_time": 1.0},
            {"from": "A", "to": "D", "distance": 3.0, "estimated_time": 1.0},
        ],
    }


def pricing_config():
    return PricingConfig(
        base_fare="4.00",
        per_distance_rate="1.50",
        per_time_rate="0.25",
        currency="AUD",
    )


def execution_steps(declared_ride):
    return execute_lifecycle(
        declared_ride,
        (
            TransitionRequest(
                ride_hash=declared_ride.ride_hash(),
                current_state="REQUESTED",
                target_state="MATCHED",
            ),
            TransitionRequest(
                ride_hash=declared_ride.ride_hash(),
                current_state="MATCHED",
                target_state="DRIVER_ACCEPTED",
            ),
        ),
    )


def test_trace_records_ride_and_dag_without_optimization_artifacts():
    declared_ride = ride()
    trace = build_ride_execution_trace(declared_ride)

    assert trace.to_canonical_dict() == {
        "assignment_hash": None,
        "dag_hash": dag_hash(),
        "execution_steps_hash": None,
        "price_hash": None,
        "ride_hash": declared_ride.ride_hash(),
        "ride_id": "RIDE-001",
        "route_hash": None,
    }


def test_trace_records_matching_and_routing_hashes():
    declared_ride = ride()
    assignment = match_driver(declared_ride, drivers())
    route = compute_route(declared_ride, graph())
    trace = build_ride_execution_trace(
        declared_ride,
        assignment=assignment,
        route=route,
    )

    assert trace.assignment_hash == assignment.assignment_hash()
    assert trace.route_hash == route.route_hash()
    assert verify_ride_execution_trace(
        trace,
        declared_ride,
        assignment=assignment,
        route=route,
    )


def test_trace_records_price_hash():
    declared_ride = ride()
    assignment = match_driver(declared_ride, drivers())
    route = compute_route(declared_ride, graph())
    price = compute_price(declared_ride, assignment, route, pricing_config())
    trace = build_ride_execution_trace(
        declared_ride,
        assignment=assignment,
        route=route,
        price=price,
    )

    assert trace.price_hash == price.price_hash()
    assert verify_ride_execution_trace(
        trace,
        declared_ride,
        assignment=assignment,
        route=route,
        price=price,
    )


def test_trace_records_execution_step_hashes():
    declared_ride = ride()
    steps = execution_steps(declared_ride)
    trace = build_ride_execution_trace(declared_ride, execution_steps=steps)

    assert trace.execution_steps_hash is not None
    assert verify_ride_execution_trace(
        trace,
        declared_ride,
        execution_steps=steps,
    )


def test_trace_canonical_representation_is_stable():
    declared_ride = ride()
    assignment = match_driver(declared_ride, drivers())
    route = compute_route(declared_ride, graph())
    first = build_ride_execution_trace(declared_ride, assignment=assignment, route=route)
    second = build_ride_execution_trace(declared_ride, assignment=assignment, route=route)

    assert first.canonical_json() == second.canonical_json()
    assert first.trace_hash() == second.trace_hash()


def test_trace_rejects_assignment_for_different_ride():
    declared_ride = ride()
    other_ride = ride(id="RIDE-002")
    assignment = match_driver(other_ride, drivers())

    with pytest.raises(RideExecutionTraceViolation):
        build_ride_execution_trace(declared_ride, assignment=assignment)


def test_trace_rejects_route_for_different_ride():
    declared_ride = ride()
    other_ride = ride(id="RIDE-002")
    route = compute_route(other_ride, graph())

    with pytest.raises(RideExecutionTraceViolation):
        build_ride_execution_trace(declared_ride, route=route)


def test_trace_rejects_price_without_required_artifacts():
    declared_ride = ride()
    assignment = match_driver(declared_ride, drivers())
    route = compute_route(declared_ride, graph())
    price = compute_price(declared_ride, assignment, route, pricing_config())

    with pytest.raises(RideExecutionTraceViolation):
        build_ride_execution_trace(declared_ride, price=price)


def test_trace_verification_detects_artifact_drift():
    declared_ride = ride()
    assignment = match_driver(declared_ride, drivers())
    route = compute_route(declared_ride, graph())
    trace = build_ride_execution_trace(
        declared_ride,
        assignment=assignment,
        route=route,
    )
    drifted = replace(trace, route_hash="not-the-route-hash")

    assert not verify_ride_execution_trace(
        drifted,
        declared_ride,
        assignment=assignment,
        route=route,
    )
