"""Contracts for shared API endpoint creation."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


EndpointHandler = Callable[[Mapping[str, Any], "RequestContext"], Awaitable[Any] | Any]


@dataclass(frozen=True, slots=True)
class ApiEndpointDefinition:
    endpoint_id: str
    product_code: str
    path: str
    methods: tuple[str, ...]
    version: str
    operation_id: str
    summary: str
    description: str
    audience: str
    visibility: str
    authentication_required: bool
    required_roles: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ()
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
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WebhookDefinition:
    webhook_id: str
    product_code: str
    path: str
    provider: str
    signature_type: str
    event_types: tuple[str, ...]
    replay_window_seconds: int
    idempotency_required: bool
    handler_name: str


@dataclass(frozen=True, slots=True)
class WebSocketDefinition:
    channel_id: str
    product_code: str
    path: str
    authentication_required: bool
    required_permissions: tuple[str, ...]
    max_connections_per_user: int
    idle_timeout_seconds: int
    heartbeat_seconds: int
    message_schema: str


@runtime_checkable
class NovaTechProductApi(Protocol):
    product_code: str
    version: str
    api_prefix: str

    def endpoint_definitions(self) -> Sequence[ApiEndpointDefinition]: ...
    def command_handlers(self) -> Mapping[str, Any]: ...
    def query_handlers(self) -> Mapping[str, Any]: ...
    def direct_handlers(self) -> Mapping[str, EndpointHandler]: ...
    def webhooks(self) -> Sequence[WebhookDefinition]: ...
    def websockets(self) -> Sequence[WebSocketDefinition]: ...


__all__ = [
    "ApiEndpointDefinition",
    "EndpointHandler",
    "NovaTechProductApi",
    "WebhookDefinition",
    "WebSocketDefinition",
]
