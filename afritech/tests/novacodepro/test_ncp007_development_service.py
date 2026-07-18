from __future__ import annotations

import subprocess
from pathlib import Path

from afritech.novacodepro import DevelopmentExecutionContext, NovaCodeProNCP007Service, NovaCodeProRepository


def _service(tmp_path: Path, monkeypatch) -> NovaCodeProNCP007Service:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# Development Studio Smoke\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "ncp007@example.com"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "NCP007"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    monkeypatch.setenv("NOVACODEPRO_REPO_ROOT", str(repo_root))
    return NovaCodeProNCP007Service(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"), repo_root=repo_root)


def _ctx(*, workspace_id: str | None = None, project_id: str | None = None, role: str = "DEVELOPER") -> DevelopmentExecutionContext:
    return DevelopmentExecutionContext(
        actor_id="developer.user",
        tenant_id="novatech",
        organization_id="novatech",
        workspace_id=workspace_id,
        project_id=project_id,
        role=role,
        permissions=(
            "development.workspace.read",
            "development.workspace.configure",
            "repository.read",
            "repository.patch.create",
            "repository.patch.apply",
            "repository.commit.prepare",
            "repository.commit.execute",
            "repository.pull_request.prepare",
            "repository.pull_request.create",
            "code.generate",
            "code.modify",
            "command.execute",
            "build.execute",
            "test.execute",
            "approval.request",
            "approval.review",
            "approval.grant",
            "approval.reject",
            "evidence.read",
        ),
        session_id="session-dev",
        correlation_id="corr-dev",
        causation_id="corr-dev",
    )


def test_ncp007_development_workspace_generation_and_evidence(tmp_path: Path, monkeypatch) -> None:
    service = _service(tmp_path, monkeypatch)
    ctx = _ctx()

    workspace = service.create_workspace({"name": "Development Workspace", "description": "Governed code generation"}, ctx)
    assert workspace["status"] in {"DRAFT", "READY", "ACTIVE"}
    assert service.list_workspaces(ctx)

    workspace_ctx = _ctx(workspace_id=workspace["id"])

    session = service.create_session(workspace["id"], {"objective": "Create a governed patch"}, workspace_ctx)
    assert session["status"] in {"PLANNING", "ACTIVE"}
    assert service.get_session(session["id"], ctx)["id"] == session["id"]

    task = service.create_task(
        session["id"],
        {
            "title": "Create development studio artifact",
            "description": "Implement governed code generation smoke test",
            "task_type": "TEST",
            "risk_level": "LOW",
        },
        workspace_ctx,
    )
    assert task["status"] in {"OPEN", "DRAFT", "ACTIVE"}

    request = service.create_generation_request(
        task["id"],
        {
            "instruction": "Create a deterministic development artifact.",
            "target_files": ["novacodepro/generated/ncp007-smoke.py"],
            "generation_mode": "CREATE",
            "model_provider": "deterministic-test",
            "model_name": "rules",
        },
        workspace_ctx,
    )

    change_set = request["change_set"]
    assert request["request"]["status"] == "GENERATED"
    assert change_set["status"] in {"GENERATED", "READY_FOR_REVIEW"}
    assert change_set["files_added_count"] + change_set["files_modified_count"] >= 1
    assert change_set["evidence_reference"]

    files = service.list_change_set_files(change_set["id"], workspace_ctx)
    assert files and files[0]["path"].endswith("ncp007-smoke.py")

    validations = service.list_validation_runs(change_set["id"], workspace_ctx)
    assert validations and validations[0]["validation_type"] == "FORMAT"

    review = service.create_review(change_set["id"], {"summary": "Review governed generation"}, workspace_ctx)
    assert review["status"] == "PENDING"
    reviewed = service.decide_review(review["id"], "APPROVED", workspace_ctx)
    assert reviewed["status"] == "APPROVED"

    approver_ctx = DevelopmentExecutionContext(
        actor_id="tech.lead",
        tenant_id=workspace_ctx.tenant_id,
        organization_id=workspace_ctx.organization_id,
        workspace_id=workspace_ctx.workspace_id,
        project_id=workspace_ctx.project_id,
        role="TECH_LEAD",
        permissions=ctx.permissions,
        session_id=ctx.session_id,
        correlation_id="corr-approver",
    )
    approval = service.request_approval(change_set["id"], {"approver_id": "tech.lead", "required_role": "TECH_LEAD"}, workspace_ctx)
    assert approval["decision"] == "PENDING"
    decided = service.decide_approval(approval["id"], "APPROVED", approver_ctx, {"reason": "Governed change approved"})
    assert decided["decision"] == "APPROVED"

    commit_proposal = service.create_commit_proposal(change_set["id"], {"branch_name": "feature/ncp007-smoke"}, workspace_ctx)
    assert commit_proposal["status"] == "READY"

    pr_proposal = service.create_pull_request_proposal(change_set["id"], {"title": "NCP-007 smoke"}, workspace_ctx)
    assert pr_proposal["status"] == "READY"

    command_run = service.execute_command(session["id"], {"command": ["git", "status", "--short"]}, workspace_ctx)
    assert command_run["status"] in {"SUCCEEDED", "FAILED"}

    timeline = service.timeline(workspace_ctx, session_id=session["id"])
    assert timeline
    evidence = service.evidence(workspace_ctx, session_id=session["id"], change_set_id=change_set["id"])
    assert evidence


def test_ncp007_cross_tenant_workspace_forbidden(tmp_path: Path, monkeypatch) -> None:
    service = _service(tmp_path, monkeypatch)
    ctx = _ctx()
    workspace = service.create_workspace({"name": "Tenant Workspace"}, ctx)
    other_ctx = DevelopmentExecutionContext(
        actor_id="other.user",
        tenant_id="other-tenant",
        organization_id="other-tenant",
        workspace_id=workspace["id"],
        project_id=ctx.project_id,
        role="DEVELOPER",
        permissions=("development.workspace.read", "repository.read"),
        session_id="other-session",
        correlation_id="corr-other",
    )
    try:
        service.get_workspace(workspace["id"], other_ctx)
    except Exception as error:  # noqa: BLE001
        assert getattr(error, "code", "") == "cross_tenant_development_forbidden"
    else:  # pragma: no cover - defensive
        raise AssertionError("expected cross-tenant access to fail")
