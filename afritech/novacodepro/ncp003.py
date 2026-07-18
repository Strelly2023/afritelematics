from __future__ import annotations

import mimetypes
import os
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from afritech.novacodepro.platform import NovaCodeProRepository, _event_envelope, _new_id, _now


ALLOWED_ATTACHMENT_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/json",
    "text/csv",
    "image/png",
    "image/jpeg",
}

PROJECT_STATUSES = {"DRAFT", "ACTIVE", "ON_HOLD", "COMPLETED", "ARCHIVED", "CANCELLED"}
WORK_ITEM_TYPES = {"EPIC", "FEATURE", "STORY", "TASK", "BUG", "RISK"}
WORK_ITEM_STATUSES = {"BACKLOG", "READY", "IN_PROGRESS", "BLOCKED", "IN_REVIEW", "DONE", "CANCELLED"}
REQUEST_STATUSES = {
    "DRAFT",
    "SUBMITTED",
    "ANALYSING",
    "CLARIFICATION_REQUIRED",
    "PLANNED",
    "POLICY_REVIEW",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "EXECUTING",
    "VERIFYING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "ARCHIVED",
}

REQUEST_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"SUBMITTED", "CANCELLED", "ARCHIVED"},
    "SUBMITTED": {"ANALYSING", "CANCELLED", "ARCHIVED"},
    "ANALYSING": {"CLARIFICATION_REQUIRED", "PLANNED", "FAILED"},
    "CLARIFICATION_REQUIRED": {"SUBMITTED", "CANCELLED"},
    "PLANNED": {"POLICY_REVIEW", "APPROVAL_REQUIRED", "CANCELLED"},
    "POLICY_REVIEW": {"APPROVAL_REQUIRED", "CANCELLED"},
    "APPROVAL_REQUIRED": {"APPROVED", "CANCELLED"},
    "APPROVED": {"EXECUTING", "CANCELLED"},
    "EXECUTING": {"VERIFYING", "FAILED", "CANCELLED"},
    "VERIFYING": {"COMPLETED", "FAILED"},
    "FAILED": {"DRAFT", "CANCELLED"},
    "CANCELLED": {"ARCHIVED"},
    "COMPLETED": {"ARCHIVED"},
    "ARCHIVED": set(),
}

DEFAULT_WORKSPACES = (
    {
        "id": "enterprise-admin",
        "slug": "admin",
        "name": "Platform Administration Workspace",
        "home_route": "/novacodepro/workspace/admin/dashboard",
        "status": "ACTIVE",
        "description": "Governance, users, settings, approvals, and release control.",
    },
    {
        "id": "enterprise-product-manager",
        "slug": "product",
        "name": "Product Management Workspace",
        "home_route": "/novacodepro/workspace/product/dashboard",
        "status": "ACTIVE",
        "description": "Roadmaps, requests, and portfolio planning.",
    },
    {
        "id": "enterprise-business-analyst",
        "slug": "business-analyst",
        "name": "Business Analysis Workspace",
        "home_route": "/novacodepro/workspace/business-analyst/dashboard",
        "status": "ACTIVE",
        "description": "Discovery, analysis, requirements, and stakeholder collaboration.",
    },
    {
        "id": "enterprise-project-manager",
        "slug": "project-manager",
        "name": "Project Delivery Workspace",
        "home_route": "/novacodepro/workspace/project-manager/dashboard",
        "status": "ACTIVE",
        "description": "Project delivery, milestones, work items, and risk tracking.",
    },
    {
        "id": "enterprise-developer",
        "slug": "developer",
        "name": "Developer Workspace",
        "home_route": "/novacodepro/workspace/developer/dashboard",
        "status": "ACTIVE",
        "description": "Implementation, code review, tasks, and release readiness.",
    },
    {
        "id": "enterprise-customer",
        "slug": "customer",
        "name": "Customer Workspace",
        "home_route": "/novacodepro/workspace/customer/dashboard",
        "status": "ACTIVE",
        "description": "Requests, comments, notifications, and delivery tracking.",
    },
)


@dataclass(frozen=True)
class NCP003ExecutionContext:
    actor_id: str
    tenant_id: str
    organization_id: str
    workspace_id: str | None
    role: str
    permissions: tuple[str, ...]
    session_id: str | None
    correlation_id: str
    causation_id: str | None = None


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "item"


def _base_record(
    *,
    kind: str,
    ctx: NCP003ExecutionContext,
    payload: dict[str, Any],
    record_id: str | None = None,
) -> dict[str, Any]:
    now = _now()
    return {
        "id": record_id or _new_id(kind.replace("_", "-")),
        "tenant_id": ctx.tenant_id,
        "organization_id": ctx.organization_id,
        "workspace_id": ctx.workspace_id,
        "created_at": now,
        "updated_at": now,
        "created_by": ctx.actor_id,
        "updated_by": ctx.actor_id,
        "correlation_id": ctx.correlation_id,
        "causation_id": ctx.causation_id or ctx.correlation_id,
        "version": int(payload.get("version") or 1),
        "metadata": dict(payload.get("metadata") or {}),
    }


