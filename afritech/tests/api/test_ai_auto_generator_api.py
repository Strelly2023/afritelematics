from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router, build_novacodepro_session_router
from afritech.api.ai_auto_generator_api import build_ai_auto_generator_router
from afritech.api.auth.novacodepro_session_store import NovaCodeProSessionStore
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    session_store = NovaCodeProSessionStore(tmp_path / "novacodepro-auth.sqlite3")
    app = FastAPI()
    app.include_router(build_auth_router(session_store=session_store))
    app.include_router(build_novacodepro_platform_router(platform))
    app.include_router(build_ai_auto_generator_router(platform))
    app.include_router(build_novacodepro_session_router(session_store=session_store))
    return TestClient(app)


def _login_and_select_workspace(client: TestClient, role: str = "PRODUCT_MANAGER") -> str:
    login = client.post(
        "/v1/novacodepro/session/login",
        json={"email": "productmanager.test@afritechnology.com", "password": "NovaCodePro123!", "role": role},
    )
    assert login.status_code == 200
    workspace_id = client.get("/v1/novacodepro/workspaces").json()["workspaces"][0]["id"]
    selected = client.post(f"/v1/novacodepro/workspaces/{workspace_id}/select")
    assert selected.status_code == 200
    return workspace_id


def _create_project(client: TestClient, workspace_id: str) -> str:
    response = client.post(
        "/v1/novacodepro/projects",
        headers={"Idempotency-Key": "ai-auto-generator-project"},
        json={"workspace_id": workspace_id, "name": "NovaCodePro AI Auto-Generator", "description": "Governed AI product lifecycle orchestration"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_ai_auto_generator_lifecycle_and_evidence(tmp_path: Path) -> None:
    client = _client(tmp_path)
    workspace_id = _login_and_select_workspace(client)
    project_id = _create_project(client, workspace_id)

    execution = client.post(
        "/api/v1/ai-auto-generator/executions",
        headers={"Idempotency-Key": "ai-auto-generator-execution"},
        json={
            "project_id": project_id,
            "request_id": "request-ai-001",
            "request_text": "Build a governed AI product lifecycle orchestration service for enterprise software delivery.",
            "requested_scope": ["strategy", "planning", "requirements", "design", "architecture", "release"],
        },
    )
    assert execution.status_code == 200
    payload = execution.json()
    assert payload["status"] == "REQUEST_RECEIVED"
    assert payload["current_service"] == "AI Strategy Service"
    assert len(payload["stages"]) == 11
    assert payload["stages"][0]["stage_id"] == "strategy"

    detail = client.get(f"/api/v1/ai-auto-generator/executions/{payload['id']}")
    assert detail.status_code == 200
    assert detail.json()["request_type"] == "enterprise software platform"

    approval = client.post(
        f"/api/v1/ai-auto-generator/executions/{payload['id']}/approvals",
        json={"stage_id": "strategy", "decision": "APPROVED", "reason": "Strategy baseline approved"},
    )
    assert approval.status_code == 200
    approved = approval.json()
    assert approved["stages"][0]["approval_status"] == "APPROVED"
    assert approved["current_service"] == "AI Planning Service"
    assert approved["status"] == "PLANNING_GENERATING"

    retry = client.post(
        f"/api/v1/ai-auto-generator/executions/{payload['id']}/retry",
        json={"stage_id": "planning", "reason": "Regenerate planning artefact"},
    )
    assert retry.status_code == 200
    assert retry.json()["current_stage_id"] == "planning"

    paused = client.post(f"/api/v1/ai-auto-generator/executions/{payload['id']}/pause")
    assert paused.status_code == 200
    assert paused.json()["status"] == "PAUSED"

    resumed = client.post(f"/api/v1/ai-auto-generator/executions/{payload['id']}/resume")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "PLANNING_REVIEW"

    traceability = client.get(f"/api/v1/ai-auto-generator/projects/{project_id}/traceability")
    assert traceability.status_code == 200
    assert traceability.json()["links"]

    evidence = client.get(f"/api/v1/ai-auto-generator/projects/{project_id}/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["evidence"]

    artifact_id = resumed.json()["artifacts"][1]
    regenerated = client.post(
        f"/api/v1/ai-auto-generator/executions/{payload['id']}/artifacts/{artifact_id}/regenerate",
        json={"reason": "Update planning artefact after review"},
    )
    assert regenerated.status_code == 200
    assert regenerated.json()["stage_id"] == "planning"

    cancelled = client.post(f"/api/v1/ai-auto-generator/executions/{payload['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"


def test_ai_auto_generator_cross_tenant_scope_is_forbidden(tmp_path: Path) -> None:
    client = _client(tmp_path)
    workspace_id = _login_and_select_workspace(client)
    project_id = _create_project(client, workspace_id)

    execution = client.post(
        "/api/v1/ai-auto-generator/executions",
        json={"project_id": project_id, "request_text": "Build governed product lifecycle orchestration."},
    )
    assert execution.status_code == 200
    execution_id = execution.json()["id"]

    cross_tenant = client.get(
        f"/api/v1/ai-auto-generator/executions/{execution_id}",
        headers={
            "Authorization": f"Bearer {JWT.create_token('other.user', role='PRODUCT_MANAGER', organization_id='other-tenant', workspace_id=workspace_id, permissions=('ai.read',))}",
        },
    )
    assert cross_tenant.status_code == 403
    assert cross_tenant.json()["detail"]["code"] == "cross_tenant_execution_forbidden"
