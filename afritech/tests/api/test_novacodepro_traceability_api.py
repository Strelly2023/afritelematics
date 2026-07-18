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


def test_ncp005_traceability_snapshot_and_resources(tmp_path: Path) -> None:
    client = _client(tmp_path)
    client.post(
        "/v1/novacodepro/session/login",
        json={"email": "productmanager.test@afritechnology.com", "password": "NovaCodePro123!", "role": "PRODUCT_MANAGER"},
    )
    workspace_id = client.get("/v1/novacodepro/workspaces").json()["workspaces"][0]["id"]
    client.post(f"/v1/novacodepro/workspaces/{workspace_id}/select")
    requirement_set = client.post("/v1/novacodepro/requirement-sets", json={"name": "Traceability set"}).json()["id"]

    requirement = client.post(
        "/v1/novacodepro/requirements",
        json={"workspace_id": workspace_id, "requirement_set_id": requirement_set, "title": "Traceability requirement", "type": "FUNCTIONAL"},
    ).json()
    link = client.post(
        "/v1/novacodepro/traceability/links",
        json={
            "source_type": "REQUIREMENT",
            "source_id": requirement["id"],
            "target_type": "EVIDENCE",
            "target_id": "evidence-1",
            "relationship": "EVIDENCED_BY",
        },
    )
    assert link.status_code == 200
    link_id = link.json()["id"]

    resource = client.get(f"/v1/novacodepro/traceability/resources/REQUIREMENT/{requirement['id']}")
    assert resource.status_code == 200
    assert resource.json()["resource_id"] == requirement["id"]

    snapshot = client.post("/v1/novacodepro/traceability/snapshots", json={"requirement_set_id": requirement_set})
    assert snapshot.status_code == 200
    snapshot_id = snapshot.json()["id"]

    loaded = client.get(f"/v1/novacodepro/traceability/snapshots/{snapshot_id}")
    assert loaded.status_code == 200

    deleted = client.delete(f"/v1/novacodepro/traceability/links/{link_id}")
    assert deleted.status_code == 200