def _record_event(
    repository: NovaCodeProRepository,
    *,
    event_type: str,
    ctx: NCP003ExecutionContext,
    project_id: str | None = None,
    request_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = _event_envelope(
        event_type=event_type,
        actor_type="user",
        actor_id=ctx.actor_id,
        tenant_id=ctx.tenant_id,
        organization_id=ctx.organization_id,
        project_id=project_id,
        workflow_id=request_id,
        correlation_id=ctx.correlation_id,
        causation_id=ctx.causation_id or ctx.correlation_id,
        data=data or {},
    )
    repository.append_event(event)
    return event


class NovaCodeProNCP003Service:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository
        self._seed_default_workspaces()

    def _seed_default_workspaces(self) -> None:
        existing = {item["id"] for item in self.repository.list("workspace")}
        for workspace in DEFAULT_WORKSPACES:
            if workspace["id"] in existing:
                continue
            self.repository.upsert(
                "workspace",
                {
                    **workspace,
                    "tenant_id": "novatech",
                    "organization_id": "novatech",
                    "owner_id": "system",
                    "settings": {"notifications_enabled": True, "favorites_enabled": True},
                    "members": [],
                    "favorites": [],
                    "activity": [],
                    "approvals": [],
                    "tasks": [],
                    "notifications": [],
                    "workspace_type": workspace["slug"],
                    "status": workspace["status"],
                    "slug": workspace["slug"],
                    "name": workspace["name"],
                    "home_route": workspace["home_route"],
                    "description": workspace["description"],
                    "created_by": "system",
                    "updated_by": "system",
                    "correlation_id": "seed",
                    "causation_id": "seed",
                    "version": 1,
                    "metadata": {"seeded": True},
                },
            )

    def _permission_check(self, ctx: NCP003ExecutionContext, permission: str) -> None:
        if permission not in ctx.permissions and ctx.role not in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN"}:
            raise PermissionError(permission)

    def _workspace(self, workspace_id: str) -> dict[str, Any] | None:
        return self.repository.get("workspace", workspace_id)

    def _workspace_or_404(self, workspace_id: str, ctx: NCP003ExecutionContext | None = None) -> dict[str, Any]:
        workspace = self._workspace(workspace_id)
        if workspace is None:
            raise KeyError("workspace_not_found")
        if ctx and str(workspace.get("tenant_id")) != ctx.tenant_id:
            raise PermissionError("workspace_forbidden")
        return workspace

    def list_workspaces(self, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        workspaces = [item for item in self.repository.list("workspace") if str(item.get("tenant_id")) == ctx.tenant_id]
        if not workspaces:
            self._seed_default_workspaces()
            workspaces = [item for item in self.repository.list("workspace") if str(item.get("tenant_id")) == ctx.tenant_id]
        return workspaces

    def create_workspace(self, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "workspace.create")
        record = {
            **_base_record(kind="workspace", ctx=ctx, payload=payload, record_id=str(payload.get("id") or payload.get("workspace_id") or _new_id("workspace"))),
            "slug": slugify(str(payload["name"])),
            "name": str(payload["name"]),
            "description": str(payload.get("description") or ""),
            "home_route": str(payload.get("home_route") or f"/novacodepro/workspace/{slugify(str(payload['name']))}/dashboard"),
            "status": str(payload.get("status") or "ACTIVE").upper(),
            "owner_id": str(payload.get("owner_id") or ctx.actor_id),
            "settings": dict(payload.get("settings") or {}),
            "members": list(payload.get("members") or []),
            "favorites": [],
            "notifications": [],
            "activity": [],
            "approvals": [],
            "tasks": [],
        }
        self.repository.upsert("workspace", record)
        self._record_workspace_activity(record["id"], "workspace.created", ctx, data={"workspace_id": record["id"], "name": record["name"]})
        return record

    def update_workspace(self, workspace_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "workspace.update")
        workspace = self._workspace_or_404(workspace_id, ctx)
        workspace.update(
            {
                "name": str(payload.get("name") or workspace["name"]),
                "description": str(payload.get("description") or workspace.get("description") or ""),
                "home_route": str(payload.get("home_route") or workspace.get("home_route") or ""),
                "status": str(payload.get("status") or workspace.get("status") or "ACTIVE").upper(),
                "settings": {**dict(workspace.get("settings") or {}), **dict(payload.get("settings") or {})},
                "updated_by": ctx.actor_id,
                "version": int(workspace.get("version") or 1) + 1,
                "metadata": {**dict(workspace.get("metadata") or {}), **dict(payload.get("metadata") or {})},
            }
        )
        self.repository.upsert("workspace", workspace)
        self._record_workspace_activity(workspace_id, "workspace.updated", ctx, data={"workspace_id": workspace_id})
        return workspace

    def select_workspace(self, workspace_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        workspace = self._workspace_or_404(workspace_id, ctx)
        self._permission_check(ctx, "workspace.read")
        membership = self._ensure_membership("workspace_membership", workspace_id, ctx.actor_id, ctx, role=ctx.role)
        self._record_workspace_activity(workspace_id, "workspace.selected", ctx, data={"workspace_id": workspace_id})
        return {"workspace": workspace, "membership": membership}

    def workspace_members(self, workspace_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._workspace_or_404(workspace_id, ctx)
        return [item for item in self.repository.list("workspace_membership") if item.get("workspace_id") == workspace_id and item.get("tenant_id") == ctx.tenant_id]

    def add_workspace_member(self, workspace_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "workspace.member.manage")
        self._workspace_or_404(workspace_id, ctx)
        member = self._ensure_membership("workspace_membership", workspace_id, str(payload["user_id"]), ctx, role=str(payload.get("role") or "MEMBER"))
        self._record_workspace_activity(workspace_id, "workspace.member.added", ctx, data={"member_id": member["id"]})
        return member

    def remove_workspace_member(self, workspace_id: str, member_id: str, ctx: NCP003ExecutionContext) -> None:
        self._permission_check(ctx, "workspace.member.manage")
        membership = self.repository.get("workspace_membership", member_id)
        if membership is None or membership.get("workspace_id") != workspace_id or membership.get("tenant_id") != ctx.tenant_id:
            raise KeyError("workspace_member_not_found")
        self.repository.delete("workspace_membership", member_id)
        self._record_workspace_activity(workspace_id, "workspace.member.removed", ctx, data={"member_id": member_id})

    def workspace_activity(self, workspace_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._workspace_or_404(workspace_id, ctx)
        return [item for item in self.repository.list("activity_event") if item.get("workspace_id") == workspace_id and item.get("tenant_id") == ctx.tenant_id]

    def workspace_tasks(self, workspace_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._workspace_or_404(workspace_id, ctx)
        return [item for item in self.repository.list("project_work_item") if item.get("workspace_id") == workspace_id and item.get("tenant_id") == ctx.tenant_id]

    def workspace_approvals(self, workspace_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._workspace_or_404(workspace_id, ctx)
        return [item for item in self.repository.list("request_assignment") if item.get("workspace_id") == workspace_id and item.get("tenant_id") == ctx.tenant_id]

    def workspace_favorites(self, workspace_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        workspace = self._workspace_or_404(workspace_id, ctx)
        return list(workspace.get("favorites") or [])

    def add_workspace_favorite(self, workspace_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "workspace.favorite.manage")
        workspace = self._workspace_or_404(workspace_id, ctx)
        favorite = {
            "id": _new_id("favorite"),
            "workspace_id": workspace_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "label": str(payload.get("label") or payload.get("name") or "Favorite"),
            "route": str(payload.get("route") or ""),
            "created_by": ctx.actor_id,
            "created_at": _now(),
        }
        favorites = list(workspace.get("favorites") or [])
        favorites.insert(0, favorite)
        workspace["favorites"] = favorites
        workspace["updated_by"] = ctx.actor_id
        workspace["updated_at"] = _now()
        self.repository.upsert("workspace", workspace)
        self.repository.upsert("workspace_preference", favorite)
        self._record_workspace_activity(workspace_id, "workspace.favorite.added", ctx, data={"favorite_id": favorite["id"]})
        return favorite

    def remove_workspace_favorite(self, workspace_id: str, favorite_id: str, ctx: NCP003ExecutionContext) -> None:
        self._permission_check(ctx, "workspace.favorite.manage")
        workspace = self._workspace_or_404(workspace_id, ctx)
        favorites = [item for item in list(workspace.get("favorites") or []) if item.get("id") != favorite_id]
        workspace["favorites"] = favorites
        workspace["updated_by"] = ctx.actor_id
        workspace["updated_at"] = _now()
        self.repository.upsert("workspace", workspace)
        self.repository.delete("workspace_preference", favorite_id)
        self._record_workspace_activity(workspace_id, "workspace.favorite.removed", ctx, data={"favorite_id": favorite_id})

    def workspace_notifications(self, workspace_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._workspace_or_404(workspace_id, ctx)
        return [item for item in self.repository.list("notification") if item.get("workspace_id") == workspace_id and item.get("tenant_id") == ctx.tenant_id]

    def update_workspace_settings(self, workspace_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "workspace.settings.manage")
        workspace = self._workspace_or_404(workspace_id, ctx)
        workspace["settings"] = {**dict(workspace.get("settings") or {}), **dict(payload.get("settings") or payload)}
        workspace["updated_by"] = ctx.actor_id
        workspace["updated_at"] = _now()
        workspace["version"] = int(workspace.get("version") or 1) + 1
        self.repository.upsert("workspace", workspace)
        self._record_workspace_activity(workspace_id, "workspace.settings.updated", ctx, data={"workspace_id": workspace_id})
        return workspace

    def list_projects(self, ctx: NCP003ExecutionContext, workspace_id: str | None = None) -> list[dict[str, Any]]:
        projects = [item for item in self.repository.list("project") if item.get("tenant_id") == ctx.tenant_id]
        if workspace_id is not None:
            projects = [item for item in projects if item.get("workspace_id") == workspace_id]
        return projects

    def create_project(self, payload: dict[str, Any], ctx: NCP003ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        self._permission_check(ctx, "project.create")
        if not idempotency_key:
            raise ValueError("invalid_idempotency_key")
        workspace_id = str(payload.get("workspace_id") or ctx.workspace_id or "")
        if not workspace_id:
            raise ValueError("workspace_required")
        workspace = self._workspace_or_404(workspace_id, ctx)
        if str(workspace.get("status") or "").upper() not in {"ACTIVE", "DRAFT"}:
            raise ValueError("workspace_inactive")
        if idempotency_key:
            previous = self.repository.get("idempotency_record", idempotency_key)
            if previous is not None:
                return dict(previous.get("response") or {})
        project = {
            **_base_record(kind="project", ctx=ctx, payload=payload, record_id=str(payload.get("id") or payload.get("project_id") or _new_id("project"))),
            "workspace_id": workspace_id,
            "slug": slugify(str(payload["name"])),
            "name": str(payload["name"]),
            "description": str(payload.get("description") or ""),
            "status": str(payload.get("status") or "DRAFT").upper(),
            "owner_id": str(payload.get("owner_id") or ctx.actor_id),
            "start_date": payload.get("start_date"),
            "target_date": payload.get("target_date"),
            "archived_at": None,
            "archived_by": None,
            "members": [{"user_id": ctx.actor_id, "role": "OWNER"}],
            "milestones": [],
            "work_items": [],
            "risks": [],
            "attachments": [],
            "comments": [],
            "activity": [],
            "requests": [],
        }
        self.repository.upsert("project", project)
        self._upsert_project_member(project["id"], ctx.actor_id, "OWNER", ctx)
        self._record_project_activity(project["id"], "project.created", ctx, data={"project_id": project["id"], "name": project["name"]})
        if idempotency_key:
            self.repository.upsert(
                "idempotency_record",
                {
                    "id": idempotency_key,
                    "tenant_id": ctx.tenant_id,
                    "organization_id": ctx.organization_id,
                    "workspace_id": workspace_id,
                    "response": project,
                    "created_at": _now(),
                    "updated_at": _now(),
                },
            )
        return project

    def get_project(self, project_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any] | None:
        project = self.repository.get("project", project_id)
        if project is None or project.get("tenant_id") != ctx.tenant_id:
            return None
        return project

    def update_project(self, project_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.update")
        project = self._project_or_404(project_id, ctx)
        if project.get("status") == "ARCHIVED":
            raise ValueError("project_archived")
        project.update(
            {
                "name": str(payload.get("name") or project["name"]),
                "description": str(payload.get("description") or project.get("description") or ""),
                "owner_id": str(payload.get("owner_id") or project.get("owner_id") or ctx.actor_id),
                "start_date": payload.get("start_date") or project.get("start_date"),
                "target_date": payload.get("target_date") or project.get("target_date"),
                "status": str(payload.get("status") or project.get("status") or "DRAFT").upper(),
                "updated_by": ctx.actor_id,
                "version": int(project.get("version") or 1) + 1,
                "metadata": {**dict(project.get("metadata") or {}), **dict(payload.get("metadata") or {})},
            }
        )
        self.repository.upsert("project", project)
        self._record_project_activity(project_id, "project.updated", ctx, data={"project_id": project_id})
        return project

    def archive_project(self, project_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.archive")
        project = self._project_or_404(project_id, ctx)
        previous = str(project.get("status") or "ACTIVE").upper()
        project["status"] = "ARCHIVED"
        project["archived_at"] = _now()
        project["archived_by"] = ctx.actor_id
        project["updated_by"] = ctx.actor_id
        project["version"] = int(project.get("version") or 1) + 1
        self.repository.upsert("project", project)
        self._record_project_activity(project_id, "project.archived", ctx, data={"project_id": project_id, "previous_status": previous, "new_status": "ARCHIVED"})
        self._notify(project.get("workspace_id"), "project_archive", f"Project {project['name']} archived", ctx, project_id=project_id)
        return project

    def restore_project(self, project_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.archive")
        project = self._project_or_404(project_id, ctx)
        project["status"] = "ACTIVE"
        project["archived_at"] = None
        project["archived_by"] = None
        project["updated_by"] = ctx.actor_id
        project["version"] = int(project.get("version") or 1) + 1
        self.repository.upsert("project", project)
        self._record_project_activity(project_id, "project.restored", ctx, data={"project_id": project_id})
        return project

    def project_activity(self, project_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._project_or_404(project_id, ctx)
        return [item for item in self.repository.list("activity_event") if item.get("project_id") == project_id]

    def project_members(self, project_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._project_or_404(project_id, ctx)
        return [item for item in self.repository.list("project_member") if item.get("project_id") == project_id and item.get("tenant_id") == ctx.tenant_id]

    def add_project_member(self, project_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.member.manage")
        project = self._project_or_404(project_id, ctx)
        member = self._upsert_project_member(project_id, str(payload["user_id"]), str(payload.get("role") or "MEMBER"), ctx)
        self._record_project_activity(project_id, "project.member.added", ctx, data={"member_id": member["id"]})
        project["members"] = self.project_members(project_id, ctx)
        self.repository.upsert("project", project)
        return member

    def remove_project_member(self, project_id: str, member_id: str, ctx: NCP003ExecutionContext) -> None:
        self._permission_check(ctx, "project.member.manage")
        member = self.repository.get("project_member", member_id)
        if member is None or member.get("project_id") != project_id or member.get("tenant_id") != ctx.tenant_id:
            raise KeyError("project_member_not_found")
        self.repository.delete("project_member", member_id)
        self._record_project_activity(project_id, "project.member.removed", ctx, data={"member_id": member_id})

    def milestone_list(self, project_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._project_or_404(project_id, ctx)
        return [item for item in self.repository.list("project_milestone") if item.get("project_id") == project_id]

    def create_milestone(self, project_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.milestone.manage")
        project = self._project_or_404(project_id, ctx)
        if project.get("status") == "ARCHIVED":
            raise ValueError("project_archived")
        milestone = {
            **_base_record(kind="project_milestone", ctx=ctx, payload=payload, record_id=str(payload.get("id") or _new_id("milestone"))),
            "project_id": project_id,
            "name": str(payload["name"]),
            "status": str(payload.get("status") or "BACKLOG").upper(),
            "due_date": payload.get("due_date"),
        }
        self.repository.upsert("project_milestone", milestone)
        project.setdefault("milestones", []).append(milestone)
        self.repository.upsert("project", project)
        self._record_project_activity(project_id, "milestone.created", ctx, data={"milestone_id": milestone["id"]})
        return milestone

    def update_milestone(self, project_id: str, milestone_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.milestone.manage")
        milestone = self._project_record_or_404("project_milestone", milestone_id, project_id, ctx)
        milestone["name"] = str(payload.get("name") or milestone["name"])
        milestone["status"] = str(payload.get("status") or milestone.get("status") or "BACKLOG").upper()
        milestone["due_date"] = payload.get("due_date") or milestone.get("due_date")
        milestone["updated_by"] = ctx.actor_id
        milestone["version"] = int(milestone.get("version") or 1) + 1
        self.repository.upsert("project_milestone", milestone)
        self._record_project_activity(project_id, "milestone.updated", ctx, data={"milestone_id": milestone_id})
        return milestone

    def delete_milestone(self, project_id: str, milestone_id: str, ctx: NCP003ExecutionContext) -> None:
        self._permission_check(ctx, "project.milestone.manage")
        self._project_record_or_404("project_milestone", milestone_id, project_id, ctx)
        self.repository.delete("project_milestone", milestone_id)
        self._record_project_activity(project_id, "milestone.deleted", ctx, data={"milestone_id": milestone_id})

    def list_work_items(self, project_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._project_or_404(project_id, ctx)
        return [item for item in self.repository.list("project_work_item") if item.get("project_id") == project_id]

    def create_work_item(self, project_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.work_item.manage")
        project = self._project_or_404(project_id, ctx)
        if project.get("status") == "ARCHIVED":
            raise ValueError("project_archived")
        work_item_type = str(payload.get("type") or payload.get("item_type") or "TASK").upper()
        if work_item_type not in WORK_ITEM_TYPES:
            raise ValueError("invalid_work_item_type")
        work_item = {
            **_base_record(kind="project_work_item", ctx=ctx, payload=payload, record_id=str(payload.get("id") or _new_id("work-item"))),
            "project_id": project_id,
            "workspace_id": project.get("workspace_id"),
            "type": work_item_type,
            "title": str(payload["title"]),
            "description": str(payload.get("description") or ""),
            "status": str(payload.get("status") or "BACKLOG").upper(),
            "assignee_id": payload.get("assignee_id"),
            "due_date": payload.get("due_date"),
        }
        self.repository.upsert("project_work_item", work_item)
        project.setdefault("work_items", []).append(work_item)
        self.repository.upsert("project", project)
        self._record_project_activity(project_id, "work_item.created", ctx, data={"work_item_id": work_item["id"]})
        return work_item

    def update_work_item(self, project_id: str, work_item_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.work_item.manage")
        work_item = self._project_record_or_404("project_work_item", work_item_id, project_id, ctx)
        if self._project_or_404(project_id, ctx).get("status") == "ARCHIVED":
            raise ValueError("project_archived")
        work_item["title"] = str(payload.get("title") or work_item["title"])
        work_item["description"] = str(payload.get("description") or work_item.get("description") or "")
        work_item["type"] = str(payload.get("type") or work_item.get("type") or "TASK").upper()
        work_item["status"] = str(payload.get("status") or work_item.get("status") or "BACKLOG").upper()
        work_item["assignee_id"] = payload.get("assignee_id", work_item.get("assignee_id"))
        work_item["due_date"] = payload.get("due_date", work_item.get("due_date"))
        work_item["updated_by"] = ctx.actor_id
        work_item["version"] = int(work_item.get("version") or 1) + 1
        self.repository.upsert("project_work_item", work_item)
        self._record_project_activity(project_id, "work_item.updated", ctx, data={"work_item_id": work_item_id})
        return work_item

    def assign_work_item(self, project_id: str, work_item_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.work_item.manage")
        work_item = self._project_record_or_404("project_work_item", work_item_id, project_id, ctx)
        work_item["assignee_id"] = str(payload["assignee_id"])
        work_item["updated_by"] = ctx.actor_id
        self.repository.upsert("project_work_item", work_item)
        self._record_project_activity(project_id, "work_item.assigned", ctx, data={"work_item_id": work_item_id, "assignee_id": work_item["assignee_id"]})
        return {
            "id": _new_id("assignment"),
            "project_id": project_id,
            "workspace_id": work_item.get("workspace_id"),
            "tenant_id": ctx.tenant_id,
            "work_item_id": work_item_id,
            "assignee_id": work_item["assignee_id"],
            "assignment_role": str(payload.get("assignment_role") or "REVIEWER"),
            "assigned_by": ctx.actor_id,
            "assigned_at": _now(),
            "due_date": payload.get("due_date"),
            "status": "ACTIVE",
        }

    def transition_work_item(self, project_id: str, work_item_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.work_item.manage")
        work_item = self._project_record_or_404("project_work_item", work_item_id, project_id, ctx)
        new_status = str(payload.get("status") or payload.get("transition") or "").upper()
        if new_status not in WORK_ITEM_STATUSES:
            raise ValueError("invalid_work_item_status")
        previous = str(work_item.get("status") or "BACKLOG")
        work_item["status"] = new_status
        work_item["updated_by"] = ctx.actor_id
        self.repository.upsert("project_work_item", work_item)
        self._record_project_activity(project_id, "work_item.transitioned", ctx, data={"work_item_id": work_item_id, "previous_status": previous, "new_status": new_status})
        return {"previous_status": previous, "new_status": new_status, "work_item": work_item}

    def delete_work_item(self, project_id: str, work_item_id: str, ctx: NCP003ExecutionContext) -> None:
        self._permission_check(ctx, "project.work_item.manage")
        self._project_record_or_404("project_work_item", work_item_id, project_id, ctx)
        self.repository.delete("project_work_item", work_item_id)
        self._record_project_activity(project_id, "work_item.deleted", ctx, data={"work_item_id": work_item_id})

    def list_risks(self, project_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._project_or_404(project_id, ctx)
        return [item for item in self.repository.list("project_risk") if item.get("project_id") == project_id]

    def create_risk(self, project_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.risk.manage")
        risk = {
            **_base_record(kind="project_risk", ctx=ctx, payload=payload, record_id=str(payload.get("id") or _new_id("risk"))),
            "project_id": project_id,
            "title": str(payload["title"]),
            "severity": str(payload.get("severity") or "MEDIUM").upper(),
            "status": str(payload.get("status") or "OPEN").upper(),
            "owner_id": payload.get("owner_id"),
        }
        self.repository.upsert("project_risk", risk)
        self._record_project_activity(project_id, "risk.created", ctx, data={"risk_id": risk["id"]})
        return risk

    def update_risk(self, project_id: str, risk_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "project.risk.manage")
        risk = self._project_record_or_404("project_risk", risk_id, project_id, ctx)
        risk["title"] = str(payload.get("title") or risk["title"])
        risk["severity"] = str(payload.get("severity") or risk.get("severity") or "MEDIUM").upper()
        risk["status"] = str(payload.get("status") or risk.get("status") or "OPEN").upper()
        risk["owner_id"] = payload.get("owner_id", risk.get("owner_id"))
        risk["updated_by"] = ctx.actor_id
        risk["version"] = int(risk.get("version") or 1) + 1
        self.repository.upsert("project_risk", risk)
        self._record_project_activity(project_id, "risk.updated", ctx, data={"risk_id": risk_id})
        return risk

    def roadmap(self, project_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        project = self._project_or_404(project_id, ctx)
        return {
            "project_id": project_id,
            "workspace_id": project.get("workspace_id"),
            "milestones": self.milestone_list(project_id, ctx),
            "work_items": self.list_work_items(project_id, ctx),
            "risks": self.list_risks(project_id, ctx),
        }

    def list_requests(self, ctx: NCP003ExecutionContext, workspace_id: str | None = None) -> list[dict[str, Any]]:
        requests = [item for item in self.repository.list("request") if item.get("tenant_id") == ctx.tenant_id]
        if workspace_id is not None:
            requests = [item for item in requests if item.get("workspace_id") == workspace_id]
        return requests

    def create_request(self, payload: dict[str, Any], ctx: NCP003ExecutionContext, *, idempotency_key: str | None = None) -> dict[str, Any]:
        self._permission_check(ctx, "request.create")
        workspace_id = str(payload.get("workspace_id") or ctx.workspace_id or "")
        if not workspace_id:
            raise ValueError("workspace_required")
        self._workspace_or_404(workspace_id, ctx)
        if idempotency_key:
            previous = self.repository.get("idempotency_record", idempotency_key)
            if previous is not None:
                return dict(previous.get("response") or {})
        request = {
            **_base_record(kind="request", ctx=ctx, payload=payload, record_id=str(payload.get("id") or payload.get("request_id") or _new_id("request"))),
            "workspace_id": workspace_id,
            "project_id": payload.get("project_id"),
            "title": str(payload["title"]),
            "description": str(payload.get("description") or ""),
            "request_type": str(payload.get("request_type") or "TEXT"),
            "priority": str(payload.get("priority") or "MEDIUM"),
            "status": str(payload.get("status") or "DRAFT").upper(),
            "attachments": [],
            "comments": [],
            "assignments": [],
            "transitions": [],
            "history": [],
            "available_transitions": [],
        }
        self.repository.upsert("request", request)
        self._record_activity(ctx, workspace_id, "request.created", request_id=request["id"], data={"request_id": request["id"]})
        self._record_request_transition(request["id"], None, "DRAFT", ctx, reason="created", project_id=request.get("project_id"), workspace_id=workspace_id)
        if idempotency_key:
            self.repository.upsert(
                "idempotency_record",
                {
                    "id": idempotency_key,
                    "tenant_id": ctx.tenant_id,
                    "organization_id": ctx.organization_id,
                    "workspace_id": workspace_id,
                    "response": request,
                    "created_at": _now(),
                    "updated_at": _now(),
                },
            )
        return request

    def get_request(self, request_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any] | None:
        request = self.repository.get("request", request_id)
        if request is None or request.get("tenant_id") != ctx.tenant_id:
            return None
        return request

    def update_request(self, request_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "request.update")
        request = self._request_or_404(request_id, ctx)
        if request.get("status") == "ARCHIVED":
            raise ValueError("request_archived")
        request["title"] = str(payload.get("title") or request["title"])
        request["description"] = str(payload.get("description") or request.get("description") or "")
        request["priority"] = str(payload.get("priority") or request.get("priority") or "MEDIUM")
        request["project_id"] = payload.get("project_id", request.get("project_id"))
        request["updated_by"] = ctx.actor_id
        request["version"] = int(request.get("version") or 1) + 1
        self.repository.upsert("request", request)
        self._record_activity(ctx, request.get("workspace_id"), "request.updated", request_id=request_id, data={"request_id": request_id})
        return request

    def submit_request(self, request_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "request.submit")
        request = self._request_or_404(request_id, ctx)
        if request.get("status") != "DRAFT":
            raise ValueError("invalid_request_transition")
        previous = request["status"]
        request["status"] = "SUBMITTED"
        request["updated_by"] = ctx.actor_id
        request["version"] = int(request.get("version") or 1) + 1
        self.repository.upsert("request", request)
        self._record_request_transition(request_id, previous, request["status"], ctx, reason="submitted", project_id=request.get("project_id"), workspace_id=request.get("workspace_id"))
        self._record_activity(ctx, request.get("workspace_id"), "request.submitted", request_id=request_id, data={"request_id": request_id})
        self._notify(request.get("workspace_id"), "request_required", f"Request {request['title']} submitted", ctx, request_id=request_id)
        return request

    def transition_request(self, request_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "request.transition")
        request = self._request_or_404(request_id, ctx)
        new_status = str(payload.get("status") or payload.get("transition") or "").upper()
        if new_status not in REQUEST_STATUSES:
            raise ValueError("invalid_request_transition")
        allowed = REQUEST_TRANSITIONS.get(str(request.get("status") or "DRAFT").upper(), set())
        if new_status not in allowed:
            raise ValueError("invalid_request_transition")
        previous = str(request.get("status") or "DRAFT").upper()
        request["status"] = new_status
        request["updated_by"] = ctx.actor_id
        request["version"] = int(request.get("version") or 1) + 1
        self.repository.upsert("request", request)
        self._record_request_transition(
            request_id,
            previous,
            new_status,
            ctx,
            reason=str(payload.get("reason") or ""),
            project_id=request.get("project_id"),
            workspace_id=request.get("workspace_id"),
        )
        self._record_activity(ctx, request.get("workspace_id"), "request.transitioned", request_id=request_id, data={"request_id": request_id, "previous_status": previous, "new_status": new_status})
        return request

    def archive_request(self, request_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "request.archive")
        request = self._request_or_404(request_id, ctx)
        previous = str(request.get("status") or "DRAFT").upper()
        request["status"] = "ARCHIVED"
        request["updated_by"] = ctx.actor_id
        request["version"] = int(request.get("version") or 1) + 1
        self.repository.upsert("request", request)
        self._record_request_transition(request_id, previous, "ARCHIVED", ctx, reason="archived", project_id=request.get("project_id"), workspace_id=request.get("workspace_id"))
        return request

    def request_history(self, request_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        request = self._request_or_404(request_id, ctx)
        return list(request.get("history") or [])

    def request_assignments(self, request_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._request_or_404(request_id, ctx)
        return [item for item in self.repository.list("request_assignment") if item.get("request_id") == request_id]

    def add_request_assignment(self, request_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "request.assign")
        request = self._request_or_404(request_id, ctx)
        assignment = {
            "id": str(payload.get("id") or _new_id("assignment")),
            "request_id": request_id,
            "project_id": request.get("project_id"),
            "workspace_id": request.get("workspace_id"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "assignee_id": str(payload["assignee_id"]),
            "assignment_role": str(payload.get("assignment_role") or "REVIEWER"),
            "assigned_by": ctx.actor_id,
            "assigned_at": _now(),
            "due_date": payload.get("due_date"),
            "status": "ACTIVE",
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "metadata": dict(payload.get("metadata") or {}),
        }
        self.repository.upsert("request_assignment", assignment)
        request.setdefault("assignments", []).append(assignment)
        self.repository.upsert("request", request)
        self._record_activity(ctx, request.get("workspace_id"), "reviewer.assigned", request_id=request_id, data={"assignment_id": assignment["id"]})
        self._notify(request.get("workspace_id"), "review_request", f"Review requested for {request['title']}", ctx, request_id=request_id)
        return assignment

    def remove_request_assignment(self, request_id: str, assignment_id: str, ctx: NCP003ExecutionContext) -> None:
        self._permission_check(ctx, "request.assign")
        assignment = self.repository.get("request_assignment", assignment_id)
        if assignment is None or assignment.get("request_id") != request_id:
            raise KeyError("request_assignment_not_found")
        self.repository.delete("request_assignment", assignment_id)
        self._record_activity(ctx, assignment.get("workspace_id"), "reviewer.unassigned", request_id=request_id, data={"assignment_id": assignment_id})

    def request_comments(self, request_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._request_or_404(request_id, ctx)
        return [item for item in self.repository.list("comment") if item.get("request_id") == request_id]

    def add_request_comment(self, request_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "request.comment")
        request = self._request_or_404(request_id, ctx)
        comment = {
            "id": str(payload.get("id") or _new_id("comment")),
            "request_id": request_id,
            "project_id": request.get("project_id"),
            "workspace_id": request.get("workspace_id"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "author_id": ctx.actor_id,
            "body": str(payload["body"]),
            "mentions": list(payload.get("mentions") or []),
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "metadata": dict(payload.get("metadata") or {}),
        }
        self.repository.upsert("comment", comment)
        request.setdefault("comments", []).append(comment)
        self.repository.upsert("request", request)
        self._record_activity(ctx, request.get("workspace_id"), "comment.added", request_id=request_id, data={"comment_id": comment["id"]})
        self._notify(request.get("workspace_id"), "mention", f"Comment added to {request['title']}", ctx, request_id=request_id)
        return comment

    def update_request_comment(self, request_id: str, comment_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "request.comment")
        comment = self.repository.get("comment", comment_id)
        if comment is None or comment.get("request_id") != request_id:
            raise KeyError("request_comment_not_found")
        comment["body"] = str(payload.get("body") or comment["body"])
        comment["mentions"] = list(payload.get("mentions") or comment.get("mentions") or [])
        comment["updated_by"] = ctx.actor_id
        comment["updated_at"] = _now()
        comment["version"] = int(comment.get("version") or 1) + 1
        self.repository.upsert("comment", comment)
        self._record_activity(ctx, comment.get("workspace_id"), "comment.updated", request_id=request_id, data={"comment_id": comment_id})
        return comment

    def delete_request_comment(self, request_id: str, comment_id: str, ctx: NCP003ExecutionContext) -> None:
        self._permission_check(ctx, "request.comment")
        comment = self.repository.get("comment", comment_id)
        if comment is None or comment.get("request_id") != request_id:
            raise KeyError("request_comment_not_found")
        self.repository.delete("comment", comment_id)
        self._record_activity(ctx, comment.get("workspace_id"), "comment.deleted", request_id=request_id, data={"comment_id": comment_id})

    def request_attachments(self, request_id: str, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        self._request_or_404(request_id, ctx)
        return [item for item in self.repository.list("attachment") if item.get("request_id") == request_id]

    def add_request_attachment(self, request_id: str, payload: dict[str, Any], ctx: NCP003ExecutionContext) -> dict[str, Any]:
        self._permission_check(ctx, "attachment.upload")
        request = self._request_or_404(request_id, ctx)
        filename = str(payload["filename"])
        content_type = str(payload.get("content_type") or mimetypes.guess_type(filename)[0] or "application/octet-stream").lower()
        content = payload.get("content")
        if isinstance(content, str):
            raw_bytes = content.encode("utf-8")
        elif isinstance(content, (bytes, bytearray)):
            raw_bytes = bytes(content)
        else:
            raw_bytes = str(payload.get("body") or "").encode("utf-8")
        if not raw_bytes:
            raise ValueError("attachment_rejected")
        size_limit = int(os.environ.get("NOVACODEPRO_ATTACHMENT_SIZE_LIMIT", str(5 * 1024 * 1024)))
        if len(raw_bytes) > size_limit:
            raise ValueError("attachment_rejected")
        if content_type not in ALLOWED_ATTACHMENT_MIME_TYPES or filename.lower().endswith((".exe", ".cmd", ".bat", ".sh", ".js", ".msi", ".apk", ".ipa")) or filename.count(".") > 2:
            quarantine = True
        else:
            quarantine = False
        digest = sha256(raw_bytes).hexdigest()
        attachment = {
            "id": str(payload.get("id") or _new_id("attachment")),
            "request_id": request_id,
            "project_id": request.get("project_id"),
            "workspace_id": request.get("workspace_id"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "filename": filename.replace("/", "_"),
            "content_type": content_type,
            "size": len(raw_bytes),
            "sha256": digest,
            "status": "QUARANTINED" if quarantine else "AVAILABLE",
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "metadata": dict(payload.get("metadata") or {}),
        }
        self.repository.upsert("attachment", attachment)
        request.setdefault("attachments", []).append(attachment)
        self.repository.upsert("request", request)
        self._record_activity(ctx, request.get("workspace_id"), "attachment.uploaded", request_id=request_id, data={"attachment_id": attachment["id"], "status": attachment["status"]})
        if quarantine:
            attachment["blocker"] = "BLOCKED_EXTERNAL_VERIFICATION"
        return attachment

    def get_request_attachment(self, request_id: str, attachment_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any] | None:
        attachment = self.repository.get("attachment", attachment_id)
        if attachment is None or attachment.get("request_id") != request_id or attachment.get("tenant_id") != ctx.tenant_id:
            return None
        return attachment

    def delete_request_attachment(self, request_id: str, attachment_id: str, ctx: NCP003ExecutionContext) -> None:
        self._permission_check(ctx, "attachment.upload")
        attachment = self.get_request_attachment(request_id, attachment_id, ctx)
        if attachment is None:
            raise KeyError("request_attachment_not_found")
        self.repository.delete("attachment", attachment_id)
        self._record_activity(ctx, attachment.get("workspace_id"), "attachment.deleted", request_id=request_id, data={"attachment_id": attachment_id})

    def notifications(self, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        return [item for item in self.repository.list("notification") if item.get("tenant_id") == ctx.tenant_id]

    def read_notification(self, notification_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        notification = self.repository.get("notification", notification_id)
        if notification is None or notification.get("tenant_id") != ctx.tenant_id:
            raise KeyError("notification_not_found")
        notification["read_at"] = _now()
        notification["status"] = "READ"
        notification["updated_by"] = ctx.actor_id
        notification["version"] = int(notification.get("version") or 1) + 1
        self.repository.upsert("notification", notification)
        self._record_activity(ctx, notification.get("workspace_id"), "notification.read", data={"notification_id": notification_id})
        return notification

    def read_all_notifications(self, ctx: NCP003ExecutionContext) -> list[dict[str, Any]]:
        updated = []
        for notification in self.notifications(ctx):
            updated.append(self.read_notification(notification["id"], ctx))
        return updated

    def create_notification(self, workspace_id: str | None, title: str, ctx: NCP003ExecutionContext, *, request_id: str | None = None, project_id: str | None = None, kind: str = "INFO") -> dict[str, Any]:
        notification = {
            "id": _new_id("notification"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": workspace_id or ctx.workspace_id,
            "project_id": project_id,
            "request_id": request_id,
            "title": title,
            "kind": kind,
            "status": "UNREAD",
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "metadata": {},
        }
        self.repository.upsert("notification", notification)
        return notification

    def _project_or_404(self, project_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        project = self.repository.get("project", project_id)
        if project is None:
            raise KeyError("project_not_found")
        if project.get("tenant_id") != ctx.tenant_id:
            raise PermissionError("project_forbidden")
        return project

    def _project_record_or_404(self, kind: str, record_id: str, project_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        record = self.repository.get(kind, record_id)
        if record is None:
            raise KeyError(f"{kind}_not_found")
        if record.get("tenant_id") != ctx.tenant_id or record.get("project_id") != project_id:
            raise PermissionError(f"{kind}_forbidden")
        project = self._project_or_404(project_id, ctx)
        if project.get("status") == "ARCHIVED" and kind in {"project_milestone", "project_work_item", "project_risk"}:
            raise ValueError("project_archived")
        return record

    def _request_or_404(self, request_id: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        request = self.repository.get("request", request_id)
        if request is None:
            raise KeyError("request_not_found")
        if request.get("tenant_id") != ctx.tenant_id:
            raise PermissionError("request_forbidden")
        return request

    def _ensure_membership(self, kind: str, workspace_id: str, user_id: str, ctx: NCP003ExecutionContext, *, role: str = "MEMBER") -> dict[str, Any]:
        for record in self.repository.list(kind):
            if record.get("workspace_id") == workspace_id and record.get("user_id") == user_id:
                return record
        membership = {
            "id": _new_id("membership"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "role": role,
            "status": "ACTIVE",
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "metadata": {},
        }
        self.repository.upsert(kind, membership)
        return membership

    def _upsert_project_member(self, project_id: str, user_id: str, role: str, ctx: NCP003ExecutionContext) -> dict[str, Any]:
        for record in self.repository.list("project_member"):
            if record.get("project_id") == project_id and record.get("user_id") == user_id:
                record["role"] = role
                record["updated_by"] = ctx.actor_id
                record["updated_at"] = _now()
                record["version"] = int(record.get("version") or 1) + 1
                self.repository.upsert("project_member", record)
                return record
        member = {
            "id": _new_id("project-member"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": self._project_or_404(project_id, ctx).get("workspace_id"),
            "project_id": project_id,
            "user_id": user_id,
            "role": role,
            "status": "ACTIVE",
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "metadata": {},
        }
        self.repository.upsert("project_member", member)
        return member

    def _record_activity(self, ctx: NCP003ExecutionContext, workspace_id: str | None, event_type: str, *, request_id: str | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
        event = {
            "id": _new_id("activity"),
            "event_type": event_type,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": workspace_id or ctx.workspace_id,
            "project_id": None,
            "request_id": request_id,
            "resource_type": "activity_event",
            "resource_id": request_id or workspace_id or ctx.correlation_id,
            "action": event_type,
            "previous_state": data.get("previous_status") if data else None,
            "new_state": data.get("new_status") if data else None,
            "timestamp": _now(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "session_id": ctx.session_id,
            "permission": "",
            "policy_decision": "allow",
            "result": "success",
            "error_code": "",
            "evidence_reference": request_id or workspace_id or ctx.correlation_id,
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "version": 1,
            "metadata": dict(data or {}),
        }
        self.repository.upsert("activity_event", event)
        return event

    def _record_workspace_activity(self, workspace_id: str, event_type: str, ctx: NCP003ExecutionContext, *, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._record_activity(ctx, workspace_id, event_type, data=data)

    def _record_project_activity(self, project_id: str, event_type: str, ctx: NCP003ExecutionContext, *, data: dict[str, Any] | None = None) -> dict[str, Any]:
        project = self.repository.get("project", project_id)
        workspace_id = project.get("workspace_id") if project else ctx.workspace_id
        event = self._record_activity(ctx, workspace_id, event_type, request_id=None, data=data)
        event["project_id"] = project_id
        self.repository.upsert("activity_event", event)
        return event

    def _record_request_transition(
        self,
        request_id: str,
        previous_status: str | None,
        new_status: str,
        ctx: NCP003ExecutionContext,
        *,
        reason: str,
        project_id: str | None,
        workspace_id: str | None,
        policy_decision: str = "allow",
    ) -> dict[str, Any]:
        request = self.repository.get("request", request_id) or {}
        transition = {
            "id": _new_id("transition"),
            "request_id": request_id,
            "project_id": project_id,
            "workspace_id": workspace_id or ctx.workspace_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "previous_status": previous_status,
            "new_status": new_status,
            "actor_id": ctx.actor_id,
            "reason": reason,
            "timestamp": _now(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "policy_decision": policy_decision,
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "version": 1,
            "metadata": {"reason": reason},
        }
        self.repository.upsert("request_transition", transition)
        request.setdefault("transitions", []).append(transition)
        request.setdefault("history", []).append(transition)
        request["available_transitions"] = sorted(REQUEST_TRANSITIONS.get(new_status, set()))
        request["status"] = new_status
        request["updated_by"] = ctx.actor_id
        request["version"] = int(request.get("version") or 1) + 1
        self.repository.upsert("request", request)
        self._record_activity(ctx, workspace_id, f"request.{new_status.lower()}", request_id=request_id, data={"request_id": request_id, "previous_status": previous_status, "new_status": new_status})
        return transition

    def _notify(self, workspace_id: str | None, kind: str, title: str, ctx: NCP003ExecutionContext, *, request_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
        notification = {
            "id": _new_id("notification"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": workspace_id or ctx.workspace_id,
            "project_id": project_id,
            "request_id": request_id,
            "kind": kind,
            "title": title,
            "status": "UNREAD",
            "created_at": _now(),
            "updated_at": _now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "version": 1,
            "metadata": {},
        }
        self.repository.upsert("notification", notification)
        return notification
