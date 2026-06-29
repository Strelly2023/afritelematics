"""NovaRide Phase 9 partner ecosystem API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase9 import (
    build_phase9_partner_ecosystem_projection,
    build_phase9_partner_revenue_projection,
    build_phase9_status,
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


def build_phase9_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase9"])

    @router.get("/v1/novaride/phase9/status")
    def phase9_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase9_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase9/partner-portal")
    def phase9_partner_portal(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase9_partner_portal",
            "organization_id": org_id,
            "partner_portal": projection["partner_portal"],
            "configuration": projection["configuration"],
            "live_dispatch_influence": projection["live_dispatch_influence"],
            "automated_incentives": projection["automated_incentives"],
            "enterprise_automation": projection["enterprise_automation"],
            "projection_only": True,
            "read_only": True,
        }

    @router.get("/v1/novaride/phase9/bookings")
    def phase9_bookings(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase9_bookings",
            "organization_id": org_id,
            "bookings": projection["bookings"],
            "live_dispatch_influence": projection["live_dispatch_influence"],
            "projection_only": True,
            "read_only": True,
        }

    @router.get("/v1/novaride/phase9/bulk-requests")
    def phase9_bulk_requests(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase9_bulk_requests",
            "organization_id": org_id,
            "bulk_scheduling": projection["bulk_scheduling"],
            "automated_incentives": projection["automated_incentives"],
            "projection_only": True,
            "read_only": True,
        }

    @router.get("/v1/novaride/phase9/event-transport")
    def phase9_event_transport(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase9_event_transport",
            "organization_id": org_id,
            "event_transport": projection["event_transport"],
            "partner_portal": projection["partner_portal"],
            "projection_only": True,
            "read_only": True,
        }

    @router.get("/v1/novaride/phase9/reports")
    def phase9_reports(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase9_partner_reporting",
            "organization_id": org_id,
            "reporting": projection["reporting"],
            "projection_only": True,
            "read_only": True,
        }

    @router.get("/v1/novaride/phase9/billing")
    def phase9_billing(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase9_partner_billing",
            "organization_id": org_id,
            "billing": projection["billing"],
            "automated_incentives": projection["automated_incentives"],
            "projection_only": True,
            "read_only": True,
        }

    @router.get("/v1/novaride/phase9/guests")
    def phase9_guests(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase9_guests",
            "organization_id": org_id,
            "bookings": projection["bookings"],
            "event_transport": projection["event_transport"],
            "partner_portal": projection["partner_portal"],
            "projection_only": True,
            "read_only": True,
        }

    @router.get("/v1/novaride/phase9/enterprise-automation")
    def phase9_enterprise_automation(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
        return {
            "view": "novaride_phase9_enterprise_automation",
            "organization_id": org_id,
            "live_dispatch_influence": projection["live_dispatch_influence"],
            "automated_incentives": projection["automated_incentives"],
            "enterprise_automation": projection["enterprise_automation"],
            "projection_only": True,
            "read_only": True,
        }

    @router.get("/v1/novaride/phase9/partner-revenue")
    def phase9_partner_revenue(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("PARTNER", "CLIENT", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase9_partner_revenue_projection(organization_id=org_id, limit=limit)

    return router


__all__ = ["build_phase9_router"]
