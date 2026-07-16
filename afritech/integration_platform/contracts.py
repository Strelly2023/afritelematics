"""Contracts for NovaTech integration and data fetching."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class IntegrationContext:
    request_id: str
    correlation_id: str
    trace_id: str
    product_code: str
    tenant_id: str
    organization_id: str
    actor_id: str
    environment: str
    region: str
    purpose: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderDefinition:
    provider_id: str
    product_code: str
    provider_type: str
    base_url: str
    environment: str
    region: str
    authentication_type: str
    secret_references: tuple[str, ...] = ()
    timeout_seconds: int = 30
    retry_policy: str = "no-retry"
    circuit_breaker_policy: str = "default"
    rate_limit_policy: str = "default"
    health_check_path: str | None = None
    data_classification: str = "INTERNAL"
    enabled: bool = True
    live_mode: bool = False


@dataclass(frozen=True, slots=True)
class ProviderGroupDefinition:
    group_id: str
    product_code: str
    strategy: str
    providers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DataQueryDefinition:
    query_id: str
    product_code: str
    endpoint: str
    method: str = "GET"
    cache_policy: str = "no-cache"
    retry_policy: str = "no-retry"
    required_permissions: tuple[str, ...] = ()
    feature_flag: str | None = None
    freshness: str = "EVENTUAL"
    parse_schema: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DataMutationDefinition:
    mutation_id: str
    product_code: str
    endpoint: str
    method: str = "POST"
    idempotency_required: bool = True
    offline_allowed: bool = False
    invalidate_queries: tuple[str, ...] = ()
    optimistic_update: bool = False
    required_permissions: tuple[str, ...] = ()
    feature_flag: str | None = None
    parse_schema: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SubscriptionDefinition:
    subscription_id: str
    product_code: str
    source_product: str
    event_types: tuple[str, ...]
    consumer_name: str
    handler_name: str
    retry_policy: str
    dead_letter_destination: str
    data_contract_id: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class WebhookIntegrationDefinition:
    webhook_id: str
    product_code: str
    provider_id: str
    event_types: tuple[str, ...]
    signature_type: str
    replay_window_seconds: int = 300
    idempotency_required: bool = True
    handler_name: str = ""


@dataclass(frozen=True, slots=True)
class SynchronizationDefinition:
    sync_id: str
    product_code: str
    source_provider: str
    target_domain: str
    direction: str
    schedule: str | None
    cursor_strategy: str
    conflict_strategy: str
    batch_size: int
    retry_policy: str
    transformation_id: str
    evidence_required: bool = True


@dataclass(frozen=True, slots=True)
class PollingDefinition:
    polling_id: str
    product_code: str
    query_id: str
    interval_seconds: int
    maximum_interval_seconds: int
    active_when_visible: bool = True
    stop_when_offline: bool = True
    backoff_on_error: bool = True
    feature_flag: str | None = None


@dataclass(frozen=True, slots=True)
class CachePolicy:
    policy_id: str
    ttl_seconds: int
    stale_while_revalidate_seconds: int
    cache_location: str
    tenant_scoped: bool = True
    user_scoped: bool = False
    allow_persistent_storage: bool = False
    invalidate_on: tuple[str, ...] = ()
    classification_limit: str = "INTERNAL"


@dataclass(frozen=True, slots=True)
class IntegrationManifest:
    product_code: str
    version: str
    providers: tuple[ProviderDefinition, ...]
    queries: tuple[DataQueryDefinition, ...]
    mutations: tuple[DataMutationDefinition, ...]
    subscriptions: tuple[SubscriptionDefinition, ...]
    webhooks: tuple[WebhookIntegrationDefinition, ...]
    sync_jobs: tuple[SynchronizationDefinition, ...]
    schemas: tuple[Mapping[str, Any], ...]
    cache_policies: tuple[CachePolicy, ...]
    retry_policies: tuple[Mapping[str, Any], ...]
    required_permissions: tuple[str, ...]
    feature_flags: tuple[str, ...]
    telemetry_namespace: str


@dataclass(frozen=True, slots=True)
class IntegrationResponse:
    status_code: int
    body: Any
    headers: Mapping[str, str]
    provider_id: str
    duration_ms: float
    cache_status: str = "MISS"
    retry_count: int = 0

