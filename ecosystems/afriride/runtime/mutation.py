# ecosystems/afriride/runtime/mutation.py

"""
Deterministic mutation algebra for AfriRide.

This module defines Δ : U → U
(the explicit state transition operator).

NON‑NEGOTIABLE PROPERTIES:
- No in‑place mutation
- Referential transparency
- Deterministic behavior
- Replay‑auditable transitions
- Closed command universe
"""

from typing import Any

from ecosystems.afriride.runtime.state import RideState
from ecosystems.afriride.runtime.commands import (
    AssignDriver,
    AssignDriverToRideA,
    AssignDriverToRideB,
)

__all__ = [
    "apply_mutation",
]


def apply_mutation(state: RideState, command: Any) -> RideState:
    """
    Apply a single admissible mutation to state.

    This function is the *only* place where state transitions occur.

    Algebraic meaning:
        Δ(state, command) → new_state

    Preconditions (guaranteed by caller):
    - command ∈ admissible command universe
    - command is admissible under π(U)
    - state is immutable
    """

    # ---------------------------------------------------------
    # Single‑ride assignment (conflicting domain)
    # ---------------------------------------------------------
    if isinstance(command, AssignDriver):
        return RideState(
            drivers_available=state.drivers_available - {command.driver_id},
            ride_status=state.ride_status,
            assigned_driver=command.driver_id,
            ride_a_assigned=state.ride_a_assigned,
            ride_b_assigned=state.ride_b_assigned,
        )

    # ---------------------------------------------------------
    # Independent mutation: Ride A
    # ---------------------------------------------------------
    if isinstance(command, AssignDriverToRideA):
        return RideState(
            drivers_available=state.drivers_available - {command.driver_id},
            ride_status=state.ride_status,
            assigned_driver=state.assigned_driver,
            ride_a_assigned=command.driver_id,
            ride_b_assigned=state.ride_b_assigned,
        )

    # ---------------------------------------------------------
    # Independent mutation: Ride B
    # ---------------------------------------------------------
    if isinstance(command, AssignDriverToRideB):
        return RideState(
            drivers_available=state.drivers_available - {command.driver_id},
            ride_status=state.ride_status,
            assigned_driver=state.assigned_driver,
            ride_a_assigned=state.ride_a_assigned,
            ride_b_assigned=command.driver_id,
        )

    # ---------------------------------------------------------
    # Non‑mutating commands (observation / auxiliary)
    # ---------------------------------------------------------
    # Explicit identity: Δ(state, command) = state
    return state