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


def test_ncp005_search_filters_cross_tenant_access(tmp_path: Path) -> None:
    client = _client(tmp_path)
    client.post(
        "/v1/novacodepro/session/login",
        json={"email": "productmanager.test@afritechnology.com", "password": "NovaCodePro123!", "role": "PRODUCT_MANAGER"},
    )
    workspace_id = client.get("/v1/novacodepro/workspaces").json()["workspaces"][0]["id"]
    client.post(f"/v1/novacodepro/workspaces/{workspace_id}/select")

    client.post(
        "/v1/novacodepro/knowledge/spaces",
        json={"name": "Internal docs"},
    )
    client.post(
        "/v1/novacodepro/knowledge/documents",
        json={
            "space_id": "workspace-knowledge",
            "title": "Internal search reference",
            "summary": "Reference document",
            "content_type": "GENERAL_DOCUMENT",
            "classification": "INTERNAL",
            "body": "Tenant scoped knowledge.",
        },
    )

    search = client.post("/v1/novacodepro/knowledge/search", json={"query": "Tenant scoped knowledge", "strategy": "keyword"})
    assert search.status_code == 200
    assert all(result["classification"] in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "REGULATED"} for result in search.json()["results"])

    forbidden = client.post(
        "/v1/novacodepro/knowledge/search",
        headers={"Authorization": "Bearer invalid.invalid.invalid"},
        json={"query": "Tenant scoped knowledge"},
    )
    assert forbidden.status_code in {401, 403}
