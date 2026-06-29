"""NovaRide Phase 0 SaaS foundation API surfaces."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.control_plane import get_control_plane


class Phase0OrganizationOnboardRequest(BaseModel):
    organization_id: str
    legal_name: str
    sector: str
    trust_domain: str


class Phase0AccountRequest(BaseModel):
    organization_id: str
    user_id: str
    role: str
    status: str = "active"
    is_primary: bool = False


class Phase0SubscriptionRequest(BaseModel):
    organization_id: str
    plan: str
    status: str = "active"
    billing_cycle: str = "monthly"
    seats: int = Field(default=1, ge=1)
    start_date: str | None = None
    end_date: str | None = None
    auto_renew: bool = True


class Phase0FeatureFlagRequest(BaseModel):
    organization_id: str
    feature_key: str
    enabled: bool
    reason: str = "platform_control"
    updated_by: str = "system"


class Phase0NotificationRequest(BaseModel):
    organization_id: str
    recipient_id: str
    channel: str
    message: str
    status: str = "queued"


class Phase0IntegrationRequest(BaseModel):
    organization_id: str
    name: str
    type: str
    config: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    last_synced_at: str | None = None


PLAN_RANK = {
    "free": 0,
    "basic": 1,
    "pro": 2,
    "enterprise": 3,
}


def _normalize_plan(plan: str | None) -> str:
    normalized = str(plan or "free").strip().lower()
    return normalized if normalized in PLAN_RANK else "free"


def _require_same_organization(requested_organization_id: str | None, claims: JWTClaims) -> str:
    org_id = requested_organization_id or claims.organization_id
    if org_id != claims.organization_id:
        raise HTTPException(status_code=403, detail="organization_isolation_violation")
    return org_id


def _require_minimum_plan(organization_id: str, minimum_plan: str) -> None:
    subscription = phase0_control_plane._STORE.latest_active_subscription(organization_id=organization_id)
    if subscription is None:
        raise HTTPException(status_code=403, detail="active_subscription_required")
    if PLAN_RANK[_normalize_plan(subscription.get("plan"))] < PLAN_RANK[_normalize_plan(minimum_plan)]:
        raise HTTPException(status_code=403, detail=f"{minimum_plan}_subscription_required")


def build_phase0_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase0"])
    control_plane = get_control_plane()

    @router.get("/v1/novatech/phase0/status")
    def phase0_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return control_plane.phase0_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novatech/phase0/organizations")
    def phase0_organizations(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return control_plane.organizations(organization_id=org_id, limit=limit)

    @router.post("/v1/novatech/phase0/organizations/onboard")
    def phase0_organization_onboard(
        body: Phase0OrganizationOnboardRequest,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.organization_id, claims)
        return control_plane.phase0_organization_onboard(
            organization_id=org_id,
            legal_name=body.legal_name,
            sector=body.sector,
            trust_domain=body.trust_domain,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/v1/novatech/phase0/accounts")
    def phase0_accounts(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return control_plane.phase0_accounts(organization_id=org_id, limit=limit)

    @router.post("/v1/novatech/phase0/accounts")
    def phase0_account_create(
        body: Phase0AccountRequest,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.organization_id, claims)
        _require_minimum_plan(org_id, "free")
        return control_plane.phase0_account_create(
            organization_id=org_id,
            user_id=body.user_id,
            role=body.role,
            status=body.status,
            is_primary=body.is_primary,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/v1/novatech/phase0/subscriptions")
    def phase0_subscriptions(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return control_plane.phase0_subscriptions(organization_id=org_id, limit=limit)

    @router.post("/v1/novatech/phase0/subscriptions")
    def phase0_subscription_create(
        body: Phase0SubscriptionRequest,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.organization_id, claims)
        _require_minimum_plan(org_id, "free")
        return control_plane.phase0_subscription_create(
            organization_id=org_id,
            plan=body.plan,
            status=body.status,
            billing_cycle=body.billing_cycle,
            seats=body.seats,
            start_date=body.start_date,
            end_date=body.end_date,
            auto_renew=body.auto_renew,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/v1/novatech/phase0/catalog")
    def phase0_catalog(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return control_plane.phase0_catalog(organization_id=org_id, limit=limit)

    @router.get("/v1/novatech/phase0/feature-flags")
    def phase0_feature_flags(
        organization_id: str | None = None,
        feature_key: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return control_plane.phase0_feature_flags(
            organization_id=org_id,
            feature_key=feature_key,
            limit=limit,
        )

    @router.post("/v1/novatech/phase0/feature-flags")
    def phase0_feature_flag_create(
        body: Phase0FeatureFlagRequest,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.organization_id, claims)
        _require_minimum_plan(org_id, "pro")
        return control_plane.phase0_feature_flag_set(
            organization_id=org_id,
            feature_key=body.feature_key,
            enabled=body.enabled,
            reason=body.reason,
            updated_by=body.updated_by,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/v1/novatech/phase0/notifications")
    def phase0_notifications(
        organization_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return control_plane.phase0_notifications(
            organization_id=org_id,
            status=status,
            limit=limit,
        )

    @router.post("/v1/novatech/phase0/notifications")
    def phase0_notification_create(
        body: Phase0NotificationRequest,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.organization_id, claims)
        _require_minimum_plan(org_id, "free")
        return control_plane.phase0_notification_queue(
            organization_id=org_id,
            recipient_id=body.recipient_id,
            channel=body.channel,
            message=body.message,
            status=body.status,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/v1/novatech/phase0/notifications/{notification_id}/deliver")
    def phase0_notification_deliver(
        notification_id: str,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_minimum_plan(org_id, "free")
        return control_plane.phase0_notification_send(
            notification_id=notification_id,
            organization_id=org_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/v1/novatech/phase0/integrations")
    def phase0_integrations(
        organization_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return control_plane.phase0_integrations(
            organization_id=org_id,
            status=status,
            limit=limit,
        )

    @router.post("/v1/novatech/phase0/integrations")
    def phase0_integration_create(
        body: Phase0IntegrationRequest,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.organization_id, claims)
        _require_minimum_plan(org_id, "pro")
        return control_plane.phase0_integration_register(
            organization_id=org_id,
            name=body.name,
            type=body.type,
            config=body.config,
            status=body.status,
            last_synced_at=body.last_synced_at,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    return router


__all__ = ["build_phase0_router"]
