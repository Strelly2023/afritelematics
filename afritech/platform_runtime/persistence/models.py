"""Persistent runtime control store models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class _BaseRecord:
    id: str
    product_code: str
    product_version: str
    environment: str
    region: str
    tenant_id: str
    status: str
    version: int = 1
    created_at: str = field(default_factory=_now)
    created_by: str = ""
    updated_at: str = field(default_factory=_now)
    updated_by: str = ""
    correlation_id: str = ""
    checksum: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProductVersionRecord(_BaseRecord):
    module_checksum: str = ""
    configuration_checksum: str = ""
    infrastructure_checksum: str = ""


@dataclass(frozen=True, slots=True)
class RuntimeInstanceRecord(_BaseRecord):
    deployment_id: str = ""
    worker_state: str = ""
    health_state: str = ""
    observed_at: str = field(default_factory=_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ActivationRecord(_BaseRecord):
    approval_id: str = ""
    current_state: str = ""
    previous_state: str = ""
    module_checksum: str = ""
    configuration_checksum: str = ""
    infrastructure_checksum: str = ""
    route_plan_checksum: str = ""
    migration_checksum: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ApprovalRecord(_BaseRecord):
    approval_type: str = ""
    approver_id: str = ""
    approver_roles: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    decision: str = ""
    expires_at: str | None = None
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkerInstanceRecord(_BaseRecord):
    worker_name: str = ""
    replica_id: str = ""
    state: str = ""
    queue: str = ""
    image: str = ""
    image_digest: str = ""
    heartbeat_at: str = ""
    started_at: str = ""
    processed_count: int = 0
    failure_count: int = 0
    retry_count: int = 0
    dead_letter_count: int = 0
    current_job_id: str | None = None
    consumer_lag: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InfrastructurePlanRecord(_BaseRecord):
    requirement_id: str = ""
    adapter: str = ""
    actions: tuple[dict[str, Any], ...] = ()
    destructive: bool = False
    state: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InfrastructureResourceRecord(_BaseRecord):
    requirement_id: str = ""
    adapter: str = ""
    resource_name: str = ""
    resource_kind: str = ""
    real_mode: str = "REAL"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeploymentRevisionRecord(_BaseRecord):
    deployment_id: str = ""
    image: str = ""
    image_digest: str = ""
    route_plan_checksum: str = ""
    configuration_checksum: str = ""
    migration_checksum: str = ""
    infrastructure_checksum: str = ""
    approval_id: str = ""
    previous_deployment_id: str = ""
    deployed_at: str = ""
    verified_at: str = ""
    promoted_at: str = ""
    rolled_back_at: str = ""
    current_state: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationRunRecord(_BaseRecord):
    verification_id: str = ""
    deployment_id: str = ""
    status: str = ""
    checks: tuple[dict[str, Any], ...] = ()
    started_at: str = ""
    completed_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationResultRecord(_BaseRecord):
    verification_id: str = ""
    probe_id: str = ""
    category: str = ""
    result_status: str = ""
    evidence: Mapping[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class RollbackRunRecord(_BaseRecord):
    rollback_id: str = ""
    deployment_id: str = ""
    previous_deployment_id: str = ""
    reason: str = ""
    status: str = ""
    started_at: str = ""
    completed_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EvidenceRecord(_BaseRecord):
    evidence_id: str = ""
    operation: str = ""
    object_uri: str = ""
    signature: str = ""
    recorded_at: str = field(default_factory=_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IdempotencyRecord(_BaseRecord):
    idempotency_key: str = ""
    request_hash: str = ""
    response_hash: str = ""
    expires_at: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
