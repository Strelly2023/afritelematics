from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_workspace_api import build_novacodepro_workspace_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_workspace_router(service))
    return TestClient(app)


def _headers(role: str, user_id: str, organization_id: str = "novatech") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_workspace_manifest_personalizes_platform_administrator_workspace(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/workspace",
        headers=_headers("ADMIN", "usr_djuma"),
    )
    assert response.status_code == 200

    body = response.json()
    assert body["user"]["display_name"] == "Djuma"
    assert body["user"]["organization"] == "NovaTech"
    assert body["user"]["primary_role"] == "ADMIN"
    assert body["workspace"]["title"] == "Platform Administration Workspace"
    assert body["workspace"]["authority_level"] == "platform-admin"
    assert body["workspace"]["home_route"] == "/novacodepro/workspace/admin"
    assert body["workspace"]["selected_environment"] == "production"
    assert body["workspace"]["feature_flags"]["role_workspace_v2"] is True
    tool_names = [tool["name"] for tool in body["workspace"]["tools"]]
    assert "Platform Administration" in tool_names
    assert "Tenant Management" in tool_names
    assert "Identity and Access Center" in tool_names
    assert "Application and Tool Registry" in tool_names
    assert "Infrastructure and Service Center" in tool_names
    assert "Release Center" in tool_names
    assert body["workspace"]["administrator_attention"]


def test_workspace_manifest_personalizes_developer_workspace(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/workspace",
        headers=_headers("DEVELOPER", "usr_djuma"),
    )
    assert response.status_code == 200

    body = response.json()
    assert body["user"]["display_name"] == "Djuma"
    assert body["user"]["primary_role"] == "DEVELOPER"
    assert body["workspace"]["title"] == "Developer Workspace"
    assert body["workspace"]["home_route"] == "/novacodepro/workspace/developer"
    assert body["workspace"]["selected_environment"] == "development"
    assert body["workspace"]["authority_level"] == "developer"
    assert body["workspace"]["current_sprint"] == "Sprint 24"
    assert body["workspace"]["developer_health"]["repositories_healthy"] == "18/20"
    assert body["workspace"]["feature_flags"]["developer_workspace"] is True
    nav_labels = [group["label"] for group in body["workspace"]["navigation"]]
    assert nav_labels == ["My Work", "Build", "Design", "Deliver", "Assure", "Knowledge"]

    tool_names = [tool["name"] for tool in body["workspace"]["tools"]]
    assert "Developer Workspace" in tool_names
    assert "Code Workspace" in tool_names
    assert "Project Center" in tool_names
    assert "Pull Request and Review Center" in tool_names
    assert "Release Request Center" in tool_names
    assert "Platform Administration" not in tool_names
    assert body["workspace"]["developer_work_items"]


def test_workspace_html_renders_launcher_and_command_palette(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/novacodepro/workspace/admin",
        headers=_headers("ADMIN", "usr_djuma"),
    )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Good evening, Djuma" in response.text
    assert "Authorized tool launcher" in response.text
    assert "Command palette" in response.text
    assert "/novacodepro/tools/platform-administration" in response.text
    assert "Tenant Management" in response.text
    assert "Administrator attention" in response.text


def test_developer_workspace_html_renders_engineering_summary(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/novacodepro/workspace/developer",
        headers=_headers("DEVELOPER", "usr_djuma"),
    )
    assert response.status_code == 200
    assert "Developer Workspace" in response.text
    assert "My work" in response.text
    assert "Engineering health" in response.text
    assert "Code Workspace" in response.text
    assert "/novacodepro/tools/platform-administration" not in response.text
    assert "Recent repositories" in response.text
    assert "Test pass rate" in response.text


def test_developer_role_does_not_expose_admin_window(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/tools/platform-administration",
        headers=_headers("DEVELOPER", "usr_djuma"),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "tool_not_found"


def test_unauthorized_tools_are_absent_and_direct_urls_return_404(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/tools",
        headers=_headers("CUSTOMER", "customer-1"),
    )
    assert response.status_code == 200
    tool_names = [tool["name"] for tool in response.json()]
    assert "Customer Center" in tool_names
    assert "Platform Administration" not in tool_names
    assert "Board Portal" not in tool_names
    assert "Tenant Management" not in tool_names

    missing = client.get(
        "/novacodepro/tools/platform-administration",
        headers=_headers("CUSTOMER", "customer-1"),
    )
    assert missing.status_code == 404

    developer_missing = client.get(
        "/novacodepro/tools/platform-administration",
        headers=_headers("DEVELOPER", "usr_djuma"),
    )
    assert developer_missing.status_code == 404


def test_command_execution_is_auditable_and_role_gated(tmp_path: Path) -> None:
    client = _client(tmp_path)

    commands = client.get(
        "/v1/novacodepro/me/commands",
        headers=_headers("ADMIN", "usr_djuma"),
    )
    assert commands.status_code == 200
    assert any(item["label"] == "Open Platform Administration" for item in commands.json())

    queued = client.post(
        "/v1/novacodepro/commands/execute",
        headers=_headers("ADMIN", "usr_djuma"),
        json={"command": "Open Platform Administration"},
    )
    assert queued.status_code == 200
    assert queued.json()["status"] == "queued"
    assert queued.json()["requires_confirmation"] is True

    developer_commands = client.get(
        "/v1/novacodepro/me/commands",
        headers=_headers("DEVELOPER", "usr_djuma"),
    )
    assert developer_commands.status_code == 200
    assert any(item["label"] == "Open Code Workspace" for item in developer_commands.json())

    developer_queued = client.post(
        "/v1/novacodepro/commands/execute",
        headers=_headers("DEVELOPER", "usr_djuma"),
        json={"command": "Open Code Workspace"},
    )
    assert developer_queued.status_code == 200
    assert developer_queued.json()["status"] == "queued"
    assert developer_queued.json()["requires_confirmation"] is False
