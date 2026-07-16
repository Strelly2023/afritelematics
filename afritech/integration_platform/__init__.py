"""Shared integration and data-fetching foundation for NovaTech."""

from .audit import IntegrationAuditEvent, IntegrationAuditRecorder
from .cache import IntegrationCache, CachePolicy
from .circuit_breaker import CircuitBreaker, CircuitBreakerState
from .contracts import (
    DataMutationDefinition,
    DataQueryDefinition,
    IntegrationContext,
    IntegrationManifest,
    IntegrationResponse,
    PollingDefinition,
    ProviderDefinition,
    ProviderGroupDefinition,
    SubscriptionDefinition,
    WebhookIntegrationDefinition,
    SynchronizationDefinition,
)
from .credentials import SecretReference, SecretResolver, SecretValue
from .evidence import IntegrationEvidence, IntegrationEvidenceStore
from .errors import (
    IntegrationError,
    IntegrationAuthenticationError,
    IntegrationCircuitOpenError,
    IntegrationConfigurationError,
    IntegrationContractError,
    IntegrationPermissionError,
    IntegrationProviderError,
    IntegrationRateLimitError,
    IntegrationSchemaError,
    IntegrationTimeoutError,
)
from .event_client import IntegrationEventClient
from .health import IntegrationHealthService
from .http_client import NovaTechHttpClient
from .idempotency import IdempotencyStore
from .provider_registry import ProviderRegistry
from .retry import RetryPolicy, retry_transient
from .telemetry import IntegrationTelemetryRecorder
from .transform import DataTransformer, TransformResult, transform_payload
from .webhook_client import WebhookDeliveryRecord, WebhookDeliveryRuntime
from .websocket_client import WebSocketSubscription, WebSocketSubscriptionRuntime
from .polling import PollingJob, PollingRuntime
from .synchronization import SynchronizationCoordinator, SynchronizationState

__all__ = [
    "CachePolicy",
    "CircuitBreaker",
    "CircuitBreakerState",
    "DataMutationDefinition",
    "DataQueryDefinition",
    "DataTransformer",
    "IdempotencyStore",
    "IntegrationAuditEvent",
    "IntegrationAuditRecorder",
    "IntegrationCache",
    "IntegrationContext",
    "IntegrationContractError",
    "IntegrationConfigurationError",
    "IntegrationEvidence",
    "IntegrationEvidenceStore",
    "IntegrationError",
    "IntegrationEventClient",
    "IntegrationHealthService",
    "IntegrationManifest",
    "IntegrationPermissionError",
    "IntegrationProviderError",
    "IntegrationRateLimitError",
    "IntegrationSchemaError",
    "IntegrationTimeoutError",
    "IntegrationTelemetryRecorder",
    "IntegrationResponse",
    "NovaTechHttpClient",
    "PollingDefinition",
    "PollingJob",
    "PollingRuntime",
    "ProviderDefinition",
    "ProviderGroupDefinition",
    "ProviderRegistry",
    "RetryPolicy",
    "SecretReference",
    "SecretResolver",
    "SecretValue",
    "SubscriptionDefinition",
    "SynchronizationCoordinator",
    "SynchronizationDefinition",
    "SynchronizationState",
    "TransformResult",
    "WebhookDeliveryRecord",
    "WebhookDeliveryRuntime",
    "WebhookIntegrationDefinition",
    "WebSocketSubscription",
    "WebSocketSubscriptionRuntime",
    "retry_transient",
    "transform_payload",
]
