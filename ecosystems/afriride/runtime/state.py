# ecosystems/afriride/runtime/state.py

from dataclasses import dataclass, field
from typing import Optional, Set, Dict, Any

__all__ = [
    "RideState",
]


@dataclass
class RideState:
    """
    Canonical mutable state for AfriRide execution.

    This state defines the *entire* replay‑defining mutable surface
    for all currently validated experiments:
    - concurrent mutation under conflict
    - observational replay isolation
    - independent mutation composition

    Design constraints (non‑negotiable):
    - no derived or transient fields
    - no observational or diagnostic metadata
    - no ordering‑dependent data structures
    """

    # Shared resource pool
    drivers_available: Set[str] = field(default_factory=set)

    # Single‑ride mutation (conflict experiments)
    ride_status: str = "OPEN"
    assigned_driver: Optional[str] = None

    # Independent mutation domains (composition experiments)
    ride_a_assigned: Optional[str] = None
    ride_b_assigned: Optional[str] = None

    def snapshot(self) -> Dict[str, Any]:
        """
        Produce a canonical, replay‑stable snapshot of state.

        Guarantees:
        - deterministic ordering of all collections
        - inclusion of only replay‑defining state
        - exclusion of observational or auxiliary data

        This snapshot defines *state identity* for replay purposes.
        """

        return {
            "drivers_available": sorted(self.drivers_available),
            "ride_status": self.ride_status,
            "assigned_driver": self.assigned_driver,
            "ride_a_assigned": self.ride_a_assigned,
            "ride_b_assigned": self.ride_b_assigned,
        }