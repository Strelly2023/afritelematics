from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from afritech.novacodepro.platform import NovaCodeProRepository, _event_envelope, _new_id, _now


REQUIREMENT_TYPES = {
    "BUSINESS",
    "FUNCTIONAL",
    "NON_FUNCTIONAL",
    "SECURITY",
    "PRIVACY",
    "COMPLIANCE",
    "OPERATIONAL",
    "OBSERVABILITY",
    "PERFORMANCE",
    "ACCESSIBILITY",
    "RELIABILITY",
    "AVAILABILITY",
    "RECOVERY",
    "DATA",
    "INTEGRATION",
    "MIGRATION",
    "ROLLBACK",
}

REQUIREMENT_STATUSES = {
    "DRAFT",
    "IN_REVIEW",
    "CHANGES_REQUESTED",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "BASELINED",
    "IMPLEMENTING",
    "VERIFIED",
    "REJECTED",
    "ARCHIVED",
    "SUPERSEDED",
}

REQUIREMENT_SOURCES = {
    "MANUAL",
    "REQUEST",
    "AI_GENERATED",
    "IMPORT",
    "POLICY",
    "REGULATION",
    "INCIDENT",
    "AUDIT",
    "CUSTOMER",
}

REQUIREMENT_PRIORITY = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

CRITERION_TYPES = {
    "GIVEN_WHEN_THEN",
    "CHECKLIST",
    "MEASURABLE_THRESHOLD",
    "MANUAL_VERIFICATION",
    "AUTOMATED_TEST",
    "SECURITY_CONTROL",
    "ACCESSIBILITY_CHECK",
    "OPERATIONAL_CHECK",
}

CRITERION_STATUS = {"DRAFT", "APPROVED", "PASS", "FAIL", "BLOCKED", "WAIVED"}

RELATIONSHIP_TYPES = {
    "PARENT_OF",
    "CHILD_OF",
    "DEPENDS_ON",
    "BLOCKS",
    "CONFLICTS_WITH",
    "DUPLICATES",
    "REFINES",
    "IMPLEMENTS",
    "VERIFIES",
    "DERIVED_FROM",
    "SUPERSEDES",
    "RELATED_TO",
}

REQUIREMENT_TRANSITIONS = {
    "DRAFT": {"IN_REVIEW", "CHANGES_REQUESTED"},
    "IN_REVIEW": {"CHANGES_REQUESTED", "APPROVAL_REQUIRED", "REJECTED"},
    "CHANGES_REQUESTED": {"DRAFT"},
    "APPROVAL_REQUIRED": {"APPROVED", "CHANGES_REQUESTED", "REJECTED"},
    "APPROVED": {"BASELINED", "SUPERSEDED"},
    "BASELINED": {"IMPLEMENTING", "SUPERSEDED"},
    "IMPLEMENTING": {"VERIFIED", "CHANGES_REQUESTED"},
    "VERIFIED": {"ARCHIVED", "SUPERSEDED"},
    "REJECTED": {"ARCHIVED"},
    "ARCHIVED": set(),
    "SUPERSEDED": set(),
}

KNOWLEDGE_TYPES = {
    "GENERAL_DOCUMENT",
    "WIKI_PAGE",
    "ADR",
    "STANDARD",
    "POLICY",
    "RUNBOOK",
    "POSTMORTEM",
    "RELEASE_NOTE",
    "API_DOCUMENTATION",
    "ARCHITECTURE_DOCUMENT",
    "DESIGN_DOCUMENT",
    "LESSON_LEARNED",
    "FAQ",
    "USER_GUIDE",
    "ADMIN_GUIDE",
    "DEVELOPER_GUIDE",
    "OPERATIONS_GUIDE",
    "SECURITY_GUIDE",
    "COMPLIANCE_GUIDE",
}

KNOWLEDGE_STATUSES = {
    "DRAFT",
    "IN_REVIEW",
    "CHANGES_REQUESTED",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "PUBLISHED",
    "ARCHIVED",
    "SUPERSEDED",
    "REJECTED",
}

KNOWLEDGE_VISIBILITY = {"PRIVATE", "WORKSPACE", "ORGANIZATION", "PARTNER", "CUSTOMER", "PUBLIC"}

KNOWLEDGE_CLASSIFICATIONS = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "REGULATED"}

RETRIEVAL_ALLOWED_TYPES = {
    "requirements",
    "acceptance_criteria",
    "knowledge_documents",
    "adrs",
    "runbooks",
    "postmortems",
    "release_notes",
    "standards",
    "policies",
}


def _utcnow() -> str:
    return _now()


def _digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "item"


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _now_datetime() -> datetime:
    return datetime.now(timezone.utc)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def _vectorize(text: str, dimensions: int = 16) -> list[float]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    vector = [0.0] * dimensions
    if not tokens:
        return vector
    for token in tokens:
      digest = hashlib.sha256(token.encode("utf-8")).digest()
      for index in range(dimensions):
          vector[index] += digest[index] / 255.0
    scale = float(len(tokens))
    return [value / scale for value in vector]


@dataclass(frozen=True)
class NCP005ExecutionContext:
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


