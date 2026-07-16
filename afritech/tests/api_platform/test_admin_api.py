from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import afritech.api.api_platform_admin_api as admin_api
from afritech.api_platform import EndpointRegistry


def test_api_platform_admin_router_registers_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_api,
        "require_roles",
        lambda *roles: (lambda: {"roles": roles}),
    )
    registry = EndpointRegistry()
    app = FastAPI()
    app.include_router(admin_api.build_api_platform_admin_router(registry))
    client = TestClient(app)

    payload = {
        "endpoint_id": "novafleet.register-vehicle.v1",
        "product_code": "novafleet",
        "path": "/v1/novafleet/vehicles",
        "methods": ["POST"],
        "version": "v1",
        "operation_id": "registerFleetVehicle",
        "summary": "Register fleet vehicle",
        "description": "",
        "audience": "CUSTOMER",
        "visibility": "public_authenticated",
        "authentication_required": True,
        "required_permissions": ["novafleet:vehicle:create"],
        "command_name": "RegisterFleetVehicle",
        "idempotency_required": True,
    }
    response = client.post("/v1/platform/apis/products/novafleet/endpoints", json=payload)
    assert response.status_code == 200
    listed = client.get("/v1/platform/apis/products/novafleet/endpoints")
    assert listed.status_code == 200
    assert listed.json()["endpoints"][0]["endpoint_id"] == "novafleet.register-vehicle.v1"

