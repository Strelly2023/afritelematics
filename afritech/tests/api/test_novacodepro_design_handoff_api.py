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


def test_ncp006b_design_handoff_and_baseline_routes(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)
    workspace = client.post("/v1/novacodepro/design/workspaces", json={"name": "Experience Workspace"})
    workspace_id = workspace.json()["id"]
    assert client.post(f"/v1/novacodepro/design/workspaces/{workspace_id}/select").status_code == 200
    component = client.post("/v1/novacodepro/design/components", json={"workspace_id": workspace_id, "name": "Button", "properties": [{"name": "label", "type": "string"}], "keyboard_behavior": "Enter", "focus_behavior": "Visible", "screen_reader_behavior": "Announces label"})
    assert component.status_code == 200
    approval = client.post("/v1/novacodepro/design/approvals", json={"resource_type": "component_definition", "resource_id": component.json()["id"], "required_role": "DESIGN"})
    assert approval.status_code == 200
    approved = client.post(f"/v1/novacodepro/design/approvals/{approval.json()['id']}/approve", json={"resource_type": "component_definition", "resource_id": component.json()["id"]})
    assert approved.status_code == 200
    baseline = client.post("/v1/novacodepro/design/projects/design-project-default/baseline", json={"resource_ids": [{"resource_type": "component_definition", "resource_id": component.json()["id"]}], "approval_references": [approval.json()["id"]]})
    assert baseline.status_code == 200
    handoff = client.post("/v1/novacodepro/design/handoffs", json={"design_baseline_id": baseline.json()["id"], "screen_specifications": [], "component_contracts": [], "token_package": {}, "theme_package": {}, "content_package": {}, "localization_package": {}, "accessibility_requirements": [], "responsive_requirements": [], "analytics_events": [], "api_references": [], "architecture_references": [], "test_requirements": [], "visual_baseline_references": [], "approval_references": [approved.json()["id"]]})
    assert handoff.status_code == 200
    validated = client.post(f"/v1/novacodepro/design/handoffs/{handoff.json()['id']}/validate")
    assert validated.status_code == 200
