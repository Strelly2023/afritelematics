# ecosystems/afriride/runtime/commands.py

from dataclasses import dataclass
from typing import Final

__all__: Final = [
    # Core mutation (single-ride)
    "AssignDriver",

    # Independent mutation targets
    "AssignDriverToRideA",
    "AssignDriverToRideB",

    # Observational / auxiliary
    "ReadRideState",
    "EmitAuditEvent",
]


# ---------------------------------------------------------
# Mutation commands (replay-defining)
# ---------------------------------------------------------

@dataclass(frozen=True)
class AssignDriver:
    """
    Mutation command.

    Requests assignment of a specific driver to the ride.

    This command:
    - mutates canonical state
    - participates in replay-defining trace identity
    - is subject to deterministic admission and ordering
    """
    driver_id: str


@dataclass(frozen=True)
class AssignDriverToRideA:
    """
    Independent mutation command.

    Assigns a driver to Ride A.

    This command:
    - mutates an independent canonical domain
    - participates in replay-defining trace identity
    - must compose deterministically with other mutations
    """
    driver_id: str


@dataclass(frozen=True)
class AssignDriverToRideB:
    """
    Independent mutation command.

    Assigns a driver to Ride B.

    This command:
    - mutates an independent canonical domain
    - participates in replay-defining trace identity
    - must compose deterministically with other mutations
    """
    driver_id: str


# ---------------------------------------------------------
# Observational / auxiliary commands (non-replay-defining)
# ---------------------------------------------------------

@dataclass(frozen=True)
class ReadRideState:
    """
    Observational command.

    Requests a snapshot read of the current ride state.

    This command:
    - must never mutate canonical state
    - must never affect replay-defining trace identity
    - is explicitly excluded from legitimacy hashing
    """
    request_id: str


@dataclass(frozen=True)
class EmitAuditEvent:
    """
    Auxiliary emission command.

    Represents an audit or logging side-effect.

    This command:
    - is allowed to occur during execution
    - must not influence replay identity
    - must not introduce ordering ambiguity
    - is excluded from canonical trace hashing
    """
    event_id: str