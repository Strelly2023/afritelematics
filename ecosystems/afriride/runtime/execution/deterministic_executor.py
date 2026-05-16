import hashlib
import json
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
    """

    ALLOWED_COMMANDS = (
        AssignDriver,
        AssignDriverToRideA,
        AssignDriverToRideB,
        ReadRideState,
        EmitAuditEvent,
    )

    # ---------------------------------------------------------
    # Canonicalization
    # ---------------------------------------------------------

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
        raise AssertionError("NON‑ADMISSIBLE COMMAND")

    @classmethod
    def canonicalize(cls, commands: Iterable[Any]) -> List[Any]:
        return sorted(commands, key=cls.canonical_key)

    # ---------------------------------------------------------
    # Admissibility
    # ---------------------------------------------------------

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
        return True

    # ---------------------------------------------------------
    # Internal execution (ONLY place state changes)
    # ---------------------------------------------------------

    @classmethod
    def _execute_internal(
        cls,
        state: RideState,
        commands: Iterable[Any],
        epoch: int,
    ) -> Tuple[List[Dict[str, Any]], RideState]:

        for cmd in commands:
            if not isinstance(cmd, cls.ALLOWED_COMMANDS):
                raise AssertionError("NON‑ADMISSIBLE COMMAND")
            if hasattr(cmd, "epoch") and cmd.epoch is not None:
                if cmd.epoch > epoch:
                    raise AssertionError("FUTURE‑EPOCH COMMAND")

        trace: List[Dict[str, Any]] = [
            {"type": "EXECUTION_CONTEXT", "epoch": epoch}
        ]

        current_state = state

        for command in cls.canonicalize(commands):
            if isinstance(command, (ReadRideState, EmitAuditEvent)):
                continue

            if not cls.admissible(current_state, command):
                trace.append({
                    "type": "REFUSAL",
                    "command": command.__class__.__name__,
                    "driver": getattr(command, "driver_id", None),
                })
                continue

            current_state = apply_mutation(current_state, command)

            trace.append({
                "type": command.__class__.__name__,
                "driver": getattr(command, "driver_id", None),
            })

        return trace, current_state

    # ---------------------------------------------------------
    # PUBLIC API (tests depend on this)
    # ---------------------------------------------------------

    @classmethod
    def execute(
        cls,
        state: RideState,
        commands: Iterable[Any],
        epoch: int,
    ) -> List[Dict[str, Any]]:
        trace, _ = cls._execute_internal(state, commands, epoch)
        return trace

    @classmethod
    def execute_with_state(
        cls,
        state: RideState,
        commands: Iterable[Any],
        epoch: int,
    ) -> Tuple[List[Dict[str, Any]], RideState]:
        return cls._execute_internal(state, commands, epoch)

    # ---------------------------------------------------------
    # Replay identity
    # ---------------------------------------------------------

    @staticmethod
    def trace_hash(trace: List[Dict[str, Any]]) -> str:
        payload = json.dumps(trace, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()