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


def test_workspace_manifest_personalizes_product_manager_workspace(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/workspace",
        headers=_headers("PRODUCT_MANAGER", "usr_djuma"),
    )
    assert response.status_code == 200

    body = response.json()
    assert body["user"]["display_name"] == "Djuma"
    assert body["user"]["primary_role"] == "PRODUCT_MANAGER"
    assert body["workspace"]["title"] == "Product Management Workspace"
    assert body["workspace"]["home_route"] == "/novacodepro/workspace/product"
    assert body["workspace"]["selected_environment"] == "business-planning"
    assert body["workspace"]["authority_level"] == "product-manager"
    assert body["workspace"]["portfolio_name"] == "Mobility and Payments"
    assert body["workspace"]["feature_flags"]["product_workspace"] is True
    nav_labels = [group["label"] for group in body["workspace"]["navigation"]]
    assert nav_labels == ["My Work", "Strategy", "Discover", "Plan", "Deliver", "Measure", "Knowledge"]

    tool_names = [tool["name"] for tool in body["workspace"]["tools"]]
    assert "Product Workspace" in tool_names
    assert "Product Portfolio" in tool_names
    assert "Roadmap Center" in tool_names
    assert "Requirements Center" in tool_names
    assert "Backlog and Prioritization Center" in tool_names
    assert "Product Documentation Center" in tool_names
    assert "Platform Administration" not in tool_names
    assert body["workspace"]["product_portfolio"]
    assert body["workspace"]["customer_signals"]


def test_workspace_manifest_personalizes_business_analyst_workspace(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/workspace",
        headers=_headers("BUSINESS_ANALYST", "usr_djuma"),
    )
    assert response.status_code == 200

    body = response.json()
    assert body["user"]["primary_role"] == "BUSINESS_ANALYST"
    assert body["workspace"]["title"] == "Business Analysis Workspace"
    assert body["workspace"]["home_route"] == "/novacodepro/workspace/business-analyst"
    assert body["workspace"]["selected_environment"] == "analysis"
    assert body["workspace"]["authority_level"] == "business-analyst"
    assert body["workspace"]["portfolio_name"] == "Mobility & Financial Services"
    assert body["workspace"]["feature_flags"]["business_analyst_workspace"] is True
    nav_labels = [group["label"] for group in body["workspace"]["navigation"]]
    assert nav_labels == ["Analysis", "Stakeholders", "Planning", "Governance", "Intelligence"]

    tool_names = [tool["name"] for tool in body["workspace"]["tools"]]
    assert "Business Analysis Workspace" in tool_names
    assert "Requirements Management Center" in tool_names
    assert "Business Process Modeling Studio" in tool_names
    assert "Business Rules Center" in tool_names
    assert "Business Reporting Center" in tool_names
    assert "Platform Administration" not in tool_names
    assert body["workspace"]["analysis_tasks"]


def test_workspace_manifest_personalizes_ui_ux_designer_workspace(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/workspace",
        headers=_headers("UI_UX_DESIGNER", "usr_djuma"),
    )
    assert response.status_code == 200

    body = response.json()
    assert body["user"]["primary_role"] == "UI_UX_DESIGNER"
    assert body["workspace"]["title"] == "Design Studio"
    assert body["workspace"]["home_route"] == "/novacodepro/workspace/design"
    assert body["workspace"]["selected_environment"] == "design"
    assert body["workspace"]["authority_level"] == "designer"
    assert body["workspace"]["feature_flags"]["design_workspace"] is True
    nav_labels = [group["label"] for group in body["workspace"]["navigation"]]
    assert nav_labels == ["Design", "System", "Research", "Delivery", "Creative"]

    tool_names = [tool["name"] for tool in body["workspace"]["tools"]]
    assert "Design Workspace" in tool_names
    assert "Wireframe Studio" in tool_names
    assert "NovaTech Design System" in tool_names
    assert "Accessibility Center" in tool_names
    assert "NovaAI Design Assistant" in tool_names
    assert "Platform Administration" not in tool_names
    assert body["workspace"]["design_projects"]


def test_workspace_manifest_personalizes_project_manager_workspace(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/workspace",
        headers=_headers("PROJECT_MANAGER", "usr_djuma"),
    )
    assert response.status_code == 200

    body = response.json()
    assert body["user"]["primary_role"] == "PROJECT_MANAGER"
    assert body["workspace"]["title"] == "Project Delivery Workspace"
    assert body["workspace"]["home_route"] == "/novacodepro/workspace/project-manager"
    assert body["workspace"]["selected_environment"] == "delivery"
    assert body["workspace"]["authority_level"] == "project-manager"
    assert body["workspace"]["portfolio_name"] == "Projects Portfolio"
    assert body["workspace"]["feature_flags"]["project_workspace"] is True
    nav_labels = [group["label"] for group in body["workspace"]["navigation"]]
    assert nav_labels == ["Projects", "Delivery", "Governance", "Communication", "Operations"]

    tool_names = [tool["name"] for tool in body["workspace"]["tools"]]
    assert "Project Workspace" in tool_names
    assert "Project Portfolio Center" in tool_names
    assert "Project Planning Center" in tool_names
    assert "Project Delivery Command Center" in tool_names
    assert "Project Documentation Center" in tool_names
    assert "Platform Administration" not in tool_names
    assert body["workspace"]["project_portfolio"]


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


