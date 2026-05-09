# afritech/guards/guard_core.py

"""
AfriTech Guard Core (Aligned with Constitutional Engine)

Purpose:
Bridge runtime guard system with constitutional engine (engine.py)

Key Constraints:
- MUST NOT modify engine.py
- MUST respect ConstitutionalViolation (SystemExit)
- MUST preserve ViolationClass taxonomy
- MUST integrate with higher-level GuardEngine

This file is the COMPATIBILITY LAYER.
"""

from typing import Dict, Any, Optional

# Import constitutional failure system (IMMUTABLE)
from afritech.guards.engine import (
    fail,
    ViolationClass,
    ConstitutionalViolation,
)


# -----------------------------------------------------------------
# COMPATIBILITY ERROR (OPTIONAL WRAPPER)
# -----------------------------------------------------------------

class GuardError(Exception):
    """
    Optional wrapper for higher-level systems that do NOT want SystemExit.

    NOTE:
    - engine.py still raises SystemExit
    - this is ONLY for optional interception (if needed)
    """

    def __init__(
        self,
        guard_id: str,
        message: str,
        violation_class: ViolationClass = ViolationClass.A_FATAL,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.guard_id = guard_id
        self.message = message
        self.violation_class = violation_class
        self.context = context or {}

        super().__init__(
            f"[{guard_id}] [{violation_class.name}] {message}"
        )


# -----------------------------------------------------------------
# OPTIONAL RESULT STRUCTURE
# -----------------------------------------------------------------

class GuardResult:
    """
    Optional structured result

    NOTE:
    Not used by engine.py (fail-fast),
    but useful for soft pipelines or analysis tools.
    """

    def __init__(self, ok: bool, reason: str = ""):
        self.ok = ok
        self.reason = reason

    def __bool__(self):
        return self.ok


# -----------------------------------------------------------------
# BASE GUARD
# -----------------------------------------------------------------

class Guard:
    """
    Base Guard class (aligned with constitutional engine)

    Contract:
    - MUST call self.fail() on violation
    - MUST NOT suppress failure
    """

    def __init__(
        self,
        guard_id: str,
        guard_type: str,
        rule: str,
        violation_class: ViolationClass = ViolationClass.A_FATAL,
    ):
        self.guard_id = guard_id
        self.guard_type = guard_type
        self.rule = rule
        self.violation_class = violation_class

    # -------------------------------------------------------------
    # ENFORCEMENT CONTRACT
    # -------------------------------------------------------------

    def enforce(self, context: Dict[str, Any]) -> bool:
        """
        Must either:
        - return True
        - OR call self.fail()

        NEVER silently return False.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.enforce not implemented"
        )

    # -------------------------------------------------------------
    # FAILURE (CRITICAL — delegates to engine.py)
    # -------------------------------------------------------------

    def fail(
        self,
        reason: str,
        violation_class: Optional[ViolationClass] = None,
    ) -> None:
        """
        Delegate failure to constitutional engine

        IMPORTANT:
        This calls engine.fail() → raises SystemExit
        """

        fail(
            msg=f"{self.guard_id}: {reason}",
            violation_class=violation_class or self.violation_class,
        )

    # -------------------------------------------------------------
    # SAFE ENFORCE (OPTIONAL)
    # -------------------------------------------------------------

    def try_enforce(self, context: Dict[str, Any]) -> bool:
        """
        Safe enforcement wrapper

        Converts SystemExit into boolean
        """

        try:
            self.enforce(context)
            return True

        except ConstitutionalViolation:
            return False

    # -------------------------------------------------------------
    # METADATA
    # -------------------------------------------------------------

    def describe(self) -> Dict[str, str]:
        return {
            "guard_id": self.guard_id,
            "type": self.guard_type,
            "rule": self.rule,
            "default_violation_class": self.violation_class.name,
        }

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def __repr__(self):
        return (
            f"<Guard id={self.guard_id} "
            f"type={self.guard_type}>"
        )