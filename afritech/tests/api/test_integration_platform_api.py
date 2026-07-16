from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.integration_platform_api import build_integration_platform_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_integration_platform_router())
    return TestClient(app)


def _auth_headers(role: str = "ADMIN", user_id: str = "integration-admin", organization_id: str = "org-novatech") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_integration_platform_registers_and_lists_providers() -> None:
    client = _client()
    headers = _auth_headers()

    create = client.post(
        "/v1/platform/integrations/products/novaride/providers",
        headers=headers,
        json={
            "provider_id": "maps-primary",
            "provider_type": "REST",
            "base_url": "https://maps.example.com",
            "environment": "staging",
            "region": "AU",
            "authentication_type": "api_key",
            "timeout_seconds": 10,
            "retry_policy": "provider-read",
            "circuit_breaker_policy": "default",
            "rate_limit_policy": "standard",
            "enabled": True,
            "live_mode": False,
        },
    )

    assert create.status_code == 200
    assert create.json()["provider"]["provider_id"] == "maps-primary"

    listing = client.get("/v1/platform/integrations", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["provider_count"] == 1
    assert listing.json()["providers"][0]["provider_id"] == "maps-primary"

    product = client.get("/v1/platform/integrations/products/novaride", headers=headers)
    assert product.status_code == 200
    assert product.json()["health"]["productCode"] == "novaride"

