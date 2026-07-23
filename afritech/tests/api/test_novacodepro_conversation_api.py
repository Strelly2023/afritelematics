from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import build_auth_router, build_novacodepro_session_router
from afritech.api.auth.novacodepro_session_store import NovaCodeProSessionStore
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    session_store = NovaCodeProSessionStore(tmp_path / "novacodepro-auth.sqlite3")
    app = FastAPI()
    app.include_router(build_auth_router(session_store=session_store))
    app.include_router(build_novacodepro_platform_router(platform))
    app.include_router(build_novacodepro_session_router(session_store=session_store))
    return TestClient(app)


def _login_and_select_workspace(client: TestClient) -> str:
    login = client.post(
        "/v1/novacodepro/session/login",
        json={"email": "productmanager.test@afritechnology.com", "password": "NovaCodePro123!", "role": "PRODUCT_MANAGER"},
    )
    assert login.status_code == 200
    workspace_id = client.get("/v1/novacodepro/workspaces").json()["workspaces"][0]["id"]
    selected = client.post(f"/v1/novacodepro/workspaces/{workspace_id}/select")
    assert selected.status_code == 200
    return workspace_id


def test_conversation_first_workspace_api_persists_messages_and_context(tmp_path: Path) -> None:
    client = _client(tmp_path)
    workspace_id = _login_and_select_workspace(client)

    create = client.post(
        "/v1/novacodepro/conversations",
        headers={"Idempotency-Key": "conversation-first-001"},
        json={
            "title": "Create architecture for a trusted rideshare platform",
            "summary": "Conversation-first request for NovaRide",
            "prompt": "Create architecture for a trusted rideshare platform.",
            "workspace_id": workspace_id,
            "repository": "afritelematics",
            "branch": "main",
            "environment": "development",
            "context_sources": ["Workspace", "Repository", "Requirement"],
            "context": {
                "workspace": workspace_id,
                "repository": "afritelematics",
                "branch": "main",
                "environment": "development",
            },
        },
    )
    assert create.status_code == 200
    conversation_id = create.json()["id"]
    assert create.json()["message_count"] == 1
    duplicate = client.post(
        "/v1/novacodepro/conversations",
        headers={"Idempotency-Key": "conversation-first-001"},
        json={"title": "Duplicate", "workspace_id": workspace_id},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == conversation_id

    listing = client.get("/v1/novacodepro/conversations", params={"workspace_id": workspace_id, "query": "rideshare"})
    assert listing.status_code == 200
    assert any(item["id"] == conversation_id for item in listing.json()["conversations"])

    ai_listing = client.get("/v1/novacodepro/ai/conversations", params={"workspace_id": workspace_id, "query": "rideshare"})
    assert ai_listing.status_code == 200
    assert any(item["id"] == conversation_id for item in ai_listing.json()["conversations"])

    detail = client.get(f"/v1/novacodepro/conversations/{conversation_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Create architecture for a trusted rideshare platform"

    message = client.post(
        f"/v1/novacodepro/conversations/{conversation_id}/messages",
        json={
            "type": "ai_response",
            "role": "NovaAI",
            "body": "Here is the first governed architecture outline.",
            "artifact_refs": ["architecture-outline"],
            "evidence_refs": ["evidence-001"],
        },
    )
    assert message.status_code == 200
    assert message.json()["message_count"] == 2

    context = client.get(f"/v1/novacodepro/conversations/{conversation_id}/context")
    assert context.status_code == 200
    assert context.json()["context"]["repository"] == "afritelematics"

    artifacts = client.get(f"/v1/novacodepro/conversations/{conversation_id}/artifacts")
    assert artifacts.status_code == 200
    assert artifacts.json()["artifacts"] == []

    traceability = client.get(f"/v1/novacodepro/conversations/{conversation_id}/traceability")
    assert traceability.status_code == 200
    assert traceability.json()["evidence"] == []

    archived = client.post(f"/v1/novacodepro/conversations/{conversation_id}/archive")
    assert archived.status_code == 200
    assert archived.json()["archived"] is True

    restored = client.post(f"/v1/novacodepro/conversations/{conversation_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["archived"] is False

    deleted = client.delete(f"/v1/novacodepro/conversations/{conversation_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    refreshed = client.get(f"/v1/novacodepro/conversations/{conversation_id}")
    assert refreshed.status_code == 200
    assert refreshed.json()["deleted"] is True
