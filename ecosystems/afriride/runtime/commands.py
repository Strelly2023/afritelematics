# ecosystems/afriride/runtime/commands.py

from dataclasses import dataclass
from typing import Final, Optional

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
# Mutation commands (replay-defining, epoch-aware)
# ---------------------------------------------------------

@dataclass(frozen=True)
class AssignDriver:
    """
    Mutation command.

    Requests assignment of a specific driver to the ride.

    Properties:
    - replay-defining
    - epoch-bounded admissibility
    - deterministic ordering participant
    """
    driver_id: str
    epoch: Optional[int] = None


@dataclass(frozen=True)
class AssignDriverToRideA:
    """
    Independent mutation command.

    Assigns a driver to Ride A.

    Properties:
    - replay-defining
    - independent mutation domain
    - epoch-bounded admissibility
    """
    driver_id: str
    epoch: Optional[int] = None


@dataclass(frozen=True)
class AssignDriverToRideB:
    """
    Independent mutation command.

    Assigns a driver to Ride B.

    Properties:
    - replay-defining
    - independent mutation domain
    - epoch-bounded admissibility
    """
    driver_id: str
    epoch: Optional[int] = None


# ---------------------------------------------------------
# Observational / auxiliary commands (non-replay-defining)
# ---------------------------------------------------------

@dataclass(frozen=True)
class ReadRideState:
    """
    Observational command.

    Requests a snapshot read of the current ride state.

    Properties:
    - non-mutating
    - excluded from replay identity
    - NOT epoch-bound (observer only)
    """
    request_id: str


@dataclass(frozen=True)
class EmitAuditEvent:
    """
    Auxiliary emission command.

    Represents an audit or logging side-effect.

    Properties:
    - non-mutating
    - excluded from replay identity
    - NOT epoch-bound
    """
    event_id: str