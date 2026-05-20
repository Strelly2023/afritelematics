from typing import Any, Dict, Iterable, List, Tuple

from ecosystems.afriride.runtime.commands import (
    AssignDriver,
    AssignDriverToRideA,
    AssignDriverToRideB,
    ReadRideState,
    EmitAuditEvent,
)
from ecosystems.afriride.runtime.state import RideState
from ecosystems.afriride.runtime.mutation import apply_mutation
from afritech.core.runtime.executor import DeterministicCommandExecutor

# ---------------------------------------------------------------------
# CONSTITUTIONAL INVARIANT DECLARATION (VISIBLE TO VERIFIER)
# ---------------------------------------------------------------------

from afritech.constitution.compiled.invariants_index import (
    I4_DETERMINISTIC_RUNTIME,
    I5_EPOCH_MONOTONIC,
    I6_CLOSED_EXECUTION_WORLD,
)

ENFORCED_INVARIANTS = {
    I4_DETERMINISTIC_RUNTIME,
    I5_EPOCH_MONOTONIC,
    I6_CLOSED_EXECUTION_WORLD,
}

__all__ = ["DeterministicExecutor"]


class DeterministicExecutor:
    """
    Deterministic execution kernel for AfriRide.

    PUBLIC CONTRACT:
      - execute(...) -> replay trace ONLY
      - execute_with_state(...) -> (trace, final_state)

    This class:
    - enforces closed-world execution
    - enforces epoch monotonicity
    - guarantees deterministic ordering
    - produces replay-stable traces
    """

    # -----------------------------------------------------------------
    # CLOSED COMMAND UNIVERSE
    # -----------------------------------------------------------------

    ALLOWED_COMMANDS = (
        AssignDriver,
        AssignDriverToRideA,
        AssignDriverToRideB,
        ReadRideState,
        EmitAuditEvent,
    )

    # -----------------------------------------------------------------
    # CANONICAL ORDERING
    # -----------------------------------------------------------------

    @staticmethod
    def canonical_key(command: Any) -> Tuple[str, str]:
        if isinstance(command, AssignDriver):
            return ("ASSIGN", command.driver_id)
        if isinstance(command, AssignDriverToRideA):
            return ("ASSIGN_A", command.driver_id)
        if isinstance(command, AssignDriverToRideB):
            return ("ASSIGN_B", command.driver_id)
        if isinstance(command, ReadRideState):
            return ("READ", command.request_id)
        if isinstance(command, EmitAuditEvent):
            return ("AUDIT", command.event_id)
        raise AssertionError("NON-ADMISSIBLE COMMAND")

    @classmethod
    def canonicalize(cls, commands: Iterable[Any]) -> List[Any]:
        return sorted(commands, key=cls.canonical_key)

    # -----------------------------------------------------------------
    # ADMISSIBILITY
    # -----------------------------------------------------------------

    @staticmethod
    def admissible(state: RideState, command: Any) -> bool:
        if isinstance(command, AssignDriver):
            return (
                state.ride_status == "OPEN"
                and command.driver_id in state.drivers_available
                and state.assigned_driver is None
            )

        if isinstance(command, AssignDriverToRideA):
            return (
                command.driver_id in state.drivers_available
                and state.ride_a_assigned is None
            )

        if isinstance(command, AssignDriverToRideB):
            return (
                command.driver_id in state.drivers_available
                and state.ride_b_assigned is None
            )

        # Observational commands are always admissible
        return True

    # -----------------------------------------------------------------
    # INTERNAL EXECUTION (ONLY PLACE STATE CHANGES)
    # -----------------------------------------------------------------

    @classmethod
    def _execute_internal(
        cls,
        state: RideState,
        commands: Iterable[Any],
        epoch: int,
    ) -> Tuple[List[Dict[str, Any]], RideState]:
        return DeterministicCommandExecutor.execute_with_state(
            state=state,
            commands=commands,
            epoch=epoch,
            allowed_commands=cls.ALLOWED_COMMANDS,
            canonical_key=cls.canonical_key,
            admissible=cls.admissible,
            apply_mutation=apply_mutation,
            refusal_driver=lambda command: getattr(command, "driver_id", None),
            observational_commands=(ReadRideState, EmitAuditEvent),
        )

    # -----------------------------------------------------------------
    # PUBLIC API (TESTS DEPEND ON THIS)
    # -----------------------------------------------------------------

    @classmethod
    def execute(
        cls,
        state: RideState,
        commands: Iterable[Any],
        epoch: int,
    ) -> List[Dict[str, Any]]:
        """
        Execute commands and return replay-defining trace only.
        """
        trace, _ = cls._execute_internal(state, commands, epoch)
        return trace

    @classmethod
    def execute_with_state(
        cls,
        state: RideState,
        commands: Iterable[Any],
        epoch: int,
    ) -> Tuple[List[Dict[str, Any]], RideState]:
        """
        Execute commands and return (trace, final_state).
        """
        return cls._execute_internal(state, commands, epoch)

    # -----------------------------------------------------------------
    # REPLAY IDENTITY
    # -----------------------------------------------------------------

    @staticmethod
    def trace_hash(trace: List[Dict[str, Any]]) -> str:
        return DeterministicCommandExecutor.trace_hash(trace)
