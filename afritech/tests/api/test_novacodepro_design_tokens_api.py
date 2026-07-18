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
    app.include_router(build_novacodepro_session_router())
    app.include_router(build_novacodepro_platform_router(platform))
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post("/v1/novacodepro/session/login", json={"email": "platformadministrator.test@afritechnology.com", "password": "NovaCodePro123!", "role": "ADMIN"})
    assert response.status_code == 200


def test_ncp006b_design_token_validation_rejects_cycles(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)
    validation = client.post(
        "/v1/novacodepro/design/tokens/validate",
        json={"tokens": [{"path": "color.brand.primary", "name": "color.brand.primary", "category": "COLOR", "level": "SEMANTIC", "value": "#0052cc", "reference": "color.brand.primary"}]},
    )
    assert validation.status_code == 400
    assert validation.json()["detail"]["code"] == "design_token_invalid"


def test_ncp006b_design_theme_and_component_contract_routes(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)
    token = client.post("/v1/novacodepro/design/tokens", json={"path": "color.brand.primary", "name": "color.brand.primary", "category": "COLOR", "level": "SEMANTIC", "value": "#0052cc"})
    assert token.status_code == 200
    component = client.post(
        "/v1/novacodepro/design/components",
        json={"name": "Primary Button", "properties": [{"name": "label", "type": "string"}], "keyboard_behavior": "Enter and Space", "focus_behavior": "Visible", "screen_reader_behavior": "Announces label"},
    )
    assert component.status_code == 200
    contract = client.post(f"/v1/novacodepro/design/components/{component.json()['id']}/implementation-contract", json={"framework": "react", "package_name": "@novacodepro/design", "export_name": "PrimaryButton"})
    assert contract.status_code == 200
    publish = client.post(f"/v1/novacodepro/design/components/{component.json()['id']}/implementation-contract/publish")
    assert publish.status_code == 200
