"""Shared backend runtime API for NovaTech product registration and configuration."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.platform_runtime import (
    BackendProductRegistration,
    PlatformRuntimeSettings,
    ProductConfigurationField,
    ProductConfigurationRevision,
    ProductConfigurationSchema,
    ProductHealthStatus,
    ProductRegistrationStatus,
    ProductRuntimeRegistry,
    RuntimeLayer,
    build_default_product_runtime_registry,
)
from afritech.platform_runtime.config import ConfigurationFieldType


class ConfigurationFieldPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    default: Any = None
    required: bool = False
    description: str = ""
    minimum: int | float | None = None
    maximum: int | float | None = None
    enum: list[Any] = Field(default_factory=list)
    secret: bool = False


class ProductConfigurationSchemaPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_name: str = Field(min_length=1)
    schema_version: int = Field(ge=1)
    description: str = ""
    fields: list[ConfigurationFieldPayload] = Field(default_factory=list)


class BackendProductRegistrationPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    product_code: str = Field(min_length=1)
    module_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    api_prefix: str = Field(min_length=1)
    health_path: str = Field(min_length=1)
    database_schema: str = Field(min_length=1)
    description: str = ""
    status: str = ProductRegistrationStatus.DRAFT
    required_services: list[str] = Field(default_factory=list)
    registered_commands: list[str] = Field(default_factory=list)
    registered_queries: list[str] = Field(default_factory=list)
    registered_events: list[str] = Field(default_factory=list)
    registered_consumers: list[str] = Field(default_factory=list)
    registered_workers: list[str] = Field(default_factory=list)
    infrastructure: dict[str, Any] = Field(default_factory=dict)
    configuration: dict[str, Any] = Field(default_factory=dict)
    health_status: str = ProductHealthStatus.UNKNOWN
    configuration_schema: ProductConfigurationSchemaPayload | None = None
    product_group: str = ""
    module_version: str = ""
    tags: list[str] = Field(default_factory=list)
    approval_reference: str = ""


class ProductConfigurationUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    values: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = ""
    region: str = ""
    actor_id: str = ""
    correlation_id: str = ""
    reason: str = ""
    layer: str = RuntimeLayer.PRODUCT


def _registry(registry: ProductRuntimeRegistry | None = None) -> ProductRuntimeRegistry:
    return registry or build_default_product_runtime_registry()


def _schema_from_payload(product_code: str, payload: ProductConfigurationSchemaPayload | None) -> ProductConfigurationSchema | None:
    if payload is None:
        return None
    return ProductConfigurationSchema(
        product_code=product_code,
        schema_name=payload.schema_name,
        schema_version=payload.schema_version,
        fields=tuple(
            ProductConfigurationField(
                name=field.name,
                type=ConfigurationFieldType(field.type),
                default=field.default,
                required=field.required,
                description=field.description,
                minimum=field.minimum,
                maximum=field.maximum,
                enum=tuple(field.enum),
                secret=field.secret,
            )
            for field in payload.fields
        ),
        description=payload.description,
    )


def _product_from_payload(payload: BackendProductRegistrationPayload) -> BackendProductRegistration:
    return BackendProductRegistration(
        product_code=payload.product_code,
        module_name=payload.module_name,
        version=payload.version,
        owner=payload.owner,
        api_prefix=payload.api_prefix,
        health_path=payload.health_path,
        database_schema=payload.database_schema,
        status=ProductRegistrationStatus(payload.status),
        configuration_schema=_schema_from_payload(payload.product_code, payload.configuration_schema),
        required_services=tuple(payload.required_services),
        registered_commands=tuple(payload.registered_commands),
        registered_queries=tuple(payload.registered_queries),
        registered_events=tuple(payload.registered_events),
        registered_consumers=tuple(payload.registered_consumers),
        registered_workers=tuple(payload.registered_workers),
        infrastructure=dict(payload.infrastructure),
        configuration=dict(payload.configuration),
        health_status=ProductHealthStatus(payload.health_status),
        description=payload.description,
        product_group=payload.product_group,
        module_version=payload.module_version,
        tags=tuple(payload.tags),
        approval_reference=payload.approval_reference,
    )


def build_platform_runtime_router(registry: ProductRuntimeRegistry | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform", tags=["platform-runtime"])
    runtime = _registry(registry)

    @router.get("")
    @router.get("/")
    def runtime_overview(
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "summary": runtime.summary(),
            "manifest": runtime.manifest(),
            "products": runtime.list_products(),
            "commands": runtime.list_commands(),
            "queries": runtime.list_queries(),
            "health": runtime.health_snapshot(),
        }

    @router.get("/products")
    def list_products(
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "summary": runtime.summary(),
            "products": runtime.list_products(),
        }

    @router.post("/products")
    def register_product(
        payload: BackendProductRegistrationPayload,
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        result = runtime.register_product(_product_from_payload(payload))
        result["platform"] = "NovaTech"
        return result

    @router.get("/products/{product_code}")
    def get_product(
        product_code: str,
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "product": runtime.get_product(product_code),
            }
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown_product") from exc

    @router.get("/products/{product_code}/configuration")
    def get_configuration(
        product_code: str,
        tenant_id: str = "",
        region: str = "",
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            product = runtime.get_product(product_code)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown_product") from exc
        return {
            "platform": "NovaTech",
            "product_code": product_code,
            "configuration": runtime.resolve_configuration(product_code, tenant_id=tenant_id, region=region),
            "configuration_schema": product.get("configuration_schema"),
        }

    @router.get("/products/{product_code}/configuration/schema")
    def get_configuration_schema(
        product_code: str,
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            product = runtime.get_product(product_code)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown_product") from exc
        return {
            "platform": "NovaTech",
            "product_code": product_code,
            "configuration_schema": product.get("configuration_schema"),
        }

    @router.get("/products/{product_code}/configuration/history")
    def get_configuration_history(
        product_code: str,
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            runtime.get_product(product_code)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown_product") from exc
        return {
            "platform": "NovaTech",
            "product_code": product_code,
            "history": runtime.list_configuration_history(product_code),
        }

    @router.post("/products/{product_code}/configuration/validate")
    def validate_configuration(
        product_code: str,
        payload: ProductConfigurationUpdatePayload,
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            runtime.get_product(product_code)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown_product") from exc
        result = runtime.validate_configuration(product_code, payload.values)
        result["tenant_id"] = payload.tenant_id
        result["region"] = payload.region
        return result

    @router.put("/products/{product_code}/configuration")
    def update_configuration(
        product_code: str,
        payload: ProductConfigurationUpdatePayload,
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        try:
            runtime.get_product(product_code)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown_product") from exc
        result = runtime.update_configuration(
            product_code,
            payload.values,
            tenant_id=payload.tenant_id,
            region=payload.region,
            actor_id=payload.actor_id,
            correlation_id=payload.correlation_id,
            reason=payload.reason,
            layer=RuntimeLayer(payload.layer),
        )
        if not result.get("valid", False):
            raise HTTPException(status_code=422, detail=result)
        result["platform"] = "NovaTech"
        return result

    @router.get("/commands")
    def list_commands(
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {"platform": "NovaTech", "commands": runtime.list_commands()}

    @router.get("/queries")
    def list_queries(
        _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {"platform": "NovaTech", "queries": runtime.list_queries()}

    @router.get("/health/products")
    def product_health() -> dict[str, Any]:
        return runtime.health_snapshot()

    @router.get("/health/products/{product_code}")
    def product_health_detail(product_code: str) -> dict[str, Any]:
        try:
            product = runtime.get_product(product_code)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown_product") from exc
        health = runtime.health_snapshot()["products"].get(product_code.lower())
        if health is None:
            health = {
                "status": "unknown",
                "database": "unknown",
                "cache": "unknown",
                "event_consumers": "unknown",
                "workers": "unknown",
                "websocket": "unknown",
            }
        return {
            "platform": "NovaTech",
            "product": product,
            "health": health,
        }

    return router


__all__ = ["build_platform_runtime_router"]
