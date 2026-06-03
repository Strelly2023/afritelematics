import pytest

from ecosystems.afriride.domain.execution.ride_execution_engine import (
    RideExecutionViolation,
    TransitionRequest,
    execute_lifecycle,
    execute_transition,
    execution_steps_hash,
)
from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.state.ride_lifecycle_dag import RideLifecycleState


def ride():
    return Ride(
        id="RIDE-001",
        passenger_id="PASSENGER-001",
        pickup_location={"zone": "ZONE-A", "node_id": "A", "lat": 0.0, "lng": 0.0},
        dropoff_location={"zone": "ZONE-B", "node_id": "D", "lat": 1.0, "lng": 1.0},
        requested_at="2026-05-25T09:00:00Z",
    )


def request(current_state, target_state, declared_ride=None):
    declared_ride = declared_ride or ride()
    return TransitionRequest(
        ride_hash=declared_ride.ride_hash(),
        current_state=current_state,
        target_state=target_state,
        declared_at="2026-05-25T09:01:00Z",
    )


def test_execution_records_explicit_transition_without_mutating_ride():
    declared_ride = ride()
    step = execute_transition(
        declared_ride,
        request("REQUESTED", "MATCHED", declared_ride),
        sequence=0,
    )

    assert step.from_state == RideLifecycleState.REQUESTED
    assert step.to_state == RideLifecycleState.MATCHED
    assert step.sequence == 0
    assert step.ride_hash == declared_ride.ride_hash()
    assert declared_ride.status.value == "REQUESTED"


def test_execution_records_ordered_lifecycle_history():
    declared_ride = ride()
    steps = execute_lifecycle(
        declared_ride,
        (
            request("REQUESTED", "MATCHED", declared_ride),
            request("MATCHED", "DRIVER_ACCEPTED", declared_ride),
            request("DRIVER_ACCEPTED", "IN_PROGRESS", declared_ride),
        ),
    )

    assert [step.sequence for step in steps] == [0, 1, 2]
    assert [step.to_state.value for step in steps] == [
        "MATCHED",
        "DRIVER_ACCEPTED",
        "IN_PROGRESS",
    ]
    assert execution_steps_hash(steps) == execution_steps_hash(steps)


def test_execution_rejects_hidden_transition_jump():
    with pytest.raises(Exception):
        execute_transition(
            ride(),
            request("REQUESTED", "IN_PROGRESS"),
            sequence=0,
        )


def test_execution_rejects_sequence_discontinuity():
    declared_ride = ride()

    with pytest.raises(RideExecutionViolation):
        execute_lifecycle(
            declared_ride,
            (
                request("REQUESTED", "MATCHED", declared_ride),
                request("DRIVER_ACCEPTED", "IN_PROGRESS", declared_ride),
            ),
        )


def test_execution_rejects_mismatched_ride_hash():
    with pytest.raises(RideExecutionViolation):
        execute_transition(
            ride(),
            TransitionRequest(
                ride_hash="not-the-ride-hash",
                current_state="REQUESTED",
                target_state="MATCHED",
            ),
            sequence=0,
        )
