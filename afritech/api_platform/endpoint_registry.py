"""Governed API endpoint registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from dataclasses import asdict

from .compatibility import ApiCompatibilityResult, ApiCompatibilityValidator
from .contracts import ApiEndpointDefinition, NovaTechProductApi, WebSocketDefinition, WebhookDefinition
from .errors import ApiRegistrationError, ApiRouteConflict


class EndpointState(StrEnum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    DEPLOYING = "DEPLOYING"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    SUNSETTING = "SUNSETTING"
    RETIRED = "RETIRED"
    SUSPENDED = "SUSPENDED"
    FAILED = "FAILED"


PROTECTED_PREFIXES = (
    "/v1/platform",
    "/v1/identity",
    "/v1/governance",
    "/v1/audit",
    "/v1/evidence",
    "/v1/internal",
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _allowed_prefixes(definition: ApiEndpointDefinition) -> tuple[str, ...]:
    metadata_prefixes = definition.metadata.get("api_prefixes") if isinstance(definition.metadata, dict) else None
    if isinstance(metadata_prefixes, (list, tuple)) and metadata_prefixes:
        return tuple(str(item) for item in metadata_prefixes)
    metadata_prefix = definition.metadata.get("api_prefix") if isinstance(definition.metadata, dict) else None
    if isinstance(metadata_prefix, str) and metadata_prefix:
        return (metadata_prefix,)
    return (f"/v1/{definition.product_code}",)


@dataclass(frozen=True, slots=True)
class RegisteredEndpoint:
    definition: ApiEndpointDefinition
    state: EndpointState = EndpointState.DRAFT
    compatibility: ApiCompatibilityResult | None = None


class EndpointRegistrationError(ApiRegistrationError):
    pass


class EndpointRegistry:
    def __init__(self, compatibility_validator: ApiCompatibilityValidator | None = None) -> None:
        self._compatibility = compatibility_validator or ApiCompatibilityValidator()
        self._endpoints: dict[str, RegisteredEndpoint] = {}
        self._products: dict[str, tuple[ApiEndpointDefinition, ...]] = {}
        self._webhooks: dict[str, WebhookDefinition] = {}
        self._websockets: dict[str, WebSocketDefinition] = {}

    def register_product_api(self, product_api: NovaTechProductApi) -> tuple[RegisteredEndpoint, ...]:
        endpoints = tuple(product_api.endpoint_definitions())
        for endpoint in endpoints:
            self.register(endpoint)
        self._products[product_api.product_code] = endpoints
        for webhook in product_api.webhooks():
            self.register_webhook(webhook)
        for websocket in product_api.websockets():
            self.register_websocket(websocket)
        return tuple(self._endpoints[endpoint.endpoint_id] for endpoint in endpoints)

    def register(self, definition: ApiEndpointDefinition) -> RegisteredEndpoint:
        if not any(definition.path.startswith(prefix) for prefix in _allowed_prefixes(definition)):
            raise ApiRouteConflict("route_prefix_mismatch")
        if any(definition.path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
            raise ApiRouteConflict("protected_route_prefix")
        if definition.endpoint_id in self._endpoints:
            raise ApiRouteConflict("duplicate_endpoint_id")
        for existing in self._endpoints.values():
            if existing.definition.operation_id == definition.operation_id:
                raise ApiRouteConflict("duplicate_operation_id")
            if existing.definition.path == definition.path and set(existing.definition.methods) & set(definition.methods):
                raise ApiRouteConflict("duplicate_route")
        record = RegisteredEndpoint(definition=definition)
        self._endpoints[definition.endpoint_id] = record
        existing = self._products.get(definition.product_code, ())
        self._products[definition.product_code] = tuple((*existing, definition))
        return record

    def register_webhook(self, webhook: WebhookDefinition) -> None:
        if webhook.webhook_id in self._webhooks:
            raise ApiRouteConflict("duplicate_webhook")
        self._webhooks[webhook.webhook_id] = webhook

    def register_websocket(self, websocket: WebSocketDefinition) -> None:
        if websocket.channel_id in self._websockets:
            raise ApiRouteConflict("duplicate_websocket")
        self._websockets[websocket.channel_id] = websocket

    def set_state(self, endpoint_id: str, state: EndpointState) -> None:
        record = self._endpoints.get(endpoint_id)
        if record is None:
            raise EndpointRegistrationError("unknown_endpoint")
        self._endpoints[endpoint_id] = RegisteredEndpoint(definition=record.definition, state=state, compatibility=record.compatibility)

    def set_compatibility(self, endpoint_id: str, compatibility: ApiCompatibilityResult) -> None:
        record = self._endpoints.get(endpoint_id)
        if record is None:
            raise EndpointRegistrationError("unknown_endpoint")
        self._endpoints[endpoint_id] = RegisteredEndpoint(definition=record.definition, state=record.state, compatibility=compatibility)

    def get(self, endpoint_id: str) -> RegisteredEndpoint:
        try:
            return self._endpoints[endpoint_id]
        except KeyError as exc:
            raise EndpointRegistrationError("unknown_endpoint") from exc

    def list_product(self, product_code: str) -> tuple[RegisteredEndpoint, ...]:
        return tuple(record for record in self._endpoints.values() if record.definition.product_code == product_code)

    def list_products(self) -> tuple[str, ...]:
        return tuple(sorted({record.definition.product_code for record in self._endpoints.values()} | set(self._products)))

    def list_all(self) -> tuple[RegisteredEndpoint, ...]:
        return tuple(self._endpoints.values())

    def snapshot(self) -> dict[str, Any]:
        return {
            "products": list(self._products),
            "endpoints": [
                {
                    "endpoint_id": record.definition.endpoint_id,
                    "product_code": record.definition.product_code,
                    "path": record.definition.path,
                    "methods": list(record.definition.methods),
                    "operation_id": record.definition.operation_id,
                    "state": str(record.state),
                    "deprecated": record.definition.deprecated,
                }
                for record in self._endpoints.values()
            ],
            "webhooks": [asdict(webhook) for webhook in self._webhooks.values()],
            "websockets": [asdict(websocket) for websocket in self._websockets.values()],
        }

    def health_snapshot(self) -> dict[str, Any]:
        return {
            "status": "ready" if self._endpoints else "empty",
            "product_count": len(self._products),
            "endpoint_count": len(self._endpoints),
            "webhook_count": len(self._webhooks),
            "websocket_count": len(self._websockets),
        }