def test_product_manager_workspace_html_renders_product_summary(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/novacodepro/workspace/product",
        headers=_headers("PRODUCT_MANAGER", "usr_djuma"),
    )
    assert response.status_code == 200
    assert "Product Management Workspace" in response.text
    assert "Product portfolio" in response.text
    assert "My priorities" in response.text
    assert "Customer signals" in response.text
    assert "/novacodepro/tools/platform-administration" not in response.text


def test_business_analyst_workspace_html_renders_analysis_summary(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/novacodepro/workspace/business-analyst",
        headers=_headers("BUSINESS_ANALYST", "usr_djuma"),
    )
    assert response.status_code == 200
    assert "Business Analysis Workspace" in response.text
    assert "Assigned projects" in response.text
    assert "Analysis health" in response.text
    assert "Requirements completed" in response.text
    assert "/novacodepro/tools/platform-administration" not in response.text


def test_ui_ux_designer_workspace_html_renders_design_summary(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/novacodepro/workspace/design",
        headers=_headers("UI_UX_DESIGNER", "usr_djuma"),
    )
    assert response.status_code == 200
    assert "Design Studio" in response.text
    assert "My design projects" in response.text
    assert "Design health" in response.text
    assert "Accessibility score" in response.text
    assert "/novacodepro/tools/platform-administration" not in response.text


def test_project_manager_workspace_html_renders_project_summary(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/novacodepro/workspace/project-manager",
        headers=_headers("PROJECT_MANAGER", "usr_djuma"),
    )
    assert response.status_code == 200
    assert "Project Delivery Workspace" in response.text
    assert "Project portfolio" in response.text
    assert "Portfolio health" in response.text
    assert "Budget utilization" in response.text
    assert "/novacodepro/tools/platform-administration" not in response.text


def test_developer_role_does_not_expose_admin_window(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/tools/platform-administration",
        headers=_headers("DEVELOPER", "usr_djuma"),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "tool_not_found"


def test_product_manager_role_does_not_expose_admin_window(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/tools/platform-administration",
        headers=_headers("PRODUCT_MANAGER", "usr_djuma"),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "tool_not_found"


def test_business_analyst_role_does_not_expose_admin_window(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/tools/platform-administration",
        headers=_headers("BUSINESS_ANALYST", "usr_djuma"),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "tool_not_found"


def test_ui_ux_designer_role_does_not_expose_admin_window(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/tools/platform-administration",
        headers=_headers("UI_UX_DESIGNER", "usr_djuma"),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "tool_not_found"


def test_project_manager_role_does_not_expose_admin_window(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/v1/novacodepro/tools/platform-administration",
        headers=_headers("PROJECT_MANAGER", "usr_djuma"),
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

    product_commands = client.get(
        "/v1/novacodepro/me/commands",
        headers=_headers("PRODUCT_MANAGER", "usr_djuma"),
    )
    assert product_commands.status_code == 200
    assert any(item["label"] == "Open Product Portfolio" for item in product_commands.json())

    product_queued = client.post(
        "/v1/novacodepro/commands/execute",
        headers=_headers("PRODUCT_MANAGER", "usr_djuma"),
        json={"command": "Open Product Portfolio"},
    )
    assert product_queued.status_code == 200
    assert product_queued.json()["status"] == "queued"
    assert product_queued.json()["requires_confirmation"] is False


def test_command_execution_supports_business_analyst_and_project_roles(tmp_path: Path) -> None:
    client = _client(tmp_path)

    business_commands = client.get(
        "/v1/novacodepro/me/commands",
        headers=_headers("BUSINESS_ANALYST", "usr_djuma"),
    )
    assert business_commands.status_code == 200
    assert any(item["label"] == "Create Business Requirement" for item in business_commands.json())

    business_queued = client.post(
        "/v1/novacodepro/commands/execute",
        headers=_headers("BUSINESS_ANALYST", "usr_djuma"),
        json={"command": "Create Business Requirement"},
    )
    assert business_queued.status_code == 200
    assert business_queued.json()["status"] == "queued"

    design_commands = client.get(
        "/v1/novacodepro/me/commands",
        headers=_headers("UI_UX_DESIGNER", "usr_djuma"),
    )
    assert design_commands.status_code == 200
    assert any(item["label"] == "Create Wireframe" for item in design_commands.json())

    design_queued = client.post(
        "/v1/novacodepro/commands/execute",
        headers=_headers("UI_UX_DESIGNER", "usr_djuma"),
        json={"command": "Create Wireframe"},
    )
    assert design_queued.status_code == 200
    assert design_queued.json()["status"] == "queued"

    project_commands = client.get(
        "/v1/novacodepro/me/commands",
        headers=_headers("PROJECT_MANAGER", "usr_djuma"),
    )
    assert project_commands.status_code == 200
    assert any(item["label"] == "Create Project" for item in project_commands.json())

    project_queued = client.post(
        "/v1/novacodepro/commands/execute",
        headers=_headers("PROJECT_MANAGER", "usr_djuma"),
        json={"command": "Create Project"},
    )
    assert project_queued.status_code == 200
    assert project_queued.json()["status"] == "queued"
