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


class IdOnlyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None


class GenericWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    state: str | None = None
    status: str | None = None
    phase: str | None = None
    note: str | None = None
    version: int | None = None


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

    @router.get("/v1/product-factory/traceability/links")
    def traceability_links(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.traceability_links(build_product_factory_context(claims))

    @router.post("/v1/product-factory/traceability/links")
    def create_traceability_link(payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.create_traceability_link(payload, build_product_factory_context(claims))
        except Exception as exc:  # noqa: BLE001
            _handle(ProductFactoryError("traceability_link_error", str(exc)))

    @router.get("/v1/product-factory/traceability/links/{link_id}")
    def get_traceability_link(link_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return {"link": factory.get_traceability_link(link_id, build_product_factory_context(claims))}
        except KeyError as exc:
            _handle(ProductFactoryError("traceability_link_not_found", str(exc), 404))

    @router.delete("/v1/product-factory/traceability/links/{link_id}")
    def delete_traceability_link(link_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        try:
            return factory.delete_traceability_link(link_id, build_product_factory_context(claims))
        except Exception as exc:  # noqa: BLE001
            _handle(ProductFactoryError("traceability_link_delete_failed", str(exc)))

    @router.get("/v1/product-factory/traceability/entities/{entity_type}/{entity_id}")
    def traceability_entity(entity_type: str, entity_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.traceability_entities(build_product_factory_context(claims), entity_type, entity_id)

    @router.get("/v1/product-factory/traceability/products/{product_id}")
    def traceability_product(product_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.traceability_products(build_product_factory_context(claims), product_id)

    @router.get("/v1/product-factory/traceability/releases/{release_id}")
    def traceability_release(release_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.traceability_releases(build_product_factory_context(claims), release_id)

    @router.post("/v1/product-factory/traceability/validate")
    def validate_traceability(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.traceability_validate(build_product_factory_context(claims))

    @router.get("/v1/product-factory/traceability/coverage")
    def traceability_coverage(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.traceability_coverage(build_product_factory_context(claims))

    @router.get("/v1/product-factory/traceability/gaps")
    def traceability_gaps(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.traceability_gaps(build_product_factory_context(claims))

    @router.post("/v1/product-factory/traceability/export")
    def export_traceability(payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.export_traceability(build_product_factory_context(claims), payload or {})

    @router.get("/v1/product-factory/requirements")
    def list_requirements(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.requirements(build_product_factory_context(claims))

    @router.post("/v1/product-factory/requirements")
    def create_requirement(payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_requirement(payload, build_product_factory_context(claims))

    @router.get("/v1/product-factory/requirements/{requirement_id}")
    def get_requirement(requirement_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        try:
            return {"requirement": factory.get_requirement(requirement_id, build_product_factory_context(claims))}
        except KeyError as exc:
            _handle(ProductFactoryError("requirement_not_found", str(exc), 404))

    @router.post("/v1/product-factory/requirements/{requirement_id}/links")
    def link_requirement(requirement_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.link_requirement(requirement_id, payload, build_product_factory_context(claims))

    @router.get("/v1/product-factory/lifecycle-templates")
    def list_lifecycle_templates(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.lifecycle_templates(build_product_factory_context(claims))

    @router.post("/v1/product-factory/lifecycle-templates")
    def create_lifecycle_template(payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_lifecycle_template(payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/lifecycle-templates/{template_id}/publish")
    def publish_lifecycle_template(template_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.publish_lifecycle_template(template_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/products/{product_id}/lifecycles")
    def create_lifecycle(product_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_lifecycle(product_id, payload, build_product_factory_context(claims))

    @router.get("/v1/product-factory/lifecycles/{lifecycle_id}")
    def get_lifecycle(lifecycle_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return {"lifecycle": factory.get_lifecycle(lifecycle_id, build_product_factory_context(claims))}

    @router.post("/v1/product-factory/lifecycles/{lifecycle_id}/start")
    def start_lifecycle(lifecycle_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.start_lifecycle(lifecycle_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/lifecycles/{lifecycle_id}/transition")
    def transition_lifecycle(lifecycle_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.transition_lifecycle(lifecycle_id, payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/lifecycles/{lifecycle_id}/pause")
    def pause_lifecycle(lifecycle_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.pause_lifecycle(lifecycle_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/lifecycles/{lifecycle_id}/resume")
    def resume_lifecycle(lifecycle_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.resume_lifecycle(lifecycle_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/lifecycles/{lifecycle_id}/cancel")
    def cancel_lifecycle(lifecycle_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.cancel_lifecycle(lifecycle_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/lifecycles/{lifecycle_id}/rollback")
    def rollback_lifecycle(lifecycle_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.rollback_lifecycle(lifecycle_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/lifecycles/{lifecycle_id}/readiness")
    def lifecycle_readiness(lifecycle_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.lifecycle_readiness(lifecycle_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/lifecycles/{lifecycle_id}/timeline")
    def lifecycle_timeline(lifecycle_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.lifecycle_timeline(lifecycle_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/workflows/definitions")
    def list_workflow_definitions(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.workflow_definitions(build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/definitions")
    def create_workflow_definition(payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_workflow_definition(payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/definitions/{definition_id}/publish")
    def publish_workflow_definition(definition_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.publish_workflow_definition(definition_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/definitions/{definition_id}/deprecate")
    def deprecate_workflow_definition(definition_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.deprecate_workflow_definition(definition_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/instances")
    def create_workflow_instance(payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_workflow_instance(payload, build_product_factory_context(claims))

    @router.get("/v1/product-factory/workflows/instances/{instance_id}")
    def get_workflow_instance(instance_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return {"instance": factory.get_workflow_instance(instance_id, build_product_factory_context(claims))}

    @router.post("/v1/product-factory/workflows/instances/{instance_id}/transition")
    def transition_workflow_instance(instance_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.transition_workflow_instance(instance_id, payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/instances/{instance_id}/approve")
    def approve_workflow_instance(instance_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.approve_workflow_instance(instance_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/instances/{instance_id}/reject")
    def reject_workflow_instance(instance_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.reject_workflow_instance(instance_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/instances/{instance_id}/pause")
    def pause_workflow_instance(instance_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.pause_workflow_instance(instance_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/instances/{instance_id}/resume")
    def resume_workflow_instance(instance_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.resume_workflow_instance(instance_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/instances/{instance_id}/cancel")
    def cancel_workflow_instance(instance_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.cancel_workflow_instance(instance_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/instances/{instance_id}/retry")
    def retry_workflow_instance(instance_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.retry_workflow_instance(instance_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/workflows/instances/{instance_id}/compensate")
    def compensate_workflow_instance(instance_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.compensate_workflow_instance(instance_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/workflows/instances/{instance_id}/events")
    def workflow_events(instance_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.workflow_events(instance_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/workflows/instances/{instance_id}/evidence")
    def workflow_evidence(instance_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.workflow_evidence(instance_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/releases")
    def list_releases(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.releases(build_product_factory_context(claims))

    @router.post("/v1/product-factory/releases")
    def create_release(payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_release(payload, build_product_factory_context(claims))

    @router.get("/v1/product-factory/releases/{release_id}")
    def get_release(release_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return {"release": factory.get_release(release_id, build_product_factory_context(claims))}

    @router.post("/v1/product-factory/releases/{release_id}/candidates")
    def register_release_candidate(release_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.register_release_candidate(release_id, payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/releases/{release_id}/artifacts")
    def register_release_artifact(release_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.register_release_artifact(release_id, payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/releases/{release_id}/evidence")
    def register_release_evidence(release_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.register_release_evidence(release_id, payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/releases/{release_id}/evaluate")
    def evaluate_release(release_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.evaluate_release(release_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/releases/{release_id}/readiness")
    def release_readiness(release_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.release_readiness(release_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/releases/{release_id}/blockers")
    def release_blockers(release_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.release_blockers(release_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/releases/{release_id}/exceptions")
    def release_exception(release_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.create_release_exception(release_id, payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/releases/{release_id}/approvals")
    def release_approval(release_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.create_release_approval(release_id, payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/releases/{release_id}/decision")
    def release_decision(release_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        try:
            return factory.release_decision(release_id, payload, build_product_factory_context(claims))
        except Exception as exc:  # noqa: BLE001
            _handle(ProductFactoryError("release_decision_failed", str(exc)))

    @router.post("/v1/product-factory/releases/{release_id}/export-prr")
    def export_prr(release_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.export_prr(release_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/search")
    def search_get(query: str = "", product: str = "", claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.search(build_product_factory_context(claims), {"query": query, "product": product})

    @router.post("/v1/product-factory/search")
    def search_post(payload: dict[str, Any], claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.search(build_product_factory_context(claims), payload)

    @router.get("/v1/product-factory/reports/catalog")
    def report_catalog(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.reports_catalog()

    @router.post("/v1/product-factory/reports/run")
    def run_report(payload: dict[str, Any], claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.run_report(build_product_factory_context(claims), payload)

    @router.get("/v1/product-factory/reports/{report_id}")
    def get_report(report_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.report(report_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/reports/{report_id}/export")
    def export_report(report_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.export_report(report_id, build_product_factory_context(claims), payload)

    @router.get("/v1/product-factory/dashboards/{kind}")
    def dashboard(kind: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.dashboard(build_product_factory_context(claims), kind)

    @router.get("/v1/product-factory/cross-product/graph")
    def cross_product_graph(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.cross_product_graph(build_product_factory_context(claims))

    @router.post("/v1/product-factory/cross-product/relationships")
    def cross_product_relationships(payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.cross_product_relationships(build_product_factory_context(claims), payload)

    @router.get("/v1/product-factory/cross-product/impact/{entity_type}/{entity_id}")
    def cross_product_impact(entity_type: str, entity_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.cross_product_impact(build_product_factory_context(claims), entity_type, entity_id)

    @router.get("/v1/product-factory/cross-product/releases/{release_id}/dependencies")
    def cross_product_dependencies(release_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.cross_product_dependencies(release_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/cross-product/validate")
    def cross_product_validate(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.cross_product_validate(build_product_factory_context(claims))

    @router.get("/v1/product-factory/migrations")
    def list_migrations(claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.migrations(build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations")
    def create_migration(payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_migration(payload, build_product_factory_context(claims))

    @router.get("/v1/product-factory/migrations/{migration_id}")
    def get_migration(migration_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return {"migration": factory.get_migration(migration_id, build_product_factory_context(claims))}

    @router.post("/v1/product-factory/migrations/{migration_id}/assess")
    def assess_migration(migration_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.assess_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/map")
    def map_migration(migration_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.map_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/preview")
    def preview_migration(migration_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.preview_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/approve")
    def approve_migration(migration_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.approve_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/execute")
    def execute_migration(migration_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.execute_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/pause")
    def pause_migration(migration_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.pause_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/resume")
    def resume_migration(migration_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.resume_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/validate")
    def validate_migration(migration_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.validate_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/reconcile")
    def reconcile_migration(migration_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.reconcile_migration(migration_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/migrations/{migration_id}/rollback")
    def rollback_migration(migration_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.rollback_migration(migration_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/migrations/{migration_id}/evidence")
    def migration_evidence(migration_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.migration_evidence(migration_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/blueprints/{blueprint_id}/versions")
    def list_blueprint_versions(blueprint_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.blueprint_versions(blueprint_id, build_product_factory_context(claims))

    @router.get("/v1/product-factory/blueprints/{blueprint_id}/versions/{version_id}")
    def get_blueprint_version(blueprint_id: str, version_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        version = factory._record("product_blueprint_version", version_id, build_product_factory_context(claims).tenant_id)
        return {"version": version, "blueprint_id": blueprint_id}

    @router.post("/v1/product-factory/blueprints/{blueprint_id}/versions")
    def create_blueprint_version(blueprint_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.create_blueprint_version(blueprint_id, payload, build_product_factory_context(claims))

    @router.post("/v1/product-factory/blueprints/{blueprint_id}/versions/{version_id}/submit")
    def submit_blueprint_version(blueprint_id: str, version_id: str, claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.submit_blueprint_version(blueprint_id, version_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/blueprints/{blueprint_id}/versions/{version_id}/approve")
    def approve_blueprint_version(blueprint_id: str, version_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.approve_blueprint_version(blueprint_id, version_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/blueprints/{blueprint_id}/versions/{version_id}/reject")
    def reject_blueprint_version(blueprint_id: str, version_id: str, claims: JWTClaims = Depends(approvers)) -> dict[str, Any]:
        return factory.reject_blueprint_version(blueprint_id, version_id, build_product_factory_context(claims))

    @router.post("/v1/product-factory/blueprints/{blueprint_id}/versions/{version_id}/amend")
    def amend_blueprint_version(blueprint_id: str, version_id: str, payload: dict[str, Any], claims: JWTClaims = Depends(writers)) -> dict[str, Any]:
        return factory.amend_blueprint_version(blueprint_id, version_id, payload, build_product_factory_context(claims))

    @router.get("/v1/product-factory/blueprints/{blueprint_id}/compare")
    def compare_blueprints(blueprint_id: str, left_version: str | None = None, right_version: str | None = None, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.compare_blueprints(blueprint_id, build_product_factory_context(claims), left_version=left_version, right_version=right_version)

    @router.post("/v1/product-factory/blueprints/{blueprint_id}/verify")
    def verify_blueprint_version(blueprint_id: str, payload: dict[str, Any] | None = None, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.verify_blueprint_version(blueprint_id, build_product_factory_context(claims), payload)

    @router.get("/v1/product-factory/prr/{release_id}")
    def prr(release_id: str, claims: JWTClaims = Depends(readers)) -> dict[str, Any]:
        return factory.prr(build_product_factory_context(claims), release_id)

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
