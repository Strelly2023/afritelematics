from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ReplayPlanRecord:
    id: str
    tenant_id: str
    organization_id: str
    workspace_id: str | None
    name: str
    description: str | None
    scenario_type: str
    source_reference: str | None
    target_environment: str
    status: str
    risk_level: str
    actions: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    affected_resources: tuple[str, ...] = field(default_factory=tuple)
    validation_requirements: tuple[str, ...] = field(default_factory=tuple)
    rollback_plan: dict[str, Any] = field(default_factory=dict)
    plan_hash: str = ""
    version: int = 1
    idempotency_key: str = ""
    created_by: str = ""
    created_at: str = ""
    updated_by: str = ""
    updated_at: str = ""
    approved_at: str | None = None
    promoted_at: str | None = None


@dataclass(frozen=True, slots=True)
class ReplayResultRecord:
    id: str
    tenant_id: str
    replay_plan_id: str
    plan_version: int
    execution_status: str
    validation_status: str
    result_payload: dict[str, Any]
    result_hash: str
    executed_by: str
    validated_by: str | None = None
    executed_at: str = ""
    validated_at: str | None = None


@dataclass(frozen=True, slots=True)
class ReplayApprovalRecord:
    id: str
    tenant_id: str
    replay_plan_id: str
    plan_version: int
    plan_hash: str
    required_quorum: int
    status: str
    approver_id: str = ""
    approver_role: str = ""
    decision: str = "APPROVE"
    reason: str | None = None
    expires_at: str | None = None
    consumed_at: str | None = None
    consumed_by_execution_id: str | None = None
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class ReplayTransitionRecord:
    id: str
    tenant_id: str
    replay_plan_id: str
    from_status: str
    to_status: str
    version: int
    actor_id: str
    reason: str | None = None
    occurred_at: str = ""


@dataclass(frozen=True, slots=True)
class RuntimeAuditRecord:
    id: str
    tenant_id: str
    actor_id: str
    action: str
    subject_type: str
    subject_id: str
    result: str
    correlation_id: str
    payload_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: str = ""
