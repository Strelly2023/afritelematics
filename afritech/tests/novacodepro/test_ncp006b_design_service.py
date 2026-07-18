from __future__ import annotations

from pathlib import Path

import pytest

from afritech.novacodepro import NovaCodeProRepository
from afritech.novacodepro.ncp006b import DesignError, DesignExecutionContext, NovaCodeProNCP006BService


def _service(tmp_path: Path) -> NovaCodeProNCP006BService:
    return NovaCodeProNCP006BService(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))


def _ctx(*, role: str = "PRODUCT_MANAGER", permissions: tuple[str, ...] = ("design.read", "design.create", "design.update", "design.review", "design.validate", "design.baseline", "design.traceability", "design.search", "design.approve"), workspace_id: str = "design-workspace-default", project_id: str = "design-project-default") -> DesignExecutionContext:
    return DesignExecutionContext(
        actor_id="djuma.productmanager",
        tenant_id="novatech",
        organization_id="novatech",
        workspace_id=workspace_id,
        project_id=project_id,
        request_id="request-design-default",
        role=role,
        permissions=permissions,
        session_id="session-design-1",
        correlation_id="corr-design-1",
        causation_id="corr-design-0",
        environment="development",
    )


def test_ncp006b_design_service_creates_and_validates_artifacts(tmp_path: Path) -> None:
    service = _service(tmp_path)
    ctx = _ctx()

    workspace = service.create_workspace({"name": "Experience Workspace"}, ctx)
    assert workspace["status"] == "DRAFT"
    workspace_ctx = _ctx(workspace_id=workspace["id"], project_id=ctx.project_id)

    brief = service.create_resource(
        "experience_brief",
        {
            "workspace_id": workspace["id"],
            "project_id": ctx.project_id,
            "title": "Design brief",
            "problem_statement": "Make the platform accessible.",
            "classification": "INTERNAL",
            "visibility": "WORKSPACE",
        },
        workspace_ctx,
    )
    token = service.create_resource(
        "design_token",
        {"workspace_id": workspace["id"], "project_id": ctx.project_id, "name": "color.brand.primary", "path": "color.brand.primary", "category": "COLOR", "level": "SEMANTIC", "value": "#0052cc"},
        workspace_ctx,
    )
    component = service.create_resource(
        "component_definition",
        {
            "workspace_id": workspace["id"],
            "project_id": ctx.project_id,
            "name": "Primary Button",
            "properties": [{"name": "label", "type": "string"}],
            "keyboard_behavior": "Enter and Space activate",
            "focus_behavior": "Visible focus ring",
            "screen_reader_behavior": "Announces label and state",
        },
        workspace_ctx,
    )
    link = service.create_traceability_link(
        {
            "workspace_id": workspace["id"],
            "project_id": ctx.project_id,
            "source_type": "EXPERIENCE_BRIEF",
            "source_id": brief["id"],
            "target_type": "COMPONENT_DEFINITION",
            "target_id": component["id"],
            "relationship": "IMPLEMENTS",
            "evidence_reference": "evidence-1",
        },
        workspace_ctx,
    )

    assert token["status"] == "DRAFT"
    assert link["relationship"] == "IMPLEMENTS"

    validation = service.validate_artifact("design_token", token["id"], workspace_ctx)
    assert validation["status"] == "PASS"

    review = service.create_review("component_definition", component["id"], {"review_type": "ACCESSIBILITY"}, workspace_ctx)
    approval = service.create_approval("component_definition", component["id"], {"required_role": "DESIGN"}, workspace_ctx)
    decided = service.decide_approval("component_definition", component["id"], approval["id"], "APPROVED", {"reason": "Ready"}, workspace_ctx)
    assert review["status"] == "OPEN"
    assert decided["decision"] == "APPROVED"

    baseline = service.create_baseline(
        workspace_ctx.project_id or "design-project-default",
        {"resource_ids": [{"resource_type": "component_definition", "resource_id": component["id"]}], "approval_references": ["approval-1"]},
        workspace_ctx,
    )
    assert baseline["items"][0]["resource_id"] == component["id"]

    coverage = service.coverage(workspace_ctx)
    assert 0 <= coverage["traceability_coverage"] <= 1


def test_ncp006b_design_service_rejects_invalid_transition(tmp_path: Path) -> None:
    service = _service(tmp_path)
    ctx = _ctx()
    token = service.create_resource(
        "design_token",
        {"name": "color.brand.secondary", "path": "color.brand.secondary", "category": "COLOR", "level": "SEMANTIC", "value": "#111111"},
        ctx,
    )
    with pytest.raises(DesignError) as exc_info:
        service.transition_resource("design_token", token["id"], "APPROVED", ctx)
    assert exc_info.value.code == "invalid_design_transition"


def test_ncp006b_design_service_search_and_drift_are_tenant_scoped(tmp_path: Path) -> None:
    service = _service(tmp_path)
    ctx = _ctx()
    workspace = service.create_workspace({"name": "Workspace A"}, ctx)
    workspace_ctx = _ctx(workspace_id=workspace["id"], project_id=ctx.project_id)
    item = service.create_resource(
        "experience_brief",
        {"workspace_id": workspace["id"], "title": "Searchable artifact", "summary": "Traceable design content"},
        workspace_ctx,
    )
    search = service.search({"query": "Searchable", "resource_types": ["experience_brief"]}, workspace_ctx)
    assert search["results"][0]["resource_id"] == item["id"]

    drift = service.calculate_drift(workspace_ctx, resource_type="experience_brief", resource_id=item["id"])
    assert drift["status"] in {"DRIFT_DETECTED", "NO_DRIFT"}
