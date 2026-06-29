"""NovaRide Phase 13 global execution bridge API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase13 import (
    build_phase13_contract_projection,
    build_phase13_global_execution_workspace_projection,
    build_phase13_status,
)


class ControlledExecutionRequest(BaseModel):
    organization_id: str | None = None
    operator_acknowledged: bool = Field(default=False)
    requested_tier: str = Field(default="controlled")
    action_type: str = Field(default="controlled_global_execution_activation")
    notes: str | None = None


def _require_same_organization(requested_organization_id: str | None, claims: JWTClaims) -> str:
    org_id = requested_organization_id or claims.organization_id
    if org_id != claims.organization_id:
        raise HTTPException(status_code=403, detail="organization_isolation_violation")
    return org_id


def _require_active_subscription(organization_id: str) -> None:
    subscription = phase0_control_plane._STORE.latest_active_subscription(organization_id=organization_id)
    if subscription is None:
        raise HTTPException(status_code=403, detail="active_subscription_required")


def build_phase13_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase13"])

    @router.get("/v1/novaride/phase13/status")
    def phase13_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase13_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase13/global-deployment-plan")
    def phase13_global_deployment_plan(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase13_global_execution_workspace_projection(organization_id=org_id, limit=limit)["global_deployment_plan"]

    @router.get("/v1/novaride/phase13/controlled-ai-decision-engine")
    def phase13_controlled_ai_decision_engine(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase13_global_execution_workspace_projection(organization_id=org_id, limit=limit)["controlled_ai_decision_engine"]

    @router.get("/v1/novaride/phase13/aws-production-infra")
    def phase13_aws_production_infra(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase13_global_execution_workspace_projection(organization_id=org_id, limit=limit)["aws_production_infra"]

    @router.get("/v1/novaride/phase13/real-execution-layer")
    def phase13_real_execution_layer(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase13_global_execution_workspace_projection(organization_id=org_id, limit=limit)["real_execution_layer"]

    @router.get("/v1/novaride/phase13/ai-optimization")
    def phase13_ai_optimization(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase13_global_execution_workspace_projection(organization_id=org_id, limit=limit)["ai_optimization"]

    @router.get("/v1/novaride/phase13/nova-connect-expansion")
    def phase13_nova_connect_expansion(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase13_global_execution_workspace_projection(organization_id=org_id, limit=limit)["novaconnect_expansion"]

    @router.get("/v1/novaride/phase13/novapay-expansion")
    def phase13_novapay_expansion(
        organization_id: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        _require_active_subscription(org_id)
        return build_phase13_global_execution_workspace_projection(organization_id=org_id, limit=limit)["novapay_expansion"]

    @router.get("/v1/novaride/phase13/global-execution-contract")
    def phase13_global_execution_contract(
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "FLEET_OWNER", "CLIENT", "PARTNER", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        return build_phase13_contract_projection()

    @router.post("/v1/novaride/phase13/controlled-execution")
    def phase13_controlled_execution(
        body: ControlledExecutionRequest,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.organization_id, claims)
        _require_active_subscription(org_id)
        workspace = build_phase13_global_execution_workspace_projection(organization_id=org_id)
        activation_ready = bool(workspace["ready"] and body.operator_acknowledged and workspace["real_execution_layer"]["execution_ready"])
        activation_status = "activated" if activation_ready else "held"
        activation_reason = (
            "Controlled execution bridge activated with operator acknowledgment."
            if activation_ready
            else "Controlled execution remains held pending operator acknowledgment or readiness."
        )
        request_payload = body.model_dump() if hasattr(body, "model_dump") else body.dict()
        record_payload = jsonable_encoder(
            {
                "request": request_payload,
                "workspace": workspace,
                "activation_status": activation_status,
                "activation_reason": activation_reason,
            }
        )
        activation_record = phase0_control_plane.record_dashboard_action_snapshot(
            payload=record_payload,
            source="afriride_phase13_controlled_execution",
            action_type=body.action_type,
            organization_id=org_id,
        )
        return {
            "view": "novaride_phase13_controlled_execution_activation",
            "organization_id": org_id,
            "requested_tier": body.requested_tier,
            "activation": {
                "activation_status": activation_status,
                "activation_reason": activation_reason,
                "requested_tier": body.requested_tier,
                "acknowledged": body.operator_acknowledged,
                "activation_ready": activation_ready,
                "action_type": body.action_type,
                "notes": body.notes,
            },
            "action_record": activation_record,
            "workspace": workspace,
            "read_only": False,
            "governance_linked": True,
            "controlled_execution": True,
        }

    return router


__all__ = ["ControlledExecutionRequest", "build_phase13_router"]
