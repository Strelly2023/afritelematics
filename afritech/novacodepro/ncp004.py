from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from afritech.novacodepro.platform import NovaCodeProRepository, _event_envelope, _new_id, _now


EXECUTION_STATES = (
    "RECEIVED",
    "CLASSIFYING",
    "CLARIFICATION_REQUIRED",
    "CONTEXT_RETRIEVAL",
    "REQUIREMENTS_GENERATION",
    "PLANNING",
    "RISK_REVIEW",
    "POLICY_REVIEW",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "EXECUTING",
    "VERIFYING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "TIMED_OUT",
    "ROLLED_BACK",
    "ARCHIVED",
)

PLAN_STATES = (
    "DRAFT",
    "GENERATED",
    "VALIDATING",
    "POLICY_REVIEW",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "EXECUTING",
    "PAUSED",
    "VERIFYING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "ROLLED_BACK",
)

AGENT_EXECUTION_STATES = (
    "QUEUED",
    "STARTING",
    "RUNNING",
    "WAITING_FOR_TOOL",
    "WAITING_FOR_APPROVAL",
    "VERIFYING",
    "SUCCEEDED",
    "FAILED",
    "TIMED_OUT",
    "CANCELLED",
    "RETRYING",
)

RISK_LEVELS = ("LOW", "MODERATE", "HIGH", "CRITICAL")

REQ_TYPES = (
    "software feature",
    "bug fix",
    "architecture request",
    "ui/ux request",
    "api request",
    "database request",
    "testing request",
    "security request",
    "deployment request",
    "documentation request",
    "data analysis request",
    "operations request",
    "business process request",
    "compliance request",
)

ADMIN_ROLES = {
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
}

ALLOWED_ATTACHMENT_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/json",
    "text/csv",
    "image/png",
    "image/jpeg",
}

REQUEST_KEYWORDS = {
    "software feature": ("feature", "build", "create", "implement", "add"),
    "bug fix": ("bug", "fix", "defect", "regression", "error"),
    "architecture request": ("architecture", "design", "c4", "sequence", "diagram", "adr"),
    "ui/ux request": ("ui", "ux", "design", "wireframe", "experience", "prototype"),
    "api request": ("api", "openapi", "contract", "endpoint", "swagger"),
    "database request": ("database", "schema", "sql", "migration", "table"),
    "testing request": ("test", "qa", "coverage", "regression", "verification"),
    "security request": ("security", "auth", "identity", "mfa", "threat", "vulnerability"),
    "deployment request": ("deploy", "release", "rollout", "rollback", "kubernetes", "production"),
    "documentation request": ("doc", "documentation", "guide", "runbook", "readme"),
    "data analysis request": ("data", "analysis", "analytics", "report", "metric"),
    "operations request": ("operation", "incident", "slo", "runbook", "alert"),
    "business process request": ("business", "workflow", "process", "approval", "onsite"),
    "compliance request": ("compliance", "privacy", "regulation", "policy", "audit"),
}

