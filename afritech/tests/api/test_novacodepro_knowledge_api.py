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
    app.include_router(build_novacodepro_platform_router(platform))
    app.include_router(build_novacodepro_session_router())
    return TestClient(app)


def _login(client: TestClient, role: str = "PRODUCT_MANAGER") -> None:
    response = client.post(
        "/v1/novacodepro/session/login",
        json={"email": "productmanager.test@afritechnology.com", "password": "NovaCodePro123!", "role": role},
    )
    assert response.status_code == 200


def test_ncp005_knowledge_publication_and_search(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)

    workspace_id = client.get("/v1/novacodepro/workspaces").json()["workspaces"][0]["id"]
    client.post(f"/v1/novacodepro/workspaces/{workspace_id}/select")

    space = client.post("/v1/novacodepro/knowledge/spaces", json={"name": "Architecture Knowledge"})
    assert space.status_code == 200
    space_id = space.json()["id"]

    document = client.post(
        "/v1/novacodepro/knowledge/documents",
        json={
            "space_id": space_id,
            "title": "NovaID architecture notes",
            "summary": "Notes for the NovaID integration",
            "content_type": "ARCHITECTURE_DOCUMENT",
            "visibility": "WORKSPACE",
            "classification": "INTERNAL",
            "body": "Identity verification and governed session flow.",
        },
    )
    assert document.status_code == 200
    document_id = document.json()["id"]

    review = client.post(f"/v1/novacodepro/knowledge/documents/{document_id}/reviews", json={"review_type": "ARCHITECTURE"})
    assert review.status_code == 200

    approval_request = client.post(f"/v1/novacodepro/knowledge/documents/{document_id}/approvals", json={"required_role": "PRODUCT_MANAGER"})
    assert approval_request.status_code == 200
    approval_id = approval_request.json()["id"]
    approval = client.post(f"/v1/novacodepro/knowledge/documents/{document_id}/approvals/{approval_id}/approve", json={"reason": "Approved for publication"})
    assert approval.status_code == 200

    published = client.post(f"/v1/novacodepro/knowledge/documents/{document_id}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"

    tagged = client.post("/v1/novacodepro/knowledge/tags", json={"name": "architecture"})
    assert tagged.status_code == 200

    search = client.post("/v1/novacodepro/knowledge/search", json={"query": "NovaID identity", "strategy": "hybrid"})
    assert search.status_code == 200
    assert search.json()["results"]

    answer = client.post("/v1/novacodepro/knowledge/answer", json={"query": "What is NovaID?"})
    assert answer.status_code == 200
    assert "citations" in answer.json()

    archived = client.post(f"/v1/novacodepro/knowledge/documents/{document_id}/archive")
    assert archived.status_code == 200
