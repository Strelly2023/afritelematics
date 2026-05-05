"""
afritech/inference/constitutional_dispatch.py

Deterministic Constitutional Dispatch

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

class DispatchViolation(Exception):
    """
    Raised when dispatch violates constitutional constraints.
    """
    pass


# ============================================================
# DISPATCH ARTIFACT (NON-EXECUTING)
# ============================================================

@dataclass(frozen=True)
class ConstitutionalDispatchArtifact:
    dispatch_id: str
    authority_profile: str
    model_target: str
    constraints: dict[str, Any]
    deterministic: bool
    reasoning_trace: list[str]


# ============================================================
# DISPATCHER
# ============================================================

class ConstitutionalDispatch:
    """
    Deterministic constitutional constraint binder.

    Responsibilities:
    - validate constitutional request envelope
    - bind output and replay constraints
    - emit a dispatch artifact only
    """

    REQUIRED_OUTPUT_CONSTRAINTS = {
        "citation_required",
        "max_claims",
        "epistemic_confidence_required",
        "causal_trace_required",
    }

    REQUIRED_AUTHORITY = "CONSTITUTIONAL_RESEARCH_AGENT"


    # ========================================================
    # PUBLIC ENTRYPOINT
    # ========================================================

    def dispatch(
        self,
        request: dict[str, Any],
        route: Any,
    ) -> ConstitutionalDispatchArtifact:

        trace: list[str] = []

        payload = self._validate_request(request)
        trace.append("request_validated")

        constraints = self._extract_constraints(payload)
        trace.append("constraints_extracted")

        dispatch_id = self._dispatch_hash(
            payload["authority_profile"],
            route.model_target,
            constraints,
        )
        trace.append("dispatch_hashed")

        return ConstitutionalDispatchArtifact(
            dispatch_id=dispatch_id,
            authority_profile=payload["authority_profile"],
            model_target=route.model_target,
            constraints=constraints,
            deterministic=True,
            reasoning_trace=trace,
        )


    # ========================================================
    # REQUEST VALIDATION
    # ========================================================

    def _validate_request(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any]:

        if "constitutional_request" not in request:
            raise DispatchViolation(
                "Missing constitutional_request envelope"
            )

        payload = request["constitutional_request"]

        if payload.get("authority_profile") != self.REQUIRED_AUTHORITY:
            raise DispatchViolation(
                "Invalid authority profile for constitutional dispatch"
            )

        replay = payload.get("replay_requirements", {})
        if replay.get("deterministic") is not True:
            raise DispatchViolation(
                "Deterministic replay requirement not satisfied"
            )

        return payload


    # ========================================================
    # CONSTRAINT EXTRACTION
    # ========================================================

    def _extract_constraints(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        output_constraints = payload.get("output_constraints", {})

        missing = (
            self.REQUIRED_OUTPUT_CONSTRAINTS
            - output_constraints.keys()
        )

        if missing:
            raise DispatchViolation(
                f"Missing required output constraints: {missing}"
            )

        return {
            "citation_required":
                output_constraints["citation_required"],
            "max_claims":
                output_constraints["max_claims"],
            "epistemic_confidence_required":
                output_constraints["epistemic_confidence_required"],
            "causal_trace_required":
                output_constraints["causal_trace_required"],
            "deterministic":
                payload["replay_requirements"]["deterministic"],
        }


    # ========================================================
    # DISPATCH HASH (DETERMINISTIC IDENTITY)
    # ========================================================

    def _dispatch_hash(
        self,
        authority_profile: str,
        model_target: str,
        constraints: dict[str, Any],
    ) -> str:

        artifact = {
            "authority_profile": authority_profile,
            "model_target": model_target,
            "constraints": constraints,
        }

        canonical = json.dumps(
            artifact,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()