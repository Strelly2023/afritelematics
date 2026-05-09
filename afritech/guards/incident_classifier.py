# afritech/guards/incident_classifier.py

"""
AfriTech Incident Classifier

Purpose:
Classify constitutional failures into standard incident categories.

Guarantees:
- deterministic classification
- stable mapping between failures and actions
- compatibility with escalation handler
- no ambiguity in incident classification
"""

from typing import Optional

from afritech.guards.engine import ViolationClass, ConstitutionalViolation


# -----------------------------------------------------------------
# INCIDENT TYPES (CANONICAL)
# -----------------------------------------------------------------

class IncidentType:

    CRITICAL_INVARIANT = "CRITICAL_INVARIANT"
    AUTHORITY_BREACH = "AUTHORITY_BREACH"
    TRACE_CORRUPTION = "TRACE_CORRUPTION"
    STATE_VIOLATION = "STATE_VIOLATION"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    EPOCH_VIOLATION = "EPOCH_VIOLATION"
    STRUCTURAL_ERROR = "STRUCTURAL_ERROR"
    DOCUMENTATION_ERROR = "DOCUMENTATION_ERROR"
    UNKNOWN = "UNKNOWN"


# -----------------------------------------------------------------
# CLASSIFIER
# -----------------------------------------------------------------

class IncidentClassifier:

    # -------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -------------------------------------------------------------

    def classify(self, error: Exception) -> str:
        """
        Classify exception into incident type.

        Supports:
        - ConstitutionalViolation (primary)
        - fallback string-based classification
        """

        if isinstance(error, ConstitutionalViolation):
            return self._classify_constitutional(error)

        # fallback classification
        return self._classify_from_message(str(error))

    # -------------------------------------------------------------
    # CONSTITUTIONAL CLASSIFICATION
    # -------------------------------------------------------------

    def _classify_constitutional(
        self,
        error: ConstitutionalViolation,
    ) -> str:

        msg = str(error).upper()
        vclass = error.violation_class

        # ---- FATAL (A) ----
        if vclass == ViolationClass.A_FATAL:

            if "AUTHORITY" in msg:
                return IncidentType.AUTHORITY_BREACH

            if "EPOCH" in msg:
                return IncidentType.EPOCH_VIOLATION

            if "TRACE" in msg:
                return IncidentType.TRACE_CORRUPTION

            if "INVARIANT" in msg or "DETERMINISTIC" in msg:
                return IncidentType.CRITICAL_INVARIANT

            if "STATE" in msg or "TRANSITION" in msg:
                return IncidentType.STATE_VIOLATION

            return IncidentType.CRITICAL_INVARIANT

        # ---- STRUCTURAL (B) ----
        if vclass == ViolationClass.B_STRUCTURAL:

            if "SCHEMA" in msg:
                return IncidentType.SCHEMA_VIOLATION

            if "STRUCTURE" in msg or "INVALID" in msg:
                return IncidentType.STRUCTURAL_ERROR

            return IncidentType.STRUCTURAL_ERROR

        # ---- DOCUMENTARY (C) ----
        if vclass == ViolationClass.C_DOCUMENTARY:
            return IncidentType.DOCUMENTATION_ERROR

        return IncidentType.UNKNOWN

    # -------------------------------------------------------------
    # FALLBACK STRING CLASSIFIER
    # -------------------------------------------------------------

    def _classify_from_message(self, msg: str) -> str:

        msg = msg.upper()

        if "AUTHORITY" in msg:
            return IncidentType.AUTHORITY_BREACH

        if "TRACE" in msg:
            return IncidentType.TRACE_CORRUPTION

        if "EPOCH" in msg:
            return IncidentType.EPOCH_VIOLATION

        if "STATE" in msg or "TRANSITION" in msg:
            return IncidentType.STATE_VIOLATION

        if "SCHEMA" in msg:
            return IncidentType.SCHEMA_VIOLATION

        if "INVARIANT" in msg:
            return IncidentType.CRITICAL_INVARIANT

        if "STRUCTURE" in msg or "INVALID" in msg:
            return IncidentType.STRUCTURAL_ERROR

        return IncidentType.UNKNOWN

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def __repr__(self):
        return "<IncidentClassifier deterministic>"