# ecosystems/afriride/tests/test_retry_idempotence.py

from ecosystems.afriride.runtime.commands import AssignDriver
from ecosystems.afriride.runtime.execution.deterministic_executor import (
    DeterministicExecutor,
)
from ecosystems.afriride.runtime.state import RideState


def test_duplicate_assign_driver_behavior():
    """
    This test asserts idempotent behavior under duplicate
    admissible mutation attempts.

    Two identical ASSIGN commands are submitted.
    Only the first is admissible; the second must be
    deterministically refused.

    Guarantees:
    - deterministic canonical ordering
    - single successful mutation
    - stable replay trace
    """

    # -----------------------------------------------------
    # Canonical initial state
    # -----------------------------------------------------
    state = RideState(
        drivers_available=frozenset({"A"}),
        ride_status="OPEN",
        assigned_driver=None,
        ride_a_assigned=None,
        ride_b_assigned=None,
    )

    # -----------------------------------------------------
    # Duplicate mutation commands
    # -----------------------------------------------------
    commands = [
        AssignDriver("A", epoch=6),
        AssignDriver("A", epoch=6),
    ]

    # -----------------------------------------------------
    # Execute deterministically
    # -----------------------------------------------------
    trace = DeterministicExecutor.execute(
        state=state,
        commands=commands,
        epoch=6,
    )

    # -----------------------------------------------------
    # Expected canonical replay trace
    # -----------------------------------------------------
    expected_trace = [
        {"type": "EXECUTION_CONTEXT", "epoch": 6},
        {"type": "AssignDriver", "driver": "A"},
        {
            "type": "REFUSAL",
            "command": "AssignDriver",
            "driver": "A",
        },
    ]

    assert trace == expected_trace

    # -----------------------------------------------------
    # Replay identity must be stable
    # -----------------------------------------------------
    hash_1 = DeterministicExecutor.trace_hash(trace)
    hash_2 = DeterministicExecutor.trace_hash(trace)

    assert hash_1 == hash_2