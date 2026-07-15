from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro.operational_verification import OperationalVerificationService, invariant_status


class ProgramCreateRequest(BaseModel):
    tenant_id: str = "default"
    organization_id: str = "novatech"
    project_id: str = "project-pending"
    product_id: str = "novacodepro"
    release_id: str = "release-pending"
    environment: str = "ci"
    region: str = "global"
    version: str = "1.0"
    created_by: str = "NovaCodePro"
    correlation_id: str = ""


class EvidenceRequest(BaseModel):
    evidence_type: str
    subject: str
    release_id: str
    execution_id: str
    environment: str = "ci"


class ExecutiveApprovalRequestBody(BaseModel):
    release_id: str
    prr_id: str
    evidence_package_hash: str = ""
    risk_summary: str = ""
    scope: dict[str, Any] = Field(default_factory=dict)


def build_novacodepro_operational_verification_router(
    service: OperationalVerificationService | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/v1/novacodepro/operational-verification", tags=["novacodepro-operational-verification"])
    svc = service or OperationalVerificationService()
    observer = require_roles("OBSERVER", "UI_UX_DESIGNER", "DEVELOPER", "ADMIN", "SUPER_ADMIN")
    executor = require_roles("DEVELOPER", "ADMIN", "SUPER_ADMIN")
    approver = require_roles("ADMIN", "SUPER_ADMIN")

    @router.get("/status")
    def status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {**svc.status(), "invariants": invariant_status()}

    @router.get("/programs")
    def programs(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return [program.to_dict() for program in svc.repository.list_programs()]

    @router.post("/programs")
    def create_program(payload: ProgramCreateRequest, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        body = payload.model_dump()
        body["created_by"] = claims.sub
        return svc.create_program(body)

    @router.get("/programs/{program_id}")
    def get_program(program_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        program = svc.repository.get_program(program_id)
        if not program:
            raise HTTPException(status_code=404, detail="program_not_found")
        return program.to_dict()

    @router.post("/programs/{program_id}/execute")
    def execute_program(program_id: str, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        try:
            return svc.execute_program(program_id, actor_id=claims.sub)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="program_not_found") from exc

    @router.get("/runs")
    def runs(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return [run.to_dict() for run in svc.repository.list_runs()]

    @router.get("/runs/{run_id}")
    def get_run(run_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        run = svc.repository.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run_not_found")
        return run.to_dict()

    @router.get("/capabilities")
    def capabilities(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return [capability for program in svc.repository.list_programs() for capability in program.to_dict()["capabilities"]]

    @router.get("/evidence")
    def evidence(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return [item.to_dict() for item in svc.repository.list_evidence()]

    @router.get("/evidence/{evidence_id}")
    def get_evidence(evidence_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        evidence_item = svc.repository.get_evidence(evidence_id)
        if not evidence_item:
            raise HTTPException(status_code=404, detail="evidence_not_found")
        body = evidence_item.to_dict()
        body["metadata"] = {key: value for key, value in body.get("metadata", {}).items() if "secret" not in key.lower()}
        return body

    @router.post("/observability/verify")
    def verify_observability(payload: EvidenceRequest, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        evidence = svc.collect_development_evidence(payload.evidence_type or "observability", payload.subject, payload.release_id, payload.execution_id, payload.environment)
        evidence["observability_verified"] = False
        evidence["verification_status"] = "PENDING"
        return evidence

    @router.post("/accessibility/verify")
    def verify_accessibility(payload: EvidenceRequest, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        evidence = svc.collect_development_evidence(payload.evidence_type or "accessibility", payload.subject, payload.release_id, payload.execution_id, payload.environment)
        evidence["accessibility_verified"] = False
        evidence["screen_reader_human_validation"] = "PENDING"
        return evidence

    @router.post("/visual-regression/verify")
    def verify_visual_regression(payload: EvidenceRequest, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        evidence = svc.collect_development_evidence(payload.evidence_type or "visual-regression", payload.subject, payload.release_id, payload.execution_id, payload.environment)
        evidence["visual_regression_verified"] = False
        evidence["approved_baseline"] = False
        return evidence

    @router.post("/digital-twin/ingest")
    def ingest_digital_twin(payload: EvidenceRequest, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        evidence = svc.collect_development_evidence(payload.evidence_type or "digital-twin", payload.subject, payload.release_id, payload.execution_id, payload.environment)
        evidence["digital_twin_verified"] = False
        evidence["telemetry_connected"] = payload.environment == "production"
        return evidence

    @router.post("/digital-twin/simulate")
    def simulate_digital_twin(payload: EvidenceRequest, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        evidence = svc.collect_development_evidence(payload.evidence_type or "digital-twin-simulation", payload.subject, payload.release_id, payload.execution_id, payload.environment)
        evidence["forbidden_external_side_effects"] = False
        return evidence

    @router.get("/observability/status")
    def observability_status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"configured": True, "executed": False, "verified": False, "status": "EVIDENCE_PENDING"}

    @router.get("/accessibility/status")
    def accessibility_status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"configured": True, "executed": False, "verified": False, "human_screen_reader_validation": "PENDING"}

    @router.get("/visual-regression/status")
    def visual_status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"configured": True, "executed": False, "verified": False, "approved_baseline": False}

    @router.get("/digital-twin/status")
    def digital_twin_status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"configured": True, "telemetry_connected": False, "verified": False}

    @router.post("/prr/packages/generate")
    def generate_prr_package(payload: EvidenceRequest, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        return svc.generate_prr_package(payload.release_id, payload.environment)

    @router.get("/prr/packages")
    def prr_packages(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return []

    @router.get("/prr/packages/{prr_id}")
    def prr_package(prr_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"prr_id": prr_id, "status": "EVIDENCE_PENDING", "ga_allowed": False, "real_payments_enabled": False}

    @router.post("/prr/{prr_id}/submit-review")
    def submit_prr_review(prr_id: str, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        return {"prr_id": prr_id, "status": "REVIEW_PENDING", "ga_allowed": False}

    @router.post("/prr/{prr_id}/decisions")
    def prr_decision(prr_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        return {"prr_id": prr_id, "decision": payload.get("decision", "REQUEST_CHANGES"), "prr_approved": False, "ga_allowed": False}

    @router.get("/approvals")
    def approvals(claims: JWTClaims = Depends(observer)) -> list[dict[str, Any]]:
        return [decision.to_dict() for decision in svc.repository.list_approvals()]

    @router.post("/executive-approvals")
    def request_executive_approval(payload: ExecutiveApprovalRequestBody, claims: JWTClaims = Depends(executor)) -> dict[str, Any]:
        return svc.request_executive_approval(payload.model_dump(), actor_id=claims.sub)

    @router.post("/executive-approvals/{approval_id}/decisions")
    def executive_decision(approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        return {"approval_id": approval_id, "decision": payload.get("decision", "REQUEST_CHANGES"), "executive_approved": False, "ga_allowed": False}

    @router.get("/ga/status")
    def ga_status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return svc.evaluate_ga()

    @router.post("/ga/evaluate")
    def ga_evaluate(claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        return svc.evaluate_ga()

    @router.get("/payments/status")
    def payment_status(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return svc.evaluate_payments()

    @router.post("/payments/evaluate")
    def payment_evaluate(claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        return svc.evaluate_payments()

    return router
