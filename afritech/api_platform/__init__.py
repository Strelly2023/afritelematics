"""Shared API platform foundation for NovaTech."""

from .audit import AuditEvent, AuditRecorder
from .authentication import ApiPrincipal, authenticate_headers
from .authorization import AuthorizationDecision, AuthorizationPolicy
from .compatibility import ApiCompatibilityResult, ApiCompatibilityValidator
from .contracts import ApiEndpointDefinition, NovaTechProductApi, WebSocketDefinition, WebhookDefinition
from .deprecation import DeprecationRecord, build_deprecation_headers
from .endpoint_registry import EndpointRegistrationError, EndpointRegistry, EndpointState
from .errors import ApiAuthorizationError, ApiCompatibilityError, ApiIdempotencyError, ApiPlatformError, ApiRegistrationError, ApiRouteConflict, ApiTenancyError, ApiValidationError
from .evidence import EvidenceRecord, EvidenceStore
from .execution_pipeline import ApiExecutionPipeline, ApiExecutionResult
from .health import ApiHealthService
from .idempotency import IdempotencyRecord, IdempotencyStore
from .openapi_registry import OpenApiRegistry
from .policy import PolicyDecision, PolicyEvaluator
from .rate_limiting import RateLimiter
from .request_context import RequestContext
from .router_factory import ProductRouterFactory
from .tenancy import require_tenant
from .telemetry import TelemetryRecorder
from .validation import SchemaRegistry
from .versioning import ApiVersionRecord
from .webhook_runtime import WebhookRuntimeResult, verify_signature
from .websocket_runtime import WebSocketSession

__all__ = [
    "ApiAuthorizationError",
    "ApiCompatibilityError",
    "ApiCompatibilityResult",
    "ApiCompatibilityValidator",
    "ApiEndpointDefinition",
    "ApiExecutionPipeline",
    "ApiExecutionResult",
    "ApiHealthService",
    "ApiIdempotencyError",
    "ApiPlatformError",
    "ApiPrincipal",
    "ApiRegistrationError",
    "ApiRouteConflict",
    "ApiTenancyError",
    "ApiValidationError",
    "AuditEvent",
    "AuditRecorder",
    "AuthorizationDecision",
    "AuthorizationPolicy",
    "DeprecationRecord",
    "EndpointRegistrationError",
    "EndpointRegistry",
    "EndpointState",
    "EvidenceRecord",
    "EvidenceStore",
    "IdempotencyRecord",
    "IdempotencyStore",
    "NovaTechProductApi",
    "OpenApiRegistry",
    "PolicyDecision",
    "PolicyEvaluator",
    "ProductRouterFactory",
    "RateLimiter",
    "RequestContext",
    "SchemaRegistry",
    "TelemetryRecorder",
    "WebSocketDefinition",
    "WebSocketSession",
    "WebhookDefinition",
    "WebhookRuntimeResult",
    "ApiVersionRecord",
    "build_deprecation_headers",
    "authenticate_headers",
    "require_tenant",
    "verify_signature",
]
