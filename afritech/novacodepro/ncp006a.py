from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from afritech.novacodepro.platform import NovaCodeProRepository


ARCHITECTURE_DOMAINS = (
    "ENTERPRISE",
    "BUSINESS",
    "CAPABILITY",
    "DOMAIN",
    "SOLUTION",
    "APPLICATION",
    "SERVICE",
    "MICROSERVICE",
    "API",
    "INTEGRATION",
    "EVENT",
    "DATA",
    "SECURITY",
    "IDENTITY",
    "PRIVACY",
    "CLOUD",
    "INFRASTRUCTURE",
    "DEPLOYMENT",
    "NETWORK",
    "OBSERVABILITY",
    "RELIABILITY",
    "DISASTER_RECOVERY",
    "AI",
)

COMPONENT_TYPES = (
    "ENTERPRISE",
    "BUSINESS CAPABILITY",
    "DOMAIN",
    "APPLICATION",
    "SERVICE",
    "MICROSERVICE",
    "MODULE",
    "LIBRARY",
    "API",
    "GATEWAY",
    "WORKFLOW",
    "AGENT",
    "AI MODEL",
    "DATABASE",
    "CACHE",
    "QUEUE",
    "TOPIC",
    "STORAGE",
    "IDENTITY PROVIDER",
    "POLICY ENGINE",
    "OBSERVABILITY COMPONENT",
    "SECURITY COMPONENT",
    "INFRASTRUCTURE COMPONENT",
    "EXTERNAL SYSTEM",
    "CLIENT",
    "MOBILE APP",
    "WEB APP",
)

INTERFACE_TYPES = (
    "REST",
    "GRAPHQL",
    "GRPC",
    "WEBSOCKET",
    "WEBHOOK",
    "EVENT",
    "MESSAGE",
    "BATCH",
    "FILE",
    "DATABASE",
    "SDK",
    "CLI",
    "STREAMING",
)

RELATIONSHIP_TYPES = (
    "CONTAINS",
    "DEPENDS_ON",
    "USES",
    "CALLS",
    "PUBLISHES",
    "CONSUMES",
    "READS",
    "WRITES",
    "AUTHENTICATES",
    "AUTHORIZES",
    "ROUTES_TO",
    "DEPLOYS_TO",
    "RUNS_ON",
    "MONITORS",
    "PROTECTS",
    "IMPLEMENTS",
    "SATISFIES",
    "VERIFIES",
    "MITIGATES",
    "SUPERSEDES",
)

REVIEW_TYPES = ("ARCHITECTURE", "SECURITY", "PRIVACY", "OPERATIONS", "RELIABILITY", "COMPLIANCE")
APPROVAL_DECISIONS = ("APPROVED", "REJECTED", "CHANGES_REQUESTED")
BASELINE_STATUSES = ("DRAFT", "APPROVAL_REQUIRED", "APPROVED", "ACTIVE", "SUPERSEDED", "REVOKED", "ARCHIVED")
VALIDATION_TYPES = ("DEPENDENCY", "SECURITY", "DATA", "DEPLOYMENT", "POLICY", "STANDARDS")
DEPLOYMENT_ENVIRONMENTS = ("DEVELOPMENT", "QA", "INTEGRATION", "UAT", "CONTROLLED_PILOT", "PUBLIC_PILOT", "PRODUCTION", "DISASTER_RECOVERY", "MULTI_REGION")
THREAT_TYPES = ("SPOOFING", "TAMPERING", "REPUDIATION", "INFORMATION_DISCLOSURE", "DENIAL_OF_SERVICE", "ELEVATION_OF_PRIVILEGE", "SUPPLY_CHAIN", "INSIDER_THREAT", "PRIVACY", "AI_PROMPT_INJECTION", "TOOL_ABUSE")

TRACEABILITY_TYPES = {
    "REQUEST",
    "REQUIREMENT",
    "ACCEPTANCE_CRITERION",
    "ARCHITECTURE_DECISION",
    "ARCHITECTURE_COMPONENT",
    "ARCHITECTURE_MODEL",
    "ARCHITECTURE_WORKSPACE",
    "DESIGN_ARTIFACT",
    "PROJECT",
    "WORK_ITEM",
    "CODE_COMMIT",
    "CODE_FILE",
    "API_CONTRACT",
    "DATABASE_MIGRATION",
    "TEST_CASE",
    "TEST_RUN",
    "SECURITY_CONTROL",
    "SECURITY_FINDING",
    "POLICY",
    "APPROVAL",
    "EVIDENCE",
    "RELEASE",
    "ARTIFACT",
    "DEPLOYMENT",
    "INCIDENT",
    "RUNBOOK",
    "ADR",
}

