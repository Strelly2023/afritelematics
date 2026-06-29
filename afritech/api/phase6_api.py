"""NovaRide Phase 6 navigation and maps intelligence API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase6 import (
    build_navigation_maps_intelligence_projection,
    build_phase6_status,
)


def _require_same_organization(requested_organization_id: str | None, claims: JWTClaims) -> str:
    org_id = requested_organization_id or claims.organization_id
    if org_id != claims.organization_id:
        raise HTTPException(status_code=403, detail="organization_isolation_violation")
    return org_id


def _require_active_subscription(organization_id: str) -> None:
    subscription = phase0_control_plane._STORE.latest_active_subscription(organization_id=organization_id)
    if subscription is None:
        raise HTTPException(status_code=403, detail="active_subscription_required")


def build_phase6_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase6"])

    @router.get("/v1/novaride/phase6/status")
    def phase6_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase6_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase6/navigation-intelligence")
    def phase6_navigation_intelligence(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_navigation_maps_intelligence_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase6/capital-allocation")
    def phase6_capital_allocation(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_navigation_maps_intelligence_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase6_capital_allocation",
            "phase": "6",
            "platform": "NovaRide Phase 6",
            "organization_id": org_id,
            "capital_allocation": projection["capital_allocation"],
            "traffic_aware_routing": projection["traffic_aware_routing"],
            "route_optimization": projection["route_optimization"],
            "controlled_execution": projection["controlled_execution"],
            "read_only": True,
            "projection_only": True,
            "governance_linked": True,
            "creates_authority": False,
        }

    return router


__all__ = ["build_phase6_router"]
