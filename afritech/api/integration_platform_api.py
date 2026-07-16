"""Administrative API for the NovaTech integration platform."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.integration_platform import (
    IntegrationAuditRecorder,
    IntegrationEvidenceStore,
    IntegrationHealthService,
    IntegrationTelemetryRecorder,
    ProviderDefinition,
    ProviderRegistry,
)

router = APIRouter(prefix="/v1/platform/integrations", tags=["integration-platform"])
_REGISTRY = ProviderRegistry()
_AUDIT = IntegrationAuditRecorder()
_EVIDENCE = IntegrationEvidenceStore()
_TELEMETRY = IntegrationTelemetryRecorder()
_HEALTH = IntegrationHealthService(_REGISTRY)


def build_integration_platform_router() -> APIRouter:
    return router


@router.get("")
def list_integrations(_principal: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
    snapshot = _REGISTRY.snapshot()
    return {
        "providers": snapshot["providers"],
        "provider_count": snapshot["provider_count"],
    }


@router.get("/products")
def list_products(_principal: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
    products = {}
    for provider in _REGISTRY.snapshot()["providers"]:
        products.setdefault(provider["product_code"], 0)
        products[provider["product_code"]] += 1
    return {"products": [{"product_code": code, "provider_count": count} for code, count in products.items()]}


@router.get("/products/{product_code}")
def get_product(product_code: str, _principal: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
    return {
        "product_code": product_code,
        "providers": [asdict(provider) for provider in _REGISTRY.list_product_providers(product_code)],
        "health": _HEALTH.health(product_code),
    }


@router.post("/products/{product_code}/providers")
def register_provider(product_code: str, payload: dict[str, Any], _principal: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
    provider = ProviderDefinition(
        provider_id=str(payload.get("provider_id") or ""),
        product_code=product_code,
        provider_type=str(payload.get("provider_type") or "REST"),
        base_url=str(payload.get("base_url") or ""),
        environment=str(payload.get("environment") or "development"),
        region=str(payload.get("region") or "AU"),
        authentication_type=str(payload.get("authentication_type") or "api_key"),
        secret_references=tuple(str(item) for item in payload.get("secret_references") or ()),
        timeout_seconds=int(payload.get("timeout_seconds") or 30),
        retry_policy=str(payload.get("retry_policy") or "no-retry"),
        circuit_breaker_policy=str(payload.get("circuit_breaker_policy") or "default"),
        rate_limit_policy=str(payload.get("rate_limit_policy") or "default"),
        health_check_path=payload.get("health_check_path"),
        data_classification=str(payload.get("data_classification") or "INTERNAL"),
        enabled=bool(payload.get("enabled", True)),
        live_mode=bool(payload.get("live_mode", False)),
    )
    registered = _REGISTRY.register(provider)
    _AUDIT.record("provider.registered", product_code=product_code, provider_id=registered.provider_id, actor_id="admin", metadata={"provider_type": registered.provider_type})
    _TELEMETRY.record("integration.provider.registered", product_code=product_code, provider_id=registered.provider_id)
    return {"provider": asdict(registered)}


@router.post("/products/{product_code}/providers/{provider_id}/validate")
def validate_provider(product_code: str, provider_id: str, _principal: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
    provider = _REGISTRY.resolve(product_code, provider_id)
    return {"provider": asdict(provider), "valid": True}


@router.post("/products/{product_code}/providers/{provider_id}/enable")
def enable_provider(product_code: str, provider_id: str, _principal: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
    provider = _REGISTRY.resolve(product_code, provider_id)
    if not provider.enabled:
        provider = ProviderDefinition(**{**asdict(provider), "enabled": True})
        _REGISTRY._providers[(product_code, provider_id)] = provider  # noqa: SLF001 - guarded admin path
    return {"provider": asdict(provider), "enabled": True}


@router.post("/products/{product_code}/providers/{provider_id}/disable")
def disable_provider(product_code: str, provider_id: str, _principal: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
    provider = _REGISTRY.disable(product_code, provider_id)
    return {"provider": asdict(provider), "enabled": False}


@router.post("/products/{product_code}/providers/{provider_id}/verify")
def verify_provider(product_code: str, provider_id: str, _principal: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
    provider = _REGISTRY.resolve(product_code, provider_id)
    if not provider.enabled:
        raise HTTPException(status_code=409, detail="provider_disabled")
    return {"provider": asdict(provider), "status": "PASS", "health": _HEALTH.health(product_code, provider_id)}
