from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from afritech.novacodepro.platform import NovaCodeProRepository, _event_envelope, _new_id


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _upper(value: Any) -> str:
    return str(value or "").strip().upper()


AI_AUTO_GENERATOR_STAGES: list[dict[str, Any]] = [
    {
        "stage_id": "strategy",
        "service_name": "AI Strategy Service",
        "review_state": "STRATEGY_REVIEW",
        "approval_gate": "STRATEGY_APPROVED",
        "next_service": "AI Planning Service",
    },
    {
        "stage_id": "planning",
        "service_name": "AI Planning Service",
        "review_state": "PLAN_REVIEW",
        "approval_gate": "PLAN_APPROVED",
        "next_service": "AI Requirements Service",
    },
    {
        "stage_id": "requirements",
        "service_name": "AI Requirements Service",
        "review_state": "REQUIREMENTS_REVIEW",
        "approval_gate": "REQUIREMENTS_BASELINE_APPROVED",
        "next_service": "AI UX and Design Service",
    },
    {
        "stage_id": "design",
        "service_name": "AI UX and Design Service",
        "review_state": "DESIGN_REVIEW",
        "approval_gate": "DESIGN_APPROVED",
        "next_service": "AI Architecture Service",
    },
    {
        "stage_id": "architecture",
        "service_name": "AI Architecture Service",
        "review_state": "ARCHITECTURE_REVIEW",
        "approval_gate": "ARCHITECTURE_APPROVED",
        "next_service": "AI Applications Service",
    },
    {
        "stage_id": "applications",
        "service_name": "AI Applications Service",
        "review_state": "APPLICATION_VALIDATION",
        "approval_gate": "APPLICATION_BASELINE_VALIDATED",
        "next_service": "AI Intelligent Identity Assurance Service",
    },
    {
        "stage_id": "identity_assurance",
        "service_name": "AI Intelligent Identity Assurance Service",
        "review_state": "IDENTITY_ASSURANCE_REVIEW",
        "approval_gate": "IDENTITY_ASSURANCE_CERTIFIED",
        "next_service": "AI Identity Operations Service",
    },
    {
        "stage_id": "identity_operations",
        "service_name": "AI Identity Operations Service",
        "review_state": "IDENTITY_OPERATIONS_REVIEW",
        "approval_gate": "IDENTITY_OPERATIONS_READY",
        "next_service": "AI Portals Service",
    },
    {
        "stage_id": "portals",
        "service_name": "AI Portals Service",
        "review_state": "PORTALS_REVIEW",
        "approval_gate": "PORTALS_VALIDATED",
        "next_service": "AI Analytics Service",
    },
    {
        "stage_id": "analytics",
        "service_name": "AI Analytics Service",
        "review_state": "ANALYTICS_REVIEW",
        "approval_gate": "ANALYTICS_CERTIFIED",
        "next_service": "AI Production Release Service",
    },
    {
        "stage_id": "production_release",
        "service_name": "AI Production Release Service",
        "review_state": "RELEASE_CERTIFICATION",
        "approval_gate": "GA_APPROVED",
        "next_service": "",
    },
]


DEFAULT_STAGE_ORDER = tuple(stage["stage_id"] for stage in AI_AUTO_GENERATOR_STAGES)

ADMIN_ROLES = {
    "ADMIN",
    "PLATFORM_ADMIN",
    "PLATFORM_OWNER",
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
}


@dataclass(frozen=True)
class AIAutoGeneratorContext:
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


class AIAutoGeneratorError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, *, details: dict[str, Any] | None = None, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.retryable = retryable


def _request_type(request_text: str) -> str:
    normalized = request_text.lower()
    if any(term in normalized for term in ("identity", "authentication", "biometric", "liveness", "session")):
        return "identity platform"
    if any(term in normalized for term in ("payment", "wallet", "ledger", "transfer", "settlement")):
        return "financial platform"
    if any(term in normalized for term in ("mobility", "ride", "driver", "fleet", "dispatch")):
        return "mobility platform"
    if any(term in normalized for term in ("api", "integration", "openapi", "webhook")):
        return "integration platform"
    return "enterprise software platform"


def _title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("_", " ").split())


