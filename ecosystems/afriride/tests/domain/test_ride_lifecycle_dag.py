import pytest

from ecosystems.afriride.domain.state.ride_lifecycle_dag import (
    CANONICAL_RIDE_LIFECYCLE_ORDER,
    RideLifecycleState,
    RideLifecycleViolation,
    as_canonical_dict,
    assert_transition,
    can_transition,
    canonical_edges,
    canonical_json,
    dag_hash,
    next_states,
    validate_lifecycle_dag,
)


def test_lifecycle_dag_declares_canonical_order():
    assert CANONICAL_RIDE_LIFECYCLE_ORDER == (
        RideLifecycleState.REQUESTED,
        RideLifecycleState.MATCHED,
        RideLifecycleState.DRIVER_ACCEPTED,
        RideLifecycleState.IN_PROGRESS,
        RideLifecycleState.COMPLETED,
    )


def test_lifecycle_dag_declares_only_forward_edges():
    assert canonical_edges() == (
        (RideLifecycleState.REQUESTED, RideLifecycleState.MATCHED),
        (RideLifecycleState.MATCHED, RideLifecycleState.DRIVER_ACCEPTED),
        (RideLifecycleState.DRIVER_ACCEPTED, RideLifecycleState.IN_PROGRESS),
        (RideLifecycleState.IN_PROGRESS, RideLifecycleState.COMPLETED),
    )
    assert validate_lifecycle_dag() is True


def test_lifecycle_dag_allows_only_declared_transitions():
    assert can_transition("REQUESTED", "MATCHED") is True
    assert can_transition("MATCHED", "DRIVER_ACCEPTED") is True
    assert can_transition("DRIVER_ACCEPTED", "IN_PROGRESS") is True
    assert can_transition("IN_PROGRESS", "COMPLETED") is True

    assert can_transition("REQUESTED", "DRIVER_ACCEPTED") is False
    assert can_transition("MATCHED", "COMPLETED") is False
    assert can_transition("COMPLETED", "REQUESTED") is False


def test_lifecycle_dag_rejects_hidden_or_unknown_transitions():
    with pytest.raises(RideLifecycleViolation):
        assert_transition("REQUESTED", "IN_PROGRESS")

    with pytest.raises(RideLifecycleViolation):
        assert_transition("DISPATCHED", "MATCHED")


def test_lifecycle_dag_returns_normalized_target_state():
    assert (
        assert_transition(
            RideLifecycleState.MATCHED,
            "DRIVER_ACCEPTED",
        )
        == RideLifecycleState.DRIVER_ACCEPTED
    )


def test_lifecycle_dag_exposes_terminal_state_without_successor():
    assert next_states(RideLifecycleState.COMPLETED) == ()


def test_lifecycle_dag_canonical_representation_is_stable():
    first_json = canonical_json()
    second_json = canonical_json()

    assert first_json == second_json
    assert dag_hash() == dag_hash()
    assert as_canonical_dict() == {
        "edges": [
            {"from": "REQUESTED", "to": "MATCHED"},
            {"from": "MATCHED", "to": "DRIVER_ACCEPTED"},
            {"from": "DRIVER_ACCEPTED", "to": "IN_PROGRESS"},
            {"from": "IN_PROGRESS", "to": "COMPLETED"},
        ],
        "states": [
            "REQUESTED",
            "MATCHED",
            "DRIVER_ACCEPTED",
            "IN_PROGRESS",
            "COMPLETED",
        ],
    }
