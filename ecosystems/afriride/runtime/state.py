# ecosystems/afriride/runtime/state.py

from dataclasses import dataclass
from typing import Optional, FrozenSet, Dict, Any

__all__ = [
    "RideState",
]


@dataclass(frozen=True)
class RideState:
    """
    Canonical immutable state for AfriRide execution.

    This state defines the *entire* replay‑defining mutable surface
    for all validated experiments.

    NON‑NEGOTIABLE CONSTRAINTS:
    - immutable (no in‑place mutation)
    - no ordering‑dependent data structures
    - no derived, transient, or observational fields
    - equality and identity are structural
    """

    # ---------------------------------------------------------
    # Shared resource pool (order‑independent, deterministic)
    # ---------------------------------------------------------
    drivers_available: FrozenSet[str]

    # ---------------------------------------------------------
    # Single‑ride mutation domain
    # ---------------------------------------------------------
    ride_status: str = "OPEN"
    assigned_driver: Optional[str] = None

    # ---------------------------------------------------------
    # Independent mutation domains (composition‑safe)
    # ---------------------------------------------------------
    ride_a_assigned: Optional[str] = None
    ride_b_assigned: Optional[str] = None

    # ---------------------------------------------------------
    # Canonical Snapshot
    # ---------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """
        Produce a canonical, replay‑stable snapshot of state.

        Guarantees:
        - deterministic ordering of collections
        - observer‑free representation
        - includes only replay‑defining state

        This snapshot defines *state identity* for replay and hashing.
        """

        return {
            "drivers_available": sorted(self.drivers_available),
            "ride_status": self.ride_status,
            "assigned_driver": self.assigned_driver,
            "ride_a_assigned": self.ride_a_assigned,
            "ride_b_assigned": self.ride_b_assigned,
        }