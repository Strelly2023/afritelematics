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


def test_ncp006b_design_traceability_and_impact_routes(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)
    workspace = client.post("/v1/novacodepro/design/workspaces", json={"name": "Experience Workspace"})
    workspace_id = workspace.json()["id"]
    assert client.post(f"/v1/novacodepro/design/workspaces/{workspace_id}/select").status_code == 200
    brief = client.post("/v1/novacodepro/design/briefs", json={"workspace_id": workspace_id, "title": "Brief", "problem_statement": "Traceability", "channels": "Web", "accessibility_targets": "WCAG_2_2_AA"})
    token = client.post("/v1/novacodepro/design/tokens", json={"workspace_id": workspace_id, "path": "color.trace.primary", "name": "color.trace.primary", "category": "COLOR", "level": "SEMANTIC", "value": "#222222"})
    assert brief.status_code == 200
    assert token.status_code == 200
    link = client.post("/v1/novacodepro/design/traceability/links", json={"workspace_id": workspace_id, "source_type": "EXPERIENCE_BRIEF", "source_id": brief.json()["id"], "target_type": "DESIGN_TOKEN", "target_id": token.json()["id"], "relationship": "DERIVED_FROM"})
    assert link.status_code == 200
    coverage = client.get("/v1/novacodepro/design/traceability/coverage")
    assert coverage.status_code == 200
    snapshot = client.post("/v1/novacodepro/design/traceability/snapshots")
    assert snapshot.status_code == 200
    impact = client.post("/v1/novacodepro/design/impact", json={"resource_type": "experience_brief", "resource_id": brief.json()["id"]})
    assert impact.status_code == 200
