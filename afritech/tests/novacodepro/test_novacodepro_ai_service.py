from __future__ import annotations

from pathlib import Path

from afritech.novacodepro import NovaCodeProRepository
from afritech.novacodepro.ncp004 import NCP004ExecutionContext, NovaCodeProNCP004Service


def _ctx() -> NCP004ExecutionContext:
    return NCP004ExecutionContext(
        execution_id="exec-1",
        actor_id="product.manager",
        tenant_id="novatech",
        organization_id="novatech",
        workspace_id="workspace-1",
        project_id="project-1",
        request_id="request-1",
        role="PRODUCT_MANAGER",
        permissions=("ai.request", "ai.read", "ai.execute", "ai.approve"),
        environment="development",
        session_id="session-1",
        correlation_id="corr-1",
    )


def test_ncp004_service_classification_and_plan(tmp_path: Path) -> None:
    repository = NovaCodeProRepository(tmp_path / "novacodepro.sqlite3")
    service = NovaCodeProNCP004Service(repository)
    repository.upsert(
        "workspace",
        {
            "id": "workspace-1",
            "tenant_id": "novatech",
            "organization_id": "novatech",
            "workspace_id": "workspace-1",
            "name": "Workspace 1",
            "status": "ACTIVE",
            "created_at": "2026-07-18T00:00:00+00:00",
            "updated_at": "2026-07-18T00:00:00+00:00",
            "created_by": "product.manager",
            "updated_by": "product.manager",
            "correlation_id": "corr-1",
            "causation_id": "corr-1",
            "version": 1,
            "metadata": {},
        },
    )
    repository.upsert(
        "project",
        {
            "id": "project-1",
            "tenant_id": "novatech",
            "organization_id": "novatech",
            "workspace_id": "workspace-1",
            "name": "Project 1",
            "slug": "project-1",
            "description": "Project 1",
            "status": "DRAFT",
            "owner_id": "product.manager",
            "start_date": None,
            "target_date": None,
            "archived_at": None,
            "archived_by": None,
            "created_at": "2026-07-18T00:00:00+00:00",
            "updated_at": "2026-07-18T00:00:00+00:00",
            "created_by": "product.manager",
            "updated_by": "product.manager",
            "correlation_id": "corr-1",
            "causation_id": "corr-1",
            "version": 1,
            "metadata": {},
            "members": [{"user_id": "product.manager", "role": "OWNER"}],
            "milestones": [],
            "work_items": [],
            "risks": [],
            "attachments": [],
            "comments": [],
            "activity": [],
            "requests": [],
        },
    )
    repository.upsert(
        "request",
        {
            "id": "request-1",
            "tenant_id": "novatech",
            "organization_id": "novatech",
            "workspace_id": "workspace-1",
            "project_id": "project-1",
            "title": "Request 1",
            "description": "Request 1",
            "request_type": "TEXT",
            "priority": "MEDIUM",
            "status": "DRAFT",
            "attachments": [],
            "comments": [],
            "assignments": [],
            "transitions": [],
            "history": [],
            "available_transitions": [],
            "created_at": "2026-07-18T00:00:00+00:00",
            "updated_at": "2026-07-18T00:00:00+00:00",
            "created_by": "product.manager",
            "updated_by": "product.manager",
            "correlation_id": "corr-1",
            "causation_id": "corr-1",
            "version": 1,
            "metadata": {},
        },
    )
    execution = service.create_execution(
        {
            "request_text": "Build rider registration with NovaID identity verification.",
            "request_id": "request-1",
            "project_id": "project-1",
        },
        _ctx(),
    )
    assert execution["status"] == "RECEIVED"

    analysed = service.analyse_execution(execution["id"], _ctx())
    assert analysed["analysis"]["risk_class"] in {"MODERATE", "HIGH"}
    if analysed["execution"]["status"] == "CLARIFICATION_REQUIRED":
        clarifications = service.list_clarifications(execution["id"], _ctx())
        assert clarifications
        service.answer_clarification(execution["id"], clarifications[0]["id"], {"answer": "Use governed approval"}, _ctx())
        service.complete_clarifications(execution["id"], _ctx())

    requirements = service.generate_requirements(execution["id"], _ctx())
    assert requirements["requirements"]

    plan = service.generate_plan(execution["id"], _ctx())
    assert plan["plan"]["steps"]

    approval = service.request_approval(execution["id"], _ctx())
    assert approval["approval"]["status"] == "OPEN"


def test_ncp004_service_notifications_and_replay(tmp_path: Path) -> None:
    repository = NovaCodeProRepository(tmp_path / "novacodepro.sqlite3")
    service = NovaCodeProNCP004Service(repository)
    neutral_ctx = NCP004ExecutionContext(
        execution_id="exec-2",
        actor_id="product.manager",
        tenant_id="novatech",
        organization_id="novatech",
        workspace_id="workspace-1",
        project_id=None,
        request_id=None,
        role="PRODUCT_MANAGER",
        permissions=("ai.request", "ai.read", "ai.execute", "ai.approve"),
        environment="development",
        session_id="session-2",
        correlation_id="corr-2",
    )
    repository.upsert(
        "workspace",
        {
            "id": "workspace-1",
            "tenant_id": "novatech",
            "organization_id": "novatech",
            "workspace_id": "workspace-1",
            "name": "Workspace 1",
            "status": "ACTIVE",
            "created_at": "2026-07-18T00:00:00+00:00",
            "updated_at": "2026-07-18T00:00:00+00:00",
            "created_by": "product.manager",
            "updated_by": "product.manager",
            "correlation_id": "corr-2",
            "causation_id": "corr-2",
            "version": 1,
            "metadata": {},
        },
    )
    execution = service.create_execution({"request_text": "Write governance documentation."}, neutral_ctx)
    service.analyse_execution(execution["id"], _ctx())
    if service.list_clarifications(execution["id"], _ctx()):
        clarifications = service.list_clarifications(execution["id"], _ctx())
        service.answer_clarification(execution["id"], clarifications[0]["id"], {"answer": "Doc only"}, _ctx())
        service.complete_clarifications(execution["id"], _ctx())
    service.generate_requirements(execution["id"], _ctx())
    service.generate_plan(execution["id"], _ctx())
    approval = service.request_approval(execution["id"], _ctx())
    service.approve(approval["approval"]["id"], {"decision": "APPROVED", "reason": "Approved"}, _ctx())
    service.execute(execution["id"], _ctx())
    result = service.verify(execution["id"], _ctx())
    assert result["verification"]["status"] == "PASS"
    replay = service.replay(execution["id"], _ctx())
    assert replay["timeline"]
    assert service.notifications(_ctx())