def _project_slug(request_text: str) -> str:
    words = [part for part in _lower(request_text).split() if part.isalnum() or part.replace("-", "").isalnum()]
    return "-".join(words[:4]) or "auto-generated-product"


def _stage_template(stage: dict[str, Any], execution: dict[str, Any], previous_artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    request_text = str(execution.get("request_text") or "")
    request_kind = _request_type(request_text)
    project_name = str(execution.get("project_name") or execution.get("project_id") or _project_slug(request_text))
    previous_traceability = [link for artifact in previous_artifacts for link in artifact.get("traceability", [])]
    if stage["stage_id"] == "strategy":
        content = {
            "product_vision": f"Governed {request_kind} for {project_name}.",
            "mission": f"Turn the request '{request_text}' into a traceable delivery package.",
            "problem_statement": request_text,
            "value_proposition": f"Trusted orchestration for {project_name}.",
            "target_segments": ["product", "engineering", "operations", "governance"],
            "risk_register": [
                {"risk": "unclear scope", "mitigation": "approval gates and traceability"},
                {"risk": "unsafe automation", "mitigation": "human approval before promotion"},
            ],
            "kpi_catalogue": [
                {"id": "AI-KPI-001", "name": "Approval wait time"},
                {"id": "AI-KPI-002", "name": "Artifact regeneration rate"},
                {"id": "AI-KPI-003", "name": "Validation pass rate"},
            ],
        }
    elif stage["stage_id"] == "planning":
        content = {
            "project_charter": {
                "name": project_name,
                "scope": request_text,
                "mode": execution.get("execution_mode") or "guided_mode",
            },
            "roadmap": [
                {"phase": "strategy", "owner": "AI Strategy Service"},
                {"phase": "planning", "owner": "AI Planning Service"},
                {"phase": "requirements", "owner": "AI Requirements Service"},
                {"phase": "release", "owner": "AI Production Release Service"},
            ],
            "milestones": [
                {"id": "M1", "name": "Governed baseline approved"},
                {"id": "M2", "name": "Implementation validated"},
                {"id": "M3", "name": "Release candidate certified"},
            ],
            "risk_register": [
                {"risk": "provider or model ambiguity", "response": "approval required"},
                {"risk": "scope expansion", "response": "request regeneration"},
            ],
        }
    elif stage["stage_id"] == "requirements":
        content = {
            "business_requirements": [
                {"id": "NCP-BR-001", "title": f"Deliver {request_kind} capabilities", "priority": "must"},
                {"id": "NCP-BR-002", "title": "Maintain tenant isolation and auditability", "priority": "must"},
            ],
            "functional_requirements": [
                {"id": "NCP-FR-001", "title": "Register and authenticate users"},
                {"id": "NCP-FR-002", "title": "Generate traceable artifacts"},
            ],
            "non_functional_requirements": [
                {"id": "NCP-NFR-001", "title": "Deterministic outputs"},
                {"id": "NCP-NFR-002", "title": "Reject unsafe automation"},
            ],
            "acceptance_criteria": [
                "Each lifecycle stage has an evidence record.",
                "Human approval is required before stage promotion.",
                "Traceability links remain project-scoped.",
            ],
            "traceability_matrix": previous_traceability or [
                {
                    "strategy_objective": "NCP-SO-001",
                    "requirement": "NCP-FR-001",
                    "ux_flow": "NCP-UX-001",
                    "architecture_component": "NCP-ARC-001",
                    "source_paths": [],
                    "tests": [],
                    "evidence": [],
                    "release_gate": "REQUIREMENTS_BASELINE_APPROVED",
                }
            ],
        }
    elif stage["stage_id"] == "design":
        content = {
            "personas": [
                {"id": "persona-product-manager", "name": "Product Manager"},
                {"id": "persona-engineer", "name": "Software Engineer"},
                {"id": "persona-governance", "name": "Governance Reviewer"},
            ],
            "journey_maps": [
                {"id": "journey-discovery", "steps": ["request", "review", "approval"]},
                {"id": "journey-release", "steps": ["build", "validate", "release"]},
            ],
            "design_tokens": {"mode": "light-dark", "accessibility": "wcag-2.2-aa"},
            "wireframes": ["workspace shell", "approval console", "evidence viewer"],
        }
    elif stage["stage_id"] == "architecture":
        content = {
            "enterprise_architecture": "governed orchestration over repository-aware lifecycle services",
            "bounded_contexts": [
                "strategy",
                "planning",
                "requirements",
                "design",
                "architecture",
                "applications",
                "identity_assurance",
                "identity_operations",
                "portals",
                "analytics",
                "release",
            ],
            "service_catalogue": [
                {"name": stage["service_name"], "ownership": "NovaCodePro"},
                {"name": stage["next_service"], "ownership": "NovaCodePro"},
            ],
            "threat_model": {"primary_controls": ["server-side authorization", "approval gating", "immutable evidence"]},
        }
    elif stage["stage_id"] == "applications":
        content = {
            "web_applications": ["governed orchestration console", "project traceability portal"],
            "backend_services": [stage["service_name"], stage["next_service"]],
            "migrations": ["ai_auto_generator_execution_records", "ai_auto_generator_artifacts"],
            "tests": ["unit", "integration", "api", "browser"],
        }
    elif stage["stage_id"] == "identity_assurance":
        content = {
            "identity_controls": ["passkeys", "MFA", "step-up approval", "device trust"],
            "risk_scoring": ["session risk", "role risk", "approval risk"],
            "privacy_controls": ["purpose limitation", "consent", "redaction"],
        }
    elif stage["stage_id"] == "identity_operations":
        content = {
            "operations_console": ["session revocation", "approval audit", "risk review"],
            "workflows": ["support-assisted recovery", "incident triage", "policy review"],
            "evidence": ["immutable audit trail", "review notes", "recovery decisions"],
        }
    elif stage["stage_id"] == "portals":
        content = {
            "portals": ["personal", "business", "operations", "administration"],
            "portal_controls": ["tenant isolation", "RBAC", "ABAC", "field masking"],
            "responsive_layouts": ["desktop", "tablet", "mobile"],
        }
    elif stage["stage_id"] == "analytics":
        content = {
            "dashboards": ["executive", "operations", "quality", "release"],
            "metrics_governance": ["identifier", "formula", "owner", "lineage", "approval status"],
            "data_domains": ["requests", "artifacts", "approvals", "evidence"],
        }
    else:
        content = {
            "release_manifest": {
                "branch": execution.get("branch") or "",
                "commit": execution.get("commit_sha") or "",
                "approval_gate": stage["approval_gate"],
            },
            "quality_gates": [
                "build",
                "lint",
                "typecheck",
                "tests",
                "security",
                "evidence",
            ],
            "rollback": "Revert the execution state and archive generated artifacts.",
        }
    traceability = [
        {
            "strategy_objective": f"NCP-SO-{index + 1:03d}",
            "requirement": f"NCP-REQ-{index + 1:03d}",
            "ux_flow": f"NCP-UX-{index + 1:03d}",
            "architecture_component": f"NCP-ARC-{index + 1:03d}",
            "source_paths": [f"generated/{stage['stage_id']}"],
            "tests": [f"tests/ai_auto_generator/test_{stage['stage_id']}.py"],
            "evidence": [f"evidence/{stage['stage_id']}/{index + 1}"],
            "release_gate": stage["approval_gate"],
        }
        for index in range(1, 2)
    ]
    return {
        "content": content,
        "traceability": traceability,
        "evidence_summary": {
            "stage": stage["stage_id"],
            "service": stage["service_name"],
            "approval_gate": stage["approval_gate"],
        },
    }


class NovaCodeProAIAutoGeneratorService:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository
        self._seed_registry()

    def _seed_registry(self) -> None:
        for stage in AI_AUTO_GENERATOR_STAGES:
            existing = self.repository.get("ai_auto_generator_service", stage["stage_id"])
            if not existing:
                self.repository.upsert(
                    "ai_auto_generator_service",
                    {
                        "id": stage["stage_id"],
                        "stage_id": stage["stage_id"],
                        "service_name": stage["service_name"],
                        "review_state": stage["review_state"],
                        "approval_gate": stage["approval_gate"],
                        "next_service": stage["next_service"],
                        "created_at": _utc_now(),
                        "updated_at": _utc_now(),
                        "version": 1,
                        "status": "ACTIVE",
                    },
                )

    def _ensure_workspace(self, ctx: AIAutoGeneratorContext) -> None:
        if not ctx.workspace_id:
            raise AIAutoGeneratorError("workspace_required", "Workspace context is required.", 409)
        if not ctx.tenant_id:
            raise AIAutoGeneratorError("tenant_required", "Tenant context is required.", 409)

    def _ensure_permission(self, ctx: AIAutoGeneratorContext, permission: str) -> None:
        if permission in ctx.permissions or ctx.role.upper() in ADMIN_ROLES:
            return
        raise AIAutoGeneratorError("forbidden", "You do not have permission to perform this action.", 403)

    def _execution_or_404(self, execution_id: str, ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        execution = self.repository.get("ai_auto_generator_execution", execution_id)
        if not execution:
            raise AIAutoGeneratorError("execution_not_found", "Execution not found.", 404)
        if str(execution.get("tenant_id")) != ctx.tenant_id:
            raise AIAutoGeneratorError("cross_tenant_execution_forbidden", "Cross-tenant access is forbidden.", 403)
        if ctx.workspace_id and str(execution.get("workspace_id")) != ctx.workspace_id:
            raise AIAutoGeneratorError("workspace_scope_mismatch", "Workspace scope mismatch.", 403)
        return execution

    def _record_event(self, event_type: str, ctx: AIAutoGeneratorContext, *, execution_id: str, stage_id: str | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
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
            data={**(data or {}), "execution_id": execution_id, "stage_id": stage_id},
            metadata={"environment": ctx.environment, "workspace_id": ctx.workspace_id, "service": "ai-auto-generator"},
        )
        self.repository.append_event(event)
        return event

    def _build_stage_records(self, execution: dict[str, Any], ctx: AIAutoGeneratorContext) -> list[dict[str, Any]]:
        artifacts: list[dict[str, Any]] = []
        for stage in AI_AUTO_GENERATOR_STAGES:
            template = _stage_template(stage, execution, artifacts)
            artifact = {
                "id": _new_id(f"ai-auto-{stage['stage_id']}-artifact"),
                "execution_id": execution["id"],
                "project_id": execution.get("project_id"),
                "request_id": execution.get("request_id"),
                "tenant_id": ctx.tenant_id,
                "organization_id": ctx.organization_id,
                "workspace_id": ctx.workspace_id,
                "stage_id": stage["stage_id"],
                "service_name": stage["service_name"],
                "approval_gate": stage["approval_gate"],
                "next_service": stage["next_service"],
                "state": stage["review_state"],
                "status": "DRAFT",
                "artifact_kind": stage["stage_id"],
                "artifact_name": f"{_title_case(stage['stage_id'])} Artifact",
                "content": template["content"],
                "traceability": template["traceability"],
                "evidence_summary": template["evidence_summary"],
                "digest": _stable_digest({"stage": stage["stage_id"], "content": template["content"], "execution_id": execution["id"]}),
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
                "created_by": ctx.actor_id,
                "updated_by": ctx.actor_id,
                "correlation_id": ctx.correlation_id,
                "causation_id": ctx.causation_id or ctx.correlation_id,
                "version": 1,
            }
            self.repository.upsert("ai_auto_generator_artifact", artifact)
            artifacts.append(artifact)
        return artifacts

    def _project_snapshot(self, project_id: str | None) -> dict[str, Any] | None:
        if not project_id:
            return None
        return self.repository.get("project", project_id) or self.repository.get("customer_project", project_id)

    def _traceability_for(self, execution: dict[str, Any]) -> list[dict[str, Any]]:
        return [dict(item) for item in execution.get("traceability") or []]

    def _evidence_for(self, execution: dict[str, Any]) -> list[dict[str, Any]]:
        return [dict(item) for item in execution.get("evidence") or []]

    def create_execution(self, payload: dict[str, Any], ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        self._ensure_workspace(ctx)
        self._ensure_permission(ctx, "ai.request")
        request_text = str(payload.get("request_text") or payload.get("request") or payload.get("prompt") or payload.get("title") or "").strip()
        if not request_text:
            raise AIAutoGeneratorError("validation_failed", "Request text is required.", 400)
        idempotency_key = str(payload.get("idempotency_key") or "").strip()
        if idempotency_key:
            for record in self.repository.list("ai_auto_generator_idempotency"):
                if str(record.get("tenant_id")) == ctx.tenant_id and str(record.get("workspace_id")) == ctx.workspace_id and str(record.get("idempotency_key")) == idempotency_key:
                    return self._execution_or_404(str(record["execution_id"]), ctx)
        execution_id = str(payload.get("execution_id") or _new_id("ai-auto-generator-execution"))
        execution = {
            "id": execution_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": str(payload.get("project_id") or ctx.project_id or ""),
            "request_id": str(payload.get("request_id") or ctx.request_id or ""),
            "request_text": request_text,
            "request_type": _request_type(request_text),
            "execution_mode": str(payload.get("execution_mode") or "guided_mode"),
            "status": "REQUEST_RECEIVED",
            "current_stage_index": 0,
            "current_stage_id": AI_AUTO_GENERATOR_STAGES[0]["stage_id"],
            "current_service": AI_AUTO_GENERATOR_STAGES[0]["service_name"],
            "next_service": AI_AUTO_GENERATOR_STAGES[0]["next_service"],
            "stages": [],
            "artifacts": [],
            "approvals": [],
            "evidence": [],
            "traceability": [],
            "risks": [
                {"id": "AI-RISK-001", "description": "Unsafe generation without approval"},
                {"id": "AI-RISK-002", "description": "Cross-tenant artifact leakage"},
            ],
            "assumptions": [
                "Repository context is authoritative.",
                "Human approval is required at each stage gate.",
            ],
            "requested_scope": list(payload.get("requested_scope") or []),
            "input_artifact_refs": list(payload.get("input_artifact_refs") or []),
            "repository_context": dict(payload.get("repository_context") or {}),
            "policy_context": dict(payload.get("policy_context") or {}),
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "created_by": ctx.actor_id,
            "updated_by": ctx.actor_id,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
            "session_id": ctx.session_id,
            "execution_mode_state": "APPROVAL_REQUIRED",
            "version": 1,
        }
        artifact_records = self._build_stage_records(execution, ctx)
        execution["artifacts"] = [artifact["id"] for artifact in artifact_records]
        execution["stages"] = [
            {
                "stage_id": stage["stage_id"],
                "service_name": stage["service_name"],
                "state": stage["review_state"],
                "approval_gate": stage["approval_gate"],
                "next_service": stage["next_service"],
                "artifact_id": artifact_records[index]["id"],
                "artifact_digest": artifact_records[index]["digest"],
                "approved": False,
                "approval_id": "",
                "approval_status": "PENDING",
            }
            for index, stage in enumerate(AI_AUTO_GENERATOR_STAGES)
        ]
        execution["traceability"] = [item for artifact in artifact_records for item in artifact["traceability"]]
        execution["evidence"] = [
            {
                "id": _new_id("ai-auto-evidence"),
                "execution_id": execution_id,
                "stage_id": artifact["stage_id"],
                "service_name": artifact["service_name"],
                "artifact_id": artifact["id"],
                "artifact_digest": artifact["digest"],
                "approval_gate": artifact["approval_gate"],
                "status": "EVIDENCE_READY",
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
            }
            for artifact in artifact_records
        ]
        execution["stage_gate"] = AI_AUTO_GENERATOR_STAGES[0]["approval_gate"]
        execution["stage_status"] = AI_AUTO_GENERATOR_STAGES[0]["review_state"]
        execution["analysis"] = {
            "request_type": execution["request_type"],
            "project_name": payload.get("project_name") or (self._project_snapshot(execution["project_id"]) or {}).get("name") or "",
            "execution_mode": execution["execution_mode"],
        }
        execution["approval_state"] = "PENDING"
        execution["digest"] = _stable_digest({"request_text": request_text, "project_id": execution["project_id"], "stages": execution["stages"]})
        self.repository.upsert("ai_auto_generator_execution", execution)
        if idempotency_key:
            self.repository.upsert(
                "ai_auto_generator_idempotency",
                {
                    "id": _new_id("ai-auto-generator-idempotency"),
                    "idempotency_key": idempotency_key,
                    "tenant_id": ctx.tenant_id,
                    "organization_id": ctx.organization_id,
                    "workspace_id": ctx.workspace_id,
                    "execution_id": execution_id,
                    "resource_kind": "ai_auto_generator_execution",
                    "resource_id": execution_id,
                    "created_at": _utc_now(),
                    "updated_at": _utc_now(),
                    "status": "ACTIVE",
                    "version": 1,
                },
            )
        self._record_event("ai.generator.execution.created", ctx, execution_id=execution_id, data={"request_text": request_text, "request_type": execution["request_type"]})
        return execution

    def list_executions(self, ctx: AIAutoGeneratorContext) -> list[dict[str, Any]]:
        self._ensure_permission(ctx, "ai.read")
        items = []
        for execution in self.repository.list("ai_auto_generator_execution"):
            if str(execution.get("tenant_id")) != ctx.tenant_id:
                continue
            if ctx.workspace_id and str(execution.get("workspace_id")) != ctx.workspace_id:
                continue
            items.append(execution)
        return items

    def get_execution(self, execution_id: str, ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.read")
        return self._execution_or_404(execution_id, ctx)

    def _update_stage(self, execution: dict[str, Any], stage_index: int, *, state: str | None = None, approval_status: str | None = None, approval_id: str | None = None) -> dict[str, Any]:
        stages = list(execution.get("stages") or [])
        if stage_index >= len(stages):
            raise AIAutoGeneratorError("stage_not_found", "Stage not found.", 404)
        stages[stage_index] = {**stages[stage_index]}
        if state is not None:
            stages[stage_index]["state"] = state
        if approval_status is not None:
            stages[stage_index]["approval_status"] = approval_status
        if approval_id is not None:
            stages[stage_index]["approval_id"] = approval_id
        execution["stages"] = stages
        execution["current_stage_index"] = stage_index
        execution["current_stage_id"] = stages[stage_index]["stage_id"]
        execution["current_service"] = stages[stage_index]["service_name"]
        execution["next_service"] = stages[stage_index]["next_service"]
        execution["stage_gate"] = stages[stage_index]["approval_gate"]
        execution["stage_status"] = stages[stage_index]["state"]
        execution["updated_at"] = _utc_now()
        execution["version"] = int(execution.get("version") or 1) + 1
        return self.repository.upsert("ai_auto_generator_execution", execution)

    def approve_stage(self, execution_id: str, payload: dict[str, Any], ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.approve")
        execution = self._execution_or_404(execution_id, ctx)
        if _upper(execution.get("status")) in {"CANCELLED", "ROLLED_BACK"}:
            raise AIAutoGeneratorError("execution_closed", "Execution is closed.", 409)
        stage_id = str(payload.get("stage_id") or execution.get("current_stage_id") or "").strip()
        if not stage_id:
            raise AIAutoGeneratorError("stage_required", "Stage is required.", 400)
        stages = list(execution.get("stages") or [])
        stage_index = next((index for index, item in enumerate(stages) if item.get("stage_id") == stage_id), -1)
        if stage_index < 0:
            raise AIAutoGeneratorError("stage_not_found", "Stage not found.", 404)
        current_index = int(execution.get("current_stage_index") or 0)
        if stage_index != current_index:
            raise AIAutoGeneratorError("stage_out_of_order", "Only the current stage can be approved.", 409)
        decision = _upper(payload.get("decision") or "APPROVED")
        if decision not in {"APPROVED", "REJECTED", "CHANGES_REQUESTED"}:
            raise AIAutoGeneratorError("validation_failed", "Unsupported decision.", 400)
        approval = {
            "id": _new_id("ai-auto-generator-approval"),
            "execution_id": execution_id,
            "stage_id": stage_id,
            "stage_name": stages[stage_index]["service_name"],
            "approval_gate": stages[stage_index]["approval_gate"],
            "decision": decision,
            "reason": str(payload.get("reason") or ""),
            "approver": ctx.actor_id,
            "tenant_id": ctx.tenant_id,
            "organization_id": ctx.organization_id,
            "workspace_id": ctx.workspace_id,
            "project_id": execution.get("project_id"),
            "request_id": execution.get("request_id"),
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "version": 1,
            "status": decision,
            "correlation_id": ctx.correlation_id,
            "causation_id": ctx.causation_id or ctx.correlation_id,
        }
        self.repository.upsert("ai_auto_generator_approval", approval)
        approvals = list(execution.get("approvals") or [])
        approvals.append(approval)
        execution["approvals"] = approvals
        if decision == "REJECTED":
            execution["status"] = "NO_GO"
            self._update_stage(execution, stage_index, approval_status="REJECTED", approval_id=approval["id"])
            self._record_event("ai.execution.failed", ctx, execution_id=execution_id, stage_id=stage_id, data={"decision": decision, "reason": approval["reason"]})
            return execution
        if decision == "CHANGES_REQUESTED":
            self._update_stage(execution, stage_index, approval_status="CHANGES_REQUESTED", approval_id=approval["id"])
            execution["status"] = "HUMAN_REVIEW_REQUIRED"
            self.repository.upsert("ai_auto_generator_execution", execution)
            self._record_event("ai.execution.paused", ctx, execution_id=execution_id, stage_id=stage_id, data={"decision": decision})
            return execution
        self._update_stage(execution, stage_index, state=stages[stage_index]["approval_gate"], approval_status="APPROVED", approval_id=approval["id"])
        if stage_index + 1 < len(stages):
            next_stage = stages[stage_index + 1]
            execution["status"] = f"{next_stage['stage_id'].upper()}_GENERATING"
            self._update_stage(execution, stage_index + 1, state=next_stage["state"], approval_status="PENDING")
        else:
            execution["status"] = "GA_READY"
        execution["updated_at"] = _utc_now()
        execution["version"] = int(execution.get("version") or 1) + 1
        self.repository.upsert("ai_auto_generator_execution", execution)
        self._record_event("ai.generator.stage.approved", ctx, execution_id=execution_id, stage_id=stage_id, data={"decision": decision, "gate": stages[stage_index]["approval_gate"]})
        if execution["status"] == "GA_READY":
            self._record_event("ai.ga.approved", ctx, execution_id=execution_id, data={"decision": "GO"})
        return execution

    def retry(self, execution_id: str, payload: dict[str, Any], ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.execute")
        execution = self._execution_or_404(execution_id, ctx)
        stage_id = str(payload.get("stage_id") or execution.get("current_stage_id") or "").strip()
        stages = list(execution.get("stages") or [])
        stage_index = next((index for index, item in enumerate(stages) if item.get("stage_id") == stage_id), -1)
        if stage_index < 0:
            raise AIAutoGeneratorError("stage_not_found", "Stage not found.", 404)
        artifacts = self._build_stage_records(execution, ctx)
        new_artifact = artifacts[stage_index]
        artifact_ids = list(execution.get("artifacts") or [])
        artifact_ids[stage_index] = new_artifact["id"]
        execution["artifacts"] = artifact_ids
        stage = {**stages[stage_index], "artifact_id": new_artifact["id"], "artifact_digest": new_artifact["digest"], "state": new_artifact["state"], "approval_status": "PENDING"}
        stages[stage_index] = stage
        execution["stages"] = stages
        execution["status"] = f"{stage_id.upper()}_GENERATING"
        execution["traceability"] = [item for artifact in artifacts for item in artifact["traceability"]]
        execution["evidence"] = [
            {
                "id": _new_id("ai-auto-evidence"),
                "execution_id": execution_id,
                "stage_id": artifact["stage_id"],
                "service_name": artifact["service_name"],
                "artifact_id": artifact["id"],
                "artifact_digest": artifact["digest"],
                "approval_gate": artifact["approval_gate"],
                "status": "EVIDENCE_READY",
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
            }
            for artifact in artifacts
        ]
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_auto_generator_execution", execution)
        self.repository.upsert("ai_auto_generator_artifact", new_artifact)
        self._record_event("ai.execution.retry_required", ctx, execution_id=execution_id, stage_id=stage_id, data={"reason": str(payload.get("reason") or "")})
        return execution

    def pause(self, execution_id: str, ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        if _upper(execution.get("status")) in {"CANCELLED", "GA_READY", "NO_GO"}:
            raise AIAutoGeneratorError("execution_closed", "Execution cannot be paused.", 409)
        execution["status"] = "PAUSED"
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_auto_generator_execution", execution)
        self._record_event("ai.execution.paused", ctx, execution_id=execution_id, stage_id=execution.get("current_stage_id"), data={"status": "PAUSED"})
        return execution

    def resume(self, execution_id: str, ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        if _upper(execution.get("status")) != "PAUSED":
            raise AIAutoGeneratorError("execution_not_paused", "Execution is not paused.", 409)
        current_stage_id = str(execution.get("current_stage_id") or "")
        execution["status"] = f"{current_stage_id.upper()}_REVIEW"
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_auto_generator_execution", execution)
        self._record_event("ai.execution.resumed", ctx, execution_id=execution_id, stage_id=current_stage_id, data={"status": execution["status"]})
        return execution

    def cancel(self, execution_id: str, ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        execution = self._execution_or_404(execution_id, ctx)
        execution["status"] = "CANCELLED"
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_auto_generator_execution", execution)
        self._record_event("ai.execution.failed", ctx, execution_id=execution_id, stage_id=execution.get("current_stage_id"), data={"decision": "CANCELLED"})
        return execution

    def regenerate_artifact(self, execution_id: str, artifact_id: str, payload: dict[str, Any], ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.execute")
        execution = self._execution_or_404(execution_id, ctx)
        artifact = self.repository.get("ai_auto_generator_artifact", artifact_id)
        if not artifact:
            raise AIAutoGeneratorError("artifact_not_found", "Artifact not found.", 404)
        if str(artifact.get("execution_id")) != execution_id:
            raise AIAutoGeneratorError("artifact_scope_mismatch", "Artifact does not belong to execution.", 403)
        stage_index = next((index for index, item in enumerate(AI_AUTO_GENERATOR_STAGES) if item["stage_id"] == artifact["stage_id"]), -1)
        if stage_index < 0:
            raise AIAutoGeneratorError("stage_not_found", "Stage not found.", 404)
        regenerated = self._build_stage_records(execution, ctx)[stage_index]
        regenerated["id"] = artifact_id
        regenerated["version"] = int(artifact.get("version") or 1) + 1
        regenerated["updated_at"] = _utc_now()
        regenerated["status"] = "REGENERATED"
        regenerated["regeneration_reason"] = str(payload.get("reason") or "")
        self.repository.upsert("ai_auto_generator_artifact", regenerated)
        execution = self._execution_or_404(execution_id, ctx)
        stages = list(execution.get("stages") or [])
        stages[stage_index] = {**stages[stage_index], "artifact_digest": regenerated["digest"], "artifact_id": artifact_id}
        execution["stages"] = stages
        execution["artifacts"] = [artifact_id if existing == artifact_id or index == stage_index else existing for index, existing in enumerate(execution.get("artifacts") or [])]
        execution["traceability"] = [item for artifact_record in self._build_stage_records(execution, ctx) for item in artifact_record["traceability"]]
        execution["updated_at"] = _utc_now()
        self.repository.upsert("ai_auto_generator_execution", execution)
        self._record_event("ai.application.generated", ctx, execution_id=execution_id, stage_id=artifact["stage_id"], data={"artifact_id": artifact_id, "reason": regenerated["regeneration_reason"]})
        return regenerated

    def traceability(self, project_id: str, ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.read")
        executions = [
            execution
            for execution in self.repository.list("ai_auto_generator_execution")
            if str(execution.get("project_id")) == project_id and str(execution.get("tenant_id")) == ctx.tenant_id
        ]
        links = [link for execution in executions for link in execution.get("traceability") or []]
        return {"project_id": project_id, "executions": executions, "links": links}

    def evidence(self, project_id: str, ctx: AIAutoGeneratorContext) -> dict[str, Any]:
        self._ensure_permission(ctx, "ai.read")
        executions = [
            execution
            for execution in self.repository.list("ai_auto_generator_execution")
            if str(execution.get("project_id")) == project_id and str(execution.get("tenant_id")) == ctx.tenant_id
        ]
        evidence_records = [item for execution in executions for item in execution.get("evidence") or []]
        return {"project_id": project_id, "executions": executions, "evidence": evidence_records}


__all__ = [
    "AI_AUTO_GENERATOR_STAGES",
    "AIAutoGeneratorContext",
    "AIAutoGeneratorError",
    "NovaCodeProAIAutoGeneratorService",
]
