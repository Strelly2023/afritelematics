from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from afritech.novacodepro.platform import NovaCodeProRepository, _event_envelope, _new_id, _now


DESIGN_STATUSES = {
    "DRAFT",
    "IN_REVIEW",
    "CHANGES_REQUESTED",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "BASELINED",
    "READY_FOR_IMPLEMENTATION",
    "IMPLEMENTING",
    "VALIDATING",
    "VERIFIED",
    "REJECTED",
    "ARCHIVED",
    "SUPERSEDED",
}

DESIGN_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"IN_REVIEW", "ARCHIVED"},
    "IN_REVIEW": {"CHANGES_REQUESTED", "APPROVAL_REQUIRED", "REJECTED"},
    "CHANGES_REQUESTED": {"DRAFT", "IN_REVIEW", "ARCHIVED"},
    "APPROVAL_REQUIRED": {"APPROVED", "CHANGES_REQUESTED", "REJECTED"},
    "APPROVED": {"BASELINED", "SUPERSEDED"},
    "BASELINED": {"READY_FOR_IMPLEMENTATION", "SUPERSEDED"},
    "READY_FOR_IMPLEMENTATION": {"IMPLEMENTING", "SUPERSEDED"},
    "IMPLEMENTING": {"VALIDATING", "CHANGES_REQUESTED"},
    "VALIDATING": {"VERIFIED", "CHANGES_REQUESTED"},
    "VERIFIED": {"ARCHIVED", "SUPERSEDED"},
    "REJECTED": {"ARCHIVED"},
    "ARCHIVED": set(),
    "SUPERSEDED": set(),
}

RESEARCH_METHODS = {
    "INTERVIEW",
    "SURVEY",
    "CONTEXTUAL_INQUIRY",
    "FIELD_STUDY",
    "DIARY_STUDY",
    "USABILITY_TEST",
    "ACCESSIBILITY_RESEARCH",
    "ANALYTICS_REVIEW",
    "SUPPORT_ANALYSIS",
    "COMPETITOR_REVIEW",
    "DESK_RESEARCH",
    "WORKSHOP",
    "CO_DESIGN",
    "EXPERT_REVIEW",
}

PERSONA_TYPES = {
    "PRIMARY",
    "SECONDARY",
    "NEGATIVE",
    "PROTO_PERSONA",
    "ACCESSIBILITY_PERSONA",
    "OPERATIONAL_PERSONA",
    "ADMINISTRATOR",
    "PARTNER",
    "CUSTOMER",
    "EMPLOYEE",
}

FLOW_NODE_TYPES = {"START", "SCREEN", "ACTION", "DECISION", "SYSTEM_ACTION", "WAIT", "ERROR", "RECOVERY", "APPROVAL", "EXTERNAL_HANDOFF", "END"}
FLOW_EDGE_TYPES = {"PRIMARY", "ALTERNATIVE", "ERROR", "RECOVERY", "CANCEL", "TIMEOUT", "RETRY", "ESCALATION"}
SCREEN_STATES = {"DEFAULT", "LOADING", "EMPTY", "READY", "VALIDATION_ERROR", "SUBMITTING", "SUCCESS", "PARTIAL_SUCCESS", "OFFLINE", "TIMEOUT", "FORBIDDEN", "NOT_FOUND", "SERVICE_UNAVAILABLE", "CONFLICT", "APPROVAL_REQUIRED", "CHANGES_REQUESTED", "ARCHIVED", "READ_ONLY"}
TOKEN_CATEGORIES = {"COLOR", "TYPOGRAPHY", "SPACING", "SIZE", "BORDER", "RADIUS", "SHADOW", "ELEVATION", "OPACITY", "MOTION", "DURATION", "EASING", "BREAKPOINT", "GRID", "Z_INDEX", "ICON", "ILLUSTRATION"}
TOKEN_LEVELS = {"GLOBAL", "SEMANTIC", "COMPONENT", "STATE", "BRAND", "TENANT"}
CONTENT_TYPES = {"LABEL", "BUTTON", "HEADING", "BODY", "HELP", "ERROR", "WARNING", "SUCCESS", "EMPTY_STATE", "NOTIFICATION", "TOOLTIP", "PLACEHOLDER", "LEGAL", "CONSENT", "ACCESSIBILITY_LABEL", "STATUS", "TRANSACTIONAL", "MARKETING"}
LOCALIZATION_STATUSES = {"DRAFT", "IN_REVIEW", "APPROVED", "PUBLISHED", "ARCHIVED", "SUPERSEDED"}
ACCESSIBILITY_TARGETS = {"WCAG_2_2_A", "WCAG_2_2_AA", "WCAG_2_2_AAA", "EN_301_549", "SECTION_508", "PLATFORM_NATIVE"}
DESIGN_REVIEW_TYPES = {"PRODUCT", "UX", "UI", "CONTENT", "ACCESSIBILITY", "BRAND", "SECURITY", "PRIVACY", "COMPLIANCE", "ENGINEERING", "ARCHITECTURE", "OPERATIONS", "LOCALIZATION"}
DESIGN_APPROVAL_DECISIONS = {"APPROVED", "REJECTED", "CHANGES_REQUESTED"}
BASELINE_STATUSES = {"DRAFT", "APPROVAL_REQUIRED", "APPROVED", "ACTIVE", "SUPERSEDED", "REVOKED", "ARCHIVED"}
DESIGN_RISK_CATEGORIES = {"USABILITY", "ACCESSIBILITY", "CONTENT", "LOCALIZATION", "CONSISTENCY", "SECURITY", "PRIVACY", "BRAND", "RESPONSIVE", "PERFORMANCE", "IMPLEMENTATION", "RESEARCH_GAP", "DEPENDENCY"}
DESIGN_DEBT_CATEGORIES = {"INCONSISTENT_COMPONENT", "DUPLICATE_COMPONENT", "DEPRECATED_TOKEN", "UNRESPONSIVE_LAYOUT", "MISSING_STATE", "ACCESSIBILITY_GAP", "CONTENT_GAP", "LOCALIZATION_GAP", "DOCUMENTATION_GAP", "VISUAL_DRIFT", "IMPLEMENTATION_DRIFT"}
PROTOTYPE_TYPES = {"LOW_FIDELITY", "HIGH_FIDELITY", "CLICKABLE", "DATA_CONNECTED", "DEVICE", "SERVICE", "ACCESSIBILITY", "OPERATIONAL"}
VALIDATION_CATEGORIES = {"STRUCTURAL", "NAVIGATION", "USER_FLOW", "COMPONENT", "TOKEN", "THEME", "RESPONSIVE", "ACCESSIBILITY", "CONTENT", "LOCALIZATION", "SECURITY", "PRIVACY", "CONSISTENCY", "TRACEABILITY", "IMPLEMENTATION_READINESS"}
FITNESS_TYPES = {"TOKEN_CONSISTENCY", "COMPONENT_CONSISTENCY", "ACCESSIBILITY_COVERAGE", "CONTENT_COMPLETENESS", "LOCALIZATION_COVERAGE", "RESPONSIVE_COVERAGE", "STATE_COVERAGE", "TRACEABILITY_COVERAGE", "IMPLEMENTATION_CONTRACT", "VISUAL_BASELINE", "INTERACTION_CONSISTENCY", "SECURITY_PATTERN", "PRIVACY_PATTERN", "CUSTOM_COMMAND"}
DIAGRAM_FORMATS = {"PNG", "SVG", "MERMAID", "PLANTUML", "JSON"}
DIAGRAM_TYPES = {"SYSTEM_CONTEXT", "CONTAINER", "COMPONENT", "SEQUENCE", "DEPLOYMENT", "NETWORK", "DATA_FLOW", "EVENT_FLOW", "TRUST_BOUNDARY", "IDENTITY_FLOW", "RECOVERY_FLOW"}
QUESTIONABLE_EXTENSIONS = {".exe", ".bat", ".cmd", ".msi", ".sh", ".ps1", ".scr", ".com", ".jar", ".js", ".ts", ".py", ".rb", ".php", ".pl", ".vbs"}
ALLOWED_ATTACHMENT_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/json",
    "text/csv",
    "image/png",
    "image/jpeg",
}
DESIGN_COLLECTIONS = {
    "experience_workspace",
    "experience_brief",
    "research_study",
    "research_finding",
    "research_source",
    "persona",
    "persona_version",
    "journey_map",
    "journey_stage",
    "journey_step",
    "service_blueprint",
    "blueprint_step",
    "information_architecture",
    "navigation_node",
    "content_model",
    "user_flow",
    "flow_node",
    "flow_edge",
    "wireframe",
    "screen_design",
    "design_system",
    "design_token",
    "theme",
    "component_definition",
    "component_contract",
    "interaction_pattern",
    "responsive_specification",
    "content_specification",
    "localization_resource",
    "accessibility_requirement",
    "accessibility_review",
    "prototype",
    "design_review",
    "design_approval",
    "design_baseline",
    "design_validation_rule",
    "design_validation_result",
    "design_coverage",
    "design_evidence_package",
    "design_generation_record",
    "design_import",
    "design_export",
    "design_metric_record",
    "design_traceability_link",
    "design_traceability_snapshot",
    "design_risk",
    "design_debt_item",
    "design_change_request",
    "design_impact_analysis",
    "design_drift",
    "design_handoff",
    "design_search_query",
    "design_retrieval_record",
    "design_retention_policy",
    "design_archive_record",
}


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
    return normalized.strip("-") or "item"


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _upper(value: Any) -> str:
    return str(value or "").strip().upper()


