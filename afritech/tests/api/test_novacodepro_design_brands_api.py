from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import build_auth_router, build_novacodepro_session_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def test_brand_collection_is_tenant_scoped_and_versionable(tmp_path: Path) -> None:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_session_router())
    app.include_router(build_novacodepro_platform_router(platform))
    client = TestClient(app)
    login = client.post("/v1/novacodepro/session/login", json={"email": "platformadministrator.test@afritechnology.com", "password": "NovaCodePro123!", "role": "ADMIN"})
    assert login.status_code == 200
    response = client.post("/v1/novacodepro/design/brands", json={"name": "NovaPay", "attributes": {"colours": ["#0052cc"]}})
    assert response.status_code == 200
    brand = response.json()
    assert brand["name"] == "NovaPay"
    assert brand["tenant_id"]

    listed = client.get("/v1/novacodepro/design/brands")
    assert listed.status_code == 200
    assert brand["id"] in {item["id"] for item in listed.json()["brands"]}

    updated = client.patch(f"/v1/novacodepro/design/brands/{brand['id']}", json={"description": "Approved product brand"})
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
