from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router, build_novacodepro_session_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_session_router())
    app.include_router(build_novacodepro_platform_router(platform))
    return TestClient(app)


def _login(client: TestClient, role: str = "ADMIN") -> None:
    response = client.post("/v1/novacodepro/session/login", json={"email": "platformadministrator.test@afritechnology.com", "password": "NovaCodePro123!", "role": role})
    assert response.status_code == 200


def test_ncp006b_design_workspace_and_brief_flow(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)

    workspace_response = client.post("/v1/novacodepro/design/workspaces", json={"name": "Experience Workspace", "description": "Governed design workspace"})
    assert workspace_response.status_code == 200
    workspace_id = workspace_response.json()["id"]
    selected = client.post(f"/v1/novacodepro/design/workspaces/{workspace_id}/select")
    assert selected.status_code == 200

    workspace_list = client.get("/v1/novacodepro/design/workspaces")
    assert workspace_list.status_code == 200
    assert workspace_list.json()["experience_workspaces"]

    detail = client.get(f"/v1/novacodepro/design/workspaces/{workspace_id}")
    assert detail.status_code == 200

    brief_response = client.post(
        "/v1/novacodepro/design/briefs",
        json={
            "workspace_id": workspace_id,
            "title": "Experience brief",
            "problem_statement": "Improve accessibility.",
            "channels": "Web",
            "accessibility_targets": "WCAG_2_2_AA",
        },
    )
    assert brief_response.status_code == 200
    brief_id = brief_response.json()["id"]

    compare = client.get(f"/v1/novacodepro/design/briefs/{brief_id}/compare")
    assert compare.status_code == 200

    token_response = client.post(
        "/v1/novacodepro/design/tokens",
        json={"workspace_id": workspace_id, "path": "color.brand.primary", "name": "color.brand.primary", "category": "COLOR", "level": "SEMANTIC", "value": "#0052cc"},
    )
    assert token_response.status_code == 200

    traceability = client.post(
        "/v1/novacodepro/design/traceability/links",
        json={
            "workspace_id": workspace_id,
            "source_type": "EXPERIENCE_BRIEF",
            "source_id": brief_id,
            "target_type": "DESIGN_TOKEN",
            "target_id": token_response.json()["id"],
            "relationship": "DERIVED_FROM",
        },
    )
    assert traceability.status_code == 200

    coverage = client.get("/v1/novacodepro/design/traceability/coverage")
    assert coverage.status_code == 200
    assert "traceability_coverage" in coverage.json()

    component_response = client.post(
        "/v1/novacodepro/design/components",
        json={
            "workspace_id": workspace_id,
            "name": "Primary Button",
            "properties": [{"name": "label", "type": "string"}],
            "keyboard_behavior": "Enter and Space",
            "focus_behavior": "Visible",
            "screen_reader_behavior": "Announces label",
        },
    )
    assert component_response.status_code == 200
    approval = client.post(
        "/v1/novacodepro/design/approvals",
        json={"resource_type": "component_definition", "resource_id": component_response.json()["id"], "required_role": "DESIGN"},
    )
    assert approval.status_code == 200
    approved = client.post(
        f"/v1/novacodepro/design/approvals/{approval.json()['id']}/approve",
        json={"resource_type": "component_definition", "resource_id": component_response.json()["id"]},
    )
    assert approved.status_code == 200

    baseline = client.post(
        "/v1/novacodepro/design/projects/design-project-default/baseline",
        json={"resource_ids": [{"resource_type": "component_definition", "resource_id": component_response.json()["id"]}], "approval_references": [approval.json()["id"]]},
    )
    assert baseline.status_code == 200

    forbidden = client.post("/v1/novacodepro/design/approvals", json={"resource_type": "design_token", "resource_id": token_response.json()["id"], "required_role": "ACCESSIBILITY"})
    assert forbidden.status_code == 200