def _digest(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utcnow() -> str:
    return _now()


def _version_kind(kind: str) -> str:
    return f"{kind}_version"


@dataclass(frozen=True)
class DesignExecutionContext:
    actor_id: str
    tenant_id: str
    organization_id: str
    workspace_id: str | None
    project_id: str | None
    request_id: str | None
    requirement_set_id: str | None = None
    architecture_workspace_id: str | None = None
    architecture_model_id: str | None = None
    architecture_baseline_id: str | None = None
    experience_workspace_id: str | None = None
    design_project_id: str | None = None
    role: str = "DEVELOPER"
    permissions: tuple[str, ...] = ()
    session_id: str | None = None
    correlation_id: str = ""
    causation_id: str | None = None
    environment: str = "development"


class DesignError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


DESIGN_ERROR = DesignError


class NovaCodeProNCP006BService:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository
        self._seed_defaults()

    # ------------------------------------------------------------------
    # seed and helpers
    # ------------------------------------------------------------------
    def _seed_defaults(self) -> None:
        if not self.repository.list("design_workspace"):
            self.repository.upsert(
                "design_workspace",
                {
                    "id": "design-workspace-default",
                    "tenant_id": "novatech",
                    "organization_id": "novatech",
                    "workspace_id": "enterprise-product-manager",
                    "project_id": "design-project-default",
                    "request_id": "request-design-default",
                    "name": "Design Studio",
                    "slug": "design-studio",
                    "description": "Governed experience and design workspace.",
                    "status": "APPROVED",
                    "version": 1,
                    "created_by": "system",
                    "updated_by": "system",
                    "created_at": _utcnow(),
                    "updated_at": _utcnow(),
                    "correlation_id": "seed",
                    "causation_id": "seed",
                    "metadata": {"seeded": True},
                    "risk": [],
                    "debt": [],
                    "summary": {},
                },
            )

    def _tenant_match(self, left: str, right: str) -> bool:
        return _lower(left) == _lower(right)

    def _admin_override(self, ctx: DesignExecutionContext) -> bool:
        return ctx.role in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN"}

    def _ensure_permission(self, ctx: DesignExecutionContext, permission: str) -> None:
        if permission in ctx.permissions or self._admin_override(ctx):
            return
        raise DesignError("design_artifact_forbidden", f"Missing permission: {permission}", 403)

    def _ensure_tenant(self, record: dict[str, Any], ctx: DesignExecutionContext) -> None:
        if not self._tenant_match(record.get("tenant_id"), ctx.tenant_id):
            raise DesignError("cross_tenant_design_forbidden", "Cross-tenant design access is forbidden.", 403)

    def _ensure_workspace(self, record: dict[str, Any], ctx: DesignExecutionContext) -> None:
        record_workspace = _lower(record.get("workspace_id"))
        if ctx.workspace_id and record_workspace and record_workspace != _lower(ctx.workspace_id):
            raise DesignError("design_workspace_forbidden", "Cross-workspace design access is forbidden.", 403)

    def _ensure_project(self, record: dict[str, Any], ctx: DesignExecutionContext) -> None:
        record_project = _lower(record.get("project_id"))
        if ctx.project_id and record_project and record_project != _lower(ctx.project_id):
            raise DesignError("design_artifact_forbidden", "Cross-project design access is forbidden.", 403)

    def _record(
        self,
        kind: str,
        ctx: DesignExecutionContext,
        payload: dict[str, Any],
        *,
        record_id: str | None = None,
        status: str | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        now = _utcnow()
        resource_id = record_id or str(payload.get("id") or _new_id(kind.replace("_", "-")))
        record = {
            "id": resource_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": payload.get("workspace_id") or ctx.workspace_id,
            "project_id": payload.get("project_id") or ctx.project_id,
            "request_id": payload.get("request_id") or ctx.request_id,
            "requirement_set_id": payload.get("requirement_set_id") or ctx.requirement_set_id,
            "architecture_workspace_id": payload.get("architecture_workspace_id") or ctx.architecture_workspace_id,
            "architecture_model_id": payload.get("architecture_model_id") or ctx.architecture_model_id,
            "architecture_baseline_id": payload.get("architecture_baseline_id") or ctx.architecture_baseline_id,
            "experience_workspace_id": payload.get("experience_workspace_id") or ctx.experience_workspace_id or payload.get("workspace_id") or ctx.workspace_id,
            "design_project_id": payload.get("design_project_id") or ctx.design_project_id or payload.get("project_id") or ctx.project_id,
            "created_by": payload.get("created_by") or ctx.actor_id,
            "updated_by": ctx.actor_id,
            "created_at": payload.get("created_at") or now,
            "updated_at": now,
            "version": int(version or payload.get("version") or 1),
            "status": str(status or payload.get("status") or "DRAFT").upper(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": dict(payload.get("metadata") or {}),
            "source_type": payload.get("source_type"),
            "source_id": payload.get("source_id"),
            "source_version": payload.get("source_version"),
            "source_uri": payload.get("source_uri"),
            "source_digest": payload.get("source_digest"),
            "creation_method": payload.get("creation_method") or "MANUAL",
            "created_from_agent_id": payload.get("created_from_agent_id"),
            "created_from_execution_id": payload.get("created_from_execution_id"),
            "created_from_tool_id": payload.get("created_from_tool_id"),
            "created_from_retrieval_id": payload.get("created_from_retrieval_id"),
            "human_verified": bool(payload.get("human_verified", False)),
            "verification_actor_id": payload.get("verification_actor_id"),
            "verification_timestamp": payload.get("verification_timestamp"),
            "review_status": payload.get("review_status") or "DRAFT",
            "approval_status": payload.get("approval_status") or "DRAFT",
            "approved_version": payload.get("approved_version"),
            "approved_by": payload.get("approved_by"),
            "approved_at": payload.get("approved_at"),
            "baseline_id": payload.get("baseline_id"),
            "policy_decision": payload.get("policy_decision") or "ALLOW",
            "evidence_reference": payload.get("evidence_reference"),
            "classification": payload.get("classification") or "INTERNAL",
            "visibility": payload.get("visibility") or "WORKSPACE",
            "retention_policy_id": payload.get("retention_policy_id"),
        }
        record.update(payload)
        record["id"] = resource_id
        return record

    def _resource_kind(self, resource_type: str) -> str:
        return _slugify(resource_type).replace("-", "_")

    def _current(self, kind: str, record_id: str) -> dict[str, Any] | None:
        record = self.repository.get(kind, record_id)
        return dict(record) if record else None

    def _list(self, kind: str, ctx: DesignExecutionContext, *, include_archived: bool = False, resource_type: str | None = None) -> list[dict[str, Any]]:
        items = [dict(item) for item in self.repository.list(kind) if self._tenant_match(item.get("tenant_id"), ctx.tenant_id)]
        if ctx.workspace_id and kind != "design_workspace":
            items = [item for item in items if not item.get("workspace_id") or _lower(item.get("workspace_id")) == _lower(ctx.workspace_id)]
        if ctx.project_id:
            items = [item for item in items if not item.get("project_id") or _lower(item.get("project_id")) == _lower(ctx.project_id)]
        if not include_archived:
            items = [item for item in items if _upper(item.get("status")) != "ARCHIVED"]
        if resource_type:
            items = [item for item in items if _upper(item.get("content_type") or item.get("artifact_type") or item.get("resource_type")) == _upper(resource_type)]
        return items

    def _list_versions(self, kind: str, resource_id: str, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        version_kind = _version_kind(kind)
        versions = [
            dict(item)
            for item in self.repository.list(version_kind)
            if str(item.get("resource_id") or item.get("id") or "") == resource_id and self._tenant_match(item.get("tenant_id"), ctx.tenant_id)
        ]
        return sorted(versions, key=lambda item: (int(item.get("version_number") or item.get("version") or 0), str(item.get("created_at") or "")))

    def _save_version(self, kind: str, record: dict[str, Any], ctx: DesignExecutionContext, *, change_summary: str = "", previous_version_id: str | None = None) -> dict[str, Any]:
        version_record = {
            "id": _new_id(f"{kind}-version"),
            "resource_id": record["id"],
            "resource_type": kind,
            "tenant_id": record["tenant_id"],
            "organization_id": record["organization_id"],
            "workspace_id": record.get("workspace_id"),
            "project_id": record.get("project_id"),
            "request_id": record.get("request_id"),
            "version_number": int(record.get("version") or 1),
            "content": json.loads(json.dumps(record, default=str)),
            "structured_fields": dict(record),
            "change_summary": change_summary,
            "changed_by": ctx.actor_id,
            "changed_at": _utcnow(),
            "previous_version_id": previous_version_id,
            "content_digest": _digest(record),
            "approval_digest": _digest(
                {
                    "approval_status": record.get("approval_status"),
                    "approved_by": record.get("approved_by"),
                    "approved_at": record.get("approved_at"),
                }
            ),
            "source_references": {
                "source_type": record.get("source_type"),
                "source_id": record.get("source_id"),
                "source_version": record.get("source_version"),
                "source_uri": record.get("source_uri"),
                "source_digest": record.get("source_digest"),
            },
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": dict(record.get("metadata") or {}),
        }
        self.repository.upsert(_version_kind(kind), version_record)
        return version_record

    def _emit(self, event_type: str, ctx: DesignExecutionContext, record: dict[str, Any], *, data: dict[str, Any] | None = None, evidence_reference: str | None = None) -> dict[str, Any]:
        event = _event_envelope(
            event_type=event_type,
            actor_type="user",
            actor_id=ctx.actor_id,
            tenant_id=record["tenant_id"],
            organization_id=record.get("organization_id", ctx.organization_id),
            project_id=record.get("project_id"),
            workflow_id=record.get("request_id"),
            correlation_id=ctx.correlation_id,
            causation_id=ctx.causation_id or ctx.correlation_id,
            data=data or record,
            metadata={"evidence_reference": evidence_reference or record.get("evidence_reference"), "workspace_id": record.get("workspace_id")},
        )
        self.repository.append_event(event)
        return event

    def _evidence(self, kind: str, record: dict[str, Any], ctx: DesignExecutionContext, *, evidence_type: str | None = None) -> dict[str, Any]:
        evidence = {
            "id": _new_id("design-evidence"),
            "tenant_id": record["tenant_id"],
            "organization_id": record["organization_id"],
            "workspace_id": record.get("workspace_id"),
            "project_id": record.get("project_id"),
            "request_id": record.get("request_id"),
            "resource_type": kind,
            "resource_id": record["id"],
            "evidence_type": evidence_type or f"{kind}.evidence",
            "digest": _digest(record),
            "status": "CAPTURED",
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "created_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "metadata": {"status": record.get("status"), "version": record.get("version")},
        }
        self.repository.upsert("design_evidence_package", evidence)
        return evidence

    def _normalise_visibility(self, visibility: str | None) -> str:
        value = _upper(visibility or "WORKSPACE")
        return value if value in {"PRIVATE", "WORKSPACE", "ORGANIZATION", "PARTNER", "CUSTOMER", "PUBLIC"} else "WORKSPACE"

    def _check_classification(self, record: dict[str, Any], ctx: DesignExecutionContext) -> None:
        classification = _upper(record.get("classification") or "INTERNAL")
        visibility = _upper(record.get("visibility") or "WORKSPACE")
        role = _upper(ctx.role)
        if classification == "PUBLIC":
            return
        if classification == "INTERNAL" and role in {"CUSTOMER", "PARTNER"}:
            raise DesignError("design_artifact_forbidden", "Internal design content is not available to this role.", 403)
        if classification in {"CONFIDENTIAL", "RESTRICTED", "REGULATED"} and role in {"CUSTOMER", "PARTNER", "EXTERNAL_REGULATOR"}:
            raise DesignError("design_artifact_forbidden", "Restricted design content is not available to this role.", 403)
        if visibility == "PRIVATE" and not self._admin_override(ctx) and record.get("created_by") != ctx.actor_id:
            raise DesignError("design_artifact_forbidden", "Private content is not available.", 403)

    def _ensure_not_archived(self, record: dict[str, Any]) -> None:
        if _upper(record.get("status")) in {"ARCHIVED", "SUPERSEDED"}:
            raise DesignError("invalid_design_transition", "Archived or superseded resources cannot be mutated.", 409, details={"status": record.get("status")})

    def _validate_transition(self, current_status: str, target_status: str) -> None:
        current = _upper(current_status)
        target = _upper(target_status)
        allowed = DESIGN_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise DesignError("invalid_design_transition", f"Invalid design transition from {current} to {target}.", 409, details={"current_status": current, "target_status": target})

    def _transition(self, kind: str, resource_id: str, target_status: str, ctx: DesignExecutionContext, *, reason: str = "", approval_reference: str | None = None, evidence_reference: str | None = None) -> dict[str, Any]:
        record = self.get_resource(kind, resource_id, ctx)
        self._validate_transition(str(record.get("status") or "DRAFT"), target_status)
        previous_status = str(record.get("status") or "DRAFT")
        record["status"] = _upper(target_status)
        record["updated_by"] = ctx.actor_id
        record["updated_at"] = _utcnow()
        if approval_reference:
            record["approval_reference"] = approval_reference
        if evidence_reference:
            record["evidence_reference"] = evidence_reference
        record["review_status"] = "APPROVED" if record["status"] in {"APPROVED", "BASELINED", "READY_FOR_IMPLEMENTATION", "IMPLEMENTING", "VALIDATING", "VERIFIED"} else record.get("review_status")
        record["approval_status"] = "APPROVED" if record["status"] in {"APPROVED", "BASELINED", "READY_FOR_IMPLEMENTATION", "IMPLEMENTING", "VALIDATING", "VERIFIED"} else record.get("approval_status")
        record["version"] = int(record.get("version") or 1) + 1
        record["change_summary"] = reason or f"{previous_status} -> {target_status}"
        self.repository.upsert(kind, record)
        version = self._save_version(kind, record, ctx, change_summary=record["change_summary"])
        evidence = self._evidence(kind, record, ctx, evidence_type=f"{kind}.transition")
        record["evidence_reference"] = evidence["id"]
        record["policy_decision"] = "ALLOW"
        self.repository.upsert(kind, record)
        self._emit(
            f"design.{kind.replace('_', '.')}.transitioned",
            ctx,
            record,
            data={
                "resource_id": record["id"],
                "previous_status": previous_status,
                "new_status": record["status"],
                "reason": reason,
                "approval_reference": approval_reference,
                "evidence_reference": evidence["id"],
                "version_id": version["id"],
            },
            evidence_reference=evidence["id"],
        )
        return record

    # ------------------------------------------------------------------
    # workspace
    # ------------------------------------------------------------------
    def list_workspaces(self, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return self._list("design_workspace", ctx, include_archived=True)

    def create_workspace(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.create")
        record = self._record(
            "design_workspace",
            ctx,
            payload,
            record_id=str(payload.get("id") or payload.get("experience_workspace_id") or _new_id("design-workspace")),
            status=str(payload.get("status") or "DRAFT"),
        )
        record["slug"] = str(payload.get("slug") or _slugify(record["name"]))
        record["summary"] = dict(payload.get("summary") or {})
        record["brief_ids"] = list(payload.get("brief_ids") or [])
        record["design_system_ids"] = list(payload.get("design_system_ids") or [])
        record["component_library_ids"] = list(payload.get("component_library_ids") or [])
        record["risk"] = list(payload.get("risk") or [])
        record["debt"] = list(payload.get("debt") or [])
        record["approval_status"] = str(payload.get("approval_status") or "DRAFT")
        self.repository.upsert("design_workspace", record)
        self._save_version("design_workspace", record, ctx, change_summary="created")
        evidence = self._evidence("design_workspace", record, ctx, evidence_type="experience_workspace.created")
        record["evidence_reference"] = evidence["id"]
        self.repository.upsert("design_workspace", record)
        self._emit("ExperienceWorkspaceCreated", ctx, record, evidence_reference=evidence["id"])
        return record

    def get_workspace(self, workspace_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        workspace = self.repository.get("design_workspace", workspace_id)
        if workspace is None:
            raise DesignError("design_workspace_not_found", "Design workspace not found.", 404)
        self._ensure_tenant(workspace, ctx)
        self._check_classification(workspace, ctx)
        return workspace

    def update_workspace(self, workspace_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.update")
        workspace = self.get_workspace(workspace_id, ctx)
        self._ensure_not_archived(workspace)
        if "name" in payload:
            workspace["name"] = str(payload["name"])
        if "description" in payload:
            workspace["description"] = str(payload["description"])
        if "status" in payload:
            self._validate_transition(str(workspace.get("status") or "DRAFT"), str(payload["status"]))
            workspace["status"] = _upper(payload["status"])
        workspace["slug"] = str(payload.get("slug") or workspace.get("slug") or _slugify(workspace["name"]))
        workspace["metadata"] = {**dict(workspace.get("metadata") or {}), **dict(payload.get("metadata") or {})}
        workspace["version"] = int(workspace.get("version") or 1) + 1
        workspace["updated_by"] = ctx.actor_id
        workspace["updated_at"] = _utcnow()
        if int(workspace["version"]) > 1 and _upper(workspace.get("approval_status")) == "APPROVED":
            workspace["approval_status"] = "CHANGES_REQUESTED"
        self.repository.upsert("design_workspace", workspace)
        version = self._save_version("design_workspace", workspace, ctx, change_summary="workspace updated")
        evidence = self._evidence("design_workspace", workspace, ctx, evidence_type="experience_workspace.updated")
        workspace["evidence_reference"] = evidence["id"]
        self.repository.upsert("design_workspace", workspace)
        self._emit("ExperienceWorkspaceUpdated", ctx, workspace, data={"resource_id": workspace["id"], "version_id": version["id"]}, evidence_reference=evidence["id"])
        return workspace

    def archive_workspace(self, workspace_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        workspace = self.get_workspace(workspace_id, ctx)
        return self._transition("design_workspace", workspace_id, "ARCHIVED", ctx, reason="workspace archived")

    def restore_workspace(self, workspace_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        workspace = self.get_workspace(workspace_id, ctx)
        if _upper(workspace.get("status")) != "ARCHIVED":
            raise DesignError("invalid_design_transition", "Only archived workspaces can be restored.", 409)
        workspace["status"] = "DRAFT"
        workspace["updated_at"] = _utcnow()
        workspace["updated_by"] = ctx.actor_id
        workspace["version"] = int(workspace.get("version") or 1) + 1
        self.repository.upsert("design_workspace", workspace)
        self._save_version("design_workspace", workspace, ctx, change_summary="workspace restored")
        self._emit("DesignRestored", ctx, workspace, data={"resource_id": workspace["id"]})
        return workspace

    def workspace_summary(self, workspace_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        workspace = self.get_workspace(workspace_id, ctx)
        kinds = {
            "experience_briefs": "experience_brief",
            "research_studies": "research_study",
            "personas": "persona",
            "journeys": "journey_map",
            "service_blueprints": "service_blueprint",
            "information_architecture": "information_architecture",
            "user_flows": "user_flow",
            "wireframes": "wireframe",
            "screen_designs": "screen_design",
            "prototypes": "prototype",
            "design_systems": "design_system",
            "component_libraries": "component_definition",
            "design_tokens": "design_token",
            "open_accessibility_findings": "accessibility_review",
            "open_review_findings": "design_review",
            "design_risks": "design_risk",
            "design_debt": "design_debt_item",
        }
        summary = {
            key: len([item for item in self.repository.list(kind) if self._tenant_match(item.get("tenant_id"), ctx.tenant_id) and _lower(item.get("workspace_id") or item.get("experience_workspace_id") or "") == _lower(workspace_id)])
            for key, kind in kinds.items()
        }
        summary.update(
            {
                "approval_status": workspace.get("approval_status"),
                "baseline_status": workspace.get("baseline_status"),
                "requirement_coverage": self.coverage(ctx, workspace_id=workspace_id).get("requirement_coverage"),
                "architecture_coverage": self.coverage(ctx, workspace_id=workspace_id).get("architecture_coverage"),
                "implementation_coverage": self.coverage(ctx, workspace_id=workspace_id).get("implementation_coverage"),
                "test_coverage": self.coverage(ctx, workspace_id=workspace_id).get("test_coverage"),
                "recent_activity": [event for event in self.repository.list_events(limit=10) if _lower(event.get("organization_id")) == _lower(ctx.organization_id)],
            }
        )
        return {"workspace": workspace, "summary": summary}

    # ------------------------------------------------------------------
    # generic resources
    # ------------------------------------------------------------------
    def list_resources(self, resource_type: str, ctx: DesignExecutionContext, *, include_archived: bool = False) -> list[dict[str, Any]]:
        return self._list(self._resource_kind(resource_type), ctx, include_archived=include_archived)

    def get_resource(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        kind = self._resource_kind(resource_type)
        record = self.repository.get(kind, resource_id)
        if record is None:
            raise DesignError("design_artifact_not_found", f"{resource_type} not found.", 404)
        self._ensure_tenant(record, ctx)
        self._ensure_workspace(record, ctx)
        self._ensure_project(record, ctx)
        self._check_classification(record, ctx)
        return record

    def create_resource(self, resource_type: str, payload: dict[str, Any], ctx: DesignExecutionContext, *, status: str | None = None) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.create")
        kind = self._resource_kind(resource_type)
        normalized = dict(payload)
        normalized["status"] = _upper(status or payload.get("status") or "DRAFT")
        normalized["visibility"] = self._normalise_visibility(payload.get("visibility"))
        normalized["classification"] = _upper(payload.get("classification") or "INTERNAL")
        normalized["resource_type"] = resource_type
        record = self._record(kind, ctx, normalized, record_id=str(payload.get("id") or _new_id(kind)), status=normalized["status"])
        record["name"] = str(payload.get("name") or payload.get("title") or resource_type.replace("_", " ").title())
        record["title"] = str(payload.get("title") or record["name"])
        record["description"] = str(payload.get("description") or payload.get("summary") or "")
        record["change_summary"] = str(payload.get("change_summary") or "created")
        record["artifact_type"] = str(payload.get("artifact_type") or resource_type)
        record["content_type"] = str(payload.get("content_type") or payload.get("artifact_type") or resource_type)
        record["source_digest"] = payload.get("source_digest") or _digest(payload)
        record["source_uri"] = payload.get("source_uri") or payload.get("uri")
        record["source_type"] = payload.get("source_type") or resource_type.upper()
        record["source_id"] = payload.get("source_id")
        record["source_version"] = payload.get("source_version")
        record["creation_method"] = payload.get("creation_method") or "MANUAL"
        record["human_verified"] = bool(payload.get("human_verified", False))
        record["metadata"] = {**dict(record.get("metadata") or {}), **dict(payload.get("metadata") or {})}
        if "approval_status" not in record:
            record["approval_status"] = "DRAFT"
        if "review_status" not in record:
            record["review_status"] = "DRAFT"
        if resource_type in {"screen", "screen_design"}:
            record["states"] = list(payload.get("states") or [])
            record["responsive_behavior"] = dict(payload.get("responsive_behavior") or {})
        if resource_type in {"wireframe"}:
            record["regions"] = list(payload.get("regions") or [])
        if resource_type in {"design_token"}:
            self._validate_tokens([record])
        if resource_type in {"information_architecture"}:
            self._validate_information_architecture(record)
        if resource_type in {"user_flow"}:
            self._validate_user_flow(record)
        if resource_type in {"content_specification"}:
            self._validate_content_specification(record)
        if resource_type in {"component_definition"}:
            self._validate_component_definition(record)
        if resource_type in {"theme"}:
            self._validate_theme(record)
        if resource_type in {"localization_resource"}:
            self._validate_localization_resource(record)
        if resource_type in {"accessibility_requirement"}:
            self._validate_accessibility_requirement(record)
        if resource_type in {"prototype"}:
            self._validate_prototype(record)
        if resource_type in {"design_system"}:
            record["token_set_ids"] = list(payload.get("token_set_ids") or [])
            record["component_library_ids"] = list(payload.get("component_library_ids") or [])
        self.repository.upsert(kind, record)
        self._save_version(kind, record, ctx, change_summary="created")
        evidence = self._evidence(kind, record, ctx)
        record["evidence_reference"] = evidence["id"]
        self.repository.upsert(kind, record)
        self._emit(f"Design{resource_type.title().replace('_', '')}Created", ctx, record, evidence_reference=evidence["id"])
        return record

    def update_resource(self, resource_type: str, resource_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.update")
        kind = self._resource_kind(resource_type)
        record = self.get_resource(resource_type, resource_id, ctx)
        current_status = _upper(record.get("status") or "DRAFT")
        if current_status in {"APPROVED", "BASELINED"}:
            record["status"] = "CHANGES_REQUESTED"
        if "name" in payload:
            record["name"] = str(payload["name"])
        if "title" in payload:
            record["title"] = str(payload["title"])
        if "description" in payload:
            record["description"] = str(payload["description"])
        if "summary" in payload:
            record["summary"] = str(payload["summary"])
        if "status" in payload:
            self._validate_transition(current_status, payload["status"])
            record["status"] = _upper(payload["status"])
        if "visibility" in payload:
            record["visibility"] = self._normalise_visibility(payload["visibility"])
        if "classification" in payload:
            record["classification"] = _upper(payload["classification"])
        if "metadata" in payload:
            record["metadata"] = {**dict(record.get("metadata") or {}), **dict(payload.get("metadata") or {})}
        if "content" in payload:
            record["content"] = payload["content"]
        if "body" in payload:
            record["body"] = payload["body"]
        if "states" in payload:
            record["states"] = list(payload.get("states") or [])
        if "regions" in payload:
            record["regions"] = list(payload.get("regions") or [])
        if "tokens" in payload:
            record["tokens"] = list(payload.get("tokens") or [])
        if "nodes" in payload:
            record["nodes"] = list(payload.get("nodes") or [])
        if "edges" in payload:
            record["edges"] = list(payload.get("edges") or [])
        if "tag_ids" in payload:
            record["tag_ids"] = list(payload.get("tag_ids") or [])
        if "components" in payload:
            record["components"] = list(payload.get("components") or [])
        if "properties" in payload:
            record["properties"] = list(payload.get("properties") or [])
        record["version"] = int(record.get("version") or 1) + 1
        record["updated_at"] = _utcnow()
        record["updated_by"] = ctx.actor_id
        record["change_summary"] = str(payload.get("change_summary") or "updated")
        if _upper(record.get("status")) == "APPROVED" and current_status == "APPROVED":
            record["approval_status"] = "APPROVED"
            record["approved_version"] = record["version"]
        if _upper(record.get("status")) in {"APPROVED", "BASELINED"}:
            record["approval_status"] = "CHANGES_REQUESTED" if record["version"] > 1 else "APPROVED"
        if resource_type == "design_token":
            self._validate_tokens([record])
        if resource_type == "information_architecture":
            self._validate_information_architecture(record)
        if resource_type == "user_flow":
            self._validate_user_flow(record)
        if resource_type == "content_specification":
            self._validate_content_specification(record)
        if resource_type == "component_definition":
            self._validate_component_definition(record)
        if resource_type == "theme":
            self._validate_theme(record)
        if resource_type == "localization_resource":
            self._validate_localization_resource(record)
        if resource_type == "accessibility_requirement":
            self._validate_accessibility_requirement(record)
        if resource_type == "prototype":
            self._validate_prototype(record)
        self.repository.upsert(kind, record)
        version = self._save_version(kind, record, ctx, change_summary=record["change_summary"])
        evidence = self._evidence(kind, record, ctx)
        record["evidence_reference"] = evidence["id"]
        self.repository.upsert(kind, record)
        self._emit(f"Design{resource_type.title().replace('_', '')}Updated", ctx, record, data={"resource_id": record["id"], "version_id": version["id"]}, evidence_reference=evidence["id"])
        return record

    def delete_resource(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        record = self.get_resource(resource_type, resource_id, ctx)
        self._ensure_not_archived(record)
        record["status"] = "ARCHIVED"
        record["updated_by"] = ctx.actor_id
        record["updated_at"] = _utcnow()
        record["version"] = int(record.get("version") or 1) + 1
        self.repository.upsert(self._resource_kind(resource_type), record)
        self._save_version(self._resource_kind(resource_type), record, ctx, change_summary="archived")
        self._emit(f"Design{resource_type.title().replace('_', '')}Archived", ctx, record)
        return record

    def archive_resource(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.transition_resource(resource_type, resource_id, "ARCHIVED", ctx, reason="archived")

    def restore_resource(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        kind = self._resource_kind(resource_type)
        record = self.get_resource(resource_type, resource_id, ctx)
        if _upper(record.get("status")) != "ARCHIVED":
            raise DesignError("invalid_design_transition", "Only archived resources can be restored.", 409)
        record["status"] = "DRAFT"
        record["updated_at"] = _utcnow()
        record["updated_by"] = ctx.actor_id
        record["version"] = int(record.get("version") or 1) + 1
        self.repository.upsert(kind, record)
        self._save_version(kind, record, ctx, change_summary="restored")
        self._emit(f"Design{resource_type.title().replace('_', '')}Restored", ctx, record)
        return record

    def transition_resource(self, resource_type: str, resource_id: str, target_status: str, ctx: DesignExecutionContext, *, reason: str = "", approval_reference: str | None = None, evidence_reference: str | None = None) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.update")
        return self._transition(self._resource_kind(resource_type), resource_id, target_status, ctx, reason=reason, approval_reference=approval_reference, evidence_reference=evidence_reference)

    def list_versions(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return self._list_versions(self._resource_kind(resource_type), resource_id, ctx)

    def get_version(self, resource_type: str, resource_id: str, version_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        versions = self._list_versions(self._resource_kind(resource_type), resource_id, ctx)
        for version in versions:
            if version["id"] == version_id:
                return version
        raise DesignError("design_version_conflict", "Design version not found.", 404)

    def compare_versions(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        versions = self._list_versions(self._resource_kind(resource_type), resource_id, ctx)
        if len(versions) < 2:
            return {"resource_id": resource_id, "versions": versions, "differences": []}
        left, right = versions[-2], versions[-1]
        differences = []
        for key in sorted(set(left.keys()) | set(right.keys())):
            if left.get(key) != right.get(key):
                differences.append({"field": key, "before": left.get(key), "after": right.get(key)})
        return {"resource_id": resource_id, "versions": [left["id"], right["id"]], "differences": differences}

    def restore_version(self, resource_type: str, resource_id: str, version_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        version = self.get_version(resource_type, resource_id, version_id, ctx)
        record = dict(version.get("content") or version.get("structured_fields") or {})
        record["id"] = resource_id
        record["version"] = int(record.get("version") or version.get("version_number") or 1) + 1
        record["updated_at"] = _utcnow()
        record["updated_by"] = ctx.actor_id
        record["status"] = "DRAFT"
        self.repository.upsert(self._resource_kind(resource_type), record)
        self._save_version(self._resource_kind(resource_type), record, ctx, change_summary=f"restored from {version_id}")
        self._emit("DesignVersionRestored", ctx, record, data={"resource_id": resource_id, "version_id": version_id})
        return record

    # ------------------------------------------------------------------
    # research, personas, journeys, blueprints, ia, flows, screens, tokens, themes, components, content, localization, accessibility, prototypes
    # ------------------------------------------------------------------
    def create_research_finding(self, research_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        record = self.get_resource("research_study", research_id, ctx)
        finding = {
            "id": str(payload.get("id") or _new_id("research-finding")),
            "research_id": research_id,
            "tenant_id": record["tenant_id"],
            "workspace_id": record.get("workspace_id"),
            "project_id": record.get("project_id"),
            "created_by": ctx.actor_id,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "summary": str(payload.get("summary") or ""),
            "confidence": float(payload.get("confidence") or 0.5),
            "status": str(payload.get("status") or "OPEN"),
            "evidence": list(payload.get("evidence") or []),
            "recommendations": list(payload.get("recommendations") or []),
        }
        self.repository.upsert("research_finding", finding)
        research = dict(record)
        research.setdefault("findings", [])
        research["findings"] = [*list(research.get("findings") or []), finding]
        research["updated_at"] = _utcnow()
        research["version"] = int(research.get("version") or 1) + 1
        self.repository.upsert("research_study", research)
        self._save_version("research_study", research, ctx, change_summary="finding added")
        self._emit("ResearchStudyUpdated", ctx, research, data={"finding_id": finding["id"]})
        return finding

    def complete_research(self, research_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.transition_resource("research_study", research_id, "ARCHIVED", ctx, reason="research completed")

    def add_journey_stage(self, journey_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        journey = self.get_resource("journey_map", journey_id, ctx)
        stage = {
            "id": str(payload.get("id") or _new_id("journey-stage")),
            "journey_id": journey_id,
            "name": str(payload.get("name") or ""),
            "order": int(payload.get("order") or len(list(journey.get("stages") or [])) + 1),
            "status": str(payload.get("status") or "DRAFT"),
            "steps": list(payload.get("steps") or []),
        }
        journey["stages"] = [*list(journey.get("stages") or []), stage]
        journey["version"] = int(journey.get("version") or 1) + 1
        journey["updated_at"] = _utcnow()
        self.repository.upsert("journey_map", journey)
        self._save_version("journey_map", journey, ctx, change_summary="stage added")
        self._emit("JourneyMapUpdated", ctx, journey, data={"stage_id": stage["id"]})
        return stage

    def update_journey_stage(self, journey_id: str, stage_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        journey = self.get_resource("journey_map", journey_id, ctx)
        stages = list(journey.get("stages") or [])
        for stage in stages:
            if stage.get("id") == stage_id:
                stage.update(payload)
                stage["updated_at"] = _utcnow()
        journey["stages"] = stages
        journey["version"] = int(journey.get("version") or 1) + 1
        journey["updated_at"] = _utcnow()
        self.repository.upsert("journey_map", journey)
        self._save_version("journey_map", journey, ctx, change_summary="stage updated")
        return journey

    def add_blueprint_step(self, blueprint_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        blueprint = self.get_resource("service_blueprint", blueprint_id, ctx)
        step = {
            "id": str(payload.get("id") or _new_id("blueprint-step")),
            "blueprint_id": blueprint_id,
            "lane": _upper(payload.get("lane") or "CUSTOMER_ACTION"),
            "sequence": int(payload.get("sequence") or len(list(blueprint.get("steps") or [])) + 1),
            "actor": str(payload.get("actor") or ""),
            "action": str(payload.get("action") or ""),
            "system": str(payload.get("system") or ""),
            "input": payload.get("input"),
            "output": payload.get("output"),
            "dependency": payload.get("dependency"),
            "failure_mode": str(payload.get("failure_mode") or ""),
            "recovery": str(payload.get("recovery") or ""),
            "policy": str(payload.get("policy") or ""),
            "evidence": str(payload.get("evidence") or ""),
            "owner": str(payload.get("owner") or ""),
            "metric": str(payload.get("metric") or ""),
        }
        blueprint["steps"] = [*list(blueprint.get("steps") or []), step]
        blueprint["version"] = int(blueprint.get("version") or 1) + 1
        blueprint["updated_at"] = _utcnow()
        self.repository.upsert("service_blueprint", blueprint)
        self._save_version("service_blueprint", blueprint, ctx, change_summary="step added")
        return step

    def add_flow_node(self, flow_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        flow = self.get_resource("user_flow", flow_id, ctx)
        node = {
            "id": str(payload.get("id") or _new_id("flow-node")),
            "flow_id": flow_id,
            "type": _upper(payload.get("type") or "SCREEN"),
            "name": str(payload.get("name") or ""),
            "screen_id": payload.get("screen_id"),
            "status": str(payload.get("status") or "DRAFT"),
            "metadata": dict(payload.get("metadata") or {}),
        }
        nodes = list(flow.get("nodes") or [])
        nodes.append(node)
        flow["nodes"] = nodes
        flow["version"] = int(flow.get("version") or 1) + 1
        flow["updated_at"] = _utcnow()
        self._validate_user_flow(flow)
        self.repository.upsert("user_flow", flow)
        self._save_version("user_flow", flow, ctx, change_summary="node added")
        return node

    def add_flow_edge(self, flow_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        flow = self.get_resource("user_flow", flow_id, ctx)
        edge = {
            "id": str(payload.get("id") or _new_id("flow-edge")),
            "flow_id": flow_id,
            "source_id": str(payload.get("source_id") or ""),
            "target_id": str(payload.get("target_id") or ""),
            "type": _upper(payload.get("type") or "PRIMARY"),
            "status": str(payload.get("status") or "DRAFT"),
            "metadata": dict(payload.get("metadata") or {}),
        }
        edges = list(flow.get("edges") or [])
        edges.append(edge)
        flow["edges"] = edges
        flow["version"] = int(flow.get("version") or 1) + 1
        flow["updated_at"] = _utcnow()
        self._validate_user_flow(flow)
        self.repository.upsert("user_flow", flow)
        self._save_version("user_flow", flow, ctx, change_summary="edge added")
        return edge

    def validate_user_flow(self, flow_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        flow = self.get_resource("user_flow", flow_id, ctx)
        findings = self._validate_user_flow(flow)
        result = {
            "id": _new_id("design-validation"),
            "resource_type": "user_flow",
            "resource_id": flow_id,
            "category": "USER_FLOW",
            "status": "PASS" if not findings else "FAIL",
            "findings": findings,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "tenant_id": flow["tenant_id"],
            "workspace_id": flow.get("workspace_id"),
            "project_id": flow.get("project_id"),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
        }
        self.repository.upsert("design_validation_result", result)
        self._emit("UserFlowValidated", ctx, flow, data=result)
        return result

    def create_traceability_link(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        source_type = _upper(payload.get("source_type") or "")
        target_type = _upper(payload.get("target_type") or "")
        relationship = _upper(payload.get("relationship") or "")
        if not source_type or not target_type or not relationship:
            raise DesignError("design_relationship_invalid", "Traceability link requires source, target and relationship.", 400)
        if _lower(payload.get("source_id")) == _lower(payload.get("target_id")):
            raise DesignError("design_traceability_gap", "Self-referential traceability links are not allowed.", 400)
        link = {
            "id": str(payload.get("id") or _new_id("design-link")),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": payload.get("workspace_id") or ctx.workspace_id,
            "project_id": payload.get("project_id") or ctx.project_id,
            "source_type": source_type,
            "source_id": str(payload.get("source_id") or ""),
            "target_type": target_type,
            "target_id": str(payload.get("target_id") or ""),
            "relationship": relationship,
            "created_by": ctx.actor_id,
            "created_at": _utcnow(),
            "evidence_reference": payload.get("evidence_reference"),
            "creation_method": payload.get("creation_method") or "MANUAL",
            "confidence": float(payload.get("confidence") or 1.0),
            "verification_status": payload.get("verification_status") or "VERIFIED",
        }
        self.repository.upsert("design_traceability_link", link)
        self._emit("DesignTraceabilityLinkCreated", ctx, link)
        return link

    def list_traceability_links(self, ctx: DesignExecutionContext, *, resource_type: str | None = None, resource_id: str | None = None) -> list[dict[str, Any]]:
        links = [item for item in self.repository.list("design_traceability_link") if self._tenant_match(item.get("tenant_id"), ctx.tenant_id)]
        if resource_type and resource_id:
            matches = _upper(resource_type)
            links = [
                item
                for item in links
                if (
                    _upper(item.get("source_type")) == matches and _lower(item.get("source_id")) == _lower(resource_id)
                )
                or (
                    _upper(item.get("target_type")) == matches and _lower(item.get("target_id")) == _lower(resource_id)
                )
            ]
        return links

    def traceability_snapshot(self, ctx: DesignExecutionContext) -> dict[str, Any]:
        links = self.list_traceability_links(ctx)
        snapshot = {
            "id": _new_id("design-traceability-snapshot"),
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "link_count": len(links),
            "resource_count": len({link["source_id"] for link in links} | {link["target_id"] for link in links}),
            "links": links,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
        }
        self.repository.upsert("design_traceability_snapshot", snapshot)
        return snapshot

    def coverage(self, ctx: DesignExecutionContext, *, workspace_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
        target_workspace = workspace_id or ctx.workspace_id
        target_project = project_id or ctx.project_id
        artifact_kinds = [
            "experience_brief",
            "persona",
            "journey_map",
            "service_blueprint",
            "information_architecture",
            "user_flow",
            "wireframe",
            "screen_design",
            "component_definition",
            "design_system",
            "design_token",
            "theme",
            "content_specification",
            "localization_resource",
            "accessibility_requirement",
            "prototype",
        ]
        artifacts = []
        for kind in artifact_kinds:
            for item in self.repository.list(kind):
                if not self._tenant_match(item.get("tenant_id"), ctx.tenant_id):
                    continue
                if target_workspace and _lower(item.get("workspace_id") or item.get("experience_workspace_id")) != _lower(target_workspace):
                    continue
                if target_project and _lower(item.get("project_id") or item.get("design_project_id")) != _lower(target_project):
                    continue
                artifacts.append(item)
        links = self.list_traceability_links(ctx)
        linked_resources = {link["source_id"] for link in links} | {link["target_id"] for link in links}
        requirements = [item for item in self.repository.list("requirement") if self._tenant_match(item.get("tenant_id"), ctx.tenant_id)]
        required_count = len(requirements) or len(artifacts) or 1
        requirement_coverage = round(min(len(requirements), len(linked_resources)) / required_count, 2)
        architecture_coverage = round(min(len([item for item in artifacts if item.get("architecture_component_ids") or item.get("architecture_references")]), len(linked_resources)) / max(len(artifacts), 1), 2)
        implementation_coverage = round(min(len([item for item in artifacts if _upper(item.get("status")) in {"IMPLEMENTING", "VALIDATING", "VERIFIED", "BASELINED", "APPROVED"}]), len(linked_resources)) / max(len(artifacts), 1), 2)
        test_coverage = round(min(len([item for item in self.repository.list("test_execution") if self._tenant_match(item.get("tenant_id"), ctx.tenant_id)]), len(linked_resources)) / max(len(artifacts), 1), 2)
        traceability_coverage = round((requirement_coverage + architecture_coverage + implementation_coverage + test_coverage) / 4, 2)
        gaps = []
        if requirement_coverage < 1:
            gaps.append("requirements_missing_links")
        if architecture_coverage < 1:
            gaps.append("architecture_missing_links")
        if implementation_coverage < 1:
            gaps.append("implementation_missing_links")
        if test_coverage < 1:
            gaps.append("tests_missing_links")
        result = {
            "tenant_id": ctx.tenant_id,
            "workspace_id": target_workspace,
            "project_id": target_project,
            "requirement_coverage": requirement_coverage,
            "architecture_coverage": architecture_coverage,
            "implementation_coverage": implementation_coverage,
            "test_coverage": test_coverage,
            "traceability_coverage": traceability_coverage,
            "gaps": gaps,
            "created_at": _utcnow(),
        }
        self.repository.upsert("design_coverage", {**result, "id": _new_id("design-coverage"), "status": "ACTIVE"})
        return result

    def calculate_impact(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        links = self.list_traceability_links(ctx, resource_type=resource_type, resource_id=resource_id)
        impacted = []
        for link in links:
            if _lower(link.get("source_id")) == _lower(resource_id):
                impacted.append({"resource_type": link["target_type"], "resource_id": link["target_id"], "relationship": link["relationship"]})
            else:
                impacted.append({"resource_type": link["source_type"], "resource_id": link["source_id"], "relationship": link["relationship"]})
        impact = {
            "id": _new_id("design-impact"),
            "resource_type": _upper(resource_type),
            "resource_id": resource_id,
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "affected_requirements": [item for item in impacted if _upper(item["resource_type"]) == "REQUIREMENT"],
            "affected_architecture_components": [item for item in impacted if "ARCHITECTURE" in _upper(item["resource_type"])],
            "affected_personas": [item for item in impacted if _upper(item["resource_type"]) == "PERSONA"],
            "affected_journeys": [item for item in impacted if _upper(item["resource_type"]) == "JOURNEY_MAP"],
            "affected_flows": [item for item in impacted if _upper(item["resource_type"]) == "USER_FLOW"],
            "affected_screens": [item for item in impacted if _upper(item["resource_type"]) in {"SCREEN", "SCREEN_DESIGN"}],
            "affected_components": [item for item in impacted if _upper(item["resource_type"]) == "COMPONENT_DEFINITION"],
            "affected_tokens": [item for item in impacted if _upper(item["resource_type"]) == "DESIGN_TOKEN"],
            "affected_themes": [item for item in impacted if _upper(item["resource_type"]) == "THEME"],
            "severity": "HIGH" if impacted else "LOW",
            "required_reviewers": ["DESIGN", "ACCESSIBILITY", "ARCHITECTURE"] if impacted else [],
            "required_approvals": ["DESIGN_APPROVAL"] if impacted else [],
            "confidence": 0.78 if impacted else 0.25,
            "unresolved_references": [item for item in impacted if not self.repository.get(self._resource_kind(item["resource_type"]), item["resource_id"])],
            "evidence_references": [item.get("evidence_reference") for item in self.repository.list("design_evidence_package") if _lower(item.get("resource_id")) == _lower(resource_id)],
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_impact_analysis", impact)
        self._emit("DesignImpactCalculated", ctx, {"tenant_id": ctx.tenant_id, "id": impact["id"], "resource_id": resource_id})
        return impact

    def calculate_drift(self, ctx: DesignExecutionContext, *, resource_type: str | None = None, resource_id: str | None = None) -> dict[str, Any]:
        if not resource_type or not resource_id:
            raise DesignError("design_drift_source_unavailable", "Design drift calculation requires a resource and rendered evidence.", 400)
        record = self.get_resource(resource_type, resource_id, ctx)
        missing_sources = [name for name in ("approval_status", "baseline_id", "evidence_reference") if not record.get(name)]
        drift = {
            "id": _new_id("design-drift"),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "resource_type": _upper(resource_type),
            "resource_id": resource_id,
            "status": "DRIFT_DETECTED" if missing_sources else "NO_DRIFT",
            "missing_sources": missing_sources,
            "findings": [] if not missing_sources else [{"field": field, "reason": "evidence unavailable"} for field in missing_sources],
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_drift", drift)
        self._emit("DesignDriftDetected", ctx, record, data=drift)
        return drift

    def create_review(self, resource_type: str, resource_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.review")
        record = self.get_resource(resource_type, resource_id, ctx)
        review = {
            "id": str(payload.get("id") or _new_id("design-review")),
            "resource_type": _upper(resource_type),
            "resource_id": resource_id,
            "tenant_id": record["tenant_id"],
            "workspace_id": record.get("workspace_id"),
            "project_id": record.get("project_id"),
            "review_type": _upper(payload.get("review_type") or "PRODUCT"),
            "status": "OPEN",
            "findings": list(payload.get("findings") or []),
            "required_role": str(payload.get("required_role") or "DESIGN"),
            "created_by": ctx.actor_id,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
        }
        self.repository.upsert("design_review", review)
        self._emit("DesignReviewStarted", ctx, record, data=review)
        return review

    def complete_review(self, resource_type: str, resource_id: str, review_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        review = self.repository.get("design_review", review_id)
        if review is None:
            raise DesignError("design_artifact_not_found", "Design review not found.", 404)
        record = self.get_resource(resource_type, resource_id, ctx)
        review["status"] = _upper(payload.get("status") or payload.get("decision") or "APPROVED")
        review["findings"] = list(payload.get("findings") or review.get("findings") or [])
        review["updated_at"] = _utcnow()
        review["completed_by"] = ctx.actor_id
        self.repository.upsert("design_review", review)
        self._emit("DesignReviewCompleted", ctx, record, data=review)
        return review

    def create_approval(self, resource_type: str, resource_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.approve")
        record = self.get_resource(resource_type, resource_id, ctx)
        approval = {
            "id": str(payload.get("id") or _new_id("design-approval")),
            "resource_type": _upper(resource_type),
            "resource_id": resource_id,
            "tenant_id": record["tenant_id"],
            "workspace_id": record.get("workspace_id"),
            "project_id": record.get("project_id"),
            "decision": "PENDING",
            "required_role": str(payload.get("required_role") or "DESIGN"),
            "risk_severity": str(payload.get("risk_severity") or "MEDIUM"),
            "reason": str(payload.get("reason") or ""),
            "conditions": list(payload.get("conditions") or []),
            "created_by": ctx.actor_id,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
        }
        self.repository.upsert("design_approval", approval)
        self._emit("DesignApprovalRequested", ctx, record, data=approval)
        return approval

    def decide_approval(self, resource_type: str, resource_id: str, approval_id: str, decision: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        approval = self.repository.get("design_approval", approval_id)
        if approval is None:
            raise DesignError("design_artifact_not_found", "Design approval not found.", 404)
        record = self.get_resource(resource_type, resource_id, ctx)
        if _upper(decision) == "APPROVED" and approval.get("required_role") and _upper(approval["required_role"]) not in {_upper(ctx.role), "DESIGN", "UI_UX_DESIGNER", "ARCHITECT"} and not self._admin_override(ctx):
            raise DesignError("design_risk_acceptance_forbidden", "Approval by this role is not permitted.", 403)
        if _upper(decision) == "APPROVED":
            approval["decision"] = "APPROVED"
            record["status"] = "APPROVED"
            record["approval_status"] = "APPROVED"
            record["approved_by"] = ctx.actor_id
            record["approved_at"] = _utcnow()
            record["approved_version"] = int(record.get("version") or 1)
        elif _upper(decision) == "REJECTED":
            approval["decision"] = "REJECTED"
            record["status"] = "REJECTED"
            record["approval_status"] = "REJECTED"
        else:
            approval["decision"] = "CHANGES_REQUESTED"
            record["status"] = "CHANGES_REQUESTED"
            record["approval_status"] = "CHANGES_REQUESTED"
        approval["reason"] = str(payload.get("reason") or approval.get("reason") or "")
        approval["updated_at"] = _utcnow()
        self.repository.upsert("design_approval", approval)
        self.repository.upsert(self._resource_kind(resource_type), record)
        self._save_version(self._resource_kind(resource_type), record, ctx, change_summary=f"approval {approval['decision'].lower()}")
        self._emit("DesignApproved" if approval["decision"] == "APPROVED" else "DesignRejected", ctx, record, data=approval)
        return approval

    def create_baseline(self, design_project_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.baseline")
        resources = list(payload.get("resource_ids") or payload.get("items") or [])
        if not resources:
            raise DesignError("design_handoff_not_ready", "A design baseline requires approved artifacts.", 400)
        items = []
        for resource_ref in resources:
            if isinstance(resource_ref, dict):
                resource_type = str(resource_ref.get("resource_type") or resource_ref.get("type") or "design_artifact")
                resource_id = str(resource_ref.get("resource_id") or resource_ref.get("id") or "")
            else:
                resource_type = "design_artifact"
                resource_id = str(resource_ref)
            if not resource_id:
                continue
            try:
                record = self.get_resource(resource_type, resource_id, ctx)
            except DesignError:
                record = None
            if record is None or _upper(record.get("approval_status")) != "APPROVED":
                raise DesignError("design_not_approved", "Baseline can only include approved resources.", 409)
            items.append(
                {
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "resource_version": int(record.get("version") or 1),
                    "approval_references": [record.get("approved_by")],
                    "timestamp": _utcnow(),
                    "content_digest": _digest(record),
                }
            )
        baseline = {
            "id": str(payload.get("id") or _new_id("design-baseline")),
            "design_project_id": design_project_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "items": items,
            "approval_references": list(payload.get("approval_references") or []),
            "baseline_digest": _digest(items),
            "status": "APPROVED",
            "created_by": ctx.actor_id,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "policy_decision": "ALLOW",
        }
        self.repository.upsert("design_baseline", baseline)
        self._emit("DesignBaselineCreated", ctx, baseline, data=baseline)
        return baseline

    def supersede_baseline(self, baseline_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        baseline = self.repository.get("design_baseline", baseline_id)
        if baseline is None:
            raise DesignError("design_artifact_not_found", "Design baseline not found.", 404)
        self._ensure_tenant(baseline, ctx)
        baseline["status"] = "SUPERSEDED"
        baseline["updated_at"] = _utcnow()
        self.repository.upsert("design_baseline", baseline)
        self._emit("DesignBaselineSuperseded", ctx, baseline)
        return baseline

    def verify_baseline(self, baseline_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        baseline = self.repository.get("design_baseline", baseline_id)
        if baseline is None:
            raise DesignError("design_artifact_not_found", "Design baseline not found.", 404)
        self._ensure_tenant(baseline, ctx)
        missing = []
        for item in baseline.get("items") or []:
            record = self.repository.get(self._resource_kind(str(item.get("resource_type") or "design_artifact")), str(item.get("resource_id") or ""))
            if record is None:
                missing.append(item)
        return {"baseline_id": baseline_id, "verified": not missing, "missing": missing, "status": "PASS" if not missing else "FAIL"}

    def import_ai_execution(self, execution_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.import")
        resource_type = str(payload.get("resource_type") or "experience_brief")
        record = self.create_resource(
            resource_type,
            {
                **dict(payload),
                "created_from_execution_id": execution_id,
                "created_from_agent_id": payload.get("created_from_agent_id") or payload.get("agent_id"),
                "created_from_retrieval_id": payload.get("created_from_retrieval_id"),
                "source_type": "AI_EXECUTION",
                "source_id": execution_id,
                "creation_method": "AI_GENERATED",
                "human_verified": False,
                "status": "DRAFT",
                "review_status": "DRAFT",
                "approval_status": "DRAFT",
            },
            ctx,
        )
        import_record = {
            "id": _new_id("design-import"),
            "execution_id": execution_id,
            "resource_type": resource_type,
            "resource_id": record["id"],
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "validation_status": "IMPORTED",
            "validation_message": "AI execution imported without auto-approval.",
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "evidence_reference": record.get("evidence_reference"),
            "metadata": {"source_digests": list(payload.get("source_digests") or []), "citations": list(payload.get("citations") or [])},
        }
        self.repository.upsert("design_import", import_record)
        self._emit("DesignImport", ctx, record, data=import_record)
        return {"import": import_record, "resource": record}

    def export(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.export")
        resource_type = str(payload.get("resource_type") or "experience_brief")
        resource_id = str(payload.get("resource_id") or "")
        if not resource_id:
            raise DesignError("design_export_failed", "A resource id is required.", 400)
        record = self.get_resource(resource_type, resource_id, ctx)
        export = {
            "id": _new_id("design-export"),
            "resource_type": resource_type,
            "resource_id": resource_id,
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "format": str(payload.get("format") or "JSON"),
            "digest": _digest(record),
            "manifest": record,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "evidence_reference": record.get("evidence_reference"),
        }
        self.repository.upsert("design_export", export)
        self._emit("DesignExport", ctx, record, data=export)
        return export

    def create_handoff(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.manage_handoffs")
        handoff = {
            "id": str(payload.get("id") or _new_id("design-handoff")),
            "design_baseline_id": str(payload.get("design_baseline_id") or ""),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "screen_specifications": list(payload.get("screen_specifications") or []),
            "component_contracts": list(payload.get("component_contracts") or []),
            "token_package": dict(payload.get("token_package") or {}),
            "theme_package": dict(payload.get("theme_package") or {}),
            "content_package": dict(payload.get("content_package") or {}),
            "localization_package": dict(payload.get("localization_package") or {}),
            "accessibility_requirements": list(payload.get("accessibility_requirements") or []),
            "responsive_requirements": list(payload.get("responsive_requirements") or []),
            "analytics_events": list(payload.get("analytics_events") or []),
            "api_references": list(payload.get("api_references") or []),
            "architecture_references": list(payload.get("architecture_references") or []),
            "test_requirements": list(payload.get("test_requirements") or []),
            "visual_baseline_references": list(payload.get("visual_baseline_references") or []),
            "digest": _digest(payload),
            "approval_references": list(payload.get("approval_references") or []),
            "status": "DRAFT",
            "created_by": ctx.actor_id,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
        }
        self.repository.upsert("design_handoff", handoff)
        return handoff

    def validate_handoff(self, handoff_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        handoff = self.repository.get("design_handoff", handoff_id)
        if handoff is None:
            raise DesignError("design_handoff_invalid", "Design handoff not found.", 404)
        baseline = self.repository.get("design_baseline", handoff.get("design_baseline_id"))
        if baseline is None or _upper(baseline.get("status")) not in {"APPROVED", "ACTIVE"}:
            raise DesignError("design_handoff_not_ready", "Design baseline must be approved before handoff.", 409)
        result = {
            "id": _new_id("design-validation"),
            "resource_type": "design_handoff",
            "resource_id": handoff_id,
            "status": "PASS",
            "findings": [],
            "created_at": _utcnow(),
        }
        self.repository.upsert("design_validation_result", result)
        return result

    def search(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "design.read")
        query = _lower(payload.get("query"))
        resource_types = [str(item) for item in list(payload.get("resource_types") or [])]
        results: list[dict[str, Any]] = []
        for kind in [
            "experience_brief",
            "research_study",
            "persona",
            "journey_map",
            "service_blueprint",
            "information_architecture",
            "user_flow",
            "wireframe",
            "screen_design",
            "design_system",
            "design_token",
            "theme",
            "component_definition",
            "interaction_pattern",
            "responsive_specification",
            "content_specification",
            "localization_resource",
            "accessibility_requirement",
            "prototype",
            "design_baseline",
            "design_handoff",
        ]:
            if resource_types and kind not in resource_types:
                continue
            for item in self.repository.list(kind):
                if not self._tenant_match(item.get("tenant_id"), ctx.tenant_id):
                    continue
                if ctx.workspace_id and _lower(item.get("workspace_id") or item.get("experience_workspace_id")) not in {"", _lower(ctx.workspace_id)}:
                    continue
                if ctx.project_id and _lower(item.get("project_id") or item.get("design_project_id")) not in {"", _lower(ctx.project_id)}:
                    continue
                if item.get("classification") and _upper(item.get("classification")) in {"RESTRICTED", "REGULATED"} and _upper(ctx.role) in {"CUSTOMER", "PARTNER", "EXTERNAL_REGULATOR"}:
                    continue
                text = json.dumps(item, sort_keys=True, default=str).lower()
                if query and query not in text:
                    continue
                results.append(
                    {
                        "resource_type": kind,
                        "resource_id": item["id"],
                        "title": item.get("title") or item.get("name"),
                        "snippet": str(item.get("summary") or item.get("description") or item.get("body") or "")[:180],
                        "status": item.get("status"),
                        "classification": item.get("classification"),
                        "workspace_id": item.get("workspace_id"),
                        "project_id": item.get("project_id"),
                        "updated_at": item.get("updated_at"),
                        "score": 0.95 if query and query in text else 0.5,
                        "citations": [item.get("evidence_reference")] if item.get("evidence_reference") else [],
                    }
                )
        search_record = {
            "id": _new_id("design-search"),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "query": payload.get("query"),
            "resource_types": resource_types,
            "results_count": len(results),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_search_query", search_record)
        return {"results": results, "search": search_record}

    def retrieve(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "knowledge.read")
        query = str(payload.get("query") or "")
        search = self.search({"query": query, "resource_types": payload.get("allowed_resource_types") or []}, ctx)
        results = [
            {**result, "citations": result.get("citations") or [f"citation:{result['resource_type']}:{result['resource_id']}"]}
            for result in search["results"][: int(payload.get("maximum_results") or 5)]
        ]
        retrieval = {
            "id": _new_id("design-retrieval"),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "query": query,
            "results": results,
            "citations": [citation for result in results for citation in result.get("citations") or []],
            "search_strategy": str(payload.get("purpose") or "hybrid"),
            "limitations": [] if results else ["No authorized results found"],
            "query_digest": _digest(query),
            "index_version": "local-1",
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_retrieval_record", retrieval)
        return retrieval

    # ------------------------------------------------------------------
    # validation helpers
    # ------------------------------------------------------------------
    def _validate_tokens(self, tokens: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        tokens = list(tokens)
        seen_paths: set[str] = set()
        graph = {str(token.get("path") or token.get("name") or token.get("id")): str(token.get("reference") or "") for token in tokens}
        findings = []
        for token in tokens:
            path = str(token.get("path") or token.get("name") or token.get("id") or "")
            reference = str(token.get("reference") or "")
            if not path:
                findings.append({"code": "design_token_invalid", "message": "Token path is required."})
            if path in seen_paths:
                findings.append({"code": "design_token_invalid", "message": f"Duplicate token path {path}."})
            seen_paths.add(path)
            if token.get("category") and _upper(token["category"]) not in TOKEN_CATEGORIES:
                findings.append({"code": "design_token_invalid", "message": f"Unsupported token category {token['category']}."})
            if token.get("level") and _upper(token["level"]) not in TOKEN_LEVELS:
                findings.append({"code": "design_token_invalid", "message": f"Unsupported token level {token['level']}."})
            if token.get("value") in (None, ""):
                findings.append({"code": "design_token_invalid", "message": f"Token {path} requires a value."})
            if reference and reference == path:
                findings.append({"code": "design_token_cycle_detected", "message": f"Token {path} references itself."})
        if any(graph.get(path) == path for path in graph):
            findings.append({"code": "design_token_cycle_detected", "message": "Token reference cycle detected."})
        if findings:
            raise DesignError("design_token_invalid", "Invalid design token set.", 400, details={"findings": findings})
        return []

    def _validate_information_architecture(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        nodes = list(record.get("nodes") or [])
        routes = [str(node.get("route") or "") for node in nodes]
        findings = []
        if len(routes) != len(set(routes)):
            findings.append({"code": "design_navigation_invalid", "message": "Duplicate routes detected."})
        if any(not node.get("label") for node in nodes):
            findings.append({"code": "design_navigation_invalid", "message": "Missing labels detected."})
        if any(not node.get("localization_key") for node in nodes):
            findings.append({"code": "design_localization_incomplete", "message": "Missing localization keys detected."})
        if any(_upper(node.get("visibility") or "WORKSPACE") == "PUBLIC" and _upper(node.get("permission") or "") == "FORBIDDEN" for node in nodes):
            findings.append({"code": "design_navigation_invalid", "message": "Forbidden-route exposure detected."})
        if findings:
            raise DesignError("design_navigation_invalid", "Information architecture validation failed.", 400, details={"findings": findings})
        return []

    def _validate_user_flow(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        nodes = list(record.get("nodes") or [])
        edges = list(record.get("edges") or [])
        findings = []
        if not nodes:
            findings.append({"code": "design_flow_invalid", "message": "Flow requires nodes."})
        if not any(_upper(node.get("type") or node.get("node_type")) == "START" for node in nodes):
            findings.append({"code": "design_flow_invalid", "message": "Flow missing START node."})
        if not any(_upper(node.get("type") or node.get("node_type")) == "END" for node in nodes):
            findings.append({"code": "design_flow_invalid", "message": "Flow missing END node."})
        node_ids = {str(node.get("id")) for node in nodes}
        reachable = set()
        adjacency: dict[str, list[str]] = {}
        for edge in edges:
            src = str(edge.get("source_id") or "")
            tgt = str(edge.get("target_id") or "")
            if src and tgt:
                adjacency.setdefault(src, []).append(tgt)
        frontier = [node["id"] for node in nodes if _upper(node.get("type") or node.get("node_type")) == "START"]
        while frontier:
            current = frontier.pop(0)
            if current in reachable:
                continue
            reachable.add(current)
            frontier.extend(adjacency.get(current, []))
        unreachable = [node_id for node_id in node_ids if node_id not in reachable]
        if unreachable:
            findings.append({"code": "design_flow_invalid", "message": "Unreachable nodes detected.", "nodes": unreachable})
        if any(edge.get("type") and _upper(edge["type"]) not in FLOW_EDGE_TYPES for edge in edges):
            findings.append({"code": "design_flow_invalid", "message": "Invalid edge type detected."})
        if findings:
            raise DesignError("design_flow_invalid", "User flow validation failed.", 400, details={"findings": findings})
        return []

    def _validate_content_specification(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        findings = []
        if not record.get("key"):
            findings.append({"code": "design_content_invalid", "message": "Missing content key."})
        if not record.get("text") and not record.get("body"):
            findings.append({"code": "design_content_invalid", "message": "Missing content text."})
        if record.get("legal_reference") and _upper(record.get("approval_status") or "") != "APPROVED":
            findings.append({"code": "design_content_invalid", "message": "Unapproved legal content cannot publish."})
        if findings:
            raise DesignError("design_content_invalid", "Content specification validation failed.", 400, details={"findings": findings})
        return []

    def _validate_component_definition(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        findings = []
        if not record.get("name"):
            findings.append({"code": "design_component_invalid", "message": "Missing component name."})
        if not record.get("properties"):
            findings.append({"code": "design_component_invalid", "message": "Missing properties."})
        if not record.get("keyboard_behavior") or not record.get("focus_behavior") or not record.get("screen_reader_behavior"):
            findings.append({"code": "design_component_invalid", "message": "Missing accessibility interaction contracts."})
        if findings:
            raise DesignError("design_component_invalid", "Component validation failed.", 400, details={"findings": findings})
        return []

    def _validate_theme(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        if not record.get("name"):
            raise DesignError("design_theme_invalid", "Theme requires a name.", 400)
        return []

    def _validate_localization_resource(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        findings = []
        if not record.get("key") or not record.get("locale"):
            findings.append({"code": "design_localization_incomplete", "message": "Localization key and locale are required."})
        if record.get("fallback") in {None, ""}:
            findings.append({"code": "design_localization_incomplete", "message": "Localization fallback is required."})
        if findings:
            raise DesignError("design_localization_incomplete", "Localization validation failed.", 400, details={"findings": findings})
        return []

    def _validate_accessibility_requirement(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        if _upper(record.get("standard") or "") not in ACCESSIBILITY_TARGETS:
            raise DesignError("design_accessibility_requirement_missing", "Unsupported accessibility standard.", 400)
        return []

    def _validate_prototype(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        if _upper(record.get("type") or "") not in PROTOTYPE_TYPES:
            raise DesignError("design_artifact_forbidden", "Unsupported prototype type.", 400)
        return []

    # ------------------------------------------------------------------
    # special helpers for lists and details
    # ------------------------------------------------------------------
    def list_versions_for(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return self.list_versions(resource_type, resource_id, ctx)

    def list_reviews(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return [item for item in self.repository.list("design_review") if self._tenant_match(item.get("tenant_id"), ctx.tenant_id) and _lower(item.get("resource_id")) == _lower(resource_id) and _upper(item.get("resource_type")) == _upper(resource_type)]

    def list_approvals(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return [item for item in self.repository.list("design_approval") if self._tenant_match(item.get("tenant_id"), ctx.tenant_id) and _lower(item.get("resource_id")) == _lower(resource_id) and _upper(item.get("resource_type")) == _upper(resource_type)]

    def list_risks(self, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return self._list("design_risk", ctx, include_archived=True)

    def list_debt(self, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return self._list("design_debt_item", ctx, include_archived=True)

    def list_search_history(self, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return [item for item in self.repository.list("design_search_query") if self._tenant_match(item.get("tenant_id"), ctx.tenant_id)]

    def validate_artifact(self, resource_type: str, resource_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        record = self.get_resource(resource_type, resource_id, ctx)
        findings: list[dict[str, Any]] = []
        try:
            if _upper(resource_type) in {"DESIGN_TOKEN"}:
                self._validate_tokens([record])
            elif _upper(resource_type) in {"INFORMATION_ARCHITECTURE"}:
                self._validate_information_architecture(record)
            elif _upper(resource_type) in {"USER_FLOW"}:
                self._validate_user_flow(record)
            elif _upper(resource_type) in {"CONTENT_SPECIFICATION"}:
                self._validate_content_specification(record)
            elif _upper(resource_type) in {"COMPONENT_DEFINITION"}:
                self._validate_component_definition(record)
            elif _upper(resource_type) in {"THEME"}:
                self._validate_theme(record)
            elif _upper(resource_type) in {"LOCALIZATION_RESOURCE"}:
                self._validate_localization_resource(record)
            elif _upper(resource_type) in {"ACCESSIBILITY_REQUIREMENT"}:
                self._validate_accessibility_requirement(record)
            elif _upper(resource_type) in {"PROTOTYPE"}:
                self._validate_prototype(record)
            elif _upper(resource_type) in {"WIREFRAME", "SCREEN_DESIGN"}:
                if not record.get("states") and _upper(resource_type) == "SCREEN_DESIGN":
                    findings.append({"code": "design_screen_invalid", "message": "Screen states are required."})
            status = "PASS"
        except DesignError as error:
            findings = [{"code": error.code, "message": error.message, "details": error.details}]
            status = "FAIL"
        result = {
            "id": _new_id("design-validation"),
            "resource_type": _upper(resource_type),
            "resource_id": resource_id,
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "status": status,
            "findings": findings,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
        }
        self.repository.upsert("design_validation_result", result)
        self._emit("DesignValidationCompleted", ctx, record, data=result)
        return result

    def validate_fitness(self, fitness_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        fitness = self.repository.get("design_validation_rule", fitness_id)
        if fitness is None:
            fitness = {"id": fitness_id, "name": fitness_id, "status": "ENABLED"}
        result = {
            "id": _new_id("design-fitness-result"),
            "fitness_id": fitness_id,
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "status": "PASS",
            "findings": [],
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_metric_record", result)
        self._emit("DesignFitnessExecutionCompleted", ctx, fitness, data=result)
        return result

    def create_metric_record(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        record = {
            "id": str(payload.get("id") or _new_id("design-metric")),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "resource_type": payload.get("resource_type"),
            "resource_id": payload.get("resource_id"),
            "metric": str(payload.get("metric") or ""),
            "value": payload.get("value"),
            "unit": str(payload.get("unit") or ""),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_metric_record", record)
        return record

    def create_risk(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        risk = {
            "id": str(payload.get("id") or _new_id("design-risk")),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "resource_type": payload.get("resource_type"),
            "resource_id": payload.get("resource_id"),
            "category": _upper(payload.get("category") or "USABILITY"),
            "severity": _upper(payload.get("severity") or "MEDIUM"),
            "status": "OPEN",
            "description": str(payload.get("description") or ""),
            "mitigation": list(payload.get("mitigation") or []),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_risk", risk)
        return risk

    def create_debt(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        debt = {
            "id": str(payload.get("id") or _new_id("design-debt")),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "resource_type": payload.get("resource_type"),
            "resource_id": payload.get("resource_id"),
            "category": _upper(payload.get("category") or "MISSING_STATE"),
            "status": "OPEN",
            "description": str(payload.get("description") or ""),
            "owner": str(payload.get("owner") or ""),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_debt_item", debt)
        return debt

    def create_import_record(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        record = {
            "id": str(payload.get("id") or _new_id("design-import")),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "source": str(payload.get("source") or "manual"),
            "digest": str(payload.get("digest") or _digest(payload)),
            "uploader": ctx.actor_id,
            "content_type": str(payload.get("content_type") or "application/json"),
            "parser": str(payload.get("parser") or "json"),
            "parser_version": str(payload.get("parser_version") or "1.0"),
            "validation_status": str(payload.get("validation_status") or "PENDING"),
            "malware_scan_status": str(payload.get("malware_scan_status") or "NOT_RUN"),
            "created_resources": list(payload.get("created_resources") or []),
            "rejected_resources": list(payload.get("rejected_resources") or []),
            "warnings": list(payload.get("warnings") or []),
            "evidence_reference": payload.get("evidence_reference"),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_import", record)
        return record

    def create_export_record(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        record = {
            "id": str(payload.get("id") or _new_id("design-export")),
            "tenant_id": ctx.tenant_id,
            "workspace_id": ctx.workspace_id,
            "project_id": ctx.project_id,
            "resource_type": payload.get("resource_type"),
            "resource_id": payload.get("resource_id"),
            "format": str(payload.get("format") or "json"),
            "digest": str(payload.get("digest") or ""),
            "evidence_reference": payload.get("evidence_reference"),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        self.repository.upsert("design_export", record)
        return record

    # ------------------------------------------------------------------
    # operational convenience
    # ------------------------------------------------------------------
    def create_ai_design_draft(self, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        resource_type = str(payload.get("resource_type") or "experience_brief")
        draft = self.create_resource(
            resource_type,
            {
                **payload,
                "creation_method": "AI_GENERATED",
                "created_from_execution_id": payload.get("execution_id"),
                "created_from_agent_id": payload.get("agent_id"),
                "created_from_tool_id": payload.get("tool_id"),
                "created_from_retrieval_id": payload.get("retrieval_id"),
                "source_type": "AI_EXECUTION",
                "source_id": payload.get("execution_id"),
                "status": "DRAFT",
                "review_status": "DRAFT",
                "approval_status": "DRAFT",
                "human_verified": False,
            },
            ctx,
        )
        self.repository.upsert("design_generation_record", {"id": _new_id("design-generation"), "tenant_id": ctx.tenant_id, "workspace_id": ctx.workspace_id, "project_id": ctx.project_id, "resource_type": resource_type, "resource_id": draft["id"], "execution_id": payload.get("execution_id"), "retrieval_id": payload.get("retrieval_id"), "agent_id": payload.get("agent_id"), "tool_id": payload.get("tool_id"), "model": payload.get("model"), "provider": payload.get("provider"), "confidence": payload.get("confidence"), "human_review_status": "PENDING", "human_verification_status": "PENDING", "created_at": _utcnow(), "updated_at": _utcnow(), "correlation_id": ctx.correlation_id, "causation_id": ctx.causation_id or ctx.correlation_id, "metadata": {"citations": list(payload.get("citations") or []), "source_digests": list(payload.get("source_digests") or [])}})
        return draft

    def create_base_design_artifact(self, resource_type: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.create_resource(resource_type, payload, ctx)

    def list_collection(self, kind: str, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return self._list(kind, ctx, include_archived=True)

    def get_collection_item(self, kind: str, item_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        record = self.repository.get(kind, item_id)
        if record is None:
            raise DesignError("design_artifact_not_found", f"{kind} not found.", 404)
        self._ensure_tenant(record, ctx)
        self._check_classification(record, ctx)
        return record

    def update_collection_item(self, kind: str, item_id: str, payload: dict[str, Any], ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.update_resource(kind, item_id, payload, ctx)

    def transition_collection_item(self, kind: str, item_id: str, target_status: str, ctx: DesignExecutionContext, *, reason: str = "") -> dict[str, Any]:
        return self.transition_resource(kind, item_id, target_status, ctx, reason=reason)

    def archive_collection_item(self, kind: str, item_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.archive_resource(kind, item_id, ctx)

    def restore_collection_item(self, kind: str, item_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.restore_resource(kind, item_id, ctx)

    def validate_collection_item(self, kind: str, item_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.validate_artifact(kind, item_id, ctx)

    def list_collection_versions(self, kind: str, item_id: str, ctx: DesignExecutionContext) -> list[dict[str, Any]]:
        return self.list_versions(kind, item_id, ctx)

    def compare_collection_versions(self, kind: str, item_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.compare_versions(kind, item_id, ctx)

    def restore_collection_version(self, kind: str, item_id: str, version_id: str, ctx: DesignExecutionContext) -> dict[str, Any]:
        return self.restore_version(kind, item_id, version_id, ctx)


__all__ = [
    "ACCESSIBILITY_TARGETS",
    "BASELINE_STATUSES",
    "CONTENT_TYPES",
    "DESIGN_APPROVAL_DECISIONS",
    "DESIGN_COLLECTIONS",
    "DESIGN_DEBT_CATEGORIES",
    "DESIGN_ERROR",
    "DESIGN_RISK_CATEGORIES",
    "DESIGN_STATUSES",
    "DESIGN_TRANSITIONS",
    "DesignError",
    "DesignExecutionContext",
    "FITNESS_TYPES",
    "FLOW_EDGE_TYPES",
    "FLOW_NODE_TYPES",
    "LOCALIZATION_STATUSES",
    "NovaCodeProNCP006BService",
    "PERSONA_TYPES",
    "PROTOTYPE_TYPES",
    "RESEARCH_METHODS",
    "SCREEN_STATES",
    "TOKEN_CATEGORIES",
    "TOKEN_LEVELS",
    "VALIDATION_CATEGORIES",
]
