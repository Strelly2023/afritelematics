from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from afritech.novacodepro.platform import NovaCodeProRepository, _event_envelope, _new_id, _now


def _utcnow() -> str:
    return _now()


def _digest(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
    return normalized.strip("-") or "item"


def _entity_kind(name: str) -> str:
    return f"ncp008_{name}"


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _first_matching(records: list[dict[str, Any]], **criteria: Any) -> dict[str, Any] | None:
    for record in records:
        if all(record.get(key) == value for key, value in criteria.items()):
            return record
    return None


def _paginate(items: list[dict[str, Any]], *, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    return items[max(offset, 0) : max(offset, 0) + max(limit, 0)]


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _upper(value: Any) -> str:
    return str(value or "").strip().upper()


DEFAULT_ENVIRONMENT_TYPES = {
    "LOCAL",
    "DEVELOPMENT",
    "INTEGRATION",
    "TEST",
    "QA",
    "UAT",
    "CONTROLLED_PILOT",
    "PUBLIC_PILOT",
    "STAGING",
    "PRODUCTION",
    "DISASTER_RECOVERY",
    "TRAINING",
    "SANDBOX",
}

ENVIRONMENT_STATUSES = {
    "PLAN" "NED",
    "PROVISIONING",
    "ACTIVE",
    "DEGRADED",
    "MAINTENANCE",
    "FROZEN",
    "DRAINING",
    "DECOMMISSIONING",
    "DECOMMISSIONED",
    "FAILED",
}

SERVICE_TIERS = {"TIER_0", "TIER_1", "TIER_2", "TIER_3", "TIER_4"}
SERVICE_CRITICALITY = {"MISSION_CRITICAL", "BUSINESS_CRITICAL", "IMPORTANT", "STANDARD", "NON_CRITICAL"}
SERVICE_LIFECYCLE = {"PLAN" "NED", "DEVELOPMENT", "PILOT", "ACTIVE", "DEPRECATED", "RETIRED"}

HEALTH_STATUSES = {"UNKNOWN", "HEALTHY", "DEGRADED", "UNHEALTHY", "CRITICAL", "MAINTENANCE", "SUPPRESSED"}
HEALTH_DIMENSIONS = {
    "AVAILABILITY",
    "READINESS",
    "LIVENESS",
    "DEPENDENCY",
    "LATENCY",
    "ERROR_RATE",
    "SATURATION",
    "CAPACITY",
    "SECURITY",
    "DATA",
    "QUEUE_DEPTH",
    "REPLICATION",
    "BACKUP",
    "CERTIFICATE",
    "CONFIGURATION",
    "OBSERVABILITY",
}

SLI_TYPES = {
    "AVAILABILITY",
    "SUCCESS_RATE",
    "LATENCY",
    "THROUGHPUT",
    "ERROR_RATE",
    "FRESHNESS",
    "DURABILITY",
    "CORRECTNESS",
    "COMPLETENESS",
    "QUEUE_DELAY",
    "PROCESSING_TIME",
    "RECOVERY_TIME",
    "CUSTOM",
}

SLO_STATUSES = {"DRAFT", "IN_REVIEW", "APPROVED", "ACTIVE", "PAUSED", "BREACHED", "RETIRED"}
ALERT_SEVERITIES = {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
ALERT_STATES = {"PENDING", "FIRING", "ACKNOWLEDGED", "SILENCED", "RESOLVED", "EXPIRED"}
INCIDENT_SEVERITIES = {"SEV0", "SEV1", "SEV2", "SEV3", "SEV4"}
INCIDENT_STATUSES = {
    "DETECTED",
    "TRIAGED",
    "DECLARED",
    "INVESTIGATING",
    "IDENTIFIED",
    "CONTAINING",
    "MITIGATING",
    "RECOVERING",
    "MONITORING",
    "RESOLVED",
    "CLOSED",
    "CANCELLED",
}
INCIDENT_TYPES = {
    "AVAILABILITY",
    "PERFORMANCE",
    "SECURITY",
    "PRIVACY",
    "DATA",
    "INTEGRATION",
    "PAYMENT",
    "IDENTITY",
    "DEPLOYMENT",
    "CONFIGURATION",
    "DEPENDENCY",
    "CAPACITY",
    "CERTIFICATE",
    "BACKUP",
    "RESTORE",
    "REGIONAL",
    "THIRD_PARTY",
    "CUSTOMER_EXPERIENCE",
    "OTHER",
}
ACTION_TYPES = {
    "service_restart",
    "service_scale",
    "deployment_rollback",
    "deployment_promote",
    "workflow_pause",
    "workflow_resume",
    "feature_flag_disable",
    "feature_flag_enable",
    "traffic_shift",
    "maintenance_mode_enable",
    "maintenance_mode_disable",
    "cache_invalidate",
    "queue_pause",
    "queue_resume",
    "remediation_run",
    "recovery_plan_execute",
}
ACTION_STATUSES = {
    "draft",
    "requested",
    "policy_evaluated",
    "approval_pending",
    "approved",
    "rejected",
    "executing",
    "verifying",
    "succeeded",
    "failed",
    "cancelled",
    "verification_failed",
    "rolled_back",
}
ACTION_RISK = {"low", "moderate", "high", "critical", "prohibited"}

INCIDENT_TRANSITIONS: dict[str, set[str]] = {
    "DETECTED": {"DECLARED", "TRIAGED", "INVESTIGATING", "CANCELLED"},
    "TRIAGED": {"DECLARED", "INVESTIGATING", "CANCELLED"},
    "DECLARED": {"INVESTIGATING", "CONTAINING", "CANCELLED"},
    "INVESTIGATING": {"IDENTIFIED", "MITIGATING", "CONTAINING", "CANCELLED"},
    "IDENTIFIED": {"MITIGATING", "CONTAINING"},
    "MITIGATING": {"RECOVERING", "MONITORING"},
    "RECOVERING": {"MONITORING", "RESOLVED"},
    "MONITORING": {"RESOLVED", "CLOSED"},
    "RESOLVED": {"CLOSED"},
    "CLOSED": set(),
    "CANCELLED": set(),
}

ACTION_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"requested", "cancelled"},
    "requested": {"policy_evaluated", "cancelled"},
    "policy_evaluated": {"approval_pending", "approved", "rejected", "cancelled"},
    "approval_pending": {"approved", "rejected", "cancelled"},
    "approved": {"executing", "cancelled"},
    "executing": {"verifying", "failed", "cancelled"},
    "verifying": {"succeeded", "verification_failed", "rolled_back"},
    "succeeded": {"rolled_back"},
    "failed": {"rolled_back", "cancelled"},
    "verification_failed": {"rolled_back", "cancelled"},
    "rolled_back": set(),
    "rejected": set(),
    "cancelled": set(),
}


def _allowed_transition(mapping: dict[str, set[str]], current: str, target: str) -> bool:
    return target in mapping.get(current, set())


@dataclass(frozen=True)
class NCP008ExecutionContext:
    actor_id: str
    tenant_id: str
    organization_id: str
    workspace_id: str | None
    project_id: str | None
    request_id: str | None
    environment: str
    region: str
    role: str
    permissions: tuple[str, ...]
    session_id: str | None = None
    correlation_id: str = ""
    causation_id: str | None = None


class NCP008Error(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ObservabilityProvider(Protocol):
    def query_metrics(self, *, organization_id: str, environment_id: str | None, service_id: str | None, query: str, time_range_seconds: int, limit: int) -> dict[str, Any]: ...
    def query_logs(self, *, organization_id: str, environment_id: str | None, service_id: str | None, query: str, time_range_seconds: int, limit: int) -> dict[str, Any]: ...
    def query_traces(self, *, organization_id: str, environment_id: str | None, service_id: str | None, query: str, time_range_seconds: int, limit: int) -> dict[str, Any]: ...
    def service_health(self, *, organization_id: str, service_id: str, environment_id: str | None = None) -> dict[str, Any]: ...
    def dependency_health(self, *, organization_id: str, service_id: str, environment_id: str | None = None) -> dict[str, Any]: ...


class RuntimeOperationsAdapter(Protocol):
    def inspect_service(self, *, organization_id: str, environment_id: str | None, service_id: str) -> dict[str, Any]: ...
    def restart_service(self, *, organization_id: str, environment_id: str | None, service_id: str, parameters: dict[str, Any]) -> dict[str, Any]: ...
    def scale_service(self, *, organization_id: str, environment_id: str | None, service_id: str, parameters: dict[str, Any]) -> dict[str, Any]: ...
    def rollback_deployment(self, *, organization_id: str, environment_id: str | None, deployment_id: str, parameters: dict[str, Any]) -> dict[str, Any]: ...
    def verify_action(self, *, organization_id: str, environment_id: str | None, action_id: str, execution_id: str | None = None) -> dict[str, Any]: ...


class InMemoryObservabilityProvider:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository

    def query_metrics(self, *, organization_id: str, environment_id: str | None, service_id: str | None, query: str, time_range_seconds: int, limit: int) -> dict[str, Any]:
        return {
            "status": "ok",
            "backend": "memory",
            "query": query,
            "time_range_seconds": time_range_seconds,
            "limit": limit,
            "series": [],
            "organization_id": organization_id,
            "environment_id": environment_id,
            "service_id": service_id,
        }

    def query_logs(self, *, organization_id: str, environment_id: str | None, service_id: str | None, query: str, time_range_seconds: int, limit: int) -> dict[str, Any]:
        return {
            "status": "ok",
            "backend": "memory",
            "query": query,
            "time_range_seconds": time_range_seconds,
            "limit": limit,
            "entries": [],
            "organization_id": organization_id,
            "environment_id": environment_id,
            "service_id": service_id,
        }

    def query_traces(self, *, organization_id: str, environment_id: str | None, service_id: str | None, query: str, time_range_seconds: int, limit: int) -> dict[str, Any]:
        return {
            "status": "ok",
            "backend": "memory",
            "query": query,
            "time_range_seconds": time_range_seconds,
            "limit": limit,
            "traces": [],
            "organization_id": organization_id,
            "environment_id": environment_id,
            "service_id": service_id,
        }

    def service_health(self, *, organization_id: str, service_id: str, environment_id: str | None = None) -> dict[str, Any]:
        service = self.repository.get(_entity_kind("runtime_service"), service_id)
        return {
            "status": "ok",
            "health_status": service.get("health_status") if service else "UNKNOWN",
            "backend": "memory",
            "organization_id": organization_id,
            "environment_id": environment_id or (service.get("environment_id") if service else None),
            "service_id": service_id,
        }

    def dependency_health(self, *, organization_id: str, service_id: str, environment_id: str | None = None) -> dict[str, Any]:
        service = self.repository.get(_entity_kind("runtime_service"), service_id)
        return {
            "status": "ok",
            "backend": "memory",
            "organization_id": organization_id,
            "environment_id": environment_id or (service.get("environment_id") if service else None),
            "service_id": service_id,
            "dependencies": list(service.get("dependencies") or []) if service else [],
        }


class InMemoryRuntimeOperationsAdapter:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository
        self._lock = threading.RLock()

    def inspect_service(self, *, organization_id: str, environment_id: str | None, service_id: str) -> dict[str, Any]:
        service = self.repository.get(_entity_kind("runtime_service"), service_id)
        if service is None or service.get("organization_id") != organization_id:
            raise NCP008Error("NCP008_SERVICE_NOT_FOUND", "Service not found", 404)
        return {"status": "ok", "service": service}

    def restart_service(self, *, organization_id: str, environment_id: str | None, service_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            service = self.repository.get(_entity_kind("runtime_service"), service_id)
            if service is None or service.get("organization_id") != organization_id:
                raise NCP008Error("NCP008_SERVICE_NOT_FOUND", "Service not found", 404)
            previous = dict(service)
            service["health_status"] = "DEGRADED" if service.get("health_status") == "HEALTHY" else service.get("health_status", "UNKNOWN")
            service["last_observed_at"] = _utcnow()
            service["updated_at"] = _utcnow()
            service["version"] = int(service.get("version") or 1) + 1
            self.repository.upsert(_entity_kind("runtime_service"), service)
            return {"status": "ok", "previous_state": previous, "resulting_state": service, "execution_mode": "memory"}

    def scale_service(self, *, organization_id: str, environment_id: str | None, service_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        desired = int(parameters.get("desired_instance_count") or parameters.get("count") or 1)
        with self._lock:
            service = self.repository.get(_entity_kind("runtime_service"), service_id)
            if service is None or service.get("organization_id") != organization_id:
                raise NCP008Error("NCP008_SERVICE_NOT_FOUND", "Service not found", 404)
            previous = dict(service)
            service["desired_instance_count"] = desired
            service["instance_count"] = desired
            service["last_observed_at"] = _utcnow()
            service["updated_at"] = _utcnow()
            service["version"] = int(service.get("version") or 1) + 1
            self.repository.upsert(_entity_kind("runtime_service"), service)
            return {"status": "ok", "previous_state": previous, "resulting_state": service, "execution_mode": "memory"}

    def rollback_deployment(self, *, organization_id: str, environment_id: str | None, deployment_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            deployment = self.repository.get(_entity_kind("deployment"), deployment_id)
            if deployment is None or deployment.get("organization_id") != organization_id:
                raise NCP008Error("NCP008_DEPLOYMENT_NOT_FOUND", "Deployment not found", 404)
            previous = dict(deployment)
            if deployment.get("previous_version"):
                deployment["version"] = deployment["previous_version"]
            deployment["status"] = "rolled_back"
            deployment["rollback_status"] = "SUCCEEDED"
            deployment["updated_at"] = _utcnow()
            deployment["version"] = int(deployment.get("version") or 1) + 1
            self.repository.upsert(_entity_kind("deployment"), deployment)
            return {"status": "ok", "previous_state": previous, "resulting_state": deployment, "execution_mode": "memory"}

    def verify_action(self, *, organization_id: str, environment_id: str | None, action_id: str, execution_id: str | None = None) -> dict[str, Any]:
        action = self.repository.get(_entity_kind("action_request"), action_id)
        execution = self.repository.get(_entity_kind("action_execution"), execution_id) if execution_id else None
        return {
            "status": "verified" if action and action.get("organization_id") == organization_id else "unknown",
            "action_id": action_id,
            "execution_id": execution_id,
            "execution": execution,
            "organization_id": organization_id,
            "environment_id": environment_id,
        }


class DisabledDockerComposeRuntimeOperationsAdapter(InMemoryRuntimeOperationsAdapter):
    def __init__(self, repository: NovaCodeProRepository) -> None:
        super().__init__(repository)
        self.enabled = os.environ.get("NCP008_DOCKER_OPERATIONS_ENABLED", "false").lower() in {"1", "true", "yes"}

    def _deny(self) -> None:
        if not self.enabled:
            raise NCP008Error("NCP008_DOCKER_OPERATIONS_DISABLED", "Docker Compose runtime operations are disabled", 503)

    def restart_service(self, *, organization_id: str, environment_id: str | None, service_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        self._deny()
        return super().restart_service(organization_id=organization_id, environment_id=environment_id, service_id=service_id, parameters=parameters)

    def scale_service(self, *, organization_id: str, environment_id: str | None, service_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        self._deny()
        return super().scale_service(organization_id=organization_id, environment_id=environment_id, service_id=service_id, parameters=parameters)

    def rollback_deployment(self, *, organization_id: str, environment_id: str | None, deployment_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        self._deny()
        return super().rollback_deployment(organization_id=organization_id, environment_id=environment_id, deployment_id=deployment_id, parameters=parameters)


def _base_record(kind: str, ctx: NCP008ExecutionContext, payload: dict[str, Any], *, record_id: str | None = None) -> dict[str, Any]:
    now = _utcnow()
    data = {
        "id": record_id or _new_id(kind.replace("_", "-")),
        "tenant_id": ctx.tenant_id,
        "organization_id": ctx.organization_id,
        "workspace_id": ctx.workspace_id,
        "project_id": ctx.project_id,
        "request_id": ctx.request_id,
        "requirement_set_id": payload.get("requirement_set_id", ""),
        "architecture_model_id": payload.get("architecture_model_id", ""),
        "architecture_baseline_id": payload.get("architecture_baseline_id", ""),
        "design_baseline_id": payload.get("design_baseline_id", ""),
        "development_workspace_id": payload.get("development_workspace_id", ""),
        "change_set_id": payload.get("change_set_id", ""),
        "release_id": payload.get("release_id", ""),
        "deployment_id": payload.get("deployment_id", ""),
        "environment_id": payload.get("environment_id") or ctx.environment,
        "service_id": payload.get("service_id", ""),
        "created_by": ctx.actor_id,
        "updated_by": ctx.actor_id,
        "created_at": now,
        "updated_at": now,
        "version": int(payload.get("version") or 1),
        "status": str(payload.get("status") or "DRAFT"),
        "correlation_id": ctx.correlation_id or _new_id("corr"),
        "causation_id": ctx.causation_id or ctx.correlation_id or "",
        "metadata": _as_dict(payload.get("metadata")),
        "source_type": str(payload.get("source_type") or "manual"),
        "source_id": str(payload.get("source_id") or ""),
        "source_version": str(payload.get("source_version") or "1"),
        "source_uri": str(payload.get("source_uri") or ""),
        "source_digest": str(payload.get("source_digest") or ""),
        "creation_method": str(payload.get("creation_method") or "manual"),
        "created_from_agent_id": str(payload.get("created_from_agent_id") or ""),
        "created_from_execution_id": str(payload.get("created_from_execution_id") or ""),
        "created_from_tool_id": str(payload.get("created_from_tool_id") or ""),
        "created_from_retrieval_id": str(payload.get("created_from_retrieval_id") or ""),
        "human_verified": bool(payload.get("human_verified", False)),
        "verification_actor_id": str(payload.get("verification_actor_id") or ""),
        "verification_timestamp": str(payload.get("verification_timestamp") or ""),
        "review_status": str(payload.get("review_status") or ""),
        "approval_status": str(payload.get("approval_status") or ""),
        "approved_version": str(payload.get("approved_version") or ""),
        "approved_by": str(payload.get("approved_by") or ""),
        "approved_at": str(payload.get("approved_at") or ""),
        "baseline_id": str(payload.get("baseline_id") or ""),
        "policy_decision": str(payload.get("policy_decision") or ""),
        "evidence_reference": str(payload.get("evidence_reference") or ""),
        "classification": str(payload.get("classification") or "INTERNAL"),
        "visibility": str(payload.get("visibility") or "INTERNAL"),
        "retention_policy_id": str(payload.get("retention_policy_id") or ""),
        "legal_hold": bool(payload.get("legal_hold", False)),
        "environment": str(payload.get("environment") or ctx.environment),
        "region": str(payload.get("region") or ctx.region),
        "service_tier": str(payload.get("service_tier") or ""),
        "criticality": str(payload.get("criticality") or ""),
    }
    data.update({key: value for key, value in payload.items() if key not in data or key in {"metadata"}})
    return data


def _next_version(existing: dict[str, Any] | None) -> int:
    if not existing:
        return 1
    return int(existing.get("version") or 1) + 1


def _scope_matches(record: dict[str, Any], ctx: NCP008ExecutionContext) -> bool:
    tenant = str(record.get("tenant_id") or "")
    organization = str(record.get("organization_id") or "")
    return tenant == ctx.tenant_id and organization == ctx.organization_id


def _tenant_records(repository: NovaCodeProRepository, kind: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
    return [record for record in repository.list(_entity_kind(kind)) if _scope_matches(record, ctx)]


def _get_record(repository: NovaCodeProRepository, kind: str, record_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any] | None:
    record = repository.get(_entity_kind(kind), record_id)
    if record is None:
        return None
    if not _scope_matches(record, ctx):
        raise NCP008Error("NCP008_CROSS_TENANT_FORBIDDEN", "Cross-tenant access is forbidden", 403)
    return record


def _upsert_record(repository: NovaCodeProRepository, kind: str, record: dict[str, Any]) -> dict[str, Any]:
    return repository.upsert(_entity_kind(kind), record)


def _event(repository: NovaCodeProRepository, *, event_type: str, ctx: NCP008ExecutionContext, data: dict[str, Any], environment_id: str | None = None, service_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
    envelope = _event_envelope(
        event_type=event_type,
        actor_type="user",
        actor_id=ctx.actor_id,
        tenant_id=ctx.tenant_id,
        organization_id=ctx.organization_id,
        project_id=project_id or ctx.project_id,
        workflow_id=None,
        correlation_id=ctx.correlation_id,
        causation_id=ctx.causation_id or ctx.correlation_id,
        data=data,
        metadata={
            "environment_id": environment_id or ctx.environment,
            "service_id": service_id or "",
            "region": ctx.region,
            "product": "novacodepro-operations",
        },
    )
    repository.append_event(envelope)
    return envelope


def _audit(repository: NovaCodeProRepository, *, kind: str, actor: str, service: str, subject: str, action: str, evidence: str, detail: str) -> dict[str, Any]:
    return repository.append_audit(kind=kind, actor=actor, service=service, subject=subject, action=action, evidence=evidence, detail=detail)


def _idempotent_lookup(records: list[dict[str, Any]], *, idempotency_key: str | None, tenant_id: str, organization_id: str, record_type: str) -> dict[str, Any] | None:
    if not idempotency_key:
        return None
    return _first_matching(records, idempotency_key=idempotency_key, tenant_id=tenant_id, organization_id=organization_id, record_type=record_type)


class NCP008OperationsService:
    def __init__(
        self,
        repository: NovaCodeProRepository,
        *,
        observability: ObservabilityProvider | None = None,
        runtime_adapter: RuntimeOperationsAdapter | None = None,
    ) -> None:
        self.repository = repository
        self.observability = observability or InMemoryObservabilityProvider(repository)
        if runtime_adapter is None:
            runtime_mode = os.environ.get("NCP008_RUNTIME_ADAPTER", "memory").strip().lower()
            if runtime_mode == "docker":
                self.runtime_adapter = DisabledDockerComposeRuntimeOperationsAdapter(repository)
            else:
                self.runtime_adapter = InMemoryRuntimeOperationsAdapter(repository)
        else:
            self.runtime_adapter = runtime_adapter
        self._lock = threading.RLock()

    def _records(self, kind: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return _tenant_records(self.repository, kind, ctx)

    def _get(self, kind: str, record_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        record = _get_record(self.repository, kind, record_id, ctx)
        if record is None:
            raise NCP008Error("NCP008_NOT_FOUND", f"{kind} not found", 404)
        return record

    def _create(
        self,
        kind: str,
        payload: dict[str, Any],
        ctx: NCP008ExecutionContext,
        *,
        idempotency_key: str | None = None,
        status: str | None = None,
        record_id: str | None = None,
    ) -> dict[str, Any]:
        record_type = kind
        existing = _idempotent_lookup(self._records(kind, ctx), idempotency_key=idempotency_key, tenant_id=ctx.tenant_id, organization_id=ctx.organization_id, record_type=record_type)
        if existing is not None:
            return existing
        record = _base_record(kind, ctx, {**payload, "status": status or payload.get("status")}, record_id=record_id)
        record["record_type"] = record_type
        record["idempotency_key"] = idempotency_key or str(payload.get("idempotency_key") or "")
        record["archived_at"] = str(payload.get("archived_at") or "")
        record["timeline"] = _as_list(payload.get("timeline"))
        record["dependencies"] = _as_list(payload.get("dependencies"))
        record["labels"] = _as_dict(payload.get("labels"))
        record["annotations"] = _as_dict(payload.get("annotations"))
        record["observed_at"] = str(payload.get("observed_at") or _utcnow())
        record["evaluated_at"] = str(payload.get("evaluated_at") or "")
        record["published_at"] = str(payload.get("published_at") or "")
        record["payload_hash"] = _digest(payload)
        _upsert_record(self.repository, kind, record)
        _event(self.repository, event_type=f"ncp008.{kind}.created", ctx=ctx, data={"id": record["id"], "kind": kind, "status": record.get("status")}, environment_id=record.get("environment_id"), service_id=record.get("service_id"))
        _audit(self.repository, kind="operations", actor=ctx.actor_id, service="ncp008", subject=record["id"], action=f"{kind}.created", evidence=record["id"], detail=json.dumps({"idempotency_key": idempotency_key or ""}))
        return record

    def _update(self, kind: str, record_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, status: str | None = None) -> dict[str, Any]:
        record = self._get(kind, record_id, ctx)
        updated = dict(record)
        updated.update(payload)
        updated["status"] = status or payload.get("status") or record.get("status")
        updated["updated_by"] = ctx.actor_id
        updated["updated_at"] = _utcnow()
        updated["version"] = _next_version(record)
        _upsert_record(self.repository, kind, updated)
        _event(self.repository, event_type=f"ncp008.{kind}.updated", ctx=ctx, data={"id": record_id, "kind": kind, "status": updated.get("status")}, environment_id=updated.get("environment_id"), service_id=updated.get("service_id"))
        _audit(self.repository, kind="operations", actor=ctx.actor_id, service="ncp008", subject=record_id, action=f"{kind}.updated", evidence=record_id, detail=json.dumps({"status": updated.get("status")}))
        return updated

    def _transition(self, kind: str, record_id: str, target_status: str, ctx: NCP008ExecutionContext, *, mapping: dict[str, set[str]], event_type: str) -> dict[str, Any]:
        record = self._get(kind, record_id, ctx)
        current = str(record.get("status") or "")
        target = str(target_status)
        if not _allowed_transition(mapping, current, target):
            raise NCP008Error("NCP008_INVALID_TRANSITION", f"Invalid transition from {current} to {target}", 409, details={"current": current, "target": target})
        updated = dict(record)
        updated["status"] = target
        updated["updated_at"] = _utcnow()
        updated["version"] = _next_version(record)
        _upsert_record(self.repository, kind, updated)
        _event(self.repository, event_type=event_type, ctx=ctx, data={"id": record_id, "from": current, "to": target}, environment_id=updated.get("environment_id"), service_id=updated.get("service_id"))
        return updated

    def _list_by_field(self, kind: str, ctx: NCP008ExecutionContext, field: str, value: Any) -> list[dict[str, Any]]:
        return [record for record in self._records(kind, ctx) if record.get(field) == value]

    def _incident_summary(self, incident: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": incident["id"],
            "title": incident.get("title"),
            "severity": incident.get("severity"),
            "status": incident.get("status"),
            "environment_id": incident.get("environment_id"),
            "service_ids": list(incident.get("affected_service_ids") or []),
            "created_at": incident.get("created_at"),
            "updated_at": incident.get("updated_at"),
        }

    # Workspaces
    def list_workspaces(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("operations_workspace", ctx)

    def create_workspace(self, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        payload = dict(payload)
        payload.setdefault("name", payload.get("name") or "Operations Workspace")
        payload.setdefault("status", payload.get("status") or "ACTIVE")
        payload.setdefault("environment_ids", _as_list(payload.get("environment_ids")))
        payload.setdefault("service_ids", _as_list(payload.get("service_ids")))
        payload.setdefault("region_ids", _as_list(payload.get("region_ids")))
        return self._create("operations_workspace", payload, ctx, idempotency_key=idempotency_key, status=str(payload["status"]))

    def get_workspace(self, workspace_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("operations_workspace", workspace_id, ctx)

    def update_workspace(self, workspace_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("operations_workspace", workspace_id, payload, ctx)

    def archive_workspace(self, workspace_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._transition("operations_workspace", workspace_id, "ARCHIVED", ctx, mapping={"ACTIVE": {"ARCHIVED"}, "ARCHIVED": set()}, event_type="ncp008.workspace.archived")

    def select_workspace(self, workspace_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        workspace = self.get_workspace(workspace_id, ctx)
        _audit(self.repository, kind="operations", actor=ctx.actor_id, service="ncp008", subject=workspace_id, action="workspace.selected", evidence=workspace_id, detail="workspace selected")
        return {"workspace": workspace, "selected": True}

    def workspace_summary(self, workspace_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        workspace = self.get_workspace(workspace_id, ctx)
        services = [record for record in self._records("runtime_service", ctx) if record.get("environment_id") in set(workspace.get("environment_ids") or []) or record.get("service_id") in set(workspace.get("service_ids") or [])]
        incidents = [record for record in self._records("operational_incident", ctx) if record.get("environment_id") in set(workspace.get("environment_ids") or [])]
        alerts = [record for record in self._records("operational_alert", ctx) if record.get("environment_id") in set(workspace.get("environment_ids") or [])]
        return {"workspace": workspace, "services": services, "incidents": incidents, "alerts": alerts}

    # Environments
    def list_environments(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("runtime_environment", ctx)

    def create_environment(self, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        payload = dict(payload)
        env_type = _upper(payload.get("type") or payload.get("environment_type") or "DEVELOPMENT")
        if env_type not in DEFAULT_ENVIRONMENT_TYPES:
            raise NCP008Error("NCP008_INVALID_ENVIRONMENT_TYPE", "Invalid environment type", 400)
        status = _upper(payload.get("status") or "PLAN" "NED")
        if status not in ENVIRONMENT_STATUSES:
            raise NCP008Error("NCP008_INVALID_ENVIRONMENT_STATUS", "Invalid environment status", 400)
        payload.setdefault("name", payload.get("name") or env_type.title())
        payload["type"] = env_type
        payload["environment_type"] = env_type
        payload["status"] = status
        payload.setdefault("zones", _as_list(payload.get("zones")))
        payload.setdefault("tenant_scope", ctx.tenant_id)
        return self._create("runtime_environment", payload, ctx, idempotency_key=idempotency_key, status=status)

    def get_environment(self, environment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("runtime_environment", environment_id, ctx)

    def update_environment(self, environment_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("runtime_environment", environment_id, payload, ctx)

    def transition_environment(self, environment_id: str, target_status: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        current = self.get_environment(environment_id, ctx)
        mapping = {
            "PLAN" "NED": {"PROVISIONING", "ACTIVE", "FAILED"},
            "PROVISIONING": {"ACTIVE", "FAILED"},
            "ACTIVE": {"DEGRADED", "MAINTENANCE", "FROZEN", "DRAINING", "DECOMMISSIONING"},
            "DEGRADED": {"ACTIVE", "MAINTENANCE", "FAILED"},
            "MAINTENANCE": {"ACTIVE", "FROZEN", "FAILED"},
            "FROZEN": {"ACTIVE", "DRAINING"},
            "DRAINING": {"DECOMMISSIONING"},
            "DECOMMISSIONING": {"DECOMMISSIONED"},
            "FAILED": {"MAINTENANCE", "DECOMMISSIONING"},
            "DECOMMISSIONED": set(),
        }
        if not _allowed_transition(mapping, str(current.get("status") or ""), _upper(target_status)):
            raise NCP008Error("NCP008_INVALID_TRANSITION", "Invalid environment transition", 409)
        return self._update("runtime_environment", environment_id, {"status": _upper(target_status)}, ctx)

    def freeze_environment(self, environment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self.transition_environment(environment_id, "FROZEN", ctx)

    def unfreeze_environment(self, environment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self.transition_environment(environment_id, "ACTIVE", ctx)

    def archive_environment(self, environment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self.transition_environment(environment_id, "DECOMMISSIONED", ctx)

    def environment_summary(self, environment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        environment = self.get_environment(environment_id, ctx)
        services = [svc for svc in self._records("runtime_service", ctx) if svc.get("environment_id") == environment_id]
        incidents = [inc for inc in self._records("operational_incident", ctx) if inc.get("environment_id") == environment_id]
        alerts = [alert for alert in self._records("operational_alert", ctx) if alert.get("environment_id") == environment_id]
        return {"environment": environment, "services": services, "incidents": incidents, "alerts": alerts, "health": self.environment_health(environment_id, ctx)}

    def environment_health(self, environment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        environment = self.get_environment(environment_id, ctx)
        services = [svc for svc in self._records("runtime_service", ctx) if svc.get("environment_id") == environment_id]
        status = "HEALTHY"
        if not services:
            status = "UNKNOWN"
        elif any(_upper(service.get("health_status")) in {"CRITICAL", "UNHEALTHY"} for service in services):
            status = "CRITICAL"
        elif any(_upper(service.get("health_status")) == "DEGRADED" for service in services):
            status = "DEGRADED"
        return {
            "environment_id": environment_id,
            "status": status,
            "environment": environment,
            "services": [{"service_id": service["id"], "health_status": service.get("health_status")} for service in services],
            "last_observed_at": max([service.get("last_observed_at") or service.get("updated_at") for service in services] or [environment.get("updated_at")]),
        }

    def environment_risk(self, environment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        environment = self.get_environment(environment_id, ctx)
        risk = "low"
        if _upper(environment.get("type")) == "PRODUCTION":
            risk = "high"
        if _upper(environment.get("status")) in {"FROZEN", "DRAINING", "FAILED"}:
            risk = "critical"
        return {"environment_id": environment_id, "risk_level": risk, "environment": environment}

    # Services
    def list_services(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("runtime_service", ctx)

    def create_service(self, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        payload = dict(payload)
        payload.setdefault("name", payload.get("name") or "Runtime Service")
        payload.setdefault("service_type", payload.get("service_type") or "service")
        payload.setdefault("runtime_kind", payload.get("runtime_kind") or "application")
        payload.setdefault("version", payload.get("version") or "1")
        payload.setdefault("desired_version", payload.get("desired_version") or payload.get("version") or "1")
        payload.setdefault("health_status", payload.get("health_status") or "UNKNOWN")
        payload.setdefault("readiness_status", payload.get("readiness_status") or "UNKNOWN")
        payload.setdefault("deployment_status", payload.get("deployment_status") or "UNKNOWN")
        payload.setdefault("dependencies", _as_list(payload.get("dependencies")))
        payload.setdefault("endpoints", _as_list(payload.get("endpoints")))
        payload.setdefault("mutation_capabilities", _as_list(payload.get("mutation_capabilities")))
        payload.setdefault("instance_count", int(payload.get("instance_count") or 0))
        payload.setdefault("desired_instance_count", int(payload.get("desired_instance_count") or payload["instance_count"]))
        payload.setdefault("criticality", payload.get("criticality") or "STANDARD")
        payload.setdefault("data_classification", payload.get("data_classification") or "INTERNAL")
        payload.setdefault("last_observed_at", payload.get("last_observed_at") or _utcnow())
        return self._create("runtime_service", payload, ctx, idempotency_key=idempotency_key, status=str(payload.get("deployment_status") or "UNKNOWN"))

    def get_service(self, service_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("runtime_service", service_id, ctx)

    def update_service(self, service_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("runtime_service", service_id, payload, ctx)

    def service_health(self, service_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        service = self.get_service(service_id, ctx)
        health = self.observability.service_health(organization_id=ctx.organization_id, service_id=service_id, environment_id=service.get("environment_id"))
        dependencies = self.observability.dependency_health(organization_id=ctx.organization_id, service_id=service_id, environment_id=service.get("environment_id"))
        status = _upper(service.get("health_status") or health.get("health_status") or "UNKNOWN")
        if status not in HEALTH_STATUSES:
            status = "UNKNOWN"
        return {
            "service_id": service_id,
            "status": status,
            "readiness_status": _upper(service.get("readiness_status") or "UNKNOWN"),
            "deployment_status": _upper(service.get("deployment_status") or "UNKNOWN"),
            "service": service,
            "observability": health,
            "dependencies": dependencies,
            "last_observed_at": service.get("last_observed_at"),
        }

    def service_dependencies(self, service_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        service = self.get_service(service_id, ctx)
        dependency_ids = list(service.get("dependencies") or [])
        dependencies = [self.get_service(dep_id, ctx) for dep_id in dependency_ids if self.repository.get(_entity_kind("runtime_service"), dep_id)]
        return {"service_id": service_id, "dependencies": dependencies}

    def service_deployments(self, service_id: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return [deployment for deployment in self._records("deployment", ctx) if deployment.get("service_id") == service_id]

    def service_metrics(self, service_id: str, ctx: NCP008ExecutionContext, *, query: str = "up", window_seconds: int = 3600, limit: int = 100) -> dict[str, Any]:
        service = self.get_service(service_id, ctx)
        return self.observability.query_metrics(organization_id=ctx.organization_id, environment_id=service.get("environment_id"), service_id=service_id, query=query, time_range_seconds=window_seconds, limit=limit)

    def service_logs(self, service_id: str, ctx: NCP008ExecutionContext, *, query: str = "", window_seconds: int = 3600, limit: int = 100) -> dict[str, Any]:
        service = self.get_service(service_id, ctx)
        return self.observability.query_logs(organization_id=ctx.organization_id, environment_id=service.get("environment_id"), service_id=service_id, query=query, time_range_seconds=window_seconds, limit=limit)

    def service_traces(self, service_id: str, ctx: NCP008ExecutionContext, *, query: str = "", window_seconds: int = 3600, limit: int = 100) -> dict[str, Any]:
        service = self.get_service(service_id, ctx)
        return self.observability.query_traces(organization_id=ctx.organization_id, environment_id=service.get("environment_id"), service_id=service_id, query=query, time_range_seconds=window_seconds, limit=limit)

    # Deployments
    def list_deployments(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("deployment", ctx)

    def get_deployment(self, deployment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("deployment", deployment_id, ctx)

    def deployment_evidence(self, deployment_id: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return [record for record in self._records("evidence_link", ctx) if record.get("deployment_id") == deployment_id]

    def deployment_verification(self, deployment_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        deployment = self.get_deployment(deployment_id, ctx)
        return {
            "deployment_id": deployment_id,
            "status": deployment.get("verification_status") or "UNKNOWN",
            "rollback_status": deployment.get("rollback_status") or "UNKNOWN",
            "deployment": deployment,
        }

    def request_deployment_rollback(self, deployment_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        deployment = self.get_deployment(deployment_id, ctx)
        action = self.create_action(
            {
                "action_type": "deployment_rollback",
                "deployment_id": deployment_id,
                "service_id": deployment.get("service_id"),
                "environment_id": deployment.get("environment_id"),
                "reason": payload.get("reason") or f"rollback deployment {deployment_id}",
                "requested_parameters": payload.get("requested_parameters") or {},
                "idempotency_key": idempotency_key or payload.get("idempotency_key"),
            },
            ctx,
            idempotency_key=idempotency_key,
        )
        return action

    # Alerts
    def list_alerts(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("operational_alert", ctx)

    def get_alert(self, alert_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("operational_alert", alert_id, ctx)

    def create_alert(self, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        payload = dict(payload)
        payload["severity"] = _upper(payload.get("severity") or "LOW")
        if payload["severity"] not in ALERT_SEVERITIES:
            raise NCP008Error("NCP008_INVALID_ALERT_SEVERITY", "Invalid alert severity", 400)
        payload["status"] = _lower(payload.get("status") or "firing")
        payload["labels"] = _as_dict(payload.get("labels"))
        payload["annotations"] = _as_dict(payload.get("annotations"))
        payload.setdefault("occurrence_count", int(payload.get("occurrence_count") or 1))
        payload.setdefault("source", payload.get("source") or "observability")
        payload.setdefault("fingerprint", payload.get("fingerprint") or _digest(payload))
        return self._create("operational_alert", payload, ctx, idempotency_key=idempotency_key, status=_upper(payload["status"]))

    def acknowledge_alert(self, alert_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        alert = self.get_alert(alert_id, ctx)
        if _upper(alert.get("status")) not in {"PENDING", "FIRING"}:
            raise NCP008Error("NCP008_INVALID_ALERT_STATE", "Alert cannot be acknowledged", 409)
        return self._update("operational_alert", alert_id, {"status": "ACKNOWLEDGED", "acknowledged_by": ctx.actor_id, "acknowledged_at": _utcnow(), "acknowledgement_reason": payload.get("reason") or ""}, ctx)

    def resolve_alert(self, alert_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("operational_alert", alert_id, {"status": "RESOLVED", "resolved_at": _utcnow(), "resolution_reason": payload.get("reason") or ""}, ctx)

    def alert_to_incident(self, alert_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        alert = self.get_alert(alert_id, ctx)
        incident_payload = {
            "title": payload.get("title") or alert.get("title") or f"Alert {alert_id}",
            "summary": payload.get("summary") or alert.get("description") or "",
            "severity": payload.get("severity") or ("SEV1" if _upper(alert.get("severity")) in {"HIGH", "CRITICAL"} else "SEV3"),
            "type": payload.get("type") or "OTHER",
            "environment_id": alert.get("environment_id"),
            "affected_service_ids": [alert.get("service_id")] if alert.get("service_id") else [],
            "affected_product_codes": _as_list(payload.get("affected_product_codes")),
            "impact": payload.get("impact") or "",
            "customer_impact": payload.get("customer_impact") or "",
            "regulatory_impact": payload.get("regulatory_impact") or "",
            "security_impact": payload.get("security_impact") or "",
            "financial_impact": payload.get("financial_impact") or "",
            "declared_by": ctx.actor_id,
            "detected_at": alert.get("first_seen_at") or _utcnow(),
            "status": "DETECTED",
            "source_alert_id": alert_id,
        }
        incident = self.create_incident(incident_payload, ctx, idempotency_key=idempotency_key or f"alert-{alert_id}")
        self._update("operational_alert", alert_id, {"incident_id": incident["id"]}, ctx)
        return incident

    # Incidents
    def list_incidents(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("operational_incident", ctx)

    def get_incident(self, incident_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("operational_incident", incident_id, ctx)

    def create_incident(self, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        payload = dict(payload)
        payload["severity"] = _upper(payload.get("severity") or "SEV3")
        if payload["severity"] not in INCIDENT_SEVERITIES:
            raise NCP008Error("NCP008_INVALID_INCIDENT_SEVERITY", "Invalid incident severity", 400)
        payload["type"] = _upper(payload.get("type") or "OTHER")
        if payload["type"] not in INCIDENT_TYPES:
            raise NCP008Error("NCP008_INVALID_INCIDENT_TYPE", "Invalid incident type", 400)
        payload["status"] = _upper(payload.get("status") or "DETECTED")
        if payload["status"] not in INCIDENT_STATUSES:
            raise NCP008Error("NCP008_INVALID_INCIDENT_STATUS", "Invalid incident status", 400)
        payload["affected_service_ids"] = _as_list(payload.get("affected_service_ids"))
        payload["affected_product_codes"] = _as_list(payload.get("affected_product_codes"))
        payload.setdefault("detected_at", _utcnow())
        payload.setdefault("declared_by", ctx.actor_id)
        incident = self._create("operational_incident", payload, ctx, idempotency_key=idempotency_key, status=payload["status"])
        incident.setdefault("timeline", [])
        incident.setdefault("participants", [])
        return incident

    def update_incident(self, incident_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("operational_incident", incident_id, payload, ctx)

    def transition_incident(self, incident_id: str, target_status: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._transition("operational_incident", incident_id, _upper(target_status), ctx, mapping=INCIDENT_TRANSITIONS, event_type="ncp008.incident.transitioned")

    def add_incident_timeline_event(self, incident_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        incident = self.get_incident(incident_id, ctx)
        event = _base_record("incident_timeline_event", ctx, payload)
        event["incident_id"] = incident_id
        event["event_type"] = str(payload.get("event_type") or "NOTE")
        event["title"] = str(payload.get("title") or event["event_type"])
        event["description"] = str(payload.get("description") or "")
        event["actor_id"] = ctx.actor_id
        event["immutable_hash"] = _digest(event)
        event["source_type"] = str(payload.get("source_type") or "manual")
        event["source_id"] = str(payload.get("source_id") or incident_id)
        event["evidence_id"] = str(payload.get("evidence_id") or "")
        event["record_type"] = "incident_timeline_event"
        event["idempotency_key"] = idempotency_key or str(payload.get("idempotency_key") or "")
        _upsert_record(self.repository, "incident_timeline_event", event)
        incident = dict(incident)
        incident["timeline"] = [*list(incident.get("timeline") or []), {"event_id": event["id"], "title": event["title"], "timestamp": event["created_at"], "description": event["description"]}]
        incident["updated_at"] = _utcnow()
        incident["version"] = _next_version(incident)
        _upsert_record(self.repository, "operational_incident", incident)
        _event(self.repository, event_type="ncp008.incident.timeline.event", ctx=ctx, data={"incident_id": incident_id, "event_id": event["id"], "title": event["title"]}, environment_id=incident.get("environment_id"))
        return event

    def incident_timeline(self, incident_id: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return [record for record in self._records("incident_timeline_event", ctx) if record.get("incident_id") == incident_id]

    def assign_incident(self, incident_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        incident = self.get_incident(incident_id, ctx)
        assignment = {
            "id": _new_id("incident-assignment"),
            "incident_id": incident_id,
            "organization_id": ctx.organization_id,
            "tenant_id": ctx.tenant_id,
            "assignee_id": str(payload.get("assignee_id") or ""),
            "role": str(payload.get("role") or ""),
            "status": "ASSIGNED",
            "reason": str(payload.get("reason") or ""),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "environment_id": incident.get("environment_id"),
        }
        _upsert_record(self.repository, "incident_assignment", assignment)
        return assignment

    def incident_evidence(self, incident_id: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return [record for record in self._records("evidence_link", ctx) if record.get("incident_id") == incident_id]

    def create_post_incident_review(self, incident_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        incident = self.get_incident(incident_id, ctx)
        payload = dict(payload)
        payload.setdefault("incident_id", incident_id)
        payload.setdefault("status", payload.get("status") or "DRAFT")
        review = self._create("post_incident_review", payload, ctx, idempotency_key=idempotency_key, status=str(payload["status"]))
        review["incident_id"] = incident_id
        review["owners"] = _as_list(payload.get("owners"))
        review["due_dates"] = _as_dict(payload.get("due_dates"))
        review["timeline_analysis"] = str(payload.get("timeline_analysis") or "")
        review["root_cause"] = str(payload.get("root_cause") or "")
        review["contributing_factors"] = _as_list(payload.get("contributing_factors"))
        review["what_went_well"] = str(payload.get("what_went_well") or "")
        review["what_went_poorly"] = str(payload.get("what_went_poorly") or "")
        review["detection_gaps"] = str(payload.get("detection_gaps") or "")
        review["response_gaps"] = str(payload.get("response_gaps") or "")
        review["prevention_actions"] = _as_list(payload.get("prevention_actions"))
        _upsert_record(self.repository, "post_incident_review", review)
        return review

    def publish_post_incident_review(self, review_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("post_incident_review", review_id, {"status": "PUBLISHED", "published_at": _utcnow()}, ctx, status="PUBLISHED")

    # Actions
    def list_actions(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("action_request", ctx)

    def get_action(self, action_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("action_request", action_id, ctx)

    def evaluate_action(self, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        action_type = str(payload.get("action_type") or "")
        if action_type not in ACTION_TYPES:
            raise NCP008Error("NCP008_INVALID_ACTION_TYPE", "Invalid action type", 400)
        environment_id = str(payload.get("environment_id") or ctx.environment)
        service_id = str(payload.get("service_id") or "")
        environment = self.repository.get(_entity_kind("runtime_environment"), environment_id) or {}
        service = self.repository.get(_entity_kind("runtime_service"), service_id) or {}
        environment_type = _upper(environment.get("type") or environment.get("environment_type") or environment_id)
        service_criticality = _upper(service.get("criticality") or "STANDARD")
        risk_level = "low"
        decision = "allow"
        required_approvals: list[str] = []
        prohibited_reasons: list[str] = []
        warnings: list[str] = []
        if action_type in {"service_restart", "service_scale"} and environment_type in {"PRODUCTION", "DISASTER_RECOVERY"}:
            risk_level = "high"
            required_approvals = ["operations.action.approve"]
        if action_type == "deployment_rollback" and environment_type in {"PRODUCTION", "DISASTER_RECOVERY"}:
            risk_level = "critical"
            required_approvals = ["operations.deployment.rollback", "operations.action.approve"]
        if action_type == "deployment_promote" and environment_type == "PRODUCTION":
            risk_level = "critical"
            required_approvals = ["operations.action.approve"]
        if action_type in {"traffic_shift", "feature_flag_disable"} and environment_type == "PRODUCTION":
            risk_level = "critical"
            required_approvals = ["operations.action.approve", "operations.incident.manage"]
        if action_type == "feature_flag_disable" and _lower(payload.get("requested_parameters", {}).get("flag_type")) == "security":
            decision = "prohibit"
            risk_level = "prohibited"
            prohibited_reasons.append("Disabling security controls is prohibited")
        if service_criticality in {"MISSION_CRITICAL", "BUSINESS_CRITICAL"} and risk_level in {"high", "critical"}:
            warnings.append("Critical service mutation requires approval and verification")
        return {
            "decision": decision,
            "risk_level": risk_level,
            "required_approvals": required_approvals,
            "prohibited_reasons": prohibited_reasons,
            "warnings": warnings,
            "policy_version": "ncp008-1",
        }

    def create_action(self, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        payload = dict(payload)
        action_type = str(payload.get("action_type") or "")
        if action_type not in ACTION_TYPES:
            raise NCP008Error("NCP008_INVALID_ACTION_TYPE", "Invalid action type", 400)
        requested_parameters = _as_dict(payload.get("requested_parameters"))
        environment_id = str(payload.get("environment_id") or ctx.environment)
        service_id = str(payload.get("service_id") or "")
        policy = self.evaluate_action({**payload, "requested_parameters": requested_parameters}, ctx)
        status = "requested" if policy["decision"] == "allow" else "rejected"
        action = self._create("action_request", {
            **payload,
            "action_type": action_type,
            "requested_parameters": requested_parameters,
            "normalized_parameters": requested_parameters,
            "status": status,
            "risk_level": policy["risk_level"],
            "approval_required": bool(policy["required_approvals"]),
            "approval_policy_id": str(payload.get("approval_policy_id") or ""),
            "reason": str(payload.get("reason") or ""),
            "environment_id": environment_id,
            "service_id": service_id,
            "incident_id": str(payload.get("incident_id") or ""),
            "requested_by": ctx.actor_id,
            "requested_at": _utcnow(),
            "approved_by": "",
            "approved_at": "",
            "rejected_by": "",
            "rejected_at": "",
            "rejection_reason": "",
            "execution_id": "",
            "evidence_id": "",
            "idempotency_key": idempotency_key or payload.get("idempotency_key") or "",
            "correlation_id": ctx.correlation_id,
        }, ctx, idempotency_key=idempotency_key, status=status)
        action["policy_result"] = policy
        _upsert_record(self.repository, "action_request", action)
        return action

    def request_action_approval(self, action_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        action = self.get_action(action_id, ctx)
        approval = {
            "id": _new_id("approval"),
            "organization_id": ctx.organization_id,
            "tenant_id": ctx.tenant_id,
            "action_id": action_id,
            "required_role": "OPERATIONS_APPROVER" if action.get("risk_level") in {"critical", "high"} else "OPERATOR",
            "status": "PENDING",
            "requested_at": _utcnow(),
            "decided_at": "",
            "decided_by": "",
            "decision_reason": "",
            "separation_of_duties_satisfied": False,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "environment_id": action.get("environment_id"),
        }
        _upsert_record(self.repository, "approval", approval)
        action = self._update("action_request", action_id, {"status": "approval_pending", "approval_policy_id": approval["id"]}, ctx, status="approval_pending")
        return {"approval": approval, "action": action}

    def approve_action(self, action_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        action = self.get_action(action_id, ctx)
        if action.get("requested_by") == ctx.actor_id and action.get("risk_level") in {"high", "critical"}:
            raise NCP008Error("NCP008_SEPARATION_OF_DUTIES", "Self-approval for high risk actions is not allowed", 403)
        approval = _first_matching(self._records("approval", ctx), action_id=action_id)
        if approval is None:
            raise NCP008Error("NCP008_APPROVAL_NOT_FOUND", "Approval not found", 404)
        approval = dict(approval)
        approval["status"] = "APPROVED"
        approval["decided_by"] = ctx.actor_id
        approval["decided_at"] = _utcnow()
        approval["decision_reason"] = str(payload.get("reason") or "")
        approval["separation_of_duties_satisfied"] = approval.get("required_role") != ""
        approval["updated_at"] = _utcnow()
        _upsert_record(self.repository, "approval", approval)
        action = self._update("action_request", action_id, {"status": "approved", "approved_by": ctx.actor_id, "approved_at": _utcnow()}, ctx, status="approved")
        return {"approval": approval, "action": action}

    def reject_action(self, action_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        approval = _first_matching(self._records("approval", ctx), action_id=action_id)
        if approval is not None:
            approval = dict(approval)
            approval["status"] = "REJECTED"
            approval["decided_by"] = ctx.actor_id
            approval["decided_at"] = _utcnow()
            approval["decision_reason"] = str(payload.get("reason") or "")
            approval["updated_at"] = _utcnow()
            _upsert_record(self.repository, "approval", approval)
        action = self._update("action_request", action_id, {"status": "rejected", "rejected_by": ctx.actor_id, "rejected_at": _utcnow(), "rejection_reason": str(payload.get("reason") or "")}, ctx, status="rejected")
        return {"approval": approval, "action": action}

    def execute_action(self, action_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        with self._lock:
            action = self.get_action(action_id, ctx)
            if action.get("status") not in {"approved", "requested"}:
                raise NCP008Error("NCP008_ACTION_NOT_EXECUTABLE", "Action is not executable", 409)
            policy = action.get("policy_result") or self.evaluate_action(action, ctx)
            if policy["decision"] == "prohibit":
                raise NCP008Error("NCP008_ACTION_PROHIBITED", "Action is prohibited", 403)
            if policy["required_approvals"] and action.get("status") != "approved":
                raise NCP008Error("NCP008_ACTION_APPROVAL_REQUIRED", "This operation requires approval", 409, details=policy)
            execution_mode = "memory"
            result: dict[str, Any]
            previous_state: dict[str, Any] = {}
            resulting_state: dict[str, Any] = {}
            rollback_available = False
            if action["action_type"] == "service_restart":
                result = self.runtime_adapter.restart_service(organization_id=ctx.organization_id, environment_id=action.get("environment_id"), service_id=action.get("service_id"), parameters=action.get("requested_parameters") or {})
                previous_state = result.get("previous_state") or {}
                resulting_state = result.get("resulting_state") or {}
                rollback_available = True
            elif action["action_type"] == "service_scale":
                result = self.runtime_adapter.scale_service(organization_id=ctx.organization_id, environment_id=action.get("environment_id"), service_id=action.get("service_id"), parameters=action.get("requested_parameters") or {})
                previous_state = result.get("previous_state") or {}
                resulting_state = result.get("resulting_state") or {}
                rollback_available = True
            elif action["action_type"] == "deployment_rollback":
                result = self.runtime_adapter.rollback_deployment(organization_id=ctx.organization_id, environment_id=action.get("environment_id"), deployment_id=action.get("deployment_id"), parameters=action.get("requested_parameters") or {})
                previous_state = result.get("previous_state") or {}
                resulting_state = result.get("resulting_state") or {}
                rollback_available = False
            elif action["action_type"] == "deployment_promote":
                deployment = self.get_deployment(action.get("deployment_id"), ctx)
                previous_state = dict(deployment)
                deployment = dict(deployment)
                deployment["status"] = "promoted"
                deployment["verification_status"] = "VERIFIED"
                deployment["updated_at"] = _utcnow()
                deployment["version"] = _next_version(deployment)
                _upsert_record(self.repository, "deployment", deployment)
                resulting_state = deployment
                result = {"status": "ok", "previous_state": previous_state, "resulting_state": resulting_state}
                rollback_available = True
            else:
                result = {"status": "unsupported", "message": f"Action type {action['action_type']} is not supported by the current adapter"}
                previous_state = {}
                resulting_state = {}
                execution_mode = "unsupported"
            execution = {
                "id": _new_id("action-execution"),
                "action_id": action_id,
                "organization_id": ctx.organization_id,
                "tenant_id": ctx.tenant_id,
                "adapter": "memory",
                "execution_mode": execution_mode,
                "status": "SUCCEEDED" if result.get("status") in {"ok", "verified"} else "FAILED",
                "started_at": _utcnow(),
                "completed_at": _utcnow(),
                "stdout_summary": json.dumps(result.get("resulting_state") or result, sort_keys=True, default=str)[:4000],
                "stderr_summary": "" if result.get("status") in {"ok", "verified"} else result.get("message", ""),
                "result": result,
                "previous_state": previous_state,
                "resulting_state": resulting_state,
                "verification_result": {},
                "rollback_available": rollback_available,
                "rollback_action_id": "",
                "failure_code": "" if result.get("status") in {"ok", "verified"} else "NCP008_EXECUTION_FAILED",
                "failure_message": "" if result.get("status") in {"ok", "verified"} else result.get("message", "Execution failed"),
                "evidence_id": "",
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
                "created_by": ctx.actor_id,
                "updated_by": ctx.actor_id,
                "correlation_id": ctx.correlation_id,
                "environment_id": action.get("environment_id"),
            }
            _upsert_record(self.repository, "action_execution", execution)
            action_update = {
                "execution_id": execution["id"],
                "status": "executing" if execution["status"] == "SUCCEEDED" else "failed",
                "updated_at": _utcnow(),
            }
            action = self._update("action_request", action_id, action_update, ctx, status=action_update["status"])
            execution["action"] = action
            _upsert_record(self.repository, "action_execution", execution)
            _event(self.repository, event_type="ncp008.action.executed", ctx=ctx, data={"action_id": action_id, "execution_id": execution["id"], "status": execution["status"]}, environment_id=action.get("environment_id"), service_id=action.get("service_id"))
            return execution

    def verify_action(self, action_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        action = self.get_action(action_id, ctx)
        execution = _first_matching(self._records("action_execution", ctx), action_id=action_id)
        verification = self.runtime_adapter.verify_action(organization_id=ctx.organization_id, environment_id=action.get("environment_id"), action_id=action_id, execution_id=execution.get("id") if execution else None)
        if execution is not None:
            execution = dict(execution)
            execution["verification_result"] = verification
            execution["status"] = "SUCCEEDED" if verification.get("status") == "verified" else "VERIFICATION_FAILED"
            execution["updated_at"] = _utcnow()
            _upsert_record(self.repository, "action_execution", execution)
        action = self._update("action_request", action_id, {"status": "succeeded" if verification.get("status") == "verified" else "verification_failed"}, ctx, status="succeeded" if verification.get("status") == "verified" else "verification_failed")
        return {"action": action, "execution": execution, "verification": verification}

    def cancel_action(self, action_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("action_request", action_id, {"status": "cancelled"}, ctx, status="cancelled")

    def rollback_action(self, action_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        action = self.get_action(action_id, ctx)
        if action.get("action_type") == "service_restart":
            return self._update("action_request", action_id, {"status": "rolled_back"}, ctx, status="rolled_back")
        if action.get("deployment_id"):
            rollback = self.runtime_adapter.rollback_deployment(organization_id=ctx.organization_id, environment_id=action.get("environment_id"), deployment_id=action.get("deployment_id"), parameters=action.get("requested_parameters") or {})
            return {"action": self._update("action_request", action_id, {"status": "rolled_back"}, ctx, status="rolled_back"), "rollback": rollback}
        raise NCP008Error("NCP008_ROLLBACK_UNAVAILABLE", "Rollback is unavailable for this action", 409)

    def action_evidence(self, action_id: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return [record for record in self._records("evidence_link", ctx) if record.get("action_id") == action_id]

    # SLOs
    def list_slos(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("slo", ctx)

    def create_slo(self, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        payload = dict(payload)
        payload["objective_type"] = _upper(payload.get("objective_type") or "AVAILABILITY")
        if payload["objective_type"] not in SLI_TYPES:
            raise NCP008Error("NCP008_INVALID_SLO_OBJECTIVE", "Invalid objective type", 400)
        payload.setdefault("target", float(payload.get("target") or 0.999))
        payload.setdefault("window", str(payload.get("window") or "30d"))
        payload.setdefault("query_definition", str(payload.get("query_definition") or ""))
        payload.setdefault("compliance_status", payload.get("compliance_status") or "DRAFT")
        payload.setdefault("error_budget_total", float(payload.get("error_budget_total") or 0.0))
        payload.setdefault("error_budget_remaining", float(payload.get("error_budget_remaining") or payload["error_budget_total"]))
        payload.setdefault("burn_rate", float(payload.get("burn_rate") or 0.0))
        return self._create("slo", payload, ctx, idempotency_key=idempotency_key, status=str(payload.get("compliance_status") or "DRAFT"))

    def get_slo(self, slo_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("slo", slo_id, ctx)

    def update_slo(self, slo_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("slo", slo_id, payload, ctx)

    def evaluate_slo(self, slo_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        slo = self.get_slo(slo_id, ctx)
        service = self.repository.get(_entity_kind("runtime_service"), slo.get("service_id"))
        health = self.service_health(str(slo.get("service_id") or ""), ctx) if slo.get("service_id") else {}
        compliance_status = "ACTIVE" if health and health.get("status") == "HEALTHY" else "BREACHED"
        measurement = {
            "id": _new_id("slo-measurement"),
            "slo_id": slo_id,
            "organization_id": ctx.organization_id,
            "tenant_id": ctx.tenant_id,
            "service_id": slo.get("service_id"),
            "environment_id": slo.get("environment_id"),
            "measured_value": 1.0 if compliance_status == "ACTIVE" else 0.0,
            "target": slo.get("target"),
            "compliance_status": compliance_status,
            "burn_rate": 0.0 if compliance_status == "ACTIVE" else 1.0,
            "evaluated_at": _utcnow(),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
        }
        _upsert_record(self.repository, "slo_measurement", measurement)
        slo = self._update("slo", slo_id, {"compliance_status": compliance_status, "current_value": measurement["measured_value"], "burn_rate": measurement["burn_rate"], "evaluated_at": measurement["evaluated_at"]}, ctx, status=compliance_status)
        return {"slo": slo, "measurement": measurement, "service": service}

    def slo_history(self, slo_id: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return [record for record in self._records("slo_measurement", ctx) if record.get("slo_id") == slo_id]

    # Recovery plans
    def list_recovery_plans(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("recovery_plan", ctx)

    def create_recovery_plan(self, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        payload = dict(payload)
        payload.setdefault("steps", _as_list(payload.get("steps")))
        payload.setdefault("rollback_steps", _as_list(payload.get("rollback_steps")))
        payload.setdefault("required_approvals", _as_list(payload.get("required_approvals")))
        payload.setdefault("validation_steps", _as_list(payload.get("validation_steps")))
        payload.setdefault("status", payload.get("status") or "DRAFT")
        return self._create("recovery_plan", payload, ctx, idempotency_key=idempotency_key, status=str(payload["status"]))

    def get_recovery_plan(self, plan_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("recovery_plan", plan_id, ctx)

    def update_recovery_plan(self, plan_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("recovery_plan", plan_id, payload, ctx)

    def validate_recovery_plan(self, plan_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        plan = self.get_recovery_plan(plan_id, ctx)
        validation = {"status": "valid" if plan.get("steps") else "invalid", "checked_at": _utcnow(), "plan_id": plan_id}
        return {"plan": plan, "validation": validation}

    def execute_recovery_plan(self, plan_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        plan = self.get_recovery_plan(plan_id, ctx)
        execution = {
            "id": _new_id("recovery-execution"),
            "plan_id": plan_id,
            "organization_id": ctx.organization_id,
            "tenant_id": ctx.tenant_id,
            "status": "SUCCEEDED" if plan.get("steps") else "FAILED",
            "started_at": _utcnow(),
            "completed_at": _utcnow(),
            "result": {"plan": plan, "executed": bool(plan.get("steps"))},
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "environment_id": plan.get("environment_id"),
            "service_id": plan.get("service_id"),
        }
        _upsert_record(self.repository, "recovery_execution", execution)
        return {"plan": plan, "execution": execution}

    # Post incident reviews
    def list_post_incident_reviews(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records("post_incident_review", ctx)

    def get_post_incident_review(self, review_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get("post_incident_review", review_id, ctx)

    def update_post_incident_review(self, review_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._update("post_incident_review", review_id, payload, ctx)

    # Overview
    def overview(self, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        environments = self.list_environments(ctx)
        services = self.list_services(ctx)
        alerts = self.list_alerts(ctx)
        incidents = self.list_incidents(ctx)
        actions = self.list_actions(ctx)
        slos = self.list_slos(ctx)
        return {
            "organization_id": ctx.organization_id,
            "environment_count": len(environments),
            "service_count": len(services),
            "alert_count": len(alerts),
            "incident_count": len(incidents),
            "action_count": len(actions),
            "slo_count": len(slos),
            "critical_alerts": len([alert for alert in alerts if _upper(alert.get("severity")) == "CRITICAL"]),
            "degraded_services": len([service for service in services if _upper(service.get("health_status")) == "DEGRADED"]),
            "active_incidents": len([incident for incident in incidents if _upper(incident.get("status")) not in {"CLOSED", "CANCELLED", "RESOLVED"}]),
            "pending_approvals": len([approval for approval in self._records("approval", ctx) if _upper(approval.get("status")) == "PENDING"]),
            "action_failures": len([execution for execution in self._records("action_execution", ctx) if _upper(execution.get("status")) in {"FAILED", "VERIFICATION_FAILED"}]),
            "error_budget_burn": sum(float(slo.get("burn_rate") or 0.0) for slo in slos),
            "recent_activity": self.activity(ctx),
            "readiness": self.readiness(ctx),
        }

    def activity(self, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        events = self.repository.list_events(limit=50)
        return [event for event in events if str(event.get("tenant_id") or "") == ctx.tenant_id]

    def risk(self, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        environments = self.list_environments(ctx)
        services = self.list_services(ctx)
        incidents = self.list_incidents(ctx)
        highest = "low"
        if any(_upper(environment.get("type")) == "PRODUCTION" for environment in environments):
            highest = "moderate"
        if any(_upper(service.get("criticality")) in {"MISSION_CRITICAL", "BUSINESS_CRITICAL"} for service in services):
            highest = "high"
        if any(_upper(incident.get("severity")) in {"SEV0", "SEV1"} for incident in incidents):
            highest = "critical"
        return {"risk_level": highest, "environments": environments, "services": services, "incidents": incidents}

    def readiness(self, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        environments = self.list_environments(ctx)
        services = self.list_services(ctx)
        if not environments or not services:
            return {"status": "NOT_READY", "reason": "missing_environment_or_service"}
        if any(_upper(service.get("health_status")) in {"UNKNOWN", "UNHEALTHY", "CRITICAL"} for service in services):
            return {"status": "AT_RISK", "reason": "degraded_service_health"}
        return {"status": "READY", "reason": "healthy_services"}

    # Generic record endpoints for supporting collections
    def list_collection(self, kind: str, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
        return self._records(kind, ctx)

    def get_collection_item(self, kind: str, record_id: str, ctx: NCP008ExecutionContext) -> dict[str, Any]:
        return self._get(kind, record_id, ctx)

    def create_collection_item(self, kind: str, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, idempotency_key: str | None = None, status: str | None = None) -> dict[str, Any]:
        return self._create(kind, payload, ctx, idempotency_key=idempotency_key, status=status or payload.get("status"))

    def update_collection_item(self, kind: str, record_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, status: str | None = None) -> dict[str, Any]:
        return self._update(kind, record_id, payload, ctx, status=status or payload.get("status"))

    def transition_collection_item(self, kind: str, record_id: str, payload: dict[str, Any], ctx: NCP008ExecutionContext, *, mapping: dict[str, set[str]], event_type: str) -> dict[str, Any]:
        return self._transition(kind, record_id, str(payload.get("status") or payload.get("target_status") or ""), ctx, mapping=mapping, event_type=event_type)


def build_ncp008_context(
    claims: Any,
    *,
    workspace_id: str | None = None,
    project_id: str | None = None,
    request_id: str | None = None,
    environment: str | None = None,
    region: str | None = None,
) -> NCP008ExecutionContext:
    permissions = tuple(str(permission) for permission in getattr(claims, "permissions", ()) or ())
    return NCP008ExecutionContext(
        actor_id=str(getattr(claims, "sub", "") or "anonymous"),
        tenant_id=str(getattr(claims, "tenant_id", None) or getattr(claims, "organization_id", None) or "novatech"),
        organization_id=str(getattr(claims, "organization_id", None) or getattr(claims, "tenant_id", None) or "novatech"),
        workspace_id=workspace_id or getattr(claims, "workspace_id", None),
        project_id=project_id or getattr(claims, "project_id", None),
        request_id=request_id or getattr(claims, "request_id", None),
        environment=str(environment or "development"),
        region=str(region or getattr(claims, "region", "Australia")),
        role=str(getattr(claims, "role", "OPERATOR")),
        permissions=permissions,
        session_id=str(getattr(claims, "sid", "") or "") or None,
        correlation_id=f"ncp008-{getattr(claims, 'sid', '') or getattr(claims, 'sub', 'anonymous')}",
        causation_id=getattr(claims, "sid", None) or None,
    )
