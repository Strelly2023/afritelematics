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


def test_nera_manifest_is_stable_and_layered(tmp_path: Path) -> None:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "platform.sqlite3"))

    manifest = service.nera_manifest()

    assert manifest["name"] == "NovaTech Enterprise Reference Architecture"
    assert len(manifest["layers"]) == 8
    assert manifest["layers"][3]["name"] == "Knowledge & Intelligence Layer"
    assert "NovaDigitalTwin" in manifest["knowledge_and_intelligence"]["services"]


def test_nera_endpoint_exposes_reference_architecture(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/novacodepro/nera", headers=_headers("OBSERVER"))

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "NovaTech Enterprise Reference Architecture"
    assert len(body["layers"]) == 8


def test_architecture_framework_endpoint_exposes_multi_view_model(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/novacodepro/architecture-framework", headers=_headers("OBSERVER"))

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "NovaTech Enterprise Architecture Framework"
    assert set(body["models"]) >= {"nera", "necm", "neom", "nerm", "ndtm"}
    assert body["models"]["necm"]["capabilities"][0] == "Identity"
