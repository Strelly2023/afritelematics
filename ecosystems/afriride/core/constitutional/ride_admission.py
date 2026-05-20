# ecosystems/afriride/core/constitutional/ride_admission.py

"""
AFRIRIDE ADMISSION

This module determines whether a command is admissible
before it reaches execution.

It answers:
    "Should this command even be considered?"

It enforces:
- Authority validation (who is issuing the command)
- Structural validity (basic command legitimacy)
- Context validity (typed execution contract)

It does NOT:
- Apply business invariants (handled by guards)
- Execute logic (handled by runtime + handlers)

This layer is:
- deterministic
- replay-safe
- side-effect free
"""

from dataclasses import dataclass
from typing import Any

# ✅ Authority
from ecosystems.afriride.core.constitutional.ride_authorities import (
    RideAuthorityChecker,
    AuthorityDecision,
)

# ✅ Typed Context
from ecosystems.afriride.domain.ride_context import (
    AfriRideExecutionContext
)


# =========================================================
# ✅ ADMISSION DECISION
# =========================================================

@dataclass(frozen=True)
class AdmissionDecision:
    allowed: bool
    reason: str

    @staticmethod
    def allow(reason: str) -> "AdmissionDecision":
        return AdmissionDecision(True, reason)

    @staticmethod
    def deny(reason: str) -> "AdmissionDecision":
        return AdmissionDecision(False, reason)


# =========================================================
# ✅ ADMISSION CHECKER
# =========================================================

class RideAdmissionChecker:
    """
    Admission gate for AfriRide commands.

    Validates:
    - Context type correctness
    - Authority rights
    - Command structural sanity

    Guarantees:
    - deterministic evaluation
    - replay-safe behavior
    """

    @staticmethod
    def check(command: Any, context: Any) -> AdmissionDecision:
        # -------------------------------------------------
        # ✅ 1. CONTEXT TYPE VALIDATION
        # -------------------------------------------------
        if not isinstance(context, AfriRideExecutionContext):
            return AdmissionDecision.deny(
                "Invalid execution context: AfriRideExecutionContext required"
            )

        # -------------------------------------------------
        # ✅ 2. COMMAND VALIDATION
        # -------------------------------------------------
        if command is None:
            return AdmissionDecision.deny("Command cannot be None")

        command_name = command.__class__.__name__

        if not command_name:
            return AdmissionDecision.deny("Invalid command type")

        # -------------------------------------------------
        # ✅ 3. AUTHORITY VALIDATION
        # -------------------------------------------------
        authority_decision: AuthorityDecision = RideAuthorityChecker.check(
            command,
            context
        )

        if not authority_decision.allowed:
            return AdmissionDecision.deny(
                f"Authority denied: {authority_decision.reason}"
            )

        # -------------------------------------------------
        # ✅ 4. MINIMAL CONTEXT VALIDATION
        # -------------------------------------------------
        # Context is typed, so we only verify attributes exist

        # Drivers must exist (can be empty but must be defined)
        if context.drivers is None:
            return AdmissionDecision.deny(
                "Invalid context: drivers field is missing"
            )

        # State may be None (valid for creation)
        # No validation on content (guards handle invariants)

        # -------------------------------------------------
        # ✅ 5. ACCEPT
        # -------------------------------------------------
        return AdmissionDecision.allow(
            f"Admitted: {command_name}"
        )