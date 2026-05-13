# ecosystems/afriride/core/constitutional/ride_authorities.py

"""
AFRIRIDE AUTHORITIES

Defines WHO is allowed to issue WHICH commands
within the AfriRide domain.

IMPORTANT:
- No execution
- No business logic validation
- Pure authority boundary enforcement

Execution authority resides exclusively in:
    afritech/runtime/main.py

This module is:
- deterministic
- side-effect free
- replay-safe
"""

from dataclasses import dataclass
from typing import List, Dict, Any

# ✅ Domain-owned role definition (NO enum defined here)
from ecosystems.afriride.core.domain.ride_roles import RideAuthorityRole

# ✅ Typed execution context
from ecosystems.afriride.core.domain.ride_context import AfriRideExecutionContext


# =========================================================
# ✅ COMMAND → AUTHORITY MAPPING
# =========================================================

COMMAND_AUTHORITY_MAP: Dict[str, List[RideAuthorityRole]] = {
    "RequestRide": [RideAuthorityRole.RIDER],
    "CancelTrip": [RideAuthorityRole.RIDER, RideAuthorityRole.DRIVER],
    "AcceptDriver": [RideAuthorityRole.DRIVER],
    "StartTrip": [RideAuthorityRole.DRIVER],
    "CompleteTrip": [RideAuthorityRole.DRIVER],

    # System-level orchestration
    "AssignDriver": [RideAuthorityRole.DISPATCHER],
    "DispatchAssignDriver": [
        RideAuthorityRole.SYSTEM,
        RideAuthorityRole.DISPATCHER
    ],
}


# =========================================================
# ✅ AUTHORITY DECISION
# =========================================================

@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    reason: str

    @staticmethod
    def allow(reason: str = "authorized") -> "AuthorityDecision":
        return AuthorityDecision(True, reason)

    @staticmethod
    def deny(reason: str) -> "AuthorityDecision":
        return AuthorityDecision(False, reason)


# =========================================================
# ✅ AUTHORITY CHECKER
# =========================================================

class RideAuthorityChecker:
    """
    Evaluates whether an actor is allowed to execute a command.

    Guarantees:
    - deterministic decision
    - replay-safe
    - strict boundary enforcement
    """

    @staticmethod
    def check(command: Any, context: Any) -> AuthorityDecision:

        # -------------------------------------------------
        # ✅ 1. CONTEXT TYPE ENFORCEMENT
        # -------------------------------------------------
        if not isinstance(context, AfriRideExecutionContext):
            return AuthorityDecision.deny(
                "Invalid context type: AfriRideExecutionContext required"
            )

        # -------------------------------------------------
        # ✅ 2. COMMAND VALIDATION
        # -------------------------------------------------
        if command is None:
            return AuthorityDecision.deny("Command cannot be None")

        command_name = command.__class__.__name__

        if not command_name:
            return AuthorityDecision.deny("Invalid command type")

        allowed_roles = COMMAND_AUTHORITY_MAP.get(command_name)

        # -------------------------------------------------
        # ✅ 3. UNKNOWN COMMAND
        # -------------------------------------------------
        if allowed_roles is None:
            return AuthorityDecision.deny(
                f"Command '{command_name}' not registered"
            )

        # -------------------------------------------------
        # ✅ 4. ROLE VALIDATION
        # -------------------------------------------------
        role = context.role

        if not isinstance(role, RideAuthorityRole):
            return AuthorityDecision.deny(
                "Invalid role type in execution context"
            )

        if role not in allowed_roles:
            return AuthorityDecision.deny(
                f"Role '{role.value}' is not allowed to execute '{command_name}'"
            )

        # -------------------------------------------------
        # ✅ 5. AUTHORIZE
        # -------------------------------------------------
        return AuthorityDecision.allow(
            reason=f"{role.value} authorized for {command_name}"
        )
