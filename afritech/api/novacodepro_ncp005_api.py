from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro import NovaCodeProPlatform
from afritech.novacodepro.ncp005 import NCP005Error, NCP005ExecutionContext, NovaCodeProNCP005Service, _digest, _utcnow


ACCESS_ROLES = (
    "OPERATOR",
    "ADMIN",
    "VERIFIER",
    "OBSERVER",
    "DEVELOPER",
    "PRODUCT_MANAGER",
    "BUSINESS_ANALYST",
    "UI_UX_DESIGNER",
    "PROJECT_MANAGER",
    "ARCHITECT",
    "QA_ENGINEER",
    "DEVOPS_ENGINEER",
    "SECURITY_ENGINEER",
    "COMPLIANCE_TEAM",
    "COMPLIANCE_OFFICER",
    "AUDIT_TEAM",
    "RISK_MANAGEMENT",
    "PRIVACY_COMPLIANCE",
    "DATA_ARCHITECT",
    "DATA_ENGINEER",
    "DATABASE_ENGINEER",
    "AI_ML_ENGINEER",
    "DATA_SCIENTIST",
    "EXTERNAL_REGULATOR",
    "LEGAL",
    "CLIENT",
    "PARTNER",
    "CUSTOMER",
)


def build_novacodepro_ncp005_router(service: NovaCodeProPlatform) -> APIRouter:
    router = APIRouter(tags=["novacodepro-ncp005"])
    ncp005 = NovaCodeProNCP005Service(service.repository)
    observer = require_roles(*ACCESS_ROLES)
    editor = require_roles(
        "OPERATOR",
        "ADMIN",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "SECURITY_ENGINEER",
        "COMPLIANCE_TEAM",
        "COMPLIANCE_OFFICER",
        "AUDIT_TEAM",
        "RISK_MANAGEMENT",
        "PRIVACY_COMPLIANCE",
        "DATA_ARCHITECT",
        "DATA_ENGINEER",
        "DATABASE_ENGINEER",
        "AI_ML_ENGINEER",
        "DATA_SCIENTIST",
        "LEGAL",
    )
    approver = require_roles(
        "OPERATOR",
        "ADMIN",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "SECURITY_ENGINEER",
        "COMPLIANCE_TEAM",
        "COMPLIANCE_OFFICER",
        "AUDIT_TEAM",
        "RISK_MANAGEMENT",
        "PRIVACY_COMPLIANCE",
        "EXTERNAL_REGULATOR",
    )

    def _ctx(
        claims: JWTClaims,
        *,
        workspace_id: str | None = None,
        project_id: str | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> NCP005ExecutionContext:
        resolved_workspace_id = workspace_id or claims.workspace_id
        permissions = tuple(sorted({str(permission) for permission in claims.permissions}))
        return NCP005ExecutionContext(
            actor_id=claims.sub,
            tenant_id=str(claims.tenant_id or claims.organization_id).lower(),
            organization_id=claims.organization_id,
            workspace_id=resolved_workspace_id,
            project_id=project_id,
            request_id=request_id,
            role=claims.role,
            permissions=permissions,
            session_id=claims.sid or None,
            correlation_id=correlation_id or f"ncp005-{claims.sid or claims.sub}-{resolved_workspace_id or project_id or request_id or 'global'}",
            causation_id=claims.sid or None,
        )

    def _map_error(error: Exception) -> HTTPException:
        if isinstance(error, NCP005Error):
            return HTTPException(
                status_code=error.status_code,
                detail={
                    "code": error.code,
                    "message": error.message,
                    "retryable": False,
                    "details": error.details,
                    "correlationId": error.details.get("correlation_id", ""),
                },
            )
        if isinstance(error, PermissionError):
            return HTTPException(status_code=403, detail={"code": "forbidden", "message": str(error)})
        if isinstance(error, KeyError):
            code = str(error).strip("'")
            return HTTPException(status_code=404, detail={"code": code, "message": code.replace("_", " ").capitalize()})
        return HTTPException(status_code=500, detail={"code": "service_unavailable", "message": "Service unavailable."})

    def _workspace_id(payload: dict[str, Any], claims: JWTClaims) -> str | None:
        return str(payload.get("workspace_id") or claims.workspace_id or "") or None

    def _project_id(payload: dict[str, Any], claims: JWTClaims) -> str | None:
        return str(payload.get("project_id") or getattr(claims, "project_id", "") or "") or None

    def _request_id(payload: dict[str, Any], claims: JWTClaims) -> str | None:
        return str(payload.get("request_id") or getattr(claims, "request_id", "") or "") or None

    # requirements
    @router.get("/requirements")
    def list_requirements(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"requirements": ncp005.list_requirements(_ctx(claims))}

    @router.post("/requirements")
    def create_requirement(
        payload: dict[str, Any],
        claims: JWTClaims = Depends(editor),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            payload = dict(payload)
            if idempotency_key:
                payload["idempotency_key"] = idempotency_key
            return ncp005.create_requirement(payload, _ctx(claims, workspace_id=_workspace_id(payload, claims), project_id=_project_id(payload, claims), request_id=_request_id(payload, claims)))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}")
    def get_requirement(requirement_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.get_requirement(requirement_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/requirements/{requirement_id}")
    def update_requirement(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.update_requirement(requirement_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/requirements/{requirement_id}")
    def delete_requirement(requirement_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.delete_requirement(requirement_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/transition")
    def transition_requirement(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.transition_requirement(requirement_id, str(payload.get("status") or payload.get("target_status") or ""), _ctx(claims), reason=str(payload.get("reason") or ""), approval_reference=payload.get("approval_reference"))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/archive")
    def archive_requirement(requirement_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.archive_requirement(requirement_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/restore")
    def restore_requirement(requirement_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.restore_requirement(requirement_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}/versions")
    def list_requirement_versions(requirement_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"versions": ncp005.list_requirement_versions(requirement_id, _ctx(claims))}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}/versions/{version_id}")
    def get_requirement_version(requirement_id: str, version_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.get_requirement_version(requirement_id, version_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/versions")
    def create_requirement_version(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_requirement_version(requirement_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/versions/{version_id}/restore")
    def restore_requirement_version(requirement_id: str, version_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.restore_requirement_version(requirement_id, version_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}/compare")
    def compare_requirement_versions(requirement_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.compare_requirement_versions(requirement_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}/reviews")
    def list_requirement_reviews(requirement_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"reviews": ncp005.list_requirement_reviews(requirement_id, _ctx(claims))}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/reviews")
    def create_requirement_review(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_requirement_review(requirement_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/reviews/{review_id}/complete")
    def complete_requirement_review(requirement_id: str, review_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.complete_requirement_review(requirement_id, review_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}/approvals")
    def list_requirement_approvals(requirement_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"approvals": ncp005.list_requirement_approvals(requirement_id, _ctx(claims))}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/approvals")
    def create_requirement_approval(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_requirement_approval(requirement_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/approvals/{approval_id}/approve")
    def approve_requirement_approval(requirement_id: str, approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return ncp005.approve_requirement_approval(requirement_id, approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/approvals/{approval_id}/reject")
    def reject_requirement_approval(requirement_id: str, approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return ncp005.reject_requirement_approval(requirement_id, approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirements/{requirement_id}/approvals/{approval_id}/request-changes")
    def request_changes_requirement_approval(requirement_id: str, approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.request_changes_requirement_approval(requirement_id, approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}/acceptance-criteria")
    def list_acceptance_criteria(requirement_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"acceptance_criteria": ncp005.list_acceptance_criteria(requirement_id, _ctx(claims))}

    @router.post("/requirements/{requirement_id}/acceptance-criteria")
    def create_acceptance_criterion(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_acceptance_criterion(requirement_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/requirements/{requirement_id}/acceptance-criteria/{criterion_id}")
    def update_acceptance_criterion(requirement_id: str, criterion_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.update_acceptance_criterion(requirement_id, criterion_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/requirements/{requirement_id}/acceptance-criteria/{criterion_id}")
    def delete_acceptance_criterion(requirement_id: str, criterion_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.delete_acceptance_criterion(requirement_id, criterion_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}/comments")
    def list_requirement_comments(requirement_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"comments": ncp005.list_requirement_comments(requirement_id, _ctx(claims))}

    @router.post("/requirements/{requirement_id}/comments")
    def add_requirement_comment(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.add_requirement_comment(requirement_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/requirements/{requirement_id}/comments/{comment_id}")
    def update_requirement_comment(requirement_id: str, comment_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.update_requirement_comment(requirement_id, comment_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/requirements/{requirement_id}/comments/{comment_id}")
    def delete_requirement_comment(requirement_id: str, comment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.delete_requirement_comment(requirement_id, comment_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirements/{requirement_id}/relationships")
    def list_requirement_relationships(requirement_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"relationships": ncp005.list_requirement_relationships(requirement_id, _ctx(claims))}

    @router.post("/requirements/{requirement_id}/relationships")
    def create_requirement_relationship(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_requirement_relationship(requirement_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/requirements/{requirement_id}/relationships/{relationship_id}")
    def delete_requirement_relationship(requirement_id: str, relationship_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.delete_requirement_relationship(relationship_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    # requirement sets and baselines
    @router.get("/requirement-sets")
    def list_requirement_sets(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"requirement_sets": ncp005.list_requirement_sets(_ctx(claims))}

    @router.post("/requirement-sets")
    def create_requirement_set(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_requirement_set(payload, _ctx(claims, workspace_id=_workspace_id(payload, claims), project_id=_project_id(payload, claims), request_id=_request_id(payload, claims)))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirement-sets/{set_id}")
    def get_requirement_set(set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.get_requirement_set(set_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/requirement-sets/{set_id}")
    def update_requirement_set(set_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.update_requirement_set(set_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirement-sets/{set_id}/archive")
    def archive_requirement_set(set_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.archive_requirement_set(set_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirement-sets/{set_id}/requirements")
    def add_requirement_to_set(set_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.add_requirement_to_set(set_id, str(payload.get("requirement_id") or ""), _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/requirement-sets/{set_id}/requirements/{requirement_id}")
    def remove_requirement_from_set(set_id: str, requirement_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.remove_requirement_from_set(set_id, requirement_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirement-sets/{set_id}/baseline")
    def create_requirement_baseline(set_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_requirement_baseline(set_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirement-sets/{set_id}/baselines")
    def list_requirement_set_baselines(set_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"baselines": ncp005.list_requirement_baselines(_ctx(claims), set_id=set_id)}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/requirement-sets/{set_id}/baselines/{baseline_id}")
    def get_requirement_baseline(set_id: str, baseline_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            baseline = ncp005._get_kind("requirement_baseline", baseline_id, _ctx(claims))
            if str(baseline.get("requirement_set_id")) != set_id:
                raise NCP005Error("requirement_baseline_immutable", "Baseline does not belong to this requirement set.", 409)
            return baseline
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/requirement-sets/{set_id}/baselines/{baseline_id}/supersede")
    def supersede_requirement_baseline(set_id: str, baseline_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            baseline = ncp005.supersede_requirement_baseline(baseline_id, _ctx(claims))
            if str(baseline.get("requirement_set_id")) != set_id:
                raise NCP005Error("requirement_baseline_immutable", "Baseline does not belong to this requirement set.", 409)
            return baseline
        except Exception as exc:
            raise _map_error(exc) from exc

    # traceability
    @router.get("/traceability/links")
    def list_traceability_links(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"links": ncp005.list_traceability_links(_ctx(claims))}

    @router.post("/traceability/links")
    def create_traceability_link(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_traceability_link(payload, _ctx(claims, workspace_id=_workspace_id(payload, claims), project_id=_project_id(payload, claims), request_id=_request_id(payload, claims)))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/traceability/links/{link_id}")
    def get_traceability_link(link_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005._get_kind("traceability_link", link_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/traceability/links/{link_id}")
    def delete_traceability_link(link_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.delete_traceability_link(link_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/traceability/resources/{resource_type}/{resource_id}")
    def traceability_resource(resource_type: str, resource_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.traceability_resource(resource_type, resource_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/traceability/resources/{resource_type}/{resource_id}/upstream")
    def traceability_upstream(resource_type: str, resource_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"upstream": ncp005.traceability_resource(resource_type, resource_id, _ctx(claims)).get("upstream", [])}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/traceability/resources/{resource_type}/{resource_id}/downstream")
    def traceability_downstream(resource_type: str, resource_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"downstream": ncp005.traceability_resource(resource_type, resource_id, _ctx(claims)).get("downstream", [])}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/traceability/resources/{resource_type}/{resource_id}/impact")
    def traceability_impact(resource_type: str, resource_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return {"impact": ncp005.traceability_resource(resource_type, resource_id, _ctx(claims)).get("impact", [])}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/traceability/coverage")
    def traceability_coverage(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.calculate_traceability_coverage(_ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/traceability/coverage/calculate")
    def calculate_traceability_coverage(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.calculate_traceability_coverage(_ctx(claims), set_id=str(payload.get("set_id") or payload.get("requirement_set_id") or ""))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/traceability/gaps")
    def traceability_gaps(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            coverage = ncp005.calculate_traceability_coverage(_ctx(claims))
            return {"gaps": coverage.get("gaps", [])}
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/traceability/snapshots")
    def create_traceability_snapshot(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            coverage = ncp005.calculate_traceability_coverage(_ctx(claims), set_id=str(payload.get("set_id") or payload.get("requirement_set_id") or ""))
            snapshot = dict(coverage.get("snapshot") or {})
            snapshot["coverage"] = coverage.get("coverage") or {}
            snapshot["gaps"] = coverage.get("gaps") or []
            return ncp005.repository.upsert("traceability_snapshot", snapshot)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/traceability/snapshots/{snapshot_id}")
    def get_traceability_snapshot(snapshot_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005._get_kind("traceability_snapshot", snapshot_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    # knowledge
    @router.get("/knowledge/spaces")
    def list_knowledge_spaces(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"spaces": ncp005.list_knowledge_spaces(_ctx(claims))}

    @router.post("/knowledge/spaces")
    def create_knowledge_space(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_knowledge_space(payload, _ctx(claims, workspace_id=_workspace_id(payload, claims), project_id=_project_id(payload, claims), request_id=_request_id(payload, claims)))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/spaces/{space_id}")
    def get_knowledge_space(space_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.get_knowledge_space(space_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/knowledge/spaces/{space_id}")
    def update_knowledge_space(space_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.update_knowledge_space(space_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/spaces/{space_id}/archive")
    def archive_knowledge_space(space_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.archive_knowledge_space(space_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/documents")
    def list_documents(space_id: str | None = None, content_type: str | None = None, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"documents": ncp005.list_documents(_ctx(claims), space_id=space_id, content_type=content_type)}

    @router.post("/knowledge/documents")
    def create_document(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_document(payload, _ctx(claims, workspace_id=_workspace_id(payload, claims), project_id=_project_id(payload, claims), request_id=_request_id(payload, claims)))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/documents/{document_id}")
    def get_document(document_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.get_document(document_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/knowledge/documents/{document_id}")
    def update_document(document_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.update_document(document_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/knowledge/documents/{document_id}")
    def delete_document(document_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.delete_document(document_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/transition")
    def transition_document(document_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.transition_document(document_id, str(payload.get("status") or payload.get("target_status") or ""), _ctx(claims), reason=str(payload.get("reason") or ""), approval_reference=payload.get("approval_reference"))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/publish")
    def publish_document(document_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.publish_document(document_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/archive")
    def archive_document(document_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.archive_document(document_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/restore")
    def restore_document(document_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.restore_document(document_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/documents/{document_id}/versions")
    def list_document_versions(document_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"versions": ncp005.list_document_versions(document_id, _ctx(claims))}

    @router.get("/knowledge/documents/{document_id}/versions/{version_id}")
    def get_document_version(document_id: str, version_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.get_document_version(document_id, version_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/versions")
    def create_document_version(document_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_document_version(document_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/versions/{version_id}/restore")
    def restore_document_version(document_id: str, version_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.restore_document_version(document_id, version_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/documents/{document_id}/compare")
    def compare_document_versions(document_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.compare_document_versions(document_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/documents/{document_id}/reviews")
    def list_document_reviews(document_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"reviews": ncp005.list_document_reviews(document_id, _ctx(claims))}

    @router.post("/knowledge/documents/{document_id}/reviews")
    def create_document_review(document_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_document_review(document_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/reviews/{review_id}/complete")
    def complete_document_review(document_id: str, review_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.complete_document_review(document_id, review_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/documents/{document_id}/approvals")
    def list_document_approvals(document_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"approvals": ncp005.list_document_approvals(document_id, _ctx(claims))}

    @router.post("/knowledge/documents/{document_id}/approvals")
    def create_document_approval(document_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_document_approval(document_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/approvals/{approval_id}/approve")
    def approve_document_approval(document_id: str, approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return ncp005.approve_document_approval(document_id, approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/approvals/{approval_id}/reject")
    def reject_document_approval(document_id: str, approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            return ncp005.reject_document_approval(document_id, approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/approvals/{approval_id}/request-changes")
    def request_changes_document_approval(document_id: str, approval_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.request_changes_document_approval(document_id, approval_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/documents/{document_id}/comments")
    def list_document_comments(document_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"comments": ncp005.list_document_comments(document_id, _ctx(claims))}

    @router.post("/knowledge/documents/{document_id}/comments")
    def add_document_comment(document_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.add_document_comment(document_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.patch("/knowledge/documents/{document_id}/comments/{comment_id}")
    def update_document_comment(document_id: str, comment_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.update_document_comment(document_id, comment_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/knowledge/documents/{document_id}/comments/{comment_id}")
    def delete_document_comment(document_id: str, comment_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.delete_document_comment(document_id, comment_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/tags")
    def list_tags(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"tags": ncp005.list_tags(_ctx(claims))}

    @router.post("/knowledge/tags")
    def create_tag(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_tag(payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/tags")
    def add_document_tag(document_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.add_document_tag(document_id, str(payload.get("tag_id") or ""), _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/knowledge/documents/{document_id}/tags/{tag_id}")
    def remove_document_tag(document_id: str, tag_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.remove_document_tag(document_id, tag_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/documents/{document_id}/relationships")
    def list_document_relationships(document_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"relationships": ncp005.list_document_relationships(document_id, _ctx(claims))}

    @router.post("/knowledge/documents/{document_id}/relationships")
    def create_document_relationship(document_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.create_document_relationship(document_id, payload, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.delete("/knowledge/documents/{document_id}/relationships/{relationship_id}")
    def delete_document_relationship(document_id: str, relationship_id: str, claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        try:
            return ncp005.delete_document_relationship(relationship_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/search")
    def search_knowledge(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.search(
                str(payload.get("query") or ""),
                _ctx(claims),
                resource_types=list(payload.get("resource_types") or []),
                classification=payload.get("classification"),
                strategy=str(payload.get("strategy") or "keyword"),
                maximum_results=int(payload.get("maximum_results") or 20),
                purpose=str(payload.get("purpose") or "search"),
                execution_id=payload.get("execution_id"),
            )
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/search/keyword")
    def search_keyword(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            filters = dict(payload)
            query = str(filters.pop("query", "") or "")
            return ncp005.search_keyword(query, _ctx(claims), **filters)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/search/semantic")
    def search_semantic(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            filters = dict(payload)
            query = str(filters.pop("query", "") or "")
            return ncp005.search_semantic(query, _ctx(claims), **filters)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/search/hybrid")
    def search_hybrid(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            filters = dict(payload)
            query = str(filters.pop("query", "") or "")
            return ncp005.search_hybrid(query, _ctx(claims), **filters)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/search/history")
    def search_history(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"searches": ncp005.recent_searches(_ctx(claims))}

    @router.post("/knowledge/answer")
    def answer(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            filters = dict(payload)
            query = str(filters.pop("query", "") or "")
            return ncp005.answer(query, _ctx(claims), **filters)
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/retrieve")
    def retrieve(payload: dict[str, Any], claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            filters = dict(payload)
            query = str(filters.pop("query", "") or "")
            retrieval = ncp005.search(
                query,
                _ctx(claims),
                resource_types=list(filters.get("allowed_resource_types") or []),
                classification=filters.get("classification_limit"),
                strategy="hybrid",
                maximum_results=int(filters.get("maximum_results") or 20),
                purpose=str(filters.get("purpose") or "retrieval"),
                execution_id=filters.get("execution_id"),
            )
            return ncp005.repository.upsert(
                "knowledge_retrieval_record",
                {
                    "id": retrieval["retrieval_id"],
                    "tenant_id": claims.tenant_id or claims.organization_id,
                    "workspace_id": claims.workspace_id,
                    "project_id": payload.get("project_id"),
                    "request_id": payload.get("request_id"),
                    "status": "COMPLETE",
                    "created_by": claims.sub,
                    "updated_by": claims.sub,
                    "created_at": _utcnow(),
                    "updated_at": _utcnow(),
                    "version": 1,
                    "correlation_id": _ctx(claims).correlation_id,
                    "causation_id": claims.sid or None,
                    "metadata": {"query_digest": retrieval.get("query_digest") or _digest(query), "source_count": len(retrieval["results"])},
                    "retrieval": retrieval,
                },
            )
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/retrievals/{retrieval_id}")
    def get_retrieval(retrieval_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        try:
            return ncp005.get_retrieval(retrieval_id, _ctx(claims))
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.get("/knowledge/spaces/{space_id}/documents")
    def list_space_documents(space_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return {"documents": ncp005.list_documents(_ctx(claims), space_id=space_id)}

    @router.get("/knowledge/documents/{document_id}/citations")
    def citations(document_id: str, claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        document = ncp005.get_document(document_id, _ctx(claims))
        return {"citations": document.get("citations", [])}

    @router.post("/knowledge/documents/{document_id}/legal-hold")
    def legal_hold(document_id: str, claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            document = ncp005.get_document(document_id, _ctx(claims))
            document["legal_hold"] = True
            ncp005.repository.upsert("knowledge_document", document)
            return document
        except Exception as exc:
            raise _map_error(exc) from exc

    @router.post("/knowledge/documents/{document_id}/release-legal-hold")
    def release_legal_hold(document_id: str, claims: JWTClaims = Depends(approver)) -> dict[str, Any]:
        try:
            document = ncp005.get_document(document_id, _ctx(claims))
            document["legal_hold"] = False
            ncp005.repository.upsert("knowledge_document", document)
            return document
        except Exception as exc:
            raise _map_error(exc) from exc

    return router


__all__ = ["build_novacodepro_ncp005_router"]
