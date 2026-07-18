from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import build_auth_router, build_novacodepro_session_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_session_router())
    app.include_router(build_novacodepro_platform_router(platform))
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post("/v1/novacodepro/session/login", json={"email": "platformadministrator.test@afritechnology.com", "password": "NovaCodePro123!", "role": "ADMIN"})
    assert response.status_code == 200


def test_ncp006b_design_brief_versioning_and_compare(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)
    workspace = client.post("/v1/novacodepro/design/workspaces", json={"name": "Experience Workspace"})
    workspace_id = workspace.json()["id"]
    assert client.post(f"/v1/novacodepro/design/workspaces/{workspace_id}/select").status_code == 200
    brief = client.post("/v1/novacodepro/design/briefs", json={"workspace_id": workspace_id, "title": "Brief", "problem_statement": "Design brief", "channels": "Web", "accessibility_targets": "WCAG_2_2_AA"})
    assert brief.status_code == 200
    brief_id = brief.json()["id"]
    update = client.patch(f"/v1/novacodepro/design/briefs/{brief_id}", json={"description": "Updated"})
    assert update.status_code == 200
    versions = client.get(f"/v1/novacodepro/design/briefs/{brief_id}/versions")
    assert versions.status_code == 200
    compare = client.get(f"/v1/novacodepro/design/briefs/{brief_id}/compare")
    assert compare.status_code == 200
