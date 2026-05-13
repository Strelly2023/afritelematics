# ecosystems/afriride/runtime/deterministic_executor.py

import hashlib
import json
from typing import Any, Dict, Iterable, List

from ecosystems.afriride.runtime.commands import (
    AssignDriver,
    AssignDriverToRideA,
    AssignDriverToRideB,
    ReadRideState,
    EmitAuditEvent,
)
from ecosystems.afriride.runtime.state import RideState

__all__ = [
    "DeterministicExecutor",
]


class DeterministicExecutor:
    """
    Deterministic executor for replay‑first execution.

    Core properties enforced here:
    - Canonicalization occurs BEFORE any mutation.
    - Mutation legitimacy is serialized deterministically.
    - Independent mutations compose deterministically.
    - Observational and auxiliary commands are excluded
      from replay‑defining trace identity.
    """

    # ---------------------------------------------------------
    # Canonicalization
    # ---------------------------------------------------------

    @staticmethod
    def canonical_key(command: Any) -> tuple:
        """
        Produce a deterministic ordering key for any command.

        This ordering defines mutation eligibility and trace order,
        not submission or scheduler order.
        """

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

        return ("UNKNOWN", "")

    @classmethod
    def canonicalize(cls, commands: Iterable[Any]) -> List[Any]:
        """
        Deterministically order all submitted commands
        before admissibility checks or mutation.
        """
        return sorted(commands, key=cls.canonical_key)

    # ---------------------------------------------------------
    # Admission
    # ---------------------------------------------------------

    @staticmethod
    def admissible(state: RideState, command: Any) -> bool:
        """
        Determine whether a command is admissible
        given the current canonical state.
        """

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

        # Observational and auxiliary commands are always admissible,
        # but excluded from replay‑defining trace identity.
        return True

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    @classmethod
    def execute(
        cls,
        state: RideState,
        commands: Iterable[Any],
    ) -> List[Dict[str, Any]]:
        """
        Execute a batch of commands deterministically.

        Rules:
        - Commands are canonicalized before execution.
        - Only mutation commands contribute to the replay trace.
        - Observational and auxiliary commands are ignored
          for replay legitimacy.
        """

        trace: List[Dict[str, Any]] = []

        ordered = cls.canonicalize(commands)

        for command in ordered:

            # ---------------------------------------------
            # Observation / auxiliary (excluded from replay)
            # ---------------------------------------------
            if isinstance(command, (ReadRideState, EmitAuditEvent)):
                continue

            admissible = cls.admissible(state, command)

            # ---------------------------------------------
            # Single‑ride mutation
            # ---------------------------------------------
            if isinstance(command, AssignDriver):

                trace.append({
                    "type": "ASSIGN_DRIVER",
                    "driver": command.driver_id,
                    "admissible": admissible,
                })

                if not admissible:
                    trace.append({
                        "type": "REFUSAL",
                        "driver": command.driver_id,
                    })
                    continue

                state.assigned_driver = command.driver_id
                state.drivers_available.remove(command.driver_id)

                trace.append({
                    "type": "MUTATION",
                    "assigned_driver": command.driver_id,
                })

            # ---------------------------------------------
            # Independent mutation: Ride A
            # ---------------------------------------------
            elif isinstance(command, AssignDriverToRideA):

                trace.append({
                    "type": "ASSIGN_A",
                    "driver": command.driver_id,
                    "admissible": admissible,
                })

                if not admissible:
                    trace.append({"type": "REFUSAL_A"})
                    continue

                state.ride_a_assigned = command.driver_id
                state.drivers_available.remove(command.driver_id)

                trace.append({"type": "MUTATION_A"})

            # ---------------------------------------------
            # Independent mutation: Ride B
            # ---------------------------------------------
            elif isinstance(command, AssignDriverToRideB):

                trace.append({
                    "type": "ASSIGN_B",
                    "driver": command.driver_id,
                    "admissible": admissible,
                })

                if not admissible:
                    trace.append({"type": "REFUSAL_B"})
                    continue

                state.ride_b_assigned = command.driver_id
                state.drivers_available.remove(command.driver_id)

                trace.append({"type": "MUTATION_B"})

        return trace

    # ---------------------------------------------------------
    # Replay Identity
    # ---------------------------------------------------------

    @staticmethod
    def trace_hash(trace: List[Dict[str, Any]]) -> str:
        """
        Compute a replay‑stable hash of the canonical trace.

        Only replay‑defining trace elements are included.
        """
        payload = json.dumps(trace, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()