"""NovaRide Phase 10 support and dispute system API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase10 import (
    build_phase10_customer_experience_projection,
    build_phase10_disputes_projection,
    build_phase10_escalations_projection,
    build_phase10_replay_evidence_projection,
    build_phase10_refunds_projection,
    build_phase10_ride_lookup_projection,
    build_phase10_status,
    build_phase10_support_contract_projection,
    build_phase10_support_workspace_projection,
    build_phase10_tickets_projection,
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


def build_phase10_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase10"])

    @router.get("/v1/novaride/phase10/status")
    def phase10_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase10_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase10/support-contract")
    def phase10_support_contract(
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        return build_phase10_support_contract_projection()

    @router.get("/v1/novaride/phase10/support-workspace")
    def phase10_support_workspace(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase10_support_workspace_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase10/tickets")
    def phase10_tickets(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase10_tickets_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase10/refunds")
    def phase10_refunds(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase10_refunds_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase10/disputes")
    def phase10_disputes(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase10_disputes_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase10/ride-lookup")
    def phase10_ride_lookup(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase10_ride_lookup_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase10/escalations")
    def phase10_escalations(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase10_escalations_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase10/replay-evidence")
    def phase10_replay_evidence(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase10_replay_evidence_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase10/customer-experience")
    def phase10_customer_experience(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase10_customer_experience_projection(organization_id=org_id, limit=limit)

    return router


__all__ = ["build_phase10_router"]
