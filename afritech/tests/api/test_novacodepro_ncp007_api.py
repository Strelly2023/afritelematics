from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router, build_novacodepro_session_router
from afritech.api.auth.novacodepro_session_store import NovaCodeProSessionStore
from afritech.api.novacodepro_ncp007_api import build_novacodepro_ncp007_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# Development Studio API Smoke\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "ncp007@example.com"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "NCP007"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    monkeypatch.setenv("NOVACODEPRO_REPO_ROOT", str(repo_root))
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    session_store = NovaCodeProSessionStore(tmp_path / "novacodepro-auth.sqlite3")
    app = FastAPI()
    app.include_router(build_auth_router(session_store=session_store))
    app.include_router(build_novacodepro_session_router(session_store=session_store))
    app.include_router(build_novacodepro_platform_router(platform))
    app.include_router(build_novacodepro_ncp007_router(platform))
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post(
        "/v1/novacodepro/session/login",
        json={"email": "productmanager.test@afritechnology.com", "password": "NovaCodePro123!", "role": "PRODUCT_MANAGER"},
    )
    assert response.status_code == 200


def test_ncp007_development_workspace_and_generation_api(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    _login(client)

    workspace_response = client.post(
        "/api/v1/development/workspaces",
        json={"name": "Development Studio", "description": "Governed code generation workspace"},
    )
    assert workspace_response.status_code == 200
    workspace_id = workspace_response.json()["id"]

    selected = client.post(f"/api/v1/development/workspaces/{workspace_id}/select")
    assert selected.status_code == 200

    workspace_list = client.get("/api/v1/development/workspaces")
    assert workspace_list.status_code == 200
    assert workspace_list.json()["workspaces"]

    summary = client.get(f"/api/v1/development/workspaces/{workspace_id}/summary")
    assert summary.status_code == 200

    session = client.post(f"/api/v1/development/workspaces/{workspace_id}/sessions", json={"objective": "Create a code change"})
    assert session.status_code == 200
    session_id = session.json()["id"]

    task = client.post(
        f"/api/v1/development/sessions/{session_id}/tasks",
        json={"title": "Build a governed code path", "description": "Create deterministic code", "task_type": "TEST"},
    )
    assert task.status_code == 200
    task_id = task.json()["id"]

    generation = client.post(
        f"/api/v1/development/tasks/{task_id}/generate",
        json={"instruction": "Generate a deterministic file", "target_files": ["novacodepro/generated/ncp007-api.py"]},
    )
    assert generation.status_code == 200
    change_set_id = generation.json()["change_set"]["id"]

    change_set = client.get(f"/api/v1/development/change-sets/{change_set_id}")
    assert change_set.status_code == 200
    assert change_set.json()["status"] in {"GENERATED", "READY_FOR_REVIEW"}

    validations = client.post(f"/api/v1/development/change-sets/{change_set_id}/validations", json={"validation_type": "CUSTOM", "command": ["git", "status", "--short"]})
    assert validations.status_code == 200

    reviews = client.post(f"/api/v1/development/change-sets/{change_set_id}/reviews", json={"summary": "API review"})
    assert reviews.status_code == 200
    review_id = reviews.json()["id"]

    approval_request = client.post(f"/api/v1/development/change-sets/{change_set_id}/approval-requests", json={"required_role": "TECH_LEAD"})
    assert approval_request.status_code == 200
    approval_id = approval_request.json()["id"]

    tech_lead_headers = {
        "Authorization": f"Bearer {JWT.create_token('tech.lead', role='TECH_LEAD', organization_id='NovaTech', workspace_id=workspace_id, permissions=('development.workspace.read', 'development.workspace.configure', 'repository.read', 'repository.patch.create', 'repository.patch.apply', 'repository.commit.prepare', 'repository.commit.execute', 'repository.pull_request.prepare', 'repository.pull_request.create', 'code.generate', 'code.modify', 'command.execute', 'build.execute', 'test.execute', 'approval.request', 'approval.review', 'approval.grant', 'evidence.read'))}",
    }

    approved = client.post(f"/api/v1/development/approvals/{approval_id}/approve", json={"reason": "Approved for testing"}, headers=tech_lead_headers)
    assert approved.status_code == 200

    commit_proposal = client.post(f"/api/v1/development/change-sets/{change_set_id}/commit-proposals", json={"branch_name": "feature/ncp007-api"}, headers=tech_lead_headers)
    assert commit_proposal.status_code == 200

    command = client.post(f"/api/v1/development/sessions/{session_id}/commands", json={"command": ["git", "status", "--short"]}, headers=tech_lead_headers)
    assert command.status_code == 200

    timeline = client.get(f"/api/v1/development/sessions/{session_id}/timeline")
    assert timeline.status_code == 200
    assert timeline.json()["events"]

    evidence = client.get(f"/api/v1/development/change-sets/{change_set_id}/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["evidence"]

    forbidden = client.get(
        f"/api/v1/development/workspaces/{workspace_id}",
        headers={
            "Authorization": f"Bearer {JWT.create_token('other.user', role='DEVELOPER', organization_id='other-tenant', workspace_id=workspace_id, permissions=('development.workspace.read',))}",
        },
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"]["code"] == "cross_tenant_development_forbidden"
