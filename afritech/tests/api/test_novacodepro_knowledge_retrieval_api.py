from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import build_auth_router, build_novacodepro_session_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(platform))
    app.include_router(build_novacodepro_session_router())
    return TestClient(app)


def test_ncp005_retrieval_returns_citations(tmp_path: Path) -> None:
    client = _client(tmp_path)
    client.post(
        "/v1/novacodepro/session/login",
        json={"email": "productmanager.test@afritechnology.com", "password": "NovaCodePro123!", "role": "PRODUCT_MANAGER"},
    )
    workspace_id = client.get("/v1/novacodepro/workspaces").json()["workspaces"][0]["id"]
    client.post(f"/v1/novacodepro/workspaces/{workspace_id}/select")
    client.post(
        "/v1/novacodepro/knowledge/documents",
        json={
            "space_id": "workspace-knowledge",
            "title": "Retrieval article",
            "summary": "Article for retrieval",
            "content_type": "GENERAL_DOCUMENT",
            "classification": "INTERNAL",
            "body": "This document should be returned with citations.",
        },
    )

    retrieval = client.post(
        "/v1/novacodepro/knowledge/retrieve",
        json={
            "query": "citations",
            "allowed_resource_types": ["knowledge_documents"],
            "classification_limit": "INTERNAL",
            "maximum_results": 5,
            "purpose": "assistant",
        },
    )
    assert retrieval.status_code == 200
    assert "retrieval" in retrieval.json()

    answer = client.post("/v1/novacodepro/knowledge/answer", json={"query": "citations"})
    assert answer.status_code == 200
    assert "citations" in answer.json()
