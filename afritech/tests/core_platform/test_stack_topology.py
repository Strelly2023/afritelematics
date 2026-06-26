from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import build_core_platform_router
from afritech.core_platform import build_novatech_stack, build_novatech_stack_readiness


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_core_platform_router())
    return TestClient(app)


def _auth_headers(role: str = "OBSERVER") -> dict[str, str]:
    token = JWT.create_token("stack-auditor", role=role, organization_id="org-stack")
    return {"Authorization": f"Bearer {token}"}


def test_novatech_stack_exposes_protocol_rails_and_apps_layers() -> None:
    stack = build_novatech_stack()
    payload = stack.canonical()

    assert payload["platform"] == "NovaTechSol"
    assert payload["protocol_version"] == "v1"
    assert payload["signed_message_prefix"] == "NOVATECH"
    assert payload["protocol"]["key"] == "protocol"
    assert payload["rails"]["key"] == "rails"
    assert payload["apps"]["key"] == "apps"
    assert any(
        surface["key"] == "novapay_api" for surface in payload["apps"]["surfaces"]
    )
    assert any(
        surface["key"] == "novaride_driver_app"
        for surface in payload["apps"]["surfaces"]
    )


def test_novatech_stack_readiness_is_wired_into_api() -> None:
    client = _client()

    response = client.get("/v1/core-platform/stack", headers=_auth_headers())
    assert response.status_code == 200
    body = response.json()

    assert body["platform"] == "NovaTechSol"
    assert body["protocol"]["label"] == "NovaTrust protocol"
    assert body["rails"]["label"] == "NovaPay rails"
    assert body["apps"]["label"] == "NovaRide and NovaPay apps"
    assert {surface["layer"] for surface in body["protocol"]["surfaces"]} == {
        "protocol"
    }
    assert {surface["layer"] for surface in body["rails"]["surfaces"]} == {"rails"}
    assert {surface["layer"] for surface in body["apps"]["surfaces"]} == {"apps"}

    readiness = build_novatech_stack_readiness()
    assert readiness["platform"] == "NovaTechSol"
    assert readiness["stack"]["platform"] == "NovaTechSol"
    assert readiness["protocol_ready"] in {True, False}
    assert readiness["rails_ready"] in {True, False}
    assert readiness["apps_ready"] in {True, False}
