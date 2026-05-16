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


# ---------------------------------------------------------
# Canonical replay harness (single authority)
# ---------------------------------------------------------

def _run_replay(commands: Iterable[Any]) -> Dict[str, Any]:
    """
    Execute a single replay run with a fresh canonical initial state.

    Guarantees:
    - identical initial conditions
    - deterministic canonicalization
    - epoch‑bounded execution
    - replay‑stable trace and hash
    - final_state reflects Δ‑composed reality

    This is the *only* execution harness used by all replay tests.
    """

    # ✅ Canonical replay epoch (sealed horizon)
    epoch = 6

    # ✅ Canonical immutable initial state
    initial_state = RideState(
        drivers_available=frozenset({"A", "B"}),
        ride_status="OPEN",
        assigned_driver=None,
        ride_a_assigned=None,
        ride_b_assigned=None,
    )

    # ✅ Correct API usage
    trace, final_state = DeterministicExecutor.execute_with_state(
        state=initial_state,
        commands=commands,
        epoch=epoch,
    )

    return {
        "final_state": final_state.snapshot(),
        "trace": trace,
        "hash": DeterministicExecutor.trace_hash(trace),
    }


# ---------------------------------------------------------
# Concurrent admissible mutation (conflict)
# ---------------------------------------------------------

def run_replay() -> Dict[str, Any]:
    """
    Replay harness for concurrent admissible mutation.
    """

    commands = [
        AssignDriver("B", epoch=6),
        AssignDriver("A", epoch=6),
    ]

    return _run_replay(commands)


# ---------------------------------------------------------
# Observational replay isolation
# ---------------------------------------------------------

def run_replay_variant_a() -> Dict[str, Any]:
    """
    Variant A submission order.
    """

    commands = [
        ReadRideState("R1"),
        EmitAuditEvent("E1"),
        AssignDriver("A", epoch=6),
        AssignDriver("B", epoch=6),
    ]

    return _run_replay(commands)


def run_replay_variant_b() -> Dict[str, Any]:
    """
    Variant B submission order.
    """

    commands = [
        EmitAuditEvent("E1"),
        AssignDriver("B", epoch=6),
        ReadRideState("R1"),
        AssignDriver("A", epoch=6),
    ]

    return _run_replay(commands)


# ---------------------------------------------------------
# Independent mutation composition
# ---------------------------------------------------------

def run_independent_replay_variant_a() -> Dict[str, Any]:
    """
    Independent mutation variant A.
    """

    commands = [
        AssignDriverToRideA("A", epoch=6),
        AssignDriverToRideB("B", epoch=6),
    ]

    return _run_replay(commands)


def run_independent_replay_variant_b() -> Dict[str, Any]:
    """
    Independent mutation variant B.
    """

    commands = [
        AssignDriverToRideB("B", epoch=6),
        AssignDriverToRideA("A", epoch=6),
    ]

    return _run_replay(commands)
