# afritech/guards/halt_controller.py

"""
AfriTech Halt Controller

Purpose:
Provide deterministic system halt capability under constitutional violation.

Guarantees:
- fail-fast termination
- deterministic halt state
- no partial execution continuation
- replay-consistent outcomes

This module MUST align with engine.py (fail → ConstitutionalViolation).
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# HALT CONTROLLER
# -----------------------------------------------------------------

class HaltController:

    def __init__(self):
        self._halted: bool = False
        self._halt_reason: Optional[str] = None
        self._halt_metadata: Dict[str, Any] = {}

    # -------------------------------------------------------------
    # HALT (CRITICAL PATH)
    # -------------------------------------------------------------

    def halt(
        self,
        reason: str,
        violation_class: ViolationClass = ViolationClass.A_FATAL,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Trigger a system halt.

        This NEVER returns.
        """

        self._halted = True
        self._halt_reason = reason
        self._halt_metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "violation_class": violation_class.name,
            "context": context or {},
        }

        fail(
            msg=f"SYSTEM HALT: {reason}",
            violation_class=violation_class,
        )

    # -------------------------------------------------------------
    # STATE CHECK
    # -------------------------------------------------------------

    def is_halted(self) -> bool:
        return self._halted

    def get_reason(self) -> Optional[str]:
        return self._halt_reason

    def get_metadata(self) -> Dict[str, Any]:
        return self._halt_metadata

    # -------------------------------------------------------------
    # GUARD ENTRYPOINT (PRE-EXECUTION CHECK)
    # -------------------------------------------------------------

    def enforce_not_halted(self) -> None:
        """
        Ensure system is not already halted.

        Used at critical execution boundaries.
        """

        if self._halted:
            fail(
                msg=f"Execution attempted on halted system: {self._halt_reason}",
                violation_class=ViolationClass.A_FATAL,
            )

    # -------------------------------------------------------------
    # SAFE HALT WRAPPER (OPTIONAL)
    # -------------------------------------------------------------

    def try_halt(
        self,
        reason: str,
        violation_class: ViolationClass = ViolationClass.A_FATAL,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Safe wrapper for halt — returns False after halting attempt.

        NOTE:
        In real execution, fail() will terminate execution.
        This is only useful for controlled test environments.
        """

        try:
            self.halt(reason, violation_class, context)
        except SystemExit:
            return False

        return False  # unreachable, for consistency

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def __repr__(self):
        return (
            f"<HaltController halted={self._halted} "
            f"reason={self._halt_reason}>"
        )