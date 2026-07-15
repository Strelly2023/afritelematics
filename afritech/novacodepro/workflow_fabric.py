from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from .enterprise_os import default_agent_registry, select_agent_team
from .platform import NovaCodeProPlatform


WORKFLOW_LIFECYCLE_STATES = (
    "DRAFT",
    "VALIDATED",
    "COMPILED",
    "REVIEWED",
    "APPROVED",
    "DEPLOYED",
    "RUNNING",
    "PAUSED",
    "RESUMED",
    "COMPLETED",
    "VERIFIED",
    "EVIDENCE_GENERATED",
    "ARCHIVED",
)

WORKFLOW_STATE_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"VALIDATED", "ARCHIVED"},
    "VALIDATED": {"COMPILED", "ARCHIVED"},
    "COMPILED": {"REVIEWED", "ARCHIVED"},
    "REVIEWED": {"APPROVED", "ARCHIVED"},
    "APPROVED": {"DEPLOYED", "ARCHIVED"},
    "DEPLOYED": {"RUNNING", "PAUSED", "ARCHIVED"},
    "RUNNING": {"PAUSED", "COMPLETED"},
    "PAUSED": {"RESUMED", "ARCHIVED"},
    "RESUMED": {"RUNNING", "PAUSED", "COMPLETED"},
    "COMPLETED": {"VERIFIED", "ARCHIVED"},
    "VERIFIED": {"EVIDENCE_GENERATED", "ARCHIVED"},
    "EVIDENCE_GENERATED": {"ARCHIVED"},
    "ARCHIVED": set(),
}

WORKFLOW_VIEWS = (
    "Business View",
    "BPMN View",
    "Flowchart View",
    "State Machine",
    "Sequence Diagram",
    "Timeline",
    "Execution Graph",
    "Audit Timeline",
)

WORKFLOW_MARKETPLACE_CATEGORIES = (
    "HR",
    "Finance",
    "Sales",
    "Customer Support",
    "Procurement",
    "Healthcare",
    "Education",
    "Manufacturing",
    "Government",
    "Retail",
    "Logistics",
    "Mobility",
    "Payments",
    "Identity",
    "Compliance",
    "Security",
    "IT Operations",
    "Software Delivery",
    "AI Workflows",
)

WORKFLOW_CONNECTORS = (
    {"id": "connector-novaid", "name": "NovaID", "kind": "identity", "version": "2026.1", "permissions": ["identity.read", "identity.write"], "rate_limits": {"per_minute": 600}, "audit": True, "evidence": True},
    {"id": "connector-novapolicy", "name": "NovaPolicy", "kind": "policy", "version": "2026.1", "permissions": ["policy.read", "policy.evaluate"], "rate_limits": {"per_minute": 300}, "audit": True, "evidence": True},
    {"id": "connector-novarisk", "name": "NovaRisk", "kind": "risk", "version": "2026.1", "permissions": ["risk.read", "risk.evaluate"], "rate_limits": {"per_minute": 300}, "audit": True, "evidence": True},
    {"id": "connector-novaevidence", "name": "NovaEvidence", "kind": "evidence", "version": "2026.1", "permissions": ["evidence.write", "evidence.read"], "rate_limits": {"per_minute": 500}, "audit": True, "evidence": True},
    {"id": "connector-novaeventmesh", "name": "NovaEventMesh", "kind": "event-mesh", "version": "2026.1", "permissions": ["events.publish", "events.consume"], "rate_limits": {"per_minute": 1200}, "audit": True, "evidence": True},
    {"id": "connector-sap", "name": "SAP", "kind": "erp", "version": "1.0", "permissions": ["connector.invoke"], "rate_limits": {"per_minute": 60}, "audit": True, "evidence": True},
    {"id": "connector-salesforce", "name": "Salesforce", "kind": "crm", "version": "1.0", "permissions": ["connector.invoke"], "rate_limits": {"per_minute": 120}, "audit": True, "evidence": True},
    {"id": "connector-servicenow", "name": "ServiceNow", "kind": "ops", "version": "1.0", "permissions": ["connector.invoke"], "rate_limits": {"per_minute": 120}, "audit": True, "evidence": True},
    {"id": "connector-postgres", "name": "PostgreSQL", "kind": "database", "version": "1.0", "permissions": ["db.read", "db.write"], "rate_limits": {"per_minute": 1000}, "audit": True, "evidence": True},
    {"id": "connector-kafka", "name": "Kafka", "kind": "event-stream", "version": "1.0", "permissions": ["events.publish", "events.consume"], "rate_limits": {"per_minute": 5000}, "audit": True, "evidence": True},
    {"id": "connector-rest", "name": "REST", "kind": "api", "version": "1.0", "permissions": ["http.invoke"], "rate_limits": {"per_minute": 300}, "audit": True, "evidence": True},
    {"id": "connector-graphql", "name": "GraphQL", "kind": "api", "version": "1.0", "permissions": ["http.invoke"], "rate_limits": {"per_minute": 300}, "audit": True, "evidence": True},
)

