# afritech/guards/quarantine_manager.py

"""
AfriTech Quarantine Manager

Purpose:
Isolate invalid or compromised entities from execution flow.

Guarantees:
- deterministic quarantine behavior
- no re-entry of quarantined entities
- structured audit trail
- integration with constitutional engine
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# QUARANTINE MANAGER
# -----------------------------------------------------------------

class QuarantineManager:

    def __init__(self):
        self._quarantine_store: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # QUARANTINE ENTITY
    # -------------------------------------------------------------

    def quarantine(
        self,
        entity: Any,
        reason: str,
        violation_class: ViolationClass = ViolationClass.A_FATAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add entity to quarantine list and immediately reject execution.
        """

        record = {
            "entity_id": self._extract_id(entity),
            "entity_repr": repr(entity),
            "reason": reason,
            "violation_class": violation_class.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }

        self._quarantine_store.append(record)

        # Immediately stop execution (constitutionally)
        fail(
            msg=f"QUARANTINED: {reason}",
            violation_class=violation_class,
        )

    # -------------------------------------------------------------
    # CHECK QUARANTINE STATUS
    # -------------------------------------------------------------

    def is_quarantined(self, entity: Any) -> bool:
        """
        Check if entity is already quarantined.
        """

        entity_id = self._extract_id(entity)

        for record in self._quarantine_store:
            if record["entity_id"] == entity_id:
                return True

        return False

    # -------------------------------------------------------------
    # ENFORCE NON-QUARANTINE (CRITICAL GUARD ENTRYPOINT)
    # -------------------------------------------------------------

    def enforce_not_quarantined(self, entity: Any) -> None:
        """
        Prevent execution of quarantined entities.
        """

        if self.is_quarantined(entity):
            fail(
                msg=f"Execution blocked: entity quarantined ({self._extract_id(entity)})",
                violation_class=ViolationClass.A_FATAL,
            )

    # -------------------------------------------------------------
    # GET ALL QUARANTINED RECORDS
    # -------------------------------------------------------------

    def list_quarantined(self) -> List[Dict[str, Any]]:
        """
        Return immutable snapshot of quarantined records.
        """

        return list(self._quarantine_store)

    # -------------------------------------------------------------
    # CLEAR QUARANTINE (CONTROLLED USE ONLY)
    # -------------------------------------------------------------

    def clear(self) -> None:
        """
        Clear quarantine store.

        NOTE:
        Should only be used in controlled/testing environments.
        """

        self._quarantine_store.clear()

    # -------------------------------------------------------------
    # INTERNAL UTILITY
    # -------------------------------------------------------------

    def _extract_id(self, entity: Any) -> str:
        """
        Deterministic entity identity extraction.
        """

        if hasattr(entity, "id"):
            return str(entity.id)

        if isinstance(entity, dict) and "id" in entity:
            return str(entity["id"])

        # fallback to stable string
        return str(hash(repr(entity)))

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def __repr__(self):
        return f"<QuarantineManager size={len(self._quarantine_store)}>"
