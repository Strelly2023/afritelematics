from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(service))
    return TestClient(app)


def _headers(role: str = "OPERATOR", user_id: str = "platform-admin") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def test_novacodepro_platform_creates_and_advances_workflows(tmp_path: Path) -> None:
    client = _client(tmp_path)

    summary = client.get("/v1/novacodepro/admin/summary", headers=_headers())
    assert summary.status_code == 200
    assert summary.json()["platform_health"] in {"healthy", "attention"}
    assert summary.json()["service_health"]["healthy"] >= 1

    status = client.get("/v1/novacodepro/status", headers=_headers())
    assert status.status_code == 200
    assert status.json()["service"] == "novacodepro-platform"
    assert status.json()["tenant_count"] >= 3
    assert status.json()["automation_ready"] is True
    assert "Workflow Service" in status.json()["distributed_services"]

    created = client.post(
        "/v1/novacodepro/workflows",
        headers=_headers(role="DEVELOPER"),
        json={
            "title": "Ride platform for Melbourne",
            "request": "Build a governed ride platform for Melbourne.",
            "tenant_id": "novatech",
            "project_id": "nova-ride-platform",
            "template_id": "solution-factory",
            "domain": "mobility",
            "region": "Australia",
            "compliance": "high",
            "surfaces": ["Rider app", "Driver app", "Operations dashboard"],
        },
    )
    assert created.status_code == 200
    workflow_id = created.json()["id"]
    assert created.json()["status"] == "active"
    assert created.json()["stages"][0]["status"] == "in_progress"

    current = created.json()
    for _ in range(7):
        transitioned = client.post(
            f"/v1/novacodepro/workflows/{workflow_id}/transition",
            headers=_headers(role="DEVELOPER"),
            json={"action": "advance", "note": "advance"},
        )
        assert transitioned.status_code == 200
        current = transitioned.json()

    assert current["status"] == "waiting-approval"
    assert current["current_stage"]["kind"] == "human"

    approved = client.post(
        f"/v1/novacodepro/workflows/{workflow_id}/transition",
        headers=_headers(role="DEVELOPER"),
        json={"action": "approve", "note": "Architecture approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["approvals"]
    assert approved.json()["stage_index"] == 8

    artifact = client.post(
        "/v1/novacodepro/artifacts",
        headers=_headers(role="DEVELOPER"),
        json={
            "workflow_id": workflow_id,
            "kind": "architecture",
            "title": "C4 model",
            "uri": "repo://novacodepro/architecture/c4.json",
            "version": "v1",
            "checksum": "sha256-demo",
            "metadata": {"format": "json"},
        },
    )
    assert artifact.status_code == 200
    assert artifact.json()["workflow_id"] == workflow_id

    audit = client.get("/v1/novacodepro/audit", headers=_headers())
    assert audit.status_code == 200
    assert any(event["action"] == "workflow.created" for event in audit.json())


def test_novacodepro_platform_supports_collaboration_and_knowledge_graph(tmp_path: Path) -> None:
    client = _client(tmp_path)

    thread = client.post(
        "/v1/novacodepro/collaboration/threads",
        headers=_headers(role="DEVELOPER"),
        json={
            "tenant_id": "novatech",
            "project_id": "nova-ride-platform",
            "scope": "Release coordination",
            "participants": ["Release", "QA", "Operations"],
        },
    )
    assert thread.status_code == 200
    thread_id = thread.json()["id"]

    comment = client.post(
        f"/v1/novacodepro/collaboration/threads/{thread_id}/messages",
        headers=_headers(role="DEVELOPER"),
        json={"body": "Release evidence is ready for review.", "author": "Djuma"},
    )
    assert comment.status_code == 200
    assert comment.json()["messages"][0]["body"] == "Release evidence is ready for review."

    graph = client.get("/v1/novacodepro/knowledge-graph", headers=_headers())
    assert graph.status_code == 200
    assert any(node["id"] == "kg-request" for node in graph.json()["nodes"])

    linked = client.post(
        "/v1/novacodepro/knowledge-graph/link",
        headers=_headers(role="DEVELOPER"),
        json={"source_id": "kg-request", "target_id": "kg-release"},
    )
    assert linked.status_code == 200
    assert "kg-release" in linked.json()["source"]["links"]

    integrations = client.post(
        "/v1/novacodepro/integrations/connect",
        headers=_headers(role="DEVELOPER"),
        json={"integration_id": "jira"},
    )
    assert integrations.status_code == 200
    assert integrations.json()["status"] == "connected"


def test_novacodepro_platform_release_factory_and_command_center(tmp_path: Path) -> None:
    client = _client(tmp_path)

    workflow = client.post(
        "/v1/novacodepro/workflows",
        headers=_headers(role="DEVELOPER"),
        json={
            "title": "Healthcare operations platform",
            "request": "Build a governed healthcare operations platform.",
            "tenant_id": "novatech",
            "project_id": "nova-pay-core",
        },
    ).json()

    release = client.post(
        "/v1/novacodepro/releases",
        headers=_headers(role="DEVELOPER"),
        json={
            "workflow_id": workflow["id"],
            "title": "Healthcare pilot release",
            "channel": "pilot",
            "target": "staging",
            "notes": "Initial release bundle",
        },
    )
    assert release.status_code == 200
    release_id = release.json()["id"]

    advanced_release = client.post(
        f"/v1/novacodepro/releases/{release_id}/transition",
        headers=_headers(role="DEVELOPER"),
        json={"action": "advance", "note": "Build complete"},
    )
    assert advanced_release.status_code == 200
    assert advanced_release.json()["stage_index"] == 1

    command = client.post(
        "/v1/novacodepro/commands",
        headers=_headers(role="DEVELOPER"),
        json={
            "command": "Generate multi-tenant customer portal",
            "context": {"tenant_id": "novatech", "project_id": "nova-ride-platform"},
        },
    )
    assert command.status_code == 200
    assert command.json()["status"] == "solution_created"
    assert command.json()["solution"]["title"] == "Generate multi-tenant customer portal"

    status = client.get("/v1/novacodepro/status", headers=_headers())
    assert status.status_code == 200
    assert status.json()["workflow_count"] >= 2
    assert status.json()["release_count"] >= 1


def test_novacodepro_platform_cloud_native_services(tmp_path: Path) -> None:
    client = _client(tmp_path)

    solution = client.post(
        "/v1/novacodepro/solutions",
        headers=_headers(role="DEVELOPER"),
        json={
            "title": "International payments platform",
            "request": "Build a governed cross-border payments platform.",
            "tenant_id": "novatech",
            "project_id": "nova-pay-core",
            "template_id": "solution-factory",
            "domain": "payments",
            "region": "Australia",
            "compliance": "high",
            "surfaces": ["Payments console", "Ledger", "Admin portal"],
            "version": "2027.1.0",
        },
    )
    assert solution.status_code == 200
    solution_id = solution.json()["id"]
    assert solution.json()["workflow_id"]

    solution_record = client.get(f"/v1/novacodepro/solutions/{solution_id}", headers=_headers())
    assert solution_record.status_code == 200
    assert solution_record.json()["status"] == "solution_factory_running"

    execution = client.post(
        "/v1/novacodepro/agents/executions",
        headers=_headers(role="DEVELOPER"),
        json={
            "agent_id": "architecture-agent",
            "version": "2027.1.0",
            "category": "engineering",
            "tenant_id": "novatech",
            "project_id": "nova-pay-core",
            "workflow_id": solution_record.json()["workflow_id"],
            "stage_id": "architecture",
            "input": {"request": "Governed payments platform"},
            "output": {"artifact": "architecture-pack"},
            "allowed_tools": ["artifact.read", "artifact.write", "knowledge.query"],
            "forbidden_tools": ["production.deploy"],
            "timeout_seconds": 900,
            "maximum_cost": 10.0,
            "approval_policy": "architecture-review-required",
            "evidence": ["architecture-pack"],
        },
    )
    assert execution.status_code == 200
    assert execution.json()["status"] == "completed"

    approval = client.post(
        "/v1/novacodepro/approvals",
        headers=_headers(role="DEVELOPER"),
        json={
            "gate_type": "SECURITY_APPROVAL",
            "workflow_id": solution_record.json()["workflow_id"],
            "release_id": "release-payments",
            "requested_by": "platform-admin",
            "conditions": ["Enable enhanced monitoring"],
            "evidence_ids": ["evidence-threat-model"],
        },
    )
    assert approval.status_code == 200
    approval_id = approval.json()["id"]
    assert approval.json()["status"] == "PENDING"

    approval_decision = client.post(
        f"/v1/novacodepro/approvals/{approval_id}/approve",
        headers=_headers(role="ADMIN"),
        json={"note": "Security approval granted"},
    )
    assert approval_decision.status_code == 200
    assert approval_decision.json()["status"] == "APPROVED"

    deployment = client.post(
        "/v1/novacodepro/deployments",
        headers=_headers(role="DEVELOPER"),
        json={
            "workflow_id": solution_record.json()["workflow_id"],
            "release_id": "release-payments",
            "environment": "staging",
            "region": "Australia",
            "version": "2027.1.0",
        },
    )
    assert deployment.status_code == 200
    deployment_id = deployment.json()["id"]
    assert deployment.json()["status"] == "provisioning"

    transitioned = client.post(
        f"/v1/novacodepro/deployments/{deployment_id}/transition",
        headers=_headers(role="DEVELOPER"),
        json={"action": "complete", "note": "Deployment verified"},
    )
    assert transitioned.status_code == 200
    assert transitioned.json()["status"] == "healthy"

    twin = client.get("/v1/novacodepro/digital-twins/twin-novacodepro", headers=_headers())
    assert twin.status_code == 200
    assert twin.json()["id"] == "twin-novacodepro"

    topology = client.get("/v1/novacodepro/digital-twins/twin-novacodepro/topology", headers=_headers())
    assert topology.status_code == 200
    assert "Workflow Service" in topology.json()["services"]

    health = client.get("/v1/novacodepro/digital-twins/twin-novacodepro/health", headers=_headers())
    assert health.status_code == 200
    assert health.json()["status"] in {"healthy", "degraded"}

    events = client.get("/v1/novacodepro/events", headers=_headers())
    assert events.status_code == 200
    assert any(event["event_type"] == "solution.created" for event in events.json())


def test_platform_admin_session_bootstrap_returns_canonical_context(tmp_path: Path) -> None:
    client = _client(tmp_path)

    login = client.post(
        "/v1/novacodepro/session/login",
        json={
            "identifier": "djuma.platformadmin",
            "password": "NovaCodePro123!",
            "role": "ADMIN",
        },
    )
    assert login.status_code == 200

    bootstrap = client.get("/v1/novacodepro/session")
    assert bootstrap.status_code == 200
    body = bootstrap.json()
    assert body["authenticated"] is True
    assert body["canonical_role"] == "PLATFORM_ADMIN"
    assert "ADMIN" in body["roles"]
    assert "PLATFORM_ADMIN" in body["roles"]
    assert body["workspace"]["id"] == "novatech-platform"
    assert body["default_route"] == "/novacodepro/dashboard"
    assert body["modules"]["nera"]["id"] == "nera"
    assert body["modules"]["eros"]["id"] == "eros"


def test_session_bootstrap_requires_authentication(tmp_path: Path) -> None:
    client = _client(tmp_path)

    bootstrap = client.get("/v1/novacodepro/session")
    assert bootstrap.status_code == 401
    assert bootstrap.json()["detail"]["code"] == "session_required"
