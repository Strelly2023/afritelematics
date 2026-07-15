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
    assert len(manifest["layers"]) == 10
    assert manifest["layers"][3]["name"] == "Knowledge & Intelligence Plane"
    assert manifest["layers"][4]["id"] == "enterprise-ai"
    assert manifest["layers"][5]["id"] == "digital-twin-resilience"
    assert "NovaDigitalTwin" in manifest["knowledge_and_intelligence"]["services"]


def test_nera_endpoint_exposes_reference_architecture(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/novacodepro/nera", headers=_headers("OBSERVER"))

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "NovaTech Enterprise Reference Architecture"
    assert len(body["layers"]) == 10


def test_architecture_framework_endpoint_exposes_multi_view_model(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/novacodepro/architecture-framework", headers=_headers("OBSERVER"))

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "NovaTech AI-Native Enterprise Operating System Framework"
    assert set(body["models"]) >= {"neaf", "nera", "necm", "neom", "nedm", "nekm", "netm", "negm", "neam", "nedtm", "ndtm", "nerm"}
    assert body["models"]["necm"]["capabilities"][0] == "Strategy, Governance & Leadership"
    assert body["models"]["nedtm"]["id"] == "nedtm"
    assert body["models"]["ndtm"]["alias_for"] == "nedtm"


def test_enterprise_model_endpoints_are_queryable(tmp_path: Path) -> None:
    client = _client(tmp_path)

    expected = {
        "/v1/novacodepro/capabilities": "necm",
        "/v1/novacodepro/operating-model": "neom",
        "/v1/novacodepro/data-model": "nedm",
        "/v1/novacodepro/knowledge-model": "nekm",
        "/v1/novacodepro/technology-model": "netm",
        "/v1/novacodepro/governance-model": "negm",
        "/v1/novacodepro/ai-model": "neam",
        "/v1/novacodepro/digital-twin-model": "nedtm",
        "/v1/novacodepro/resilience-model": "nerm",
    }

    for path, model_id in expected.items():
        response = client.get(path, headers=_headers("OBSERVER"))
        assert response.status_code == 200
        assert response.json()["id"] == model_id
