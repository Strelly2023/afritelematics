from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import build_auth_router, build_novacodepro_session_router
from afritech.api.auth.novacodepro_session_store import NovaCodeProSessionStore
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.api.novacodepro_workspace_api import build_novacodepro_workspace_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    session_store = NovaCodeProSessionStore(tmp_path / "novacodepro-auth.sqlite3")
    app = FastAPI()
    app.include_router(build_auth_router(session_store=session_store))
    app.include_router(build_novacodepro_platform_router(platform))
    app.include_router(build_novacodepro_session_router(session_store=session_store))
    app.include_router(build_novacodepro_workspace_router(platform))
    return TestClient(app)


def test_login_session_workspace_and_logout_cycle(tmp_path: Path) -> None:
    client = _client(tmp_path)

    signed_out = client.get("/v1/novacodepro/workspace")
    assert signed_out.status_code == 401

    login = client.post(
        "/v1/novacodepro/session/login",
        json={
            "email": "platformadministrator.test@afritechnology.com",
            "password": "NovaCodePro123!",
            "role": "ADMIN",
        },
    )
    assert login.status_code == 200
    login_body = login.json()
    assert login_body["user"]["display_name"] == "Djuma Platform Administrator"
    assert login_body["user"]["active_role"] == "ADMIN"

    session = client.get("/v1/novacodepro/session")
    assert session.status_code == 200
    assert session.json()["canonical_role"] == "PLATFORM_ADMIN"
    assert session.json()["workspace"]["home_route"] == "/novacodepro/dashboard"

    workspace = client.get("/v1/novacodepro/workspace")
    assert workspace.status_code == 200
    assert workspace.json()["workspace"]["title"] == "Platform Administration Workspace"

    logout = client.post("/v1/novacodepro/session/logout")
    assert logout.status_code == 200
    assert logout.json()["status"] == "logged_out"

    revoked = client.get("/v1/novacodepro/workspace")
    assert revoked.status_code == 401

    session_after_logout = client.get("/v1/novacodepro/session")
    assert session_after_logout.status_code == 401


def test_canonical_session_aliases_work_without_platform_router(tmp_path: Path) -> None:
    session_store = NovaCodeProSessionStore(tmp_path / "novacodepro-auth.sqlite3")
    app = FastAPI()
    app.include_router(build_novacodepro_session_router(session_store=session_store))
    client = TestClient(app)

    login = client.post(
        "/v1/novacodepro/session/login",
        json={
            "email": "platformadministrator.test@afritechnology.com",
            "password": "NovaCodePro123!",
            "role": "ADMIN",
        },
    )
    assert login.status_code == 200
    assert login.json()["user"]["active_role"] == "ADMIN"

    session = client.get("/v1/novacodepro/session")
    assert session.status_code == 200
    assert session.json()["active_role"] == "ADMIN"

    bootstrap = client.get("/v1/novacodepro/session/bootstrap")
    assert bootstrap.status_code == 200
    assert bootstrap.json()["active_role"] == "ADMIN"

    refresh = client.post("/v1/novacodepro/session/refresh")
    assert refresh.status_code == 200

    logout = client.post("/v1/novacodepro/session/logout")
    assert logout.status_code == 200


def test_super_account_can_switch_roles(tmp_path: Path) -> None:
    client = _client(tmp_path)

    login = client.post(
        "/v1/novacodepro/session/login",
        json={
            "email": "djstrelly@gmail.com",
            "password": "NovaCodePro123!",
            "role": "ADMIN",
        },
    )
    assert login.status_code == 200

    switch_role = client.post("/v1/auth/switch-role", json={"role": "DEVELOPER"})
    assert switch_role.status_code == 200
    assert switch_role.json()["session"]["active_role"] == "DEVELOPER"

    switched_workspace = client.get("/v1/novacodepro/workspace")
    assert switched_workspace.status_code == 200
    assert switched_workspace.json()["workspace"]["title"] == "Developer Workspace"


def test_invalid_login_and_forbidden_role_switch(tmp_path: Path) -> None:
    client = _client(tmp_path)

    invalid = client.post(
        "/v1/novacodepro/session/login",
        json={
            "email": "developer.test@afritechnology.com",
            "password": "wrong-password",
            "role": "DEVELOPER",
        },
    )
    assert invalid.status_code == 401

    login = client.post(
        "/v1/novacodepro/session/login",
        json={
            "email": "developer.test@afritechnology.com",
            "password": "NovaCodePro123!",
            "role": "DEVELOPER",
        },
    )
    assert login.status_code == 200

    forbidden = client.post("/v1/auth/switch-role", json={"role": "ADMIN"})
    assert forbidden.status_code == 403
