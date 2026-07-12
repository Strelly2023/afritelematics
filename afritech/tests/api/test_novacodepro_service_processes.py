from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT
from afritech.novacodepro.distributed.process import build_process_app
from afritech.novacodepro.distributed.workers import AgentExecutionWorker, OutboxWorker
from afritech.novacodepro.processes import command_center_app, identity_context_app


def test_novacodepro_process_app_supports_async_workers_and_outbox(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "agent-service.sqlite3"
    monkeypatch.setenv("NOVACODEPRO_AGENT_DB_PATH", str(db_path))
    app = build_process_app(
        service_name="agent",
        db_env_var="NOVACODEPRO_AGENT_DB_PATH",
        title="NovaCodePro Agent Service",
        async_agents=True,
    )
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["service"] == "agent"

    token = JWT.create_token("platform-admin", role="DEVELOPER", organization_id="novatech")
    execution = client.post(
        "/v1/novacodepro/agents/executions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "agent_id": "architecture-agent",
            "version": "2027.1.0",
            "category": "engineering",
            "workflow_id": "workflow-ride-platform",
            "stage_id": "architecture",
            "input": {"request": "Governed payments platform"},
            "output": {"artifact": "architecture-pack"},
        },
    )
    assert execution.status_code == 200
    assert execution.json()["status"] == "queued"
    assert client.get("/v1/outbox").status_code == 200


def test_novacodepro_async_agent_worker_completes_queued_execution(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "agent-worker.sqlite3"
    monkeypatch.setenv("NOVACODEPRO_AGENT_DB_PATH", str(db_path))
    app = build_process_app(
        service_name="agent",
        db_env_var="NOVACODEPRO_AGENT_DB_PATH",
        title="NovaCodePro Agent Service",
        async_agents=True,
    )
    platform = app.state.platform
    platform.create_workflow(
        {
            "title": "Queued architecture workflow",
            "request": "Generate a governed architecture pack.",
            "tenant_id": "novatech",
            "project_id": "nova-ride-platform",
        }
    )
    execution = platform.create_agent_execution(
        {
            "agent_id": "architecture-agent",
            "workflow_id": platform.workflows()[0]["id"],
            "stage_id": "architecture",
            "input": {"request": "Governed payments platform"},
            "output": {},
            "async_mode": True,
        }
    )
    assert execution["status"] == "queued"
    assert platform.repository.list_outbox(limit=10)

    agent_worker = AgentExecutionWorker(platform=platform)
    result = agent_worker.run_once()
    assert result["processed"] >= 1
    assert platform.get_agent_execution(execution["id"])["status"] == "completed"

    outbox_worker = OutboxWorker(platform=platform)
    drained = outbox_worker.run_once()
    assert drained["published"] >= 1


def test_novacodepro_additional_service_processes_are_exposed() -> None:
    identity_client = TestClient(identity_context_app)
    command_client = TestClient(command_center_app)

    assert identity_client.get("/health").json()["service"] == "identity-context"
    assert command_client.get("/health").json()["service"] == "command-center"
