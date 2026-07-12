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
    assert command.json()["status"] == "workflow_created"
    assert command.json()["workflow"]["title"] == "Generate multi-tenant customer portal"

    status = client.get("/v1/novacodepro/status", headers=_headers())
    assert status.status_code == 200
    assert status.json()["workflow_count"] >= 2
    assert status.json()["release_count"] >= 1
