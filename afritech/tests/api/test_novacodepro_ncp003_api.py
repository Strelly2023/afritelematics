from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router, build_novacodepro_session_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.api.novacodepro_workspace_api import build_novacodepro_workspace_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(platform))
    app.include_router(build_novacodepro_session_router())
    app.include_router(build_novacodepro_workspace_router(platform))
    return TestClient(app)


def _login(
    client: TestClient,
    role: str = "PRODUCT_MANAGER",
    email: str = "productmanager.test@afritechnology.com",
) -> None:
    response = client.post(
        "/v1/novacodepro/session/login",
        json={
            "email": email,
            "password": "NovaCodePro123!",
            "role": role,
        },
    )
    assert response.status_code == 200


def _bearer(role: str, user_id: str, organization_id: str = "novatech", workspace_id: str | None = None) -> dict[str, str]:
    token = JWT.create_token(
        user_id,
        role=role,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permissions=("workspace.read", "project.read", "project.create", "request.create"),
    )
    return {"Authorization": f"Bearer {token}"}


def test_ncp003_workspace_project_request_flow(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)

    workspaces = client.get("/v1/novacodepro/workspaces")
    assert workspaces.status_code == 200
    workspace_id = workspaces.json()["workspaces"][0]["id"]

    selected = client.post(f"/v1/novacodepro/workspaces/{workspace_id}/select")
    assert selected.status_code == 200
    assert selected.json()["session"]["workspace_id"] == workspace_id

    project = client.post(
        "/v1/novacodepro/projects",
        headers={"Idempotency-Key": "project-ncp003-1"},
        json={
            "workspace_id": workspace_id,
            "name": "NovaCodePro release workspace",
            "description": "Workspace project for NCP-003",
            "owner_id": "djuma.productmanager",
        },
    )
    assert project.status_code == 200
    project_id = project.json()["id"]

    duplicate = client.post(
        "/v1/novacodepro/projects",
        headers={"Idempotency-Key": "project-ncp003-1"},
        json={
            "workspace_id": workspace_id,
            "name": "NovaCodePro release workspace",
            "description": "Workspace project for NCP-003",
            "owner_id": "djuma.productmanager",
        },
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == project_id

    milestone = client.post(
        f"/v1/novacodepro/projects/{project_id}/milestones",
        json={"name": "Milestone 1", "due_date": "2026-08-01"},
    )
    assert milestone.status_code == 200

    work_item = client.post(
        f"/v1/novacodepro/projects/{project_id}/work-items",
        json={"title": "Task 1", "type": "TASK", "description": "Implement route wiring", "assignee_id": "djuma.productmanager"},
    )
    assert work_item.status_code == 200

    request = client.post(
        "/v1/novacodepro/requests",
        headers={"Idempotency-Key": "request-ncp003-1"},
        json={
            "workspace_id": workspace_id,
            "project_id": project_id,
            "title": "Add secure workspace switching",
            "description": "Implement workspace selection and persistence.",
            "priority": "HIGH",
        },
    )
    assert request.status_code == 200
    request_id = request.json()["id"]
    assert request.json()["status"] == "DRAFT"

    attachment = client.post(
        f"/v1/novacodepro/requests/{request_id}/attachments",
        json={"filename": "requirements.pdf", "content_type": "application/pdf", "content": "pdf-bytes"},
    )
    assert attachment.status_code == 200
    assert attachment.json()["status"] == "AVAILABLE"

    submit = client.post(f"/v1/novacodepro/requests/{request_id}/submit")
    assert submit.status_code == 200
    assert submit.json()["status"] == "SUBMITTED"

    assignment = client.post(
        f"/v1/novacodepro/requests/{request_id}/assignments",
        json={"assignee_id": "reviewer-1", "assignment_role": "REVIEWER"},
    )
    assert assignment.status_code == 200

    comment = client.post(f"/v1/novacodepro/requests/{request_id}/comments", json={"body": "Looks good."})
    assert comment.status_code == 200

    transition = client.post(
        f"/v1/novacodepro/requests/{request_id}/transition",
        json={"status": "ANALYSING", "reason": "analysis started"},
    )
    assert transition.status_code == 200
    assert transition.json()["status"] == "ANALYSING"

    project_archive = client.post(f"/v1/novacodepro/projects/{project_id}/archive")
    assert project_archive.status_code == 200
    assert project_archive.json()["status"] == "ARCHIVED"

    archived_milestone = client.post(
        f"/v1/novacodepro/projects/{project_id}/milestones",
        json={"name": "Blocked milestone"},
    )
    assert archived_milestone.status_code == 409
    assert archived_milestone.json()["detail"]["code"] == "project_archived"

    notifications = client.get("/v1/novacodepro/notifications")
    assert notifications.status_code == 200
    assert notifications.json()["notifications"]

    logout = client.post("/v1/novacodepro/session/logout")
    assert logout.status_code == 200

    revoked = client.get("/v1/novacodepro/workspace")
    assert revoked.status_code == 401


def test_ncp003_tenant_isolation_and_attachment_quarantine(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client, role="DEVELOPER", email="developer.test@afritechnology.com")

    workspace_id = client.get("/v1/novacodepro/workspaces").json()["workspaces"][0]["id"]
    project = client.post(
        "/v1/novacodepro/projects",
        headers={"Idempotency-Key": "project-ncp003-tenant"},
        json={"workspace_id": workspace_id, "name": "Tenant isolation project"},
    )
    assert project.status_code == 200
    project_id = project.json()["id"]

    foreign = client.get(
        f"/v1/novacodepro/projects/{project_id}",
        headers=_bearer("PRODUCT_MANAGER", "foreign.user", organization_id="other-tenant"),
    )
    assert foreign.status_code == 403
    assert foreign.json()["detail"]["code"] == "project_forbidden"

    request_id = client.post(
        "/v1/novacodepro/requests",
        headers={"Idempotency-Key": "request-foreign"},
        json={"workspace_id": workspace_id, "project_id": project_id, "title": "Attachment quarantine request"},
    ).json()["id"]
    quarantined = client.post(
        f"/v1/novacodepro/requests/{request_id}/attachments",
        json={"filename": "invoice.pdf.exe", "content_type": "application/pdf", "content": "malware"},
    )
    assert quarantined.status_code == 200
    assert quarantined.json()["status"] == "QUARANTINED"

    auditor = client.post(
        f"/v1/novacodepro/projects/{project_id}/archive",
        headers=_bearer("AUDITOR", "auditor.user", workspace_id=workspace_id),
    )
    assert auditor.status_code == 403
