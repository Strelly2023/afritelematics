"""NovaRide Phase 12 multi-city and global scaling API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase12 import (
    build_phase12_auto_decision_engine_projection,
    build_phase12_contract_projection,
    build_phase12_currency_support_projection,
    build_phase12_distributed_infrastructure_projection,
    build_phase12_driver_incentives_projection,
    build_phase12_fraud_prediction_projection,
    build_phase12_geo_fencing_projection,
    build_phase12_global_learning_projection,
    build_phase12_global_scale_workspace_projection,
    build_phase12_localization_projection,
    build_phase12_multi_city_management_projection,
    build_phase12_region_pricing_projection,
    build_phase12_status,
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


def build_phase12_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase12"])

    @router.get("/v1/novaride/phase12/status")
    def phase12_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase12_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/global-scale-workspace")
    def phase12_global_scale_workspace(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_global_scale_workspace_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/multi-city-management")
    def phase12_multi_city_management(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_multi_city_management_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/geo-fencing")
    def phase12_geo_fencing(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_geo_fencing_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/currency-support")
    def phase12_currency_support(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_currency_support_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/localization")
    def phase12_localization(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_localization_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/region-pricing")
    def phase12_region_pricing(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_region_pricing_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/distributed-infrastructure")
    def phase12_distributed_infrastructure(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_distributed_infrastructure_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/auto-decision-engine")
    def phase12_auto_decision_engine(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_auto_decision_engine_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/fraud-prediction")
    def phase12_fraud_prediction(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_fraud_prediction_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/driver-incentives")
    def phase12_driver_incentives(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_driver_incentives_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/global-learning")
    def phase12_global_learning(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase12_global_learning_projection(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase12/global-scale-contract")
    def phase12_global_scale_contract(
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        return build_phase12_contract_projection()

    return router


__all__ = ["build_phase12_router"]
