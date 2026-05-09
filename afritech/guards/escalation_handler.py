# afritech/guards/escalation_handler.py

"""
AfriTech Escalation Handler

Purpose:
Map classified incidents to deterministic system actions.

Guarantees:
- deterministic escalation decisions
- no undefined recovery behavior
- integration with guard + recovery system
"""

from typing import Dict, Any

from afritech.guards.engine import ViolationClass
from afritech.guards.incident_classifier import IncidentType


# -----------------------------------------------------------------
# ACTION TYPES
# -----------------------------------------------------------------

class EscalationAction:

    SYSTEM_HALT = "SYSTEM_HALT"
    ROLLBACK = "ROLLBACK"
    QUARANTINE = "QUARANTINE"
    REJECT = "REJECT"


# -----------------------------------------------------------------
# ESCALATION HANDLER
# -----------------------------------------------------------------

class EscalationHandler:

    def __init__(self):
        """
        Define deterministic escalation mapping.
        """

        self._mapping: Dict[str, str] = {

            # -----------------------------------------------------
            # CRITICAL FAILURES → HALT
            # -----------------------------------------------------

            IncidentType.CRITICAL_INVARIANT: EscalationAction.SYSTEM_HALT,
            IncidentType.AUTHORITY_BREACH: EscalationAction.SYSTEM_HALT,

            # -----------------------------------------------------
            # STATE / TRACE → RECOVERABLE
            # -----------------------------------------------------

            IncidentType.TRACE_CORRUPTION: EscalationAction.ROLLBACK,
            IncidentType.STATE_VIOLATION: EscalationAction.ROLLBACK,

            # -----------------------------------------------------
            # STRUCTURAL → BLOCK EXECUTION
            # -----------------------------------------------------

            IncidentType.SCHEMA_VIOLATION: EscalationAction.REJECT,
            IncidentType.STRUCTURAL_ERROR: EscalationAction.REJECT,

            # -----------------------------------------------------
            # TIME SYSTEM
            # -----------------------------------------------------

            IncidentType.EPOCH_VIOLATION: EscalationAction.REJECT,

            # -----------------------------------------------------
            # NON-CRITICAL
            # -----------------------------------------------------

            IncidentType.DOCUMENTATION_ERROR: EscalationAction.REJECT,

            # -----------------------------------------------------
            # UNKNOWN → safest default
            # -----------------------------------------------------

            IncidentType.UNKNOWN: EscalationAction.REJECT,
        }

    # -------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -------------------------------------------------------------

    def escalate(self, incident_type: str) -> str:
        """
        Return deterministic action for incident.

        Guarantees:
        - Always returns a valid action
        - No undefined escalation path
        """

        return self._mapping.get(
            incident_type,
            EscalationAction.REJECT,
        )

    # -------------------------------------------------------------
    # OPTIONAL: EXECUTE ESCALATION (FULL PIPELINE)
    # -------------------------------------------------------------

    def execute(
        self,
        incident_type: str,
        context: Dict[str, Any],
    ) -> None:
        """
        Execute escalation action directly.

        Integrates with:
        - HaltController
        - RollbackEngine
        - QuarantineManager
        """

        action = self.escalate(incident_type)

        # ---------------------------------------------------------
        # HALT
        # ---------------------------------------------------------

        if action == EscalationAction.SYSTEM_HALT:

            halt_controller = context.get("halt_controller")

            if halt_controller:
                halt_controller.halt(
                    reason=f"Escalation: {incident_type}",
                )

            # fallback (fail hard)
            from afritech.guards.engine import fail
            fail(f"Escalation HALT: {incident_type}", ViolationClass.A_FATAL)

        # ---------------------------------------------------------
        # ROLLBACK
        # ---------------------------------------------------------

        elif action == EscalationAction.ROLLBACK:

            from afritech.guards.rollback_engine import RollbackEngine

            engine = context.get("state_engine")

            if engine:
                RollbackEngine().execute(engine, mode="LAST")

            else:
                from afritech.guards.engine import fail
                fail("Rollback requested but no state_engine", ViolationClass.B_STRUCTURAL)

        # ---------------------------------------------------------
        # QUARANTINE
        # ---------------------------------------------------------

        elif action == EscalationAction.QUARANTINE:

            qm = context.get("quarantine_manager")
            entity = context.get("entity")

            if qm and entity:
                qm.quarantine(entity, reason=f"Escalation: {incident_type}")

            else:
                from afritech.guards.engine import fail
                fail("Quarantine failed: missing context", ViolationClass.B_STRUCTURAL)

        # ---------------------------------------------------------
        # REJECT
        # ---------------------------------------------------------

        elif action == EscalationAction.REJECT:

            from afritech.guards.engine import fail

            fail(
                msg=f"Execution rejected: {incident_type}",
                violation_class=ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # SAFETY NET
        # ---------------------------------------------------------

        else:
            from afritech.guards.engine import fail

            fail(
                msg=f"Unknown escalation action: {action}",
                violation_class=ViolationClass.B_STRUCTURAL,
            )

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def __repr__(self):
        return "<EscalationHandler deterministic>"