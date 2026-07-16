"""Executable runtime models for NovaTech products."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


CommandHandler = Callable[[Mapping[str, Any], "ExecutionContext"], Awaitable[Any] | Any]
QueryHandler = Callable[[Mapping[str, Any], "ExecutionContext"], Awaitable[Any] | Any]
WorkerHandler = Callable[["WorkerExecutionContext"], Awaitable[None] | None]


class ProductRuntimeState(StrEnum):
    UNLOADED = "UNLOADED"
    LOADING = "LOADING"
    LOADED = "LOADED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class WorkerState(StrEnum):
    REGISTERED = "REGISTERED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    DRAINING = "DRAINING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class DeploymentStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASS = "PASS"
    DEGRADED = "DEGRADED"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class ActivationState(StrEnum):
    DRAFT = "DRAFT"
    REGISTERED = "REGISTERED"
    VALIDATING = "VALIDATING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    PROVISIONING = "PROVISIONING"
    PROVISIONED = "PROVISIONED"
    LOADING = "LOADING"
    LOADED = "LOADED"
    DEPLOYING = "DEPLOYING"
    DEPLOYED = "DEPLOYED"
    VERIFYING = "VERIFYING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    FAILED = "FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    request_id: str
    correlation_id: str
    causation_id: str | None
    product_code: str
    tenant_id: str
    organization_id: str
    actor_id: str
    actor_type: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    environment: str
    region: str
    language: str
    timezone: str
    trace_id: str
    device_id: str | None = None
    session_id: str | None = None
    idempotency_key: str | None = None
    purpose: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "product_code": self.product_code,
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "roles": list(self.roles),
            "permissions": list(self.permissions),
            "environment": self.environment,
            "region": self.region,
            "language": self.language,
            "timezone": self.timezone,
            "trace_id": self.trace_id,
            "device_id": self.device_id,
            "session_id": self.session_id,
            "idempotency_key": self.idempotency_key,
            "purpose": self.purpose,
        }


@dataclass(frozen=True, slots=True)
class WorkerExecutionContext:
    product_code: str
    tenant_id: str
    organization_id: str
    worker_name: str
    region: str
    trace_id: str
    correlation_id: str
    request_id: str
    job_id: str | None = None
    queue: str = ""


@dataclass(frozen=True, slots=True)
class ProductStartupContext:
    product_code: str
    version: str
    environment: str
    region: str
    registry_snapshot: Mapping[str, Any]
    configuration: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ProductHealthCheck:
    check_id: str
    name: str
    required: bool = True
    timeout_seconds: int = 10
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProductMigration:
    migration_id: str
    version: str
    checksum: str
    approved: bool = False
    destructive: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EventConsumerDefinition:
    name: str
    product_code: str
    topic: str
    group: str
    required: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkerDefinition:
    name: str
    product_code: str
    handler: WorkerHandler
    queue: str
    concurrency: int = 1
    timeout_seconds: int = 60
    max_attempts: int = 5
    retry_delays_seconds: tuple[int, ...] = (0, 5, 30, 120, 600)
    dead_letter_queue: str = ""
    required: bool = True
    graceful_shutdown_seconds: int = 30
    heartbeat_seconds: int = 15


@dataclass(frozen=True, slots=True)
class RouteRegistration:
    product_code: str
    path: str
    methods: tuple[str, ...]
    operation_id: str
    authentication_required: bool
    permissions: tuple[str, ...]
    public: bool
    websocket: bool
    timeout_seconds: int


@dataclass(frozen=True, slots=True)
class RoutePlan:
    revision_id: str
    product_code: str
    additions: tuple[RouteRegistration, ...]
    removals: tuple[RouteRegistration, ...]
    conflicts: tuple[str, ...]
    requires_restart: bool


@dataclass(frozen=True, slots=True)
class LoadedProduct:
    product_code: str
    version: str
    registration: Any
    backend: Any
    commands: dict[str, CommandHandler]
    queries: dict[str, QueryHandler]
    routers: tuple[Any, ...]
    workers: tuple[WorkerDefinition, ...]
    consumers: tuple[EventConsumerDefinition, ...]
    health_checks: tuple[ProductHealthCheck, ...]
    loaded_at: str
    module_checksum: str
    state: ProductRuntimeState


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    success: bool
    product_code: str
    operation: str
    result: Any
    events: tuple[str, ...]
    audit_id: str
    evidence_id: str
    request_id: str
    correlation_id: str
    duration_ms: float


@dataclass(frozen=True, slots=True)
class QueryResult:
    success: bool
    product_code: str
    operation: str
    result: Any
    audit_id: str
    evidence_id: str
    request_id: str
    correlation_id: str
    duration_ms: float


@dataclass(frozen=True, slots=True)
class InfrastructureRequirement:
    id: str
    product_code: str
    kind: "InfrastructureKind"
    name: str
    required: bool
    configuration: Mapping[str, Any]
    desired_state: str
    ownership: str
    region: str


class InfrastructureKind(StrEnum):
    POSTGRES_SCHEMA = "postgres_schema"
    REDIS_NAMESPACE = "redis_namespace"
    EVENT_TOPIC = "event_topic"
    EVENT_CONSUMER = "event_consumer"
    OBJECT_STORAGE_PREFIX = "object_storage_prefix"
    SEARCH_INDEX = "search_index"
    SCHEDULE = "schedule"
    WEBSOCKET_CHANNEL = "websocket_channel"
    SECRET_NAMESPACE = "secret_namespace"


@dataclass(frozen=True, slots=True)
class ProvisioningPlan:
    plan_id: str
    product_code: str
    requirements: tuple[InfrastructureRequirement, ...]
    destructive: bool
    checksum: str
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True, slots=True)
class ProvisioningResult:
    plan_id: str
    product_code: str
    success: bool
    checksum: str
    applied_at: str
    result: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class VerificationResult:
    requirement_id: str
    success: bool
    details: Mapping[str, Any]
    verified_at: str


@dataclass(frozen=True, slots=True)
class RollbackResult:
    product_code: str
    success: bool
    reason: str
    restored_state: str
    completed_at: str


@dataclass(frozen=True, slots=True)
class RuntimeApproval:
    approval_id: str
    product_code: str
    product_version: str
    environment: str
    decision: str
    approver_id: str
    approver_roles: tuple[str, ...]
    approved_at: str
    expires_at: str | None
    conditions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    checksum: str


@dataclass(frozen=True, slots=True)
class ActivationAssessment:
    product_code: str
    version: str
    state: ActivationState
    checks: Mapping[str, str]
    evidence_id: str
    approval_required: bool
    details: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ActivationResult:
    product_code: str
    version: str
    previous_state: ActivationState
    current_state: ActivationState
    approval_id: str
    evidence_id: str
    correlation_id: str
    checks: Mapping[str, str]
    details: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class RuntimeEvidenceRecord:
    evidence_id: str
    product_code: str
    version: str
    environment: str
    region: str
    operation: str
    actor_id: str
    approval_id: str
    correlation_id: str
    inputs_hash: str
    result_hash: str
    module_checksum: str
    configuration_checksum: str
    infrastructure_checksum: str
    checks: tuple[dict[str, Any], ...]
    recorded_at: str
    signature: str


@dataclass(frozen=True, slots=True)
class DeploymentVerificationPlan:
    plan_id: str
    product_code: str
    version: str
    environment: str
    region: str
    checks: tuple["VerificationCheck", ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    check_id: str
    product_code: str
    category: str
    required: bool
    timeout_seconds: int
    attempts: int
    configuration: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class VerificationCheckResult:
    check_id: str
    status: str
    started_at: str
    completed_at: str
    duration_ms: float
    evidence: Mapping[str, Any]
    error_code: str | None


@dataclass(frozen=True, slots=True)
class RuntimeVerificationRecord:
    product_code: str
    version: str
    environment: str
    region: str
    status: str
    plan_id: str
    evidence_id: str
    checks: tuple[VerificationCheckResult, ...]
    started_at: str
    completed_at: str


@dataclass(frozen=True, slots=True)
class WorkerHealthRecord:
    product_code: str
    worker_name: str
    state: WorkerState
    replica_id: str
    started_at: str
    last_heartbeat_at: str
    last_success_at: str
    last_failure_at: str
    processed_count: int
    failure_count: int
    retry_count: int
    dead_letter_count: int
    current_job_id: str | None
    consumer_lag: int


@dataclass(frozen=True, slots=True)
class WorkerOperationResult:
    product_code: str
    operation: str
    success: bool
    state: str
    evidence_id: str
    details: Mapping[str, Any]


def clone_worker_definition(definition: WorkerDefinition) -> WorkerDefinition:
    return WorkerDefinition(
        name=definition.name,
        product_code=definition.product_code,
        handler=definition.handler,
        queue=definition.queue,
        concurrency=definition.concurrency,
        timeout_seconds=definition.timeout_seconds,
        max_attempts=definition.max_attempts,
        retry_delays_seconds=definition.retry_delays_seconds,
        dead_letter_queue=definition.dead_letter_queue,
        required=definition.required,
        graceful_shutdown_seconds=definition.graceful_shutdown_seconds,
        heartbeat_seconds=definition.heartbeat_seconds,
    )


__all__ = [
    "ActivationAssessment",
    "ActivationResult",
    "ActivationState",
    "CommandHandler",
    "DeploymentStatus",
    "DeploymentVerificationPlan",
    "EventConsumerDefinition",
    "ExecutionContext",
    "ExecutionResult",
    "InfrastructureKind",
    "InfrastructureRequirement",
    "LoadedProduct",
    "ProductHealthCheck",
    "ProductMigration",
    "ProductStartupContext",
    "ProductRuntimeState",
    "ProvisioningPlan",
    "ProvisioningResult",
    "QueryHandler",
    "QueryResult",
    "RoutePlan",
    "RouteRegistration",
    "RollbackResult",
    "RuntimeApproval",
    "RuntimeEvidenceRecord",
    "VerificationCheck",
    "VerificationCheckResult",
    "WorkerDefinition",
    "WorkerExecutionContext",
    "WorkerHealthRecord",
    "WorkerOperationResult",
    "WorkerState",
    "clone_worker_definition",
]
