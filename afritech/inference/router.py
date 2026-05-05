"""
afritech/inference/router.py

Deterministic Constitutional Inference Router

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

class RoutingViolation(Exception):
    """
    Raised when routing violates constitutional constraints.
    """
    pass


# ============================================================
# ROUTE (NON-EXECUTING)
# ============================================================

@dataclass(frozen=True)
class InferenceRoute:
    route_id: str
    authority_profile: str
    model_target: str
    deterministic: bool
    reasoning_trace: list[str]


# ============================================================
# ROUTER
# ============================================================

class InferenceRouter:
    """
    Deterministic constitutional route selector.

    Responsibilities:
    - validate deterministic replay requirement
    - select a lawful inference target
    - emit route identity only (no execution)
    """

    ROUTE_TABLE = {
        "CONSTITUTIONAL_RESEARCH_AGENT": {
            "low": "deterministic-research-model-v1"
        }
    }

    REQUIRED_DETERMINISM = True


    # ========================================================
    # PUBLIC ENTRYPOINT
    # ========================================================

    def route(
        self,
        request: dict[str, Any]
    ) -> InferenceRoute:

        trace: list[str] = []

        self._validate_request_envelope(request)
        trace.append("request_validated")

        payload = request["constitutional_request"]
        authority = payload["authority_profile"]
        risk = payload["risk_class"]

        model = self._resolve_route(authority, risk)
        trace.append("routing_selection")

        route_id = self._route_hash(authority, risk, model)
        trace.append("route_hashed")

        return InferenceRoute(
            route_id=route_id,
            authority_profile=authority,
            model_target=model,
            deterministic=True,
            reasoning_trace=trace,
        )


    # ========================================================
    # REQUEST VALIDATION
    # ========================================================

    def _validate_request_envelope(
        self,
        request: dict[str, Any]
    ) -> None:

        if "constitutional_request" not in request:
            raise RoutingViolation(
                "Missing constitutional_request envelope"
            )

        payload = request["constitutional_request"]

        replay = payload.get("replay_requirements", {})

        if replay.get("deterministic") is not True:
            raise RoutingViolation(
                "Deterministic replay requirement not satisfied"
            )


    # ========================================================
    # ROUTE RESOLUTION
    # ========================================================

    def _resolve_route(
        self,
        authority: str,
        risk: str
    ) -> str:

        if authority not in self.ROUTE_TABLE:
            raise RoutingViolation(
                "Unknown authority profile"
            )

        authority_routes = self.ROUTE_TABLE[authority]

        if risk not in authority_routes:
            raise RoutingViolation(
                "Unsupported risk class for authority"
            )

        return authority_routes[risk]


    # ========================================================
    # ROUTE HASHING (DETERMINISTIC IDENTITY)
    # ========================================================

    def _route_hash(
        self,
        authority: str,
        risk: str,
        model: str
    ) -> str:

        canonical = json.dumps(
            {
                "authority": authority,
                "risk": risk,
                "model": model,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()