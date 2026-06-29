"""NovaRide Phase 11 compliance and inspection API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase11 import (
    build_phase11_auto_ticket_classification_projection,
    build_phase11_compliance_tracking_projection,
    build_phase11_compliance_workspace_projection,
    build_phase11_document_verification_projection,
    build_phase11_driver_scoring_projection,
    build_phase11_fraud_detection_projection,
    build_phase11_inspection_reports_projection,
    build_phase11_inspections_projection,
    build_phase11_regulatory_readiness_projection,
    build_phase11_smart_refunds_projection,
    build_phase11_status,
    build_phase11_support_dashboard_projection,
    build_phase11_compliance_contract_projection,
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


def build_phase11_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase11"])

    @router.get("/v1/novaride/phase11/status")
    def phase11_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase11_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/compliance-workspace")
    def phase11_compliance_workspace(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_compliance_workspace_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/support-dashboard")
    def phase11_support_dashboard(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_support_dashboard_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/inspections")
    def phase11_inspections(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_inspections_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/document-verification")
    def phase11_document_verification(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_document_verification_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/inspection-reports")
    def phase11_inspection_reports(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_inspection_reports_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/compliance-tracking")
    def phase11_compliance_tracking(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_compliance_tracking_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/driver-scoring")
    def phase11_driver_scoring(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_driver_scoring_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/fraud-detection")
    def phase11_fraud_detection(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_fraud_detection_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/smart-refunds")
    def phase11_smart_refunds(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_smart_refunds_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/auto-ticket-classification")
    def phase11_auto_ticket_classification(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_auto_ticket_classification_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/regulatory-readiness")
    def phase11_regulatory_readiness(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase11_regulatory_readiness_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase11/compliance-contract")
    def phase11_compliance_contract(
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        return build_phase11_compliance_contract_projection()

    return router


__all__ = ["build_phase11_router"]
