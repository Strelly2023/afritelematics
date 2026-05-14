# ecosystems/afriride/runtime/replay.py

from typing import Dict, Any, Iterable

from ecosystems.afriride.runtime.commands import (
    AssignDriver,
    AssignDriverToRideA,
    AssignDriverToRideB,
    ReadRideState,
    EmitAuditEvent,
)
from ecosystems.afriride.runtime.execution.deterministic_executor import (
    DeterministicExecutor,
)
from ecosystems.afriride.runtime.state import RideState

__all__ = [
    "run_replay",
    "run_replay_variant_a",
    "run_replay_variant_b",
    "run_independent_replay_variant_a",
    "run_independent_replay_variant_b",
]


def _run_replay(commands: Iterable[Any]) -> Dict[str, Any]:
    """
    Execute a single replay run with a fresh canonical initial state.

    Guarantees:
    - identical initial conditions
    - deterministic canonicalization
    - replay‑stable trace and hash

    This is the *only* execution harness used by all replay tests.
    """

    state = RideState(
        drivers_available={"A", "B"},
        ride_status="OPEN",
    )

    trace = DeterministicExecutor.execute(state, commands)

    return {
        "final_state": state.snapshot(),
        "trace": trace,
        "hash": DeterministicExecutor.trace_hash(trace),
    }


# ---------------------------------------------------------
# Concurrent admissible mutation (conflict)
# ---------------------------------------------------------

def run_replay() -> Dict[str, Any]:
    """
    Replay harness for concurrent admissible mutation.

    Two conflicting ASSIGN commands are submitted without order.
    DeterministicExecutor must serialize mutation canonically.
    """

    commands = [
        AssignDriver("B"),
        AssignDriver("A"),
    ]

    return _run_replay(commands)


# ---------------------------------------------------------
# Observational replay isolation
# ---------------------------------------------------------

def run_replay_variant_a() -> Dict[str, Any]:
    """
    Variant A submission order:
    - Read
    - Audit emission
    - Competing mutations
    """

    commands = [
        ReadRideState("R1"),
        EmitAuditEvent("E1"),
        AssignDriver("A"),
        AssignDriver("B"),
    ]

    return _run_replay(commands)


def run_replay_variant_b() -> Dict[str, Any]:
    """
    Variant B submission order:
    - Audit emission
    - Mutation
    - Read
    - Competing mutation

    Replay identity must match Variant A.
    """

    commands = [
        EmitAuditEvent("E1"),
        AssignDriver("B"),
        ReadRideState("R1"),
        AssignDriver("A"),
    ]

    return _run_replay(commands)


# ---------------------------------------------------------
# Independent mutation composition
# ---------------------------------------------------------

def run_independent_replay_variant_a() -> Dict[str, Any]:
    """
    Independent mutation variant A.

    Two non‑conflicting mutations submitted in order A → B.
    """

    commands = [
        AssignDriverToRideA("A"),
        AssignDriverToRideB("B"),
    ]

    return _run_replay(commands)


def run_independent_replay_variant_b() -> Dict[str, Any]:
    """
    Independent mutation variant B.

    Same mutations as variant A, submitted in reverse order.
    Replay identity must remain canonical.
    """

    commands = [
        AssignDriverToRideB("B"),
        AssignDriverToRideA("A"),
    ]

    return _run_replay(commands)