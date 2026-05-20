# ecosystems/afriride/core/domain/ride_context.py

"""
AFRIRIDE DOMAIN CONTEXT

This module defines the execution context used across AfriRide.

IMPORTANT:
- This is a PURE domain object
- It MUST NOT depend on constitutional or runtime layers
- It contains only data, not logic

Responsibilities:
- Represent execution context (who, state, environment)
- Provide deterministic, immutable inputs to the system

Guarantees:
- Immutable (frozen dataclass)
- Deterministic structure
- Replay-safe representation
"""

from dataclasses import dataclass
from typing import List, Optional, Dict

# ✅ Domain-owned roles (NO circular dependency)
from ecosystems.afriride.domain.ride_roles import RideAuthorityRole


# =========================================================
# ✅ EXECUTION CONTEXT
# =========================================================

@dataclass(frozen=True)
class AfriRideExecutionContext:
    """
    Immutable execution context for AfriRide.

    This is the ONLY valid context type for:
    - authority evaluation
    - admission
    - guards
    - runtime execution

    Fields:
    - role: WHO is performing the action
    - drivers: available drivers (must be deterministic)
    - state: current ride state (optional for creation flows)

    Guarantees:
    - explicit authority (via role)
    - deterministic behavior (ordered inputs expected)
    - replay-safe and immutable
    """

    role: RideAuthorityRole
    drivers: List[Dict]
    state: Optional[Dict] = None

    # -----------------------------------------------------
    # ✅ OPTIONAL VALIDATION HOOK (SAFE)
    # -----------------------------------------------------

    def __post_init__(self):
        """
        Lightweight structural validation.
        Must remain deterministic and side-effect free.
        """

        # ✅ drivers must always be a list
        if not isinstance(self.drivers, list):
            raise TypeError("drivers must be a list")

        # ✅ enforce deterministic driver ordering (fail early)
        if self.drivers:
            driver_ids = [d.get("id") for d in self.drivers]
            if driver_ids != sorted(driver_ids):
                raise ValueError(
                    "drivers must be sorted by 'id' for deterministic execution"
                )

        # ✅ state must be None or dict
        if self.state is not None and not isinstance(self.state, dict):
            raise TypeError("state must be a dict or None")
