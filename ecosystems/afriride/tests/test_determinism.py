# ecosystems/afriride/tests/test_determinism.py

import copy

from ecosystems.afriride.runtime.execution.deterministic_executor import (
    DeterministicExecutor,
)
from ecosystems.afriride.runtime.state import RideState
from ecosystems.afriride.runtime.commands import (
    AssignDriver,
    AssignDriverToRideA,
    AssignDriverToRideB,
    ReadRideState,
    EmitAuditEvent,
)


def make_initial_state() -> RideState:
    """
    Construct a canonical initial state.

    NOTE:
    - drivers_available is a FrozenSet
    - state is immutable
    """
    return RideState(
        drivers_available=frozenset({"driver-1", "driver-2", "driver-3"}),
        ride_status="OPEN",
        assigned_driver=None,
        ride_a_assigned=None,
        ride_b_assigned=None,
    )


def make_commands():
    """
    Return commands in deliberately non-deterministic order.
    Canonicalization must normalize this.
    """
    return [
        AssignDriverToRideB(driver_id="driver-2", epoch=6),
        ReadRideState(request_id="read-1"),
        AssignDriver(driver_id="driver-1", epoch=6),
        EmitAuditEvent(event_id="audit-1"),
        AssignDriverToRideA(driver_id="driver-3", epoch=6),
    ]


# ---------------------------------------------------------
# I4 — Deterministic Execution
# ---------------------------------------------------------

def test_execution_is_deterministic():
    """
    Same state + same commands ⇒ identical replay trace.
    """

    state_1 = make_initial_state()
    state_2 = make_initial_state()

    commands = make_commands()
    epoch = 6

    trace_1 = DeterministicExecutor.execute(
        state=state_1,
        commands=commands,
        epoch=epoch,
    )

    trace_2 = DeterministicExecutor.execute(
        state=state_2,
        commands=commands,
        epoch=epoch,
    )

    assert trace_1 == trace_2

    hash_1 = DeterministicExecutor.trace_hash(trace_1)
    hash_2 = DeterministicExecutor.trace_hash(trace_2)

    assert hash_1 == hash_2


# ---------------------------------------------------------
# Canonicalization Independence
# ---------------------------------------------------------

def test_execution_order_independence():
    """
    Different submission orders must converge
    to the same canonical execution.
    """

    state_a = make_initial_state()
    state_b = make_initial_state()

    commands = make_commands()
    reversed_commands = list(reversed(commands))

    epoch = 6

    trace_a = DeterministicExecutor.execute(
        state=state_a,
        commands=commands,
        epoch=epoch,
    )

    trace_b = DeterministicExecutor.execute(
        state=state_b,
        commands=reversed_commands,
        epoch=epoch,
    )

    assert trace_a == trace_b
    assert (
        DeterministicExecutor.trace_hash(trace_a)
        == DeterministicExecutor.trace_hash(trace_b)
    )


# ---------------------------------------------------------
# Independent Mutation Composition
# ---------------------------------------------------------

def test_independent_mutations_compose_deterministically():
    """
    Independent mutation domains (Ride A / Ride B)
    must compose deterministically regardless of ordering.
    """

    state_1 = make_initial_state()
    state_2 = make_initial_state()

    cmds_1 = [
        AssignDriverToRideA(driver_id="driver-1", epoch=6),
        AssignDriverToRideB(driver_id="driver-2", epoch=6),
    ]

    cmds_2 = [
        AssignDriverToRideB(driver_id="driver-2", epoch=6),
        AssignDriverToRideA(driver_id="driver-1", epoch=6),
    ]

    trace_1 = DeterministicExecutor.execute(
        state=state_1,
        commands=cmds_1,
        epoch=6,
    )

    trace_2 = DeterministicExecutor.execute(
        state=state_2,
        commands=cmds_2,
        epoch=6,
    )

    assert trace_1 == trace_2
    assert (
        DeterministicExecutor.trace_hash(trace_1)
        == DeterministicExecutor.trace_hash(trace_2)
    )


# ---------------------------------------------------------
# Replay Identity Stability
# ---------------------------------------------------------

def test_replay_identity_is_observer_free():
    """
    Observational commands must not affect replay identity.
    """

    state = make_initial_state()

    cmds_with_observation = [
        AssignDriver(driver_id="driver-1", epoch=6),
        ReadRideState(request_id="read-1"),
        EmitAuditEvent(event_id="audit-1"),
    ]

    cmds_without_observation = [
        AssignDriver(driver_id="driver-1", epoch=6),
    ]

    trace_obs = DeterministicExecutor.execute(
        state=state,
        commands=cmds_with_observation,
        epoch=6,
    )

    trace_pure = DeterministicExecutor.execute(
        state=state,
        commands=cmds_without_observation,
        epoch=6,
    )

    assert trace_obs == trace_pure
    assert (
        DeterministicExecutor.trace_hash(trace_obs)
        == DeterministicExecutor.trace_hash(trace_pure)
    )