WORKFLOW_TEMPLATE_LIBRARY = (
    {"id": "employee-onboarding", "category": "HR", "title": "Employee onboarding", "summary": "Provision people, approvals, and access in a governed sequence."},
    {"id": "purchase-approval", "category": "Finance", "title": "Purchase approval", "summary": "Route a purchase request through budget, risk, and finance approvals."},
    {"id": "incident-response", "category": "IT Operations", "title": "Incident response", "summary": "Open, triage, escalate, and close operational incidents with evidence."},
    {"id": "security-remediation", "category": "Security", "title": "Security remediation", "summary": "Track findings, approvals, and remediation evidence."},
    {"id": "workflow-deployment", "category": "Software Delivery", "title": "Workflow deployment", "summary": "Validate, compile, approve, deploy, and verify a workflow release."},
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{_now()}".encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:12]}"


def _canonical_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _as_list(value: Iterable[str] | None) -> list[str]:
    return list(value or [])


def _workflow_contract(workflow: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflow_id": workflow["id"],
        "workflow_version": str(payload.get("workflow_version") or "1.0"),
        "organization_id": workflow["tenant_id"],
        "tenant_id": workflow["tenant_id"],
        "environment": str(payload.get("environment") or "development"),
        "owner": str(payload.get("owner") or "NovaCodePro"),
        "risk_level": str(payload.get("risk_level") or "medium").upper(),
        "required_approvals": _as_list(payload.get("required_approvals") or ("manager", "policy", "security")),
        "policies": _as_list(payload.get("policies") or ("identity", "authorization", "policy", "risk", "compliance")),
        "sla": str(payload.get("sla") or "24h"),
        "evidence_profile": str(payload.get("evidence_profile") or "operational"),
        "retention_policy": str(payload.get("retention_policy") or "seven_years"),
        "audit_profile": str(payload.get("audit_profile") or "full"),
        "rollback_strategy": str(payload.get("rollback_strategy") or "compensate"),
        "compensation_strategy": str(payload.get("compensation_strategy") or "manual_review"),
    }


def _workflow_views(workflow: dict[str, Any], fabric: dict[str, Any]) -> dict[str, Any]:
    team = list(fabric.get("ai_agents") or [])
    stages = [
        {"id": "draft", "label": "Draft", "state": "DRAFT"},
        {"id": "validate", "label": "Validate", "state": "VALIDATED"},
        {"id": "compile", "label": "Compile", "state": "COMPILED"},
        {"id": "review", "label": "Review", "state": "REVIEWED"},
        {"id": "approve", "label": "Approve", "state": "APPROVED"},
        {"id": "deploy", "label": "Deploy", "state": "DEPLOYED"},
        {"id": "run", "label": "Running", "state": "RUNNING"},
        {"id": "pause", "label": "Paused", "state": "PAUSED"},
        {"id": "resume", "label": "Resumed", "state": "RESUMED"},
        {"id": "complete", "label": "Completed", "state": "COMPLETED"},
        {"id": "verify", "label": "Verified", "state": "VERIFIED"},
        {"id": "evidence", "label": "Evidence Generated", "state": "EVIDENCE_GENERATED"},
        {"id": "archive", "label": "Archived", "state": "ARCHIVED"},
    ]
    return {
        "business_view": {
            "title": workflow["title"],
            "objective": workflow["request"],
            "domain": workflow.get("domain"),
            "region": workflow.get("region"),
            "surfaces": list(workflow.get("surfaces") or []),
        },
        "bpmn_view": {"nodes": stages, "edges": [{"from": stages[index]["id"], "to": stages[index + 1]["id"]} for index in range(len(stages) - 1)]},
        "flowchart_view": {"nodes": stages, "edges": [{"from": stages[index]["id"], "to": stages[index + 1]["id"]} for index in range(len(stages) - 1)]},
        "state_machine": {"states": list(WORKFLOW_LIFECYCLE_STATES), "transitions": {state: sorted(targets) for state, targets in WORKFLOW_STATE_TRANSITIONS.items()}},
        "sequence_diagram": {
            "participants": ["Requester", "NovaWorkflow", "Approvals", "AI Agents", "Connector Runtime", "Evidence"],
            "steps": [
                "Requester raises intent",
                "NovaWorkflow validates the contract",
                "Approvals review the plan",
                "AI agents contribute analysis",
                "Connector runtime executes integrations",
                "Evidence is generated and archived",
            ],
        },
        "timeline": fabric.get("timeline") or [],
        "execution_graph": {
            "nodes": [
                {"id": "request", "kind": "intent", "label": workflow["title"]},
                *[{"id": agent["id"], "kind": "agent", "label": agent["name"]} for agent in team],
                *[{"id": connector["id"], "kind": "connector", "label": connector["name"]} for connector in fabric.get("connectors") or []],
            ],
            "edges": [
                {"from": "request", "to": agent["id"], "kind": "orchestrates"}
                for agent in team
            ]
            + [{"from": team[index]["id"], "to": team[index + 1]["id"], "kind": "coordinates"} for index in range(max(len(team) - 1, 0))],
            "current_state": fabric.get("state"),
        },
        "audit_timeline": fabric.get("audit_timeline") or [],
    }


def _workflow_dashboard(workflow: dict[str, Any], fabric: dict[str, Any]) -> dict[str, Any]:
    timeline = list(fabric.get("timeline") or [])
    transitions = len(timeline)
    first_at = str(timeline[0]["at"]) if timeline else workflow.get("created_at")
    last_at = str(timeline[-1]["at"]) if timeline else workflow.get("updated_at")
    created_at = datetime.fromisoformat(str(first_at).replace("Z", "+00:00"))
    last_seen = datetime.fromisoformat(str(last_at).replace("Z", "+00:00"))
    return {
        "workflow_id": workflow["id"],
        "state": fabric.get("state"),
        "revision": int(fabric.get("revision") or 1),
        "transition_count": transitions,
        "approval_count": len(fabric.get("approvals") or []),
        "review_count": len(fabric.get("reviews") or []),
        "execution_count": len(fabric.get("executions") or []),
        "evidence_count": len(fabric.get("evidence_refs") or []),
        "cycle_time_seconds": max(int((last_seen - created_at).total_seconds()), 0),
        "last_transition_at": last_at,
        "approved": fabric.get("state") in {"APPROVED", "DEPLOYED", "RUNNING", "PAUSED", "RESUMED", "COMPLETED", "VERIFIED", "EVIDENCE_GENERATED", "ARCHIVED"},
        "connectors": [connector["name"] for connector in fabric.get("connectors") or []],
        "agents": [agent["name"] for agent in fabric.get("ai_agents") or []],
    }


class WorkflowFabricService:
    def __init__(self, platform: NovaCodeProPlatform) -> None:
        self.platform = platform

    def summary(self) -> dict[str, Any]:
        workflows = self.workflows()
        fabrics = [self._fabric_for(workflow["id"]) for workflow in workflows]
        return {
            "fabric": "NovaWorkflow Fabric",
            "status": "operational",
            "workflow_count": len(workflows),
            "draft_count": sum(1 for fabric in fabrics if fabric["state"] == "DRAFT"),
            "running_count": sum(1 for fabric in fabrics if fabric["state"] == "RUNNING"),
            "paused_count": sum(1 for fabric in fabrics if fabric["state"] == "PAUSED"),
            "approved_count": sum(1 for fabric in fabrics if fabric["state"] == "APPROVED"),
            "connector_count": len(WORKFLOW_CONNECTORS),
            "agent_count": len(default_agent_registry()),
            "marketplace_category_count": len(WORKFLOW_MARKETPLACE_CATEGORIES),
            "views": list(WORKFLOW_VIEWS),
        }

    def workflows(self) -> list[dict[str, Any]]:
        return [self.workflow_view(workflow["id"]) for workflow in self.platform.workflows()]

    def workflow_view(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        fabric = self._fabric_for(workflow_id, workflow)
        return self._enrich(workflow, fabric)

    def create_workflow(self, payload: dict[str, Any], *, actor: str = "NovaID") -> dict[str, Any]:
        tenant_id = str(payload.get("tenant_id") or self.platform.tenants()[0]["id"])
        idempotency_key = str(payload.get("idempotency_key") or "").strip()
        if idempotency_key:
            existing = [
                record
                for record in self.platform.repository.list("workflow_fabric")
                if str(record.get("tenant_id") or "") == tenant_id and str(record.get("idempotency_key") or "") == idempotency_key
            ]
            if existing:
                return self.workflow_view(str(existing[0]["workflow_id"]))

        workflow = self.platform.create_workflow(
            {
                "title": str(payload["title"]),
                "request": str(payload["request"]),
                "tenant_id": tenant_id,
                "project_id": str(payload.get("project_id") or self.platform.projects()[0]["id"]),
                "template_id": str(payload.get("template_id") or "workflow-fabric"),
                "domain": str(payload.get("domain") or "enterprise"),
                "region": str(payload.get("region") or "Australia"),
                "compliance": str(payload.get("compliance") or "governed"),
                "surfaces": list(payload.get("surfaces") or ["business", "bpmn", "timeline"]),
            }
        )
        fabric = self._bootstrap_fabric(workflow, payload, actor=actor, idempotency_key=idempotency_key)
        self._persist_fabric(fabric)
        return self._enrich(workflow, fabric)

    def generate_from_prompt(self, prompt: str, *, actor: str = "NovaAI") -> dict[str, Any]:
        request = str(prompt).strip()
        title = request if len(request) <= 80 else f"{request[:77].rstrip()}..."
        payload = {
            "title": title or "NovaWorkflow",
            "request": request or "Enterprise workflow",
            "domain": "enterprise",
            "region": "Australia",
            "template_id": "ai-generated",
            "surfaces": ["business", "bpmn", "flowchart", "timeline", "execution"],
            "idempotency_key": _canonical_hash({"prompt": request, "actor": actor})[:24],
        }
        workflow = self.create_workflow(payload, actor=actor)
        workflow["ai_generation"] = {
            "prompt": request,
            "diagram": workflow["views"]["bpmn_view"],
            "human_tasks": workflow["fabric"]["human_tasks"],
            "ai_tasks": workflow["fabric"]["ai_tasks"],
            "forms": workflow["fabric"]["forms"],
            "notifications": workflow["fabric"]["notifications"],
            "policies": workflow["fabric"]["contract"]["policies"],
            "approvals": workflow["fabric"]["contract"]["required_approvals"],
            "kpis": workflow["fabric"]["kpis"],
            "documentation": workflow["fabric"]["documentation"],
            "tests": workflow["fabric"]["tests"],
            "deployment": workflow["fabric"]["deployment"],
        }
        return workflow

    def validate(self, workflow_id: str, *, actor: str = "NovaID") -> dict[str, Any]:
        return self._transition(workflow_id, "VALIDATED", "validate", actor=actor)

    def compile(self, workflow_id: str, *, actor: str = "NovaID") -> dict[str, Any]:
        view = self.workflow_view(workflow_id)
        fabricated = self._transition(workflow_id, "COMPILED", "compile", actor=actor)
        compiled = {
            "business_process": view["views"]["business_view"],
            "workflow_diagram": view["views"]["bpmn_view"],
            "human_tasks": fabricated["fabric"]["human_tasks"],
            "ai_tasks": fabricated["fabric"]["ai_tasks"],
            "forms": fabricated["fabric"]["forms"],
            "notifications": fabricated["fabric"]["notifications"],
            "policies": fabricated["fabric"]["contract"]["policies"],
            "approvals": fabricated["fabric"]["contract"]["required_approvals"],
            "kpis": fabricated["fabric"]["kpis"],
            "documentation": fabricated["fabric"]["documentation"],
            "tests": fabricated["fabric"]["tests"],
            "deployment": fabricated["fabric"]["deployment"],
        }
        return self._finalize(workflow_id, "compiled_definition", compiled, actor=actor)

    def review(self, workflow_id: str, payload: dict[str, Any] | None = None, *, actor: str = "NovaID") -> dict[str, Any]:
        review = {
            "id": _new_id("workflow-review"),
            "workflow_id": workflow_id,
            "reviewer": actor,
            "status": str((payload or {}).get("status") or "REVIEWED").upper(),
            "note": str((payload or {}).get("note") or ""),
            "created_at": _now(),
        }
        result = self._transition(workflow_id, "REVIEWED", "review", actor=actor)
        result["fabric"]["reviews"] = [review, *list(result["fabric"].get("reviews") or [])]
        result["fabric"]["reviewed_by"] = actor
        result["fabric"]["review_note"] = review["note"]
        self._persist_fabric(result["fabric"])
        self.platform.repository.upsert("workflow_review", review)
        return self._enrich(self.platform.get_workflow(workflow_id) or result, result["fabric"])

    def approve(self, workflow_id: str, payload: dict[str, Any] | None = None, *, actor: str = "NovaID") -> dict[str, Any]:
        approval = {
            "id": _new_id("workflow-approval"),
            "workflow_id": workflow_id,
            "approver": actor,
            "approval_reference": str((payload or {}).get("approval_reference") or ""),
            "reason": str((payload or {}).get("reason") or ""),
            "created_at": _now(),
        }
        result = self._transition(workflow_id, "APPROVED", "approve", actor=actor)
        result["fabric"]["approvals"] = [approval, *list(result["fabric"].get("approvals") or [])]
        result["fabric"]["approval_reference"] = approval["approval_reference"]
        self._persist_fabric(result["fabric"])
        self.platform.repository.upsert("workflow_approval", approval)
        return self._enrich(self.platform.get_workflow(workflow_id) or result, result["fabric"])

    def deploy(self, workflow_id: str, payload: dict[str, Any] | None = None, *, actor: str = "NovaID") -> dict[str, Any]:
        result = self._transition(workflow_id, "DEPLOYED", "deploy", actor=actor, note=str((payload or {}).get("note") or ""))
        result["fabric"]["deployment"] = {
            "environment": str((payload or {}).get("environment") or result["fabric"]["contract"]["environment"]),
            "version": str((payload or {}).get("version") or result["fabric"]["contract"]["workflow_version"]),
            "deployed_by": actor,
            "deployed_at": _now(),
        }
        self._persist_fabric(result["fabric"])
        self.platform.repository.upsert("workflow_deployment", {"id": workflow_id, "workflow_id": workflow_id, **result["fabric"]["deployment"]})
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        return self._enrich(workflow, result["fabric"])

    def execute(self, workflow_id: str, payload: dict[str, Any] | None = None, *, actor: str = "NovaID") -> dict[str, Any]:
        result = self._transition(workflow_id, "RUNNING", "execute", actor=actor)
        execution = {
            "id": _new_id("workflow-execution"),
            "workflow_id": workflow_id,
            "actor": actor,
            "input": dict((payload or {}).get("input") or {}),
            "output": dict((payload or {}).get("output") or {}),
            "status": "RUNNING",
            "started_at": _now(),
            "created_at": _now(),
        }
        result["fabric"]["executions"] = [execution, *list(result["fabric"].get("executions") or [])]
        result["fabric"]["execution_state"] = "RUNNING"
        result["fabric"]["current_execution_id"] = execution["id"]
        self._persist_fabric(result["fabric"])
        self.platform.repository.upsert("workflow_execution", execution)
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        return self._enrich(workflow, result["fabric"])

    def pause(self, workflow_id: str, *, actor: str = "NovaID") -> dict[str, Any]:
        return self._transition(workflow_id, "PAUSED", "pause", actor=actor)

    def resume(self, workflow_id: str, *, actor: str = "NovaID") -> dict[str, Any]:
        result = self._transition(workflow_id, "RESUMED", "resume", actor=actor)
        result["fabric"]["execution_state"] = "RUNNING"
        self._persist_fabric(result["fabric"])
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        return self._enrich(workflow, result["fabric"])

    def complete(self, workflow_id: str, *, actor: str = "NovaID") -> dict[str, Any]:
        return self._transition(workflow_id, "COMPLETED", "complete", actor=actor)

    def verify(self, workflow_id: str, *, actor: str = "NovaID") -> dict[str, Any]:
        return self._transition(workflow_id, "VERIFIED", "verify", actor=actor)

    def emit_evidence(self, workflow_id: str, *, actor: str = "NovaID") -> dict[str, Any]:
        fabric = self._fabric_for(workflow_id)
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        evidence = self.platform.create_evidence_bundle(
            {
                "tenant_id": workflow["tenant_id"],
                "workflow_id": workflow_id,
                "actor": {"type": "user", "id": actor},
                "action": "workflow.evidence.generated",
                "policy_id": "NOVAWORKFLOW-FABRIC",
                "artifact_ids": [workflow_id],
                "payload": {
                    "workflow_id": workflow_id,
                    "state": fabric["state"],
                    "revision": fabric["revision"],
                    "contract": fabric["contract"],
                },
                "verified": True,
                "verification_status": "FABRIC_VERIFIED",
            }
        )
        fabric["evidence_refs"] = [evidence["id"], *list(fabric.get("evidence_refs") or [])]
        fabric["state"] = "EVIDENCE_GENERATED"
        fabric["audit_timeline"] = [*list(fabric.get("audit_timeline") or []), {"id": evidence["id"], "type": "evidence", "at": evidence["created_at"], "status": evidence["verification_status"]}]
        fabric["timeline"] = [*list(fabric.get("timeline") or []), {"id": evidence["id"], "at": evidence["created_at"], "state": fabric["state"], "action": "evidence"}]
        self._persist_fabric(fabric)
        self.platform.repository.append_audit(
            kind="workflow",
            actor=actor,
            service="NovaWorkflow Fabric",
            subject=workflow["title"],
            action="workflow.evidence.generated",
            evidence=evidence["id"],
            detail="Workflow evidence was generated by the fabric runtime.",
        )
        return {"workflow_id": workflow_id, "evidence": evidence, "fabric": self._enrich(workflow, fabric)["fabric"]}

    def archive(self, workflow_id: str, *, actor: str = "NovaID") -> dict[str, Any]:
        return self._transition(workflow_id, "ARCHIVED", "archive", actor=actor)

    def analytics(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        fabric = self._fabric_for(workflow_id, workflow)
        return _workflow_dashboard(workflow, fabric)

    def timeline(self, workflow_id: str) -> list[dict[str, Any]]:
        fabric = self._fabric_for(workflow_id)
        return list(fabric.get("timeline") or [])

    def replay(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        fabric = self._fabric_for(workflow_id, workflow)
        return {
            "workflow": self._enrich(workflow, fabric),
            "events": self.platform.repository.list_events_for_aggregate(workflow_id, limit=200),
            "timeline": list(fabric.get("timeline") or []),
            "evidence": list(fabric.get("evidence_refs") or []),
        }

    def evidence(self, workflow_id: str) -> list[dict[str, Any]]:
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        fabric = self._fabric_for(workflow_id, workflow)
        evidence_ids = list(fabric.get("evidence_refs") or [])
        if not evidence_ids:
            return []
        evidence_bundles = self.platform.evidence_bundles()
        return [bundle for bundle in evidence_bundles if bundle["id"] in evidence_ids]

    def views(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        fabric = self._fabric_for(workflow_id, workflow)
        return _workflow_views(workflow, fabric)

    def connectors(self) -> list[dict[str, Any]]:
        return [dict(connector) for connector in WORKFLOW_CONNECTORS]

    def marketplace(self) -> dict[str, Any]:
        return {
            "categories": list(WORKFLOW_MARKETPLACE_CATEGORIES),
            "templates": [dict(template) for template in WORKFLOW_TEMPLATE_LIBRARY],
        }

    def _bootstrap_fabric(self, workflow: dict[str, Any], payload: dict[str, Any], *, actor: str, idempotency_key: str) -> dict[str, Any]:
        team_ids = select_agent_team(workflow["request"], str(payload.get("risk_level") or "medium"))
        registry = {item["id"]: item for item in default_agent_registry()}
        ai_agents = [registry[item_id] for item_id in team_ids if item_id in registry]
        connectors = list(WORKFLOW_CONNECTORS[: min(4, len(WORKFLOW_CONNECTORS))])
        created_at = _now()
        fabric = {
            "id": workflow["id"],
            "workflow_id": workflow["id"],
            "tenant_id": workflow["tenant_id"],
            "organization_id": workflow["tenant_id"],
            "project_id": workflow["project_id"],
            "title": workflow["title"],
            "request": workflow["request"],
            "domain": workflow.get("domain"),
            "region": workflow.get("region"),
            "category": str(payload.get("category") or "AI Workflows"),
            "state": "DRAFT",
            "status": "ACTIVE",
            "revision": 1,
            "created_by": actor,
            "idempotency_key": idempotency_key,
            "created_at": created_at,
            "updated_at": created_at,
            "contract": _workflow_contract(workflow, payload),
            "views": {},
            "ai_agents": ai_agents,
            "connectors": connectors,
            "human_tasks": list(payload.get("human_tasks") or ["Manager Approval", "Legal Review", "Deployment Approval"]),
            "ai_tasks": list(payload.get("ai_tasks") or ["Architect Agent", "Business Analyst Agent", "Security Agent", "Documentation Agent"]),
            "forms": list(payload.get("forms") or ["Request Form", "Approval Form", "Deployment Form"]),
            "notifications": list(payload.get("notifications") or ["Email", "Slack", "Teams", "SMS"]),
            "policies": list(payload.get("policies") or ["Identity", "Authorization", "Risk", "Compliance"]),
            "approvals": [],
            "reviews": [],
            "deployments": [],
            "executions": [],
            "evidence_refs": [],
            "documentation": list(payload.get("documentation") or ["Workflow specification", "Operational guide", "Runbook"]),
            "tests": list(payload.get("tests") or ["Validation", "Simulation", "Replay", "Deployment verification"]),
            "kpis": list(payload.get("kpis") or ["Cycle time", "Automation rate", "Approval delay", "Bottleneck count"]),
            "deployment": {},
            "compiled_definition": {},
            "execution_state": "IDLE",
            "timeline": [
                {
                    "id": _new_id("workflow-event"),
                    "state": "DRAFT",
                    "action": "create",
                    "actor": actor,
                    "note": str(payload.get("note") or "Workflow fabric draft created."),
                    "at": created_at,
                }
            ],
            "audit_timeline": [],
        }
        fabric["views"] = _workflow_views(workflow, fabric)
        fabric["execution_graph"] = fabric["views"]["execution_graph"]
        fabric["routing"] = {
            "people": ["Person", "Team", "Role", "Department"],
            "automation": ["AI Agent", "Automation Worker", "External Partner", "Third-party API"],
        }
        fabric["governance"] = {
            "identity": "NovaID",
            "authorization": "NovaPolicy",
            "risk": "NovaRisk",
            "compliance": "NovaTrust",
            "approvals": "Human review where required",
            "evidence": "NovaEvidence",
            "audit": "NovaAudit",
            "digital_twin": "NovaTwin",
        }
        return fabric

    def _fabric_for(self, workflow_id: str, workflow: dict[str, Any] | None = None) -> dict[str, Any]:
        record = self.platform.repository.get("workflow_fabric", workflow_id)
        if record is not None:
            return record
        if workflow is None:
            workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        fabric = self._bootstrap_fabric(workflow, {}, actor="NovaCodePro", idempotency_key="")
        self._persist_fabric(fabric)
        return fabric

    def _persist_fabric(self, fabric: dict[str, Any]) -> dict[str, Any]:
        fabric = dict(fabric)
        fabric["updated_at"] = _now()
        fabric["views"] = _workflow_views(self.platform.get_workflow(str(fabric["workflow_id"])) or {"title": fabric.get("title", ""), "request": fabric.get("request", ""), "domain": fabric.get("domain"), "region": fabric.get("region"), "surfaces": []}, fabric)
        fabric["execution_graph"] = fabric["views"]["execution_graph"]
        self.platform.repository.upsert("workflow_fabric", fabric)
        return fabric

    def _finalize(self, workflow_id: str, key: str, value: Any, *, actor: str) -> dict[str, Any]:
        fabric = self._fabric_for(workflow_id)
        fabric[key] = value
        fabric["timeline"] = [
            *list(fabric.get("timeline") or []),
            {"id": _new_id("workflow-event"), "state": fabric["state"], "action": key, "actor": actor, "at": _now(), "note": f"{key} updated"},
        ]
        self._persist_fabric(fabric)
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        return self._enrich(workflow, fabric)

    def _transition(self, workflow_id: str, target_state: str, action: str, *, actor: str, note: str = "") -> dict[str, Any]:
        workflow = self.platform.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        fabric = self._fabric_for(workflow_id, workflow)
        current_state = str(fabric.get("state") or "DRAFT")
        if target_state not in WORKFLOW_STATE_TRANSITIONS.get(current_state, set()) and target_state != current_state:
            raise ValueError(f"invalid_transition:{current_state.lower()}_to_{target_state.lower()}")
        fabric["state"] = target_state
        fabric["revision"] = int(fabric.get("revision") or 1) + 1
        fabric["timeline"] = [
            *list(fabric.get("timeline") or []),
            {"id": _new_id("workflow-event"), "state": target_state, "action": action, "actor": actor, "note": note or f"Workflow {action}d.", "at": _now()},
        ]
        fabric["audit_timeline"] = [
            *list(fabric.get("audit_timeline") or []),
            {"id": _new_id("workflow-audit"), "action": action, "actor": actor, "state": target_state, "at": _now()},
        ]
        self._persist_fabric(fabric)
        self.platform.repository.append_event(
            {
                "event_id": _new_id("workflow-event"),
                "occurred_at": _now(),
                "event_type": f"workflow.fabric.{action}",
                "tenant_id": workflow["tenant_id"],
                "organization_id": workflow["tenant_id"],
                "project_id": workflow["project_id"],
                "workflow_id": workflow_id,
                "actor": {"type": "user", "id": actor},
                "correlation_id": workflow_id,
                "causation_id": workflow_id,
                "metadata": {"fabric": "NovaWorkflow", "state": target_state},
                "data": {"workflow_id": workflow_id, "state": target_state, "action": action},
            }
        )
        self.platform.repository.append_audit(
            kind="workflow",
            actor=actor,
            service="NovaWorkflow Fabric",
            subject=workflow["title"],
            action=f"workflow.fabric.{action}",
            evidence=target_state,
            detail=f"Workflow fabric transition applied: {action}.",
        )
        return self._enrich(workflow, fabric)

    def _enrich(self, workflow: dict[str, Any], fabric: dict[str, Any]) -> dict[str, Any]:
        views = _workflow_views(workflow, fabric)
        fabric = dict(fabric)
        fabric["views"] = views
        fabric["execution_graph"] = views["execution_graph"]
        fabric["dashboard"] = _workflow_dashboard(workflow, fabric)
        return {
            **workflow,
            "fabric": fabric,
            "views": views,
            "dashboard": fabric["dashboard"],
            "contract": fabric["contract"],
            "state": fabric["state"],
            "revision": fabric["revision"],
            "evidence_refs": list(fabric.get("evidence_refs") or []),
        }


__all__ = [
    "WORKFLOW_CONNECTORS",
    "WORKFLOW_LIFECYCLE_STATES",
    "WORKFLOW_MARKETPLACE_CATEGORIES",
    "WORKFLOW_TEMPLATE_LIBRARY",
    "WORKFLOW_VIEWS",
    "WorkflowFabricService",
]