GRAPH_RELATIONSHIP_TYPES = {"CONTAINS", "DEPENDS_ON", "USES", "CALLS", "PUBLISHES", "CONSUMES", "READS", "WRITES", "AUTHENTICATES", "AUTHORIZES", "ROUTES_TO", "DEPLOYS_TO", "RUNS_ON", "MONITORS", "PROTECTS", "IMPLEMENTS", "SATISFIES", "VERIFIES", "MITIGATES", "SUPERSEDES"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _stable_digest(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _upper(value: Any) -> str:
    return str(value or "").strip().upper()


class ArchitectureError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


@dataclass(frozen=True)
class ArchitectureExecutionContext:
    actor_id: str
    tenant_id: str
    organization_id: str
    workspace_id: str | None
    project_id: str | None
    request_id: str | None
    role: str
    permissions: tuple[str, ...]
    session_id: str | None
    correlation_id: str
    causation_id: str | None = None
    environment: str = "development"


class NovaCodeProNCP006AService:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository

    # ------------------------------------------------------------------
    # guards and record helpers
    # ------------------------------------------------------------------
    def _admin_override(self, ctx: ArchitectureExecutionContext) -> bool:
        return ctx.role in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN"}

    def _ensure_permission(self, ctx: ArchitectureExecutionContext, permission: str) -> None:
        if permission in ctx.permissions or self._admin_override(ctx):
            return
        raise ArchitectureError("architecture_forbidden", f"Missing permission: {permission}", 403)

    def _ensure_tenant(self, record: dict[str, Any], ctx: ArchitectureExecutionContext) -> None:
        if _lower(record.get("tenant_id")) != _lower(ctx.tenant_id):
            raise ArchitectureError("cross_tenant_architecture_forbidden", "Cross-tenant access is forbidden.", 403)

    def _ensure_workspace(self, record: dict[str, Any], ctx: ArchitectureExecutionContext) -> None:
        record_workspace = _lower(record.get("workspace_id"))
        if ctx.workspace_id and record_workspace and record_workspace != _lower(ctx.workspace_id):
            raise ArchitectureError("cross_workspace_architecture_forbidden", "Cross-workspace access is forbidden.", 403)

    def _ensure_model(self, model_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        model = self.repository.get("architecture_model", model_id)
        if model is None:
            raise ArchitectureError("architecture_model_not_found", "Architecture model not found.", 404)
        self._ensure_tenant(model, ctx)
        self._ensure_workspace(model, ctx)
        return model

    def _ensure_workspace_record(self, workspace_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        workspace = self.repository.get("architecture_workspace", workspace_id)
        if workspace is None:
            raise ArchitectureError("architecture_workspace_not_found", "Architecture workspace not found.", 404)
        self._ensure_tenant(workspace, ctx)
        return workspace

    def _record(self, kind: str, ctx: ArchitectureExecutionContext, payload: dict[str, Any], *, record_id: str | None = None, version: int = 1, status: str = "DRAFT") -> dict[str, Any]:
        now = _utc_now()
        record = {
            "id": record_id or payload.get("id") or _new_id(kind.replace("_", "-")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": payload.get("workspace_id") or ctx.workspace_id,
            "project_id": payload.get("project_id") or ctx.project_id,
            "request_id": payload.get("request_id") or ctx.request_id,
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "created_at": now,
            "updated_at": now,
            "version": int(version),
            "status": status,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": dict(payload.get("metadata") or {}),
        }
        record.update(payload)
        record["id"] = str(record["id"])
        return record

    def _list_kind(self, kind: str, ctx: ArchitectureExecutionContext, *, workspace_id: str | None = None, model_id: str | None = None) -> list[dict[str, Any]]:
        items = [dict(item) for item in self.repository.list(kind) if _lower(item.get("tenant_id")) == _lower(ctx.tenant_id)]
        if workspace_id or ctx.workspace_id:
            wanted = _lower(workspace_id or ctx.workspace_id)
            items = [item for item in items if _lower(item.get("workspace_id")) == wanted]
        if model_id:
            wanted = _lower(model_id)
            items = [item for item in items if _lower(item.get("model_id")) == wanted]
        return items

    def _append_event(self, event_type: str, ctx: ArchitectureExecutionContext, *, resource_type: str, resource_id: str, project_id: str | None = None, request_id: str | None = None, previous_state: Any = None, new_state: Any = None, result: str = "SUCCESS", error_code: str = "", approval_reference: str | None = None, evidence_reference: str | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        event = {
            "event_id": _new_id("arch-event"),
            "occurred_at": _utc_now(),
            "event_type": event_type,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "project_id": project_id or ctx.project_id,
            "workflow_id": request_id or ctx.request_id,
            "actor": {"type": "user", "id": ctx.actor_id},
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": {"service": "ncp006a", "workspace_id": ctx.workspace_id},
            "data": {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "previous_state": previous_state,
                "new_state": new_state,
                "result": result,
                "error_code": error_code,
                "approval_reference": approval_reference,
                "evidence_reference": evidence_reference,
                **(extra or {}),
            },
        }
        self.repository.append_event(event)
        self.repository.upsert(
            "audit_event",
            {
                "id": event["event_id"],
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": project_id or ctx.project_id,
                "request_id": request_id or ctx.request_id,
                "created_by": ctx.actor_id,
                "updated_by": ctx.actor_id,
                "created_at": event["occurred_at"],
                "updated_at": event["occurred_at"],
                "version": 1,
                "status": result,
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "metadata": {
                    "event_type": event_type,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "previous_state": previous_state,
                    "new_state": new_state,
                    "result": result,
                    "error_code": error_code,
                    "approval_reference": approval_reference,
                    "evidence_reference": evidence_reference,
                    **(extra or {}),
                },
            },
        )
        return event

    def _snapshot_version(self, model: dict[str, Any], ctx: ArchitectureExecutionContext, *, change_summary: str, source_references: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        version = {
            "id": _new_id("architecture-version"),
            "model_id": model["id"],
            "version_number": int(model.get("version") or 1),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": model.get("workspace_id"),
            "project_id": model.get("project_id"),
            "request_id": model.get("request_id"),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "version": int(model.get("version") or 1),
            "status": _upper(model.get("status") or "DRAFT"),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": dict(model.get("metadata") or {}),
            "content": dict(model),
            "change_summary": change_summary,
            "content_digest": _stable_digest(model),
            "approval_digest": _stable_digest({"approvals": self._list_kind("architecture_approval", ctx, model_id=model["id"])}),
            "source_references": list(source_references or []),
        }
        self.repository.upsert("architecture_version", version)
        return version

    def _validate_enum(self, value: str, options: Iterable[str], code: str, message: str) -> str:
        normalized = _upper(value)
        if normalized not in set(options):
            raise ArchitectureError(code, message, 400)
        return normalized

    def _traceability_resource_kind(self, resource_type: str) -> str | None:
        mapping = {
            "REQUEST": "request",
            "REQUIREMENT": "requirement",
            "ACCEPTANCE_CRITERION": "acceptance_criterion",
            "ARCHITECTURE_DECISION": "architecture_decision",
            "ARCHITECTURE_COMPONENT": "architecture_component",
            "ARCHITECTURE_MODEL": "architecture_model",
            "ARCHITECTURE_WORKSPACE": "architecture_workspace",
            "DESIGN_ARTIFACT": "design_artifact",
            "PROJECT": "project",
            "WORK_ITEM": "work_item",
            "CODE_COMMIT": "code_commit",
            "CODE_FILE": "code_file",
            "API_CONTRACT": "api_contract",
            "DATABASE_MIGRATION": "database_migration",
            "TEST_CASE": "test_case",
            "TEST_RUN": "test_run",
            "SECURITY_CONTROL": "security_control",
            "SECURITY_FINDING": "security_finding",
            "POLICY": "policy",
            "APPROVAL": "approval",
            "EVIDENCE": "evidence",
            "RELEASE": "release",
            "ARTIFACT": "artifact",
            "DEPLOYMENT": "deployment",
            "INCIDENT": "incident",
            "RUNBOOK": "runbook",
            "ADR": "adr",
        }
        return mapping.get(_upper(resource_type))

    def _assert_traceability_resource_exists(self, resource_type: str, resource_id: str, ctx: ArchitectureExecutionContext) -> None:
        kind = self._traceability_resource_kind(resource_type)
        if kind is None:
            raise ArchitectureError("traceability_target_not_found", "Unsupported traceability resource type.", 400)
        if not self.repository.get(kind, resource_id):
            raise ArchitectureError("traceability_target_not_found", "Traceability resource not found.", 404)

    def _workspace_scope(self, workspace_id: str | None, ctx: ArchitectureExecutionContext) -> str:
        scope = workspace_id or ctx.workspace_id
        if not scope:
            raise ArchitectureError("workspace_required", "Workspace context is required.", 409)
        return str(scope)

    # ------------------------------------------------------------------
    # workspaces
    # ------------------------------------------------------------------
    def list_workspaces(self, ctx: ArchitectureExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "architecture.read")
        return self._list_kind("architecture_workspace", ctx)

    def create_workspace(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.create")
        workspace_id = str(payload.get("id") or payload.get("workspace_id") or _new_id("architecture-workspace"))
        workspace = self._record(
            "architecture_workspace",
            ctx,
            {
                "id": workspace_id,
                "name": str(payload.get("name") or "Architecture Workspace"),
                "slug": str(payload.get("slug") or str(payload.get("name") or "architecture-workspace").lower().replace(" ", "-")),
                "description": str(payload.get("description") or ""),
                "domain": self._validate_enum(payload.get("domain") or "ENTERPRISE", ARCHITECTURE_DOMAINS, "validation_failed", "Unsupported architecture domain."),
                "status": _upper(payload.get("status") or "ACTIVE"),
                "owner_id": str(payload.get("owner_id") or ctx.actor_id),
                "model_ids": list(payload.get("model_ids") or []),
                "view_ids": list(payload.get("view_ids") or []),
                "baseline_ids": list(payload.get("baseline_ids") or []),
                "review_ids": list(payload.get("review_ids") or []),
                "approval_ids": list(payload.get("approval_ids") or []),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=workspace_id,
            status=_upper(payload.get("status") or "ACTIVE"),
        )
        self.repository.upsert("architecture_workspace", workspace)
        self._append_event("architecture.workspace.created", ctx, resource_type="architecture_workspace", resource_id=workspace["id"], new_state=workspace["status"])
        return workspace

    def get_workspace(self, workspace_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.read")
        workspace = self._ensure_workspace_record(workspace_id, ctx)
        return workspace

    def update_workspace(self, workspace_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.update")
        workspace = self._ensure_workspace_record(workspace_id, ctx)
        previous = dict(workspace)
        workspace.update(
            {
                "name": str(payload.get("name") or workspace.get("name") or ""),
                "slug": str(payload.get("slug") or workspace.get("slug") or ""),
                "description": str(payload.get("description") or workspace.get("description") or ""),
                "domain": self._validate_enum(payload.get("domain") or workspace.get("domain") or "ENTERPRISE", ARCHITECTURE_DOMAINS, "validation_failed", "Unsupported architecture domain."),
                "status": _upper(payload.get("status") or workspace.get("status") or "ACTIVE"),
                "owner_id": str(payload.get("owner_id") or workspace.get("owner_id") or ctx.actor_id),
                "metadata": {**dict(workspace.get("metadata") or {}), **dict(payload.get("metadata") or {})},
                "updated_by": ctx.actor_id,
                "updated_at": _utc_now(),
                "version": int(workspace.get("version") or 1) + 1,
            }
        )
        self.repository.upsert("architecture_workspace", workspace)
        self._append_event("architecture.workspace.updated", ctx, resource_type="architecture_workspace", resource_id=workspace_id, previous_state=previous.get("status"), new_state=workspace["status"])
        return workspace

    # ------------------------------------------------------------------
    # models and graph primitives
    # ------------------------------------------------------------------
    def list_models(self, ctx: ArchitectureExecutionContext, *, workspace_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "architecture.read")
        return self._list_kind("architecture_model", ctx, workspace_id=workspace_id)

    def create_model(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.create")
        workspace_id = self._workspace_scope(str(payload.get("workspace_id") or ctx.workspace_id or ""), ctx)
        self._ensure_workspace_record(workspace_id, ctx)
        model_id = str(payload.get("id") or payload.get("model_id") or _new_id("architecture-model"))
        model = self._record(
            "architecture_model",
            ctx,
            {
                "id": model_id,
                "workspace_id": workspace_id,
                "project_id": str(payload.get("project_id") or ctx.project_id or ""),
                "request_id": str(payload.get("request_id") or ctx.request_id or ""),
                "name": str(payload.get("name") or "Architecture Model"),
                "slug": str(payload.get("slug") or str(payload.get("name") or "architecture-model").lower().replace(" ", "-")),
                "description": str(payload.get("description") or ""),
                "domain": self._validate_enum(payload.get("domain") or "SOLUTION", ARCHITECTURE_DOMAINS, "validation_failed", "Unsupported architecture domain."),
                "status": _upper(payload.get("status") or "DRAFT"),
                "owner_id": str(payload.get("owner_id") or ctx.actor_id),
                "current_version_id": "",
                "component_ids": list(payload.get("component_ids") or []),
                "interface_ids": list(payload.get("interface_ids") or []),
                "data_ids": list(payload.get("data_ids") or []),
                "security_ids": list(payload.get("security_ids") or []),
                "deployment_ids": list(payload.get("deployment_ids") or []),
                "relationship_ids": list(payload.get("relationship_ids") or []),
                "requirement_ids": list(payload.get("requirement_ids") or []),
                "technology_standard": str(payload.get("technology_standard") or ""),
                "threat_model": list(payload.get("threat_model") or []),
                "slo": dict(payload.get("slo") or {}),
                "metadata": dict(payload.get("metadata") or {}),
                "citations": list(payload.get("citations") or []),
            },
            record_id=model_id,
            status=_upper(payload.get("status") or "DRAFT"),
        )
        self.repository.upsert("architecture_model", model)
        version = self._snapshot_version(model, ctx, change_summary="Model created", source_references=list(payload.get("source_references") or []))
        model["current_version_id"] = version["id"]
        model["version"] = int(model.get("version") or 1)
        model["content_digest"] = version["content_digest"]
        self.repository.upsert("architecture_model", model)
        self._append_event("architecture.model.created", ctx, resource_type="architecture_model", resource_id=model_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=model["status"], evidence_reference=version["id"])
        if "architecture.traceability" in ctx.permissions or self._admin_override(ctx):
            for requirement_id in model["requirement_ids"]:
                if not requirement_id:
                    continue
                self.create_traceability_link(
                    {
                        "source_type": "REQUIREMENT",
                        "source_id": requirement_id,
                        "target_type": "ARCHITECTURE_MODEL",
                        "target_id": model_id,
                        "relationship": "SATISFIES",
                        "creation_method": "architecture_model_import",
                        "confidence": 0.9,
                        "verification_status": "UNVERIFIED",
                        "evidence_reference": version["id"],
                    },
                    ctx,
                )
        return model

    def get_model(self, model_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.read")
        return self._ensure_model(model_id, ctx)

    def update_model(self, model_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.update")
        model = self._ensure_model(model_id, ctx)
        previous = dict(model)
        model.update(
            {
                "name": str(payload.get("name") or model.get("name") or ""),
                "slug": str(payload.get("slug") or model.get("slug") or ""),
                "description": str(payload.get("description") or model.get("description") or ""),
                "domain": self._validate_enum(payload.get("domain") or model.get("domain") or "SOLUTION", ARCHITECTURE_DOMAINS, "validation_failed", "Unsupported architecture domain."),
                "status": _upper(payload.get("status") or model.get("status") or "DRAFT"),
                "owner_id": str(payload.get("owner_id") or model.get("owner_id") or ctx.actor_id),
                "technology_standard": str(payload.get("technology_standard") or model.get("technology_standard") or ""),
                "threat_model": list(payload.get("threat_model") or model.get("threat_model") or []),
                "slo": {**dict(model.get("slo") or {}), **dict(payload.get("slo") or {})},
                "metadata": {**dict(model.get("metadata") or {}), **dict(payload.get("metadata") or {})},
                "component_ids": list(payload.get("component_ids") or model.get("component_ids") or []),
                "interface_ids": list(payload.get("interface_ids") or model.get("interface_ids") or []),
                "data_ids": list(payload.get("data_ids") or model.get("data_ids") or []),
                "security_ids": list(payload.get("security_ids") or model.get("security_ids") or []),
                "deployment_ids": list(payload.get("deployment_ids") or model.get("deployment_ids") or []),
                "relationship_ids": list(payload.get("relationship_ids") or model.get("relationship_ids") or []),
                "requirement_ids": list(payload.get("requirement_ids") or model.get("requirement_ids") or []),
                "updated_by": ctx.actor_id,
                "updated_at": _utc_now(),
                "version": int(model.get("version") or 1) + 1,
            }
        )
        version = self._snapshot_version(model, ctx, change_summary=str(payload.get("change_summary") or "Model updated"), source_references=list(payload.get("source_references") or []))
        model["current_version_id"] = version["id"]
        model["content_digest"] = version["content_digest"]
        self.repository.upsert("architecture_model", model)
        self._append_event("architecture.model.updated", ctx, resource_type="architecture_model", resource_id=model_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, previous_state=previous.get("status"), new_state=model["status"], evidence_reference=version["id"])
        return model

    def archive_model(self, model_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.update")
        model = self._ensure_model(model_id, ctx)
        model["status"] = "ARCHIVED"
        model["archived_at"] = _utc_now()
        model["archived_by"] = ctx.actor_id
        model["version"] = int(model.get("version") or 1) + 1
        model["updated_by"] = ctx.actor_id
        model["updated_at"] = _utc_now()
        version = self._snapshot_version(model, ctx, change_summary="Model archived")
        model["current_version_id"] = version["id"]
        model["content_digest"] = version["content_digest"]
        self.repository.upsert("architecture_model", model)
        self._append_event("architecture.model.archived", ctx, resource_type="architecture_model", resource_id=model_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, previous_state="ACTIVE", new_state="ARCHIVED", evidence_reference=version["id"])
        return model

    def list_versions(self, model_id: str, ctx: ArchitectureExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "architecture.read")
        self._ensure_model(model_id, ctx)
        return [version for version in self._list_kind("architecture_version", ctx, model_id=model_id) if _lower(version.get("model_id")) == _lower(model_id)]

    def get_version(self, model_id: str, version_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.read")
        version = self.repository.get("architecture_version", version_id)
        if version is None or _lower(version.get("model_id")) != _lower(model_id):
            raise ArchitectureError("architecture_version_not_found", "Architecture version not found.", 404)
        self._ensure_tenant(version, ctx)
        self._ensure_workspace(version, ctx)
        return version

    # ------------------------------------------------------------------
    # generic child resources
    # ------------------------------------------------------------------
    def _create_child(self, kind: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext, *, permission: str, status: str = "DRAFT") -> dict[str, Any]:
        self._ensure_permission(ctx, permission)
        model = self._ensure_model(str(payload.get("model_id") or ""), ctx)
        record_id = str(payload.get("id") or payload.get(f"{kind}_id") or _new_id(kind.replace("_", "-")))
        record = self._record(kind, ctx, {"id": record_id, "model_id": model["id"], **payload}, record_id=record_id, status=status)
        self.repository.upsert(kind, record)
        self._append_event(f"architecture.{kind}.created", ctx, resource_type=kind, resource_id=record["id"], project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=record["status"])
        return record

    def _update_child(self, kind: str, record_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext, *, permission: str) -> dict[str, Any]:
        self._ensure_permission(ctx, permission)
        record = self.repository.get(kind, record_id)
        if record is None:
            raise ArchitectureError(f"{kind}_not_found", f"{kind.replace('_', ' ').title()} not found.", 404)
        self._ensure_tenant(record, ctx)
        self._ensure_workspace(record, ctx)
        previous = dict(record)
        record.update(
            {
                **{key: value for key, value in payload.items() if key not in {"id", "model_id", "tenant_id", "organization_id", "workspace_id"}},
                "updated_by": ctx.actor_id,
                "updated_at": _utc_now(),
                "version": int(record.get("version") or 1) + 1,
            }
        )
        self.repository.upsert(kind, record)
        self._append_event(f"architecture.{kind}.updated", ctx, resource_type=kind, resource_id=record_id, project_id=record.get("project_id") or None, request_id=record.get("request_id") or None, previous_state=previous.get("status"), new_state=record.get("status"))
        return record

    def _list_child(self, kind: str, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "architecture.read")
        items = self._list_kind(kind, ctx, model_id=model_id)
        if model_id:
            items = [item for item in items if _lower(item.get("model_id")) == _lower(model_id)]
        return items

    # components / interfaces / data / security / deployments
    def list_components(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_component", ctx, model_id=model_id)

    def create_component(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        kind = "architecture_component"
        self._ensure_permission(ctx, "architecture.create")
        component_type = self._validate_enum(payload.get("component_type") or "APPLICATION", COMPONENT_TYPES, "validation_failed", "Unsupported component type.")
        model = self._ensure_model(str(payload.get("model_id") or ""), ctx)
        component_id = str(payload.get("id") or payload.get("component_id") or _new_id("architecture-component"))
        component = self._record(
            kind,
            ctx,
            {
                "id": component_id,
                "model_id": model["id"],
                "name": str(payload.get("name") or "Component"),
                "component_type": component_type,
                "description": str(payload.get("description") or ""),
                "technology": str(payload.get("technology") or ""),
                "status": _upper(payload.get("status") or "DRAFT"),
                "owner_id": str(payload.get("owner_id") or ctx.actor_id),
                "interfaces": list(payload.get("interfaces") or []),
                "dependencies": list(payload.get("dependencies") or []),
                "data_classification": str(payload.get("data_classification") or "INTERNAL"),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=component_id,
            status=_upper(payload.get("status") or "DRAFT"),
        )
        self.repository.upsert(kind, component)
        self._append_event("architecture.component.created", ctx, resource_type=kind, resource_id=component_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=component["status"])
        return component

    def update_component(self, component_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        return self._update_child("architecture_component", component_id, payload, ctx, permission="architecture.update")

    def list_interfaces(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_interface", ctx, model_id=model_id)

    def create_interface(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        kind = "architecture_interface"
        self._ensure_permission(ctx, "architecture.create")
        interface_type = self._validate_enum(payload.get("interface_type") or "REST", INTERFACE_TYPES, "validation_failed", "Unsupported interface type.")
        model = self._ensure_model(str(payload.get("model_id") or ""), ctx)
        interface_id = str(payload.get("id") or payload.get("interface_id") or _new_id("architecture-interface"))
        interface = self._record(
            kind,
            ctx,
            {
                "id": interface_id,
                "model_id": model["id"],
                "name": str(payload.get("name") or "Interface"),
                "interface_type": interface_type,
                "source_id": str(payload.get("source_id") or ""),
                "target_id": str(payload.get("target_id") or ""),
                "protocol": str(payload.get("protocol") or interface_type.lower()),
                "status": _upper(payload.get("status") or "DRAFT"),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=interface_id,
            status=_upper(payload.get("status") or "DRAFT"),
        )
        self.repository.upsert(kind, interface)
        self._append_event("architecture.interface.created", ctx, resource_type=kind, resource_id=interface_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=interface["status"])
        return interface

    def update_interface(self, interface_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        return self._update_child("architecture_interface", interface_id, payload, ctx, permission="architecture.update")

    def list_data(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_data", ctx, model_id=model_id)

    def create_data(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        kind = "architecture_data"
        self._ensure_permission(ctx, "architecture.create")
        model = self._ensure_model(str(payload.get("model_id") or ""), ctx)
        data_id = str(payload.get("id") or payload.get("data_id") or _new_id("architecture-data"))
        data = self._record(
            kind,
            ctx,
            {
                "id": data_id,
                "model_id": model["id"],
                "name": str(payload.get("name") or "Data Model"),
                "logical_model": dict(payload.get("logical_model") or {}),
                "physical_model": dict(payload.get("physical_model") or {}),
                "entities": list(payload.get("entities") or []),
                "relationships": list(payload.get("relationships") or []),
                "data_stores": list(payload.get("data_stores") or []),
                "ownership": dict(payload.get("ownership") or {}),
                "classification": _upper(payload.get("classification") or "INTERNAL"),
                "retention": str(payload.get("retention") or "retain-indefinitely"),
                "encryption": dict(payload.get("encryption") or {}),
                "lineage": list(payload.get("lineage") or []),
                "replication": dict(payload.get("replication") or {}),
                "backup": dict(payload.get("backup") or {}),
                "recovery": dict(payload.get("recovery") or {}),
                "migration": dict(payload.get("migration") or {}),
                "status": _upper(payload.get("status") or "DRAFT"),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=data_id,
            status=_upper(payload.get("status") or "DRAFT"),
        )
        self.repository.upsert(kind, data)
        self._append_event("architecture.data.created", ctx, resource_type=kind, resource_id=data_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=data["status"])
        return data

    def update_data(self, data_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        return self._update_child("architecture_data", data_id, payload, ctx, permission="architecture.update")

    def list_security(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_security", ctx, model_id=model_id)

    def create_security(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        kind = "architecture_security"
        self._ensure_permission(ctx, "architecture.create")
        model = self._ensure_model(str(payload.get("model_id") or ""), ctx)
        security_id = str(payload.get("id") or payload.get("security_id") or _new_id("architecture-security"))
        security = self._record(
            kind,
            ctx,
            {
                "id": security_id,
                "model_id": model["id"],
                "trust_boundaries": list(payload.get("trust_boundaries") or []),
                "identity_flows": list(payload.get("identity_flows") or []),
                "authentication": dict(payload.get("authentication") or {}),
                "authorization": dict(payload.get("authorization") or {}),
                "secrets": dict(payload.get("secrets") or {}),
                "encryption": dict(payload.get("encryption") or {}),
                "threat_model": [self._validate_enum(item, THREAT_TYPES, "validation_failed", "Unsupported threat type.") for item in list(payload.get("threat_model") or [])] or ["SPOOFING"],
                "security_controls": list(payload.get("security_controls") or []),
                "privacy_controls": list(payload.get("privacy_controls") or []),
                "compliance_controls": list(payload.get("compliance_controls") or []),
                "status": _upper(payload.get("status") or "DRAFT"),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=security_id,
            status=_upper(payload.get("status") or "DRAFT"),
        )
        self.repository.upsert(kind, security)
        self._append_event("architecture.security.created", ctx, resource_type=kind, resource_id=security_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=security["status"])
        return security

    def update_security(self, security_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        return self._update_child("architecture_security", security_id, payload, ctx, permission="architecture.update")

    def list_deployments(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_deployment", ctx, model_id=model_id)

    def create_deployment(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        kind = "architecture_deployment"
        self._ensure_permission(ctx, "architecture.create")
        model = self._ensure_model(str(payload.get("model_id") or ""), ctx)
        deployment_id = str(payload.get("id") or payload.get("deployment_id") or _new_id("architecture-deployment"))
        environment = self._validate_enum(payload.get("environment") or "DEVELOPMENT", DEPLOYMENT_ENVIRONMENTS, "validation_failed", "Unsupported deployment environment.")
        deployment = self._record(
            kind,
            ctx,
            {
                "id": deployment_id,
                "model_id": model["id"],
                "environment": environment,
                "region": str(payload.get("region") or "australia-southeast"),
                "nodes": list(payload.get("nodes") or []),
                "zones": list(payload.get("zones") or []),
                "topology": dict(payload.get("topology") or {}),
                "status": _upper(payload.get("status") or "DRAFT"),
                "slo": dict(payload.get("slo") or {}),
                "rto": str(payload.get("rto") or ""),
                "rpo": str(payload.get("rpo") or ""),
                "health_checks": list(payload.get("health_checks") or []),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=deployment_id,
            status=_upper(payload.get("status") or "DRAFT"),
        )
        self.repository.upsert(kind, deployment)
        self._append_event("architecture.deployment.created", ctx, resource_type=kind, resource_id=deployment_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=deployment["status"])
        return deployment

    def update_deployment(self, deployment_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        return self._update_child("architecture_deployment", deployment_id, payload, ctx, permission="architecture.update")

    # ------------------------------------------------------------------
    # reviews, approvals, baselines
    # ------------------------------------------------------------------
    def list_reviews(self, model_id: str, ctx: ArchitectureExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "architecture.read")
        self._ensure_model(model_id, ctx)
        return self._list_kind("architecture_review", ctx, model_id=model_id)

    def create_review(self, model_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.review")
        model = self._ensure_model(model_id, ctx)
        review_id = str(payload.get("id") or payload.get("review_id") or _new_id("architecture-review"))
        review = self._record(
            "architecture_review",
            ctx,
            {
                "id": review_id,
                "model_id": model["id"],
                "review_type": self._validate_enum(payload.get("review_type") or "ARCHITECTURE", REVIEW_TYPES, "validation_failed", "Unsupported review type."),
                "findings": list(payload.get("findings") or []),
                "decision": "PENDING",
                "requested_by": ctx.actor_id,
                "required_role": str(payload.get("required_role") or "ARCHITECT"),
                "status": "OPEN",
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=review_id,
            status="OPEN",
        )
        self.repository.upsert("architecture_review", review)
        self._append_event("architecture.review.created", ctx, resource_type="architecture_review", resource_id=review_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state="OPEN")
        return review

    def complete_review(self, model_id: str, review_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.review")
        review = self.repository.get("architecture_review", review_id)
        if review is None or _lower(review.get("model_id")) != _lower(model_id):
            raise ArchitectureError("architecture_review_not_found", "Architecture review not found.", 404)
        self._ensure_tenant(review, ctx)
        self._ensure_workspace(review, ctx)
        decision = self._validate_enum(payload.get("decision") or "APPROVED", ("APPROVED", "REJECTED", "CHANGES_REQUESTED"), "validation_failed", "Unsupported review decision.")
        review["decision"] = decision
        review["findings"] = list(payload.get("findings") or review.get("findings") or [])
        review["status"] = decision
        review["updated_by"] = ctx.actor_id
        review["updated_at"] = _utc_now()
        review["version"] = int(review.get("version") or 1) + 1
        self.repository.upsert("architecture_review", review)
        self._append_event("architecture.review.completed", ctx, resource_type="architecture_review", resource_id=review_id, project_id=review.get("project_id") or None, request_id=review.get("request_id") or None, previous_state="OPEN", new_state=decision)
        return review

    def list_approvals(self, model_id: str, ctx: ArchitectureExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "architecture.read")
        self._ensure_model(model_id, ctx)
        return self._list_kind("architecture_approval", ctx, model_id=model_id)

    def request_approval(self, model_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.review")
        model = self._ensure_model(model_id, ctx)
        approval_id = str(payload.get("id") or payload.get("approval_id") or _new_id("architecture-approval"))
        approval = self._record(
            "architecture_approval",
            ctx,
            {
                "id": approval_id,
                "model_id": model["id"],
                "requested_from": str(payload.get("requested_from") or "ARCHITECT"),
                "requested_by": ctx.actor_id,
                "required_role": str(payload.get("required_role") or "ARCHITECT"),
                "risk_class": _upper(payload.get("risk_class") or "MODERATE"),
                "decision": "PENDING",
                "reason": "",
                "conditions": list(payload.get("conditions") or []),
                "expires_at": str(payload.get("expires_at") or ""),
                "model_digest": model.get("content_digest") or _stable_digest(model),
                "status": "OPEN",
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=approval_id,
            status="OPEN",
        )
        self.repository.upsert("architecture_approval", approval)
        self._append_event("architecture.approval.requested", ctx, resource_type="architecture_approval", resource_id=approval_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state="OPEN")
        return approval

    def decide_approval(self, model_id: str, approval_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.approve")
        approval = self.repository.get("architecture_approval", approval_id)
        if approval is None or _lower(approval.get("model_id")) != _lower(model_id):
            raise ArchitectureError("architecture_approval_not_found", "Architecture approval not found.", 404)
        self._ensure_tenant(approval, ctx)
        self._ensure_workspace(approval, ctx)
        if approval.get("decision") not in {"PENDING", "OPEN"}:
            raise ArchitectureError("approval_expired", "Approval is not open.", 409)
        required_roles = {item.strip().upper() for item in str(approval.get("required_role") or "").split(",") if item.strip()}
        if required_roles and ctx.role not in required_roles and not self._admin_override(ctx):
            raise ArchitectureError("approval_forbidden", "Your role cannot approve this architecture.", 403)
        model = self._ensure_model(model_id, ctx)
        current_digest = model.get("content_digest") or _stable_digest({key: value for key, value in model.items() if key not in {"updated_at", "updated_by", "version"}})
        if current_digest != approval.get("model_digest"):
            raise ArchitectureError("plan_changed_after_approval", "The architecture changed after approval was requested.", 409)
        decision = self._validate_enum(payload.get("decision") or "APPROVED", APPROVAL_DECISIONS, "validation_failed", "Unsupported approval decision.")
        approval["decision"] = decision
        approval["reason"] = str(payload.get("reason") or "")
        approval["conditions"] = list(payload.get("conditions") or approval.get("conditions") or [])
        approval["status"] = decision
        approval["decided_at"] = _utc_now()
        approval["decided_by"] = ctx.actor_id
        approval["updated_by"] = ctx.actor_id
        approval["updated_at"] = _utc_now()
        approval["version"] = int(approval.get("version") or 1) + 1
        self.repository.upsert("architecture_approval", approval)
        if decision == "APPROVED":
            model["status"] = "APPROVED"
            model["version"] = int(model.get("version") or 1) + 1
            model["updated_by"] = ctx.actor_id
            model["updated_at"] = _utc_now()
            self.repository.upsert("architecture_model", model)
        self._append_event("architecture.approval.decided", ctx, resource_type="architecture_approval", resource_id=approval_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, previous_state="OPEN", new_state=decision)
        return approval

    def list_baselines(self, model_id: str, ctx: ArchitectureExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "architecture.read")
        self._ensure_model(model_id, ctx)
        return self._list_kind("architecture_baseline", ctx, model_id=model_id)

    def create_baseline(self, model_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.baseline")
        model = self._ensure_model(model_id, ctx)
        baseline_id = str(payload.get("id") or payload.get("baseline_id") or _new_id("architecture-baseline"))
        versions = self.list_versions(model_id, ctx)
        if not versions:
            versions = [self._snapshot_version(model, ctx, change_summary="Baseline snapshot")]
        approval_references = list(payload.get("approval_references") or [])
        baseline_status = "APPROVED" if approval_references else "DRAFT"
        baseline = self._record(
            "architecture_baseline",
            ctx,
            {
                "id": baseline_id,
                "model_id": model["id"],
                "name": str(payload.get("name") or f"{model.get('name', 'Architecture Model')} Baseline"),
                "status": baseline_status,
                "included_version_ids": [version["id"] for version in versions],
                "approval_references": approval_references,
                "content_digest": _stable_digest({"model": model, "versions": [version["id"] for version in versions]}),
                "snapshot": {
                    "model": dict(model),
                    "components": self.list_components(ctx, model_id=model_id),
                    "interfaces": self.list_interfaces(ctx, model_id=model_id),
                    "data": self.list_data(ctx, model_id=model_id),
                    "security": self.list_security(ctx, model_id=model_id),
                    "deployments": self.list_deployments(ctx, model_id=model_id),
                    "relationships": self.list_relationships(ctx, model_id=model_id),
                },
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=baseline_id,
            status=baseline_status,
        )
        self.repository.upsert("architecture_baseline", baseline)
        self._append_event("architecture.baseline.created", ctx, resource_type="architecture_baseline", resource_id=baseline_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=baseline["status"])
        return baseline

    def approve_baseline(self, model_id: str, baseline_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.approve")
        baseline = self.repository.get("architecture_baseline", baseline_id)
        if baseline is None or _lower(baseline.get("model_id")) != _lower(model_id):
            raise ArchitectureError("architecture_baseline_not_found", "Architecture baseline not found.", 404)
        self._ensure_tenant(baseline, ctx)
        self._ensure_workspace(baseline, ctx)
        baseline["status"] = "APPROVED"
        baseline["approval_references"] = list(payload.get("approval_references") or baseline.get("approval_references") or [])
        baseline["updated_by"] = ctx.actor_id
        baseline["updated_at"] = _utc_now()
        baseline["version"] = int(baseline.get("version") or 1) + 1
        self.repository.upsert("architecture_baseline", baseline)
        self._append_event("architecture.baseline.approved", ctx, resource_type="architecture_baseline", resource_id=baseline_id, new_state="APPROVED")
        return baseline

    def activate_baseline(self, model_id: str, baseline_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.baseline")
        baseline = self.repository.get("architecture_baseline", baseline_id)
        if baseline is None or _lower(baseline.get("model_id")) != _lower(model_id):
            raise ArchitectureError("architecture_baseline_not_found", "Architecture baseline not found.", 404)
        if _upper(baseline.get("status")) != "APPROVED":
            raise ArchitectureError("architecture_baseline_immutable", "Baseline must be approved before activation.", 409)
        baseline["status"] = "ACTIVE"
        baseline["updated_by"] = ctx.actor_id
        baseline["updated_at"] = _utc_now()
        baseline["version"] = int(baseline.get("version") or 1) + 1
        self.repository.upsert("architecture_baseline", baseline)
        self._append_event("architecture.baseline.activated", ctx, resource_type="architecture_baseline", resource_id=baseline_id, new_state="ACTIVE")
        return baseline

    def supersede_baseline(self, model_id: str, baseline_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.baseline")
        baseline = self.repository.get("architecture_baseline", baseline_id)
        if baseline is None or _lower(baseline.get("model_id")) != _lower(model_id):
            raise ArchitectureError("architecture_baseline_not_found", "Architecture baseline not found.", 404)
        baseline["status"] = "SUPERSEDED"
        baseline["updated_by"] = ctx.actor_id
        baseline["updated_at"] = _utc_now()
        baseline["version"] = int(baseline.get("version") or 1) + 1
        self.repository.upsert("architecture_baseline", baseline)
        self._append_event("architecture.baseline.superseded", ctx, resource_type="architecture_baseline", resource_id=baseline_id, new_state="SUPERSEDED")
        return baseline

    # ------------------------------------------------------------------
    # relationships / traceability
    # ------------------------------------------------------------------
    def list_relationships(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_relationship", ctx, model_id=model_id)

    def add_relationship(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.update")
        model = self._ensure_model(str(payload.get("model_id") or ""), ctx)
        relationship = self._validate_enum(payload.get("relationship") or "DEPENDS_ON", RELATIONSHIP_TYPES, "validation_failed", "Unsupported architecture relationship.")
        record_id = str(payload.get("id") or payload.get("relationship_id") or _new_id("architecture-relationship"))
        record = self._record(
            "architecture_relationship",
            ctx,
            {
                "id": record_id,
                "model_id": model["id"],
                "source_id": str(payload.get("source_id") or ""),
                "target_id": str(payload.get("target_id") or ""),
                "relationship": relationship,
                "label": str(payload.get("label") or ""),
                "status": _upper(payload.get("status") or "ACTIVE"),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=record_id,
            status=_upper(payload.get("status") or "ACTIVE"),
        )
        self.repository.upsert("architecture_relationship", record)
        self.repository.upsert("traceability_link", {
            "id": _new_id("traceability-link"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": model.get("project_id"),
            "request_id": model.get("request_id"),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "version": 1,
            "status": "ACTIVE",
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": {"architecture_model_id": model["id"], "creation_method": "architecture_relationship"},
            "source_type": "ARCHITECTURE_COMPONENT" if record["source_id"] else "ARCHITECTURE_MODEL",
            "source_id": record["source_id"] or model["id"],
            "target_type": "ARCHITECTURE_COMPONENT" if record["target_id"] else "ARCHITECTURE_MODEL",
            "target_id": record["target_id"] or model["id"],
            "relationship": relationship,
            "confidence": 1.0,
            "verification_status": "UNVERIFIED",
            "creation_method": "architecture_relationship",
            "evidence_reference": None,
        })
        self._append_event("architecture.relationship.created", ctx, resource_type="architecture_relationship", resource_id=record_id, project_id=model.get("project_id") or None, request_id=model.get("request_id") or None, new_state=relationship)
        return record

    def create_traceability_link(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.traceability")
        source_type = _upper(payload.get("source_type") or "")
        target_type = _upper(payload.get("target_type") or "")
        relationship = _upper(payload.get("relationship") or "DERIVED_FROM")
        if source_type not in TRACEABILITY_TYPES:
            raise ArchitectureError("traceability_target_not_found", "Unsupported traceability source type.", 400)
        if target_type not in TRACEABILITY_TYPES:
            raise ArchitectureError("traceability_target_not_found", "Unsupported traceability target type.", 400)
        if relationship not in {"DERIVED_FROM", "SATISFIES", "IMPLEMENTS", "VERIFIES", "VALIDATES", "DEPENDS_ON", "CONFLICTS_WITH", "SUPERSEDES", "MITIGATES", "APPROVED_BY", "EVIDENCED_BY", "RELEASED_IN", "DEPLOYED_AS", "OPERATED_BY"}:
            raise ArchitectureError("traceability_link_invalid", "Unsupported traceability relationship.", 400)
        source_id = str(payload.get("source_id") or "")
        target_id = str(payload.get("target_id") or "")
        if not source_id or not target_id:
            raise ArchitectureError("traceability_target_not_found", "Source and target are required.", 404)
        self._assert_traceability_resource_exists(source_type, source_id, ctx)
        self._assert_traceability_resource_exists(target_type, target_id, ctx)
        link = self._record(
            "traceability_link",
            ctx,
            {
                "source_type": source_type,
                "source_id": source_id,
                "target_type": target_type,
                "target_id": target_id,
                "relationship": relationship,
                "status": _upper(payload.get("status") or "ACTIVE"),
                "confidence": float(payload.get("confidence") or 1.0),
                "verification_status": _upper(payload.get("verification_status") or "UNVERIFIED"),
                "creation_method": str(payload.get("creation_method") or "manual"),
                "evidence_reference": payload.get("evidence_reference"),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=str(payload.get("id") or payload.get("link_id") or _new_id("traceability-link")),
            status=_upper(payload.get("status") or "ACTIVE"),
        )
        self.repository.upsert("traceability_link", link)
        self._append_event("traceability.link.created", ctx, resource_type="traceability_link", resource_id=link["id"], new_state=relationship)
        return link

    def list_traceability_links(self, ctx: ArchitectureExecutionContext, *, resource_type: str | None = None, resource_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "architecture.read")
        links = [link for link in self._list_kind("traceability_link", ctx) if _lower(link.get("tenant_id")) == _lower(ctx.tenant_id)]
        if resource_type:
            links = [link for link in links if _lower(link.get("source_type")) == _lower(resource_type) or _lower(link.get("target_type")) == _lower(resource_type)]
        if resource_id:
            links = [link for link in links if _lower(link.get("source_id")) == _lower(resource_id) or _lower(link.get("target_id")) == _lower(resource_id)]
        return links

    def traceability_resource(self, resource_type: str, resource_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.read")
        links = self.list_traceability_links(ctx, resource_id=resource_id)
        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "upstream": [link for link in links if _lower(link.get("target_id")) == _lower(resource_id)],
            "downstream": [link for link in links if _lower(link.get("source_id")) == _lower(resource_id)],
            "impact": {
                "upstream_count": len([link for link in links if _lower(link.get("target_id")) == _lower(resource_id)]),
                "downstream_count": len([link for link in links if _lower(link.get("source_id")) == _lower(resource_id)]),
            },
        }

    def calculate_traceability_coverage(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.read")
        models = self.list_models(ctx, workspace_id=ctx.workspace_id)
        if model_id:
            models = [model for model in models if _lower(model["id"]) == _lower(model_id)]
        total = len(models)
        architecture_covered = 0
        deployment_covered = 0
        evidence_covered = 0
        gaps: list[dict[str, Any]] = []
        for model in models:
            links = self.list_traceability_links(ctx, resource_id=model["id"])
            if any(link.get("target_type") in {"ARCHITECTURE_MODEL", "ARCHITECTURE_COMPONENT", "ARCHITECTURE_DECISION"} for link in links):
                architecture_covered += 1
            if any(link.get("target_type") == "DEPLOYMENT" for link in links):
                deployment_covered += 1
            if any(link.get("target_type") == "EVIDENCE" for link in links):
                evidence_covered += 1
            if not links:
                gaps.append({"model_id": model["id"], "gap": "missing_traceability"})
        denominator = max(total, 1)
        coverage = {
            "coverage_id": _new_id("architecture-coverage"),
            "models_with_architecture_links": architecture_covered / denominator,
            "models_with_deployment_links": deployment_covered / denominator,
            "models_with_evidence_links": evidence_covered / denominator,
        }
        coverage["coverage_ratio"] = (
            coverage["models_with_architecture_links"]
            + coverage["models_with_deployment_links"]
            + coverage["models_with_evidence_links"]
        ) / 3
        snapshot = self._record(
            "architecture_snapshot",
            ctx,
            {
                "model_id": model_id or "",
                "coverage": coverage,
                "gap_count": len(gaps),
                "model_count": total,
                "gaps": gaps,
                "metadata": {"calculated_at": _utc_now()},
            },
            record_id=_new_id("architecture-snapshot"),
            status="ACTIVE",
        )
        self.repository.upsert("architecture_snapshot", snapshot)
        self._append_event("architecture.coverage.calculated", ctx, resource_type="architecture_snapshot", resource_id=snapshot["id"], new_state=coverage)
        return {"snapshot": snapshot, "coverage": coverage, "gaps": gaps}

    # ------------------------------------------------------------------
    # validation, fitness, diagrams, impact
    # ------------------------------------------------------------------
    def _dependency_graph(self, model_id: str, ctx: ArchitectureExecutionContext) -> dict[str, set[str]]:
        edges: dict[str, set[str]] = {}
        for relationship in self.list_relationships(ctx, model_id=model_id):
            if _upper(relationship.get("relationship")) not in GRAPH_RELATIONSHIP_TYPES:
                continue
            source = str(relationship.get("source_id") or "")
            target = str(relationship.get("target_id") or "")
            if not source or not target:
                continue
            edges.setdefault(source, set()).add(target)
        return edges

    def _has_cycle(self, edges: dict[str, set[str]]) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for nxt in edges.get(node, set()):
                if dfs(nxt):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(dfs(node) for node in list(edges))

    def validate_model(self, model_id: str, payload: dict[str, Any] | None, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.validate")
        model = self._ensure_model(model_id, ctx)
        validation_type = _upper((payload or {}).get("validation_type") or "DEPENDENCY")
        if validation_type not in VALIDATION_TYPES:
            raise ArchitectureError("validation_failed", "Unsupported validation type.", 400)
        issues: list[dict[str, Any]] = []
        checks: dict[str, Any] = {"validation_type": validation_type}
        if validation_type in {"DEPENDENCY", "POLICY", "STANDARDS"}:
            edges = self._dependency_graph(model_id, ctx)
            checks["dependency_nodes"] = len(edges)
            checks["dependency_edges"] = sum(len(targets) for targets in edges.values())
            if self._has_cycle(edges):
                issues.append({"code": "dependency_cycles", "message": "Dependency cycle detected."})
        if validation_type in {"SECURITY", "POLICY"}:
            security_records = self.list_security(ctx, model_id=model_id)
            if not security_records:
                issues.append({"code": "missing_security_architecture", "message": "Security architecture is required."})
            for security in security_records:
                if not security.get("security_controls"):
                    issues.append({"code": "security_controls_missing", "message": "Security controls are missing.", "resource_id": security["id"]})
        if validation_type in {"DATA", "POLICY"}:
            data_records = self.list_data(ctx, model_id=model_id)
            if not data_records:
                issues.append({"code": "missing_data_architecture", "message": "Data architecture is required."})
            for data in data_records:
                if not data.get("classification") or not data.get("retention"):
                    issues.append({"code": "data_validation_failed", "message": "Data classification and retention are required.", "resource_id": data["id"]})
        if validation_type in {"DEPLOYMENT", "POLICY"}:
            deployments = self.list_deployments(ctx, model_id=model_id)
            if not deployments:
                issues.append({"code": "missing_deployment_architecture", "message": "Deployment architecture is required."})
            for deployment in deployments:
                if _upper(deployment.get("environment")) not in DEPLOYMENT_ENVIRONMENTS:
                    issues.append({"code": "deployment_validation_failed", "message": "Unsupported deployment environment.", "resource_id": deployment["id"]})
        if validation_type in {"STANDARDS", "POLICY"} and not model.get("technology_standard"):
            issues.append({"code": "technology_standard_missing", "message": "Technology standard is required."})
        status = "PASS" if not issues else "FAIL"
        validation = self._record(
            "architecture_validation_result",
            ctx,
            {
                "id": _new_id("architecture-validation"),
                "model_id": model["id"],
                "validation_type": validation_type,
                "status": status,
                "checks": checks,
                "issues": issues,
                "metadata": dict((payload or {}).get("metadata") or {}),
            },
            status=status,
        )
        self.repository.upsert("architecture_validation_result", validation)
        self._append_event("architecture.validation.completed", ctx, resource_type="architecture_validation_result", resource_id=validation["id"], new_state=status, error_code="" if status == "PASS" else "validation_failed")
        return validation

    def list_validation_results(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_validation_result", ctx, model_id=model_id)

    def evaluate_fitness(self, model_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.validate")
        model = self._ensure_model(model_id, ctx)
        validation = self.validate_model(model_id, {"validation_type": "POLICY"}, ctx)
        results = [
            {"name": "dependency_rules", "status": "PASS" if not any(issue["code"] == "dependency_cycles" for issue in validation["issues"]) else "FAIL"},
            {"name": "security_rules", "status": "PASS" if not any(issue["code"].startswith("security") for issue in validation["issues"]) else "FAIL"},
            {"name": "performance_rules", "status": "PASS" if model.get("slo") else "FAIL"},
            {"name": "availability_rules", "status": "PASS" if any(deployment.get("environment") in {"PRODUCTION", "DISASTER_RECOVERY", "MULTI_REGION"} for deployment in self.list_deployments(ctx, model_id=model_id)) else "FAIL"},
            {"name": "observability_rules", "status": "PASS" if any(component.get("component_type") == "OBSERVABILITY COMPONENT" for component in self.list_components(ctx, model_id=model_id)) else "FAIL"},
            {"name": "deployment_rules", "status": "PASS" if self.list_deployments(ctx, model_id=model_id) else "FAIL"},
            {"name": "technology_standards", "status": "PASS" if model.get("technology_standard") else "FAIL"},
        ]
        fitness = {
            "id": _new_id("architecture-fitness"),
            "model_id": model["id"],
            "status": "PASS" if all(result["status"] == "PASS" for result in results) else "FAIL",
            "results": results,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": model.get("project_id"),
            "request_id": model.get("request_id"),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "version": 1,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": {"validation_id": validation["id"]},
        }
        self.repository.upsert("architecture_fitness_function", fitness)
        self._append_event("architecture.fitness.evaluated", ctx, resource_type="architecture_fitness_function", resource_id=fitness["id"], new_state=fitness["status"])
        return fitness

    def list_fitness_functions(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_fitness_function", ctx, model_id=model_id)

    def create_diagram(self, model_id: str, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.read")
        model = self._ensure_model(model_id, ctx)
        diagram_type = _upper(payload.get("diagram_type") or "SYSTEM_CONTEXT")
        format_name = _upper(payload.get("format") or "JSON")
        relationships = self.list_relationships(ctx, model_id=model["id"])
        payload_export = {
            "model_id": model["id"],
            "diagram_type": diagram_type,
            "name": model.get("name"),
            "components": model.get("component_ids") or [],
            "relationships": [item.get("id") for item in relationships],
        }
        mermaid = "graph TD\n" + "\n".join(f"  {item['source_id']}-->{item['target_id']}" for item in relationships)
        plantuml = "@startuml\n" + "\n".join(f"{item['source_id']} --> {item['target_id']}" for item in relationships) + "\n@enduml"
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 600'><rect width='800' height='600' fill='#111827'/><text x='40' y='80' fill='#f9fafb' font-size='24'>{model.get('name')}</text><text x='40' y='130' fill='#d1d5db' font-size='16'>{diagram_type} • {format_name}</text></svg>"
        png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO4B0+QAAAAASUVORK5CYII="
        diagram = self._record(
            "architecture_diagram",
            ctx,
            {
                "id": str(payload.get("id") or payload.get("diagram_id") or _new_id("architecture-diagram")),
                "model_id": model["id"],
                "diagram_type": diagram_type,
                "format": format_name,
                "title": str(payload.get("title") or f"{model.get('name')} {diagram_type.title()}"),
                "content": dict(payload.get("content") or {}),
                "exports": {"json": payload_export, "mermaid": mermaid, "plantuml": plantuml, "svg": svg, "png": png},
                "metadata": dict(payload.get("metadata") or {}),
            },
            status="ACTIVE",
        )
        self.repository.upsert("architecture_diagram", diagram)
        self._append_event("architecture.diagram.created", ctx, resource_type="architecture_diagram", resource_id=diagram["id"], new_state=diagram_type)
        return diagram

    def list_diagrams(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_diagram", ctx, model_id=model_id)

    def calculate_impact(self, model_id: str, ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.read")
        model = self._ensure_model(model_id, ctx)
        links = self.list_traceability_links(ctx, resource_id=model["id"])
        affected_requirements = sorted({link["source_id"] for link in links if link.get("source_type") == "REQUIREMENT"} | {link["target_id"] for link in links if link.get("target_type") == "REQUIREMENT"})
        affected_apis = sorted({link["source_id"] for link in links if link.get("source_type") == "API_CONTRACT"} | {link["target_id"] for link in links if link.get("target_type") == "API_CONTRACT"})
        affected_services = sorted({link["source_id"] for link in links if link.get("source_type") in {"ARCHITECTURE_COMPONENT", "SERVICE", "MICROSERVICE", "API", "GATEWAY"}} | {link["target_id"] for link in links if link.get("target_type") in {"ARCHITECTURE_COMPONENT", "SERVICE", "MICROSERVICE", "API", "GATEWAY"}})
        affected_deployments = sorted({link["source_id"] for link in links if link.get("source_type") == "DEPLOYMENT"} | {link["target_id"] for link in links if link.get("target_type") == "DEPLOYMENT"})
        affected_tests = sorted({link["source_id"] for link in links if link.get("source_type") in {"TEST_CASE", "TEST_RUN"}} | {link["target_id"] for link in links if link.get("target_type") in {"TEST_CASE", "TEST_RUN"}})
        affected_releases = sorted({link["source_id"] for link in links if link.get("source_type") in {"RELEASE", "ARTIFACT"}} | {link["target_id"] for link in links if link.get("target_type") in {"RELEASE", "ARTIFACT"}})
        affected_documents = sorted({link["source_id"] for link in links if link.get("source_type") in {"ADR", "RUNBOOK", "POLICY"} } | {link["target_id"] for link in links if link.get("target_type") in {"ADR", "RUNBOOK", "POLICY"}})
        affected_risks = sorted({link["source_id"] for link in links if link.get("source_type") in {"INCIDENT", "SECURITY_FINDING"}} | {link["target_id"] for link in links if link.get("target_type") in {"INCIDENT", "SECURITY_FINDING"}})
        impact = {
            "id": _new_id("architecture-impact"),
            "model_id": model["id"],
            "affected_requirements": affected_requirements,
            "affected_apis": affected_apis,
            "affected_services": affected_services,
            "affected_deployments": affected_deployments,
            "affected_tests": affected_tests,
            "affected_releases": affected_releases,
            "affected_documents": affected_documents,
            "affected_risks": affected_risks,
            "traceability_link_count": len(links),
            "status": "ACTIVE" if links else "NO_IMPACT",
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": model.get("project_id"),
            "request_id": model.get("request_id"),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "version": 1,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": {"source_model_version": model.get("current_version_id")},
        }
        self.repository.upsert("architecture_impact", impact)
        self._append_event("architecture.impact.calculated", ctx, resource_type="architecture_impact", resource_id=impact["id"], new_state=impact["status"])
        return impact

    def list_impact(self, ctx: ArchitectureExecutionContext, *, model_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_child("architecture_impact", ctx, model_id=model_id)

    # ------------------------------------------------------------------
    # AI support
    # ------------------------------------------------------------------
    def draft_from_ai_execution(self, payload: dict[str, Any], ctx: ArchitectureExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "architecture.create")
        execution_id = str(payload.get("execution_id") or "")
        if not execution_id:
            raise ArchitectureError("validation_failed", "execution_id is required.", 400)
        model = self.create_model(
            {
                "workspace_id": payload.get("workspace_id") or ctx.workspace_id,
                "project_id": payload.get("project_id") or ctx.project_id,
                "request_id": payload.get("request_id") or ctx.request_id,
                "name": payload.get("name") or "AI Draft Architecture",
                "domain": payload.get("domain") or "SOLUTION",
                "description": payload.get("description") or "Draft generated from AI execution.",
                "status": "DRAFT",
                "metadata": {
                    "created_from_execution_id": execution_id,
                    "retrieval_id": payload.get("retrieval_id"),
                    "model": payload.get("model"),
                    "provider": payload.get("provider"),
                    "confidence": payload.get("confidence"),
                    "citations": list(payload.get("citations") or []),
                    **dict(payload.get("metadata") or {}),
                },
                "requirement_ids": list(payload.get("requirement_ids") or []),
                "source_references": [
                    {
                        "source_type": "AI_EXECUTION",
                        "source_id": execution_id,
                        "source_version": str(payload.get("execution_version") or ""),
                        "source_uri": str(payload.get("execution_uri") or ""),
                        "source_digest": str(payload.get("execution_digest") or ""),
                        "created_from_agent_id": str(payload.get("agent_id") or ""),
                        "created_from_execution_id": execution_id,
                        "created_from_tool_id": str(payload.get("tool_id") or ""),
                        "human_verified": False,
                    }
                ],
            },
            ctx,
        )
        self._append_event("architecture.model.drafted_from_ai", ctx, resource_type="architecture_model", resource_id=model["id"], new_state=model["status"], evidence_reference=model.get("current_version_id"))
        return model


__all__ = [
    "ARCHITECTURE_DOMAINS",
    "APPROVAL_DECISIONS",
    "ArchitectureError",
    "ArchitectureExecutionContext",
    "ARCHITECTURE_DOMAINS",
    "BASELINE_STATUSES",
    "COMPONENT_TYPES",
    "DEPLOYMENT_ENVIRONMENTS",
    "INTERFACE_TYPES",
    "NovaCodeProNCP006AService",
    "RELATIONSHIP_TYPES",
    "REVIEW_TYPES",
    "THREAT_TYPES",
    "TRACEABILITY_TYPES",
    "VALIDATION_TYPES",
]
