"""Read-only mobile intelligence API for driver and passenger surfaces."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.intelligence.mobile_projection import (
    build_driver_intelligence_projection,
    build_passenger_intelligence_projection,
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


def build_mobile_intelligence_router() -> APIRouter:
    router = APIRouter(tags=["novaride-mobile-intelligence"])

    @router.get("/v1/intelligence/driver")
    def driver_intelligence(
        organization_id: str | None = None,
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR", "ADMIN")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_driver_intelligence_projection(organization_id=org_id, driver_id=claims.sub)

    @router.get("/v1/intelligence/passenger")
    def passenger_intelligence(
        organization_id: str | None = None,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "OPERATOR", "ADMIN")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_passenger_intelligence_projection(organization_id=org_id, passenger_id=claims.sub)

    return router


__all__ = ["build_mobile_intelligence_router"]
