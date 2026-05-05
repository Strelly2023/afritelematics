"""
afritech/agents/constitutional_agent.py

Minimal Constitutional Research Agent

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

class ConstitutionalViolation(Exception):
    """
    Raised when a constitutional constraint is violated.
    """
    pass


# ============================================================
# DECISION INTENT (NON-EXECUTING)
# ============================================================

@dataclass(frozen=True)
class DecisionIntent:
    request_hash: str
    authority_profile: str
    permitted: bool
    reasoning_trace: list[str]


# ============================================================
# CONSTITUTIONAL AGENT
# ============================================================

class ConstitutionalAgent:
    """
    Deterministic authority-scoped constitutional decision surface.

    This agent:
    - evaluates authority BEFORE reasoning
    - enforces scope invariants
    - emits decision intent only
    - performs no execution, mutation, or I/O
    """

    REQUIRED_AUTHORITY = "CONSTITUTIONAL_RESEARCH_AGENT"

    PERMITTED_OPERATIONS = {
        "research_synthesis",
        "citation_analysis",
        "non_mutating_inference",
    }

    PROHIBITED_OPERATIONS = {
        "state_mutation",
        "external_write",
        "environment_interaction",
        "registry_modification",
        "epoch_advancement",
        "authority_delegation",
    }

    def __init__(
        self,
        authority_profile: str,
        constitution: dict[str, Any],
    ):
        self.authority_profile = authority_profile
        self.constitution = constitution

        self._validate_authority()


    # ========================================================
    # PUBLIC ENTRYPOINT
    # ========================================================

    def decide(
        self,
        request: dict[str, Any],
    ) -> DecisionIntent:

        trace: list[str] = []

        self._validate_request_envelope(request)
        trace.append("request_envelope_validated")

        self._validate_scope(request)
        trace.append("scope_validated")

        self._validate_operations(request)
        trace.append("operations_validated")

        req_hash = self._canonical_request_hash(request)
        trace.append("decision_intent_emitted")

        return DecisionIntent(
            request_hash=req_hash,
            authority_profile=self.authority_profile,
            permitted=True,
            reasoning_trace=trace,
        )


    # ========================================================
    # AUTHORITY VALIDATION
    # ========================================================

    def _validate_authority(self) -> None:
        if self.authority_profile != self.REQUIRED_AUTHORITY:
            raise ConstitutionalViolation(
                "Invalid authority profile for ConstitutionalAgent"
            )


    # ========================================================
    # REQUEST ENVELOPE VALIDATION
    # ========================================================

    def _validate_request_envelope(
        self,
        request: dict[str, Any],
    ) -> None:

        if "constitutional_request" not in request:
            raise ConstitutionalViolation(
                "Missing constitutional_request envelope"
            )

        envelope = request["constitutional_request"]

        if envelope.get("authority_profile") != self.authority_profile:
            raise ConstitutionalViolation(
                "Authority mismatch in constitutional_request"
            )


    # ========================================================
    # SCOPE VALIDATION
    # ========================================================

    def _validate_scope(
        self,
        request: dict[str, Any],
    ) -> None:

        payload = request["constitutional_request"]

        prohibited = set(payload.get("prohibited_operations", []))

        if prohibited & self.PROHIBITED_OPERATIONS:
            raise ConstitutionalViolation(
                "Request includes constitutionally prohibited operations"
            )


    # ========================================================
    # OPERATION VALIDATION
    # ========================================================

    def _validate_operations(
        self,
        request: dict[str, Any],
    ) -> None:

        payload = request["constitutional_request"]
        requested = set(payload.get("permissible_operations", []))

        if not requested:
            raise ConstitutionalViolation(
                "No permissible_operations declared"
            )

        if not requested.issubset(self.PERMITTED_OPERATIONS):
            raise ConstitutionalViolation(
                "Requested operation outside constitutional scope"
            )


    # ========================================================
    # HASHING (DETERMINISTIC)
    # ========================================================

    def _canonical_request_hash(
        self,
        request: dict[str, Any],
    ) -> str:

        canonical = json.dumps(
            request,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
