"""Administrative API for the shared NovaTech API platform."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.api_platform import (
    ApiCompatibilityValidator,
    ApiEndpointDefinition,
    EndpointRegistry,
    EndpointState,
    OpenApiRegistry,
)
from afritech.api_platform.deprecation import DeprecationRecord, build_deprecation_headers


class ApiEndpointDefinitionPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    endpoint_id: str = Field(min_length=1)
    product_code: str = Field(min_length=1)
    path: str = Field(min_length=1)
    methods: list[str] = Field(default_factory=list)
    version: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    summary: str = ""
    description: str = ""
    audience: str = "INTERNAL"
    visibility: str = "internal"
    authentication_required: bool = True
    required_roles: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    policy_code: str | None = None
    purpose: str | None = None
    command_name: str | None = None
    query_name: str | None = None
    handler_name: str | None = None
    idempotency_required: bool = False
    rate_limit_policy: str = "standard-product-write"
    timeout_seconds: int = 30
    request_schema: str | None = None
    response_schema: str | None = None
    data_classification: str = "INTERNAL"
    audit_required: bool = True
    evidence_required: bool = True
    deprecated: bool = False
    sunset_at: str | None = None
    tags: list[str] = Field(default_factory=list)


def _definition(payload: ApiEndpointDefinitionPayload) -> ApiEndpointDefinition:
    return ApiEndpointDefinition(
        endpoint_id=payload.endpoint_id,
        product_code=payload.product_code,
        path=payload.path,
        methods=tuple(payload.methods),
        version=payload.version,
        operation_id=payload.operation_id,
        summary=payload.summary,
        description=payload.description,
        audience=payload.audience,
        visibility=payload.visibility,
        authentication_required=payload.authentication_required,
        required_roles=tuple(payload.required_roles),
        required_permissions=tuple(payload.required_permissions),
        policy_code=payload.policy_code,
        purpose=payload.purpose,
        command_name=payload.command_name,
        query_name=payload.query_name,
        handler_name=payload.handler_name,
        idempotency_required=payload.idempotency_required,
        rate_limit_policy=payload.rate_limit_policy,
        timeout_seconds=payload.timeout_seconds,
        request_schema=payload.request_schema,
        response_schema=payload.response_schema,
        data_classification=payload.data_classification,
        audit_required=payload.audit_required,
        evidence_required=payload.evidence_required,
        deprecated=payload.deprecated,
        sunset_at=payload.sunset_at,
        tags=tuple(payload.tags),
    )


def _registry(registry: EndpointRegistry | None = None) -> EndpointRegistry:
    return registry or EndpointRegistry()


def build_api_platform_admin_router(registry: EndpointRegistry | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform/apis", tags=["api-platform"])
    platform_registry = _registry(registry)
    compatibility = ApiCompatibilityValidator()
    openapi_registry = OpenApiRegistry(platform_registry)

    @router.get("")
    def overview(_: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"platform": "NovaTech", "summary": platform_registry.health_snapshot(), "products": platform_registry.list_products()}

    @router.get("/products")
    def list_products(_: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"products": platform_registry.list_products(), "health": platform_registry.health_snapshot()}

    @router.get("/products/{product_code}")
    def get_product(product_code: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        records = platform_registry.list_product(product_code)
        if not records:
            raise HTTPException(status_code=404, detail="unknown_product")
        return {"product_code": product_code, "endpoints": [asdict(record.definition) | {"state": str(record.state)} for record in records]}

    @router.get("/products/{product_code}/endpoints")
    def list_endpoints(product_code: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"product_code": product_code, "endpoints": [asdict(record.definition) | {"state": str(record.state)} for record in platform_registry.list_product(product_code)]}

    @router.post("/products/{product_code}/endpoints")
    def register_endpoint(product_code: str, payload: ApiEndpointDefinitionPayload, _: Any = Depends(require_roles("ADMIN", "DEVELOPER"))) -> dict[str, Any]:
        if product_code != payload.product_code:
            raise HTTPException(status_code=400, detail="product_code_mismatch")
        record = platform_registry.register(_definition(payload))
        platform_registry.set_state(record.definition.endpoint_id, EndpointState.VALIDATING)
        return {"endpoint": asdict(record.definition), "state": str(record.state)}

    @router.post("/products/{product_code}/endpoints/{endpoint_id}/validate")
    def validate_endpoint(product_code: str, endpoint_id: str, _: Any = Depends(require_roles("ADMIN", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        record = platform_registry.get(endpoint_id)
        if record.definition.product_code != product_code:
            raise HTTPException(status_code=404, detail="unknown_endpoint")
        platform_registry.set_state(endpoint_id, EndpointState.REVIEW_REQUIRED)
        return {"endpoint_id": endpoint_id, "classification": "COMPATIBLE", "state": "REVIEW_REQUIRED"}

    @router.post("/products/{product_code}/endpoints/{endpoint_id}/approve")
    def approve_endpoint(product_code: str, endpoint_id: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR"))) -> dict[str, Any]:
        record = platform_registry.get(endpoint_id)
        if record.definition.product_code != product_code:
            raise HTTPException(status_code=404, detail="unknown_endpoint")
        platform_registry.set_state(endpoint_id, EndpointState.APPROVED)
        return {"endpoint_id": endpoint_id, "state": "APPROVED"}

    @router.post("/products/{product_code}/endpoints/{endpoint_id}/deploy")
    def deploy_endpoint(product_code: str, endpoint_id: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        record = platform_registry.get(endpoint_id)
        if record.definition.product_code != product_code:
            raise HTTPException(status_code=404, detail="unknown_endpoint")
        platform_registry.set_state(endpoint_id, EndpointState.DEPLOYING)
        return {"endpoint_id": endpoint_id, "state": "DEPLOYING"}

    @router.post("/products/{product_code}/endpoints/{endpoint_id}/activate")
    def activate_endpoint(product_code: str, endpoint_id: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        record = platform_registry.get(endpoint_id)
        if record.definition.product_code != product_code:
            raise HTTPException(status_code=404, detail="unknown_endpoint")
        platform_registry.set_state(endpoint_id, EndpointState.ACTIVE)
        return {"endpoint_id": endpoint_id, "state": "ACTIVE"}

    @router.post("/products/{product_code}/endpoints/{endpoint_id}/deprecate")
    def deprecate_endpoint(product_code: str, endpoint_id: str, sunset_at: str | None = None, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        record = platform_registry.get(endpoint_id)
        if record.definition.product_code != product_code:
            raise HTTPException(status_code=404, detail="unknown_endpoint")
        platform_registry.set_state(endpoint_id, EndpointState.DEPRECATED)
        response = {"endpoint_id": endpoint_id, "state": "DEPRECATED"}
        if sunset_at or record.definition.sunset_at:
            headers = build_deprecation_headers(
                DeprecationRecord(
                    endpoint_id=endpoint_id,
                    deprecated_at="now",
                    sunset_at=sunset_at or record.definition.sunset_at,
                    replacement=None,
                )
            )
            response["headers"] = headers
        return response

    @router.post("/products/{product_code}/endpoints/{endpoint_id}/retire")
    def retire_endpoint(product_code: str, endpoint_id: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR"))) -> dict[str, Any]:
        record = platform_registry.get(endpoint_id)
        if record.definition.product_code != product_code:
            raise HTTPException(status_code=404, detail="unknown_endpoint")
        platform_registry.set_state(endpoint_id, EndpointState.RETIRED)
        return {"endpoint_id": endpoint_id, "state": "RETIRED"}

    @router.get("/openapi")
    def openapi(_: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return openapi_registry.build_platform_document()

    @router.post("/products/{product_code}/compatibility")
    def compatibility_report(product_code: str, payload: list[ApiEndpointDefinitionPayload], _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        current = tuple(item.definition for item in platform_registry.list_product(product_code))
        proposed = tuple(_definition(item) for item in payload)
        result = compatibility.classify(current, proposed)
        return {"product_code": product_code, "result": asdict(result)}

    return router
