"""NovaTech documentation compliance and certification API."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.api.realtime.dashboard_bus import publish_dashboard_snapshot
from afritech.afriprogramming.control_plane import get_control_plane
from afritech.afriprogramming.persistence import get_platform_store
from afritech.docs.document_system import (
    COMPLIANCE_REGISTRY_PATH,
    GOVERNANCE_ROOT,
    REGISTRY_ROOT,
    ROOT as REPO_ROOT,
    build_documentation_compliance_registry,
    load_documentation_compliance_registry,
)


class DocumentationTrainingRecordRequest(BaseModel):
    organization_id: str | None = None
    manual_id: str = "NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2"
    manual_version: str = "2.0"
    role: str = "operator"
    trainee_user_id: str
    trainer_user_id: str = "training-admin"
    completion_status: str = "completed"
    assessment_score: int = 100
    evidence_count: int = 0
    notes: list[str] = Field(default_factory=list)


class DocumentationCertificationIssueRequest(BaseModel):
    organization_id: str | None = None
    certification_type: str = "DOCUMENTATION_COMPLIANCE_CERTIFICATION"


def build_documentation_compliance_router() -> APIRouter:
    router = APIRouter(tags=["novatech-documentation"])
    control_plane = get_control_plane()

    @router.get("/v1/novatech/documentation/status")
    async def documentation_status(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        bundle = _documentation_bundle()
        document_registry = bundle["document_registry"]
        compliance_registry = bundle["compliance_registry"]
        policy_registry = control_plane.policy_registry(organization_id=organization_id)
        policy_decisions = control_plane.policy_decisions(organization_id=organization_id)
        certification = control_plane.certification(organization_id=organization_id)
        trust = control_plane.trust(organization_id=organization_id)
        trust_risk = control_plane.trust_risk(organization_id=organization_id)
        trust_network = control_plane.federated_trust_network(organization_id=organization_id)
        training = _platform_store().operator_training_summary(organization_id=organization_id)
        assurance_status = control_plane.assurance_status(organization_id=organization_id)
        assurance_history = control_plane.assurance_history(organization_id=organization_id, limit=limit)
        assurance_report = control_plane.assurance_report(organization_id=organization_id)
        assurance_alerts = control_plane.assurance_alerts(organization_id=organization_id, limit=limit)
        marketplace = control_plane.trust_marketplace(organization_id=organization_id)
        onboarding = control_plane.marketplace_onboarding_strategy(organization_id=organization_id)
        organization_directory = control_plane.organizations(limit=limit)
        current_tenant = next(
            (
                tenant
                for tenant in organization_directory.get("organizations", [])
                if tenant.get("organization_id") == organization_id
            ),
            None,
        )

        payload = {
            "view": "novatech_documentation_compliance_status",
            "organization_id": organization_id,
            "status": "ready",
            "document_registry": document_registry,
            "compliance_registry": compliance_registry,
            "policy_registry": policy_registry,
            "policy_decisions": policy_decisions,
            "certification_registry": certification,
            "trust_registry": {
                "trust": trust,
                "risk": trust_risk,
                "network": trust_network,
            },
            "operator_training_records": training,
            "continuous_assurance_reports": {
                "status": assurance_status,
                "history": assurance_history,
                "report": assurance_report,
                "alerts": assurance_alerts,
            },
            "marketplace": marketplace,
            "marketplace_onboarding": onboarding,
            "organization_governance": {
                "directory": organization_directory,
                "current_tenant": current_tenant,
                "tenant_count": organization_directory.get("organization_count", len(organization_directory.get("organizations", []))),
                "directory_surface": "/v1/novatech/organizations",
                "detail_surface": f"/v1/novatech/organizations/{organization_id}",
                "billing_surface": f"/v1/novatech/organizations/{organization_id}/billing",
                "execution_surface": f"/v1/novatech/organizations/{organization_id}/execution",
                "execution_activation_surface": f"/v1/novatech/organizations/{organization_id}/execution/activation",
                "onboarding_surface": "/v1/novatech/organizations/onboard",
                "platform_surface": "/v1/novatech/intranet/platform",
                "public_verification_portal": "/public/verify/portal",
                "public_documentation_portal": "/public/documentation/portal",
            },
            "certification_issuance": {
                "issue_surface": "/v1/novatech/documentation/certification/issue",
                "registry_surface": "/v1/novatech/documentation/certification",
                "status": "issued" if certification.get("issued") else "review",
                "classification": certification.get("classification", "CONTROLLED_OPERATIONAL_STATE"),
                "trust_score": certification.get("trust_score", 0),
                "proof_count": certification.get("proof_count", 0),
                "receipt_count": certification.get("receipt_count", 0),
            },
            "public_verification": {
                "portal_surface": "/public/verify/portal",
                "documentation_portal_surface": "/public/documentation/portal",
                "documentation_verification_surface": f"/public/documentation/{organization_id}",
            },
            "summary": {
                "document_count": len(document_registry.get("documents", [])),
                "policy_count": policy_registry.get("count", 0),
                "certification_status": "issued" if certification.get("issued") else "review",
                "certification_classification": certification.get("classification", "CONTROLLED_OPERATIONAL_STATE"),
                "trust_score": trust.get("trust_score", 0),
                "training_completion_rate": training.get("completion_rate", 0.0),
                "assurance_status": assurance_status.get("assurance_status", "unknown"),
                "marketplace_services": marketplace.get("summary", {}).get("service_count", 0),
                "standard_protocol": compliance_registry.get("standard_protocol", {}).get("name", "AfriCPPT"),
                "tenant_count": organization_directory.get("organization_count", len(organization_directory.get("organizations", []))),
                "current_tenant_status": current_tenant.get("status", "unknown") if current_tenant else "unknown",
            },
            "read_only": True,
            "projection_only": True,
            "governance_linked": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_status",
                "organization_id": organization_id,
                "status": payload["summary"]["assurance_status"],
                "summary": payload["summary"],
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/registry")
    async def documentation_registry(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        bundle = _documentation_bundle()
        payload = {
            "view": "novatech_documentation_registry",
            "organization_id": organization_id,
            **bundle,
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_registry",
                "organization_id": organization_id,
                "status": payload["compliance_registry"]["status"],
                "summary": {
                    "document_count": len(payload["document_registry"].get("documents", [])),
                    "source_count": len(payload["compliance_registry"].get("source_documents", [])),
                },
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/policy")
    async def documentation_policy(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        policy_registry = control_plane.policy_registry(organization_id=organization_id)
        policy_decisions = control_plane.policy_decisions(organization_id=organization_id)
        payload = {
            "view": "novatech_documentation_policy",
            "organization_id": organization_id,
            "policy_registry": policy_registry,
            "policy_decisions": policy_decisions,
            "summary": {
                "policy_count": policy_registry.get("count", 0),
                "decision_count": policy_decisions.get("count", len(policy_decisions.get("decisions", []))),
            },
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_policy",
                "organization_id": organization_id,
                "status": "ready",
                "summary": payload["summary"],
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/certification")
    async def documentation_certification(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        certification = control_plane.certification(organization_id=organization_id)
        payload = {
            "view": "novatech_documentation_certification",
            "organization_id": organization_id,
            "certification_registry": certification,
            "summary": {
                "status": "issued" if certification.get("issued") else "review",
                "classification": certification.get("classification", "CONTROLLED_OPERATIONAL_STATE"),
                "trust_score": certification.get("trust_score", 0),
                "proof_count": certification.get("proof_count", 0),
                "receipt_count": certification.get("receipt_count", 0),
            },
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_certification",
                "organization_id": organization_id,
                "status": payload["summary"]["status"],
                "summary": payload["summary"],
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/trust")
    async def documentation_trust(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        trust = control_plane.trust(organization_id=organization_id)
        trust_risk = control_plane.trust_risk(organization_id=organization_id)
        trust_network = control_plane.federated_trust_network(organization_id=organization_id)
        payload = {
            "view": "novatech_documentation_trust",
            "organization_id": organization_id,
            "trust_registry": trust,
            "trust_risk": trust_risk,
            "trust_network": trust_network,
            "summary": {
                "trust_score": trust.get("trust_score", 0),
                "risk_level": trust_risk.get("risk_level", "unknown"),
                "member_count": trust_network.get("member_count", 0),
            },
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_trust",
                "organization_id": organization_id,
                "status": payload["summary"]["risk_level"],
                "summary": payload["summary"],
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/training")
    async def documentation_training(
        limit: int = 100,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        platform_store = _platform_store()
        summary = platform_store.operator_training_summary(organization_id=organization_id)
        records = platform_store.list_operator_training_records(organization_id=organization_id, limit=limit)
        payload = {
            "view": "novatech_documentation_training",
            "organization_id": organization_id,
            "training_summary": summary,
            "training_records": records,
            "summary": {
                "count": summary.get("count", 0),
                "completion_rate": summary.get("completion_rate", 0.0),
                "latest_manual_id": summary.get("latest", {}).get("manual_id") if summary.get("latest") else None,
            },
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_training",
                "organization_id": organization_id,
                "status": "ready",
                "summary": payload["summary"],
            }
        )
        return payload

    @router.post("/v1/novatech/documentation/training/record")
    async def documentation_training_record(
        body: DocumentationTrainingRecordRequest,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = body.organization_id or claims.organization_id
        platform_store = _platform_store()
        record = platform_store.store_operator_training_record(
            organization_id=organization_id,
            manual_id=body.manual_id,
            manual_version=body.manual_version,
            role=body.role,
            trainee_user_id=body.trainee_user_id,
            trainer_user_id=body.trainer_user_id,
            completion_status=body.completion_status,
            assessment_score=body.assessment_score,
            evidence_count=body.evidence_count,
            notes=body.notes,
        )
        summary = platform_store.operator_training_summary(organization_id=organization_id)
        payload = {
            "view": "novatech_documentation_training_record",
            "organization_id": organization_id,
            "record": record,
            "training_summary": summary,
            "status": "recorded",
            "read_only": False,
            "projection_only": False,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_training_record",
                "organization_id": organization_id,
                "status": "recorded",
                "summary": {
                    "manual_id": record["manual_id"],
                    "role": record["role"],
                    "completion_status": record["completion_status"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/assurance")
    async def documentation_assurance(
        limit: int = 100,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        status = control_plane.assurance_status(organization_id=organization_id)
        history = control_plane.assurance_history(organization_id=organization_id, limit=limit)
        report = control_plane.assurance_report(organization_id=organization_id)
        alerts = control_plane.assurance_alerts(organization_id=organization_id, limit=limit)
        payload = {
            "view": "novatech_documentation_assurance",
            "organization_id": organization_id,
            "status": status,
            "history": history,
            "report": report,
            "alerts": alerts,
            "summary": {
                "assurance_status": status.get("assurance_status", "unknown"),
                "history_count": history.get("count", len(history.get("runs", []))),
                "alert_count": alerts.get("count", len(alerts.get("alerts", []))),
            },
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_assurance",
                "organization_id": organization_id,
                "status": payload["summary"]["assurance_status"],
                "summary": payload["summary"],
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/marketplace")
    async def documentation_marketplace(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        marketplace = control_plane.trust_marketplace(organization_id=organization_id)
        services = control_plane.trust_marketplace_services(organization_id=organization_id)
        onboarding = control_plane.marketplace_onboarding_strategy(organization_id=organization_id)
        payload = {
            "view": "novatech_documentation_marketplace",
            "organization_id": organization_id,
            "marketplace": marketplace,
            "services": services,
            "onboarding": onboarding,
            "summary": {
                "service_count": marketplace.get("summary", {}).get("service_count", 0),
                "tenant_count": marketplace.get("summary", {}).get("tenant_count", 0),
                "trust_member_count": marketplace.get("summary", {}).get("trust_member_count", 0),
            },
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_marketplace",
                "organization_id": organization_id,
                "status": marketplace.get("status", "ready"),
                "summary": payload["summary"],
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/onboarding")
    async def documentation_onboarding(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        onboarding = control_plane.marketplace_onboarding_strategy(organization_id=organization_id)
        payload = {
            "view": "novatech_documentation_onboarding",
            "organization_id": organization_id,
            "onboarding": onboarding,
            "summary": {
                "phase_count": len(onboarding.get("phases", [])),
                "service_count": onboarding.get("summary", {}).get("service_count", 0),
                "tenant_count": onboarding.get("summary", {}).get("tenant_count", 0),
            },
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_onboarding",
                "organization_id": organization_id,
                "status": onboarding.get("status", "ready"),
                "summary": payload["summary"],
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/standard")
    async def documentation_standard(
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        bundle = _documentation_bundle()
        payload = {
            "view": "novatech_documentation_standard",
            "organization_id": organization_id,
            "standard_protocol": bundle["compliance_registry"].get("standard_protocol", {}),
            "positioning": bundle["compliance_registry"].get("positioning", {}),
            "read_only": True,
            "projection_only": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_standard",
                "organization_id": organization_id,
                "status": payload["standard_protocol"].get("name", "AfriCPPT"),
                "summary": {
                    "standard": payload["standard_protocol"].get("name", "AfriCPPT"),
                    "expansion": payload["standard_protocol"].get("expansion", ""),
                },
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/organizations")
    async def documentation_organizations(
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        payload = _organization_compliance_surface(organization_id=claims.organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_organizations",
                "organization_id": claims.organization_id,
                "status": payload["summary"]["certification_status"],
                "summary": {
                    "tenant_count": payload["summary"]["tenant_count"],
                    "trust_score": payload["summary"]["trust_score"],
                    "assurance_status": payload["summary"]["assurance_status"],
                },
            }
        )
        return payload

    @router.get("/v1/novatech/documentation/organizations/{organization_id}")
    async def documentation_organization(
        organization_id: str,
        limit: int = 24,
        claims = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
    ) -> dict[str, Any]:
        payload = _organization_compliance_surface(organization_id=organization_id, limit=limit)
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_organization",
                "organization_id": organization_id,
                "status": payload["summary"]["certification_status"],
                "summary": {
                    "tenant_count": payload["summary"]["tenant_count"],
                    "execution_tier": payload["organization_governance"]["execution_activation"]["activation"]["execution_tier"],
                    "public_verification_portal": payload["public_verification"]["portal_surface"],
                },
            }
        )
        return payload

    @router.post("/v1/novatech/documentation/certification/issue")
    async def documentation_certification_issue(
        body: DocumentationCertificationIssueRequest,
        claims = Depends(require_roles("VERIFIER")),
    ) -> dict[str, Any]:
        organization_id = body.organization_id or claims.organization_id
        certification_issue = control_plane.certification_issue(
            organization_id=organization_id,
            certification_type=body.certification_type,
            actor_user_id=claims.sub,
        )
        certification_record = certification_issue.get("certification", {})
        organization_payload = _organization_compliance_surface(organization_id=organization_id, limit=24)
        payload = {
            "view": "novatech_documentation_certification_issue",
            "organization_id": organization_id,
            "certification_issuance": {
                **certification_issue,
                "issue_surface": "/v1/novatech/documentation/certification/issue",
                "registry_surface": "/v1/novatech/documentation/certification",
                "summary": {
                    "status": "issued",
                    "certification_type": certification_record.get("certification_type", body.certification_type),
                    "classification": certification_record.get("classification", certification_record.get("certification_type", body.certification_type)),
                    "trust_score": certification_record.get("trust_score", 0),
                    "proof_count": certification_record.get("proof_count", 0),
                    "receipt_count": certification_record.get("receipt_count", 0),
                    "certification_hash": certification_record.get("certification_hash"),
                },
            },
            "organization_governance": organization_payload["organization_governance"],
            "public_verification": organization_payload["public_verification"],
            "status": "issued",
            "read_only": False,
            "projection_only": False,
            "governance_linked": True,
        }
        await publish_dashboard_snapshot(
            {
                "source": "novatech_documentation_certification_issue",
                "organization_id": organization_id,
                "status": "issued",
                "summary": {
                    "certification_type": certification_issue.get("certification_type"),
                    "classification": certification_issue.get("classification"),
                    "public_verification_portal": payload["public_verification"]["portal_surface"],
                },
            }
        )
        return payload

    @router.get("/public/documentation/portal", response_class=HTMLResponse)
    def public_documentation_portal() -> str:
        bundle = _documentation_bundle()
        return _documentation_public_portal_html(bundle["compliance_registry"])

    @router.get("/public/documentation/{organization_id}")
    def public_documentation_verification(
        organization_id: str,
        limit: int = 24,
    ) -> dict[str, Any]:
        payload = _organization_compliance_surface(organization_id=organization_id, limit=limit)
        certification = payload["certification_issuance"]
        return {
            "classification": "DOCUMENTATION_COMPLIANCE_PUBLIC_VERIFICATION",
            "organization_id": organization_id,
            "status": payload["summary"]["certification_status"],
            "document_registry": {
                "registry_id": payload["document_registry"].get("registry_id", "NOVATECH_DOCUMENT_REGISTRY_V1"),
                "document_count": payload["summary"]["document_count"],
                "standard_protocol": payload["summary"]["standard_protocol"],
            },
            "organization_governance": {
                "directory_surface": payload["organization_governance"]["directory_surface"],
                "detail_surface": payload["organization_governance"]["detail_surface"],
                "billing_surface": payload["organization_governance"]["billing_surface"],
                "execution_surface": payload["organization_governance"]["execution_surface"],
                "public_verification_portal": payload["organization_governance"]["public_verification_portal"],
            },
            "tenant_governance": {
                "tenant_count": payload["organization_governance"]["tenant_count"],
                "current_tenant": payload["organization_governance"]["current_tenant"],
                "billing_preview": payload["organization_governance"]["billing_preview"],
                "execution_activation": payload["organization_governance"]["execution_activation"],
            },
            "policy_registry": {
                "count": payload["policy_registry"].get("count", 0),
                "decision_count": payload["policy_decisions"].get("count", len(payload["policy_decisions"].get("decisions", []))),
            },
            "certification_issuance": {
                "status": certification["status"],
                "classification": certification["classification"],
                "trust_score": certification["trust_score"],
                "proof_count": certification["proof_count"],
                "receipt_count": certification["receipt_count"],
                "issue_surface": certification["issue_surface"],
            },
            "trust_registry": {
                "trust_score": payload["trust_registry"]["trust"].get("trust_score", 0),
                "risk_level": payload["trust_registry"]["risk"].get("risk_level", "unknown"),
                "member_count": payload["trust_registry"]["network"].get("member_count", 0),
            },
            "continuous_assurance": {
                "status": payload["continuous_assurance_reports"]["status"].get("assurance_status", "unknown"),
                "report_surface": "/v1/novatech/documentation/assurance",
                "history_count": payload["continuous_assurance_reports"]["history"].get("count", len(payload["continuous_assurance_reports"]["history"].get("runs", []))),
                "alert_count": payload["continuous_assurance_reports"]["alerts"].get("count", len(payload["continuous_assurance_reports"]["alerts"].get("alerts", []))),
            },
            "public_verification": payload["public_verification"],
            "marketplace": {
                "service_count": payload["marketplace"].get("summary", {}).get("service_count", 0),
                "tenant_count": payload["marketplace"].get("summary", {}).get("tenant_count", 0),
                "onboarding_surface": "/v1/novatech/documentation/onboarding",
            },
            "read_only": True,
            "projection_only": True,
        }

    return router


def _organization_compliance_surface(*, organization_id: str, limit: int) -> dict[str, Any]:
    bundle = _documentation_bundle()
    platform_store = _platform_store()
    organization_directory = get_control_plane().organizations(limit=limit)
    tenant_directory = get_control_plane().organizations(organization_id=organization_id, limit=limit)
    tenants = list(organization_directory.get("organizations", []))
    current_tenant = next(
        (tenant for tenant in tenants if tenant.get("organization_id") == organization_id),
        tenant_directory.get("organizations", [None])[0] if tenant_directory.get("organizations") else None,
    )
    policy_registry = get_control_plane().policy_registry(organization_id=organization_id)
    policy_decisions = get_control_plane().policy_decisions(organization_id=organization_id)
    certification = get_control_plane().certification(organization_id=organization_id)
    trust = get_control_plane().trust(organization_id=organization_id)
    trust_risk = get_control_plane().trust_risk(organization_id=organization_id)
    trust_network = get_control_plane().federated_trust_network(organization_id=organization_id)
    training = platform_store.operator_training_summary(organization_id=organization_id)
    assurance_status = get_control_plane().assurance_status(organization_id=organization_id)
    assurance_history = get_control_plane().assurance_history(organization_id=organization_id, limit=limit)
    assurance_report = get_control_plane().assurance_report(organization_id=organization_id)
    assurance_alerts = get_control_plane().assurance_alerts(organization_id=organization_id, limit=limit)
    marketplace = get_control_plane().trust_marketplace(organization_id=organization_id)
    onboarding = get_control_plane().marketplace_onboarding_strategy(organization_id=organization_id)
    billing = get_control_plane().billing_preview(organization_id=organization_id)
    execution_activation = get_control_plane().controlled_execution_activation(
        organization_id=organization_id,
        limit=limit,
    )
    return {
        "view": "novatech_documentation_organization_compliance",
        "organization_id": organization_id,
        "document_registry": bundle["document_registry"],
        "compliance_registry": bundle["compliance_registry"],
        "organization_governance": {
            "directory": organization_directory,
            "tenant_directory": tenant_directory,
            "current_tenant": current_tenant,
            "tenant_count": organization_directory.get("organization_count", len(tenants)),
            "directory_surface": "/v1/novatech/organizations",
            "detail_surface": f"/v1/novatech/organizations/{organization_id}",
            "billing_surface": f"/v1/novatech/organizations/{organization_id}/billing",
            "execution_surface": f"/v1/novatech/organizations/{organization_id}/execution",
            "execution_activation_surface": f"/v1/novatech/organizations/{organization_id}/execution/activation",
            "onboarding_surface": "/v1/novatech/organizations/onboard",
            "platform_surface": "/v1/novatech/intranet/platform",
            "public_verification_portal": "/public/verify/portal",
            "public_documentation_portal": "/public/documentation/portal",
            "billing_preview": billing,
            "execution_activation": execution_activation,
        },
        "policy_registry": policy_registry,
        "policy_decisions": policy_decisions,
        "certification_registry": certification,
        "certification_issuance": {
            "issue_surface": "/v1/novatech/documentation/certification/issue",
            "registry_surface": "/v1/novatech/documentation/certification",
            "status": "issued" if certification.get("issued") else "review",
            "classification": certification.get("classification", "CONTROLLED_OPERATIONAL_STATE"),
            "trust_score": certification.get("trust_score", 0),
            "proof_count": certification.get("proof_count", 0),
            "receipt_count": certification.get("receipt_count", 0),
        },
        "trust_registry": {
            "trust": trust,
            "risk": trust_risk,
            "network": trust_network,
        },
        "operator_training_records": training,
        "continuous_assurance_reports": {
            "status": assurance_status,
            "history": assurance_history,
            "report": assurance_report,
            "alerts": assurance_alerts,
        },
        "marketplace": marketplace,
        "marketplace_onboarding": onboarding,
        "public_verification": {
            "portal_surface": "/public/verify/portal",
            "documentation_portal_surface": "/public/documentation/portal",
            "documentation_verification_surface": f"/public/documentation/{organization_id}",
        },
        "summary": {
            "document_count": len(bundle["document_registry"].get("documents", [])),
            "policy_count": policy_registry.get("count", 0),
            "certification_status": "issued" if certification.get("issued") else "review",
            "certification_classification": certification.get("classification", "CONTROLLED_OPERATIONAL_STATE"),
            "trust_score": trust.get("trust_score", 0),
            "training_completion_rate": training.get("completion_rate", 0.0),
            "assurance_status": assurance_status.get("assurance_status", "unknown"),
            "marketplace_services": marketplace.get("summary", {}).get("service_count", 0),
            "standard_protocol": bundle["compliance_registry"].get("standard_protocol", {}).get("name", "AfriCPPT"),
            "tenant_count": organization_directory.get("organization_count", len(tenants)),
        },
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def _documentation_public_portal_html(compliance_registry: dict[str, Any]) -> str:
    standard_protocol = compliance_registry.get("standard_protocol", {})
    linked_surfaces = compliance_registry.get("linked_surfaces", {})
    organization_os = linked_surfaces.get("organization_os", {})
    tenant_governance = linked_surfaces.get("tenant_governance", {})
    certification_registry = linked_surfaces.get("certification_registry", {})
    public_verification_portal = linked_surfaces.get("public_verification_portal", {})
    marketplace = linked_surfaces.get("marketplace", {})
    return f"""<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <title>NovaTech Documentation Compliance Portal</title>
    <style>
      :root {{ color-scheme: light; }}
      body {{ font-family: Inter, Arial, sans-serif; margin: 0; background: #f6f8fb; color: #152130; }}
      main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 56px; }}
      header {{ padding: 24px 0 16px; }}
      h1 {{ margin: 0 0 8px; font-size: 30px; }}
      p {{ line-height: 1.55; }}
      .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
      .panel {{ background: #fff; border: 1px solid #d7e0ea; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(16,24,40,.05); }}
      .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #66788b; margin-bottom: 8px; }}
      a {{ color: #1f5aa6; text-decoration: none; }}
      ul {{ margin: 8px 0 0 18px; }}
      code {{ background: #eef3f7; padding: 2px 6px; border-radius: 4px; }}
      .status {{ display: inline-block; padding: 4px 10px; border-radius: 999px; background: #e8f5ed; color: #1a6b42; font-weight: 600; }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div class='status'>Read-only compliance portal</div>
        <h1>NovaTech Documentation Compliance Portal</h1>
        <p>Documentation is certified, governed, and linked to the Organization OS, tenant governance, certification issuance, and public verification surfaces.</p>
      </header>
      <section class='grid'>
        <div class='panel'>
          <div class='label'>Standard protocol</div>
          <p><strong>{escape(str(standard_protocol.get("name", "AfriCPPT")))}</strong></p>
          <p>{escape(str(standard_protocol.get("expansion", "Global standard protocol for proof, compliance, and trust portability")))}</p>
          <p><code>{escape(str(standard_protocol.get("publication_surface", "/v1/novatech/documentation/standard")))}</code></p>
        </div>
        <div class='panel'>
          <div class='label'>Organization OS</div>
          <ul>
            <li><a href='{escape(str(organization_os.get("api_surface", "/v1/novatech/intranet/platform")))}'>Organization platform</a></li>
            <li><a href='{escape(str(organization_os.get("directory_surface", "/v1/novatech/organizations")))}'>Organization directory</a></li>
            <li><a href='{escape(str(tenant_governance.get("api_surface", "/v1/novatech/organizations/{organization_id}")))}'>Tenant governance detail</a></li>
            <li><a href='{escape(str(tenant_governance.get("billing_surface", "/v1/novatech/organizations/{organization_id}/billing")))}'>Billing governance</a></li>
            <li><a href='{escape(str(tenant_governance.get("execution_surface", "/v1/novatech/organizations/{organization_id}/execution")))}'>Execution governance</a></li>
          </ul>
        </div>
        <div class='panel'>
          <div class='label'>Certification and verification</div>
          <ul>
            <li><a href='{escape(str(certification_registry.get("api_surface", "/v1/novatech/documentation/certification")))}'>Certification registry</a></li>
            <li><a href='{escape(str(certification_registry.get("issuance_surface", "/v1/novatech/documentation/certification/issue")))}'>Certification issuance</a></li>
            <li><a href='{escape(str(public_verification_portal.get("portal_surface", "/public/verify/portal")))}'>Public verification portal</a></li>
            <li><a href='{escape(str(public_verification_portal.get("documentation_portal_surface", "/public/documentation/portal")))}'>Documentation verification portal</a></li>
            <li><code>{escape(str(public_verification_portal.get("verification_surface", "/public/documentation/{organization_id}")))}</code></li>
          </ul>
        </div>
        <div class='panel'>
          <div class='label'>Marketplace integration</div>
          <ul>
            <li><a href='{escape(str(marketplace.get("api_surface", "/v1/novatech/documentation/marketplace")))}'>Documentation marketplace</a></li>
            <li><a href='{escape(str(marketplace.get("onboarding_surface", "/v1/novatech/documentation/onboarding")))}'>Partner onboarding</a></li>
            <li><a href='/v1/novatech/documentation/status'>Documentation status</a></li>
            <li><a href='/v1/novatech/documentation/registry'>Documentation registry</a></li>
          </ul>
        </div>
      </section>
    </main>
  </body>
</html>"""


def _documentation_bundle() -> dict[str, Any]:
    document_registry_path = REGISTRY_ROOT / "DOCUMENT_REGISTRY.yaml"
    if document_registry_path.exists():
        document_registry = yaml.safe_load(document_registry_path.read_text(encoding="utf-8")) or {}
    else:
        document_registry = {"registry_id": "NOVATECH_DOCUMENT_REGISTRY_V1", "status": "ACTIVE", "documents": []}
    compliance_registry_path = COMPLIANCE_REGISTRY_PATH
    if compliance_registry_path.exists():
        compliance_registry = load_documentation_compliance_registry() or {}
    else:
        documents = list(document_registry.get("documents", []))
        full_reference = _full_reference_path(document_registry)
        compliance_registry = build_documentation_compliance_registry(
            registry_entries=documents,
            full_reference_path=full_reference,
        )
    return {
        "document_registry": document_registry,
        "compliance_registry": compliance_registry,
    }


def _platform_store():
    return get_platform_store()


def _full_reference_path(document_registry: dict[str, Any]) -> Path:
    for item in document_registry.get("documents", []):
        if item.get("profile") == "full_reference":
            output = Path(item["output"])
            return output if output.is_absolute() else REPO_ROOT / output
    return GOVERNANCE_ROOT / "NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2.md"
