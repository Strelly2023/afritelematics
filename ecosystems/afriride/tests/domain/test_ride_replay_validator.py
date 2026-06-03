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
from ecosystems.afriride.domain.replay.ride_replay_validator import (
    RideReplayViolation,
    replay_ride_execution,
    validate_ride_replay,
)
from ecosystems.afriride.domain.trace.ride_execution_trace import (
    build_ride_execution_trace,
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


def pricing_config(**overrides):
    payload = {
        "base_fare": "4.00",
        "per_distance_rate": "1.50",
        "per_time_rate": "0.25",
        "currency": "AUD",
    }
    payload.update(overrides)
    return PricingConfig(**payload)


def full_trace():
    declared_ride = ride()
    assignment = match_driver(declared_ride, drivers())
    route = compute_route(declared_ride, graph())
    price = compute_price(declared_ride, assignment, route, pricing_config())
    return build_ride_execution_trace(
        declared_ride,
        assignment=assignment,
        route=route,
        price=price,
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


def test_replay_validates_full_trace_against_declared_inputs():
    report = validate_ride_replay(
        full_trace(),
        ride(),
        drivers=drivers(),
        map_graph=graph(),
        pricing_config=pricing_config(),
    )

    assert report.replay_valid is True
    assert report.ride_hash_match is True
    assert report.dag_hash_match is True
    assert report.assignment_hash_match is True
    assert report.route_hash_match is True
    assert report.price_hash_match is True
    assert report.execution_steps_hash_match is True
    assert report.original_trace_hash == report.replayed_trace_hash


def test_replay_validates_base_trace_without_optimization_artifacts():
    declared_ride = ride()
    trace = build_ride_execution_trace(declared_ride)

    report = validate_ride_replay(trace, declared_ride)

    assert report.replay_valid is True
    assert report.assignment_hash_match is True
    assert report.route_hash_match is True
    assert report.price_hash_match is True
    assert report.execution_steps_hash_match is True


def test_replay_validates_execution_steps():
    declared_ride = ride()
    steps = execution_steps(declared_ride)
    trace = build_ride_execution_trace(declared_ride, execution_steps=steps)

    report = validate_ride_replay(
        trace,
        declared_ride,
        execution_steps=steps,
    )

    assert report.replay_valid is True
    assert report.execution_steps_hash_match is True


def test_replay_detects_ride_input_drift():
    report = replay_ride_execution(
        full_trace(),
        ride(passenger_id="PASSENGER-DRIFT"),
        drivers=drivers(),
        map_graph=graph(),
        pricing_config=pricing_config(),
    )

    assert report.replay_valid is False
    assert report.ride_hash_match is False
    with pytest.raises(RideReplayViolation):
        report.assert_valid()


def test_replay_detects_matching_drift():
    drifted_drivers = [
        {"id": "DRIVER-000", "zone": "ZONE-A", "lat": 0.01, "lng": 0.0},
        *drivers(),
    ]

    report = replay_ride_execution(
        full_trace(),
        ride(),
        drivers=drifted_drivers,
        map_graph=graph(),
        pricing_config=pricing_config(),
    )

    assert report.replay_valid is False
    assert report.assignment_hash_match is False


def test_replay_detects_route_drift():
    drifted_graph = graph()
    drifted_graph["edges"] = [
        {"from": "A", "to": "D", "distance": 0.5, "estimated_time": 1.0},
        *graph()["edges"],
    ]

    report = replay_ride_execution(
        full_trace(),
        ride(),
        drivers=drivers(),
        map_graph=drifted_graph,
        pricing_config=pricing_config(),
    )

    assert report.replay_valid is False
    assert report.route_hash_match is False


def test_replay_detects_price_drift():
    report = replay_ride_execution(
        full_trace(),
        ride(),
        drivers=drivers(),
        map_graph=graph(),
        pricing_config=pricing_config(base_fare="9.00"),
    )

    assert report.replay_valid is False
    assert report.price_hash_match is False


def test_replay_detects_execution_step_drift():
    declared_ride = ride()
    steps = execution_steps(declared_ride)
    trace = build_ride_execution_trace(declared_ride, execution_steps=steps)
    drifted_steps = execute_lifecycle(
        declared_ride,
        (
            TransitionRequest(
                ride_hash=declared_ride.ride_hash(),
                current_state="REQUESTED",
                target_state="MATCHED",
                declared_at="2026-05-25T09:01:00Z",
            ),
            TransitionRequest(
                ride_hash=declared_ride.ride_hash(),
                current_state="MATCHED",
                target_state="DRIVER_ACCEPTED",
            ),
        ),
    )

    report = replay_ride_execution(
        trace,
        declared_ride,
        execution_steps=drifted_steps,
    )

    assert report.replay_valid is False
    assert report.execution_steps_hash_match is False


def test_replay_fails_closed_when_assignment_inputs_are_missing():
    with pytest.raises(RideReplayViolation):
        replay_ride_execution(
            full_trace(),
            ride(),
            map_graph=graph(),
            pricing_config=pricing_config(),
        )


def test_replay_fails_closed_when_route_inputs_are_missing():
    with pytest.raises(RideReplayViolation):
        replay_ride_execution(
            full_trace(),
            ride(),
            drivers=drivers(),
            pricing_config=pricing_config(),
        )


def test_replay_fails_closed_when_pricing_config_is_missing():
    with pytest.raises(RideReplayViolation):
        replay_ride_execution(
            full_trace(),
            ride(),
            drivers=drivers(),
            map_graph=graph(),
        )


def test_replay_fails_closed_when_execution_steps_are_missing():
    declared_ride = ride()
    trace = build_ride_execution_trace(
        declared_ride,
        execution_steps=execution_steps(declared_ride),
    )

    with pytest.raises(RideReplayViolation):
        replay_ride_execution(trace, declared_ride)


def test_replay_detects_trace_hash_drift():
    trace = replace(full_trace(), dag_hash="not-the-dag-hash")

    report = replay_ride_execution(
        trace,
        ride(),
        drivers=drivers(),
        map_graph=graph(),
        pricing_config=pricing_config(),
    )

    assert report.replay_valid is False
    assert report.dag_hash_match is False
