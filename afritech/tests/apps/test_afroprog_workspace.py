from __future__ import annotations

from afritech.afroprog_workspace.models import afroprog_seed_projects
from afritech.afroprog_workspace.service import AfriProAIService, seed_session
from afritech.afroprog_workspace.workspace import (
    build_workspace_payload,
    render_afroprog_dashboard_view,
    render_chat_view,
)


def test_afroprog_ai_service_generates_poultry_django_bundle() -> None:
    project = afroprog_seed_projects()[0]
    session = seed_session(project)
    response = AfriProAIService().generate_code(
        "Create Django model for poultry farm and vaccination tracking",
        mode="code",
        project=project,
        session=session,
    )
    payload = response.canonical_dict()

    paths = [item["path"] for item in payload["files"]]
    assert "poultry/apps/farm/models.py" in paths
    assert "poultry/apps/farm/serializers.py" in paths
    assert payload["governance_view"]["authority_boundary_preserved"] is True
    assert payload["execution_preview"]["mutation_allowed"] is False
    assert payload["evidence"]["design_domain"] == "poultry_management"


def test_workspace_payload_is_codex_style_and_governance_linked() -> None:
    payload = build_workspace_payload(
        prompt="Create Django API for poultry farm",
        mode="analysis",
    )

    assert payload["dashboard_title"] == "AfriPro Dashboard"
    assert payload["workspace_mode"] == "codex_style"
    assert payload["proposal_only"] is True
    assert payload["governance_linked"] is True
    assert payload["chat_panel"]["response"]["governance_view"]["target_is_governed_execution"] is True


def test_render_chat_view_returns_project_and_response() -> None:
    payload = render_chat_view(
        prompt="Create API for employee management",
        mode="code",
        project_id="project-employee-rbac",
    )

    assert payload["view"] == "afroprog_chat"
    assert payload["project"]["project_id"] == "project-employee-rbac"
    assert payload["response"]["files"][0]["path"] == "employee_api/models.py"


def test_render_dashboard_view_preserves_non_authority_boundary() -> None:
    payload = render_afroprog_dashboard_view()

    assert payload["view"] == "afroprog_dashboard"
    assert payload["read_only"] is True
    assert payload["proposal_only"] is True
    assert payload["creates_authority"] is False
