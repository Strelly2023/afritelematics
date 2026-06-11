from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.afroprog_workspace_api import build_afroprog_workspace_router


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_afroprog_workspace_router())
    return TestClient(app)


def auth_headers(role: str = "DEVELOPER", user_id: str = "dev-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_afroprog_dashboard_endpoint_exposes_codex_style_workspace() -> None:
    client = build_client()

    response = client.get("/v1/afroprog/dashboard", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["view"] == "afroprog_dashboard"
    assert body["payload"]["workspace_mode"] == "codex_style"
    assert body["payload"]["governance_linked"] is True
    assert body["proposal_only"] is True


def test_afroprog_chat_prompt_endpoint_generates_poultry_bundle() -> None:
    client = build_client()

    response = client.post(
        "/v1/afroprog/chat/prompts",
        params={
            "prompt": "Create Django model for poultry farm and vaccination tracking",
            "mode": "code",
            "project_id": "project-poultry-suite",
        },
        headers=auth_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["view"] == "afroprog_chat"
    assert body["response"]["files"][0]["path"] == "poultry/apps/farm/models.py"
    assert body["response"]["governance_view"]["authority_boundary_preserved"] is True


def test_afroprog_projects_endpoint_lists_seed_workspaces() -> None:
    client = build_client()

    response = client.get("/v1/afroprog/projects", headers=auth_headers(role="VERIFIER", user_id="audit-1"))
    assert response.status_code == 200
    body = response.json()
    project_ids = [item["project_id"] for item in body["projects"]]
    assert "project-poultry-suite" in project_ids
    assert "project-employee-rbac" in project_ids
