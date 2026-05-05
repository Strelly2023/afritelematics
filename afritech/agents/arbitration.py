"""
afritech/agents/arbitration.py

Deterministic Constitutional Arbitration

Authority:
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib
import json


# ============================================================
# EXCEPTIONS
# ============================================================

class ArbitrationViolation(Exception):
    """
    Raised when arbitration violates constitutional constraints.
    """
    pass


# ============================================================
# ARBITRATION RESULT (NON-AUTHORITY-GENERATING)
# ============================================================

@dataclass(frozen=True)
class ArbitrationResult:
    arbitration_id: str
    authority_profile: str
    permitted: bool
    deterministic: bool
    reasoning_trace: list[str]


# ============================================================
# ARBITER
# ============================================================

class ConstitutionalArbitration:
    """
    Deterministic constitutional intent arbiter.

    Responsibilities:
    - verify authority alignment
    - verify determinism
    - verify permission
    - resolve intent without creating legitimacy
    """

    REQUIRED_AUTHORITY = "CONSTITUTIONAL_RESEARCH_AGENT"


    # ========================================================
    # PUBLIC ENTRYPOINT
    # ========================================================

    def resolve(
        self,
        decision_intent: Any,
        dispatch_artifact: Any,
    ) -> ArbitrationResult:

        trace: list[str] = []

        self._validate_authority(decision_intent, dispatch_artifact)
        trace.append("authority_aligned")

        self._validate_determinism(dispatch_artifact)
        trace.append("determinism_validated")

        self._validate_permission(decision_intent)
        trace.append("permission_validated")

        arbitration_id = self._arbitration_hash(
            decision_intent,
            dispatch_artifact,
        )
        trace.append("arbitration_hashed")

        return ArbitrationResult(
            arbitration_id=arbitration_id,
            authority_profile=self.REQUIRED_AUTHORITY,
            permitted=True,
            deterministic=True,
            reasoning_trace=trace,
        )


    # ========================================================
    # AUTHORITY VALIDATION
    # ========================================================

    def _validate_authority(
        self,
        decision_intent: Any,
        dispatch_artifact: Any,
    ) -> None:

        if decision_intent.authority_profile != self.REQUIRED_AUTHORITY:
            raise ArbitrationViolation(
                "Decision authority mismatch"
            )

        if dispatch_artifact.authority_profile != self.REQUIRED_AUTHORITY:
            raise ArbitrationViolation(
                "Dispatch authority mismatch"
            )


    # ========================================================
    # DETERMINISM VALIDATION
    # ========================================================

    def _validate_determinism(
        self,
        dispatch_artifact: Any,
    ) -> None:

        if dispatch_artifact.deterministic is not True:
            raise ArbitrationViolation(
                "Dispatch artifact is non-deterministic"
            )


    # ========================================================
    # PERMISSION VALIDATION
    # ========================================================

    def _validate_permission(
        self,
        decision_intent: Any,
    ) -> None:

        if decision_intent.permitted is not True:
            raise ArbitrationViolation(
                "Decision intent denied"
            )


    # ========================================================
    # ARBITRATION HASH (TERMINAL IDENTITY)
    # ========================================================

    def _arbitration_hash(
        self,
        decision_intent: Any,
        dispatch_artifact: Any,
    ) -> str:

        payload = {
            "request_hash": decision_intent.request_hash,
            "dispatch_id": dispatch_artifact.dispatch_id,
            "authority_profile": self.REQUIRED_AUTHORITY,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()