from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT
from afritech.api.novacodepro_workflow_fabric_api import build_novacodepro_workflow_fabric_router
from afritech.novacodepro.platform import NovaCodeProPlatform, NovaCodeProRepository
from afritech.novacodepro.workflow_fabric import WorkflowFabricService


def _service(db_path: Path) -> WorkflowFabricService:
    repository = NovaCodeProRepository(db_path)
    platform = NovaCodeProPlatform(repository)
    return WorkflowFabricService(platform)


def _client(service: WorkflowFabricService) -> TestClient:
    app = FastAPI()
    app.include_router(build_novacodepro_workflow_fabric_router(service))
    return TestClient(app)


def _headers() -> dict[str, str]:
    token = JWT.create_token("platform-admin", role="ADMIN", organization_id="novatech", tenant_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def test_workflow_fabric_transitions_persist_and_generate_evidence(tmp_path: Path) -> None:
    service = _service(tmp_path / "workflow-fabric.sqlite3")
    created = service.create_workflow(
        {
            "title": "Employee onboarding workflow",
            "request": "Create an employee onboarding workflow with approvals and connector automation.",
            "tenant_id": "novatech",
            "project_id": "project-novacodepro",
            "idempotency_key": "workflow-onboarding-001",
        }
    )

    duplicate = service.create_workflow(
        {
            "title": "Employee onboarding workflow",
            "request": "Create an employee onboarding workflow with approvals and connector automation.",
            "tenant_id": "novatech",
            "project_id": "project-novacodepro",
            "idempotency_key": "workflow-onboarding-001",
        }
    )

    assert duplicate["id"] == created["id"]
    assert created["fabric"]["state"] == "DRAFT"
    assert "business_view" in created["views"]
    assert "execution_graph" in created["fabric"]["views"]

    validated = service.validate(created["id"])
    compiled = service.compile(created["id"])
    reviewed = service.review(created["id"], {"note": "reviewed by governance"})
    approved = service.approve(created["id"], {"approval_reference": "APR-001"})
    deployed = service.deploy(created["id"], {"environment": "production", "version": "1.0.0"})
    executed = service.execute(created["id"], {"input": {"country": "KE"}, "output": {"status": "started"}})
    evidence = service.emit_evidence(created["id"])
    replay = service.replay(created["id"])

    assert validated["state"] == "VALIDATED"
    assert compiled["state"] == "COMPILED"
    assert reviewed["fabric"]["state"] == "REVIEWED"
    assert approved["fabric"]["state"] == "APPROVED"
    assert deployed["fabric"]["state"] == "DEPLOYED"
    assert executed["fabric"]["state"] == "RUNNING"
    assert evidence["fabric"]["state"] == "EVIDENCE_GENERATED"
    assert evidence["evidence"]["verification_status"] == "FABRIC_VERIFIED"
    assert replay["workflow"]["state"] == "EVIDENCE_GENERATED"
    assert len(replay["events"]) >= 1

    verification = service.platform.verify_evidence_bundle(evidence["evidence"]["id"])
    assert verification["verified"] is True


def test_workflow_fabric_survives_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "workflow-fabric-restart.sqlite3"
    service = _service(db_path)
    created = service.create_workflow(
        {
            "title": "Purchase approval workflow",
            "request": "Create a governed purchase approval workflow.",
            "tenant_id": "novatech",
            "project_id": "project-procurement",
            "idempotency_key": "workflow-purchase-001",
        }
    )
    service.validate(created["id"])
    service.compile(created["id"])
    service.review(created["id"], {"note": "restart check"})

    restarted = _service(db_path)
    view = restarted.workflow_view(created["id"])
    timeline = restarted.timeline(created["id"])

    assert view["fabric"]["state"] == "REVIEWED"
    assert view["fabric"]["contract"]["workflow_id"] == created["id"]
    assert len(timeline) >= 4
    assert restarted.summary()["fabric"] == "NovaWorkflow Fabric"


def test_workflow_fabric_api_exposes_authorized_endpoints(tmp_path: Path) -> None:
    service = _service(tmp_path / "workflow-fabric-api.sqlite3")
    client = _client(service)

    generated = client.post("/v1/workflows/generate", headers=_headers(), json={"prompt": "Create an incident response workflow"})
    assert generated.status_code == 200
    workflow_id = generated.json()["id"]

    views = client.get(f"/v1/workflows/{workflow_id}/views", headers=_headers())
    assert views.status_code == 200
    assert "state_machine" in views.json()

    validate = client.post(f"/v1/workflows/{workflow_id}/validate", headers=_headers())
    compile_response = client.post(f"/v1/workflows/{workflow_id}/compile", headers=_headers())
    review = client.post(
        f"/v1/workflows/{workflow_id}/review",
        headers=_headers(),
        json={"note": "governance review complete"},
    )
    approve = client.post(
        f"/v1/workflows/{workflow_id}/approve",
        headers=_headers(),
        json={"approval_reference": "APR-API-001", "reason": "policy approved"},
    )
    evidence = client.post(f"/v1/workflows/{workflow_id}/evidence", headers=_headers())

    assert validate.status_code == 200
    assert compile_response.status_code == 200
    assert review.status_code == 200
    assert approve.status_code == 200
    assert evidence.status_code == 200

    fabric_summary = client.get("/v1/workflow-fabric", headers=_headers())
    assert fabric_summary.status_code == 200
    assert fabric_summary.json()["workflow_count"] >= 1
