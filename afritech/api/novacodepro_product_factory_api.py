from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro import NovaCodeProPlatform, get_novacodepro_platform
from afritech.novacodepro.product_factory import (
    ProductFactoryError,
    ProductFactoryService,
    build_product_factory_context,
)


def _service() -> ProductFactoryService:
    db_path = Path(__file__).resolve().parents[2] / "var/novacodepro-platform.sqlite3"
    platform = get_novacodepro_platform(db_path)
    return ProductFactoryService(platform)


def _handle(error: ProductFactoryError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


class RequestTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    note: str | None = None


class BlueprintAmendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changes: dict[str, Any] = Field(default_factory=dict)


class PhaseTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    note: str | None = None


class EvidenceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str | None = None
    blueprint_id: str | None = None
    phase_id: str | None = None
    gate_id: str | None = None
    title: str | None = None
    type: str | None = None
    subject: str | None = None
    correlation_id: str | None = None
    integrity_status: str | None = None
    source_records: list[Any] = Field(default_factory=list)
    timeline: list[Any] = Field(default_factory=list)
    verification_status: str | None = None
    manifest: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None


class ImprovementCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    source: str | None = None
    priority: str | None = None
    status: str | None = None
    linked_request_id: str | None = None
    linked_requirement_id: str | None = None
    linked_release_id: str | None = None
    evidence: list[Any] = Field(default_factory=list)


class CloneArchetypeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)


