# ecosystems/afriride/core/constitutional/ride_guards.py

"""
AFRIRIDE GUARDS

This module enforces domain invariants AFTER admission
and BEFORE execution.

It answers:
    "Is this command valid given the current state?"

Responsibilities:
- Enforce business invariants
- Enforce determinism constraints
- Ensure safe state transitions

It does NOT:
- Execute domain logic
- Perform I/O
- Mutate state

This layer MUST remain:
- deterministic
- side-effect free
- replay-safe
"""

from dataclasses import dataclass
from typing import Any, List

# ✅ Typed Context
from ecosystems.afriride.core.domain.ride_context import (
    AfriRideExecutionContext
)

# ✅ Authority
from ecosystems.afriride.core.constitutional.ride_authorities import (
    RideAuthorityChecker
)


# =========================================================
# ✅ GUARD DECISION
# =========================================================

@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    reason: str


# =========================================================
# ✅ BASE GUARD
# =========================================================

class BaseGuard:
    def check(self, command: Any, context: AfriRideExecutionContext) -> GuardDecision:
        raise NotImplementedError


# =========================================================
# ✅ AUTHORITY GUARD (REINFORCEMENT)
# =========================================================

class AuthorityGuard(BaseGuard):
    """
    Re-validates authority at guard stage.
    Ensures no bypass of admission layer.
    """

    def check(self, command, context: AfriRideExecutionContext):
        decision = RideAuthorityChecker.check(command, context)

        return GuardDecision(
            allowed=decision.allowed,
            reason=decision.reason
        )


# =========================================================
# ✅ STATE PRESENCE GUARD
# =========================================================

class StatePresenceGuard(BaseGuard):
    """
    Ensures state consistency structure exists.
    """

    def check(self, command, context: AfriRideExecutionContext):
        # state may be None (creation case)
        if context.state is None:
            return GuardDecision(True, "No state (creation allowed)")

        if not isinstance(context.state, dict):
            return GuardDecision(False, "State must be a dictionary")

        return GuardDecision(True, "State valid")


# =========================================================
# ✅ RIDE STATE TRANSITION GUARD
# =========================================================

class RideStateGuard(BaseGuard):
    """
    Enforces valid ride lifecycle transitions.
    """

    COMMAND_STATE_MAP = {
        "AssignDriver": ("REQUESTED", "ASSIGNED"),
        "StartTrip": ("ASSIGNED", "STARTED"),
        "CompleteTrip": ("STARTED", "COMPLETED"),
        "CancelTrip": ("REQUESTED", "CANCELLED"),
    }

    def check(self, command, context: AfriRideExecutionContext):
        state = context.state

        if not state:
            return GuardDecision(True, "No state yet (allowed for creation)")

        current_state = state.get("status")
        command_name = command.__class__.__name__

        if command_name not in self.COMMAND_STATE_MAP:
            return GuardDecision(True, "No state transition required")

        expected_from, expected_to = self.COMMAND_STATE_MAP[command_name]

        if current_state != expected_from:
            return GuardDecision(
                False,
                f"Invalid transition: {current_state} → {expected_to}"
            )

        return GuardDecision(
            True,
            f"Valid transition {expected_from} → {expected_to}"
        )


# =========================================================
# ✅ DRIVER AVAILABILITY GUARD
# =========================================================

class DriverAvailabilityGuard(BaseGuard):
    """
    Ensures selected driver is available.
    """

    def check(self, command, context: AfriRideExecutionContext):
        command_name = command.__class__.__name__

        if command_name not in ["AcceptDriver", "StartTrip"]:
            return GuardDecision(True, "Not applicable")

        # deterministic assumption: first driver is selected
        drivers = context.drivers

        if not drivers:
            return GuardDecision(False, "No drivers available")

        driver = drivers[0]

        if not driver.get("available", False):
            return GuardDecision(False, "Driver not available")

        return GuardDecision(True, "Driver available")


# =========================================================
# ✅ DETERMINISM GUARD
# =========================================================

class DeterminismGuard(BaseGuard):
    """
    Enforces determinism contract rules.
    """

    def check(self, command, context: AfriRideExecutionContext):
        drivers = context.drivers

        if drivers and isinstance(drivers, list):
            driver_ids = [d["id"] for d in drivers]

            if driver_ids != sorted(driver_ids):
                return GuardDecision(
                    False,
                    "Drivers must be sorted by id for deterministic execution"
                )

        return GuardDecision(True, "Deterministic context")


# =========================================================
# ✅ EVENT ORDER GUARD
# =========================================================

class EventOrderGuard(BaseGuard):
    """
    Ensures pending events (if present) are deterministic.
    """

    def check(self, command, context: AfriRideExecutionContext):
        # optional extension: attach events later in pipeline
        pending_events = getattr(context, "pending_events", None)

        if pending_events is None:
            return GuardDecision(True, "No pending events")

        if not isinstance(pending_events, list):
            return GuardDecision(False, "Events must be a list")

        event_strings = [str(e) for e in pending_events]

        if event_strings != sorted(event_strings):
            return GuardDecision(
                False,
                "Events must be deterministically ordered"
            )

        return GuardDecision(True, "Event order valid")


# =========================================================
# ✅ GUARD REGISTRY (ORDER IS CRITICAL)
# =========================================================

ALL_GUARDS: List[BaseGuard] = [
    AuthorityGuard(),          # ✅ identity + role
    StatePresenceGuard(),      # ✅ structural integrity
    RideStateGuard(),          # ✅ lifecycle correctness
    DriverAvailabilityGuard(), # ✅ operational validity
    DeterminismGuard(),        # ✅ replay safety
    EventOrderGuard(),         # ✅ proof stability
]