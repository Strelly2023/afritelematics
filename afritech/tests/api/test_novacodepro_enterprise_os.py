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


def _headers(role: str, user_id: str = "usr_djuma") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def test_solution_package_creates_approval_knowledge_and_event_bus_snapshot(tmp_path: Path) -> None:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "platform.sqlite3"))

    package = service.orchestrate_solution_package(
        {
            "title": "NovaRide payment reconciliation",
            "request": "Build NovaRide payment reconciliation service with audit evidence and compliance checks.",
            "domain": "payments",
            "region": "Australia",
            "risk_level": "medium",
            "execution_enabled": False,
            "comments": ["Review routing", "Attach evidence"],
        }
    )

    assert package["solution"]["title"] == "NovaRide payment reconciliation"
    assert package["approval"]["solution_id"] == package["solution"]["id"]
    assert package["approval"]["knowledge_created"] is True
    assert package["knowledge_entry"]["solution_id"] == package["solution"]["id"]
    assert any(agent["id"] == "security-agent" for agent in package["agent_team"])
    assert any(agent["id"] == "compliance-agent" for agent in package["agent_team"])
    assert len(package["events"]) == 4

    snapshot = service.event_bus_snapshot()
    assert snapshot["domain_events"] >= 5
    assert snapshot["outbox_pending"] >= 1


def test_replay_knowledge_graph_persists_approved_nodes(tmp_path: Path) -> None:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "platform.sqlite3"))

    package = service.orchestrate_solution_package(
        {
            "title": "NovaCodePro architecture decision",
            "request": "Review the approval and knowledge graph lifecycle.",
            "risk_level": "medium",
        }
    )

    nodes = service.replay_knowledge_graph()
    assert nodes
    assert any(node["solution_id"] == package["solution"]["id"] for node in nodes)


def test_platform_api_exposes_solution_packages_and_queue_controls(tmp_path: Path) -> None:
    client = _client(tmp_path)

    package_response = client.post(
        "/v1/novacodepro/solutions/packages",
        headers=_headers("DEVELOPER"),
        json={
            "title": "Enterprise AI operating system",
            "request": "Create a governed AI operating system with approval objects and a knowledge graph.",
            "risk_level": "high",
            "execution_enabled": False,
        },
    )
    assert package_response.status_code == 200
    package = package_response.json()
    assert package["solution"]["title"] == "Enterprise AI operating system"
    assert package["approval"]["status"] in {"APPROVED", "REVIEWED"}

    bus_response = client.get("/v1/novacodepro/event-bus", headers=_headers("OBSERVER"))
    assert bus_response.status_code == 200
    assert "domain_events" in bus_response.json()

    retry_response = client.post(
        "/v1/novacodepro/retry-queue",
        headers=_headers("DEVELOPER"),
        json={
            "event_id": "evt-1001",
            "consumer_name": "knowledge-graph-consumer",
            "aggregate_id": "sol-1001",
            "event_type": "knowledge.entry.promoted",
            "payload": {"solution_id": "sol-1001"},
            "retry_count": 0,
            "next_retry_at": "2026-07-13T12:00:00Z",
            "last_error": "temporary timeout",
        },
    )
    assert retry_response.status_code == 200
    retry_id = retry_response.json()["id"]

    dead_letter_response = client.post(
        f"/v1/novacodepro/retry-queue/{retry_id}/dead-letter",
        headers=_headers("DEVELOPER"),
        json={"failure_reason": "invalid aggregate"},
    )
    assert dead_letter_response.status_code == 200

    queue_response = client.get("/v1/novacodepro/dead-letter-queue", headers=_headers("OBSERVER"))
    assert queue_response.status_code == 200
    assert queue_response.json()
