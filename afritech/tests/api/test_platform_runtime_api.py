from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.platform_runtime_api import build_platform_runtime_router
from afritech.platform_runtime import (
    BackendProductRegistration,
    PlatformRuntimeSettings,
    ProductConfigurationField,
    ProductConfigurationSchema,
    ProductHealthStatus,
    ProductRegistrationStatus,
    ProductRuntimeRegistry,
)
from afritech.platform_runtime.config import ConfigurationFieldType


def _auth_headers(role: str = "ADMIN", user_id: str = "runtime-admin", organization_id: str = "org-novatech") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def _client(registry: ProductRuntimeRegistry) -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_platform_runtime_router(registry))
    return TestClient(app)


def test_platform_runtime_registers_products_and_configuration(tmp_path: Path) -> None:
    registry = ProductRuntimeRegistry(path=tmp_path / "backend-registry.yaml")
    client = _client(registry)
    headers = _auth_headers()

    response = client.post(
        "/v1/platform/products",
        headers=headers,
        json={
            "product_code": "novafleet",
            "module_name": "afritech.products.novafleet",
            "version": "2026.07.0",
            "owner": "Fleet Platform Team",
            "api_prefix": "/v1/novafleet",
            "health_path": "/health/products/novafleet",
            "database_schema": "novafleet",
            "description": "Fleet operations backend",
            "status": "APPROVED",
            "registered_commands": ["RegisterFleetVehicle"],
            "registered_queries": ["ListFleetVehicles"],
            "registered_workers": ["fleet-worker"],
            "configuration_schema": {
                "schema_name": "novafleet-config-v1",
                "schema_version": 1,
                "fields": [
                    {
                        "name": "maintenance_reminder_days",
                        "type": "integer",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 365,
                    },
                    {"name": "assignment_timeout_seconds", "type": "integer", "default": 60, "minimum": 1, "maximum": 600},
                ],
            },
            "configuration": {"maintenance_reminder_days": 30, "assignment_timeout_seconds": 60},
            "health_status": "ready",
        },
    )

    assert response.status_code == 200
    assert response.json()["product"]["product_code"] == "novafleet"

    configuration = client.get("/v1/platform/products/novafleet/configuration", headers=headers)
    assert configuration.status_code == 200
    assert configuration.json()["configuration"]["maintenance_reminder_days"] == 30

    validation = client.post(
        "/v1/platform/products/novafleet/configuration/validate",
        headers=headers,
        json={"values": {"maintenance_reminder_days": 15, "assignment_timeout_seconds": 75}},
    )
    assert validation.status_code == 200
    assert validation.json()["valid"] is True

    update = client.put(
        "/v1/platform/products/novafleet/configuration",
        headers=headers,
        json={
            "values": {"maintenance_reminder_days": 21, "assignment_timeout_seconds": 90},
            "actor_id": "runtime-admin",
            "tenant_id": "tenant-a",
            "region": "AU",
            "reason": "pilot tuning",
            "correlation_id": "corr-1",
        },
    )
    assert update.status_code == 200
    assert update.json()["product"]["configuration"]["maintenance_reminder_days"] == 21

    history = client.get("/v1/platform/products/novafleet/configuration/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()["history"]) == 1

    health = client.get("/v1/platform/health/products/novafleet")
    assert health.status_code == 200
    assert health.json()["health"]["status"] == "ready"

    reloaded = ProductRuntimeRegistry.load(registry.path)
    assert reloaded.get_product("novafleet")["status"] == "APPROVED"
    assert reloaded.list_configuration_history("novafleet")[0]["reason"] == "pilot tuning"


def test_platform_runtime_refuses_invalid_production_settings() -> None:
    settings = PlatformRuntimeSettings(
        environment="production",
        region="AU",
        postgres_dsn="",
        redis_dsn="",
        event_broker_dsn="",
        allow_memory_fallback=True,
    )
    try:
        settings.validate()
    except ValueError as exc:
        assert "production_platform_settings_missing" in str(exc)
    else:
        raise AssertionError("expected validation failure")


def test_platform_runtime_registry_seed_contains_shared_products() -> None:
    registry = ProductRuntimeRegistry()
    products = {item["product_code"] for item in registry.list_products()}
    assert {"novaride", "novapay", "novacodepro"}.issubset(products)
    health = registry.health_snapshot()
    assert health["platform"] == "NovaTech"
    assert health["products"]["novaride"]["status"] == "ready"