def build_novacodepro_product_factory_router(service: ProductFactoryService | None = None) -> APIRouter:
    factory = service or _service()
    router = APIRouter(tags=["novacodepro-product-factory"])

    readers = require_roles(
        "ADMIN",
        "OPERATOR",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "UI_UX_DESIGNER",
        "ARCHITECT",
        "PROJECT_MANAGER",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "OPERATIONS_TEAM",
        "AUDIT_TEAM",
        "SECURITY_ENGINEER",
        "OBSERVER",
    )
    writers = require_roles(
        "ADMIN",
        "OPERATOR",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "UI_UX_DESIGNER",
        "ARCHITECT",
        "PROJECT_MANAGER",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
    )
    approvers = require_roles(
        "ADMIN",
        "OPERATOR",
        "PRODUCT_MANAGER",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "OPERATIONS_TEAM",
        "AUDIT_TEAM",
    )

    @router.get("/v1/product-factory")
    def overview(claims: JWTClaims = Depends(readers), request: Request = None) -> dict[str, Any]:
        return factory.overview(build_product_factory_context(claims))

    @router.get("/v1/product-factory/inventory")
    def inventory(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.capability_inventory()

    @router.get("/v1/product-factory/gaps")
    def gaps(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.gap_matrix()

    @router.get("/v1/product-factory/archetypes")
    def list_archetypes(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return {"archetypes": factory.archetypes(), "count": len(factory.archetypes())}

    @router.post("/v1/product-factory/archetypes/{archetype_id}/clone")
    def clone_archetype(archetype_id: str, payload: CloneArchetypeRequest | None = None, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.clone_archetype(archetype_id, (payload or {}).model_dump(exclude_none=True) if payload else {}, build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/archetypes/{archetype_id}/publish")
    def publish_archetype(archetype_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.publish_archetype(archetype_id, build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/archetypes/{archetype_id}/deprecate")
    def deprecate_archetype(archetype_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.deprecate_archetype(archetype_id, build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.get("/v1/product-factory/requests")
    def list_requests(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        ctx = build_product_factory_context(claims)
        requests = factory.requests(ctx)
        return {"requests": requests, "count": len(requests)}

    @router.post("/v1/product-factory/requests")
    def create_request(payload: dict[str, Any], claims: JWTClaims = Depends(writers), x_idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        ctx = build_product_factory_context(claims)
        request_payload = dict(payload)
        if x_idempotency_key:
            request_payload.setdefault("idempotency_key", x_idempotency_key)
        try:
            return factory.create_request(request_payload, ctx)
        except ProductFactoryError as exc:
            _handle(exc)

    @router.get("/v1/product-factory/requests/{request_id}")
    def get_request(request_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return {"request": factory._request(request_id, build_product_factory_context(claims))}
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/requests/{request_id}/submit")
    def submit_request(request_id: str, payload: RequestTransitionRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.transition_request(request_id, "Submitted", build_product_factory_context(claims), note=payload.note or "")
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/requests/{request_id}/review")
    def review_request(request_id: str, payload: RequestTransitionRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.transition_request(request_id, payload.status, build_product_factory_context(claims), note=payload.note or "")
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/requests/{request_id}/approve")
    def approve_request(request_id: str, payload: RequestTransitionRequest | None = None, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            return factory.approve_request(request_id, build_product_factory_context(claims), approval_ref=(payload.note if payload else ""))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/requests/{request_id}/reject")
    def reject_request(request_id: str, payload: RequestTransitionRequest | None = None, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            return factory.reject_request(request_id, build_product_factory_context(claims), reason=(payload.note if payload else ""))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/requests/{request_id}/archive")
    def archive_request(request_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.archive_request(request_id, build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/requests/{request_id}/convert/product")
    def convert_to_product(request_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            return factory.convert_request_to_product(request_id, build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/requests/{request_id}/convert/project")
    def convert_to_project(request_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            return factory.convert_request_to_project(request_id, build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.get("/v1/product-factory/blueprints")
    def list_blueprints(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        ctx = build_product_factory_context(claims)
        blueprints = factory.blueprints(ctx)
        return {"blueprints": blueprints, "count": len(blueprints)}

    @router.post("/v1/product-factory/requests/{request_id}/blueprints")
    def create_blueprint(request_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.create_blueprint(request_id, payload, build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.get("/v1/product-factory/blueprints/{blueprint_id}")
    def get_blueprint(blueprint_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return {"blueprint": factory._blueprint(blueprint_id, build_product_factory_context(claims))}
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/blueprints/{blueprint_id}/approve")
    def approve_blueprint(blueprint_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            evidence = list((payload or {}).get("evidence") or [])
            return factory.approve_blueprint(blueprint_id, build_product_factory_context(claims), evidence=evidence)
        except ProductFactoryError as exc:
            _handle(exc)

    @router.post("/v1/product-factory/blueprints/{blueprint_id}/amend")
    def amend_blueprint(blueprint_id: str, payload: BlueprintAmendRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.amend_blueprint(blueprint_id, payload.changes, build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.get("/v1/product-factory/phases")
    def list_phases(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        ctx = build_product_factory_context(claims)
        phases = factory.phases(ctx)
        return {"phases": phases, "count": len(phases)}

    @router.post("/v1/product-factory/phases/{phase_id}/transition")
    def transition_phase(phase_id: str, payload: PhaseTransitionRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.transition_phase(phase_id, payload.status, build_product_factory_context(claims), note=payload.note or "")
        except ProductFactoryError as exc:
            _handle(exc)

    @router.get("/v1/product-factory/traceability")
    def traceability(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.traceability_matrix(build_product_factory_context(claims))

    @router.get("/v1/product-factory/evidence")
    def list_evidence(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        ctx = build_product_factory_context(claims)
        evidence = factory.evidence(ctx)
        return {"evidence": evidence, "count": len(evidence)}

    @router.post("/v1/product-factory/evidence")
    def create_evidence(payload: EvidenceCreateRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.create_evidence(payload.model_dump(exclude_none=True), build_product_factory_context(claims))
        except ProductFactoryError as exc:
            _handle(exc)

    @router.get("/v1/product-factory/audit")
    def audit(limit: int = 100, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        ctx = build_product_factory_context(claims)
        return {"audit": factory.audit(ctx, limit=limit), "count": len(factory.audit(ctx, limit=limit))}

    @router.get("/v1/product-factory/improvement-backlog")
    def improvement_backlog(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        ctx = build_product_factory_context(claims)
        backlog = factory.improvement_backlog(ctx)
        return {"improvements": backlog, "count": len(backlog)}

    @router.post("/v1/product-factory/improvements")
    def create_improvement(payload: ImprovementCreateRequest, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_improvement(payload.model_dump(exclude_none=True), build_product_factory_context(claims))

    @router.post("/v1/product-factory/demo")
    def demo_product(claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.demo_product(build_product_factory_context(claims))

    @router.post("/v1/product-factory/gates")
    def create_gate(payload: dict[str, Any], claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.create_gate_decision(payload, build_product_factory_context(claims))

    @router.get("/v1/product-factory/gates")
    def list_gates(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        ctx = build_product_factory_context(claims)
        gates = [item for item in factory.platform.repository.list("product_gate") if str(item.get("tenant_id") or "") == ctx.tenant_id]
        return {"gates": gates, "count": len(gates)}

    return router


__all__ = ["build_novacodepro_product_factory_router"]
