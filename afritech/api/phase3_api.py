"""NovaRide Phase 3 business pricing and incentive API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase3 import (
    build_business_incentives_projection,
    build_business_pricing_projection,
    build_phase3_status,
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


def build_phase3_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase3"])

    @router.get("/v1/novaride/phase3/status")
    def phase3_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase3_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase3/business/pricing")
    def phase3_business_pricing(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_business_pricing_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase3/business/incentives")
    def phase3_business_incentives(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_business_incentives_projection(organization_id=org_id, limit=limit)

    return router


__all__ = ["build_phase3_router"]
