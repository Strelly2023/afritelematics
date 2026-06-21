"""FastAPI router for the NovaScript assistant product."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.afriprogramming.roles import Role
from afritech.novascript import (
    NovaScriptArchitectureRequest,
    NovaScriptDebugRequest,
    NovaScriptDocsRequest,
    NovaScriptExplainRequest,
    NovaScriptGenerateRequest,
    NovaScriptTestRequest,
    get_novascript_service,
)


def build_novascript_router() -> APIRouter:
    service = get_novascript_service()
    router = APIRouter(prefix="/v1/novascript", tags=["novascript"])

    @router.get("/status")
    def status(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.status(organization_id=claims.organization_id)

    @router.get("/model/status")
    def model_status(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.model_status(organization_id=claims.organization_id)

    @router.get("/dashboard")
    def dashboard(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        organization_id = claims.organization_id
        status = service.status(organization_id=organization_id)
        catalog = service.catalog(organization_id=organization_id)
        risk = service.organization_risk_dashboard(organization_id=organization_id)
        trust_graph = service.trust_graph()
        trust_status = service.global_trust_status()
        integrations = service.platform_integrations(organization_id=organization_id)
        adoption = service.field_adoption_status()
        assurance = service.model_status(organization_id=organization_id)
        certification = service.standard_profile_status()
        return {
            "view": "novascript_dashboard",
            "organization_id": organization_id,
            "status": status,
            "catalog": catalog,
            "risk_dashboard": risk,
            "trust_graph": trust_graph,
            "global_trust": trust_status,
            "platform_integrations": integrations,
            "field_adoption": adoption,
            "assurance": assurance,
            "standard_profile": certification,
            "read_only": True,
            "governance_linked": True,
        }

    @router.get("/catalog")
    def catalog(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.catalog(organization_id=claims.organization_id)

    @router.get("/prompts")
    def prompts(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> list[dict[str, Any]]:
        return service.prompt_catalog()

    @router.get("/context/{project_id}")
    def context(
        project_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.project_context(project_id, organization_id=claims.organization_id)

    @router.get("/memory/{project_id}")
    def memory(
        project_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.memory_snapshot(project_id=project_id, organization_id=claims.organization_id)

    @router.post("/generate")
    def generate(
        body: NovaScriptGenerateRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.generate(
            prompt=body.prompt,
            project_id=body.project_id,
            language=body.language,
            mode=body.mode,
            organization_id=claims.organization_id,
        )

    @router.post("/explain")
    def explain(
        body: NovaScriptExplainRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.explain(
            code=body.code,
            context=body.context,
            organization_id=claims.organization_id,
        )

    @router.post("/debug")
    def debug(
        body: NovaScriptDebugRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.debug(
            code=body.code,
            error=body.error,
            context=body.context,
            organization_id=claims.organization_id,
        )

    @router.post("/architecture")
    def architecture(
        body: NovaScriptArchitectureRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.architecture(
            description=body.description,
            stack=body.stack,
            organization_id=claims.organization_id,
        )

    @router.post("/tests")
    def tests(
        body: NovaScriptTestRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.tests(
            target=body.target,
            framework=body.framework,
            organization_id=claims.organization_id,
        )

    @router.post("/docs")
    def docs(
        body: NovaScriptDocsRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.docs(
            topic=body.topic,
            audience=body.audience,
            format=body.format,
            metadata=body.metadata,
            organization_id=claims.organization_id,
        )

    @router.post("/receipts/verify")
    def verify_receipt(
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.verify_receipt(body)

    @router.post("/audit/verify")
    def audit_verify(
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.verify_audit_package(body)

    @router.post("/validate/artifact")
    def validate_artifact(
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.validate_artifact(body)

    @router.post("/policies")
    def policy_register(
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        source = str(body.get("source", "")).strip()
        if not source:
            raise HTTPException(status_code=400, detail="source required")
        try:
            return service.register_policy(source)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/policies/{policy_id}/transition")
    def policy_transition(
        policy_id: str,
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        try:
            return service.transition_policy(policy_id=policy_id, status=str(body.get("status", "")))
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/receipts/{project_id}")
    def receipts(
        project_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> list[dict[str, Any]]:
        return service.receipt_history(project_id=project_id, organization_id=claims.organization_id)

    @router.get("/trust/{project_id}/analytics")
    def trust_analytics(
        project_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.trust_analytics(project_id=project_id, organization_id=claims.organization_id)

    @router.get("/federation/status")
    def federation_status(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.federation_status()

    @router.get("/trust/global")
    def global_trust(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.global_trust_status()

    @router.get("/trust/graph")
    def trust_graph(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.trust_graph()

    @router.get("/risk/dashboard")
    def risk_dashboard(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.organization_risk_dashboard(organization_id=claims.organization_id)

    @router.get("/standard/profile")
    def standard_profile(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.standard_profile_status()

    @router.get("/integrations")
    def platform_integrations(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.platform_integrations(organization_id=claims.organization_id)

    @router.post("/integrations")
    def platform_integration_register(
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        scopes = body.get("scopes", [])
        if not isinstance(scopes, list):
            raise HTTPException(status_code=400, detail="scopes must be a list")
        integration_name = str(body.get("integration_name", "")).strip()
        integration_type = str(body.get("integration_type", "")).strip()
        if not integration_name or not integration_type:
            raise HTTPException(status_code=400, detail="integration_name and integration_type required")
        return service.register_platform_integration(
            organization_id=claims.organization_id,
            integration_name=integration_name,
            integration_type=integration_type,
            scopes=[str(scope) for scope in scopes],
        )

    @router.get("/adoption/status")
    def field_adoption_status(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.field_adoption_status()

    @router.post("/organizations/onboard")
    def organization_onboard(
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        organization_id = str(body.get("organization_id", "")).strip()
        legal_name = str(body.get("legal_name", "")).strip()
        sector = str(body.get("sector", "")).strip()
        trust_domain = str(body.get("trust_domain", "")).strip()
        if not all([organization_id, legal_name, sector, trust_domain]):
            raise HTTPException(
                status_code=400,
                detail="organization_id, legal_name, sector, and trust_domain required",
            )
        return service.onboard_organization(
            organization_id=organization_id,
            legal_name=legal_name,
            sector=sector,
            trust_domain=trust_domain,
        )

    @router.post("/federation/trust-exchange")
    def federation_trust_exchange(
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        try:
            trust_score = int(body.get("trust_score", 0))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="trust_score must be an integer") from exc
        return service.trust_exchange(
            issuer_org=str(body.get("issuer_org", claims.organization_id)),
            subject_org=str(body.get("subject_org", "external-auditor")),
            receipt_hash=str(body.get("receipt_hash", "")),
            trust_score=trust_score,
        )

    @router.post("/deployment/{project_id}/feedback")
    def deployment_feedback(
        project_id: str,
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        try:
            validation_score = int(body.get("validation_score", 100))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="validation_score must be an integer") from exc
        return service.record_deployment_feedback(
            project_id=project_id,
            environment=str(body.get("environment", "staging")),
            status=str(body.get("status", "validated")),
            validation_score=validation_score,
            evidence=body.get("evidence") if isinstance(body.get("evidence"), dict) else {},
            organization_id=claims.organization_id,
        )

    @router.post("/production/{project_id}/evidence")
    def production_evidence(
        project_id: str,
        body: dict[str, Any],
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        environment = str(body.get("environment", "production")).strip() or "production"
        evidence_type = str(body.get("evidence_type", "deployment_validation")).strip() or "deployment_validation"
        validation_status = str(body.get("validation_status", "")).strip()
        if not validation_status:
            raise HTTPException(status_code=400, detail="validation_status required")
        evidence_hash = body.get("evidence_hash")
        return service.record_production_evidence(
            organization_id=claims.organization_id,
            project_id=project_id,
            environment=environment,
            evidence_type=evidence_type,
            validation_status=validation_status,
            evidence_hash=str(evidence_hash) if evidence_hash is not None else None,
        )

    @router.get("/repo/{project_id}/intelligence")
    def repository_intelligence(
        project_id: str,
        focus: str = "",
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return service.repository_intelligence(
            project_id=project_id,
            focus=focus,
            organization_id=claims.organization_id,
        )

    return router


def build_novascript_public_router() -> APIRouter:
    service = get_novascript_service()
    router = APIRouter(tags=["novascript-public"])

    @router.get("/public/trust/{receipt_id}")
    def public_trust_receipt(receipt_id: str) -> dict[str, Any]:
        result = service.public_receipt(receipt_id)
        if result is None:
            raise HTTPException(status_code=404, detail="receipt not found")
        return result

    @router.get("/public/certificates/{certificate_id}")
    def public_certificate(certificate_id: str) -> dict[str, Any]:
        result = service.public_certificate(certificate_id)
        if result is None:
            raise HTTPException(status_code=404, detail="certificate not found")
        return result

    @router.get("/public/assurance/{report_id}")
    def public_assurance(report_id: str) -> dict[str, Any]:
        result = service.public_assurance_report(report_id)
        if result is None:
            raise HTTPException(status_code=404, detail="assurance report not found")
        return result

    @router.get("/public/trust/{receipt_id}/package")
    def public_verification_package(receipt_id: str) -> dict[str, Any]:
        result = service.portable_verification_package(receipt_id)
        if result is None:
            raise HTTPException(status_code=404, detail="verification package not found")
        return result

    return router
