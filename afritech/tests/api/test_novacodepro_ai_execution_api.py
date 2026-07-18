from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router, build_novacodepro_session_router
from afritech.api.auth.novacodepro_session_store import NovaCodeProSessionStore
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    session_store = NovaCodeProSessionStore(tmp_path / "novacodepro-auth.sqlite3")
    app = FastAPI()
    app.include_router(build_auth_router(session_store=session_store))
    app.include_router(build_novacodepro_platform_router(platform))
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


def _create_project_and_request(client: TestClient, workspace_id: str) -> tuple[str, str]:
    project = client.post(
        "/v1/novacodepro/projects",
        headers={"Idempotency-Key": "ncp004-project"},
        json={"workspace_id": workspace_id, "name": "NovaRide pilot", "description": "NCP-004 project"},
    )
    assert project.status_code == 200
    project_id = project.json()["id"]
    request = client.post(
        "/v1/novacodepro/requests",
        headers={"Idempotency-Key": "ncp004-request"},
        json={
            "workspace_id": workspace_id,
            "project_id": project_id,
            "title": "Build rider registration with NovaID identity verification.",
            "description": "Governed rider registration flow.",
        },
    )
    assert request.status_code == 200
    return project_id, request.json()["id"]


def test_ncp004_end_to_end_governed_execution(tmp_path: Path) -> None:
    client = _client(tmp_path)
    workspace_id = _login_and_select_workspace(client)
    project_id, request_id = _create_project_and_request(client, workspace_id)

    execution = client.post(
        "/v1/novacodepro/ai/executions",
        json={
            "project_id": project_id,
            "request_id": request_id,
            "request_text": "Build rider registration with NovaID identity verification.",
            "idempotency_key": "ncp004-execution",
        },
    )
    assert execution.status_code == 200
    execution_id = execution.json()["id"]
    assert execution.json()["status"] == "RECEIVED"

    analysed = client.post(f"/v1/novacodepro/ai/executions/{execution_id}/analyse")
    assert analysed.status_code == 200
    assert analysed.json()["analysis"]["request_type"] in {"security request", "software feature"}
    clarifications = client.get(f"/v1/novacodepro/ai/executions/{execution_id}/clarifications")
    assert clarifications.status_code == 200
    clarification_items = clarifications.json()["clarifications"]
    assert clarification_items

    answer = client.post(
        f"/v1/novacodepro/ai/executions/{execution_id}/clarifications/{clarification_items[0]['id']}/answer",
        json={"answer": "Use the selected workspace and product-manager approval."},
    )
    assert answer.status_code == 200
    complete = client.post(f"/v1/novacodepro/ai/executions/{execution_id}/clarifications/complete")
    assert complete.status_code == 200

    requirements = client.post(f"/v1/novacodepro/ai/executions/{execution_id}/generate-requirements")
    assert requirements.status_code == 200
    assert requirements.json()["requirements"]

    plan = client.post(f"/v1/novacodepro/ai/executions/{execution_id}/generate-plan")
    assert plan.status_code == 200
    assert plan.json()["plan"]["steps"]

    approval = client.post(f"/v1/novacodepro/ai/executions/{execution_id}/request-approval")
    assert approval.status_code == 200
    approval_id = approval.json()["approval"]["id"]

    approved = client.post(
        f"/v1/novacodepro/ai/approvals/{approval_id}/approve",
        json={"decision": "APPROVED", "reason": "Governed development approval"},
    )
    assert approved.status_code == 200

    executed = client.post(f"/v1/novacodepro/ai/executions/{execution_id}/execute")
    assert executed.status_code == 200
    assert executed.json()["status"] == "VERIFYING"

    verified = client.post(f"/v1/novacodepro/ai/executions/{execution_id}/verify")
    assert verified.status_code == 200
    assert verified.json()["verification"]["status"] == "PASS"

    replay = client.get(f"/v1/novacodepro/ai/executions/{execution_id}/replay")
    assert replay.status_code == 200
    assert replay.json()["timeline"]

    notifications = client.get("/v1/novacodepro/ai/notifications")
    assert notifications.status_code == 200
    assert notifications.json()["notifications"]

    other_tenant = client.get(
        f"/v1/novacodepro/ai/executions/{execution_id}",
        headers={
            "Authorization": f"Bearer {JWT.create_token('other.user', role='PRODUCT_MANAGER', organization_id='other-tenant', workspace_id=workspace_id, permissions=('ai.read',))}",
        },
    )
    assert other_tenant.status_code == 403
    assert other_tenant.json()["detail"]["code"] == "cross_tenant_execution_forbidden"

    second_execution = client.post(
        "/v1/novacodepro/ai/executions",
        json={
            "project_id": project_id,
            "request_id": request_id,
            "request_text": "Build a second governed flow for approval testing.",
            "idempotency_key": "ncp004-second-execution",
        },
    )
    assert second_execution.status_code == 200
    second_execution_id = second_execution.json()["id"]
    client.post(f"/v1/novacodepro/ai/executions/{second_execution_id}/analyse")
    second_clarifications = client.get(f"/v1/novacodepro/ai/executions/{second_execution_id}/clarifications").json()["clarifications"]
    client.post(
        f"/v1/novacodepro/ai/executions/{second_execution_id}/clarifications/{second_clarifications[0]['id']}/answer",
        json={"answer": "Approved by the product manager."},
    )
    client.post(f"/v1/novacodepro/ai/executions/{second_execution_id}/clarifications/complete")
    client.post(f"/v1/novacodepro/ai/executions/{second_execution_id}/generate-requirements")
    client.post(f"/v1/novacodepro/ai/executions/{second_execution_id}/generate-plan")
    pending_approval = client.post(f"/v1/novacodepro/ai/executions/{second_execution_id}/request-approval")
    assert pending_approval.status_code == 200
    pending_approval_id = pending_approval.json()["approval"]["id"]

    auditor = client.post(
        f"/v1/novacodepro/ai/approvals/{pending_approval_id}/approve",
        headers={
            "Authorization": f"Bearer {JWT.create_token('auditor.user', role='AUDITOR', organization_id='novatech', workspace_id=workspace_id, permissions=('ai.approve', 'ai.read'))}",
        },
        json={"decision": "APPROVED", "reason": "Should fail"},
    )
    assert auditor.status_code == 403
    assert auditor.json()["detail"]["code"] == "approval_forbidden"

    executions = client.get("/v1/novacodepro/ai/executions")
    assert executions.status_code == 200
    assert executions.json()["executions"]

    project_archive = client.post(f"/v1/novacodepro/projects/{project_id}/archive")
    assert project_archive.status_code == 200


def test_ncp004_approval_state_and_legacy_aliases(tmp_path: Path) -> None:
    client = _client(tmp_path)
    workspace_id = _login_and_select_workspace(client)
    _, request_id = _create_project_and_request(client, workspace_id)

    execution = client.post(
        "/v1/novacodepro/ai/requests",
        json={
            "request_id": request_id,
            "request_text": "Document the governance flow.",
            "idempotency_key": "ncp004-legacy",
        },
    )
    assert execution.status_code == 200
    execution_id = execution.json()["id"]
    analysed = client.post(f"/v1/novacodepro/ai/requests/{execution_id}/interpretation", json={"summary": "Governance flow"})
    assert analysed.status_code == 200
    plan = client.get(f"/v1/novacodepro/ai/requests/{execution_id}/plan")
    assert plan.status_code == 200
    assert isinstance(plan.json()["plan"], dict)