AGENT_SEEDS: list[dict[str, Any]] = [
    {
        "agent_id": "business-analyst-agent",
        "name": "Business Analyst Agent",
        "version": "1.0.0",
        "description": "Clarifies intent and converts requests into requirements.",
        "purpose": "requirements",
        "supported_request_types": ["business process request", "software feature", "documentation request"],
        "allowed_tools": ["repository_read", "repository_search", "documentation_generation", "requirement_creation"],
        "required_permissions": ["ai.read", "ai.request", "request.read"],
        "risk_class": "LOW",
        "approval_policy": "none",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 30,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "product-manager-agent",
        "name": "Product Manager Agent",
        "version": "1.0.0",
        "description": "Frames business goals, scope and approval routing.",
        "purpose": "product",
        "supported_request_types": ["software feature", "business process request", "product request"],
        "allowed_tools": ["requirement_creation", "project_task_creation"],
        "required_permissions": ["ai.read", "request.read", "project.read"],
        "risk_class": "LOW",
        "approval_policy": "none",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 30,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "architecture-agent",
        "name": "Architecture Agent",
        "version": "1.0.0",
        "description": "Produces architecture decisions and dependency mapping.",
        "purpose": "architecture",
        "supported_request_types": ["architecture request", "software feature", "deployment request"],
        "allowed_tools": ["repository_read", "repository_search", "architecture_generation", "schema_validation"],
        "required_permissions": ["ai.read", "request.read", "project.read"],
        "risk_class": "MEDIUM",
        "approval_policy": "moderate",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 30,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "ui-ux-agent",
        "name": "UI/UX Agent",
        "version": "1.0.0",
        "description": "Creates interaction flows, wireframes, and accessibility notes.",
        "purpose": "design",
        "supported_request_types": ["ui/ux request", "software feature"],
        "allowed_tools": ["documentation_generation", "artifact_build"],
        "required_permissions": ["ai.read", "request.read"],
        "risk_class": "LOW",
        "approval_policy": "none",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 30,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "coding-agent",
        "name": "Coding Agent",
        "version": "1.0.0",
        "description": "Produces bounded code changes and diffs.",
        "purpose": "implementation",
        "supported_request_types": ["software feature", "bug fix", "api request", "database request"],
        "allowed_tools": ["repository_read", "repository_search", "file_read", "file_update", "code_diff", "artifact_build"],
        "required_permissions": ["ai.read", "ai.execute", "request.read", "project.read"],
        "risk_class": "MEDIUM",
        "approval_policy": "moderate",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 45,
        "maximum_retries": 2,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "testing-agent",
        "name": "Testing Agent",
        "version": "1.0.0",
        "description": "Creates and executes validation checks.",
        "purpose": "validation",
        "supported_request_types": ["testing request", "software feature", "bug fix"],
        "allowed_tools": ["test_run", "lint_run", "typecheck_run", "schema_validation"],
        "required_permissions": ["ai.read", "ai.execute", "request.read"],
        "risk_class": "LOW",
        "approval_policy": "none",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 45,
        "maximum_retries": 2,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "security-agent",
        "name": "Security Agent",
        "version": "1.0.0",
        "description": "Assesses identity, privacy, and security risk.",
        "purpose": "security",
        "supported_request_types": ["security request", "deployment request", "compliance request", "software feature"],
        "allowed_tools": ["security_scan", "policy_evaluation", "schema_validation"],
        "required_permissions": ["ai.read", "ai.execute", "policy.evaluate"],
        "risk_class": "HIGH",
        "approval_policy": "high",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 45,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "devops-agent",
        "name": "DevOps Agent",
        "version": "1.0.0",
        "description": "Plans build, deploy, rollback, and verification work.",
        "purpose": "delivery",
        "supported_request_types": ["deployment request", "software feature", "operations request"],
        "allowed_tools": ["artifact_build", "deployment_request", "test_run"],
        "required_permissions": ["ai.read", "ai.execute", "request.read"],
        "risk_class": "HIGH",
        "approval_policy": "high",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 45,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "data-agent",
        "name": "Data Agent",
        "version": "1.0.0",
        "description": "Inspects schemas, data flows, and reporting needs.",
        "purpose": "data",
        "supported_request_types": ["database request", "data analysis request"],
        "allowed_tools": ["repository_read", "repository_search", "schema_validation"],
        "required_permissions": ["ai.read", "request.read"],
        "risk_class": "MEDIUM",
        "approval_policy": "moderate",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 30,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "documentation-agent",
        "name": "Documentation Agent",
        "version": "1.0.0",
        "description": "Produces guides, changelogs, and operational notes.",
        "purpose": "documentation",
        "supported_request_types": ["documentation request", "software feature", "operations request"],
        "allowed_tools": ["documentation_generation", "repository_read"],
        "required_permissions": ["ai.read", "request.read"],
        "risk_class": "LOW",
        "approval_policy": "none",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 30,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "operations-agent",
        "name": "Operations Agent",
        "version": "1.0.0",
        "description": "Assesses incidents, incidents and operational readiness.",
        "purpose": "operations",
        "supported_request_types": ["operations request", "deployment request", "security request"],
        "allowed_tools": ["test_run", "security_scan", "deployment_request"],
        "required_permissions": ["ai.read", "request.read"],
        "risk_class": "HIGH",
        "approval_policy": "high",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 45,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
    {
        "agent_id": "compliance-agent",
        "name": "Compliance Agent",
        "version": "1.0.0",
        "description": "Evaluates policy and regulatory implications.",
        "purpose": "compliance",
        "supported_request_types": ["compliance request", "security request", "business process request"],
        "allowed_tools": ["policy_evaluation", "schema_validation", "documentation_generation"],
        "required_permissions": ["ai.read", "policy.evaluate", "request.read"],
        "risk_class": "HIGH",
        "approval_policy": "high",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "timeout_seconds": 45,
        "maximum_retries": 1,
        "model_configuration": {"provider": "deterministic-test", "model": "rules"},
        "evidence_policy": "required",
        "enabled": True,
        "tenant_scope": "*",
        "environment_scope": ["development", "test", "pilot"],
    },
]

TOOL_SEEDS: list[dict[str, Any]] = [
    {"tool_id": "repository_read", "version": "1.0.0", "description": "Read repository files and manifests.", "required_permission": "ai.read", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 30, "maximum_output_size": 20000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "repository_search", "version": "1.0.0", "description": "Search repository content.", "required_permission": "ai.read", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 30, "maximum_output_size": 20000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "file_read", "version": "1.0.0", "description": "Read a file.", "required_permission": "ai.read", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 20, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "file_create", "version": "1.0.0", "description": "Create a bounded file.", "required_permission": "ai.execute", "risk_level": "MEDIUM", "allowed_environments": ["development", "test", "pilot"], "requires_approval": True, "timeout": 20, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "file_update", "version": "1.0.0", "description": "Update a bounded file.", "required_permission": "ai.execute", "risk_level": "MEDIUM", "allowed_environments": ["development", "test", "pilot"], "requires_approval": True, "timeout": 20, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "code_diff", "version": "1.0.0", "description": "Produce a code diff.", "required_permission": "ai.execute", "risk_level": "MEDIUM", "allowed_environments": ["development", "test", "pilot"], "requires_approval": True, "timeout": 30, "maximum_output_size": 16000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "test_run", "version": "1.0.0", "description": "Run deterministic tests.", "required_permission": "ai.execute", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 60, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "lint_run", "version": "1.0.0", "description": "Run linters.", "required_permission": "ai.execute", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 60, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "typecheck_run", "version": "1.0.0", "description": "Run type checks.", "required_permission": "ai.execute", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 60, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "security_scan", "version": "1.0.0", "description": "Run a security scan.", "required_permission": "policy.evaluate", "risk_level": "HIGH", "allowed_environments": ["development", "test", "pilot"], "requires_approval": True, "timeout": 90, "maximum_output_size": 16000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "policy_evaluation", "version": "1.0.0", "description": "Evaluate a request against policy.", "required_permission": "policy.evaluate", "risk_level": "HIGH", "allowed_environments": ["development", "test", "pilot"], "requires_approval": True, "timeout": 45, "maximum_output_size": 16000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "schema_validation", "version": "1.0.0", "description": "Validate a schema or contract.", "required_permission": "ai.read", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 30, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "documentation_generation", "version": "1.0.0", "description": "Generate documentation artifacts.", "required_permission": "ai.execute", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 30, "maximum_output_size": 16000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "architecture_generation", "version": "1.0.0", "description": "Generate architecture notes and diagrams.", "required_permission": "ai.execute", "risk_level": "MEDIUM", "allowed_environments": ["development", "test", "pilot"], "requires_approval": True, "timeout": 30, "maximum_output_size": 16000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "project_task_creation", "version": "1.0.0", "description": "Create project tasks.", "required_permission": "project.create", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 20, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "requirement_creation", "version": "1.0.0", "description": "Create requirements records.", "required_permission": "request.create", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 20, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "evidence_write", "version": "1.0.0", "description": "Persist evidence records.", "required_permission": "ai.execute", "risk_level": "LOW", "allowed_environments": ["development", "test", "pilot"], "requires_approval": False, "timeout": 20, "maximum_output_size": 12000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "artifact_build", "version": "1.0.0", "description": "Build controlled artifacts.", "required_permission": "ai.execute", "risk_level": "MEDIUM", "allowed_environments": ["development", "test", "pilot"], "requires_approval": True, "timeout": 60, "maximum_output_size": 16000, "audit_policy": "full", "evidence_policy": "required"},
    {"tool_id": "deployment_request", "version": "1.0.0", "description": "Request a controlled deployment.", "required_permission": "ai.execute", "risk_level": "HIGH", "allowed_environments": ["development", "test", "pilot"], "requires_approval": True, "timeout": 60, "maximum_output_size": 16000, "audit_policy": "full", "evidence_policy": "required"},
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _upper(value: Any) -> str:
    return str(value or "").strip().upper()


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
      return list(value)
    if isinstance(value, tuple):
      return list(value)
    if value is None:
      return []
    return [value]


@dataclass(frozen=True)
class NCP004ExecutionContext:
    execution_id: str
    actor_id: str
    tenant_id: str
    organization_id: str
    workspace_id: str
    project_id: str | None
    request_id: str | None
    role: str
    permissions: tuple[str, ...]
    environment: str
    session_id: str | None
    correlation_id: str
    causation_id: str | None = None
    approval_references: tuple[str, ...] = ()


class NCP004Error(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, *, details: dict[str, Any] | None = None, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.retryable = retryable


class DeterministicModelProvider:
    def __init__(self, *, provider: str = "deterministic-test", model: str = "rules") -> None:
        self.provider = provider
        self.model = model

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider, "model": self.model, "status": "healthy"}

    def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        digest = _stable_digest({"prompt": prompt, "context": context or {}, "model": self.model})
        return {
            "provider": self.provider,
            "model": self.model,
            "output": f"Deterministic output for {prompt[:120]}",
            "digest": digest,
        }

    def stream(self, prompt: str, *, context: dict[str, Any] | None = None):
        yield self.generate(prompt, context=context)

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [round(byte / 255.0, 6) for byte in digest[:8]]

    def usage(self) -> dict[str, Any]:
        return {"provider": self.provider, "model": self.model, "tokens": 0}

    def cancel(self, execution_id: str) -> dict[str, Any]:
        return {"execution_id": execution_id, "status": "cancelled"}


def _default_agent_registry() -> list[dict[str, Any]]:
    return [dict(item) for item in AGENT_SEEDS]


def _default_tool_registry() -> list[dict[str, Any]]:
    return [dict(item) for item in TOOL_SEEDS]


class NovaCodeProNCP004Service:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository
        self._seed_registry()

    def _seed_registry(self) -> None:
        for agent in _default_agent_registry():
            existing = self.repository.get("ai_agent", agent["agent_id"])
            if not existing:
                self.repository.upsert("ai_agent", {
                    **agent,
                    "id": agent["agent_id"],
                    "created_at": _utc_now(),
                    "updated_at": _utc_now(),
                    "versions": [self._agent_version_payload(agent, created_at=_utc_now())],
                })
        for tool in _default_tool_registry():
            existing = self.repository.get("ai_tool", tool["tool_id"])
            if not existing:
                self.repository.upsert("ai_tool", {
                    **tool,
                    "id": tool["tool_id"],
                    "created_at": _utc_now(),
                    "updated_at": _utc_now(),
                })

    def _agent_version_payload(self, agent: dict[str, Any], *, created_at: str | None = None) -> dict[str, Any]:
        created = created_at or _utc_now()
        version = {
            "id": f"{agent['agent_id']}:{agent['version']}",
            "agent_id": agent["agent_id"],
            "version": agent["version"],
            "description": agent["description"],
            "purpose": agent["purpose"],
            "supported_request_types": list(agent["supported_request_types"]),
            "allowed_tools": list(agent["allowed_tools"]),
            "required_permissions": list(agent["required_permissions"]),
            "risk_class": agent["risk_class"],
            "approval_policy": agent["approval_policy"],
            "input_schema": dict(agent["input_schema"]),
            "output_schema": dict(agent["output_schema"]),
            "timeout_seconds": agent["timeout_seconds"],
            "maximum_retries": agent["maximum_retries"],
            "model_configuration": dict(agent["model_configuration"]),
            "evidence_policy": agent["evidence_policy"],
            "enabled": bool(agent["enabled"]),
            "tenant_scope": agent["tenant_scope"],
            "environment_scope": list(agent["environment_scope"]),
            "created_at": created,
            "updated_at": created,
        }
        return version

    def _record_event(self, *, event_type: str, ctx: NCP004ExecutionContext, execution_id: str | None = None, plan_id: str | None = None, step_id: str | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
        event = _event_envelope(
            event_type=event_type,
            actor_type="user",
            actor_id=ctx.actor_id,
            tenant_id=ctx.tenant_id,
            organization_id=ctx.organization_id,
            project_id=ctx.project_id,
            workflow_id=ctx.request_id or execution_id,
            correlation_id=ctx.correlation_id,
            causation_id=ctx.causation_id or ctx.correlation_id,
            data={
                **(data or {}),
                "execution_id": execution_id,
                "plan_id": plan_id,
                "step_id": step_id,
            },
            metadata={"environment": ctx.environment, "workspace_id": ctx.workspace_id},
        )
        self.repository.append_event(event)
        return event

    def _seed_record(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.repository.upsert(kind, payload)
        return payload

    def _admin_override(self, ctx: NCP004ExecutionContext) -> bool:
        return ctx.role in ADMIN_ROLES or any(permission in ctx.permissions for permission in ("ai.manage", "platform.manage"))

    def _ensure_permission(self, ctx: NCP004ExecutionContext, permission: str) -> None:
        if permission in ctx.permissions or self._admin_override(ctx):
            return
        raise NCP004Error("ai_execution_forbidden", "You do not have permission to perform this action.", 403)

    def _ensure_scope(self, record: dict[str, Any], ctx: NCP004ExecutionContext, *, code: str) -> None:
        record_tenant = str(record.get("tenant_id") or record.get("tenant_scope") or "").lower()
        if record_tenant and record_tenant not in {"*", ctx.tenant_id}:
            raise NCP004Error("cross_tenant_execution_forbidden", "Cross-tenant access is forbidden.", 403)
        if ctx.workspace_id and str(record.get("workspace_id") or "") not in {"", ctx.workspace_id}:
            raise NCP004Error(code, "Workspace scope mismatch.", 403)

    def _execution_or_404(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        record = self.repository.get("ai_execution", execution_id)
        if not record:
            raise NCP004Error("ai_execution_not_found", "Execution not found.", 404)
        self._ensure_scope(record, ctx, code="ai_execution_forbidden")
        return record

    def _agent_or_404(self, agent_id: str, ctx: NCP004ExecutionContext | None = None) -> dict[str, Any]:
        record = self.repository.get("ai_agent", agent_id)
        if not record:
            raise NCP004Error("agent_not_found", "Agent not found.", 404)
        if ctx:
            self._ensure_scope(record, ctx, code="ai_execution_forbidden")
        return record

    def _tool_or_404(self, tool_id: str, ctx: NCP004ExecutionContext | None = None) -> dict[str, Any]:
        record = self.repository.get("ai_tool", tool_id)
        if not record:
            raise NCP004Error("tool_not_found", "Tool not found.", 404)
        if ctx:
            self._ensure_scope(record, ctx, code="ai_execution_forbidden")
        return record

    def _current_provider(self) -> DeterministicModelProvider | None:
        provider = _lower(os.environ.get("NOVACODEPRO_AI_PROVIDER") or "deterministic-test")
        if provider in {"deterministic-test", "deterministic", "test"}:
            return DeterministicModelProvider(provider=provider, model=os.environ.get("NOVACODEPRO_AI_MODEL", "rules"))
        endpoint = os.environ.get("NOVACODEPRO_AI_ENDPOINT")
        credential = os.environ.get("NOVACODEPRO_AI_CREDENTIAL")
        if not endpoint or not credential:
            return None
        return DeterministicModelProvider(provider=provider, model=os.environ.get("NOVACODEPRO_AI_MODEL", "remote-fallback"))

    def _attach_timeline(self, execution: dict[str, Any], event_type: str, ctx: NCP004ExecutionContext, *, status: str | None = None, summary: str | None = None, detail: dict[str, Any] | None = None, evidence_reference: str | None = None) -> dict[str, Any]:
        timeline = list(execution.get("timeline") or [])
        item = {
            "id": _new_id("ai-timeline"),
            "event_type": event_type,
            "timestamp": _utc_now(),
            "actor_id": ctx.actor_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": execution.get("project_id"),
            "request_id": execution.get("request_id"),
            "execution_id": execution["id"],
            "plan_id": execution.get("plan_id"),
            "step_id": detail.get("step_id") if detail else None,
            "status": status or execution.get("status"),
            "summary": summary or event_type,
            "detail": detail or {},
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "evidence_reference": evidence_reference or execution.get("evidence_reference") or "",
        }
        timeline.append(item)
        execution["timeline"] = timeline
        execution["updated_at"] = _utc_now()
        execution["version"] = int(execution.get("version") or 1) + 1
        self.repository.upsert("ai_execution", execution)
        self._record_event(event_type=event_type, ctx=ctx, execution_id=execution["id"], plan_id=execution.get("plan_id"), data=item)
        return execution

    def _transition(self, execution: dict[str, Any], next_state: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        current = _upper(execution.get("status") or "RECEIVED")
        if current == next_state:
            return execution
        allowed = {
            "RECEIVED": {"CLASSIFYING", "CANCELLED"},
            "CLASSIFYING": {"CLARIFICATION_REQUIRED", "CONTEXT_RETRIEVAL"},
            "CLARIFICATION_REQUIRED": {"CONTEXT_RETRIEVAL", "CANCELLED"},
            "CONTEXT_RETRIEVAL": {"REQUIREMENTS_GENERATION", "FAILED"},
            "REQUIREMENTS_GENERATION": {"PLANNING", "FAILED"},
            "PLANNING": {"RISK_REVIEW", "POLICY_REVIEW", "APPROVAL_REQUIRED", "FAILED"},
            "RISK_REVIEW": {"POLICY_REVIEW", "APPROVAL_REQUIRED", "FAILED"},
            "POLICY_REVIEW": {"APPROVAL_REQUIRED", "APPROVED", "FAILED"},
            "APPROVAL_REQUIRED": {"APPROVED", "REJECTED", "FAILED"},
            "APPROVED": {"EXECUTING", "FAILED"},
            "EXECUTING": {"VERIFYING", "FAILED", "TIMED_OUT", "ROLLED_BACK"},
            "VERIFYING": {"COMPLETED", "FAILED"},
            "COMPLETED": {"ARCHIVED"},
            "FAILED": {"ROLLED_BACK", "ARCHIVED"},
            "CANCELLED": {"ARCHIVED"},
            "TIMED_OUT": {"ROLLED_BACK", "ARCHIVED"},
            "ROLLED_BACK": {"ARCHIVED"},
            "ARCHIVED": set(),
        }
        if next_state not in allowed.get(current, set()):
            raise NCP004Error("invalid_execution_transition", f"Cannot transition execution from {current} to {next_state}.", 409)
        execution["status"] = next_state
        execution["updated_at"] = _utc_now()
        execution["version"] = int(execution.get("version") or 1) + 1
        self.repository.upsert("ai_execution", execution)
        self._attach_timeline(execution, f"ai.execution.{next_state.lower()}", ctx, status=next_state, summary=f"Execution moved to {next_state}")
        return execution

    def _score_risk(self, text: str, request_type: str, environment: str) -> tuple[str, dict[str, Any]]:
        normalized = text.lower()
        score = 0
        reasons: list[str] = []
        if any(term in normalized for term in ("production", "deploy", "release", "rollback", "kubernetes")):
            score += 2
            reasons.append("deployment-impact")
        if any(term in normalized for term in ("identity", "auth", "mfa", "security", "privacy")):
            score += 2
            reasons.append("identity-security-impact")
        if any(term in normalized for term in ("delete", "drop", "destroy", "wipe")):
            score += 3
            reasons.append("destructive-action")
        if any(term in normalized for term in ("payment", "financial", "money", "billing")):
            score += 3
            reasons.append("financial-impact")
        if request_type in {"security request", "compliance request", "deployment request"}:
            score += 1
            reasons.append("sensitive-request-type")
        if environment.lower() in {"production", "prod"}:
            score += 2
            reasons.append("production-environment")
        if score <= 1:
            risk = "LOW"
        elif score <= 3:
            risk = "MODERATE"
        elif score <= 5:
            risk = "HIGH"
        else:
            risk = "CRITICAL"
        return risk, {"score": score, "reasons": reasons}

    def _classify(self, request_text: str) -> dict[str, Any]:
        normalized = request_text.lower().strip()
        detected_domains = [name for name, keywords in REQUEST_KEYWORDS.items() if any(keyword in normalized for keyword in keywords)]
        if not detected_domains:
            detected_domains = ["software feature"]
        request_type = detected_domains[0]
        if "bug" in normalized or "fix" in normalized:
            request_type = "bug fix"
        if "security" in normalized or "identity" in normalized:
            request_type = "security request"
        confidence = 0.92
        missing_information = []
        ambiguities = []
        if not any(term in normalized for term in ("workspace", "project", "tenant", "organization")):
            missing_information.append("target_workspace")
        if not any(term in normalized for term in ("approval", "approved", "review", "signoff", "authority")):
            missing_information.append("approval_authority")
        if not any(term in normalized for term in ("test", "verify", "validation")):
            missing_information.append("verification_scope")
        if len(detected_domains) > 1:
            ambiguities.append("multi_domain_request")
            confidence -= 0.1
        if "maybe" in normalized or "should" in normalized:
            ambiguities.append("uncertain_outcome")
            confidence -= 0.05
        confidence = max(round(confidence, 2), 0.51)
        required_agents = self._select_agents(request_type, normalized)
        required_tools = self._select_tools(request_type, normalized)
        risk_class, risk_meta = self._score_risk(request_text, request_type, environment="development")
        return {
            "request_type": request_type,
            "confidence": confidence,
            "detected_domains": detected_domains,
            "required_agents": required_agents,
            "required_tools": required_tools,
            "risk_class": risk_class,
            "risk_meta": risk_meta,
            "ambiguities": ambiguities,
            "missing_information": missing_information,
            "suggested_workflow": ["analyse", "requirements", "plan", "policy", "approval", "execute", "verify", "evidence"],
        }

    def _select_agents(self, request_type: str, text: str) -> list[str]:
        candidates = ["business-analyst-agent", "product-manager-agent", "architecture-agent", "coding-agent", "testing-agent", "documentation-agent"]
        if request_type in {"security request", "compliance request"} or any(term in text for term in ("security", "identity", "privacy")):
            candidates.append("security-agent")
            candidates.append("compliance-agent")
        if request_type in {"deployment request", "operations request"} or any(term in text for term in ("deploy", "release", "rollback", "incident")):
            candidates.append("devops-agent")
            candidates.append("operations-agent")
        if request_type in {"database request", "data analysis request"}:
            candidates.append("data-agent")
        if request_type in {"ui/ux request"}:
            candidates.append("ui-ux-agent")
        return list(dict.fromkeys(candidates))

    def _select_tools(self, request_type: str, text: str) -> list[str]:
        tools = ["repository_read", "repository_search", "documentation_generation", "requirement_creation", "evidence_write"]
        if request_type in {"software feature", "bug fix", "api request", "database request"}:
            tools.extend(["file_update", "code_diff", "test_run"])
        if request_type in {"security request", "compliance request"} or any(term in text for term in ("security", "privacy", "identity")):
            tools.extend(["security_scan", "policy_evaluation"])
        if request_type in {"deployment request", "operations request"}:
            tools.extend(["artifact_build", "deployment_request"])
        if request_type in {"testing request"}:
            tools.extend(["lint_run", "typecheck_run", "schema_validation"])
        return list(dict.fromkeys(tools))

    def _context_snapshot(self, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        workspace = self.repository.get("workspace", ctx.workspace_id)
        project = self.repository.get("project", ctx.project_id) if ctx.project_id else None
        request = self.repository.get("request", ctx.request_id) if ctx.request_id else None
        return {"workspace": workspace, "project": project, "request": request}

    def _requirements_for(self, execution: dict[str, Any], classification: dict[str, Any]) -> list[dict[str, Any]]:
        text = _lower(execution.get("request_text") or execution.get("title") or "")
        reqs = [
            {"id": _new_id("ai-req"), "type": "business requirement", "summary": f"Deliver {execution.get('request_type')} outcome.", "confidence": classification["confidence"], "source_request_reference": execution["id"]},
            {"id": _new_id("ai-req"), "type": "functional requirement", "summary": f"Support {execution.get('request_type')} scenario for {execution.get('request_text')}", "confidence": classification["confidence"], "source_request_reference": execution["id"]},
            {"id": _new_id("ai-req"), "type": "non-functional requirement", "summary": "Meet tenant isolation, audit, and access control requirements.", "confidence": 0.98, "source_request_reference": execution["id"]},
            {"id": _new_id("ai-req"), "type": "acceptance criterion", "summary": "The approved flow can be executed end to end with evidence recorded.", "confidence": 0.94, "source_request_reference": execution["id"]},
        ]
        if "identity" in text or "security" in text:
            reqs.append({"id": _new_id("ai-req"), "type": "security requirement", "summary": "Identity and session state must be server-authoritative.", "confidence": 0.96, "source_request_reference": execution["id"]})
        if "deploy" in text or "release" in text:
            reqs.append({"id": _new_id("ai-req"), "type": "operational requirement", "summary": "Deployments must be approved, verifiable, and rollback capable.", "confidence": 0.95, "source_request_reference": execution["id"]})
        return reqs

    def _plan_for(self, execution: dict[str, Any], classification: dict[str, Any], requirements: list[dict[str, Any]]) -> dict[str, Any]:
        steps: list[dict[str, Any]] = []
        required_agents = classification["required_agents"]
        required_tools = classification["required_tools"]
        previous_step_ids: list[str] = []
        for index, agent_id in enumerate(required_agents, start=1):
            agent = self._agent_or_404(agent_id)
            tool_id = agent["allowed_tools"][0] if agent.get("allowed_tools") else required_tools[min(index - 1, len(required_tools) - 1)]
            step_id = f"{execution['id']}:step:{index}"
            step = {
                "id": step_id,
                "sequence": index,
                "agent_id": agent_id,
                "agent_version": agent["versions"][-1]["version"] if agent.get("versions") else agent["version"],
                "tool_id": tool_id,
                "description": f"{agent['name']} handles {execution.get('request_type')} work.",
                "dependencies": list(previous_step_ids),
                "expected_inputs": ["request", "requirements", "context"],
                "expected_outputs": ["artifact", "evidence"],
                "verification_criteria": ["schema valid", "permissions valid", "evidence recorded"],
                "rollback_action": "revert_artifacts",
                "risk_class": classification["risk_class"],
                "approval_requirements": ["moderate" if classification["risk_class"] == "MODERATE" else "high"] if classification["risk_class"] != "LOW" else [],
                "estimated_resource_usage": {"tokens": 1000 + index * 100, "minutes": 5 + index},
                "status": "DRAFT",
            }
            steps.append(step)
            previous_step_ids.append(step_id)
        return {
            "id": f"{execution['id']}:plan",
            "execution_id": execution["id"],
            "state": "GENERATED",
            "risk_class": classification["risk_class"],
            "requirements": [requirement["id"] for requirement in requirements],
            "steps": steps,
            "dependencies": [{"from": step["dependencies"][-1], "to": step["id"]} for step in steps if step["dependencies"]],
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "version": 1,
            "metadata": {"classification": classification, "digest": _stable_digest({"steps": steps, "execution_id": execution["id"]})},
        }

    def _approval_required_role(self, risk_class: str) -> str | tuple[str, ...]:
        if risk_class == "LOW":
            return "PRODUCT_MANAGER"
        if risk_class == "MODERATE":
            return "PRODUCT_MANAGER"
        if risk_class == "HIGH":
            return ("PLATFORM_ADMIN", "SECURITY_ENGINEER")
        return ("PLATFORM_ADMIN", "COMPLIANCE_OFFICER")

    def _require_workspace_and_permissions(self, ctx: NCP004ExecutionContext) -> None:
        if not ctx.workspace_id:
            raise NCP004Error("workspace_required", "Workspace context is required.", 409)
        if not ctx.tenant_id:
            raise NCP004Error("tenant_required", "Tenant context is required.", 409)

    def list_agents(self, ctx: NCP004ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "ai.read")
        agents = [agent for agent in self.repository.list("ai_agent") if str(agent.get("tenant_scope") or "*") in {"*", ctx.tenant_id}]
        return agents

    def get_agent(self, agent_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.read")
        return self._agent_or_404(agent_id, ctx)

    def create_agent(self, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.manage")
        agent_id = str(payload.get("agent_id") or payload.get("id") or _new_id("agent"))
        versions = list(payload.get("versions") or [])
        if not versions:
            versions.append({
                "id": f"{agent_id}:{payload.get('version') or '1.0.0'}",
                "version": str(payload.get("version") or "1.0.0"),
                "description": str(payload.get("description") or ""),
                "purpose": str(payload.get("purpose") or "general"),
                "supported_request_types": list(payload.get("supported_request_types") or []),
                "allowed_tools": list(payload.get("allowed_tools") or []),
                "required_permissions": list(payload.get("required_permissions") or []),
                "risk_class": str(payload.get("risk_class") or "LOW"),
                "approval_policy": str(payload.get("approval_policy") or "none"),
                "input_schema": dict(payload.get("input_schema") or {"type": "object"}),
                "output_schema": dict(payload.get("output_schema") or {"type": "object"}),
                "timeout_seconds": int(payload.get("timeout_seconds") or 30),
                "maximum_retries": int(payload.get("maximum_retries") or 1),
                "model_configuration": dict(payload.get("model_configuration") or {"provider": "deterministic-test"}),
                "evidence_policy": str(payload.get("evidence_policy") or "required"),
                "enabled": bool(payload.get("enabled", True)),
                "tenant_scope": str(payload.get("tenant_scope") or ctx.tenant_id),
                "environment_scope": list(payload.get("environment_scope") or [ctx.environment]),
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
            })
        record = {
            "id": agent_id,
            "agent_id": agent_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "status": "ACTIVE",
            "metadata": dict(payload.get("metadata") or {}),
            "versions": versions,
            "active_version": versions[-1]["version"],
            "enabled": bool(payload.get("enabled", True)),
        }
        return self.repository.upsert("ai_agent", record)

    def patch_agent(self, agent_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.manage")
        agent = self._agent_or_404(agent_id, ctx)
        agent.update({key: value for key, value in payload.items() if key not in {"id", "agent_id", "versions"}})
        agent["updated_at"] = _utc_now()
        agent["updated_by"] = ctx.actor_id
        return self.repository.upsert("ai_agent", agent)

    def add_agent_version(self, agent_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.manage")
        agent = self._agent_or_404(agent_id, ctx)
        version = self._agent_version_payload({
            "agent_id": agent_id,
            "version": str(payload.get("version") or time.strftime("%Y.%m.%d")),
            "description": str(payload.get("description") or agent.get("description") or ""),
            "purpose": str(payload.get("purpose") or agent.get("purpose") or "general"),
            "supported_request_types": list(payload.get("supported_request_types") or agent.get("supported_request_types") or []),
            "allowed_tools": list(payload.get("allowed_tools") or agent.get("allowed_tools") or []),
            "required_permissions": list(payload.get("required_permissions") or agent.get("required_permissions") or []),
            "risk_class": str(payload.get("risk_class") or agent.get("risk_class") or "LOW"),
            "approval_policy": str(payload.get("approval_policy") or agent.get("approval_policy") or "none"),
            "input_schema": dict(payload.get("input_schema") or agent.get("input_schema") or {"type": "object"}),
            "output_schema": dict(payload.get("output_schema") or agent.get("output_schema") or {"type": "object"}),
            "timeout_seconds": int(payload.get("timeout_seconds") or agent.get("timeout_seconds") or 30),
            "maximum_retries": int(payload.get("maximum_retries") or agent.get("maximum_retries") or 1),
            "model_configuration": dict(payload.get("model_configuration") or agent.get("model_configuration") or {"provider": "deterministic-test"}),
            "evidence_policy": str(payload.get("evidence_policy") or agent.get("evidence_policy") or "required"),
            "enabled": bool(payload.get("enabled", True)),
            "tenant_scope": str(payload.get("tenant_scope") or agent.get("tenant_scope") or ctx.tenant_id),
            "environment_scope": list(payload.get("environment_scope") or agent.get("environment_scope") or [ctx.environment]),
        })
        agent_versions = list(agent.get("versions") or [])
        agent_versions.append(version)
        agent["versions"] = agent_versions
        agent["active_version"] = version["version"]
        agent["updated_at"] = _utc_now()
        agent["updated_by"] = ctx.actor_id
        return self.repository.upsert("ai_agent", agent)

    def enable_agent(self, agent_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        agent = self.patch_agent(agent_id, {"enabled": True}, ctx)
        agent["enabled"] = True
        return self.repository.upsert("ai_agent", agent)

    def disable_agent(self, agent_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        agent = self.patch_agent(agent_id, {"enabled": False}, ctx)
        agent["enabled"] = False
        return self.repository.upsert("ai_agent", agent)

    def list_tools(self, ctx: NCP004ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "ai.read")
        return [tool for tool in self.repository.list("ai_tool")]

    def get_tool(self, tool_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.read")
        return self._tool_or_404(tool_id, ctx)

    def enable_tool(self, tool_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.manage")
        tool = self._tool_or_404(tool_id, ctx)
        tool["enabled"] = True
        tool["updated_at"] = _utc_now()
        return self.repository.upsert("ai_tool", tool)

    def disable_tool(self, tool_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.manage")
        tool = self._tool_or_404(tool_id, ctx)
        tool["enabled"] = False
        tool["updated_at"] = _utc_now()
        return self.repository.upsert("ai_tool", tool)

    def create_execution(self, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._require_workspace_and_permissions(ctx)
        self._ensure_permission(ctx, "ai.request")
        idempotency_key = str(payload.get("idempotency_key") or "").strip()
        if idempotency_key:
            existing = [
                item
                for item in self.repository.list("ai_idempotency")
                if str(item.get("tenant_id")) == ctx.tenant_id
                and str(item.get("workspace_id")) == ctx.workspace_id
                and str(item.get("idempotency_key")) == idempotency_key
            ]
            if existing:
                return self._execution_or_404(str(existing[0]["execution_id"]), ctx)
        request_text = str(payload.get("request_text") or payload.get("request") or payload.get("title") or payload.get("prompt") or "").strip()
        if not request_text:
            raise NCP004Error("validation_failed", "Request text is required.", 400)
        request_id = str(payload.get("request_id") or ctx.request_id or _new_id("request"))
        if payload.get("workspace_id") and str(payload["workspace_id"]) != ctx.workspace_id:
            raise NCP004Error("cross_tenant_execution_forbidden", "Workspace mismatch.", 403)
        project_id = str(payload.get("project_id") or ctx.project_id or "")
        if project_id:
            project = self.repository.get("project", project_id)
            if not project:
                raise NCP004Error("project_not_found", "Project not found.", 404)
            self._ensure_scope(project, ctx, code="ai_execution_forbidden")
            if project.get("status") == "ARCHIVED":
                raise NCP004Error("project_archived", "Project is archived.", 409)
        request_record = self.repository.get("request", request_id)
        if request_record:
            self._ensure_scope(request_record, ctx, code="request_forbidden")
        classification = self._classify(request_text)
        risk_class = classification["risk_class"]
        execution = {
            "id": str(payload.get("execution_id") or _new_id("ai-execution")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": project_id or (request_record.get("project_id") if request_record else None),
            "request_id": request_id,
            "request_text": request_text,
            "actor_id": ctx.actor_id,
            "session_id": ctx.session_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "version": 1,
            "status": "RECEIVED",
            "metadata": dict(payload.get("metadata") or {}),
            "environment": ctx.environment,
            "role": ctx.role,
            "permissions": list(ctx.permissions),
            "risk_class": risk_class,
            "classification": {},
            "requirements": [],
            "plan_id": "",
            "plan": {},
            "approval_id": "",
            "policy_decision": "",
            "agent_executions": [],
            "tool_executions": [],
            "clarifications": [],
            "timeline": [],
            "evidence": [],
            "verification": {},
            "replay": {},
            "failure_reason": "",
            "retry_count": 0,
            "model_configuration": {
                "provider": os.environ.get("NOVACODEPRO_AI_PROVIDER", "deterministic-test"),
                "model": os.environ.get("NOVACODEPRO_AI_MODEL", "rules"),
            },
            "provider_status": "AVAILABLE",
        }
        self.repository.upsert("ai_execution", execution)
        if idempotency_key:
            self.repository.upsert(
                "ai_idempotency",
                {
                    "id": _new_id("ai-idempotency"),
                    "idempotency_key": idempotency_key,
                    "tenant_id": ctx.tenant_id,
                    "organization_id": ctx.organization_id,
                    "workspace_id": ctx.workspace_id,
                    "execution_id": execution["id"],
                    "resource_kind": "ai_execution",
                    "resource_id": execution["id"],
                    "created_at": _utc_now(),
                    "updated_at": _utc_now(),
                    "version": 1,
                    "status": "LOCKED",
                    "metadata": {"request_digest": _stable_digest({"request_text": request_text, "project_id": project_id, "request_id": request_id})},
                },
            )
        self._record_event(event_type="ai.execution.created", ctx=ctx, execution_id=execution["id"], data={"request_text": request_text, "risk_class": risk_class})
        self._attach_timeline(execution, "ai.execution.created", ctx, status="RECEIVED", summary="Execution created", detail={"request_text": request_text})
        return execution

    def list_executions(self, ctx: NCP004ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "ai.read")
        items = []
        for execution in self.repository.list("ai_execution"):
            if str(execution.get("tenant_id")) != ctx.tenant_id:
                continue
            if ctx.workspace_id and str(execution.get("workspace_id") or "") != ctx.workspace_id:
                continue
            items.append(execution)
        return items

    def get_execution(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.read")
        return self._execution_or_404(execution_id, ctx)

    def analyse_execution(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.request")
        execution = self._execution_or_404(execution_id, ctx)
        if _upper(execution.get("status")) not in {"RECEIVED", "CLARIFICATION_REQUIRED"}:
            raise NCP004Error("invalid_execution_transition", "Execution is not ready for analysis.", 409)
        self._transition(execution, "CLASSIFYING", ctx)
        classification = self._classify(str(execution.get("request_text") or ""))
        execution["classification"] = classification
        execution["request_type"] = classification["request_type"]
        execution["risk_class"] = classification["risk_class"]
        execution["detected_domains"] = classification["detected_domains"]
        execution["required_agents"] = classification["required_agents"]
        execution["required_tools"] = classification["required_tools"]
        execution["ambiguities"] = classification["ambiguities"]
        execution["missing_information"] = classification["missing_information"]
        execution["suggested_workflow"] = classification["suggested_workflow"]
        execution["updated_at"] = _utc_now()
        execution["version"] = int(execution.get("version") or 1) + 1
        self.repository.upsert("ai_execution", execution)
        if classification["ambiguities"] or classification["missing_information"]:
            execution = self._transition(execution, "CLARIFICATION_REQUIRED", ctx)
            missing = list(classification["missing_information"] or ["approval_authority"])
            question = "Please clarify " + ", ".join(item.replace("_", " ") for item in missing) + "."
            clarification = {
                "id": _new_id("ai-clarification"),
                "execution_id": execution["id"],
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": execution.get("project_id"),
                "request_id": execution.get("request_id"),
                "question": question,
                "why": f"The execution needs {', '.join(item.replace('_', ' ') for item in missing)} before continuing.",
                "answer_schema": {"type": "string"},
                "answer": "",
                "status": "OPEN",
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
                "created_by": ctx.actor_id,
                "updated_by": ctx.actor_id,
                "version": 1,
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "metadata": {"missing_information": missing},
            }
            self.repository.upsert("ai_clarification", clarification)
            clarifications = [clarification]
            execution["clarifications"] = clarifications
            self.repository.upsert("ai_execution", execution)
            self._attach_timeline(execution, "ai.execution.clarification_required", ctx, status="CLARIFICATION_REQUIRED", summary="Clarification required", detail={"questions": [item["question"] for item in clarifications]})
            return {"execution": execution, "analysis": classification, "clarifications": clarifications}
        context_snapshot = self._context_snapshot(ctx)
        execution["context_snapshot"] = context_snapshot
        execution = self._transition(execution, "CONTEXT_RETRIEVAL", ctx)
        self.repository.upsert("ai_execution", execution)
        self._attach_timeline(execution, "ai.execution.context_retrieved", ctx, status="CONTEXT_RETRIEVAL", summary="Context retrieved", detail={"context": context_snapshot})
        return {"execution": execution, "analysis": classification, "context": context_snapshot}

    def list_clarifications(self, execution_id: str, ctx: NCP004ExecutionContext) -> list[dict[str, Any]]:
        execution = self._execution_or_404(execution_id, ctx)
        return [item for item in self.repository.list("ai_clarification") if str(item.get("execution_id")) == execution["id"]]

    def answer_clarification(self, execution_id: str, clarification_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.request")
        execution = self._execution_or_404(execution_id, ctx)
        clarification = self.repository.get("ai_clarification", clarification_id)
        if not clarification or str(clarification.get("execution_id")) != execution["id"]:
            raise NCP004Error("clarification_required", "Clarification not found.", 404)
        clarification["answer"] = str(payload.get("answer") or payload.get("value") or "")
        clarification["status"] = "ANSWERED"
        clarification["updated_at"] = _utc_now()
        clarification["updated_by"] = ctx.actor_id
        self.repository.upsert("ai_clarification", clarification)
        execution["clarifications"] = [item for item in self.list_clarifications(execution_id, ctx)]
        execution["updated_at"] = _utc_now()
        execution["version"] = int(execution.get("version") or 1) + 1
        self.repository.upsert("ai_execution", execution)
        self._attach_timeline(execution, "ai.clarification.answered", ctx, summary="Clarification answered", detail={"clarification_id": clarification_id})
        return clarification

    def complete_clarifications(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        clarifications = self.list_clarifications(execution_id, ctx)
        if any(item.get("status") != "ANSWERED" for item in clarifications):
            raise NCP004Error("clarification_required", "Required clarifications are still open.", 409)
        if _upper(execution.get("status")) == "CLARIFICATION_REQUIRED":
            execution = self._transition(execution, "CONTEXT_RETRIEVAL", ctx)
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_execution", execution)
        self._attach_timeline(execution, "ai.execution.clarifications_complete", ctx, status="CONTEXT_RETRIEVAL", summary="Clarifications complete")
        return execution

    def generate_requirements(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.execute")
        execution = self._execution_or_404(execution_id, ctx)
        status = _upper(execution.get("status"))
        if status == "CLARIFICATION_REQUIRED":
            raise NCP004Error("clarification_required", "Clarifications must be answered before requirements generation.", 409)
        if status not in {"CONTEXT_RETRIEVAL", "REQUIREMENTS_GENERATION", "PLANNING", "POLICY_REVIEW", "APPROVAL_REQUIRED", "APPROVED"}:
            raise NCP004Error("requirements_not_generated", "Execution is not ready for requirements generation.", 409)
        execution = self._transition(execution, "REQUIREMENTS_GENERATION", ctx)
        classification = execution.get("classification") or self._classify(str(execution.get("request_text") or ""))
        requirements = self._requirements_for(execution, classification)
        execution["requirements"] = requirements
        execution["requirement_digest"] = _stable_digest({"requirements": requirements, "execution_id": execution["id"]})
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_execution", execution)
        for requirement in requirements:
            self.repository.upsert("ai_requirement", {
                **requirement,
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": execution.get("project_id"),
                "request_id": execution.get("request_id"),
                "actor_id": ctx.actor_id,
                "session_id": ctx.session_id,
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
                "version": 1,
                "status": "GENERATED",
                "metadata": {"source_request_reference": execution["id"]},
            })
        self._attach_timeline(execution, "ai.requirements.generated", ctx, status="REQUIREMENTS_GENERATION", summary="Requirements generated", detail={"count": len(requirements)})
        return {"execution": execution, "requirements": requirements}

    def generate_plan(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.execute")
        execution = self._execution_or_404(execution_id, ctx)
        if not execution.get("requirements"):
            raise NCP004Error("plan_not_generated", "Requirements must be generated before planning.", 409)
        execution = self._transition(execution, "PLANNING", ctx)
        classification = execution.get("classification") or self._classify(str(execution.get("request_text") or ""))
        plan = self._plan_for(execution, classification, list(execution.get("requirements") or []))
        self._validate_plan(plan, execution, ctx)
        execution["plan_id"] = plan["id"]
        execution["plan"] = plan
        execution["plan_digest"] = plan["metadata"]["digest"]
        execution["risk_class"] = classification["risk_class"]
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_execution", execution)
        self.repository.upsert("ai_plan", {
            **plan,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": execution.get("project_id"),
            "request_id": execution.get("request_id"),
            "actor_id": ctx.actor_id,
            "session_id": ctx.session_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "status": "GENERATED",
            "version": 1,
        })
        for step in plan["steps"]:
            self.repository.upsert("ai_plan_step", {
                **step,
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": execution.get("project_id"),
                "request_id": execution.get("request_id"),
                "actor_id": ctx.actor_id,
                "session_id": ctx.session_id,
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "plan_id": plan["id"],
                "status": "GENERATED",
                "version": 1,
            })
        self._attach_timeline(execution, "ai.plan.generated", ctx, status="PLANNING", summary="Plan generated", detail={"plan_id": plan["id"], "step_count": len(plan["steps"])})
        execution = self._transition(execution, "RISK_REVIEW", ctx)
        return {"execution": execution, "plan": plan}

    def _validate_plan(self, plan: dict[str, Any], execution: dict[str, Any], ctx: NCP004ExecutionContext) -> None:
        step_ids = {step["id"] for step in plan["steps"]}
        if len(step_ids) != len(plan["steps"]):
            raise NCP004Error("plan_invalid", "Plan step identifiers must be unique.", 400)
        for step in plan["steps"]:
            agent = self._agent_or_404(step["agent_id"], ctx)
            if not agent.get("enabled", True):
                raise NCP004Error("agent_disabled", f"Agent {step['agent_id']} is disabled.", 409)
            if step["tool_id"] not in agent.get("versions", [{}])[-1].get("allowed_tools", agent.get("allowed_tools", [])):
                raise NCP004Error("agent_permission_denied", "Agent is not allowed to use the selected tool.", 403)
            tool = self._tool_or_404(step["tool_id"], ctx)
            if not tool.get("enabled", True):
                raise NCP004Error("tool_disabled", f"Tool {step['tool_id']} is disabled.", 409)
        for step in plan["steps"]:
            for dependency in step.get("dependencies") or []:
                if dependency not in step_ids:
                    raise NCP004Error("plan_invalid", "Plan dependency is missing.", 400)
        order = [step["id"] for step in plan["steps"]]
        if len(order) != len(set(order)):
            raise NCP004Error("plan_invalid", "Plan contains duplicate steps.", 400)

    def validate_plan(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        plan = execution.get("plan")
        if not plan:
            raise NCP004Error("plan_not_generated", "Plan has not been generated.", 409)
        self._validate_plan(plan, execution, ctx)
        plan["state"] = "VALIDATING"
        self.repository.upsert("ai_plan", plan)
        self._attach_timeline(execution, "ai.plan.validated", ctx, status=_upper(execution.get("status")), summary="Plan validated")
        return {"plan": plan}

    def request_approval(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.approve")
        execution = self._execution_or_404(execution_id, ctx)
        plan = execution.get("plan")
        if not plan:
            raise NCP004Error("plan_not_generated", "Plan not generated.", 409)
        risk_class = _upper(execution.get("risk_class") or plan.get("risk_class") or "MODERATE")
        required_role = self._approval_required_role(risk_class)
        approval = {
            "id": _new_id("ai-approval"),
            "execution_id": execution["id"],
            "plan_id": execution.get("plan_id"),
            "step_id": "",
            "requested_from": ",".join(required_role) if isinstance(required_role, tuple) else required_role,
            "requested_by": ctx.actor_id,
            "required_role": ",".join(required_role) if isinstance(required_role, tuple) else required_role,
            "risk_class": risk_class,
            "decision": "PENDING",
            "reason": "",
            "conditions": [],
            "created_at": _utc_now(),
            "decided_at": "",
            "expires_at": "",
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": execution.get("project_id"),
            "request_id": execution.get("request_id"),
            "actor_id": ctx.actor_id,
            "session_id": ctx.session_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "status": "OPEN",
            "metadata": {"plan_digest": execution.get("plan_digest")},
        }
        self.repository.upsert("ai_approval", approval)
        execution["approval_id"] = approval["id"]
        execution["approval_state"] = "APPROVAL_REQUIRED"
        execution = self._transition(execution, "APPROVAL_REQUIRED", ctx)
        self._attach_timeline(execution, "ai.approval.requested", ctx, status="APPROVAL_REQUIRED", summary="Approval requested", detail={"approval_id": approval["id"], "required_role": approval["required_role"]})
        self.create_notifier_snapshot(execution, ctx)
        return {"execution": execution, "approval": approval}

    def list_approvals(self, ctx: NCP004ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "ai.read")
        return [approval for approval in self.repository.list("ai_approval") if str(approval.get("tenant_id")) == ctx.tenant_id and (not ctx.workspace_id or str(approval.get("workspace_id")) == ctx.workspace_id)]

    def get_approval(self, approval_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.read")
        approval = self.repository.get("ai_approval", approval_id)
        if not approval:
            raise NCP004Error("approval_not_found", "Approval not found.", 404)
        self._ensure_scope(approval, ctx, code="approval_forbidden")
        return approval

    def approve(self, approval_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.approve")
        approval = self.get_approval(approval_id, ctx)
        if _upper(approval.get("status")) not in {"OPEN", "REQUESTED"}:
            raise NCP004Error("approval_expired", "Approval is not open.", 409)
        required_roles = {role.strip().upper() for role in str(approval.get("required_role") or "").split(",") if role.strip()}
        if required_roles and ctx.role not in required_roles and not self._admin_override(ctx):
            raise NCP004Error("approval_forbidden", "Your role cannot approve this execution.", 403)
        execution = self._execution_or_404(str(approval["execution_id"]), ctx)
        if execution.get("plan_digest") != approval.get("metadata", {}).get("plan_digest"):
            raise NCP004Error("plan_changed_after_approval", "The plan changed after approval was requested.", 409)
        decision = _upper(payload.get("decision") or "APPROVED")
        if decision not in {"APPROVED", "REJECTED", "CHANGES_REQUESTED"}:
            raise NCP004Error("validation_failed", "Unsupported approval decision.", 400)
        approval["decision"] = decision
        approval["reason"] = str(payload.get("reason") or "")
        approval["conditions"] = list(payload.get("conditions") or [])
        approval["decided_at"] = _utc_now()
        approval["status"] = decision
        approval["actor_id"] = ctx.actor_id
        approval["updated_at"] = _utc_now()
        approval["updated_by"] = ctx.actor_id
        self.repository.upsert("ai_approval", approval)
        if decision == "REJECTED":
            execution["policy_decision"] = "DENY"
            execution["approval_state"] = "REJECTED"
            execution = self._transition(execution, "FAILED", ctx)
            execution["failure_reason"] = "approval_rejected"
            self.repository.upsert("ai_execution", execution)
        elif decision == "CHANGES_REQUESTED":
            execution["approval_state"] = "CHANGES_REQUESTED"
            execution["updated_at"] = _utc_now()
            self.repository.upsert("ai_execution", execution)
        else:
            execution["approval_state"] = "APPROVED"
            execution = self._transition(execution, "APPROVED", ctx)
        self.create_notifier_snapshot(execution, ctx)
        self._attach_timeline(execution, f"ai.approval.{decision.lower()}", ctx, status=_upper(execution.get("status")), summary=f"Approval {decision.lower()}", detail={"approval_id": approval_id, "reason": approval["reason"]})
        return {"approval": approval, "execution": execution}

    def reject(self, approval_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        return self.approve(approval_id, {"decision": "REJECTED", "reason": payload.get("reason") or "Rejected"}, ctx)

    def request_changes(self, approval_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        return self.approve(approval_id, {"decision": "CHANGES_REQUESTED", "reason": payload.get("reason") or "Changes requested"}, ctx)

    def execute(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.execute")
        execution = self._execution_or_404(execution_id, ctx)
        if not execution.get("plan"):
            raise NCP004Error("plan_not_generated", "Plan is required before execution.", 409)
        if _upper(execution.get("approval_state")) != "APPROVED":
            raise NCP004Error("approval_required", "Approval is required before execution.", 409)
        provider = self._current_provider()
        if provider is None:
            execution["provider_status"] = "BLOCKED_EXTERNAL_VERIFICATION"
            execution["failure_reason"] = "model_provider_unavailable"
            execution = self._transition(execution, "FAILED", ctx)
            self.repository.upsert("ai_execution", execution)
            raise NCP004Error("model_provider_unavailable", "No model provider credential is available.", 503, retryable=False)
        execution = self._transition(execution, "EXECUTING", ctx)
        agent_executions: list[dict[str, Any]] = []
        tool_executions: list[dict[str, Any]] = []
        for step in list(execution["plan"]["steps"]):
            agent = self._agent_or_404(step["agent_id"], ctx)
            tool = self._tool_or_404(step["tool_id"], ctx)
            if not agent.get("enabled", True):
                raise NCP004Error("agent_disabled", "An execution agent is disabled.", 409)
            if not tool.get("enabled", True):
                raise NCP004Error("tool_disabled", "A required tool is disabled.", 409)
            agent_exec = {
                "id": _new_id("ai-agent-execution"),
                "execution_id": execution["id"],
                "plan_id": execution["plan_id"],
                "step_id": step["id"],
                "agent_id": agent["agent_id"],
                "agent_version": step["agent_version"],
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": execution.get("project_id"),
                "request_id": execution.get("request_id"),
                "actor_id": ctx.actor_id,
                "session_id": ctx.session_id,
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
                "version": 1,
                "status": "RUNNING",
                "metadata": {"risk_class": execution.get("risk_class")},
                "tool_id": tool["tool_id"],
                "output": {},
            }
            self.repository.upsert("ai_agent_execution", agent_exec)
            tool_output = provider.generate(
                f"{agent['name']} executes {step['description']}",
                context={"execution_id": execution["id"], "step_id": step["id"], "tool_id": tool["tool_id"]},
            )
            tool_exec = {
                "id": _new_id("ai-tool-execution"),
                "execution_id": execution["id"],
                "plan_id": execution["plan_id"],
                "step_id": step["id"],
                "tool_id": tool["tool_id"],
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": execution.get("project_id"),
                "request_id": execution.get("request_id"),
                "actor_id": ctx.actor_id,
                "session_id": ctx.session_id,
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
                "version": 1,
                "status": "SUCCEEDED",
                "metadata": {"provider": provider.provider, "model": provider.model, "digest": tool_output["digest"]},
                "input": {"prompt": step["description"]},
                "output": tool_output,
            }
            agent_exec["status"] = "SUCCEEDED"
            agent_exec["updated_at"] = _utc_now()
            agent_exec["output"] = tool_output
            self.repository.upsert("ai_agent_execution", agent_exec)
            self.repository.upsert("ai_tool_execution", tool_exec)
            agent_executions.append(agent_exec)
            tool_executions.append(tool_exec)
            self._attach_timeline(execution, "ai.agent.completed", ctx, status="EXECUTING", summary=f"{agent['name']} completed", detail={"step_id": step["id"], "tool_id": tool["tool_id"]}, evidence_reference=tool_exec["id"])
        execution["agent_executions"] = agent_executions
        execution["tool_executions"] = tool_executions
        execution["provider_status"] = provider.health()["status"].upper()
        execution["execution_digest"] = _stable_digest({"agents": agent_executions, "tools": tool_executions, "execution_id": execution["id"]})
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_execution", execution)
        self._attach_timeline(execution, "ai.execution.executed", ctx, status="VERIFYING", summary="Execution completed", detail={"agent_count": len(agent_executions), "tool_count": len(tool_executions)})
        execution = self._transition(execution, "VERIFYING", ctx)
        return execution

    def verify(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.read")
        execution = self._execution_or_404(execution_id, ctx)
        if _upper(execution.get("status")) not in {"VERIFYING", "EXECUTING", "APPROVED"}:
            raise NCP004Error("verification_failed", "Execution is not ready for verification.", 409)
        agent_executions = [item for item in self.repository.list("ai_agent_execution") if str(item.get("execution_id")) == execution["id"]]
        tool_executions = [item for item in self.repository.list("ai_tool_execution") if str(item.get("execution_id")) == execution["id"]]
        passed = bool(agent_executions) and len(agent_executions) == len(tool_executions) and all(item.get("status") == "SUCCEEDED" for item in agent_executions) and all(item.get("status") == "SUCCEEDED" for item in tool_executions)
        verification = {
            "id": _new_id("ai-verification"),
            "execution_id": execution["id"],
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": execution.get("project_id"),
            "request_id": execution.get("request_id"),
            "actor_id": ctx.actor_id,
            "session_id": ctx.session_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "version": 1,
            "status": "PASS" if passed else "FAIL",
            "result": "PASS" if passed else "FAIL",
            "details": {"agent_count": len(agent_executions), "tool_count": len(tool_executions)},
            "metadata": {"plan_digest": execution.get("plan_digest")},
        }
        self.repository.upsert("ai_verification", verification)
        execution["verification"] = verification
        execution["evidence"] = list(execution.get("evidence") or []) + [verification["id"]]
        if passed:
            execution = self._transition(execution, "COMPLETED", ctx)
            self._attach_timeline(execution, "ai.execution.completed", ctx, status="COMPLETED", summary="Execution verified", detail={"verification_id": verification["id"]}, evidence_reference=verification["id"])
        else:
            execution["failure_reason"] = "verification_failed"
            execution = self._transition(execution, "FAILED", ctx)
            self._attach_timeline(execution, "ai.execution.verification_failed", ctx, status="FAILED", summary="Verification failed", detail={"verification_id": verification["id"]}, evidence_reference=verification["id"])
            self.repository.upsert("ai_execution", execution)
            raise NCP004Error("verification_failed", "Verification failed.", 409)
        evidence = {
            "id": _new_id("ai-evidence"),
            "execution_id": execution["id"],
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": execution.get("project_id"),
            "request_id": execution.get("request_id"),
            "actor_id": ctx.actor_id,
            "session_id": ctx.session_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "version": 1,
            "status": "RECORDED",
            "artifact_refs": [verification["id"], execution.get("plan_id")],
            "input_digest": _stable_digest({"request_text": execution.get("request_text"), "context": execution.get("context_snapshot")}),
            "plan_digest": execution.get("plan_digest"),
            "output_digest": _stable_digest({"verification": verification, "agent_executions": agent_executions, "tool_executions": tool_executions}),
            "metadata": {"provider": execution.get("model_configuration", {}).get("provider", "deterministic-test")},
        }
        self.repository.upsert("ai_evidence", evidence)
        execution["evidence_reference"] = evidence["id"]
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_execution", execution)
        self.create_notifier_snapshot(execution, ctx)
        self._attach_timeline(execution, "ai.evidence.recorded", ctx, status="COMPLETED", summary="Evidence recorded", detail={"evidence_id": evidence["id"]}, evidence_reference=evidence["id"])
        return {"execution": execution, "verification": verification, "evidence": evidence}

    def cancel(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        execution["failure_reason"] = "cancelled"
        execution = self._transition(execution, "CANCELLED", ctx)
        return execution

    def pause(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        if _upper(execution.get("status")) not in {"EXECUTING", "APPROVED", "VERIFYING"}:
            raise NCP004Error("invalid_execution_transition", "Execution cannot be paused in its current state.", 409)
        execution["status"] = "PAUSED"
        return self.repository.upsert("ai_execution", execution)

    def resume(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        if _upper(execution.get("status")) != "PAUSED":
            raise NCP004Error("invalid_execution_transition", "Execution is not paused.", 409)
        execution["status"] = "EXECUTING"
        return self.repository.upsert("ai_execution", execution)

    def rollback(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        execution["status"] = "ROLLED_BACK"
        execution["failure_reason"] = "rolled_back"
        execution["rolled_back_at"] = _utc_now()
        self.repository.upsert("ai_execution", execution)
        self._attach_timeline(execution, "ai.execution.rolled_back", ctx, status="ROLLED_BACK", summary="Execution rolled back")
        return execution

    def timeline(self, execution_id: str, ctx: NCP004ExecutionContext) -> list[dict[str, Any]]:
        execution = self._execution_or_404(execution_id, ctx)
        return list(execution.get("timeline") or [])

    def evidence(self, execution_id: str, ctx: NCP004ExecutionContext) -> list[dict[str, Any]]:
        execution = self._execution_or_404(execution_id, ctx)
        evidences = [item for item in self.repository.list("ai_evidence") if str(item.get("execution_id")) == execution["id"]]
        return evidences

    def replay(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        replay = {
            "id": _new_id("ai-replay"),
            "execution_id": execution["id"],
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": execution.get("project_id"),
            "request_id": execution.get("request_id"),
            "actor_id": ctx.actor_id,
            "session_id": ctx.session_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "version": 1,
            "status": _upper(execution.get("status") or "RECEIVED"),
            "timeline": list(execution.get("timeline") or []),
            "evidence": self.evidence(execution_id, ctx),
            "plan": execution.get("plan"),
            "verification": execution.get("verification"),
            "metadata": {"replay_mode": "read_only"},
        }
        self.repository.upsert("ai_replay", replay)
        return replay

    def request_alias(self, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self.create_execution(payload, ctx)
        return {"request": execution}

    def execution_alias(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        return {"request": self.get_execution(execution_id, ctx)}

    def execution_plan_alias(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self.get_execution(execution_id, ctx)
        return {"plan": execution.get("plan") or {}}

    def update_interpretation(self, execution_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        execution["interpretation"] = dict(payload)
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_execution", execution)
        self._attach_timeline(execution, "ai.interpretation.updated", ctx, summary="Interpretation updated")
        return execution

    def request_review(self, execution_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        return self.request_approval(execution_id, ctx)

    def submit_review(self, execution_id: str, payload: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        return self.request_approval(execution_id, ctx)

    def get_evidence(self, execution_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        evidences = self.evidence(execution_id, ctx)
        return {"evidence": evidences}

    def create_notifier_snapshot(self, execution: dict[str, Any], ctx: NCP004ExecutionContext) -> dict[str, Any]:
        notification = {
            "id": _new_id("ai-notification"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": execution.get("project_id"),
            "request_id": execution.get("request_id"),
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "status": "UNREAD",
            "metadata": {},
            "title": f"AI execution {execution['id']} {execution['status']}",
            "body": execution.get("request_text") or "",
        }
        self.repository.upsert("notification", notification)
        return notification

    def notifications(self, ctx: NCP004ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "ai.read")
        return [notification for notification in self.repository.list("notification") if str(notification.get("tenant_id")) == ctx.tenant_id and (not ctx.workspace_id or str(notification.get("workspace_id") or "") == ctx.workspace_id)]

    def read_notification(self, notification_id: str, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        notification = self.repository.get("notification", notification_id)
        if not notification:
            raise NCP004Error("notification_not_found", "Notification not found.", 404)
        self._ensure_scope(notification, ctx, code="ai_execution_forbidden")
        notification["status"] = "READ"
        notification["updated_at"] = _utc_now()
        return self.repository.upsert("notification", notification)

    def read_all_notifications(self, ctx: NCP004ExecutionContext) -> dict[str, Any]:
        notifications = []
        for notification in self.notifications(ctx):
            notification["status"] = "READ"
            notification["updated_at"] = _utc_now()
            notifications.append(self.repository.upsert("notification", notification))
        return {"notifications": notifications}
