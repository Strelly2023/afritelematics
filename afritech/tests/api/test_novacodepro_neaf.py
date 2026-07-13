from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(platform))
    return TestClient(app)


def _headers(role: str, user_id: str = "usr_djuma") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def test_neaf_manifest_is_plane_based(tmp_path: Path) -> None:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "platform.sqlite3"))

    manifest = service.neaf_manifest()

    assert manifest["name"] == "NovaTech Enterprise Plane Model"
    assert manifest["sequence"] == [
        "Governance Plane",
        "Intelligence Plane",
        "Execution Plane",
        "Product Plane",
        "Infrastructure Plane",
    ]
    assert len(manifest["planes"]) == 5
    assert manifest["planes"][1]["platforms"][6] == "NovaDigitalTwin"


def test_neaf_endpoint_exposes_plane_model(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/novacodepro/neaf", headers=_headers("OBSERVER"))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "nepm"
    assert body["planes"][0]["owner"] == "NovaGovernance"