class NCP005Error(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NovaCodeProNCP005Service:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository
        self.semantic_backend = os.environ.get("NOVACODEPRO_VECTOR_BACKEND", "").strip().lower()
        self._seed_defaults()

    # -- seeding -----------------------------------------------------
    def _seed_defaults(self) -> None:
        if not self.repository.list("knowledge_space"):
            self.repository.upsert(
                "knowledge_space",
                {
                    "id": "workspace-knowledge",
                    "tenant_id": "novatech",
                    "organization_id": "novatech",
                    "workspace_id": "enterprise-product-manager",
                    "project_id": None,
                    "request_id": None,
                    "name": "Workspace Knowledge",
                    "slug": "workspace-knowledge",
                    "description": "Shared requirements and knowledge for NovaCodePro internal teams.",
                    "status": "ACTIVE",
                    "version": 1,
                    "created_by": "system",
                    "updated_by": "system",
                    "created_at": _utcnow(),
                    "updated_at": _utcnow(),
                    "correlation_id": "seed",
                    "causation_id": "seed",
                    "metadata": {"seeded": True},
                    "classification": "INTERNAL",
                    "retention_policy_id": "retain-indefinitely",
                },
            )

    # -- guards ------------------------------------------------------
    def _ensure_permission(self, ctx: NCP005ExecutionContext, permission: str) -> None:
        if permission not in ctx.permissions and ctx.role not in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SYSTEM_ADMIN", "SUPER_ADMIN"}:
            raise NCP005Error("forbidden", f"Missing permission: {permission}", 403)

    def _ensure_tenant(self, ctx: NCP005ExecutionContext, record: dict[str, Any]) -> None:
        if _lower(record.get("tenant_id")) != _lower(ctx.tenant_id):
            raise NCP005Error("cross_tenant_knowledge_forbidden", "Cross-tenant access is forbidden.", 403)

    def _ensure_workspace(self, ctx: NCP005ExecutionContext, record: dict[str, Any]) -> None:
        record_workspace = _lower(record.get("workspace_id"))
        if ctx.workspace_id and record_workspace and record_workspace != _lower(ctx.workspace_id):
            raise NCP005Error("cross_tenant_knowledge_forbidden", "Cross-workspace access is forbidden.", 403)

    def _ensure_project(self, ctx: NCP005ExecutionContext, record: dict[str, Any]) -> None:
        record_project = _lower(record.get("project_id"))
        if ctx.project_id and record_project and record_project != _lower(ctx.project_id):
            raise NCP005Error("cross_tenant_knowledge_forbidden", "Cross-project access is forbidden.", 403)

    def _record(self, kind: str, ctx: NCP005ExecutionContext, payload: dict[str, Any], *, record_id: str | None = None, version: int = 1, status: str = "DRAFT") -> dict[str, Any]:
        now = _utcnow()
        record = {
            "id": record_id or _new_id(kind.replace("_", "-")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "request_id": ctx.request_id,
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
        return record

    def _append_event(self, event_type: str, ctx: NCP005ExecutionContext, *, resource_type: str, resource_id: str, project_id: str | None = None, request_id: str | None = None, previous_state: Any = None, new_state: Any = None, approval_reference: str | None = None, result: str = "SUCCESS", error_code: str = "", evidence_reference: str | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        event = _event_envelope(
            event_type=event_type,
            actor_type="user",
            actor_id=ctx.actor_id,
            tenant_id=ctx.tenant_id,
            organization_id=ctx.organization_id,
            project_id=project_id or ctx.project_id,
            workflow_id=request_id or ctx.request_id,
            correlation_id=ctx.correlation_id,
            causation_id=ctx.causation_id or ctx.correlation_id,
            data={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "previous_state": previous_state,
                "new_state": new_state,
                "approval_reference": approval_reference,
                "result": result,
                "error_code": error_code,
                "evidence_reference": evidence_reference,
                **(extra or {}),
            },
            metadata={"service": "ncp005"},
        )
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
                "correlation_id": event["correlation_id"],
                "causation_id": event["causation_id"],
                "metadata": {
                    "event_type": event_type,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "approval_reference": approval_reference,
                    "evidence_reference": evidence_reference,
                },
                "event_type": event_type,
                "result": result,
                "error_code": error_code,
                "previous_state": previous_state,
                "new_state": new_state,
                "approval_reference": approval_reference,
                "evidence_reference": evidence_reference,
            },
        )
        return event

    def _version_record(self, *, kind: str, entity: dict[str, Any], ctx: NCP005ExecutionContext, version_number: int, content: dict[str, Any], change_summary: str, source_references: list[dict[str, Any]] | None = None, approval_digest: str | None = None) -> dict[str, Any]:
        version = {
            "id": _new_id(f"{kind}-version"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": entity.get("workspace_id") or ctx.workspace_id,
            "project_id": entity.get("project_id") or ctx.project_id,
            "request_id": entity.get("request_id") or ctx.request_id,
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "version": version_number,
            "status": entity.get("status") or "DRAFT",
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": {
                "change_summary": change_summary,
                "approval_digest": approval_digest,
                "source_references": source_references or [],
            },
            "content": content,
            "content_digest": _digest(content),
            "source_type": entity.get("source_type"),
            "source_id": entity.get("source_id"),
            "source_version": entity.get("source_version"),
            "source_uri": entity.get("source_uri"),
            "source_digest": entity.get("source_digest"),
            "created_from_agent_id": entity.get("created_from_agent_id"),
            "created_from_execution_id": entity.get("created_from_execution_id"),
            "created_from_tool_id": entity.get("created_from_tool_id"),
            "human_verified": entity.get("human_verified", False),
            "verification_actor_id": entity.get("verification_actor_id"),
            "verification_timestamp": entity.get("verification_timestamp"),
        }
        self.repository.upsert(f"{kind}_version", version)
        return version

    def _list_kind(self, kind: str, ctx: NCP005ExecutionContext | None = None) -> list[dict[str, Any]]:
        records = self.repository.list(kind)
        if ctx is None:
            return records
        return [record for record in records if _lower(record.get("tenant_id")) == _lower(ctx.tenant_id) and (not ctx.workspace_id or _lower(record.get("workspace_id")) == _lower(ctx.workspace_id))]

    def _get_kind(self, kind: str, record_id: str, ctx: NCP005ExecutionContext | None = None) -> dict[str, Any]:
        record = self.repository.get(kind, record_id)
        if record is None:
            raise NCP005Error(f"{kind}_not_found", f"{kind} not found.", 404)
        if ctx is not None:
            self._ensure_tenant(ctx, record)
            self._ensure_workspace(ctx, record)
        return record

    def _requirement_or_404(self, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        return self._get_kind("requirement", requirement_id, ctx)

    def _set_or_404(self, set_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        return self._get_kind("requirement_set", set_id, ctx)

    def _document_or_404(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        return self._get_kind("knowledge_document", document_id, ctx)

    def _space_or_404(self, space_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        return self._get_kind("knowledge_space", space_id, ctx)

    def _requirement_versions(self, requirement_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        return [version for version in self._list_kind("requirement_version", ctx) if _lower(version.get("requirement_id")) == _lower(requirement_id)]

    def _criterion_versions(self, requirement_id: str, criterion_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        return [criterion for criterion in self._list_kind("acceptance_criterion", ctx) if _lower(criterion.get("requirement_id")) == _lower(requirement_id) and _lower(criterion.get("id")) == _lower(criterion_id)]

    def _document_versions(self, document_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        return [version for version in self._list_kind("knowledge_document_version", ctx) if _lower(version.get("document_id")) == _lower(document_id)]

    def _classification_allows(self, ctx: NCP005ExecutionContext, classification: str) -> bool:
        classification = classification.upper()
        if classification in {"PUBLIC", "INTERNAL"}:
            return True
        if classification == "CONFIDENTIAL":
            return any(permission.startswith("knowledge.") or permission.startswith("requirements.") for permission in ctx.permissions) or ctx.role in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SYSTEM_ADMIN", "SUPER_ADMIN", "AUDITOR", "COMPLIANCE_OFFICER"}
        if classification == "RESTRICTED":
            return ctx.role in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SYSTEM_ADMIN", "SUPER_ADMIN", "AUDITOR", "COMPLIANCE_OFFICER", "SECURITY_ENGINEER"}
        if classification == "REGULATED":
            return ctx.role in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SYSTEM_ADMIN", "SUPER_ADMIN", "COMPLIANCE_OFFICER", "AUDITOR"}
        return False

    def _requirement_search_scope(self, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        return [item for item in self._list_kind("requirement", ctx)]

    def _document_search_scope(self, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        return [item for item in self._list_kind("knowledge_document", ctx) if self._classification_allows(ctx, str(item.get("classification") or "INTERNAL"))]

    def _state_transition(self, current: str, target: str, transitions: dict[str, set[str]]) -> None:
        current = current.upper()
        target = target.upper()
        if target not in transitions.get(current, set()) and target != current:
            raise NCP005Error("invalid_requirement_transition", f"Invalid transition {current} -> {target}.", 409)

    def _latest_requirement_version(self, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any] | None:
        versions = sorted(self._requirement_versions(requirement_id, ctx), key=lambda item: int(item.get("version") or 0), reverse=True)
        return versions[0] if versions else None

    def _latest_document_version(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any] | None:
        versions = sorted(self._document_versions(document_id, ctx), key=lambda item: int(item.get("version") or 0), reverse=True)
        return versions[0] if versions else None

    def _audited_read(self, ctx: NCP005ExecutionContext, resource_type: str, resource_id: str, status: str = "SUCCESS") -> None:
        self._append_event(
            f"{resource_type}.read",
            ctx,
            resource_type=resource_type,
            resource_id=resource_id,
            result=status,
        )

    # -- requirement sets --------------------------------------------
    def list_requirement_sets(self, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.read")
        records = [record for record in self._list_kind("requirement_set", ctx) if _lower(record.get("tenant_id")) == _lower(ctx.tenant_id)]
        return records

    def create_requirement_set(self, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.create")
        set_id = str(payload.get("id") or payload.get("set_id") or _new_id("reqset"))
        record = self._record(
            "requirement_set",
            ctx,
            {
                "id": set_id,
                "name": str(payload.get("name") or payload.get("title") or "Requirement set"),
                "description": str(payload.get("description") or ""),
                "status": str(payload.get("status") or "DRAFT").upper(),
                "classification": str(payload.get("classification") or "INTERNAL").upper(),
                "retention_policy_id": str(payload.get("retention_policy_id") or "retain-indefinitely"),
                "requirements": [],
                "baseline_ids": [],
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=set_id,
        )
        self.repository.upsert("requirement_set", record)
        self._append_event("requirement_set.created", ctx, resource_type="requirement_set", resource_id=set_id, new_state=record["status"])
        return record

    def get_requirement_set(self, set_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.read")
        record = self._set_or_404(set_id, ctx)
        self._audited_read(ctx, "requirement_set", set_id)
        return record

    def update_requirement_set(self, set_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        record = self._set_or_404(set_id, ctx)
        if record.get("status") == "ARCHIVED":
            raise NCP005Error("requirement_baseline_immutable", "Archived requirement sets are immutable.", 409)
        previous = dict(record)
        record["name"] = str(payload.get("name") or record.get("name") or "Requirement set")
        record["description"] = str(payload.get("description") or record.get("description") or "")
        record["classification"] = str(payload.get("classification") or record.get("classification") or "INTERNAL").upper()
        record["retention_policy_id"] = str(payload.get("retention_policy_id") or record.get("retention_policy_id") or "retain-indefinitely")
        record["updated_by"] = ctx.actor_id
        record["updated_at"] = _utcnow()
        record["version"] = int(record.get("version") or 1) + 1
        self.repository.upsert("requirement_set", record)
        self._append_event("requirement_set.updated", ctx, resource_type="requirement_set", resource_id=set_id, previous_state=previous.get("status"), new_state=record.get("status"))
        return record

    def archive_requirement_set(self, set_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.archive")
        record = self._set_or_404(set_id, ctx)
        previous = record.get("status")
        record["status"] = "ARCHIVED"
        record["updated_by"] = ctx.actor_id
        record["updated_at"] = _utcnow()
        record["version"] = int(record.get("version") or 1) + 1
        self.repository.upsert("requirement_set", record)
        self._append_event("requirement_set.archived", ctx, resource_type="requirement_set", resource_id=set_id, previous_state=previous, new_state="ARCHIVED")
        return record

    def add_requirement_to_set(self, set_id: str, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        requirement_set = self._set_or_404(set_id, ctx)
        requirement = self._requirement_or_404(requirement_id, ctx)
        requirement_set.setdefault("requirements", [])
        if requirement_id not in requirement_set["requirements"]:
            requirement_set["requirements"].append(requirement_id)
        requirement_set["updated_by"] = ctx.actor_id
        requirement_set["updated_at"] = _utcnow()
        requirement_set["version"] = int(requirement_set.get("version") or 1) + 1
        self.repository.upsert("requirement_set", requirement_set)
        self._append_event("requirement_set.requirement_added", ctx, resource_type="requirement_set", resource_id=set_id, project_id=requirement.get("project_id"), previous_state=None, new_state=requirement_id, extra={"requirement_id": requirement_id})
        return requirement_set

    def remove_requirement_from_set(self, set_id: str, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        requirement_set = self._set_or_404(set_id, ctx)
        requirement_set["requirements"] = [item for item in _as_list(requirement_set.get("requirements")) if item != requirement_id]
        requirement_set["updated_by"] = ctx.actor_id
        requirement_set["updated_at"] = _utcnow()
        requirement_set["version"] = int(requirement_set.get("version") or 1) + 1
        self.repository.upsert("requirement_set", requirement_set)
        self._append_event("requirement_set.requirement_removed", ctx, resource_type="requirement_set", resource_id=set_id, extra={"requirement_id": requirement_id})
        return requirement_set

    # -- requirements ------------------------------------------------
    def list_requirements(self, ctx: NCP005ExecutionContext, *, requirement_set_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.read")
        records = self._requirement_search_scope(ctx)
        if requirement_set_id:
            records = [item for item in records if _lower(item.get("requirement_set_id")) == _lower(requirement_set_id)]
        return records

    def create_requirement(self, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.create")
        set_id = str(payload.get("requirement_set_id") or payload.get("set_id") or payload.get("requirement_set") or "")
        if not set_id:
            raise NCP005Error("validation_failed", "requirement_set_id is required.", 422)
        requirement_set = self._set_or_404(set_id, ctx)
        if requirement_set.get("status") == "ARCHIVED":
            raise NCP005Error("requirement_baseline_immutable", "Archived requirement sets are immutable.", 409)
        req_id = str(payload.get("id") or payload.get("requirement_id") or _new_id("requirement"))
        requirement = self._record(
            "requirement",
            ctx,
            {
                "id": req_id,
                "requirement_set_id": set_id,
                "title": str(payload.get("title") or payload.get("summary") or "Requirement"),
                "summary": str(payload.get("summary") or payload.get("title") or ""),
                "description": str(payload.get("description") or ""),
                "type": str(payload.get("type") or payload.get("requirement_type") or "FUNCTIONAL").upper(),
                "priority": str(payload.get("priority") or "MEDIUM").upper(),
                "source": str(payload.get("source") or "MANUAL").upper(),
                "status": str(payload.get("status") or ("GENERATED" if str(payload.get("source") or "").upper() == "AI_GENERATED" else "DRAFT")).upper(),
                "classification": str(payload.get("classification") or requirement_set.get("classification") or "INTERNAL").upper(),
                "retention_policy_id": str(payload.get("retention_policy_id") or requirement_set.get("retention_policy_id") or "retain-indefinitely"),
                "content": dict(payload.get("content") or {}),
                "assumptions": _as_list(payload.get("assumptions")),
                "dependencies": _as_list(payload.get("dependencies")),
                "constraints": _as_list(payload.get("constraints")),
                "risks": _as_list(payload.get("risks")),
                "acceptance_criteria_ids": [],
                "relationship_ids": [],
                "traceability_link_ids": [],
                "review_ids": [],
                "approval_ids": [],
                "baseline_ids": [],
                "comment_ids": [],
                "metadata": {
                    **dict(payload.get("metadata") or {}),
                    "request_reference": payload.get("request_id") or ctx.request_id,
                },
                "source_type": str(payload.get("source_type") or "REQUEST").upper(),
                "source_id": str(payload.get("source_id") or ctx.request_id or set_id),
                "source_version": str(payload.get("source_version") or "1"),
                "source_uri": str(payload.get("source_uri") or ""),
                "source_digest": str(payload.get("source_digest") or _digest(payload.get("content") or payload)),
                "created_from_agent_id": payload.get("created_from_agent_id"),
                "created_from_execution_id": payload.get("created_from_execution_id"),
                "created_from_tool_id": payload.get("created_from_tool_id"),
                "human_verified": bool(payload.get("human_verified", False)),
                "verification_actor_id": payload.get("verification_actor_id"),
                "verification_timestamp": payload.get("verification_timestamp"),
            },
            record_id=req_id,
            status=str(payload.get("status") or ("GENERATED" if str(payload.get("source") or "").upper() == "AI_GENERATED" else "DRAFT")).upper(),
        )
        self.repository.upsert("requirement", requirement)
        self._create_requirement_version(requirement, ctx, "Created requirement")
        requirement_set.setdefault("requirements", [])
        if req_id not in requirement_set["requirements"]:
            requirement_set["requirements"].append(req_id)
            requirement_set["version"] = int(requirement_set.get("version") or 1) + 1
            requirement_set["updated_by"] = ctx.actor_id
            requirement_set["updated_at"] = _utcnow()
            self.repository.upsert("requirement_set", requirement_set)
        self._append_event("requirement.created", ctx, resource_type="requirement", resource_id=req_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), new_state=requirement["status"])
        return requirement

    def _create_requirement_version(self, requirement: dict[str, Any], ctx: NCP005ExecutionContext, change_summary: str, *, approval_digest: str | None = None) -> dict[str, Any]:
        version_number = int(requirement.get("version") or 1)
        content = {
            "title": requirement.get("title"),
            "summary": requirement.get("summary"),
            "description": requirement.get("description"),
            "type": requirement.get("type"),
            "priority": requirement.get("priority"),
            "source": requirement.get("source"),
            "status": requirement.get("status"),
            "content": requirement.get("content"),
            "assumptions": requirement.get("assumptions"),
            "dependencies": requirement.get("dependencies"),
            "constraints": requirement.get("constraints"),
            "risks": requirement.get("risks"),
            "acceptance_criteria_ids": requirement.get("acceptance_criteria_ids", []),
            "relationship_ids": requirement.get("relationship_ids", []),
            "traceability_link_ids": requirement.get("traceability_link_ids", []),
        }
        version = self._version_record(
            kind="requirement",
            entity=requirement,
            ctx=ctx,
            version_number=version_number,
            content=content,
            change_summary=change_summary,
            source_references=[{"type": "REQUEST", "id": requirement.get("source_id"), "version": requirement.get("source_version"), "uri": requirement.get("source_uri"), "digest": requirement.get("source_digest")}],
            approval_digest=approval_digest,
        )
        version["requirement_id"] = requirement["id"]
        version["change_summary"] = change_summary
        self.repository.upsert("requirement_version", version)
        requirement["current_version_id"] = version["id"]
        requirement["current_version_number"] = version_number
        requirement["updated_at"] = _utcnow()
        requirement["updated_by"] = ctx.actor_id
        requirement["version"] = version_number
        self.repository.upsert("requirement", requirement)
        return version

    def get_requirement(self, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.read")
        requirement = self._requirement_or_404(requirement_id, ctx)
        self._audited_read(ctx, "requirement", requirement_id)
        return requirement

    def update_requirement(self, requirement_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        requirement = self._requirement_or_404(requirement_id, ctx)
        if requirement.get("status") in {"ARCHIVED", "SUPERSEDED"}:
            raise NCP005Error("requirement_baseline_immutable", "Historical requirements are immutable.", 409)
        previous = dict(requirement)
        requirement["title"] = str(payload.get("title") or requirement.get("title") or "Requirement")
        requirement["summary"] = str(payload.get("summary") or requirement.get("summary") or "")
        requirement["description"] = str(payload.get("description") or requirement.get("description") or "")
        requirement["type"] = str(payload.get("type") or requirement.get("type") or "FUNCTIONAL").upper()
        requirement["priority"] = str(payload.get("priority") or requirement.get("priority") or "MEDIUM").upper()
        requirement["content"] = dict(payload.get("content") or requirement.get("content") or {})
        requirement["assumptions"] = _as_list(payload.get("assumptions") or requirement.get("assumptions"))
        requirement["dependencies"] = _as_list(payload.get("dependencies") or requirement.get("dependencies"))
        requirement["constraints"] = _as_list(payload.get("constraints") or requirement.get("constraints"))
        requirement["risks"] = _as_list(payload.get("risks") or requirement.get("risks"))
        requirement["source_type"] = str(payload.get("source_type") or requirement.get("source_type") or "REQUEST").upper()
        requirement["source_id"] = str(payload.get("source_id") or requirement.get("source_id") or ctx.request_id or "")
        requirement["source_version"] = str(payload.get("source_version") or requirement.get("source_version") or "1")
        requirement["source_uri"] = str(payload.get("source_uri") or requirement.get("source_uri") or "")
        requirement["source_digest"] = str(payload.get("source_digest") or requirement.get("source_digest") or _digest(requirement))
        requirement["status"] = "IN_REVIEW" if requirement.get("status") in {"APPROVED", "BASELINED", "IMPLEMENTING", "VERIFIED"} else str(payload.get("status") or requirement.get("status") or "DRAFT").upper()
        requirement["updated_by"] = ctx.actor_id
        requirement["updated_at"] = _utcnow()
        requirement["version"] = int(requirement.get("version") or 1) + 1
        if previous.get("status") in {"APPROVED", "BASELINED", "IMPLEMENTING", "VERIFIED"} and requirement["status"] == "IN_REVIEW":
            requirement["approval_ids"] = []
            requirement["baseline_ids"] = []
        self.repository.upsert("requirement", requirement)
        self._create_requirement_version(requirement, ctx, str(payload.get("change_summary") or "Updated requirement"))
        self._append_event("requirement.updated", ctx, resource_type="requirement", resource_id=requirement_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), previous_state=previous.get("status"), new_state=requirement["status"])
        return requirement

    def delete_requirement(self, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.archive")
        requirement = self._requirement_or_404(requirement_id, ctx)
        if requirement.get("status") in {"APPROVED", "BASELINED", "VERIFIED"}:
            raise NCP005Error("requirement_baseline_immutable", "Approved requirements cannot be deleted.", 409)
        self.repository.delete("requirement", requirement_id)
        self._append_event("requirement.deleted", ctx, resource_type="requirement", resource_id=requirement_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), previous_state=requirement.get("status"), new_state="DELETED")
        return {"id": requirement_id, "deleted": True}

    def transition_requirement(self, requirement_id: str, target_status: str, ctx: NCP005ExecutionContext, *, reason: str = "", approval_reference: str | None = None) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        requirement = self._requirement_or_404(requirement_id, ctx)
        target_status = target_status.upper()
        self._state_transition(str(requirement.get("status") or "DRAFT"), target_status, REQUIREMENT_TRANSITIONS)
        if target_status == "APPROVED":
            if not any(item.get("status") in {"APPROVED", "PASS"} for item in self.list_requirement_reviews(requirement_id, ctx)) and not approval_reference:
                raise NCP005Error("requirement_approval_required", "A review or approval is required before approval.", 409)
            self._ensure_permission(ctx, "requirements.approve")
        if target_status == "BASELINED":
            self._ensure_permission(ctx, "requirements.baseline")
            if not any(item.get("status") == "APPROVED" for item in self.list_requirement_approvals(requirement_id, ctx)):
                raise NCP005Error("requirement_not_approved", "Requirement must be approved before baselining.", 409)
        previous = requirement.get("status")
        requirement["status"] = target_status
        requirement["updated_by"] = ctx.actor_id
        requirement["updated_at"] = _utcnow()
        requirement["version"] = int(requirement.get("version") or 1) + 1
        self.repository.upsert("requirement", requirement)
        self._create_requirement_version(requirement, ctx, reason or f"Transitioned to {target_status}", approval_digest=approval_reference)
        self._append_event("requirement.transitioned", ctx, resource_type="requirement", resource_id=requirement_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), previous_state=previous, new_state=target_status, approval_reference=approval_reference, extra={"reason": reason})
        return requirement

    def archive_requirement(self, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        return self.transition_requirement(requirement_id, "ARCHIVED", ctx, reason="Archived")

    def restore_requirement(self, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        requirement = self._requirement_or_404(requirement_id, ctx)
        if requirement.get("status") != "ARCHIVED":
            raise NCP005Error("invalid_requirement_transition", "Only archived requirements can be restored.", 409)
        requirement["status"] = "DRAFT"
        requirement["updated_by"] = ctx.actor_id
        requirement["updated_at"] = _utcnow()
        requirement["version"] = int(requirement.get("version") or 1) + 1
        self.repository.upsert("requirement", requirement)
        self._create_requirement_version(requirement, ctx, "Restored requirement")
        self._append_event("requirement.restored", ctx, resource_type="requirement", resource_id=requirement_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), previous_state="ARCHIVED", new_state="DRAFT")
        return requirement

    def list_requirement_versions(self, requirement_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.read")
        requirement = self._requirement_or_404(requirement_id, ctx)
        self._ensure_tenant(ctx, requirement)
        return sorted(self._requirement_versions(requirement_id, ctx), key=lambda item: int(item.get("version") or 0))

    def get_requirement_version(self, requirement_id: str, version_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.read")
        versions = self._requirement_versions(requirement_id, ctx)
        for version in versions:
            if _lower(version.get("id")) == _lower(version_id):
                return version
        raise NCP005Error("requirement_not_found", "Requirement version not found.", 404)

    def create_requirement_version(self, requirement_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        requirement = self._requirement_or_404(requirement_id, ctx)
        self._ensure_permission(ctx, "requirements.update")
        change_summary = str(payload.get("change_summary") or "Version created")
        requirement["content"] = dict(payload.get("content") or requirement.get("content") or {})
        requirement["summary"] = str(payload.get("summary") or requirement.get("summary") or "")
        requirement["description"] = str(payload.get("description") or requirement.get("description") or "")
        requirement["type"] = str(payload.get("type") or requirement.get("type") or "FUNCTIONAL").upper()
        requirement["priority"] = str(payload.get("priority") or requirement.get("priority") or "MEDIUM").upper()
        requirement["status"] = "DRAFT" if requirement.get("status") == "DRAFT" else "IN_REVIEW"
        requirement["version"] = int(requirement.get("version") or 1) + 1
        self.repository.upsert("requirement", requirement)
        version = self._create_requirement_version(requirement, ctx, change_summary)
        self._append_event("requirement.version.created", ctx, resource_type="requirement", resource_id=requirement_id, previous_state=int(version.get("version") or 0) - 1, new_state=version.get("version"))
        return version

    def restore_requirement_version(self, requirement_id: str, version_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        version = self.get_requirement_version(requirement_id, version_id, ctx)
        requirement = self._requirement_or_404(requirement_id, ctx)
        requirement["title"] = version["content"].get("title")
        requirement["summary"] = version["content"].get("summary")
        requirement["description"] = version["content"].get("description")
        requirement["type"] = version["content"].get("type")
        requirement["priority"] = version["content"].get("priority")
        requirement["content"] = dict(version["content"].get("content") or {})
        requirement["assumptions"] = _as_list(version["content"].get("assumptions"))
        requirement["dependencies"] = _as_list(version["content"].get("dependencies"))
        requirement["constraints"] = _as_list(version["content"].get("constraints"))
        requirement["risks"] = _as_list(version["content"].get("risks"))
        requirement["status"] = "IN_REVIEW"
        requirement["version"] = int(requirement.get("version") or 1) + 1
        self.repository.upsert("requirement", requirement)
        self._create_requirement_version(requirement, ctx, f"Restored version {version_id}")
        self._append_event("requirement.version.restored", ctx, resource_type="requirement", resource_id=requirement_id, previous_state=version_id, new_state=requirement["version"])
        return requirement

    def compare_requirement_versions(self, requirement_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        versions = self.list_requirement_versions(requirement_id, ctx)
        if len(versions) < 2:
            return {"requirement_id": requirement_id, "diff": [], "versions": versions}
        left, right = versions[-2], versions[-1]
        diff = []
        for field in ("title", "summary", "description", "type", "priority", "status"):
            if left["content"].get(field) != right["content"].get(field):
                diff.append({"field": field, "before": left["content"].get(field), "after": right["content"].get(field)})
        return {"requirement_id": requirement_id, "diff": diff, "versions": [left, right]}

    # -- reviews and approvals --------------------------------------
    def list_requirement_reviews(self, requirement_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.review")
        return [review for review in self._list_kind("requirement_review", ctx) if _lower(review.get("requirement_id")) == _lower(requirement_id)]

    def create_requirement_review(self, requirement_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.review")
        requirement = self._requirement_or_404(requirement_id, ctx)
        review = self._record(
            "requirement_review",
            ctx,
            {
                "requirement_id": requirement_id,
                "review_type": str(payload.get("review_type") or "PRODUCT").upper(),
                "status": "OPEN",
                "summary": str(payload.get("summary") or ""),
                "comments": _as_list(payload.get("comments")),
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("requirement_review", review)
        requirement.setdefault("review_ids", []).append(review["id"])
        self.repository.upsert("requirement", requirement)
        self._append_event("requirement.review.created", ctx, resource_type="requirement_review", resource_id=review["id"], project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), new_state=review["status"])
        return review

    def complete_requirement_review(self, requirement_id: str, review_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.review")
        review = self._get_kind("requirement_review", review_id, ctx)
        if _lower(review.get("requirement_id")) != _lower(requirement_id):
            raise NCP005Error("requirement_relationship_invalid", "Review does not belong to requirement.", 409)
        review["status"] = str(payload.get("status") or "APPROVED").upper()
        review["comments"] = _as_list(payload.get("comments") or review.get("comments"))
        review["updated_by"] = ctx.actor_id
        review["updated_at"] = _utcnow()
        review["version"] = int(review.get("version") or 1) + 1
        self.repository.upsert("requirement_review", review)
        requirement = self._requirement_or_404(requirement_id, ctx)
        if review["status"] in {"APPROVED", "PASS"} and requirement.get("status") == "IN_REVIEW":
            requirement["status"] = "APPROVAL_REQUIRED"
            self.repository.upsert("requirement", requirement)
        self._append_event("requirement.review.completed", ctx, resource_type="requirement_review", resource_id=review_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), previous_state="OPEN", new_state=review["status"])
        return review

    def list_requirement_approvals(self, requirement_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.approve")
        return [approval for approval in self._list_kind("requirement_approval", ctx) if _lower(approval.get("requirement_id")) == _lower(requirement_id)]

    def create_requirement_approval(self, requirement_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.approve")
        requirement = self._requirement_or_404(requirement_id, ctx)
        approval = self._record(
            "requirement_approval",
            ctx,
            {
                "requirement_id": requirement_id,
                "required_role": str(payload.get("required_role") or "PRODUCT_MANAGER"),
                "requested_by": ctx.actor_id,
                "requested_from": str(payload.get("requested_from") or ""),
                "risk_class": str(payload.get("risk_class") or "MODERATE").upper(),
                "decision": "PENDING",
                "reason": str(payload.get("reason") or ""),
                "conditions": _as_list(payload.get("conditions")),
                "expires_at": payload.get("expires_at"),
                "decided_at": None,
                "approval_reference": payload.get("approval_reference"),
            },
        )
        self.repository.upsert("requirement_approval", approval)
        requirement.setdefault("approval_ids", []).append(approval["id"])
        self.repository.upsert("requirement", requirement)
        self._append_event("requirement.approval.requested", ctx, resource_type="requirement_approval", resource_id=approval["id"], project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), new_state="PENDING")
        return approval

    def approve_requirement_approval(self, requirement_id: str, approval_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.approve")
        approval = self._get_kind("requirement_approval", approval_id, ctx)
        if _lower(approval.get("requirement_id")) != _lower(requirement_id):
            raise NCP005Error("requirement_relationship_invalid", "Approval does not belong to requirement.", 409)
        approval["decision"] = "APPROVED"
        approval["status"] = "APPROVED"
        approval["reason"] = str(payload.get("reason") or approval.get("reason") or "")
        approval["conditions"] = _as_list(payload.get("conditions") or approval.get("conditions"))
        approval["decided_at"] = _utcnow()
        approval["updated_by"] = ctx.actor_id
        approval["updated_at"] = _utcnow()
        approval["version"] = int(approval.get("version") or 1) + 1
        self.repository.upsert("requirement_approval", approval)
        requirement = self._requirement_or_404(requirement_id, ctx)
        requirement["status"] = "APPROVED"
        requirement["updated_at"] = _utcnow()
        requirement["updated_by"] = ctx.actor_id
        requirement["version"] = int(requirement.get("version") or 1) + 1
        self.repository.upsert("requirement", requirement)
        self._create_requirement_version(requirement, ctx, f"Requirement approved by {ctx.actor_id}", approval_digest=approval_id)
        self._append_event("requirement.approved", ctx, resource_type="requirement_approval", resource_id=approval_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), previous_state="PENDING", new_state="APPROVED", approval_reference=approval_id)
        return approval

    def reject_requirement_approval(self, requirement_id: str, approval_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.approve")
        approval = self._get_kind("requirement_approval", approval_id, ctx)
        if _lower(approval.get("requirement_id")) != _lower(requirement_id):
            raise NCP005Error("requirement_relationship_invalid", "Approval does not belong to requirement.", 409)
        approval["decision"] = "REJECTED"
        approval["status"] = "REJECTED"
        approval["reason"] = str(payload.get("reason") or approval.get("reason") or "")
        approval["decided_at"] = _utcnow()
        approval["updated_by"] = ctx.actor_id
        approval["updated_at"] = _utcnow()
        approval["version"] = int(approval.get("version") or 1) + 1
        self.repository.upsert("requirement_approval", approval)
        requirement = self._requirement_or_404(requirement_id, ctx)
        requirement["status"] = "REJECTED"
        requirement["updated_at"] = _utcnow()
        requirement["updated_by"] = ctx.actor_id
        requirement["version"] = int(requirement.get("version") or 1) + 1
        self.repository.upsert("requirement", requirement)
        self._append_event("requirement.rejected", ctx, resource_type="requirement_approval", resource_id=approval_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), previous_state="PENDING", new_state="REJECTED", approval_reference=approval_id)
        return approval

    def request_changes_requirement_approval(self, requirement_id: str, approval_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.review")
        approval = self._get_kind("requirement_approval", approval_id, ctx)
        if _lower(approval.get("requirement_id")) != _lower(requirement_id):
            raise NCP005Error("requirement_relationship_invalid", "Approval does not belong to requirement.", 409)
        approval["decision"] = "CHANGES_REQUESTED"
        approval["status"] = "CHANGES_REQUESTED"
        approval["reason"] = str(payload.get("reason") or approval.get("reason") or "")
        approval["decided_at"] = _utcnow()
        approval["updated_by"] = ctx.actor_id
        approval["updated_at"] = _utcnow()
        approval["version"] = int(approval.get("version") or 1) + 1
        self.repository.upsert("requirement_approval", approval)
        requirement = self._requirement_or_404(requirement_id, ctx)
        requirement["status"] = "CHANGES_REQUESTED"
        requirement["updated_at"] = _utcnow()
        requirement["updated_by"] = ctx.actor_id
        requirement["version"] = int(requirement.get("version") or 1) + 1
        self.repository.upsert("requirement", requirement)
        self._append_event("requirement.changes_requested", ctx, resource_type="requirement_approval", resource_id=approval_id, project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), previous_state="PENDING", new_state="CHANGES_REQUESTED", approval_reference=approval_id)
        return approval

    # -- acceptance criteria ----------------------------------------
    def list_acceptance_criteria(self, requirement_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.read")
        return [criterion for criterion in self._list_kind("acceptance_criterion", ctx) if _lower(criterion.get("requirement_id")) == _lower(requirement_id)]

    def create_acceptance_criterion(self, requirement_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        requirement = self._requirement_or_404(requirement_id, ctx)
        criterion = self._record(
            "acceptance_criterion",
            ctx,
            {
                "requirement_id": requirement_id,
                "description": str(payload.get("description") or ""),
                "criterion_type": str(payload.get("criterion_type") or "CHECKLIST").upper(),
                "verification_method": str(payload.get("verification_method") or "MANUAL_VERIFICATION").upper(),
                "expected_result": str(payload.get("expected_result") or ""),
                "status": str(payload.get("status") or "DRAFT").upper(),
                "linked_test_ids": _as_list(payload.get("linked_test_ids")),
                "linked_evidence_ids": _as_list(payload.get("linked_evidence_ids")),
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("acceptance_criterion", criterion)
        requirement.setdefault("acceptance_criteria_ids", []).append(criterion["id"])
        self.repository.upsert("requirement", requirement)
        self._append_event("acceptance_criterion.created", ctx, resource_type="acceptance_criterion", resource_id=criterion["id"], project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), new_state=criterion["status"])
        return criterion

    def update_acceptance_criterion(self, requirement_id: str, criterion_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        criterion = self._get_kind("acceptance_criterion", criterion_id, ctx)
        if _lower(criterion.get("requirement_id")) != _lower(requirement_id):
            raise NCP005Error("requirement_relationship_invalid", "Criterion does not belong to requirement.", 409)
        previous = criterion.get("status")
        criterion["description"] = str(payload.get("description") or criterion.get("description") or "")
        criterion["criterion_type"] = str(payload.get("criterion_type") or criterion.get("criterion_type") or "CHECKLIST").upper()
        criterion["verification_method"] = str(payload.get("verification_method") or criterion.get("verification_method") or "MANUAL_VERIFICATION").upper()
        criterion["expected_result"] = str(payload.get("expected_result") or criterion.get("expected_result") or "")
        criterion["status"] = str(payload.get("status") or criterion.get("status") or "DRAFT").upper()
        criterion["linked_test_ids"] = _as_list(payload.get("linked_test_ids") or criterion.get("linked_test_ids"))
        criterion["linked_evidence_ids"] = _as_list(payload.get("linked_evidence_ids") or criterion.get("linked_evidence_ids"))
        criterion["updated_at"] = _utcnow()
        criterion["updated_by"] = ctx.actor_id
        criterion["version"] = int(criterion.get("version") or 1) + 1
        self.repository.upsert("acceptance_criterion", criterion)
        self._append_event("acceptance_criterion.updated", ctx, resource_type="acceptance_criterion", resource_id=criterion_id, project_id=criterion.get("project_id"), request_id=criterion.get("request_id"), previous_state=previous, new_state=criterion["status"])
        return criterion

    def delete_acceptance_criterion(self, requirement_id: str, criterion_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.update")
        criterion = self._get_kind("acceptance_criterion", criterion_id, ctx)
        if _lower(criterion.get("requirement_id")) != _lower(requirement_id):
            raise NCP005Error("requirement_relationship_invalid", "Criterion does not belong to requirement.", 409)
        self.repository.delete("acceptance_criterion", criterion_id)
        self._append_event("acceptance_criterion.deleted", ctx, resource_type="acceptance_criterion", resource_id=criterion_id, project_id=criterion.get("project_id"), request_id=criterion.get("request_id"), previous_state=criterion.get("status"), new_state="DELETED")
        return {"id": criterion_id, "deleted": True}

    # -- comments ----------------------------------------------------
    def list_requirement_comments(self, requirement_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.read")
        return [comment for comment in self._list_kind("requirement_comment", ctx) if _lower(comment.get("requirement_id")) == _lower(requirement_id)]

    def add_requirement_comment(self, requirement_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.review")
        requirement = self._requirement_or_404(requirement_id, ctx)
        comment = self._record(
            "requirement_comment",
            ctx,
            {
                "requirement_id": requirement_id,
                "body": str(payload.get("body") or ""),
                "edited": False,
                "mentions": _as_list(payload.get("mentions")),
                "deleted": False,
                "status": "ACTIVE",
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("requirement_comment", comment)
        requirement.setdefault("comment_ids", []).append(comment["id"])
        self.repository.upsert("requirement", requirement)
        self._append_event("requirement.comment.added", ctx, resource_type="requirement_comment", resource_id=comment["id"], project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), new_state="ACTIVE")
        return comment

    def update_requirement_comment(self, requirement_id: str, comment_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.review")
        comment = self._get_kind("requirement_comment", comment_id, ctx)
        if _lower(comment.get("requirement_id")) != _lower(requirement_id):
            raise NCP005Error("requirement_relationship_invalid", "Comment does not belong to requirement.", 409)
        comment["body"] = str(payload.get("body") or comment.get("body") or "")
        comment["mentions"] = _as_list(payload.get("mentions") or comment.get("mentions"))
        comment["edited"] = True
        comment["updated_at"] = _utcnow()
        comment["updated_by"] = ctx.actor_id
        comment["version"] = int(comment.get("version") or 1) + 1
        self.repository.upsert("requirement_comment", comment)
        self._append_event("requirement.comment.updated", ctx, resource_type="requirement_comment", resource_id=comment_id, project_id=comment.get("project_id"), request_id=comment.get("request_id"))
        return comment

    def delete_requirement_comment(self, requirement_id: str, comment_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.review")
        comment = self._get_kind("requirement_comment", comment_id, ctx)
        if _lower(comment.get("requirement_id")) != _lower(requirement_id):
            raise NCP005Error("requirement_relationship_invalid", "Comment does not belong to requirement.", 409)
        comment["deleted"] = True
        comment["updated_at"] = _utcnow()
        comment["updated_by"] = ctx.actor_id
        comment["status"] = "DELETED"
        self.repository.upsert("requirement_comment", comment)
        self._append_event("requirement.comment.deleted", ctx, resource_type="requirement_comment", resource_id=comment_id, project_id=comment.get("project_id"), request_id=comment.get("request_id"), new_state="DELETED")
        return comment

    # -- relationships ------------------------------------------------
    def list_requirement_relationships(self, requirement_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.traceability")
        return [link for link in self._list_kind("requirement_relationship", ctx) if _lower(link.get("source_id")) == _lower(requirement_id) or _lower(link.get("target_id")) == _lower(requirement_id)]

    def _relationship_cycle(self, source_id: str, target_id: str, ctx: NCP005ExecutionContext) -> bool:
        if _lower(source_id) == _lower(target_id):
            return True
        adjacency: dict[str, set[str]] = {}
        for rel in self._list_kind("requirement_relationship", ctx):
            adjacency.setdefault(_lower(rel.get("source_id")), set()).add(_lower(rel.get("target_id")))
        adjacency.setdefault(_lower(source_id), set()).add(_lower(target_id))
        stack = [_lower(target_id)]
        seen: set[str] = set()
        while stack:
            node = stack.pop()
            if node == _lower(source_id):
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adjacency.get(node, set()))
        return False

    def create_requirement_relationship(self, requirement_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.traceability")
        requirement = self._requirement_or_404(requirement_id, ctx)
        target_id = str(payload.get("target_id") or "")
        if not target_id:
            raise NCP005Error("traceability_target_not_found", "Target requirement is required.", 404)
        target = self._requirement_or_404(target_id, ctx)
        relationship = str(payload.get("relationship") or "RELATED_TO").upper()
        if relationship not in RELATIONSHIP_TYPES:
            raise NCP005Error("requirement_relationship_invalid", "Unsupported requirement relationship.", 400)
        if relationship != "RELATED_TO" and self._relationship_cycle(requirement_id, target_id, ctx):
            raise NCP005Error("traceability_cycle_detected", "Relationship creates a dependency cycle.", 409)
        record = self._record(
            "requirement_relationship",
            ctx,
            {
                "source_id": requirement_id,
                "target_id": target_id,
                "relationship": relationship,
                "status": "ACTIVE",
                "confidence": float(payload.get("confidence") or 1.0),
                "verification_status": str(payload.get("verification_status") or "UNVERIFIED"),
                "creation_method": str(payload.get("creation_method") or "manual"),
                "evidence_reference": payload.get("evidence_reference"),
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("requirement_relationship", record)
        requirement.setdefault("relationship_ids", []).append(record["id"])
        self.repository.upsert("requirement", requirement)
        self._append_event("requirement.relationship.created", ctx, resource_type="requirement_relationship", resource_id=record["id"], project_id=requirement.get("project_id"), request_id=requirement.get("request_id"), new_state=relationship, extra={"target_id": target["id"]})
        return record

    def delete_requirement_relationship(self, relationship_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.traceability")
        record = self._get_kind("requirement_relationship", relationship_id, ctx)
        self.repository.delete("requirement_relationship", relationship_id)
        self._append_event("requirement.relationship.deleted", ctx, resource_type="requirement_relationship", resource_id=relationship_id, project_id=record.get("project_id"), request_id=record.get("request_id"), previous_state=record.get("relationship"), new_state="DELETED")
        return {"id": relationship_id, "deleted": True}

    # -- baselines ---------------------------------------------------
    def list_requirement_baselines(self, ctx: NCP005ExecutionContext, *, set_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.baseline")
        records = self._list_kind("requirement_baseline", ctx)
        if set_id:
            records = [baseline for baseline in records if _lower(baseline.get("requirement_set_id")) == _lower(set_id)]
        return records

    def create_requirement_baseline(self, set_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.baseline")
        requirement_set = self._set_or_404(set_id, ctx)
        requirement_ids = _as_list(payload.get("requirement_ids") or requirement_set.get("requirements") or [])
        requirement_versions = []
        for requirement_id in requirement_ids:
            requirement = self._requirement_or_404(requirement_id, ctx)
            current_version = self._latest_requirement_version(requirement_id, ctx)
            if current_version is None:
                raise NCP005Error("requirement_not_found", "Requirement version missing.", 404)
            requirement_versions.append(
                {
                    "requirement_id": requirement_id,
                    "requirement_version_id": current_version["id"],
                    "requirement_version": current_version["version"],
                    "acceptance_criteria_versions": [
                        {"criterion_id": criterion["id"], "version": criterion.get("version", 1), "status": criterion.get("status")}
                        for criterion in self.list_acceptance_criteria(requirement_id, ctx)
                    ],
                    "approval_references": [approval["id"] for approval in self.list_requirement_approvals(requirement_id, ctx) if approval.get("decision") == "APPROVED"],
                    "timestamp": _utcnow(),
                }
            )
        baseline = self._record(
            "requirement_baseline",
            ctx,
            {
                "requirement_set_id": set_id,
                "name": str(payload.get("name") or f"{requirement_set.get('name') or 'Requirement'} baseline"),
                "status": "DRAFT",
                "requirement_versions": requirement_versions,
                "content_digest": _digest(requirement_versions),
                "approval_references": [],
                "snapshot": requirement_versions,
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("requirement_baseline", baseline)
        requirement_set.setdefault("baseline_ids", []).append(baseline["id"])
        self.repository.upsert("requirement_set", requirement_set)
        self._append_event("requirement.baseline.created", ctx, resource_type="requirement_baseline", resource_id=baseline["id"], new_state=baseline["status"])
        return baseline

    def activate_requirement_baseline(self, baseline_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.baseline")
        baseline = self._get_kind("requirement_baseline", baseline_id, ctx)
        if baseline.get("status") not in {"DRAFT", "APPROVED"}:
            raise NCP005Error("requirement_baseline_immutable", "Baseline cannot be activated.", 409)
        baseline["status"] = "ACTIVE"
        baseline["updated_by"] = ctx.actor_id
        baseline["updated_at"] = _utcnow()
        baseline["version"] = int(baseline.get("version") or 1) + 1
        self.repository.upsert("requirement_baseline", baseline)
        self._append_event("requirement.baseline.activated", ctx, resource_type="requirement_baseline", resource_id=baseline_id, previous_state="APPROVED", new_state="ACTIVE")
        return baseline

    def supersede_requirement_baseline(self, baseline_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.baseline")
        baseline = self._get_kind("requirement_baseline", baseline_id, ctx)
        baseline["status"] = "SUPERSEDED"
        baseline["updated_by"] = ctx.actor_id
        baseline["updated_at"] = _utcnow()
        baseline["version"] = int(baseline.get("version") or 1) + 1
        self.repository.upsert("requirement_baseline", baseline)
        self._append_event("requirement.baseline.superseded", ctx, resource_type="requirement_baseline", resource_id=baseline_id, previous_state="ACTIVE", new_state="SUPERSEDED")
        return baseline

    # -- traceability ------------------------------------------------
    def list_traceability_links(self, ctx: NCP005ExecutionContext, *, resource_type: str | None = None, resource_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "requirements.traceability")
        links = self._list_kind("traceability_link", ctx)
        if resource_type:
            links = [link for link in links if _lower(link.get("source_type")) == _lower(resource_type) or _lower(link.get("target_type")) == _lower(resource_type)]
        if resource_id:
            links = [link for link in links if _lower(link.get("source_id")) == _lower(resource_id) or _lower(link.get("target_id")) == _lower(resource_id)]
        return links

    def create_traceability_link(self, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.traceability")
        source_type = str(payload.get("source_type") or "").upper()
        target_type = str(payload.get("target_type") or "").upper()
        relationship = str(payload.get("relationship") or "DERIVED_FROM").upper()
        if source_type not in {"REQUEST", "REQUIREMENT", "ACCEPTANCE_CRITERION", "ARCHITECTURE_DECISION", "ARCHITECTURE_COMPONENT", "DESIGN_ARTIFACT", "PROJECT", "WORK_ITEM", "CODE_COMMIT", "CODE_FILE", "API_CONTRACT", "DATABASE_MIGRATION", "TEST_CASE", "TEST_RUN", "SECURITY_CONTROL", "SECURITY_FINDING", "POLICY", "APPROVAL", "EVIDENCE", "RELEASE", "ARTIFACT", "DEPLOYMENT", "INCIDENT", "RUNBOOK"}:
            raise NCP005Error("traceability_target_not_found", "Unsupported traceability source type.", 400)
        if target_type not in {"REQUEST", "REQUIREMENT", "ACCEPTANCE_CRITERION", "ARCHITECTURE_DECISION", "ARCHITECTURE_COMPONENT", "DESIGN_ARTIFACT", "PROJECT", "WORK_ITEM", "CODE_COMMIT", "CODE_FILE", "API_CONTRACT", "DATABASE_MIGRATION", "TEST_CASE", "TEST_RUN", "SECURITY_CONTROL", "SECURITY_FINDING", "POLICY", "APPROVAL", "EVIDENCE", "RELEASE", "ARTIFACT", "DEPLOYMENT", "INCIDENT", "RUNBOOK"}:
            raise NCP005Error("traceability_target_not_found", "Unsupported traceability target type.", 400)
        if relationship not in {"DERIVED_FROM", "SATISFIES", "IMPLEMENTS", "VERIFIES", "VALIDATES", "DEPENDS_ON", "CONFLICTS_WITH", "SUPERSEDES", "MITIGATES", "APPROVED_BY", "EVIDENCED_BY", "RELEASED_IN", "DEPLOYED_AS", "OPERATED_BY"}:
            raise NCP005Error("traceability_link_invalid", "Unsupported traceability relationship.", 400)
        source_id = str(payload.get("source_id") or "")
        target_id = str(payload.get("target_id") or "")
        if not source_id or not target_id:
            raise NCP005Error("traceability_target_not_found", "Source and target are required.", 404)
        link = self._record(
            "traceability_link",
            ctx,
            {
                "source_type": source_type,
                "source_id": source_id,
                "target_type": target_type,
                "target_id": target_id,
                "relationship": relationship,
                "status": str(payload.get("status") or "ACTIVE"),
                "confidence": float(payload.get("confidence") or 1.0),
                "verification_status": str(payload.get("verification_status") or "UNVERIFIED"),
                "creation_method": str(payload.get("creation_method") or "manual"),
                "evidence_reference": payload.get("evidence_reference"),
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("traceability_link", link)
        self._append_event("traceability.link.created", ctx, resource_type="traceability_link", resource_id=link["id"], new_state=relationship)
        return link

    def delete_traceability_link(self, link_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.traceability")
        link = self._get_kind("traceability_link", link_id, ctx)
        self.repository.delete("traceability_link", link_id)
        self._append_event("traceability.link.deleted", ctx, resource_type="traceability_link", resource_id=link_id, previous_state=link.get("relationship"), new_state="DELETED")
        return {"id": link_id, "deleted": True}

    def traceability_resource(self, resource_type: str, resource_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.traceability")
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

    def calculate_traceability_coverage(self, ctx: NCP005ExecutionContext, *, set_id: str | None = None) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.traceability")
        requirements = self.list_requirements(ctx, requirement_set_id=set_id)
        total = len(requirements)
        criteria_covered = 0
        architecture_covered = 0
        implementation_covered = 0
        tests_covered = 0
        controls_covered = 0
        evidence_covered = 0
        release_covered = 0
        deployment_covered = 0
        gaps: list[dict[str, Any]] = []
        for requirement in requirements:
            criteria = self.list_acceptance_criteria(requirement["id"], ctx)
            links = self.list_traceability_links(ctx, resource_id=requirement["id"])
            if criteria:
                criteria_covered += 1
            if any(link.get("target_type") in {"ARCHITECTURE_DECISION", "ARCHITECTURE_COMPONENT"} for link in links):
                architecture_covered += 1
            if any(link.get("target_type") in {"WORK_ITEM", "CODE_COMMIT", "CODE_FILE"} for link in links):
                implementation_covered += 1
            if any(link.get("target_type") in {"TEST_CASE", "TEST_RUN"} for link in links):
                tests_covered += 1
            if any(link.get("target_type") in {"SECURITY_CONTROL", "SECURITY_FINDING"} for link in links):
                controls_covered += 1
            if any(link.get("target_type") == "EVIDENCE" for link in links):
                evidence_covered += 1
            if any(link.get("target_type") in {"RELEASE", "ARTIFACT"} for link in links):
                release_covered += 1
            if any(link.get("target_type") == "DEPLOYMENT" for link in links):
                deployment_covered += 1
            if not criteria:
                gaps.append({"requirement_id": requirement["id"], "gap": "missing_acceptance_criteria"})
        denominator = max(total, 1)
        coverage = {
            "coverage_id": _new_id("coverage"),
            "requirements_with_acceptance_criteria": criteria_covered / denominator,
            "requirements_with_architecture_coverage": architecture_covered / denominator,
            "requirements_with_implementation_coverage": implementation_covered / denominator,
            "requirements_with_tests": tests_covered / denominator,
            "requirements_with_security_controls": controls_covered / denominator,
            "requirements_with_evidence": evidence_covered / denominator,
            "requirements_in_release": release_covered / denominator,
            "requirements_verified_in_deployment": deployment_covered / denominator,
        }
        numeric_values = [value for key, value in coverage.items() if key != "coverage_id"]
        coverage["coverage_ratio"] = sum(numeric_values) / max(len(numeric_values), 1)
        snapshot = self._record(
            "traceability_snapshot",
            ctx,
            {
                "set_id": set_id,
                "coverage": coverage,
                "gap_count": len(gaps),
                "requirement_count": total,
                "gaps": gaps,
                "metadata": {"calculated_at": _utcnow()},
            },
        )
        self.repository.upsert("traceability_snapshot", snapshot)
        self._append_event("traceability.coverage.calculated", ctx, resource_type="traceability_snapshot", resource_id=snapshot["id"], new_state=coverage)
        return {"snapshot": snapshot, "coverage": coverage, "gaps": gaps}

    # -- knowledge spaces --------------------------------------------
    def list_knowledge_spaces(self, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.read")
        return self._list_kind("knowledge_space", ctx)

    def create_knowledge_space(self, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.create")
        space = self._record(
            "knowledge_space",
            ctx,
            {
                "id": str(payload.get("id") or payload.get("space_id") or _new_id("space")),
                "name": str(payload.get("name") or "Knowledge Space"),
                "slug": str(payload.get("slug") or _slug(str(payload.get("name") or "knowledge-space"))),
                "description": str(payload.get("description") or ""),
                "status": str(payload.get("status") or "ACTIVE").upper(),
                "classification": str(payload.get("classification") or "INTERNAL").upper(),
                "visibility": str(payload.get("visibility") or "WORKSPACE").upper(),
                "retention_policy_id": str(payload.get("retention_policy_id") or "retain-indefinitely"),
                "metadata": dict(payload.get("metadata") or {}),
            },
            record_id=str(payload.get("id") or payload.get("space_id") or _new_id("space")),
            status=str(payload.get("status") or "ACTIVE").upper(),
        )
        self.repository.upsert("knowledge_space", space)
        self._append_event("knowledge.space.created", ctx, resource_type="knowledge_space", resource_id=space["id"], new_state=space["status"])
        return space

    def get_knowledge_space(self, space_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.read")
        return self._space_or_404(space_id, ctx)

    def update_knowledge_space(self, space_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        space = self._space_or_404(space_id, ctx)
        previous = dict(space)
        space["name"] = str(payload.get("name") or space.get("name") or "Knowledge Space")
        space["description"] = str(payload.get("description") or space.get("description") or "")
        space["classification"] = str(payload.get("classification") or space.get("classification") or "INTERNAL").upper()
        space["visibility"] = str(payload.get("visibility") or space.get("visibility") or "WORKSPACE").upper()
        space["retention_policy_id"] = str(payload.get("retention_policy_id") or space.get("retention_policy_id") or "retain-indefinitely")
        space["updated_by"] = ctx.actor_id
        space["updated_at"] = _utcnow()
        space["version"] = int(space.get("version") or 1) + 1
        self.repository.upsert("knowledge_space", space)
        self._append_event("knowledge.space.updated", ctx, resource_type="knowledge_space", resource_id=space_id, previous_state=previous.get("status"), new_state=space.get("status"))
        return space

    def archive_knowledge_space(self, space_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.archive")
        space = self._space_or_404(space_id, ctx)
        space["status"] = "ARCHIVED"
        space["updated_by"] = ctx.actor_id
        space["updated_at"] = _utcnow()
        space["version"] = int(space.get("version") or 1) + 1
        self.repository.upsert("knowledge_space", space)
        self._append_event("knowledge.space.archived", ctx, resource_type="knowledge_space", resource_id=space_id, previous_state="ACTIVE", new_state="ARCHIVED")
        return space

    # -- knowledge documents ----------------------------------------
    def list_documents(self, ctx: NCP005ExecutionContext, *, space_id: str | None = None, content_type: str | None = None) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.read")
        documents = [doc for doc in self._document_search_scope(ctx)]
        if space_id:
            documents = [doc for doc in documents if _lower(doc.get("space_id")) == _lower(space_id)]
        if content_type:
            documents = [doc for doc in documents if _lower(doc.get("content_type")) == _lower(content_type)]
        return documents

    def create_document(self, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.create")
        space_id = str(payload.get("space_id") or payload.get("knowledge_space_id") or "")
        if not space_id:
            raise NCP005Error("knowledge_space_not_found", "space_id is required.", 404)
        space = self._space_or_404(space_id, ctx)
        classification = str(payload.get("classification") or space.get("classification") or "INTERNAL").upper()
        if classification not in KNOWLEDGE_CLASSIFICATIONS:
            raise NCP005Error("knowledge_classification_forbidden", "Unsupported knowledge classification.", 403)
        if not self._classification_allows(ctx, classification):
            raise NCP005Error("knowledge_classification_forbidden", "Actor cannot access this classification.", 403)
        document_id = str(payload.get("id") or payload.get("document_id") or _new_id("doc"))
        document = self._record(
            "knowledge_document",
            ctx,
            {
                "id": document_id,
                "space_id": space_id,
                "title": str(payload.get("title") or "Knowledge Document"),
                "summary": str(payload.get("summary") or ""),
                "body": str(payload.get("body") or payload.get("content") or ""),
                "structured_content": dict(payload.get("structured_content") or {}),
                "content_type": str(payload.get("content_type") or "GENERAL_DOCUMENT").upper(),
                "source_format": str(payload.get("source_format") or "MANUAL"),
                "status": str(payload.get("status") or "DRAFT").upper(),
                "visibility": str(payload.get("visibility") or "WORKSPACE").upper(),
                "classification": classification,
                "retention_policy_id": str(payload.get("retention_policy_id") or space.get("retention_policy_id") or "retain-indefinitely"),
                "tags": _as_list(payload.get("tags")),
                "section_ids": [],
                "comment_ids": [],
                "review_ids": [],
                "approval_ids": [],
                "citation_ids": [],
                "relationship_ids": [],
                "attachment_ids": [],
                "metadata": dict(payload.get("metadata") or {}),
                "source_type": str(payload.get("source_type") or "MANUAL").upper(),
                "source_id": str(payload.get("source_id") or ctx.request_id or ctx.project_id or ""),
                "source_version": str(payload.get("source_version") or "1"),
                "source_uri": str(payload.get("source_uri") or ""),
                "source_digest": str(payload.get("source_digest") or _digest(payload.get("body") or payload.get("content") or payload)),
                "created_from_agent_id": payload.get("created_from_agent_id"),
                "created_from_execution_id": payload.get("created_from_execution_id"),
                "created_from_tool_id": payload.get("created_from_tool_id"),
                "human_verified": bool(payload.get("human_verified", False)),
                "verification_actor_id": payload.get("verification_actor_id"),
                "verification_timestamp": payload.get("verification_timestamp"),
            },
            record_id=document_id,
            status=str(payload.get("status") or "DRAFT").upper(),
        )
        self.repository.upsert("knowledge_document", document)
        self._create_document_version(document, ctx, "Created document")
        self._create_embedding_record(document, ctx)
        self._append_event("knowledge.document.created", ctx, resource_type="knowledge_document", resource_id=document_id, new_state=document["status"])
        return document

    def _create_document_version(self, document: dict[str, Any], ctx: NCP005ExecutionContext, change_summary: str, *, approval_digest: str | None = None) -> dict[str, Any]:
        version_number = int(document.get("version") or 1)
        version = self._version_record(
            kind="knowledge_document",
            entity=document,
            ctx=ctx,
            version_number=version_number,
            content={
                "title": document.get("title"),
                "summary": document.get("summary"),
                "body": document.get("body"),
                "structured_content": document.get("structured_content"),
                "content_type": document.get("content_type"),
                "source_format": document.get("source_format"),
                "status": document.get("status"),
                "visibility": document.get("visibility"),
                "classification": document.get("classification"),
                "tags": document.get("tags"),
                "citation_ids": document.get("citation_ids"),
                "relationship_ids": document.get("relationship_ids"),
            },
            change_summary=change_summary,
            source_references=[{"type": document.get("source_type"), "id": document.get("source_id"), "version": document.get("source_version"), "uri": document.get("source_uri"), "digest": document.get("source_digest")}],
            approval_digest=approval_digest,
        )
        version["document_id"] = document["id"]
        version["change_summary"] = change_summary
        self.repository.upsert("knowledge_document_version", version)
        document["current_version_id"] = version["id"]
        document["current_version_number"] = version_number
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        document["version"] = version_number
        self.repository.upsert("knowledge_document", document)
        return version

    def _create_embedding_record(self, document: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        text = f"{document.get('title')} {document.get('summary')} {document.get('body')}"
        embedding = _vectorize(text)
        record = self._record(
            "knowledge_embedding_record",
            ctx,
            {
                "document_id": document["id"],
                "document_version_id": document.get("current_version_id"),
                "section_id": "body",
                "embedding_provider": self.semantic_backend or "deterministic-local",
                "embedding_model": "deterministic-hash-16",
                "embedding_version": 1,
                "content_digest": _digest(text),
                "vector_reference": embedding,
                "classification": document.get("classification"),
            },
        )
        self.repository.upsert("knowledge_embedding_record", record)
        return record

    def get_document(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.read")
        document = self._document_or_404(document_id, ctx)
        if not self._classification_allows(ctx, str(document.get("classification") or "INTERNAL")):
            raise NCP005Error("knowledge_document_forbidden", "Document is not accessible.", 403)
        self._audited_read(ctx, "knowledge_document", document_id)
        return document

    def update_document(self, document_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        document = self._document_or_404(document_id, ctx)
        if not self._classification_allows(ctx, str(document.get("classification") or "INTERNAL")):
            raise NCP005Error("knowledge_document_forbidden", "Document is not accessible.", 403)
        if document.get("status") in {"PUBLISHED", "ARCHIVED"}:
            raise NCP005Error("knowledge_publication_forbidden", "Published documents are edited via draft successors.", 409)
        document["title"] = str(payload.get("title") or document.get("title") or "Knowledge Document")
        document["summary"] = str(payload.get("summary") or document.get("summary") or "")
        document["body"] = str(payload.get("body") or payload.get("content") or document.get("body") or "")
        document["structured_content"] = dict(payload.get("structured_content") or document.get("structured_content") or {})
        document["content_type"] = str(payload.get("content_type") or document.get("content_type") or "GENERAL_DOCUMENT").upper()
        document["source_format"] = str(payload.get("source_format") or document.get("source_format") or "MANUAL")
        document["visibility"] = str(payload.get("visibility") or document.get("visibility") or "WORKSPACE").upper()
        document["classification"] = str(payload.get("classification") or document.get("classification") or "INTERNAL").upper()
        document["tags"] = _as_list(payload.get("tags") or document.get("tags"))
        document["status"] = "IN_REVIEW" if document.get("status") in {"PUBLISHED", "APPROVED"} else str(payload.get("status") or document.get("status") or "DRAFT").upper()
        document["version"] = int(document.get("version") or 1) + 1
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        self.repository.upsert("knowledge_document", document)
        self._create_document_version(document, ctx, str(payload.get("change_summary") or "Updated document"))
        self._create_embedding_record(document, ctx)
        self._append_event("knowledge.document.updated", ctx, resource_type="knowledge_document", resource_id=document_id, previous_state=document.get("status"), new_state=document["status"])
        return document

    def delete_document(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.archive")
        document = self._document_or_404(document_id, ctx)
        if document.get("legal_hold") is True:
            raise NCP005Error("legal_hold_active", "Legal hold prevents deletion.", 409)
        self.repository.delete("knowledge_document", document_id)
        self._append_event("knowledge.document.deleted", ctx, resource_type="knowledge_document", resource_id=document_id, previous_state=document.get("status"), new_state="DELETED")
        return {"id": document_id, "deleted": True}

    def transition_document(self, document_id: str, target_status: str, ctx: NCP005ExecutionContext, *, reason: str = "", approval_reference: str | None = None) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        document = self._document_or_404(document_id, ctx)
        if not self._classification_allows(ctx, str(document.get("classification") or "INTERNAL")):
            raise NCP005Error("knowledge_document_forbidden", "Document is not accessible.", 403)
        target_status = target_status.upper()
        transitions = {
            "DRAFT": {"IN_REVIEW", "CHANGES_REQUESTED", "APPROVAL_REQUIRED"},
            "IN_REVIEW": {"APPROVAL_REQUIRED", "CHANGES_REQUESTED", "REJECTED"},
            "CHANGES_REQUESTED": {"DRAFT"},
            "APPROVAL_REQUIRED": {"APPROVED", "CHANGES_REQUESTED", "REJECTED"},
            "APPROVED": {"PUBLISHED", "SUPERSEDED"},
            "PUBLISHED": {"ARCHIVED", "SUPERSEDED", "DEPRECATED"},
            "ARCHIVED": set(),
            "SUPERSEDED": set(),
            "REJECTED": {"ARCHIVED"},
        }
        self._state_transition(str(document.get("status") or "DRAFT"), target_status, transitions)
        if target_status in {"APPROVED", "PUBLISHED"}:
            if target_status == "APPROVED":
                self._ensure_permission(ctx, "knowledge.approve")
            else:
                self._ensure_permission(ctx, "knowledge.publish")
        previous = document.get("status")
        document["status"] = target_status
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        document["version"] = int(document.get("version") or 1) + 1
        self.repository.upsert("knowledge_document", document)
        self._create_document_version(document, ctx, reason or f"Transitioned to {target_status}", approval_digest=approval_reference)
        self._append_event("knowledge.document.transitioned", ctx, resource_type="knowledge_document", resource_id=document_id, previous_state=previous, new_state=target_status, approval_reference=approval_reference, extra={"reason": reason})
        return document

    def publish_document(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.publish")
        document = self._document_or_404(document_id, ctx)
        if not self._classification_allows(ctx, str(document.get("classification") or "INTERNAL")):
            raise NCP005Error("knowledge_classification_forbidden", "Document is not accessible.", 403)
        if document.get("status") not in {"APPROVED", "PUBLISHED"}:
            raise NCP005Error("knowledge_approval_required", "Document must be approved before publication.", 409)
        document["status"] = "PUBLISHED"
        document["publication_timestamp"] = _utcnow()
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        document["version"] = int(document.get("version") or 1) + 1
        self.repository.upsert("knowledge_document", document)
        self._create_document_version(document, ctx, "Published document")
        self._index_document(document, ctx)
        self._append_event("knowledge.document.published", ctx, resource_type="knowledge_document", resource_id=document_id, new_state="PUBLISHED")
        return document

    def archive_document(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.archive")
        document = self._document_or_404(document_id, ctx)
        document["status"] = "ARCHIVED"
        document["archived_at"] = _utcnow()
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        document["version"] = int(document.get("version") or 1) + 1
        self.repository.upsert("knowledge_document", document)
        self.repository.upsert(
            "knowledge_archive_record",
            {
                "id": _new_id("archive"),
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": document.get("project_id"),
                "request_id": document.get("request_id"),
                "created_by": ctx.actor_id,
                "updated_by": ctx.actor_id,
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
                "version": 1,
                "status": "ARCHIVED",
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "metadata": {"document_id": document_id},
                "document_id": document_id,
                "document_version_id": document.get("current_version_id"),
            },
        )
        self._append_event("knowledge.document.archived", ctx, resource_type="knowledge_document", resource_id=document_id, previous_state="PUBLISHED", new_state="ARCHIVED")
        return document

    def restore_document(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        document = self._document_or_404(document_id, ctx)
        document["status"] = "DRAFT"
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        document["version"] = int(document.get("version") or 1) + 1
        self.repository.upsert("knowledge_document", document)
        self._create_document_version(document, ctx, "Restored document")
        self._append_event("knowledge.document.restored", ctx, resource_type="knowledge_document", resource_id=document_id, previous_state="ARCHIVED", new_state="DRAFT")
        return document

    def list_document_versions(self, document_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.read")
        return sorted(self._document_versions(document_id, ctx), key=lambda item: int(item.get("version") or 0))

    def get_document_version(self, document_id: str, version_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.read")
        for version in self._document_versions(document_id, ctx):
            if _lower(version.get("id")) == _lower(version_id):
                return version
        raise NCP005Error("knowledge_document_not_found", "Document version not found.", 404)

    def create_document_version(self, document_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        document = self._document_or_404(document_id, ctx)
        document["body"] = str(payload.get("body") or document.get("body") or "")
        document["summary"] = str(payload.get("summary") or document.get("summary") or "")
        document["title"] = str(payload.get("title") or document.get("title") or "Knowledge Document")
        document["version"] = int(document.get("version") or 1) + 1
        document["status"] = "DRAFT" if document.get("status") == "DRAFT" else "IN_REVIEW"
        self.repository.upsert("knowledge_document", document)
        version = self._create_document_version(document, ctx, str(payload.get("change_summary") or "Created document version"))
        self._append_event("knowledge.document.version.created", ctx, resource_type="knowledge_document", resource_id=document_id, new_state=version["version"])
        return version

    def restore_document_version(self, document_id: str, version_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        version = self.get_document_version(document_id, version_id, ctx)
        document = self._document_or_404(document_id, ctx)
        document["title"] = version["content"].get("title")
        document["summary"] = version["content"].get("summary")
        document["body"] = version["content"].get("body")
        document["structured_content"] = dict(version["content"].get("structured_content") or {})
        document["content_type"] = version["content"].get("content_type")
        document["source_format"] = version["content"].get("source_format")
        document["visibility"] = version["content"].get("visibility")
        document["classification"] = version["content"].get("classification")
        document["status"] = "DRAFT"
        document["version"] = int(document.get("version") or 1) + 1
        self.repository.upsert("knowledge_document", document)
        self._create_document_version(document, ctx, f"Restored version {version_id}")
        self._append_event("knowledge.document.version.restored", ctx, resource_type="knowledge_document", resource_id=document_id, previous_state=version_id, new_state=document["version"])
        return document

    def compare_document_versions(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        versions = self.list_document_versions(document_id, ctx)
        if len(versions) < 2:
            return {"document_id": document_id, "diff": [], "versions": versions}
        left, right = versions[-2], versions[-1]
        diff = []
        for field in ("title", "summary", "body", "content_type", "source_format", "visibility", "classification"):
            if left["content"].get(field) != right["content"].get(field):
                diff.append({"field": field, "before": left["content"].get(field), "after": right["content"].get(field)})
        return {"document_id": document_id, "diff": diff, "versions": [left, right]}

    # -- document reviews / approvals / comments / tags --------------
    def list_document_reviews(self, document_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.read")
        return [review for review in self._list_kind("knowledge_review", ctx) if _lower(review.get("document_id")) == _lower(document_id)]

    def create_document_review(self, document_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.review")
        document = self._document_or_404(document_id, ctx)
        review = self._record(
            "knowledge_review",
            ctx,
            {
                "document_id": document_id,
                "review_type": str(payload.get("review_type") or "EDITORIAL").upper(),
                "status": "OPEN",
                "summary": str(payload.get("summary") or ""),
                "comments": _as_list(payload.get("comments")),
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("knowledge_review", review)
        document.setdefault("review_ids", []).append(review["id"])
        self.repository.upsert("knowledge_document", document)
        self._append_event("knowledge.document.review.created", ctx, resource_type="knowledge_review", resource_id=review["id"], new_state="OPEN")
        return review

    def complete_document_review(self, document_id: str, review_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.review")
        review = self._get_kind("knowledge_review", review_id, ctx)
        if _lower(review.get("document_id")) != _lower(document_id):
            raise NCP005Error("knowledge_document_not_found", "Review does not belong to document.", 404)
        review["status"] = str(payload.get("status") or "APPROVED").upper()
        review["comments"] = _as_list(payload.get("comments") or review.get("comments"))
        review["updated_by"] = ctx.actor_id
        review["updated_at"] = _utcnow()
        review["version"] = int(review.get("version") or 1) + 1
        self.repository.upsert("knowledge_review", review)
        document = self._document_or_404(document_id, ctx)
        if review["status"] in {"APPROVED", "PASS"} and document.get("status") == "IN_REVIEW":
            document["status"] = "APPROVAL_REQUIRED"
            self.repository.upsert("knowledge_document", document)
        self._append_event("knowledge.document.review.completed", ctx, resource_type="knowledge_review", resource_id=review_id, previous_state="OPEN", new_state=review["status"])
        return review

    def list_document_approvals(self, document_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.approve")
        return [approval for approval in self._list_kind("knowledge_approval", ctx) if _lower(approval.get("document_id")) == _lower(document_id)]

    def create_document_approval(self, document_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.approve")
        document = self._document_or_404(document_id, ctx)
        approval = self._record(
            "knowledge_approval",
            ctx,
            {
                "document_id": document_id,
                "required_role": str(payload.get("required_role") or "PRODUCT_MANAGER"),
                "requested_by": ctx.actor_id,
                "requested_from": str(payload.get("requested_from") or ""),
                "decision": "PENDING",
                "reason": str(payload.get("reason") or ""),
                "conditions": _as_list(payload.get("conditions")),
                "expires_at": payload.get("expires_at"),
                "decided_at": None,
                "approval_reference": payload.get("approval_reference"),
            },
        )
        self.repository.upsert("knowledge_approval", approval)
        document.setdefault("approval_ids", []).append(approval["id"])
        self.repository.upsert("knowledge_document", document)
        self._append_event("knowledge.document.approval.requested", ctx, resource_type="knowledge_approval", resource_id=approval["id"], new_state="PENDING")
        return approval

    def approve_document_approval(self, document_id: str, approval_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.approve")
        approval = self._get_kind("knowledge_approval", approval_id, ctx)
        if _lower(approval.get("document_id")) != _lower(document_id):
            raise NCP005Error("knowledge_document_not_found", "Approval does not belong to document.", 404)
        approval["decision"] = "APPROVED"
        approval["status"] = "APPROVED"
        approval["reason"] = str(payload.get("reason") or approval.get("reason") or "")
        approval["conditions"] = _as_list(payload.get("conditions") or approval.get("conditions"))
        approval["decided_at"] = _utcnow()
        approval["updated_by"] = ctx.actor_id
        approval["updated_at"] = _utcnow()
        approval["version"] = int(approval.get("version") or 1) + 1
        self.repository.upsert("knowledge_approval", approval)
        document = self._document_or_404(document_id, ctx)
        document["status"] = "APPROVED"
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        document["version"] = int(document.get("version") or 1) + 1
        self.repository.upsert("knowledge_document", document)
        self._create_document_version(document, ctx, f"Document approved by {ctx.actor_id}", approval_digest=approval_id)
        self._append_event("knowledge.document.approved", ctx, resource_type="knowledge_approval", resource_id=approval_id, previous_state="PENDING", new_state="APPROVED", approval_reference=approval_id)
        return approval

    def reject_document_approval(self, document_id: str, approval_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.approve")
        approval = self._get_kind("knowledge_approval", approval_id, ctx)
        if _lower(approval.get("document_id")) != _lower(document_id):
            raise NCP005Error("knowledge_document_not_found", "Approval does not belong to document.", 404)
        approval["decision"] = "REJECTED"
        approval["status"] = "REJECTED"
        approval["reason"] = str(payload.get("reason") or approval.get("reason") or "")
        approval["decided_at"] = _utcnow()
        approval["updated_by"] = ctx.actor_id
        approval["updated_at"] = _utcnow()
        approval["version"] = int(approval.get("version") or 1) + 1
        self.repository.upsert("knowledge_approval", approval)
        document = self._document_or_404(document_id, ctx)
        document["status"] = "REJECTED"
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        document["version"] = int(document.get("version") or 1) + 1
        self.repository.upsert("knowledge_document", document)
        self._append_event("knowledge.document.rejected", ctx, resource_type="knowledge_approval", resource_id=approval_id, previous_state="PENDING", new_state="REJECTED", approval_reference=approval_id)
        return approval

    def request_changes_document_approval(self, document_id: str, approval_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.review")
        approval = self._get_kind("knowledge_approval", approval_id, ctx)
        if _lower(approval.get("document_id")) != _lower(document_id):
            raise NCP005Error("knowledge_document_not_found", "Approval does not belong to document.", 404)
        approval["decision"] = "CHANGES_REQUESTED"
        approval["status"] = "CHANGES_REQUESTED"
        approval["reason"] = str(payload.get("reason") or approval.get("reason") or "")
        approval["decided_at"] = _utcnow()
        approval["updated_by"] = ctx.actor_id
        approval["updated_at"] = _utcnow()
        approval["version"] = int(approval.get("version") or 1) + 1
        self.repository.upsert("knowledge_approval", approval)
        document = self._document_or_404(document_id, ctx)
        document["status"] = "CHANGES_REQUESTED"
        document["updated_by"] = ctx.actor_id
        document["updated_at"] = _utcnow()
        document["version"] = int(document.get("version") or 1) + 1
        self.repository.upsert("knowledge_document", document)
        self._append_event("knowledge.document.changes_requested", ctx, resource_type="knowledge_approval", resource_id=approval_id, previous_state="PENDING", new_state="CHANGES_REQUESTED", approval_reference=approval_id)
        return approval

    def list_document_comments(self, document_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.read")
        return [comment for comment in self._list_kind("knowledge_comment", ctx) if _lower(comment.get("document_id")) == _lower(document_id)]

    def add_document_comment(self, document_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.review")
        document = self._document_or_404(document_id, ctx)
        comment = self._record(
            "knowledge_comment",
            ctx,
            {
                "document_id": document_id,
                "body": str(payload.get("body") or ""),
                "edited": False,
                "mentions": _as_list(payload.get("mentions")),
                "deleted": False,
                "status": "ACTIVE",
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("knowledge_comment", comment)
        document.setdefault("comment_ids", []).append(comment["id"])
        self.repository.upsert("knowledge_document", document)
        self._append_event("knowledge.comment.added", ctx, resource_type="knowledge_comment", resource_id=comment["id"], new_state="ACTIVE")
        return comment

    def update_document_comment(self, document_id: str, comment_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.review")
        comment = self._get_kind("knowledge_comment", comment_id, ctx)
        if _lower(comment.get("document_id")) != _lower(document_id):
            raise NCP005Error("knowledge_document_not_found", "Comment does not belong to document.", 404)
        comment["body"] = str(payload.get("body") or comment.get("body") or "")
        comment["mentions"] = _as_list(payload.get("mentions") or comment.get("mentions"))
        comment["edited"] = True
        comment["updated_at"] = _utcnow()
        comment["updated_by"] = ctx.actor_id
        comment["version"] = int(comment.get("version") or 1) + 1
        self.repository.upsert("knowledge_comment", comment)
        self._append_event("knowledge.comment.updated", ctx, resource_type="knowledge_comment", resource_id=comment_id, previous_state="ACTIVE", new_state="ACTIVE")
        return comment

    def delete_document_comment(self, document_id: str, comment_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.review")
        comment = self._get_kind("knowledge_comment", comment_id, ctx)
        if _lower(comment.get("document_id")) != _lower(document_id):
            raise NCP005Error("knowledge_document_not_found", "Comment does not belong to document.", 404)
        comment["deleted"] = True
        comment["status"] = "DELETED"
        comment["updated_at"] = _utcnow()
        comment["updated_by"] = ctx.actor_id
        self.repository.upsert("knowledge_comment", comment)
        self._append_event("knowledge.comment.deleted", ctx, resource_type="knowledge_comment", resource_id=comment_id, previous_state="ACTIVE", new_state="DELETED")
        return comment

    def list_tags(self, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.read")
        return self._list_kind("knowledge_tag", ctx)

    def create_tag(self, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        tag = self._record(
            "knowledge_tag",
            ctx,
            {
                "id": str(payload.get("id") or payload.get("tag_id") or _new_id("tag")),
                "name": str(payload.get("name") or ""),
                "description": str(payload.get("description") or ""),
                "status": "ACTIVE",
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("knowledge_tag", tag)
        self._append_event("knowledge.tag.created", ctx, resource_type="knowledge_tag", resource_id=tag["id"], new_state="ACTIVE")
        return tag

    def add_document_tag(self, document_id: str, tag_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        document = self._document_or_404(document_id, ctx)
        tag = self.repository.get("knowledge_tag", tag_id)
        if tag is None:
            raise NCP005Error("knowledge_document_not_found", "Tag not found.", 404)
        document.setdefault("tags", [])
        if tag_id not in document["tags"]:
            document["tags"].append(tag_id)
        document["updated_at"] = _utcnow()
        document["updated_by"] = ctx.actor_id
        self.repository.upsert("knowledge_document", document)
        self._append_event("knowledge.tag.added", ctx, resource_type="knowledge_document", resource_id=document_id, extra={"tag_id": tag_id})
        return document

    def remove_document_tag(self, document_id: str, tag_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        document = self._document_or_404(document_id, ctx)
        document["tags"] = [item for item in _as_list(document.get("tags")) if item != tag_id]
        document["updated_at"] = _utcnow()
        document["updated_by"] = ctx.actor_id
        self.repository.upsert("knowledge_document", document)
        self._append_event("knowledge.tag.removed", ctx, resource_type="knowledge_document", resource_id=document_id, extra={"tag_id": tag_id})
        return document

    def list_document_relationships(self, document_id: str, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.read")
        return [link for link in self._list_kind("knowledge_relationship", ctx) if _lower(link.get("source_id")) == _lower(document_id) or _lower(link.get("target_id")) == _lower(document_id)]

    def create_document_relationship(self, document_id: str, payload: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        source = self._document_or_404(document_id, ctx)
        target_id = str(payload.get("target_id") or "")
        target = self._document_or_404(target_id, ctx)
        relationship = str(payload.get("relationship") or "RELATED_TO").upper()
        if relationship not in RELATIONSHIP_TYPES:
            raise NCP005Error("traceability_link_invalid", "Unsupported relationship.", 400)
        link = self._record(
            "knowledge_relationship",
            ctx,
            {
                "source_id": document_id,
                "target_id": target_id,
                "relationship": relationship,
                "status": "ACTIVE",
                "confidence": float(payload.get("confidence") or 1.0),
                "verification_status": str(payload.get("verification_status") or "UNVERIFIED"),
                "creation_method": str(payload.get("creation_method") or "manual"),
                "evidence_reference": payload.get("evidence_reference"),
                "metadata": dict(payload.get("metadata") or {}),
            },
        )
        self.repository.upsert("knowledge_relationship", link)
        self._append_event("knowledge.relationship.created", ctx, resource_type="knowledge_relationship", resource_id=link["id"], extra={"target_id": target["id"]})
        return link

    def delete_document_relationship(self, relationship_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.update")
        relationship = self._get_kind("knowledge_relationship", relationship_id, ctx)
        self.repository.delete("knowledge_relationship", relationship_id)
        self._append_event("knowledge.relationship.deleted", ctx, resource_type="knowledge_relationship", resource_id=relationship_id, previous_state=relationship.get("relationship"), new_state="DELETED")
        return {"id": relationship_id, "deleted": True}

    # -- search / retrieval ------------------------------------------
    def _search_pool(self, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        pool = []
        for requirement in self.list_requirements(ctx):
            pool.append(
                {
                    "resource_type": "REQUIREMENT",
                    "resource_id": requirement["id"],
                    "title": requirement.get("title"),
                    "snippet": requirement.get("summary") or requirement.get("description"),
                    "classification": requirement.get("classification"),
                    "status": requirement.get("status"),
                    "workspace_id": requirement.get("workspace_id"),
                    "project_id": requirement.get("project_id"),
                    "updated_at": requirement.get("updated_at"),
                    "text": " ".join(str(requirement.get(field) or "") for field in ("title", "summary", "description", "type", "priority")),
                    "source": "requirements",
                }
            )
        for criterion in self._list_kind("acceptance_criterion", ctx):
            requirement = self.repository.get("requirement", criterion.get("requirement_id"))
            if requirement is None:
                continue
            pool.append(
                {
                    "resource_type": "ACCEPTANCE_CRITERION",
                    "resource_id": criterion["id"],
                    "title": criterion.get("description"),
                    "snippet": criterion.get("expected_result"),
                    "classification": requirement.get("classification"),
                    "status": criterion.get("status"),
                    "workspace_id": requirement.get("workspace_id"),
                    "project_id": requirement.get("project_id"),
                    "updated_at": criterion.get("updated_at"),
                    "text": " ".join(str(criterion.get(field) or "") for field in ("description", "verification_method", "expected_result", "criterion_type")),
                    "source": "acceptance_criteria",
                }
            )
        for document in self.list_documents(ctx):
            if not self._classification_allows(ctx, str(document.get("classification") or "INTERNAL")):
                continue
            pool.append(
                {
                    "resource_type": "KNOWLEDGE_DOCUMENT",
                    "resource_id": document["id"],
                    "title": document.get("title"),
                    "snippet": document.get("summary") or str(document.get("body") or "")[:180],
                    "classification": document.get("classification"),
                    "status": document.get("status"),
                    "workspace_id": document.get("workspace_id"),
                    "project_id": document.get("project_id"),
                    "updated_at": document.get("updated_at"),
                    "text": " ".join(str(document.get(field) or "") for field in ("title", "summary", "body", "content_type", "source_format")),
                    "source": "knowledge_documents",
                }
            )
        for document in self._list_kind("knowledge_document", ctx):
            if _lower(document.get("content_type")) == "adr":
                pool.append(
                    {
                        "resource_type": "ADR",
                        "resource_id": document["id"],
                        "title": document.get("title"),
                        "snippet": document.get("summary") or str(document.get("body") or "")[:180],
                        "classification": document.get("classification"),
                        "status": document.get("status"),
                        "workspace_id": document.get("workspace_id"),
                        "project_id": document.get("project_id"),
                        "updated_at": document.get("updated_at"),
                        "text": " ".join(str(document.get(field) or "") for field in ("title", "summary", "body", "content_type")),
                        "source": "adrs",
                    }
                )
        return pool

    def search(self, query: str, ctx: NCP005ExecutionContext, *, resource_types: list[str] | None = None, classification: str | None = None, strategy: str = "keyword", maximum_results: int = 20, purpose: str = "search", execution_id: str | None = None) -> dict[str, Any]:
        if strategy == "semantic" and not self.semantic_backend and _lower(ctx.environment) in {"production", "prod"}:
            raise NCP005Error("retrieval_source_unavailable", "Semantic backend unavailable.", 503)
        permission = "knowledge.search" if strategy != "keyword" else "knowledge.read"
        self._ensure_permission(ctx, permission)
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return {"query": normalized_query, "strategy": strategy, "results": [], "retrieval_id": _new_id("retrieval"), "source_count": 0}
        query_terms = re.findall(r"[a-z0-9]+", normalized_query.lower())
        pool = self._search_pool(ctx)
        if resource_types:
            wanted = {value.lower() for value in resource_types}
            pool = [item for item in pool if item["resource_type"].lower() in wanted]
        if classification:
            wanted_classification = classification.upper()
            pool = [item for item in pool if str(item.get("classification") or "").upper() == wanted_classification]
        scored: list[dict[str, Any]] = []
        query_vec = _vectorize(normalized_query)
        for item in pool:
            text = item["text"].lower()
            keyword_score = sum(text.count(term) for term in query_terms)
            semantic_score = _cosine(query_vec, _vectorize(item["text"]))
            authority_score = 1.0 if item.get("status") in {"APPROVED", "PUBLISHED", "BASELINED", "VERIFIED", "ACTIVE"} else 0.6
            total_score = keyword_score + semantic_score + authority_score
            if keyword_score <= 0 and strategy == "keyword":
                continue
            scored.append(
                {
                    **item,
                    "score": round(total_score, 6),
                    "keyword_score": round(float(keyword_score), 6),
                    "semantic_score": round(float(semantic_score), 6),
                    "authority_score": round(float(authority_score), 6),
                    "matched_sections": [term for term in query_terms if term in text],
                    "why_matched": f"Matched on {', '.join(sorted(set(term for term in query_terms if term in text))) or 'semantic similarity'}",
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        results = scored[:maximum_results]
        retrieval_id = _new_id("retrieval")
        retrieval = self._record(
            "knowledge_retrieval_record",
            ctx,
            {
                "id": retrieval_id,
                "query": normalized_query,
                "strategy": strategy,
                "purpose": purpose,
                "execution_id": execution_id,
                "maximum_results": maximum_results,
                "results": results,
                "query_digest": _digest(normalized_query),
                "index_version": 1,
                "source_count": len(results),
                "metadata": {"resource_types": resource_types or [], "classification": classification},
            },
            record_id=retrieval_id,
        )
        self.repository.upsert("knowledge_retrieval_record", retrieval)
        self.repository.upsert(
            "knowledge_search_query",
            {
                "id": _new_id("search"),
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "project_id": ctx.project_id,
                "request_id": ctx.request_id,
                "created_by": ctx.actor_id,
                "updated_by": ctx.actor_id,
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
                "version": 1,
                "status": "RECORDED",
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "metadata": {"execution_id": execution_id, "strategy": strategy, "purpose": purpose},
                "query": normalized_query,
                "result_ids": [item["resource_id"] for item in results],
                "retrieval_id": retrieval_id,
            },
        )
        self._append_event("knowledge.search.completed", ctx, resource_type="knowledge_search_query", resource_id=retrieval_id, new_state=strategy, extra={"result_count": len(results)})
        return {"retrieval_id": retrieval_id, "query": normalized_query, "strategy": strategy, "results": results, "source_count": len(results)}

    def search_keyword(self, query: str, ctx: NCP005ExecutionContext, **filters: Any) -> dict[str, Any]:
        return self.search(query, ctx, strategy="keyword", **filters)

    def search_semantic(self, query: str, ctx: NCP005ExecutionContext, **filters: Any) -> dict[str, Any]:
        return self.search(query, ctx, strategy="semantic", **filters)

    def search_hybrid(self, query: str, ctx: NCP005ExecutionContext, **filters: Any) -> dict[str, Any]:
        return self.search(query, ctx, strategy="hybrid", **filters)

    def answer(self, query: str, ctx: NCP005ExecutionContext, **filters: Any) -> dict[str, Any]:
        retrieval = self.search_hybrid(query, ctx, **filters)
        citations = []
        for result in retrieval["results"]:
            citations.append(
                {
                    "citation_id": _new_id("citation"),
                    "document_id": result["resource_id"],
                    "document_version_id": result.get("resource_id"),
                    "section_id": "snippet",
                    "start_offset": 0,
                    "end_offset": len(str(result.get("snippet") or "")),
                    "quoted_digest": _digest(result.get("snippet") or ""),
                    "source_uri": f"{result['source']}://{result['resource_id']}",
                    "source_title": result.get("title"),
                    "retrieved_at": _utcnow(),
                }
            )
        answer = {
            "answer": retrieval["results"][0]["snippet"] if retrieval["results"] else "No accessible sources matched the query.",
            "citations": citations,
            "confidence": round(min(1.0, (retrieval["results"][0]["score"] if retrieval["results"] else 0.0) / 8.0), 3),
            "source_count": len(retrieval["results"]),
            "search_strategy": retrieval["strategy"],
            "limitations": [] if retrieval["results"] else ["No accessible sources matched the query."],
        }
        self._append_event("knowledge.answer.generated", ctx, resource_type="knowledge_retrieval_record", resource_id=retrieval["retrieval_id"], new_state="ANSWERED")
        return answer

    def get_retrieval(self, retrieval_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.search")
        retrieval = self.repository.get("knowledge_retrieval_record", retrieval_id)
        if retrieval is None:
            raise NCP005Error("retrieval_source_unavailable", "Retrieval not found.", 404)
        self._ensure_tenant(ctx, retrieval)
        return retrieval

    def recent_searches(self, ctx: NCP005ExecutionContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "knowledge.search")
        return self._list_kind("knowledge_search_query", ctx)

    def index_document(self, document_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        document = self._document_or_404(document_id, ctx)
        if not self._classification_allows(ctx, str(document.get("classification") or "INTERNAL")):
            raise NCP005Error("knowledge_document_forbidden", "Document is not accessible.", 403)
        record = self._record(
            "knowledge_index_record",
            ctx,
            {
                "document_id": document_id,
                "document_version_id": document.get("current_version_id"),
                "index_status": "INDEXED",
                "index_provider": self.semantic_backend or "deterministic-local",
                "index_version": 1,
                "content_digest": _digest(document.get("body") or ""),
                "vector_reference": _vectorize(" ".join([str(document.get("title") or ""), str(document.get("summary") or ""), str(document.get("body") or "")])),
                "classification": document.get("classification"),
            },
        )
        self.repository.upsert("knowledge_index_record", record)
        self._append_event("knowledge.document.indexed", ctx, resource_type="knowledge_index_record", resource_id=record["id"], new_state="INDEXED")
        return record

    def _index_document(self, document: dict[str, Any], ctx: NCP005ExecutionContext) -> dict[str, Any]:
        return self.index_document(str(document.get("id") or ""), ctx)

    # -- AI integration ----------------------------------------------
    def import_ai_execution(self, execution_id: str, ctx: NCP005ExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "requirements.create")
        execution = self.repository.get("ai_execution", execution_id)
        if execution is None:
            raise NCP005Error("requirement_not_found", "AI execution not found.", 404)
        if _lower(execution.get("tenant_id")) != _lower(ctx.tenant_id):
            raise NCP005Error("cross_tenant_knowledge_forbidden", "Cross-tenant AI import forbidden.", 403)
        if ctx.workspace_id and _lower(execution.get("workspace_id")) and _lower(execution.get("workspace_id")) != _lower(ctx.workspace_id):
            raise NCP005Error("cross_tenant_knowledge_forbidden", "Cross-workspace AI import forbidden.", 403)
        output_digest = str(execution.get("requirement_digest") or execution.get("execution_digest") or _digest(execution.get("requirements") or []))
        existing = [record for record in self._list_kind("requirement_import", ctx) if _lower(record.get("created_from_execution_id")) == _lower(execution_id) and str(record.get("output_digest") or "") == output_digest]
        if existing:
            return existing[0]
        requirement_set = self.create_requirement_set(
            {
                "name": f"AI execution {execution_id} requirements",
                "description": str(execution.get("request_text") or execution.get("summary") or ""),
                "classification": str(execution.get("classification", {}).get("sensitivity") if isinstance(execution.get("classification"), dict) else "INTERNAL").upper(),
                "retention_policy_id": "retain-indefinitely",
                "metadata": {
                    "source_execution_id": execution_id,
                    "input_digest": execution.get("input_digest"),
                    "output_digest": output_digest,
                    "agent_version": execution.get("agent_version"),
                    "model_provider": execution.get("model_configuration", {}).get("provider"),
                    "model": execution.get("model_configuration", {}).get("model"),
                },
            },
            ctx,
        )
        imported_requirements = []
        requirements = _as_list(execution.get("requirements"))
        for item in requirements:
            requirement = self.create_requirement(
                {
                    "requirement_set_id": requirement_set["id"],
                    "title": item.get("title") or item.get("summary") or "Requirement",
                    "summary": item.get("summary") or item.get("title") or "",
                    "description": item.get("description") or "",
                    "type": item.get("type") or item.get("kind") or "FUNCTIONAL",
                    "priority": item.get("priority") or "MEDIUM",
                    "source": "AI_GENERATED",
                    "status": "GENERATED",
                    "content": dict(item.get("content") or item),
                    "assumptions": _as_list(item.get("assumptions")),
                    "dependencies": _as_list(item.get("dependencies")),
                    "constraints": _as_list(item.get("constraints")),
                    "risks": _as_list(item.get("risks")),
                    "metadata": {
                        "source_execution_id": execution_id,
                        "agent_id": item.get("agent_id"),
                        "agent_version": item.get("agent_version"),
                        "model_provider": item.get("model_provider"),
                        "model": item.get("model"),
                    },
                    "created_from_execution_id": execution_id,
                    "created_from_agent_id": item.get("agent_id") or execution.get("agent_id"),
                    "source_digest": item.get("source_digest") or _digest(item),
                    "source_type": "AI_GENERATED",
                    "source_id": execution_id,
                    "source_version": str(item.get("version") or execution.get("version") or "1"),
                },
                ctx,
            )
            imported_requirements.append(requirement)
            for criterion in _as_list(item.get("acceptance_criteria")):
                self.create_acceptance_criterion(
                    requirement["id"],
                    {
                        "description": str(criterion.get("description") or criterion.get("text") or ""),
                        "criterion_type": str(criterion.get("criterion_type") or "CHECKLIST"),
                        "verification_method": str(criterion.get("verification_method") or "MANUAL_VERIFICATION"),
                        "expected_result": str(criterion.get("expected_result") or criterion.get("outcome") or ""),
                        "status": "APPROVED" if criterion.get("approved") else "DRAFT",
                        "linked_test_ids": _as_list(criterion.get("linked_test_ids")),
                        "linked_evidence_ids": _as_list(criterion.get("linked_evidence_ids")),
                        "metadata": {"source_execution_id": execution_id},
                    },
                    ctx,
                )
            self.create_traceability_link(
                {
                    "source_type": "REQUEST",
                    "source_id": execution.get("request_id") or ctx.request_id or execution_id,
                    "target_type": "REQUIREMENT",
                    "target_id": requirement["id"],
                    "relationship": "DERIVED_FROM",
                    "confidence": 1.0,
                    "verification_status": "VERIFIED",
                    "creation_method": "ai-import",
                    "evidence_reference": execution.get("evidence_reference"),
                    "metadata": {"source_execution_id": execution_id},
                },
                ctx,
            )
            self.create_traceability_link(
                {
                    "source_type": "REQUIREMENT",
                    "source_id": requirement["id"],
                    "target_type": "EVIDENCE",
                    "target_id": execution.get("evidence_reference") or execution_id,
                    "relationship": "EVIDENCED_BY",
                    "confidence": 1.0,
                    "verification_status": "VERIFIED",
                    "creation_method": "ai-import",
                    "evidence_reference": execution.get("evidence_reference"),
                    "metadata": {"source_execution_id": execution_id},
                },
                ctx,
            )
        import_record = self._record(
            "requirement_import",
            ctx,
            {
                "created_from_execution_id": execution_id,
                "created_from_agent_id": execution.get("agent_id"),
                "created_from_tool_id": execution.get("tool_id"),
                "source_type": "AI_EXECUTION",
                "source_id": execution_id,
                "source_version": str(execution.get("version") or "1"),
                "source_uri": str(execution.get("source_uri") or ""),
                "source_digest": str(execution.get("input_digest") or ""),
                "output_digest": output_digest,
                "human_verified": False,
                "verification_actor_id": None,
                "verification_timestamp": None,
                "status": "RECORDED",
                "metadata": {
                    "requirement_set_id": requirement_set["id"],
                    "imported_requirement_ids": [item["id"] for item in imported_requirements],
                    "input_digest": execution.get("input_digest"),
                    "output_digest": output_digest,
                },
            },
            record_id=_new_id("req-import"),
            status="RECORDED",
        )
        self.repository.upsert("requirement_import", import_record)
        self._append_event("requirements.imported.from_ai", ctx, resource_type="requirement_import", resource_id=import_record["id"], request_id=execution.get("request_id"), new_state="RECORDED", extra={"execution_id": execution_id, "requirement_set_id": requirement_set["id"]})
        return {"requirement_set": requirement_set, "requirements": imported_requirements, "import": import_record}


__all__ = [
    "NCP005Error",
    "NCP005ExecutionContext",
    "NovaCodeProNCP005Service",
    "REQUIREMENT_TYPES",
    "REQUIREMENT_STATUSES",
    "REQUIREMENT_SOURCES",
    "REQUIREMENT_PRIORITY",
    "CRITERION_TYPES",
    "CRITERION_STATUS",
    "RELATIONSHIP_TYPES",
    "KNOWLEDGE_TYPES",
    "KNOWLEDGE_STATUSES",
    "KNOWLEDGE_VISIBILITY",
    "KNOWLEDGE_CLASSIFICATIONS",
]
