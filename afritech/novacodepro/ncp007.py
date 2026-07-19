from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from afritech.extensions.afriprog.code_executor.diff_model import Diff
from afritech.extensions.afriprog.code_executor.patch_model import Patch
from afritech.extensions.afriprog.git_agent.git_client import GitClient, GitClientError
from afritech.extensions.afriprog.git_agent.pr_generator import PullRequestProposalGenerator
from afritech.extensions.afriprog.repository_intelligence.repo_loader import RepoLoader, RepoLoaderError
from afritech.extensions.afriprog.repository_intelligence.structure_mapper import StructureMapper, StructureMapperError
from afritech.novacodepro.platform import NovaCodeProRepository, _event_envelope


WORKSPACE_STATUSES = {"DRAFT", "INITIALIZING", "READY", "ACTIVE", "PAUSED", "LOCKED", "ARCHIVED", "FAILED"}
SESSION_STATUSES = {"PLANNING", "ACTIVE", "AWAITING_REVIEW", "AWAITING_APPROVAL", "APPROVED", "REJECTED", "COMPLETED", "CANCELLED", "FAILED"}
TASK_TYPES = {"FEATURE", "BUG_FIX", "REFACTOR", "SECURITY_FIX", "PERFORMANCE", "ACCESSIBILITY", "DATABASE", "API", "FRONTEND", "MOBILE", "INFRASTRUCTURE", "TEST", "DOCUMENTATION", "MIGRATION"}
GENERATION_MODES = {"CREATE", "MODIFY", "REFACTOR", "FIX", "EXPLAIN", "TEST_GENERATION", "MIGRATION_GENERATION", "DOCUMENTATION", "REVIEW"}
CHANGE_SET_STATUSES = {"GENERATED", "POLICY_BLOCKED", "VALIDATION_FAILED", "READY_FOR_REVIEW", "CHANGES_REQUESTED", "APPROVED", "APPLIED", "REVERTED", "REJECTED", "EXPIRED"}
VALIDATION_TYPES = {"FORMAT", "LINT", "TYPE_CHECK", "UNIT_TEST", "INTEGRATION_TEST", "CONTRACT_TEST", "E2E_TEST", "ACCESSIBILITY_TEST", "SECURITY_SCAN", "DEPENDENCY_SCAN", "SECRET_SCAN", "LICENSE_SCAN", "MIGRATION_CHECK", "BUILD", "PACKAGE", "CUSTOM"}
REVIEW_STATUSES = {"PENDING", "IN_REVIEW", "CHANGES_REQUESTED", "APPROVED", "REJECTED"}
APPROVAL_DECISIONS = {"PENDING", "APPROVED", "REJECTED"}
COMMAND_STATUSES = {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT"}
ADMIN_ROLES = {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN"}
APPROVER_ROLES = {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN", "TECH_LEAD", "RELEASE_MANAGER", "SECURITY_ENGINEER", "APPROVER"}
EDITOR_ROLES = {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN", "DEVELOPER", "SENIOR_DEVELOPER", "TECH_LEAD", "PROJECT_OWNER", "PRODUCT_MANAGER", "BUSINESS_ANALYST", "ARCHITECT", "QA_ENGINEER", "DEVOPS_ENGINEER", "SECURITY_ENGINEER", "RELEASE_MANAGER", "APPROVER", "AI_AGENT", "SERVICE_ACCOUNT"}
OBSERVER_ROLES = EDITOR_ROLES | {"AUDITOR", "READ_ONLY_REVIEWER"}

ALLOWED_COMMANDS = {
    ("python3", "-m", "compileall"),
    ("python3", "-m", "pytest"),
    ("python", "-m", "pytest"),
    ("npm", "test"),
    ("npm", "run", "lint"),
    ("npm", "run", "build"),
    ("npm", "run", "typecheck"),
    ("git", "status", "--short"),
    ("git", "branch", "--show-current"),
    ("git", "rev-parse", "HEAD"),
    ("git", "diff", "--"),
}

PROTECTED_PATH_PREFIXES = (
    ".env",
    ".git",
    "secrets",
    "credentials",
    "private-keys",
    "production",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _stable_digest(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class DevelopmentExecutionContext:
    actor_id: str
    tenant_id: str
    organization_id: str
    workspace_id: str | None
    project_id: str | None
    role: str
    permissions: tuple[str, ...]
    session_id: str | None
    correlation_id: str
    causation_id: str | None = None
    request_id: str | None = None
    environment: str = "development"


class DevelopmentError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _command_allowed(command: Iterable[str]) -> bool:
    parts = tuple(str(item) for item in command)
    if not parts:
        return False
    if parts[0] in {"rm", "sudo", "chown", "mkfs", "dd"}:
        return False
    if any("|" in item for item in parts):
        return False
    normalized = tuple(parts[: len(min(ALLOWED_COMMANDS, key=len))])
    return any(parts[: len(template)] == template for template in ALLOWED_COMMANDS)


class NovaCodeProNCP007Service:
    def __init__(self, repository: NovaCodeProRepository, *, repo_root: str | Path | None = None) -> None:
        self.repository = repository
        self.repo_root = Path(repo_root or os.environ.get("NOVACODEPRO_REPO_ROOT") or Path.cwd()).resolve()
        self.git = GitClient(self.repo_root)
        self.repo_loader = RepoLoader(self.repo_root)
        self.pr_generator = PullRequestProposalGenerator()

    # ------------------------------------------------------------------
    # guards
    # ------------------------------------------------------------------
    def _is_admin(self, ctx: DevelopmentExecutionContext) -> bool:
        return ctx.role in ADMIN_ROLES

    def _ensure_permission(self, ctx: DevelopmentExecutionContext, permission: str) -> None:
        if self._is_admin(ctx) or permission in ctx.permissions:
            return
        raise DevelopmentError("development_forbidden", f"Missing permission: {permission}", 403)

    def _ensure_scope(self, record: dict[str, Any], ctx: DevelopmentExecutionContext, *, code: str = "development_forbidden") -> None:
        if _lower(record.get("tenant_id")) not in {"", _lower(ctx.tenant_id)}:
            raise DevelopmentError("cross_tenant_development_forbidden", "Cross-tenant access is forbidden.", 403)
        workspace_id = _lower(record.get("workspace_id"))
        if ctx.workspace_id and workspace_id and workspace_id != _lower(ctx.workspace_id):
            raise DevelopmentError(code, "Cross-workspace access is forbidden.", 403)
        project_id = _lower(record.get("project_id"))
        if ctx.project_id and project_id and project_id != _lower(ctx.project_id):
            raise DevelopmentError(code, "Cross-project access is forbidden.", 403)

    def _load(self, kind: str, record_id: str, ctx: DevelopmentExecutionContext | None = None) -> dict[str, Any]:
        record = self.repository.get(kind, record_id)
        if record is None:
            raise DevelopmentError(f"{kind}_not_found", f"{kind.replace('_', ' ').title()} not found.", 404)
        if ctx is not None:
            self._ensure_scope(record, ctx)
        return record

    def _prepare_record(self, kind: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext, *, status: str | None = None) -> dict[str, Any]:
        record = dict(payload)
        record.setdefault("id", _new_id(kind))
        record.setdefault("tenant_id", ctx.tenant_id)
        record.setdefault("organization_id", ctx.organization_id)
        if ctx.workspace_id is not None:
            record.setdefault("workspace_id", ctx.workspace_id)
        if ctx.project_id is not None:
            record.setdefault("project_id", ctx.project_id)
        if ctx.request_id is not None:
            record.setdefault("request_id", ctx.request_id)
        record.setdefault("created_by", ctx.actor_id)
        record.setdefault("updated_by", ctx.actor_id)
        record.setdefault("correlation_id", ctx.correlation_id)
        record.setdefault("causation_id", ctx.causation_id or ctx.correlation_id)
        record.setdefault("metadata", {})
        record.setdefault("version", 1)
        if status is not None:
            record["status"] = status
        record.setdefault("status", "ACTIVE")
        return record

    def _store(self, kind: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext, *, status: str | None = None) -> dict[str, Any]:
        existing = self.repository.get(kind, str(payload["id"])) if payload.get("id") else None
        record = self._prepare_record(kind, payload, ctx, status=status)
        if existing:
            record["created_at"] = existing.get("created_at")
            record["version"] = int(existing.get("version") or 1) + 1
        record["updated_at"] = _now()
        if "created_at" not in record:
            record["created_at"] = record["updated_at"]
        stored = self.repository.upsert(kind, record)
        return stored

    def _append_event(self, event_type: str, ctx: DevelopmentExecutionContext, *, resource_type: str, resource_id: str, project_id: str | None = None, request_id: str | None = None, previous_state: Any = None, new_state: Any = None, result: str = "SUCCESS", error_code: str = "", approval_reference: str | None = None, evidence_reference: str | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        event = _event_envelope(
            event_type=event_type,
            actor_type=ctx.role,
            actor_id=ctx.actor_id,
            tenant_id=ctx.tenant_id,
            organization_id=ctx.organization_id,
            project_id=project_id or ctx.project_id,
            workflow_id=ctx.workspace_id,
            correlation_id=ctx.correlation_id,
            causation_id=ctx.causation_id or ctx.correlation_id,
            data={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "request_id": request_id or ctx.request_id,
                "session_id": ctx.session_id,
                "previous_state": previous_state,
                "new_state": new_state,
                "result": result,
                "error_code": error_code,
                "approval_reference": approval_reference,
                "evidence_reference": evidence_reference,
                **(extra or {}),
            },
            metadata={
                "session_id": ctx.session_id,
                "workspace_id": ctx.workspace_id,
                "request_id": request_id or ctx.request_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        event["resource_type"] = resource_type
        event["resource_id"] = resource_id
        event["session_id"] = ctx.session_id or ""
        event["previous_state"] = previous_state
        event["new_state"] = new_state
        event["result"] = result
        event["error_code"] = error_code
        event["approval_reference"] = approval_reference or ""
        event["evidence_reference"] = evidence_reference or ""
        self.repository.append_event(event)
        self.repository.upsert(
            "development_event",
            {
                "id": event["event_id"],
                "event_id": event["event_id"],
                "event_type": event_type,
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": project_id or ctx.project_id,
                "request_id": request_id or ctx.request_id,
                "actor_id": ctx.actor_id,
                "session_id": ctx.session_id,
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "timestamp": event["occurred_at"],
                "resource_type": resource_type,
                "resource_id": resource_id,
                "previous_state": previous_state,
                "new_state": new_state,
                "result": result,
                "error_code": error_code,
                "approval_reference": approval_reference or "",
                "evidence_reference": evidence_reference or "",
                "metadata": extra or {},
                "status": new_state or result,
            },
        )
        return event

    def _append_audit(self, *, ctx: DevelopmentExecutionContext, resource_type: str, resource_id: str, action: str, previous_state: Any = None, new_state: Any = None, result: str = "SUCCESS", error_code: str = "", approval_reference: str | None = None, evidence_reference: str | None = None) -> dict[str, Any]:
        audit = self.repository.append_audit(
            kind="development",
            actor=ctx.actor_id,
            service="development-studio",
            subject=f"{resource_type}:{resource_id}",
            action=action,
            evidence=evidence_reference or "",
            detail=json.dumps(
                {
                    "tenant_id": ctx.tenant_id,
                    "workspace_id": ctx.workspace_id,
                    "project_id": ctx.project_id,
                    "previous_state": previous_state,
                    "new_state": new_state,
                    "result": result,
                    "error_code": error_code,
                    "approval_reference": approval_reference,
                },
                sort_keys=True,
            ),
        )
        return audit

    # ------------------------------------------------------------------
    # workspace
    # ------------------------------------------------------------------
    def list_workspaces(self, ctx: DevelopmentExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "development.workspace.read")
        return [item for item in self.repository.list("development_workspace") if _lower(item.get("tenant_id")) == _lower(ctx.tenant_id)]

    def create_workspace(self, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "development.workspace.configure")
        record = self._prepare_record("development_workspace", payload, ctx, status=str(payload.get("status") or "DRAFT").upper())
        record["workspace_id"] = str(payload.get("workspace_id") or record["id"])
        record["project_id"] = str(payload.get("project_id") or "")
        record.setdefault("name", "Development Workspace")
        record.setdefault("description", "")
        record.setdefault("repository_id", payload.get("repository_id") or "")
        record.setdefault("default_branch", payload.get("default_branch") or "main")
        record.setdefault("active_branch", payload.get("active_branch") or record["default_branch"])
        record.setdefault("environment_profile_id", payload.get("environment_profile_id") or "development")
        record.setdefault("architecture_baseline_id", payload.get("architecture_baseline_id") or "")
        record.setdefault("design_baseline_id", payload.get("design_baseline_id") or "")
        record.setdefault("requirement_baseline_id", payload.get("requirement_baseline_id") or "")
        record.setdefault("coding_standard_profile_id", payload.get("coding_standard_profile_id") or "")
        record.setdefault("security_profile_id", payload.get("security_profile_id") or "")
        record.setdefault("policy_profile_id", payload.get("policy_profile_id") or "")
        record["status"] = record["status"] if record["status"] in WORKSPACE_STATUSES else "DRAFT"
        stored = self._store("development_workspace", record, ctx)
        self._append_event("development.workspace.created", ctx, resource_type="development_workspace", resource_id=stored["id"], new_state=stored["status"])
        self._append_audit(ctx=ctx, resource_type="development_workspace", resource_id=stored["id"], action="create")
        return stored

    def get_workspace(self, workspace_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "development.workspace.read")
        workspace = self._load("development_workspace", workspace_id, ctx)
        return workspace

    def update_workspace(self, workspace_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "development.workspace.configure")
        workspace = self._load("development_workspace", workspace_id, ctx)
        previous = dict(workspace)
        for field in ("name", "description", "repository_id", "default_branch", "active_branch", "environment_profile_id", "architecture_baseline_id", "design_baseline_id", "requirement_baseline_id", "coding_standard_profile_id", "security_profile_id", "policy_profile_id"):
            if field in payload:
                workspace[field] = payload[field]
        workspace["status"] = str(payload.get("status") or workspace.get("status") or "DRAFT").upper()
        if workspace["status"] not in WORKSPACE_STATUSES:
            raise DevelopmentError("invalid_design_transition", "Invalid workspace status.", 400)
        workspace["updated_by"] = ctx.actor_id
        stored = self._store("development_workspace", workspace, ctx)
        self._append_event("development.workspace.updated", ctx, resource_type="development_workspace", resource_id=workspace_id, previous_state=previous.get("status"), new_state=stored["status"])
        self._append_audit(ctx=ctx, resource_type="development_workspace", resource_id=workspace_id, action="update", previous_state=previous.get("status"), new_state=stored["status"])
        return stored

    def archive_workspace(self, workspace_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "development.workspace.configure")
        workspace = self._load("development_workspace", workspace_id, ctx)
        previous = workspace.get("status")
        workspace["status"] = "ARCHIVED"
        stored = self._store("development_workspace", workspace, ctx)
        self._append_event("development.workspace.archived", ctx, resource_type="development_workspace", resource_id=workspace_id, previous_state=previous, new_state="ARCHIVED")
        return stored

    def restore_workspace(self, workspace_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "development.workspace.configure")
        workspace = self._load("development_workspace", workspace_id, ctx)
        previous = workspace.get("status")
        workspace["status"] = "READY"
        stored = self._store("development_workspace", workspace, ctx)
        self._append_event("development.workspace.restored", ctx, resource_type="development_workspace", resource_id=workspace_id, previous_state=previous, new_state="READY")
        return stored

    def workspace_summary(self, workspace_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        try:
            self.get_workspace(workspace_id, ctx)
        except DevelopmentError:
            pass
        sessions = [item for item in self.repository.list("development_session") if _lower(item.get("workspace_id")) == _lower(workspace_id)]
        tasks = [item for item in self.repository.list("development_task") if _lower(item.get("workspace_id")) == _lower(workspace_id)]
        change_sets = [item for item in self.repository.list("generated_change_set") if _lower(item.get("workspace_id")) == _lower(workspace_id)]
        approvals = [item for item in self.repository.list("development_approval") if _lower(item.get("workspace_id")) == _lower(workspace_id)]
        return {
            "workspace_id": workspace_id,
            "session_count": len(sessions),
            "task_count": len(tasks),
            "change_set_count": len(change_sets),
            "approval_count": len(approvals),
            "recent_activity": self.timeline(ctx, limit=12),
        }

    # ------------------------------------------------------------------
    # repository browsing
    # ------------------------------------------------------------------
    def repository_tree(self, ctx: DevelopmentExecutionContext, *, path: str = ".", max_depth: int = 3) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.read")
        base = (self.repo_root / path).resolve()
        if not str(base).startswith(str(self.repo_root)):
            raise DevelopmentError("repository_path_forbidden", "Path escape rejected.", 403)
        nodes: list[dict[str, Any]] = []
        for item in self.repo_loader.list_files():
            if not item.path.startswith(path.strip("./") if path not in {"", "."} else ""):
                continue
            nodes.append({"path": item.path, "extension": item.extension, "size_bytes": item.size_bytes})
        return {"root": str(self.repo_root), "path": path, "tree": nodes}

    def repository_file(self, ctx: DevelopmentExecutionContext, *, path: str) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.read")
        target = (self.repo_root / path).resolve()
        if not str(target).startswith(str(self.repo_root)):
            raise DevelopmentError("repository_path_forbidden", "Path escape rejected.", 403)
        for prefix in PROTECTED_PATH_PREFIXES:
            if Path(path).as_posix().startswith(prefix):
                raise DevelopmentError("repository_path_forbidden", "Protected path rejected.", 403)
        if not target.exists() or not target.is_file():
            raise DevelopmentError("repository_file_not_found", "File not found.", 404)
        raw = target.read_bytes()
        if b"\x00" in raw:
            raise DevelopmentError("repository_file_not_found", "Binary file not supported.", 400)
        text = raw.decode("utf-8", errors="replace")
        symbols = self._extract_symbols(text)
        return {"path": path, "content": text, "hash": hashlib.sha256(raw).hexdigest(), "symbols": symbols}

    def repository_search(self, ctx: DevelopmentExecutionContext, query: str, *, path: str | None = None) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.read")
        needle = query.strip().lower()
        if not needle:
            return {"query": query, "matches": []}
        matches: list[dict[str, Any]] = []
        for item in self.repo_loader.list_files():
            if path and not item.path.startswith(path):
                continue
            file_path = self.repo_root / item.path
            try:
                text = file_path.read_text(encoding="utf-8")
            except Exception:
                continue
            if needle not in text.lower() and needle not in item.path.lower():
                continue
            matches.append({"path": item.path, "snippet": self._snippet(text, needle), "symbols": self._extract_symbols(text)})
        return {"query": query, "matches": matches}

    def repository_status(self, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.read")
        snapshot = self.git.snapshot()
        return snapshot.canonical_dict()

    def repository_diff(self, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.read")
        result = self.git.diff()
        return {"diff": result.stdout, "exit_code": result.exit_code, "duration_seconds": result.duration_seconds}

    # ------------------------------------------------------------------
    # sessions and tasks
    # ------------------------------------------------------------------
    def create_session(self, workspace_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "development.workspace.read")
        self.get_workspace(workspace_id, ctx)
        record = self._prepare_record("development_session", payload, ctx, status="PLANNING")
        record["development_workspace_id"] = workspace_id
        record["branch_name"] = payload.get("branch_name") or self.repository_status(ctx)["branch"]
        record["base_revision"] = payload.get("base_revision") or self.repository_status(ctx)["head_sha"]
        record["current_revision"] = record["base_revision"]
        record["objective"] = payload.get("objective") or ""
        record["actor_type"] = payload.get("actor_type") or "USER"
        stored = self._store("development_session", record, ctx)
        self._append_event("development.session.created", ctx, resource_type="development_session", resource_id=stored["id"], project_id=ctx.project_id, new_state=stored["status"])
        return stored

    def get_session(self, session_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "development.workspace.read")
        return self._load("development_session", session_id, ctx)

    def complete_session(self, session_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        session = self.get_session(session_id, ctx)
        session["status"] = "COMPLETED"
        stored = self._store("development_session", session, ctx)
        self._append_event("development.session.completed", ctx, resource_type="development_session", resource_id=session_id, previous_state="ACTIVE", new_state="COMPLETED")
        return stored

    def cancel_session(self, session_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        session = self.get_session(session_id, ctx)
        session["status"] = "CANCELLED"
        stored = self._store("development_session", session, ctx)
        self._append_event("development.session.cancelled", ctx, resource_type="development_session", resource_id=session_id, previous_state="ACTIVE", new_state="CANCELLED")
        return stored

    def list_tasks(self, session_id: str, ctx: DevelopmentExecutionContext) -> list[dict[str, Any]]:
        session = self.get_session(session_id, ctx)
        return [item for item in self.repository.list("development_task") if _lower(item.get("development_session_id")) == _lower(session["id"]) or _lower(item.get("session_id")) == _lower(session["id"])]

    def create_task(self, session_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "code.generate")
        session = self.get_session(session_id, ctx)
        task = self._prepare_record("development_task", payload, ctx, status=str(payload.get("status") or "OPEN").upper())
        task["development_session_id"] = session["id"]
        task["requirement_id"] = payload.get("requirement_id") or ""
        task["architecture_element_id"] = payload.get("architecture_element_id") or ""
        task["design_artifact_id"] = payload.get("design_artifact_id") or ""
        task["title"] = payload.get("title") or "Development task"
        task["description"] = payload.get("description") or ""
        task["acceptance_criteria"] = payload.get("acceptance_criteria") or []
        task["task_type"] = str(payload.get("task_type") or "FEATURE").upper()
        if task["task_type"] not in TASK_TYPES:
            raise DevelopmentError("development_task_invalid", "Unsupported task type.", 400)
        task["risk_level"] = str(payload.get("risk_level") or "LOW").upper()
        task["assigned_actor_id"] = payload.get("assigned_actor_id") or ""
        task["assigned_agent_id"] = payload.get("assigned_agent_id") or ""
        task["sequence"] = int(payload.get("sequence") or 0)
        task["dependencies"] = payload.get("dependencies") or []
        stored = self._store("development_task", task, ctx)
        self._append_event("development.task.created", ctx, resource_type="development_task", resource_id=stored["id"], new_state=stored["status"])
        return stored

    def update_task(self, task_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "code.modify")
        task = self._load("development_task", task_id, ctx)
        for field in ("title", "description", "acceptance_criteria", "assigned_actor_id", "assigned_agent_id", "risk_level", "status", "sequence", "dependencies"):
            if field in payload:
                task[field] = payload[field]
        if "task_type" in payload and str(payload["task_type"]).upper() not in TASK_TYPES:
            raise DevelopmentError("development_task_invalid", "Unsupported task type.", 400)
        if "task_type" in payload:
            task["task_type"] = str(payload["task_type"]).upper()
        stored = self._store("development_task", task, ctx)
        self._append_event("development.task.updated", ctx, resource_type="development_task", resource_id=task_id, new_state=stored["status"])
        return stored

    # ------------------------------------------------------------------
    # generation
    # ------------------------------------------------------------------
    def create_generation_request(self, task_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "code.generate")
        task = self._load("development_task", task_id, ctx)
        session = self._load("development_session", str(task.get("development_session_id") or task.get("session_id")), ctx)
        if task.get("status") in {"ARCHIVED", "CANCELLED"}:
            raise DevelopmentError("development_forbidden", "Archived task cannot be generated.", 409)
        request = self._prepare_record("code_generation_request", payload, ctx, status="GENERATED")
        request["development_session_id"] = session["id"]
        request["development_task_id"] = task["id"]
        request["instruction"] = payload.get("instruction") or task.get("description") or task.get("title")
        request["context_snapshot_id"] = self._assemble_context(task, payload, ctx)["id"]
        request["target_files"] = list(payload.get("target_files") or [])
        request["excluded_files"] = list(payload.get("excluded_files") or [])
        request["generation_mode"] = str(payload.get("generation_mode") or "MODIFY").upper()
        if request["generation_mode"] not in GENERATION_MODES:
            raise DevelopmentError("development_generation_invalid", "Unsupported generation mode.", 400)
        request["model_provider"] = payload.get("model_provider") or "deterministic-test"
        request["model_name"] = payload.get("model_name") or "rules"
        request["policy_profile_id"] = payload.get("policy_profile_id") or task.get("policy_profile_id") or ""
        request["risk_level"] = str(payload.get("risk_level") or task.get("risk_level") or "LOW").upper()
        stored = self._store("code_generation_request", request, ctx)
        change_set = self._build_change_set(stored, task, ctx, payload)
        stored["generated_change_set_id"] = change_set["id"]
        self._store("code_generation_request", stored, ctx)
        self._append_event("development.generation.requested", ctx, resource_type="code_generation_request", resource_id=stored["id"], project_id=ctx.project_id, request_id=ctx.request_id, new_state=stored["status"], evidence_reference=change_set["id"])
        return {"request": stored, "change_set": change_set}

    def get_generation_request(self, request_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "code.generate")
        return self._load("code_generation_request", request_id, ctx)

    def retry_generation_request(self, request_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        request = self.get_generation_request(request_id, ctx)
        request["status"] = "GENERATED"
        stored = self._store("code_generation_request", request, ctx)
        self._append_event("development.generation.retried", ctx, resource_type="code_generation_request", resource_id=request_id, new_state="GENERATED")
        return stored

    def cancel_generation_request(self, request_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        request = self.get_generation_request(request_id, ctx)
        request["status"] = "CANCELLED"
        stored = self._store("code_generation_request", request, ctx)
        self._append_event("development.generation.cancelled", ctx, resource_type="code_generation_request", resource_id=request_id, new_state="CANCELLED")
        return stored

    def _build_change_set(self, request: dict[str, Any], task: dict[str, Any], ctx: DevelopmentExecutionContext, payload: dict[str, Any]) -> dict[str, Any]:
        target_files = [str(item) for item in request.get("target_files") or payload.get("target_files") or []]
        if not target_files:
            target_files = [self._default_target_file(task)]
        change_set = self._prepare_record("generated_change_set", {
            "id": _new_id("change-set"),
            "code_generation_request_id": request["id"],
            "development_session_id": request.get("development_session_id") or ctx.session_id or "",
            "development_task_id": request.get("development_task_id") or task.get("id") or "",
            "repository_id": payload.get("repository_id") or ctx.workspace_id or "repository",
            "base_revision": payload.get("base_revision") or self.repository_status(ctx)["head_sha"],
            "proposed_revision": payload.get("proposed_revision") or _new_id("rev"),
            "summary": payload.get("summary") or f"Generated change set for {task.get('title') or task['id']}",
            "rationale": payload.get("rationale") or "Deterministic generated proposal",
            "risk_level": str(payload.get("risk_level") or task.get("risk_level") or "LOW").upper(),
            "status": "GENERATED",
            "files_added_count": 0,
            "files_modified_count": 0,
            "files_deleted_count": 0,
        }, ctx, status="GENERATED")
        file_changes: list[dict[str, Any]] = []
        for index, path in enumerate(target_files):
            operation = "ADD"
            if (self.repo_root / path).exists():
                operation = "MODIFY"
            content = self._generated_content(task, path, request)
            file_change = self._prepare_record("file_change", {
                "id": _new_id("file-change"),
                "change_set_id": change_set["id"],
                "path": path,
                "operation": operation,
                "previous_hash": "",
                "proposed_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "previous_content_reference": "",
                "proposed_content_reference": content,
                "diff_reference": self._unified_diff(path, content),
                "language": self._language_for_path(path),
                "generated_by": ctx.actor_id,
                "risk_flags": [],
            }, ctx, status="ACTIVE")
            file_changes.append(file_change)
        change_set["files_added_count"] = sum(1 for item in file_changes if item["operation"] == "ADD")
        change_set["files_modified_count"] = sum(1 for item in file_changes if item["operation"] == "MODIFY")
        change_set["files_deleted_count"] = 0
        change_set["metadata"] = {
            "files": [item["id"] for item in file_changes],
            "traceability": {
                "requirement_ids": [str(task.get("requirement_id") or "")] if task.get("requirement_id") else [],
                "architecture_ids": [str(task.get("architecture_element_id") or "")] if task.get("architecture_element_id") else [],
                "design_ids": [str(task.get("design_artifact_id") or "")] if task.get("design_artifact_id") else [],
            },
        }
        stored = self._store("generated_change_set", change_set, ctx)
        for file_change in file_changes:
            file_change["change_set_id"] = stored["id"]
            self._store("file_change", file_change, ctx)
        validation = self.create_validation_run(stored["id"], {"validation_type": "FORMAT", "command": ["python3", "-m", "compileall", "."], "output_reference": "generated"}, ctx)
        evidence = self.create_evidence_package(session_id=task.get("development_session_id") or request.get("development_session_id"), change_set_id=stored["id"], ctx=ctx, references={"validation_results_reference": validation["id"], "repository_diff_reference": stored["id"]})
        stored["evidence_reference"] = evidence["id"]
        self._store("generated_change_set", stored, ctx)
        self._append_event("development.change_set.generated", ctx, resource_type="generated_change_set", resource_id=stored["id"], project_id=ctx.project_id, evidence_reference=evidence["id"], new_state=stored["status"])
        return stored

    def _generated_content(self, task: dict[str, Any], path: str, request: dict[str, Any]) -> str:
        if path.endswith(".md"):
            return f"# {task.get('title') or 'Development Change'}\n\nGenerated by NovaCodePro Development Studio.\n"
        if path.endswith(".py"):
            stem = re.sub(r"[^a-zA-Z0-9_]+", "_", Path(path).stem) or "generated_module"
            return (
                "from __future__ import annotations\n\n"
                f"def {stem}_proposal() -> dict[str, object]:\n"
                "    return {\n"
                f"        'task_id': {task['id']!r},\n"
                f"        'instruction': {request.get('instruction')!r},\n"
                "        'status': 'generated',\n"
                "    }\n"
            )
        return json.dumps({"task_id": task["id"], "instruction": request.get("instruction"), "generated": True}, indent=2)

    def _default_target_file(self, task: dict[str, Any]) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", str(task.get("title") or task.get("id") or "change").lower()).strip("-") or "change"
        return f"novacodepro/generated/{slug}.py"

    def _language_for_path(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        return {".py": "python", ".js": "javascript", ".ts": "typescript", ".jsx": "javascript", ".tsx": "typescript", ".md": "markdown", ".json": "json"}.get(suffix, "text")

    def _unified_diff(self, path: str, content: str) -> str:
        try:
            original = ""
            existing = self.repo_root / path
            if existing.exists() and existing.is_file():
                original = existing.read_text(encoding="utf-8", errors="replace")
            diff = Diff(file_path=path, diff_text="\n".join([
                f"--- a/{path}",
                f"+++ b/{path}",
                f"@@ -1 +1 @@",
                f"-{original[:200]}",
                f"+{content[:200]}",
            ]))
            return diff.diff_text
        except Exception:
            return content

    # ------------------------------------------------------------------
    # validation / reviews / approvals / commit proposals
    # ------------------------------------------------------------------
    def create_validation_run(self, change_set_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "build.execute")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        validation_type = str(payload.get("validation_type") or "CUSTOM").upper()
        if validation_type not in VALIDATION_TYPES:
            raise DevelopmentError("development_validation_invalid", "Unsupported validation type.", 400)
        command = payload.get("command") or []
        if isinstance(command, str):
            command = command.split()
        command = [str(part) for part in command]
        if command and not _command_allowed(command):
            raise DevelopmentError("development_command_forbidden", "Command is not allowed.", 403)
        started_at = _now()
        output = ""
        error = ""
        status = "PASSED"
        exit_code = 0
        if command:
            try:
                completed = subprocess.run(command, cwd=self.repo_root, capture_output=True, text=True, timeout=int(payload.get("timeout_seconds") or 600), check=False)
                output = completed.stdout
                error = completed.stderr
                exit_code = int(completed.returncode)
                status = "PASSED" if exit_code == 0 else "FAILED"
            except subprocess.TimeoutExpired as exc:
                status = "TIMED_OUT"
                exit_code = 124
                output = _normalize_output(exc.stdout)
                error = _normalize_output(exc.stderr) or "validation timed out"
        validation = self._prepare_record("validation_run", {
            "id": _new_id("validation"),
            "change_set_id": change_set_id,
            "validation_type": validation_type,
            "command": command,
            "execution_environment_id": payload.get("execution_environment_id") or ctx.environment,
            "status": status,
            "exit_code": exit_code,
            "started_at": started_at,
            "completed_at": _now(),
            "duration_ms": int(max(0.0, time.time() * 1000) - 0),
            "output_reference": payload.get("output_reference") or "",
            "error_reference": payload.get("error_reference") or "",
            "evidence_id": payload.get("evidence_id") or "",
            "stdout": output,
            "stderr": error,
        }, ctx, status=status)
        stored = self._store("validation_run", validation, ctx, status=status)
        if status == "PASSED":
            change_set["status"] = "READY_FOR_REVIEW"
            self._store("generated_change_set", change_set, ctx)
        else:
            change_set["status"] = "VALIDATION_FAILED"
            self._store("generated_change_set", change_set, ctx)
        self._append_event("development.validation.completed", ctx, resource_type="validation_run", resource_id=stored["id"], project_id=ctx.project_id, new_state=stored["status"], error_code="" if status == "PASSED" else "validation_failed")
        return stored

    def list_validation_runs(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> list[dict[str, Any]]:
        self._load("generated_change_set", change_set_id, ctx)
        return [item for item in self.repository.list("validation_run") if _lower(item.get("change_set_id")) == _lower(change_set_id)]

    def get_validation_run(self, validation_run_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "build.execute")
        return self._load("validation_run", validation_run_id, ctx)

    def cancel_validation_run(self, validation_run_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        run = self.get_validation_run(validation_run_id, ctx)
        run["status"] = "CANCELLED"
        stored = self._store("validation_run", run, ctx, status="CANCELLED")
        self._append_event("development.validation.cancelled", ctx, resource_type="validation_run", resource_id=validation_run_id, new_state="CANCELLED")
        return stored

    def create_review(self, change_set_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "approval.request")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        review = self._prepare_record("code_review", {
            "id": _new_id("review"),
            "change_set_id": change_set_id,
            "reviewer_id": payload.get("reviewer_id") or "",
            "reviewer_type": payload.get("reviewer_type") or "HUMAN",
            "status": "PENDING",
            "summary": payload.get("summary") or "",
            "risk_assessment": payload.get("risk_assessment") or change_set.get("risk_level") or "LOW",
            "reviewed_at": "",
        }, ctx, status="PENDING")
        stored = self._store("code_review", review, ctx, status="PENDING")
        self._append_event("development.review.requested", ctx, resource_type="code_review", resource_id=stored["id"], new_state="PENDING")
        return stored

    def list_reviews(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> list[dict[str, Any]]:
        self._load("generated_change_set", change_set_id, ctx)
        return [item for item in self.repository.list("code_review") if _lower(item.get("change_set_id")) == _lower(change_set_id)]

    def add_review_comment(self, review_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "approval.review")
        self._load("code_review", review_id, ctx)
        comment = self._prepare_record("review_comment", {
            "id": _new_id("review-comment"),
            "code_review_id": review_id,
            "file_path": payload.get("file_path") or "",
            "line_start": int(payload.get("line_start") or 0),
            "line_end": int(payload.get("line_end") or 0),
            "comment_type": payload.get("comment_type") or "GENERAL",
            "severity": payload.get("severity") or "LOW",
            "body": payload.get("body") or "",
            "status": "OPEN",
            "resolved_by": "",
            "resolved_at": "",
        }, ctx, status="OPEN")
        return self._store("review_comment", comment, ctx, status="OPEN")

    def update_review_comment(self, comment_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        comment = self._load("review_comment", comment_id, ctx)
        for field in ("body", "status", "resolved_by", "resolved_at"):
            if field in payload:
                comment[field] = payload[field]
        return self._store("review_comment", comment, ctx, status=str(comment.get("status") or "OPEN").upper())

    def decide_review(self, review_id: str, decision: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "approval.review")
        review = self._load("code_review", review_id, ctx)
        status = decision.upper()
        if status not in REVIEW_STATUSES:
            raise DevelopmentError("development_review_invalid", "Unsupported review decision.", 400)
        review["status"] = status
        review["reviewed_at"] = _now()
        stored = self._store("code_review", review, ctx, status=status)
        if status == "APPROVED":
            change_set = self._load("generated_change_set", review["change_set_id"], ctx)
            change_set["status"] = "APPROVED"
            self._store("generated_change_set", change_set, ctx)
        elif status == "CHANGES_REQUESTED":
            change_set = self._load("generated_change_set", review["change_set_id"], ctx)
            change_set["status"] = "CHANGES_REQUESTED"
            self._store("generated_change_set", change_set, ctx)
        self._append_event("development.review.completed", ctx, resource_type="code_review", resource_id=review_id, new_state=status)
        return stored

    def request_approval(self, change_set_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "approval.request")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        approval = self._prepare_record("development_approval", {
            "id": _new_id("approval"),
            "change_set_id": change_set_id,
            "approval_type": payload.get("approval_type") or "CHANGE_SET",
            "approver_id": payload.get("approver_id") or "",
            "decision": "PENDING",
            "conditions": list(payload.get("conditions") or []),
            "reason": payload.get("reason") or "",
            "policy_evaluation_id": payload.get("policy_evaluation_id") or "",
            "decided_at": "",
            "required_role": payload.get("required_role") or "TECH_LEAD",
            "workspace_id": change_set.get("workspace_id"),
            "project_id": change_set.get("project_id"),
            "risk_level": change_set.get("risk_level") or "LOW",
        }, ctx, status="PENDING")
        return self._store("development_approval", approval, ctx, status="PENDING")

    def list_approvals(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> list[dict[str, Any]]:
        self._load("generated_change_set", change_set_id, ctx)
        return [item for item in self.repository.list("development_approval") if _lower(item.get("change_set_id")) == _lower(change_set_id)]

    def get_approval(self, approval_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        return self._load("development_approval", approval_id, ctx)

    def decide_approval(self, approval_id: str, decision: str, ctx: DevelopmentExecutionContext, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_permission(ctx, "approval.grant")
        approval = self._load("development_approval", approval_id, ctx)
        if ctx.role not in APPROVER_ROLES and not self._is_admin(ctx):
            raise DevelopmentError("approval_forbidden", "Approver role required.", 403)
        if approval.get("decision") not in {"PENDING", ""}:
            raise DevelopmentError("approval_forbidden", "Approval already decided.", 409)
        approval["decision"] = decision.upper()
        if approval["decision"] not in APPROVAL_DECISIONS:
            raise DevelopmentError("approval_forbidden", "Unsupported approval decision.", 400)
        approval["decided_at"] = _now()
        approval["reason"] = (payload or {}).get("reason") or approval.get("reason") or ""
        approval["policy_evaluation_id"] = (payload or {}).get("policy_evaluation_id") or approval.get("policy_evaluation_id") or ""
        stored = self._store("development_approval", approval, ctx, status=approval["decision"])
        change_set = self._load("generated_change_set", approval["change_set_id"], ctx)
        if approval["decision"] == "APPROVED":
            change_set["status"] = "APPROVED"
            self._store("generated_change_set", change_set, ctx)
        elif approval["decision"] == "REJECTED":
            change_set["status"] = "REJECTED"
            self._store("generated_change_set", change_set, ctx)
        self._append_event("development.approval.decided", ctx, resource_type="development_approval", resource_id=approval_id, new_state=approval["decision"])
        return stored

    # ------------------------------------------------------------------
    # apply / revert / commit proposals / pull requests
    # ------------------------------------------------------------------
    def get_change_set(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.read")
        return self._load("generated_change_set", change_set_id, ctx)

    def list_change_set_files(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> list[dict[str, Any]]:
        self._load("generated_change_set", change_set_id, ctx)
        return [item for item in self.repository.list("file_change") if _lower(item.get("change_set_id")) == _lower(change_set_id)]

    def dry_run_change_set(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.patch.create")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        files = self.list_change_set_files(change_set_id, ctx)
        return {"change_set_id": change_set_id, "status": change_set.get("status"), "files": files, "summary": change_set.get("summary")}

    def apply_change_set(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.patch.apply")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        if change_set.get("status") not in {"READY_FOR_REVIEW", "APPROVED", "GENERATED"}:
            raise DevelopmentError("development_patch_invalid", "Change set cannot be applied.", 409)
        for file_change in self.list_change_set_files(change_set_id, ctx):
            path = Path(file_change["path"])
            target = (self.repo_root / path).resolve()
            if not str(target).startswith(str(self.repo_root)):
                raise DevelopmentError("repository_path_forbidden", "Path escape rejected.", 403)
            if any(path.as_posix().startswith(prefix) for prefix in PROTECTED_PATH_PREFIXES):
                raise DevelopmentError("repository_path_forbidden", "Protected path rejected.", 403)
            if file_change["operation"] == "DELETE":
                if target.exists():
                    target.unlink()
                continue
            _ensure_directory(target.parent)
            target.write_text(str(file_change.get("proposed_content_reference") or ""), encoding="utf-8")
        change_set["status"] = "APPLIED"
        stored = self._store("generated_change_set", change_set, ctx, status="APPLIED")
        evidence = self.create_evidence_package(session_id=change_set.get("development_session_id"), change_set_id=change_set_id, ctx=ctx, references={"commit_reference": stored["id"]})
        stored["evidence_reference"] = evidence["id"]
        self._store("generated_change_set", stored, ctx, status="APPLIED")
        self._append_event("development.change_set.applied", ctx, resource_type="generated_change_set", resource_id=change_set_id, new_state="APPLIED", evidence_reference=evidence["id"])
        return stored

    def revert_change_set(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.patch.apply")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        change_set["status"] = "REVERTED"
        stored = self._store("generated_change_set", change_set, ctx, status="REVERTED")
        self._append_event("development.change_set.reverted", ctx, resource_type="generated_change_set", resource_id=change_set_id, new_state="REVERTED")
        return stored

    def reject_change_set(self, change_set_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "approval.reject")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        change_set["status"] = "REJECTED"
        stored = self._store("generated_change_set", change_set, ctx, status="REJECTED")
        self._append_event("development.change_set.rejected", ctx, resource_type="generated_change_set", resource_id=change_set_id, new_state="REJECTED")
        return stored

    def create_commit_proposal(self, change_set_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.commit.prepare")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        proposal = self.pr_generator.build(
            task=self._task_for_change_set(change_set, ctx),
            patch=self._patch_for_change_set(change_set, ctx),
            diff=self._diff_for_change_set(change_set, ctx),
        )
        record = self._prepare_record("commit_proposal", {
            "id": _new_id("commit-proposal"),
            "change_set_id": change_set_id,
            "branch_name": payload.get("branch_name") or f"ncp007/{change_set_id}",
            "commit_message": payload.get("commit_message") or f"feat(ncp-007): governed changes for {change_set_id}",
            "author_id": ctx.actor_id,
            "status": "READY",
            "resulting_commit_hash": "",
            "proposal_hash": proposal.proposal_hash,
            "proposal_body": proposal.body,
        }, ctx, status="READY")
        return self._store("commit_proposal", record, ctx, status="READY")

    def get_commit_proposal(self, proposal_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.commit.prepare")
        return self._load("commit_proposal", proposal_id, ctx)

    def execute_commit_proposal(self, proposal_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.commit.execute")
        proposal = self._load("commit_proposal", proposal_id, ctx)
        try:
            subprocess.run(["git", "status", "--short"], cwd=self.repo_root, check=False, capture_output=True, text=True, timeout=30)
        except Exception as exc:
            raise DevelopmentError("development_commit_failed", f"Commit execution unavailable: {exc}", 500) from exc
        proposal["status"] = "EXECUTED"
        proposal["executed_at"] = _now()
        proposal["resulting_commit_hash"] = self.repository_status(ctx)["head_sha"]
        stored = self._store("commit_proposal", proposal, ctx, status="EXECUTED")
        self._append_event("development.commit.executed", ctx, resource_type="commit_proposal", resource_id=proposal_id, new_state="EXECUTED")
        return stored

    def create_pull_request_proposal(self, change_set_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.pull_request.prepare")
        change_set = self._load("generated_change_set", change_set_id, ctx)
        proposal = self.pr_generator.build(task=self._task_for_change_set(change_set, ctx), patch=self._patch_for_change_set(change_set, ctx), diff=self._diff_for_change_set(change_set, ctx))
        record = self._prepare_record("pull_request_proposal", {
            "id": _new_id("pull-request-proposal"),
            "change_set_id": change_set_id,
            "branch_name": proposal.branch_name,
            "title": payload.get("title") or proposal.title,
            "body": payload.get("body") or proposal.body,
            "status": "READY",
            "proposal_hash": proposal.proposal_hash,
        }, ctx, status="READY")
        return self._store("pull_request_proposal", record, ctx, status="READY")

    def execute_pull_request_proposal(self, proposal_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.pull_request.create")
        proposal = self._load("pull_request_proposal", proposal_id, ctx)
        proposal["status"] = "EXECUTED"
        proposal["executed_at"] = _now()
        return self._store("pull_request_proposal", proposal, ctx, status="EXECUTED")

    def _task_for_change_set(self, change_set: dict[str, Any], ctx: DevelopmentExecutionContext) -> Any:
        task = self._load("development_task", str(change_set.get("development_task_id") or ""), ctx)
        return type("TaskProxy", (), {"task_id": task["id"], "description": task.get("description") or task.get("title") or "", "risk_level": task.get("risk_level") or "LOW", "task_type": task.get("task_type") or "FEATURE"})()

    def _patch_for_change_set(self, change_set: dict[str, Any], ctx: DevelopmentExecutionContext) -> Patch | None:
        files = self.list_change_set_files(change_set["id"], ctx)
        if not files:
            return None
        first = files[0]
        return Patch(
            file_path=str(first.get("path")),
            original_content=str(first.get("previous_content_reference") or ""),
            updated_content=str(first.get("proposed_content_reference") or ""),
            patch_type=str(first.get("operation") or "proposal"),
            risk_level=str(change_set.get("risk_level") or "LOW"),
        )

    def _diff_for_change_set(self, change_set: dict[str, Any], ctx: DevelopmentExecutionContext) -> Diff | None:
        files = self.list_change_set_files(change_set["id"], ctx)
        if not files:
            return None
        first = files[0]
        return Diff(file_path=str(first.get("path")), diff_text=str(first.get("diff_reference") or ""))

    # ------------------------------------------------------------------
    # evidence / timeline / commands
    # ------------------------------------------------------------------
    def create_evidence_package(self, session_id: str | None, change_set_id: str | None, ctx: DevelopmentExecutionContext, references: dict[str, Any] | None = None) -> dict[str, Any]:
        evidence = self._prepare_record("development_evidence_package", {
            "id": _new_id("development-evidence"),
            "development_session_id": session_id or ctx.session_id or "",
            "change_set_id": change_set_id or "",
            "requirement_trace_reference": (references or {}).get("requirement_trace_reference") or "",
            "architecture_trace_reference": (references or {}).get("architecture_trace_reference") or "",
            "design_trace_reference": (references or {}).get("design_trace_reference") or "",
            "policy_results_reference": (references or {}).get("policy_results_reference") or "",
            "validation_results_reference": (references or {}).get("validation_results_reference") or "",
            "review_reference": (references or {}).get("review_reference") or "",
            "approval_reference": (references or {}).get("approval_reference") or "",
            "repository_diff_reference": (references or {}).get("repository_diff_reference") or "",
            "commit_reference": (references or {}).get("commit_reference") or "",
            "build_reference": (references or {}).get("build_reference") or "",
            "integrity_hash": _stable_digest({"session_id": session_id, "change_set_id": change_set_id, "references": references or {}}),
        }, ctx, status="ACTIVE")
        return self._store("development_evidence_package", evidence, ctx, status="ACTIVE")

    def evidence(self, ctx: DevelopmentExecutionContext, *, session_id: str | None = None, change_set_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "evidence.read")
        items = self.repository.list("development_evidence_package")
        if session_id:
            items = [item for item in items if _lower(item.get("development_session_id")) == _lower(session_id)]
        if change_set_id:
            items = [item for item in items if _lower(item.get("change_set_id")) == _lower(change_set_id)]
        return items

    def timeline(self, ctx: DevelopmentExecutionContext, *, session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        events = [item for item in self.repository.list("development_event") if _lower(item.get("tenant_id")) == _lower(ctx.tenant_id)]
        if session_id:
            events = [item for item in events if _lower(item.get("session_id") or item.get("metadata", {}).get("session_id")) == _lower(session_id) or _lower(item.get("request_id")) == _lower(session_id) or _lower(item.get("resource_id")) == _lower(session_id)]
        return events[:limit]

    def execute_command(self, session_id: str, payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "command.execute")
        self.get_session(session_id, ctx)
        command = [str(part) for part in (payload.get("command") or [])]
        if not command or not _command_allowed(command):
            raise DevelopmentError("development_command_forbidden", "Command is not allowed.", 403)
        run = self._prepare_record("command_execution_run", {
            "id": _new_id("command-run"),
            "development_session_id": session_id,
            "command": command,
            "working_directory": payload.get("working_directory") or str(self.repo_root),
            "environment_profile_id": payload.get("environment_profile_id") or ctx.environment,
            "status": "RUNNING",
            "exit_code": None,
            "started_at": _now(),
            "completed_at": "",
            "duration_ms": 0,
            "output_reference": "",
            "error_reference": "",
        }, ctx, status="RUNNING")
        try:
            completed = subprocess.run(command, cwd=Path(run["working_directory"]), capture_output=True, text=True, timeout=int(payload.get("timeout_seconds") or 900), check=False)
            run["output"] = completed.stdout
            run["error"] = completed.stderr
            run["exit_code"] = int(completed.returncode)
            run["status"] = "SUCCEEDED" if completed.returncode == 0 else "FAILED"
        except subprocess.TimeoutExpired as exc:
            run["output"] = _normalize_output(exc.stdout)
            run["error"] = _normalize_output(exc.stderr) or "command timed out"
            run["exit_code"] = 124
            run["status"] = "TIMED_OUT"
        run["completed_at"] = _now()
        run["duration_ms"] = int(max(0.0, time.time() * 1000) - 0)
        stored = self._store("command_execution_run", run, ctx, status=run["status"])
        self._append_event("development.command.executed", ctx, resource_type="command_execution_run", resource_id=stored["id"], new_state=stored["status"], error_code="" if stored["status"] == "SUCCEEDED" else "command_failed")
        return stored

    def get_command_run(self, execution_id: str, ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "command.execute")
        return self._load("command_execution_run", execution_id, ctx)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _assemble_context(self, task: dict[str, Any], payload: dict[str, Any], ctx: DevelopmentExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "repository.read")
        snapshot_id = _new_id("context-snapshot")
        items: list[dict[str, Any]] = []
        for source_type, source_id, content in (
            ("task", task["id"], task),
            ("workspace", ctx.workspace_id or "", self.repository.get("development_workspace", ctx.workspace_id) if ctx.workspace_id else {}),
            ("repository_tree", "repo", self.repository_tree(ctx, path=str(payload.get("repository_path") or "."))),
        ):
            items.append(
                {
                    "id": _new_id("context-item"),
                    "context_snapshot_id": snapshot_id,
                    "source_type": source_type,
                    "source_id": source_id,
                    "source_version": str(content.get("version") if isinstance(content, dict) else ""),
                    "content_hash": _stable_digest(content),
                    "included_reason": f"development context: {source_type}",
                    "authorization_decision": "ALLOW",
                    "retrieved_at": _now(),
                }
            )
        snapshot = self._store("context_snapshot", {
            "id": snapshot_id,
            "development_session_id": task.get("development_session_id") or "",
            "development_task_id": task["id"],
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "sources": [item["id"] for item in items],
            "status": "READY",
            "content_hash": _stable_digest(items),
        }, ctx, status="READY")
        for item in items:
            self._store("context_snapshot_item", item, ctx, status="ACTIVE")
        return snapshot

    def _extract_symbols(self, text: str) -> list[dict[str, Any]]:
        symbols: list[dict[str, Any]] = []
        for match in re.finditer(r"^(class|def|function)\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.MULTILINE):
            symbols.append({"kind": match.group(1), "name": match.group(2), "line": text.count("\n", 0, match.start()) + 1})
        return symbols[:25]

    def _snippet(self, text: str, needle: str, width: int = 120) -> str:
        index = text.lower().find(needle.lower())
        if index < 0:
            return text[:width]
        start = max(0, index - width // 2)
        end = min(len(text), index + width // 2)
        return text[start:end].replace("\n", " ")


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
