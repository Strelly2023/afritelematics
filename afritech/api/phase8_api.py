"""NovaRide Phase 8 business and fleet systems API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase8 import (
    build_phase8_business_fleet_projection,
    build_phase8_enterprise_revenue_projection,
    build_phase8_status,
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


def build_phase8_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase8"])

    @router.get("/v1/novaride/phase8/status")
    def phase8_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase8_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase8/business-fleet")
    def phase8_business_fleet(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase8_business_fleet_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase8/corporate-accounts")
    def phase8_corporate_accounts(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return {
            "view": "novaride_phase8_corporate_accounts",
            "organization_id": org_id,
            **build_phase8_business_fleet_projection(organization_id=org_id, limit=limit)["corporate_accounts"],
        }

    @router.get("/v1/novaride/phase8/employee-booking")
    def phase8_employee_booking(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return {
            "view": "novaride_phase8_employee_booking",
            "organization_id": org_id,
            **build_phase8_business_fleet_projection(organization_id=org_id, limit=limit)["employee_booking"],
        }

    @router.get("/v1/novaride/phase8/invoicing")
    def phase8_invoicing(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return {
            "view": "novaride_phase8_invoicing",
            "organization_id": org_id,
            **build_phase8_business_fleet_projection(organization_id=org_id, limit=limit)["invoicing"],
        }

    @router.get("/v1/novaride/phase8/budgeting")
    def phase8_budgeting(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return {
            "view": "novaride_phase8_budgeting",
            "organization_id": org_id,
            **build_phase8_business_fleet_projection(organization_id=org_id, limit=limit)["budgeting"],
        }

    @router.get("/v1/novaride/phase8/monthly-billing")
    def phase8_monthly_billing(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return {
            "view": "novaride_phase8_monthly_billing",
            "organization_id": org_id,
            **build_phase8_business_fleet_projection(organization_id=org_id, limit=limit)["monthly_billing"],
        }

    @router.get("/v1/novaride/phase8/adaptive-markets")
    def phase8_adaptive_markets(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return {
            "view": "novaride_phase8_adaptive_markets",
            "organization_id": org_id,
            **build_phase8_business_fleet_projection(organization_id=org_id, limit=limit)["adaptive_markets"],
        }

    @router.get("/v1/novaride/phase8/enterprise-revenue")
    def phase8_enterprise_revenue(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase8_enterprise_revenue_projection(organization_id=org_id, limit=limit)

    return router


__all__ = ["build_phase8_router"]
