"""Read-only NovaTech intranet portal for internal engineering and operations."""

from __future__ import annotations

from html import escape
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.api.realtime.dashboard_bus import publish_dashboard_snapshot
from afritech.afripay.billing import BillingService
from afritech.afripay.money import Money
from afritech.afroprog_workspace.workspace import build_workspace_payload, render_projects_view
from afritech.afriprogramming.control_plane import get_control_plane
from afritech.novascript import get_novascript_service


class OrganizationOnboardRequest(BaseModel):
    organization_id: str
    legal_name: str
    sector: str
    trust_domain: str


class ControlledExecutionActivationRequest(BaseModel):
    acknowledged: bool = True
    requested_tier: str = "controlled"
    operator_note: str = "Operator acknowledged controlled execution readiness."


def build_novatech_intranet_router() -> APIRouter:
    router = APIRouter(tags=["novatech-intranet"])
    novascript = get_novascript_service()
    control_plane = get_control_plane()

    @router.get("/novatech/intranet/", response_class=HTMLResponse)
    def intranet_home() -> str:
        return _render_intranet_html()

    @router.get("/novatech/extranet/", response_class=HTMLResponse)
    def extranet_home() -> str:
        return _render_extranet_html()

    @router.get("/v1/novatech/intranet/status")
    async def intranet_status(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = {
            "view": "novatech_intranet_status",
            "product": "NovaTech Intranet",
            "organization_id": organization_id,
            "status": "ready",
            "access": "internal_authenticated",
            "dashboards": {
                "novascript": "/v1/novascript/dashboard",
                "novaprogramming": "/v1/novaprogramming/dashboard",
                "operator_analytics": "/v1/operator/analytics",
                "operator_decisions": "/v1/operator/decisions",
                "operator_actions": "/v1/operator/actions",
                "novatech_analytics": "/v1/novatech/intranet/analytics",
                "novatech_decisions": "/v1/novatech/intranet/decisions",
                "novatech_actions": "/v1/novatech/intranet/actions",
                "novatech_platform": "/v1/novatech/intranet/platform",
                "novatech_extranet": "/v1/novatech/extranet/status",
                "novatech_knowledge": "/v1/novatech/intranet/knowledge",
                "novatech_workflows": "/v1/novatech/intranet/workflows",
                "novatech_comms": "/v1/novatech/intranet/comms",
                "novatech_saas": "/v1/novatech/saas/status",
                "novatech_organizations": "/v1/novatech/organizations",
                "novatech_outcomes": "/v1/novatech/outcomes/status",
                "novatech_trust_network": "/v1/novatech/trust-network/status",
                "novatech_marketplace": "/v1/novatech/marketplace/status",
                "novatech_execution_activation": "/v1/novatech/organizations/{organization_id}/execution/activation",
                "novatech_marketplace_onboarding": "/v1/novatech/marketplace/onboarding",
                "operations": "/v1/dashboard/gateway",
                "public_trust": "/public/trust/dashboard",
            },
            "read_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_status",
                "organization_id": organization_id,
                "status": payload["status"],
                "dashboards": payload["dashboards"],
            }
        )
        return payload

    @router.get("/v1/novatech/intranet/dashboard")
    async def intranet_dashboard(
        role: str = "developers",
        project_id: str = "project-employee-rbac",
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = {
            "view": "novatech_intranet_dashboard",
            "product": "NovaTech Intranet",
            "organization_id": organization_id,
            "status": novascript.status(organization_id=organization_id),
            "novascript_dashboard": {
                "status": novascript.status(organization_id=organization_id),
                "catalog": novascript.catalog(organization_id=organization_id),
                "risk_dashboard": novascript.organization_risk_dashboard(organization_id=organization_id),
            },
            "novaprogramming_dashboard": {
                "status": control_plane.status(organization_id=organization_id),
                "catalog": control_plane.catalog(organization_id=organization_id),
                "metrics": control_plane.metrics(organization_id=organization_id),
                "trust": control_plane.trust(organization_id=organization_id),
                "staff_dashboard": control_plane.staff_dashboard(
                    role=role,
                    project_id=project_id,
                    organization_id=organization_id,
                ),
            },
            "internal_links": _internal_links(),
            "read_only": True,
            "governance_linked": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_dashboard",
                "organization_id": organization_id,
                "status": payload["status"],
                "novascript_status": payload["novascript_dashboard"]["status"],
                "novaprogramming_status": payload["novaprogramming_dashboard"]["status"],
            }
        )
        return payload

    @router.get("/v1/novatech/intranet/platform")
    async def intranet_platform(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = _build_novatech_platform_payload(
            organization_id=organization_id,
            role="developers",
            project_id="project-employee-rbac",
        )
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_platform",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "intranet": payload["surfaces"]["intranet"]["status"],
                    "extranet": payload["surfaces"]["extranet"]["status"],
                    "knowledge": payload["surfaces"]["knowledge"]["project_count"],
                    "workflows": payload["surfaces"]["workflows"]["workflow_count"],
                    "comms": payload["surfaces"]["comms"]["message_count"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/extranet/status")
    async def extranet_status(
        claims = Depends(require_roles("CLIENT", "PARTNER", "SUPPLIER", "INVESTOR", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = _build_extranet_surface(organization_id=organization_id)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_extranet_status",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "audiences": len(payload["audiences"]),
                    "public_routes": len(payload["routes"]),
                },
            }
        )
        return payload

    @router.get("/v1/novatech/intranet/knowledge")
    async def intranet_knowledge(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = _build_knowledge_surface(
            organization_id=organization_id,
            project_id="project-employee-rbac",
        )
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_knowledge",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "project_count": payload["project_count"],
                    "file_count": payload["file_count"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/intranet/workflows")
    async def intranet_workflows(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = _build_workflow_surface(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_workflows",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "workflow_count": payload["workflow_count"],
                    "running": payload["state_counts"].get("running", 0),
                    "completed": payload["state_counts"].get("completed", 0),
                },
            }
        )
        return payload

    @router.get("/v1/novatech/intranet/comms")
    async def intranet_comms(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = _build_comms_surface(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_comms",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "channel_count": len(payload["channels"]),
                    "message_count": payload["message_count"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/saas/status")
    async def saas_status(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = _build_saas_surface(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_saas_status",
                "organization_id": organization_id,
                "status": payload["safe_execution"]["execution_tier"],
                "summary": {
                    "tenant_count": payload["tenant_count"],
                    "billing_estimated_amount": payload["billing"]["estimated_amount"],
                    "safe_execution_enabled": payload["safe_execution"]["safe_execution_enabled"],
                },
            }
        )
        return payload

    @router.post("/v1/novatech/organizations/onboard")
    async def organization_onboard(
        body: OrganizationOnboardRequest,
        claims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        payload = control_plane.onboard_organization(
            organization_id=body.organization_id,
            legal_name=body.legal_name,
            sector=body.sector,
            trust_domain=body.trust_domain,
        )
        await publish_dashboard_snapshot(
            {
                "source": "novatech_organization_onboard",
                "organization_id": body.organization_id,
                "status": payload["status"],
                "summary": {
                    "legal_name": body.legal_name,
                    "sector": body.sector,
                    "trust_domain": body.trust_domain,
                    "requested_by": claims.organization_id,
                },
            }
        )
        return payload

    @router.get("/v1/novatech/organizations")
    async def organization_directory(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = _build_organization_directory_surface(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_organization_directory",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "organization_count": payload["organization_count"],
                    "certified_count": payload["certified_count"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/organizations/{organization_id}")
    async def organization_detail(
        organization_id: str,
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        payload = _build_organization_detail_surface(
            organization_id=organization_id,
            requester_organization_id=claims.organization_id,
            limit=limit,
        )
        await publish_dashboard_snapshot(
            {
                "source": "novatech_organization_detail",
                "organization_id": organization_id,
                "status": payload["safe_execution"]["execution_tier"],
                "summary": {
                    "billing_plan": payload["billing"]["summary"]["plan"],
                    "execution_tier": payload["safe_execution"]["execution_tier"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/organizations/{organization_id}/billing")
    async def organization_billing(
        organization_id: str,
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        payload = _build_organization_billing_surface(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_organization_billing",
                "organization_id": organization_id,
                "status": payload["summary"]["plan"],
                "summary": {
                    "estimated_amount": payload["summary"]["estimated_amount"],
                    "invoice_status": payload["invoice_preview"]["status"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/organizations/{organization_id}/execution")
    async def organization_execution(
        organization_id: str,
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        payload = _build_safe_execution_surface(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_organization_execution",
                "organization_id": organization_id,
                "status": payload["execution"]["execution_tier"],
                "summary": {
                    "safe_execution_enabled": payload["execution"]["safe_execution_enabled"],
                    "execution_tier_ready": payload["execution"]["execution_tier_ready"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/organizations/{organization_id}/execution/activation")
    async def organization_execution_activation(
        organization_id: str,
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        payload = control_plane.controlled_execution_activation(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_organization_execution_activation",
                "organization_id": organization_id,
                "status": payload["activation"]["activation_status"],
                "summary": {
                    "safe_execution_enabled": payload["activation"]["safe_execution_enabled"],
                    "requested_tier": payload["activation"]["requested_tier"],
                    "acknowledged": payload["activation"]["acknowledged"],
                },
            }
        )
        return payload

    @router.post("/v1/novatech/organizations/{organization_id}/execution/activate")
    async def organization_execution_activate(
        organization_id: str,
        body: ControlledExecutionActivationRequest,
        claims = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        payload = control_plane.activate_controlled_execution(
            organization_id=organization_id,
            acknowledged=body.acknowledged,
            requested_tier=body.requested_tier,
            operator_note=body.operator_note,
        )
        await publish_dashboard_snapshot(
            {
                "source": "novatech_organization_execution_activation",
                "organization_id": organization_id,
                "status": payload["activation"]["activation_status"],
                "summary": {
                    "safe_execution_enabled": payload["activation"]["safe_execution_enabled"],
                    "requested_tier": payload["activation"]["requested_tier"],
                    "acknowledged": payload["activation"]["acknowledged"],
                    "requested_by": claims.organization_id,
                },
            }
        )
        return payload

    @router.get("/v1/novatech/outcomes/status")
    async def outcome_status(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.outcome_status(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_outcomes_status",
                "organization_id": organization_id,
                "status": payload["current"]["outcome_band"],
                "summary": {
                    "outcome_score": payload["current"]["outcome_score"],
                    "learning_band": payload["current"]["learning_band"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/outcomes/registry")
    async def outcome_registry(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.outcome_registry(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_outcomes_registry",
                "organization_id": organization_id,
                "status": payload["current"]["outcome_band"],
                "summary": {
                    "count": payload["registry"]["count"],
                    "latest": payload["current"]["outcome_score"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/outcomes/learning")
    async def outcome_learning(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.outcome_learning(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_outcomes_learning",
                "organization_id": organization_id,
                "status": payload["learning"]["band"],
                "summary": {
                    "watch_items": len(payload["learning"]["watch_items"]),
                    "recommendations": len(payload["learning"]["recommendations"]),
                },
            }
        )
        return payload

    @router.get("/v1/novatech/outcomes/scoring")
    async def outcome_scoring(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.outcome_scoring(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_outcomes_scoring",
                "organization_id": organization_id,
                "status": payload["scoring"]["band"],
                "summary": {
                    "outcome_score": payload["scoring"]["score"],
                    "history_points": payload["scoring"]["trend"]["count"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/outcomes/replay")
    async def outcome_replay(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.outcome_replay(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_outcomes_replay",
                "organization_id": organization_id,
                "status": payload["replay"]["status"],
                "summary": {
                    "replayable": payload["replay"]["replayable"],
                    "latest_action_id": payload["replay"]["latest_action_id"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/organizations/{organization_id}/outcomes")
    async def organization_outcomes(
        organization_id: str,
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        payload = control_plane.outcome_status(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_organization_outcomes",
                "organization_id": organization_id,
                "status": payload["current"]["outcome_band"],
                "summary": {
                    "outcome_score": payload["current"]["outcome_score"],
                    "learning_band": payload["current"]["learning_band"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/trust-network/status")
    async def trust_network_status(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.federated_trust_network(organization_id=organization_id)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_trust_network_status",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "member_count": payload["member_count"],
                    "exchange_modes": len(payload["exchange_catalog"]),
                },
            }
        )
        return payload

    @router.get("/v1/novatech/marketplace/status")
    async def marketplace_status(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.trust_marketplace(organization_id=organization_id)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_marketplace_status",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "service_count": payload["summary"]["service_count"],
                    "tenant_count": payload["summary"]["tenant_count"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/marketplace/services")
    async def marketplace_services(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.trust_marketplace_services(organization_id=organization_id)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_marketplace_services",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "service_count": payload["service_count"],
                    "tenant_count": payload["tenant_count"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/marketplace/onboarding")
    async def marketplace_onboarding(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = control_plane.marketplace_onboarding_strategy(organization_id=organization_id)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_marketplace_onboarding",
                "organization_id": organization_id,
                "status": payload["status"],
                "summary": {
                    "service_count": payload["summary"]["service_count"],
                    "tenant_count": payload["summary"]["tenant_count"],
                    "phases": len(payload["phases"]),
                },
            }
        )
        return payload

    @router.get("/v1/novatech/intranet/analytics")
    async def intranet_analytics(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = {
            "view": "novatech_intranet_analytics",
            "product": "NovaTech Intranet",
            "organization_id": organization_id,
            "operator_analytics": control_plane.dashboard_analytics(
                organization_id=organization_id,
                source="afriride_operator_dashboard",
                limit=limit,
            ),
            "novaprogramming_insights": control_plane.insights(organization_id=organization_id),
            "novaprogramming_trust_trends": control_plane.trust_trends(organization_id=organization_id),
            "novaprogramming_risk_predictions": control_plane.risk_predictions(organization_id=organization_id),
            "read_only": True,
            "governance_linked": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_analytics",
                "organization_id": organization_id,
                "status": payload["operator_analytics"]["prediction"]["risk_level"],
                "summary": {
                    "latest_trust_score": payload["operator_analytics"]["latest"]["trust_score"]
                    if payload["operator_analytics"]["latest"]
                    else None,
                    "latest_evidence_coverage": payload["operator_analytics"]["latest"]["evidence_coverage"]
                    if payload["operator_analytics"]["latest"]
                    else None,
                },
            }
        )
        return payload

    @router.get("/v1/novatech/intranet/decisions")
    async def intranet_decisions(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = {
            "view": "novatech_intranet_decisions",
            "product": "NovaTech Intranet",
            "organization_id": organization_id,
            "operator_decisions": control_plane.dashboard_decisions(
                organization_id=organization_id,
                source="afriride_operator_dashboard",
                limit=limit,
            ),
            "novaprogramming_risk_predictions": control_plane.risk_predictions(organization_id=organization_id),
            "read_only": True,
            "governance_linked": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_decisions",
                "organization_id": organization_id,
                "status": payload["operator_decisions"]["current"]["decision_lane"],
                "summary": {
                    "current_action": payload["operator_decisions"]["current"]["decision_action"],
                    "priority": payload["operator_decisions"]["current"]["decision_priority"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/intranet/actions")
    async def intranet_actions(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        payload = {
            "view": "novatech_intranet_actions",
            "product": "NovaTech Intranet",
            "organization_id": organization_id,
            "operator_actions": control_plane.dashboard_actions(
                organization_id=organization_id,
                source="afriride_operator_dashboard",
                limit=limit,
            ),
            "operator_decisions": control_plane.dashboard_decisions(
                organization_id=organization_id,
                source="afriride_operator_dashboard",
                limit=limit,
            ),
            "novaprogramming_risk_predictions": control_plane.risk_predictions(organization_id=organization_id),
            "read_only": True,
            "governance_linked": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_intranet_actions",
                "organization_id": organization_id,
                "status": payload["operator_actions"]["current"]["quality_band"],
                "summary": {
                    "control_signal": payload["operator_actions"]["current"]["control_signal"],
                    "calibrated_confidence": payload["operator_actions"]["current"]["calibrated_confidence"],
                },
            }
        )
        return payload

    return router


def _internal_links() -> list[dict[str, str]]:
    return [
        {"label": "NovaScript Dashboard", "path": "/v1/novascript/dashboard"},
        {"label": "NovaProgramming Dashboard", "path": "/v1/novaprogramming/dashboard"},
        {"label": "NovaProgramming Analytics", "path": "/v1/novaprogramming/analytics"},
        {"label": "NovaProgramming Decisions", "path": "/v1/novaprogramming/decisions"},
        {"label": "Operator Analytics", "path": "/v1/operator/analytics"},
        {"label": "Operator Decisions", "path": "/v1/operator/decisions"},
        {"label": "Operator Actions", "path": "/v1/operator/actions"},
        {"label": "NovaTech Analytics", "path": "/v1/novatech/intranet/analytics"},
        {"label": "NovaTech Decisions", "path": "/v1/novatech/intranet/decisions"},
        {"label": "NovaTech Actions", "path": "/v1/novatech/intranet/actions"},
        {"label": "NovaTech Platform", "path": "/v1/novatech/intranet/platform"},
        {"label": "NovaTech Extranet", "path": "/v1/novatech/extranet/status"},
        {"label": "NovaTech Knowledge", "path": "/v1/novatech/intranet/knowledge"},
        {"label": "NovaTech Workflows", "path": "/v1/novatech/intranet/workflows"},
        {"label": "NovaTech Comms", "path": "/v1/novatech/intranet/comms"},
        {"label": "NovaTech SaaS", "path": "/v1/novatech/saas/status"},
        {"label": "NovaTech Organizations", "path": "/v1/novatech/organizations"},
        {"label": "NovaTech Outcomes", "path": "/v1/novatech/outcomes/status"},
        {"label": "NovaTech Trust Network", "path": "/v1/novatech/trust-network/status"},
        {"label": "NovaTech Marketplace", "path": "/v1/novatech/marketplace/status"},
        {
            "label": "Controlled Execution Activation",
            "path": "/v1/novatech/organizations/{organization_id}/execution/activation",
        },
        {"label": "Marketplace Onboarding", "path": "/v1/novatech/marketplace/onboarding"},
        {"label": "Dashboard Gateway", "path": "/v1/dashboard/gateway"},
        {"label": "Public Trust Dashboard", "path": "/public/trust/dashboard"},
        {"label": "Public Verification Portal", "path": "/public/verify/portal"},
        {"label": "Ops Observability", "path": "/v1/ops/observability/dashboard"},
        {"label": "NovaTech Extranet Portal", "path": "/novatech/extranet/"},
    ]


def _build_novatech_platform_payload(
    *,
    organization_id: str,
    role: str,
    project_id: str,
) -> dict[str, Any]:
    intranet = _build_intranet_surface(organization_id=organization_id, role=role, project_id=project_id)
    extranet = _build_extranet_surface(organization_id=organization_id)
    knowledge = _build_knowledge_surface(organization_id=organization_id, project_id=project_id)
    workflows = _build_workflow_surface(organization_id=organization_id, limit=24)
    comms = _build_comms_surface(organization_id=organization_id, limit=24)
    return {
        "view": "novatech_intranet_platform",
        "product": "NovaTech Platform",
        "organization_id": organization_id,
        "status": "ready",
        "surfaces": {
            "intranet": intranet,
            "extranet": extranet,
            "knowledge": knowledge,
            "workflows": workflows,
            "comms": comms,
        },
        "routes": [
            {"label": "Intranet", "path": "/novatech/intranet/"},
            {"label": "Extranet", "path": "/novatech/extranet/status"},
            {"label": "Knowledge", "path": "/v1/novatech/intranet/knowledge"},
            {"label": "Workflows", "path": "/v1/novatech/intranet/workflows"},
            {"label": "Comms", "path": "/v1/novatech/intranet/comms"},
            {"label": "SaaS", "path": "/v1/novatech/saas/status"},
            {"label": "Organizations", "path": "/v1/novatech/organizations"},
            {"label": "Outcomes", "path": "/v1/novatech/outcomes/status"},
            {"label": "Trust Network", "path": "/v1/novatech/trust-network/status"},
            {"label": "Marketplace", "path": "/v1/novatech/marketplace/status"},
            {"label": "Controlled Execution", "path": "/v1/novatech/organizations/{organization_id}/execution/activation"},
            {"label": "Marketplace Onboarding", "path": "/v1/novatech/marketplace/onboarding"},
        ],
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_intranet_surface(
    *,
    organization_id: str,
    role: str,
    project_id: str,
) -> dict[str, Any]:
    control_plane = get_control_plane()
    novascript = get_novascript_service()
    return {
        "view": "novatech_intranet_surface",
        "title": "NovaTech Intranet",
        "status": "ready",
        "organization_id": organization_id,
        "role": role,
        "route": "/novatech/intranet/",
        "summary": "Internal collaboration, governed engineering, analytics, decisions, and control.",
        "dashboards": {
            "novascript": "/v1/novascript/dashboard",
            "novaprogramming": "/v1/novaprogramming/dashboard",
            "operator": "/v1/operator/dashboard",
            "analytics": "/v1/novatech/intranet/analytics",
            "decisions": "/v1/novatech/intranet/decisions",
            "actions": "/v1/novatech/intranet/actions",
            "workflows": "/v1/novatech/intranet/workflows",
            "outcomes": "/v1/novatech/outcomes/status",
            "trust_network": "/v1/novatech/trust-network/status",
            "marketplace": "/v1/novatech/marketplace/status",
            "controlled_execution": "/v1/novatech/organizations/{organization_id}/execution/activation",
            "marketplace_onboarding": "/v1/novatech/marketplace/onboarding",
        },
        "staff_dashboard": control_plane.staff_dashboard(
            role=role,
            project_id=project_id,
            organization_id=organization_id,
        ),
        "novascript": {
            "status": novascript.status(organization_id=organization_id),
            "catalog": novascript.catalog(organization_id=organization_id),
            "risk_dashboard": novascript.organization_risk_dashboard(organization_id=organization_id),
        },
        "novaprogramming": {
            "status": control_plane.status(organization_id=organization_id),
            "catalog": control_plane.catalog(organization_id=organization_id),
            "metrics": control_plane.metrics(organization_id=organization_id),
            "trust": control_plane.trust(organization_id=organization_id),
        },
        "outcomes": control_plane.outcome_status(organization_id=organization_id, limit=24),
        "trust_network": control_plane.federated_trust_network(organization_id=organization_id),
        "marketplace": control_plane.trust_marketplace(organization_id=organization_id),
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_extranet_surface(*, organization_id: str) -> dict[str, Any]:
    return {
        "view": "novatech_extranet_surface",
        "title": "NovaTech Extranet",
        "status": "ready",
        "organization_id": organization_id,
        "route": "/novatech/extranet/",
        "summary": "External partner, client, supplier, and investor visibility with bounded proof surfaces.",
        "audiences": [
            "CLIENT",
            "PARTNER",
            "SUPPLIER",
            "INVESTOR",
        ],
        "routes": [
            "/public/trust/dashboard",
            "/public/trust-badge",
            "/public/registry",
            "/public/verify/portal",
            "/public/partners/registry",
            "/v1/dashboard/gateway",
        ],
        "public_verification": {
            "dashboard": "/public/trust/dashboard",
            "badge": "/public/trust-badge",
            "registry": "/public/registry",
            "portal": "/public/verify/portal",
        },
        "partner_surface": {
            "dashboard_gateway": "/v1/dashboard/gateway",
            "partner_registry": "/public/partners/registry",
            "verification_surface": "/public/verify/portal",
        },
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_knowledge_surface(*, organization_id: str, project_id: str) -> dict[str, Any]:
    projects = render_projects_view()
    workspace = build_workspace_payload(
        prompt="Map NovaTech knowledge surfaces",
        mode="analysis",
        project_id=project_id,
    )
    files = workspace.get("project_explorer", [])
    return {
        "view": "novatech_knowledge_surface",
        "title": "NovaKnowledge",
        "status": "ready",
        "organization_id": organization_id,
        "route": "/v1/novatech/intranet/knowledge",
        "summary": "File, project, and workspace knowledge for internal engineering teams.",
        "project_count": len(projects.get("projects", [])),
        "file_count": len(files),
        "projects": projects.get("projects", []),
        "workspace": workspace,
        "document_roots": [
            "docs/architecture",
            "docs/mobile",
            "docs/operations",
            "afritech/afriprogramming",
        ],
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_workflow_surface(*, organization_id: str, limit: int) -> dict[str, Any]:
    control_plane = get_control_plane()
    workflows = control_plane.workflow_instances(organization_id=organization_id, limit=limit)
    workflow_items = list(workflows.get("workflows", []))
    state_counts: dict[str, int] = {}
    for workflow in workflow_items:
        state = str(workflow.get("state") or "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1
    return {
        "view": "novatech_workflow_surface",
        "title": "NovaWorkflow",
        "status": "ready",
        "organization_id": organization_id,
        "route": "/v1/novatech/intranet/workflows",
        "summary": "Controlled delivery, assurance, and federation workflows.",
        "workflow_count": len(workflow_items),
        "workflows": workflow_items,
        "templates": workflows.get("templates", []),
        "state_counts": state_counts,
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_comms_surface(*, organization_id: str, limit: int) -> dict[str, Any]:
    control_plane = get_control_plane()
    audit_log = control_plane.audit_log(organization_id=organization_id)
    entries = list(audit_log.get("entries", []))[:limit]
    channels = [
        {
            "name": "operations",
            "purpose": "platform ops, trust, and incident coordination",
        },
        {
            "name": "engineering",
            "purpose": "delivery, workflow, and code review coordination",
        },
        {
            "name": "alerts",
            "purpose": "live risk, replay, and evidence notifications",
        },
        {
            "name": "partners",
            "purpose": "external trust and onboarding messages",
        },
        {
            "name": "support",
            "purpose": "help desk and operator follow-up",
        },
    ]
    messages = [_audit_event_to_message(entry) for entry in entries]
    return {
        "view": "novatech_comms_surface",
        "title": "NovaComms",
        "status": "ready",
        "organization_id": organization_id,
        "route": "/v1/novatech/intranet/comms",
        "summary": "Read-only internal communications derived from audit and control-plane events.",
        "channels": channels,
        "message_count": len(messages),
        "messages": messages,
        "audit_log": audit_log,
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _tenant_source_maps() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    novascript = get_novascript_service()
    adoption_status = novascript.field_adoption_status()
    organization_map = {
        str(item.get("organization_id")): item
        for item in adoption_status.get("organizations", [])
        if str(item.get("organization_id") or "").strip()
    }
    certification_map = {
        str(item.get("organization_id")): item
        for item in adoption_status.get("certifications", [])
        if str(item.get("organization_id") or "").strip()
    }
    return adoption_status, organization_map, certification_map


def _tenant_record(
    *,
    organization_id: str,
    store_record: dict[str, Any] | None,
    adoption_record: dict[str, Any] | None,
    certification_record: dict[str, Any] | None,
    billing_record: dict[str, Any] | None,
) -> dict[str, Any]:
    organization_name = (
        (store_record or {}).get("organization_name")
        or (adoption_record or {}).get("legal_name")
        or organization_id
    )
    status = (adoption_record or {}).get("status") or (store_record or {}).get("status") or "discovered"
    certification_level = (certification_record or {}).get("level")
    certification_label = (certification_record or {}).get("label")
    trust_score = 0
    if certification_level == 3:
        trust_score = 96
    elif certification_level == 2:
        trust_score = 88
    elif certification_level == 1:
        trust_score = 80
    return {
        "organization_id": organization_id,
        "organization_name": organization_name,
        "legal_name": (adoption_record or {}).get("legal_name") or organization_name,
        "sector": (adoption_record or {}).get("sector") or "unknown",
        "trust_domain": (adoption_record or {}).get("trust_domain") or "tenant",
        "status": status,
        "source": "field_adoption" if adoption_record else "store",
        "tenant_model": "tenant_isolated",
        "trust_score": trust_score,
        "certification_level": certification_level,
        "certification_label": certification_label,
        "billing_plan": (billing_record or {}).get("plan") or "enterprise",
        "billing_status": (billing_record or {}).get("status") or "preview",
        "billing_enabled": bool((billing_record or {}).get("billing_enabled", False)),
        "billing_estimated_amount": float((billing_record or {}).get("estimated_amount", 0.0) or 0.0),
        "billing_usage_total": int((billing_record or {}).get("usage_total", 0) or 0),
        "created_at": (store_record or {}).get("created_at") or (adoption_record or {}).get("created_at"),
    }


def _build_organization_directory_surface(*, organization_id: str, limit: int) -> dict[str, Any]:
    control_plane = get_control_plane()
    store_directory = control_plane.organizations(limit=limit)
    adoption_status, adoption_map, certification_map = _tenant_source_maps()
    store_map = {
        str(item.get("organization_id")): item
        for item in store_directory.get("organizations", [])
        if str(item.get("organization_id") or "").strip()
    }
    tenant_ids = set(store_map) | set(adoption_map)
    if organization_id:
        tenant_ids.add(organization_id)

    tenants: list[dict[str, Any]] = []
    for tenant_id in sorted(tenant_ids):
        latest_billing = control_plane.billing_records(organization_id=tenant_id, limit=1)
        billing_record = latest_billing.get("billing_records", [])
        tenants.append(
            _tenant_record(
                organization_id=tenant_id,
                store_record=store_map.get(tenant_id),
                adoption_record=adoption_map.get(tenant_id),
                certification_record=certification_map.get(tenant_id),
                billing_record=billing_record[0] if billing_record else None,
            )
        )

    return {
        "view": "novatech_organization_directory",
        "product": "NovaTech SaaS",
        "organization_id": organization_id,
        "status": "ready",
        "organization_count": len(tenants),
        "certified_count": sum(1 for tenant in tenants if tenant.get("certification_level")),
        "tenants": tenants,
        "adoption": adoption_status,
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_organization_billing_surface(*, organization_id: str, limit: int) -> dict[str, Any]:
    control_plane = get_control_plane()
    billing_preview = control_plane.billing_preview(organization_id=organization_id)
    billing_history = control_plane.billing_records(organization_id=organization_id, limit=limit)
    estimated_amount = max(float(billing_preview["estimated_amount"] or 0.0), 79.0)
    billing_service = BillingService()
    subscription = billing_service.create_subscription(
        customer_id=organization_id,
        plan_name="enterprise",
        recurring_amount=Money.of(estimated_amount, "AUD"),
    )
    invoice = billing_service.generate_invoice(subscription)
    return {
        "view": "novatech_organization_billing",
        "product": "NovaTech SaaS",
        "organization_id": organization_id,
        "status": "ready",
        "summary": billing_preview,
        "billing_history": billing_history.get("billing_records", []),
        "subscription_preview": {
            "subscription_id": subscription.subscription_id,
            "customer_id": subscription.customer_id,
            "plan_name": subscription.plan_name,
            "recurring_amount": subscription.recurring_amount.canonical(),
            "status": subscription.status,
            "next_billing_at": subscription.next_billing_at.replace(microsecond=0).isoformat(),
        },
        "invoice_preview": {
            "invoice_id": invoice.invoice_id,
            "customer_id": invoice.customer_id,
            "amount": invoice.amount.canonical(),
            "status": invoice.status,
            "due_at": invoice.due_at.replace(microsecond=0).isoformat(),
        },
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_safe_execution_surface(*, organization_id: str, limit: int) -> dict[str, Any]:
    control_plane = get_control_plane()
    billing = _build_organization_billing_surface(organization_id=organization_id, limit=limit)
    directory = _build_organization_directory_surface(organization_id=organization_id, limit=limit)
    tenants = directory.get("tenants", [])
    current_tenant = next((tenant for tenant in tenants if tenant["organization_id"] == organization_id), None)
    action_surface = control_plane.dashboard_actions(
        organization_id=organization_id,
        source="novatech_saas_safe_execution",
        limit=limit,
    )
    current_action = action_surface.get("current", {})
    tenant_ready = bool(current_tenant and current_tenant.get("status") in {"active", "pilot_ready", "certified"})
    billing_ready = bool(billing["subscription_preview"]["status"] == "active")
    safe_execution_enabled = (
        tenant_ready
        and billing_ready
        and bool(current_action.get("execution_tier_ready"))
        and current_action.get("safety_gate") == "pass"
    )
    reasons = [
        f"tenant status: {(current_tenant or {}).get('status', 'discovered')}",
        f"billing status: {billing['summary'].get('billing_enabled', False) and 'enabled' or 'preview'}",
        f"execution tier: {current_action.get('execution_tier', 'advisory')}",
        f"safety gate: {current_action.get('safety_gate', 'hold')}",
    ]
    return {
        "view": "novatech_safe_execution",
        "product": "NovaTech SaaS",
        "organization_id": organization_id,
        "status": "ready" if safe_execution_enabled else "hold",
        "tenant": current_tenant
        or {
            "organization_id": organization_id,
            "organization_name": organization_id,
            "status": "implicit",
            "source": "claim",
            "tenant_model": "tenant_isolated",
        },
        "billing": billing,
        "execution": {
            "action_lane": current_action.get("action_lane", "monitor"),
            "action_mode": current_action.get("action_mode", "guided_control"),
            "action_priority": current_action.get("action_priority", "low"),
            "action_summary": current_action.get("action_summary", ""),
            "control_signal": current_action.get("control_signal", "maintain_monitoring"),
            "safety_gate": current_action.get("safety_gate", "hold"),
            "automation_tier": current_action.get("automation_tier", 0),
            "execution_tier": current_action.get("execution_tier", "advisory"),
            "execution_tier_ready": bool(current_action.get("execution_tier_ready", False)),
            "execution_tier_summary": current_action.get("execution_tier_summary", ""),
            "execution_tier_controls": current_action.get("execution_tier_controls", []),
            "decision_quality_score": current_action.get("decision_quality_score", 0),
            "calibrated_confidence": current_action.get("calibrated_confidence", 0),
            "safe_execution_enabled": safe_execution_enabled,
            "allowed": False,
            "advisory_only": True,
            "execution_authority": False,
            "read_only": True,
            "projection_only": True,
            "control_actions": current_action.get("control_actions", []),
            "operator_guidance": current_action.get("operator_guidance", []),
            "recommended_actions": current_action.get("recommended_actions", []),
            "watch_items": current_action.get("watch_items", []),
            "reasoning": current_action.get("reasoning", {}),
            "readiness": {
                "tenant_ready": tenant_ready,
                "billing_ready": billing_ready,
                "execution_tier_ready": bool(current_action.get("execution_tier_ready", False)),
                "safety_gate": current_action.get("safety_gate", "hold"),
            },
        },
        "reasons": reasons,
        "tenant_count": len(tenants),
        "organization_count": directory.get("organization_count", len(tenants)),
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_organization_detail_surface(
    *,
    organization_id: str,
    requester_organization_id: str,
    limit: int,
) -> dict[str, Any]:
    control_plane = get_control_plane()
    novascript = get_novascript_service()
    directory = _build_organization_directory_surface(organization_id=organization_id, limit=limit)
    tenant = next(
        (item for item in directory.get("tenants", []) if item["organization_id"] == organization_id),
        directory.get("tenants", [None])[0] if directory.get("tenants") else None,
    )
    safe_execution_surface = _build_safe_execution_surface(organization_id=organization_id, limit=limit)
    return {
        "view": "novatech_organization_detail",
        "product": "NovaTech SaaS",
        "organization_id": organization_id,
        "requester_organization_id": requester_organization_id,
        "status": "ready",
        "tenant": tenant,
        "platform": {
            "status": control_plane.status(organization_id=organization_id),
            "metrics": control_plane.metrics(organization_id=organization_id),
            "trust": control_plane.trust(organization_id=organization_id),
            "risk_dashboard": novascript.organization_risk_dashboard(organization_id=organization_id),
            "platform_integrations": novascript.platform_integrations(organization_id=organization_id),
        },
        "billing": _build_organization_billing_surface(organization_id=organization_id, limit=limit),
        "safe_execution": safe_execution_surface["execution"],
        "safe_execution_surface": safe_execution_surface,
        "directory": directory,
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _build_saas_surface(*, organization_id: str, limit: int) -> dict[str, Any]:
    directory = _build_organization_directory_surface(organization_id=organization_id, limit=limit)
    billing = _build_organization_billing_surface(organization_id=organization_id, limit=limit)
    safe_execution = _build_safe_execution_surface(organization_id=organization_id, limit=limit)
    return {
        "view": "novatech_saas_status",
        "product": "NovaTech SaaS",
        "organization_id": organization_id,
        "status": "ready" if safe_execution["execution"]["safe_execution_enabled"] else "hold",
        "tenancy_model": "multi_tenant",
        "tenant_count": directory["organization_count"],
        "directory": directory,
        "organizations": directory["tenants"],
        "billing": billing["summary"],
        "billing_surface": billing,
        "safe_execution": safe_execution["execution"],
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _audit_event_to_message(event: dict[str, Any]) -> dict[str, Any]:
    event_type = str(event.get("event_type") or "audit.event")
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    channel = _channel_for_event(event_type, payload)
    detail = (
        payload.get("summary")
        if isinstance(payload.get("summary"), str)
        else payload.get("message")
        if isinstance(payload.get("message"), str)
        else payload.get("title")
        if isinstance(payload.get("title"), str)
        else f"{event_type} -> {event.get('status')}"
    )
    return {
        "channel": channel,
        "title": event_type.replace(".", " ").replace("_", " ").title(),
        "detail": detail,
        "status": event.get("status"),
        "actor_role": event.get("actor_role"),
        "actor_user_id": event.get("actor_user_id"),
        "target": event.get("target"),
        "created_at": event.get("created_at"),
    }


def _channel_for_event(event_type: str, payload: dict[str, Any]) -> str:
    lowered = event_type.lower()
    if "workflow" in lowered or "workflow" in str(payload.get("source", "")).lower():
        return "workflows"
    if "deploy" in lowered or "cloud" in lowered or "release" in lowered:
        return "engineering"
    if "partner" in lowered or "registry" in lowered or "federation" in lowered:
        return "partners"
    if "trust" in lowered or "governance" in lowered or "audit" in lowered:
        return "operations"
    if "alert" in lowered or "warning" in lowered or "exception" in lowered:
        return "alerts"
    return "operations"


def _render_extranet_html() -> str:
    links = "".join(
        f'<li><a href="{escape(item["path"])}">{escape(item["label"])}</a></li>'
        for item in [
            {"label": "Public Trust Dashboard", "path": "/public/trust/dashboard"},
            {"label": "Public Verification Portal", "path": "/public/verify/portal"},
            {"label": "Public Registry", "path": "/public/registry"},
            {"label": "Partner Registry", "path": "/public/partners/registry"},
            {"label": "Dashboard Gateway", "path": "/v1/dashboard/gateway"},
            {"label": "NovaTech Intranet", "path": "/novatech/intranet/"},
        ]
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>NovaTech Extranet</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f4f7fb;
        --surface: #ffffff;
        --ink: #122033;
        --muted: #5d6b7f;
        --line: #d8e1ea;
        --trust: #185b8c;
        --radius: 8px;
      }}
      body {{
        margin: 0;
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        background: var(--bg);
        color: var(--ink);
      }}
      main {{
        max-width: 1100px;
        margin: 0 auto;
        padding: 32px 20px 48px;
      }}
      .shell {{
        display: grid;
        gap: 20px;
      }}
      .hero, .panel {{
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        padding: 20px;
      }}
      h1 {{ margin: 0; font-size: 28px; }}
      .subtitle {{ margin-top: 8px; color: var(--muted); line-height: 1.5; max-width: 72ch; }}
      .grid {{
        display: grid;
        gap: 16px;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      }}
      h2 {{ margin: 0 0 12px; font-size: 18px; }}
      ul {{ margin: 0; padding-left: 18px; }}
      li {{ margin: 8px 0; }}
      a {{ color: var(--trust); text-decoration: none; }}
      .meta {{ color: var(--muted); font-size: 14px; }}
      code {{ background: #eef3f0; border-radius: 4px; padding: 2px 6px; }}
    </style>
  </head>
  <body>
    <main>
      <div class="shell">
        <section class="hero">
          <div class="meta">NovaTech external access surface</div>
          <h1>NovaTech Extranet</h1>
          <div class="subtitle">
            External customers, partners, suppliers, and investors receive bounded
            read-only access to public trust, verification, and registry surfaces.
            This portal does not expose execution authority.
          </div>
        </section>

        <section class="grid">
          <div class="panel">
            <h2>Public Surfaces</h2>
            <ul>{links}</ul>
          </div>
          <div class="panel">
            <h2>Access Model</h2>
            <div class="meta">Bounded external visibility</div>
            <ul>
              <li>Roles: <code>CLIENT</code>, <code>PARTNER</code>, <code>SUPPLIER</code>, <code>INVESTOR</code></li>
              <li>Mode: read-only portal</li>
              <li>Authority: public proof and verification only</li>
            </ul>
          </div>
        </section>
      </div>
    </main>
  </body>
</html>"""


def _render_intranet_html() -> str:
    links = "".join(
        f'<li><a href="{escape(item["path"])}">{escape(item["label"])}</a></li>'
        for item in _internal_links()
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>NovaTech Intranet</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f4f7f6;
        --surface: #ffffff;
        --ink: #101820;
        --muted: #60706a;
        --line: #d9e2dd;
        --trust: #116b4a;
        --radius: 8px;
      }}
      body {{
        margin: 0;
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        background: var(--bg);
        color: var(--ink);
      }}
      main {{
        max-width: 1100px;
        margin: 0 auto;
        padding: 32px 20px 48px;
      }}
      .shell {{
        display: grid;
        gap: 20px;
      }}
      .hero, .panel {{
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        padding: 20px;
      }}
      h1 {{ margin: 0; font-size: 28px; }}
      .subtitle {{ margin-top: 8px; color: var(--muted); line-height: 1.5; max-width: 72ch; }}
      .grid {{
        display: grid;
        gap: 16px;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      }}
      h2 {{ margin: 0 0 12px; font-size: 18px; }}
      ul {{ margin: 0; padding-left: 18px; }}
      li {{ margin: 8px 0; }}
      a {{ color: var(--trust); text-decoration: none; }}
      .meta {{ color: var(--muted); font-size: 14px; }}
      code {{ background: #eef3f0; border-radius: 4px; padding: 2px 6px; }}
    </style>
  </head>
  <body>
    <main>
      <div class="shell">
        <section class="hero">
          <div class="meta">NovaTech internal portal</div>
          <h1>NovaTech Intranet</h1>
          <div class="subtitle">
            Internal read-only entrypoint for NovaScript and NovaProgramming. It aggregates
            engineering intelligence, governed operations, and trusted internal dashboards
            without creating new authority over the underlying systems.
          </div>
        </section>

        <section class="grid">
          <div class="panel">
            <h2>Core Dashboards</h2>
            <ul>{links}</ul>
          </div>
          <div class="panel">
            <h2>Access Model</h2>
            <div class="meta">Authenticated staff only</div>
            <ul>
              <li>Roles: <code>OPERATOR</code>, <code>VERIFIER</code>, <code>OBSERVER</code>, <code>DEVELOPER</code></li>
              <li>Mode: read-only portal</li>
              <li>Authority: dashboards only, no execution control</li>
            </ul>
          </div>
        </section>
      </div>
    </main>
  </body>
</html>"""


__all__ = ["build_novatech_intranet_router"]
