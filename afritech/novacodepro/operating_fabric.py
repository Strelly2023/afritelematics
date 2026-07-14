from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


CANONICAL_ROLE_ALIASES = {
    "ADMIN": "PLATFORM_ADMIN",
    "SUPER_ADMIN": "PLATFORM_OWNER",
    "SYSTEM_ADMIN": "PLATFORM_ADMIN",
}

OPERATING_LIFECYCLE = [
    "Describe",
    "Understand",
    "Model",
    "Plan",
    "Simulate",
    "Assess",
    "Approve",
    "Execute",
    "Observe",
    "Validate",
    "Record",
    "Learn",
    "Optimize",
]

ENTERPRISE_OBJECT_TYPES = [
    "Capability",
    "Product",
    "Service",
    "Application",
    "API",
    "Dataset",
    "Knowledge Item",
    "Policy",
    "Risk",
    "Control",
    "Decision",
    "Approval",
    "Workflow",
    "Agent",
    "Model",
    "Twin",
    "Incident",
    "Recovery Plan",
    "Execution",
    "Evidence",
]

FABRICS = [
    "Enterprise Identity and Authority Fabric",
    "Enterprise Event Fabric",
    "Enterprise Capability Fabric",
    "Enterprise Knowledge Fabric",
    "Digital Twin and State Fabric",
    "AI and Agent Fabric",
    "Workflow and Execution Fabric",
    "Governance Fabric",
    "Resilience Fabric",
    "Evidence and Assurance Fabric",
]

COMMAND_CENTER_VIEWS = [
    "Executive View",
    "Operations View",
    "Architecture View",
    "Product View",
    "Security View",
    "Governance View",
    "AI View",
    "Data View",
    "Digital Twin View",
    "Resilience View",
    "Regional View",
]

PORTAL_NAVIGATION = [
    "Home",
    "Command Center",
    "Requests",
    "Workspaces",
    "Projects",
    "Architecture",
    "Capabilities",
    "Products",
    "Agents",
    "Workflows",
    "Reviews",
    "Approvals",
    "Knowledge",
    "Digital Twins",
    "Simulations",
    "Incidents",
    "Recovery",
    "Evidence",
    "Observability",
    "Reports",
    "Administration",
]

VIEW_STATES = ["Loading", "Ready", "Empty", "Degraded", "Unavailable", "Forbidden", "Error", "Recovery"]

REQUEST_STATES = {
    "DRAFT": {"SUBMITTED", "CANCELLED"},
    "SUBMITTED": {"PLANNING", "CANCELLED"},
    "PLANNING": {"REVIEW_REQUIRED", "APPROVED", "FAILED", "CANCELLED"},
    "REVIEW_REQUIRED": {"APPROVED", "FAILED", "CANCELLED"},
    "APPROVED": {"EXECUTING", "CANCELLED"},
    "EXECUTING": {"VALIDATING", "FAILED"},
    "VALIDATING": {"COMPLETED", "FAILED"},
    "COMPLETED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
}

KNOWLEDGE_STATES = {
    "DRAFT": {"VALIDATING", "ARCHIVED"},
    "VALIDATING": {"REVIEW_REQUIRED", "DISPUTED", "ARCHIVED"},
    "REVIEW_REQUIRED": {"APPROVED", "DISPUTED", "ARCHIVED"},
    "APPROVED": {"PUBLISHED", "SUPERSEDED", "ARCHIVED"},
    "PUBLISHED": {"STALE", "DISPUTED", "SUPERSEDED", "ARCHIVED"},
    "STALE": {"PUBLISHED", "SUPERSEDED", "ARCHIVED"},
    "DISPUTED": {"REVIEW_REQUIRED", "ARCHIVED"},
    "SUPERSEDED": {"ARCHIVED"},
    "ARCHIVED": set(),
}

RELATIONSHIP_TYPES = {
    "OWNS",
    "BELONGS_TO",
    "DEPENDS_ON",
    "ENABLES",
    "IMPLEMENTS",
    "OPERATES",
    "GOVERNS",
    "MITIGATES",
    "APPROVES",
    "EXECUTES",
    "PRODUCES",
    "CONSUMES",
    "REPRESENTS",
    "OBSERVES",
    "PREDICTS",
    "SIMULATES",
    "RECOVERS",
    "VALIDATES",
    "EVIDENCED_BY",
    "LEARNED_FROM",
    "SUPERSEDES",
    "CONTRADICTS",
}

ASSERTION_TYPES = {"DECLARED", "OBSERVED", "INFERRED", "IMPORTED", "APPROVED"}


class PolicyOutcome(str, Enum):
    PERMIT = "PERMIT"
    DENY = "DENY"
    PERMIT_WITH_CONDITIONS = "PERMIT_WITH_CONDITIONS"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REQUIRE_MFA = "REQUIRE_MFA"
    REQUIRE_EVIDENCE = "REQUIRE_EVIDENCE"
    QUARANTINE = "QUARANTINE"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class EnterpriseExecutionContext:
    subject_id: str
    actor_type: str
    tenant_id: str
    organization_id: str
    workspace_id: str
    canonical_roles: tuple[str, ...]
    permissions: frozenset[str]
    authority_grants: tuple[str, ...]
    session_id: str
    authentication_strength: str
    device_trust: int
    session_risk: int
    jurisdiction: str
    region: str
    correlation_id: str


class MissingTrustedExecutionContext(PermissionError):
    pass


def require_execution_context(
    context: EnterpriseExecutionContext | None,
    *,
    environment: str,
) -> EnterpriseExecutionContext:
    if context is not None:
        return context
    if environment.lower() in {"test", "development"}:
        raise MissingTrustedExecutionContext(
            "Inject an explicit test execution context. Payload-derived authority is prohibited."
        )
    raise MissingTrustedExecutionContext("trusted_execution_context_required")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "enterprise-object"


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))


def validate_transition(machine: dict[str, set[str]], current: str, target: str) -> None:
    if current == target:
        return
    allowed = machine.get(current)
    if allowed is None or target not in allowed:
        raise ValueError(f"invalid_lifecycle_transition:{current}->{target}")


def normalize_role(role: str) -> str:
    value = str(role or "OBSERVER").strip().upper()
    return CANONICAL_ROLE_ALIASES.get(value, value)


def subject_hash(payload: dict[str, Any]) -> str:
    return f"sha256:{_hash_payload(payload)}"


def enterprise_object_envelope(
    *,
    object_id: str | None,
    object_type: str,
    tenant_id: str,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    owner: str = "NovaCodePro",
    lifecycle_status: str = "ACTIVE",
    classification: str = "INTERNAL",
    jurisdiction: str = "AU",
    region: str = "Australia",
    version: str = "1.0",
    correlation_id: str | None = None,
    policy_context: dict[str, Any] | None = None,
    risk_context: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = _now()
    normalized_type = str(object_type or "Enterprise Object").strip()
    record_id = object_id or _new_id(_slug(normalized_type))
    return {
        "id": record_id,
        "type": normalized_type,
        "object_type": normalized_type,
        "tenant_id": tenant_id,
        "organization_id": organization_id or tenant_id,
        "workspace_id": workspace_id or "workspace-platform",
        "owner": owner,
        "owner_id": owner,
        "lifecycle_status": lifecycle_status,
        "classification": classification,
        "jurisdiction": jurisdiction,
        "region": region,
        "version": version,
        "schema_version": version,
        "object_version": 1,
        "correlation_id": correlation_id or record_id,
        "policy_context": dict(policy_context or {}),
        "risk_context": dict(risk_context or {}),
        "evidence": list(evidence or []),
        "data": dict(data or {}),
        "created_at": now,
        "updated_at": now,
    }


def canonical_event_contract(
    *,
    event_type: str,
    tenant_id: str,
    actor_type: str,
    actor_id: str,
    subject_type: str,
    subject_id: str,
    organization_id: str | None = None,
    workspace_id: str = "workspace-platform",
    correlation_id: str | None = None,
    causation_id: str | None = None,
    classification: str = "INTERNAL",
    region: str = "Australia",
    data: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": _new_id("evt"),
        "event_type": event_type,
        "schema_version": "1.0",
        "tenant_id": tenant_id,
        "organization_id": organization_id or tenant_id,
        "workspace_id": workspace_id,
        "actor": {"type": actor_type, "id": actor_id},
        "subject": {"type": subject_type, "id": subject_id},
        "correlation_id": correlation_id or subject_id,
        "causation_id": causation_id or subject_id,
        "classification": classification,
        "region": region,
        "occurred_at": _now(),
        "data": dict(data or {}),
        "evidence": list(evidence or []),
    }


def canonical_evidence_object(
    *,
    evidence_type: str,
    subject_type: str,
    subject_id: str,
    actor_id: str,
    authority_reference: str,
    policy_results: list[str],
    classification: str = "INTERNAL",
    region: str = "Australia",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = _now()
    evidence_payload = {
        "schema_version": "2.0",
        "domain": "NOVATECH_EVIDENCE",
        "evidence_type": evidence_type,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "actor_id": actor_id,
        "authority_reference": authority_reference,
        "policy_results": list(policy_results),
        "classification": classification,
        "region": region,
        "payload": dict(payload or {}),
    }
    content_hash = f"sha256:{_hash_payload(evidence_payload)}"
    signing_input = f"NOVATECH_EVIDENCE:{content_hash}".encode("utf-8")
    signature = hmac.new(b"novacodepro-local-evidence-key", signing_input, hashlib.sha256).hexdigest()
    return {
        "evidence_id": _new_id("evd"),
        "schema_version": "2.0",
        "domain": "NOVATECH_EVIDENCE",
        "evidence_type": evidence_type,
        "subject": {"type": subject_type, "id": subject_id, "version": 1},
        "subject_type": subject_type,
        "subject_id": subject_id,
        "actor": {"type": "USER" if actor_id != "recovery-agent" else "AI_AGENT", "id": actor_id},
        "actor_id": actor_id,
        "authority_reference": authority_reference,
        "policy_decision_ids": list(policy_results),
        "policy_results": list(policy_results),
        "content_hash": content_hash,
        "payload_hash": content_hash,
        "signing_key_id": "local://novacodepro/evidence-development-key",
        "signature_algorithm": "HMAC_SHA_256_LOCAL",
        "signature": signature,
        "classification": classification,
        "region": region,
        "created_at": now,
        "signed_at": now,
        "verification_status": "VERIFIED",
        "payload": dict(payload or {}),
    }


def build_operating_fabric_manifest() -> dict[str, Any]:
    return {
        "id": "novacodepro-unified-enterprise-operating-fabric",
        "name": "NovaCodePro Unified Enterprise Operating Fabric",
        "version": "1.0",
        "positioning": "NovaCodePro understands, builds, governs, executes, verifies, and remembers governed enterprise work.",
        "lifecycle": OPERATING_LIFECYCLE,
        "fabrics": FABRICS,
        "enterprise_object_types": ENTERPRISE_OBJECT_TYPES,
        "role_normalization": CANONICAL_ROLE_ALIASES,
        "command_center_views": COMMAND_CENTER_VIEWS,
        "portal_navigation": PORTAL_NAVIGATION,
        "view_states": VIEW_STATES,
        "canonical_contracts": [
            "Enterprise Object Envelope",
            "Event Envelope",
            "Evidence Contract",
            "Twin Contract",
            "Agent Contract",
            "Workflow Contract",
            "Policy Decision Contract",
        ],
        "runtime_loop": [
            "Observe",
            "Correlate",
            "Update twins",
            "Detect drift",
            "Calculate impact",
            "Retrieve knowledge",
            "Generate recommendations",
            "Evaluate policy and risk",
            "Request approval",
            "Execute",
            "Validate",
            "Record evidence",
            "Update knowledge",
            "Recalculate enterprise state",
        ],
    }


class EnterpriseOperatingFabric:
    def __init__(self, platform: Any) -> None:
        self.platform = platform

    def manifest(self) -> dict[str, Any]:
        return build_operating_fabric_manifest()

    def enterprise_objects(self) -> list[dict[str, Any]]:
        return self.platform.repository.list("enterprise_object")

    def capability_registry(self) -> list[dict[str, Any]]:
        return self.platform.repository.list("enterprise_capability")

    def command_center(self) -> dict[str, Any]:
        twins = self.platform.digital_twins()
        risks = self.platform.risks()
        approvals = self.platform.approvals()
        workflows = self.platform.workflows()
        events = self.platform.events(limit=200)
        evidence = self.platform.evidence_bundles()
        capabilities = self.capability_registry()
        open_approvals = [item for item in approvals if str(item.get("status") or "").upper() == "PENDING"]
        active_workflows = [item for item in workflows if str(item.get("status") or "").lower() in {"active", "waiting-approval", "paused"}]
        degraded_twins = [item for item in twins if str(item.get("status") or "").lower() != "healthy"]
        critical_risks = [item for item in risks if str(item.get("classification") or "").upper() in {"HIGH", "CRITICAL"}]
        return {
            "id": "global-command-center",
            "status": "READY",
            "views": COMMAND_CENTER_VIEWS,
            "enterprise_health": {
                "status": "DEGRADED" if degraded_twins or critical_risks else "HEALTHY",
                "capability_count": len(capabilities),
                "active_workflows": len(active_workflows),
                "pending_approvals": len(open_approvals),
                "critical_risks": len(critical_risks),
                "degraded_twins": len(degraded_twins),
                "evidence_count": len(evidence),
                "event_count": len(events),
            },
            "executive_view": {
                "enterprise_health": "DEGRADED" if degraded_twins or critical_risks else "HEALTHY",
                "required_approvals": open_approvals[:10],
                "critical_risks": critical_risks[:10],
                "resilience_score": self.platform.digital_twin_summary().get("scores", {}).get("enterprise_resilience_score"),
            },
            "operations_view": {
                "active_workflows": active_workflows[:10],
                "degraded_twins": degraded_twins[:10],
                "recent_events": events[:10],
            },
            "governance_view": {
                "pending_approvals": open_approvals[:10],
                "policy_count": len(self.platform.policies()),
                "evidence_count": len(evidence),
            },
            "ai_view": {
                "registered_agents": len(self.platform.agents()),
                "active_agent_tasks": len(self.platform.pending_agent_executions()),
                "kill_switch_status": "READY",
            },
            "updated_at": _now(),
        }

    def submit_enterprise_request(
        self,
        payload: dict[str, Any],
        *,
        context: EnterpriseExecutionContext | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        context = require_execution_context(
            context,
            environment=str(payload.get("runtime_environment") or os.environ.get("NOVACODEPRO_RUNTIME_ENVIRONMENT", "production")),
        )
        self._reject_authority_mismatch(payload, context)
        if idempotency_key:
            existing_result = self.platform.repository.get("idempotency_result", f"{context.tenant_id}:{idempotency_key}")
            if existing_result is not None:
                return dict(existing_result["result"])
        tenant_id = context.tenant_id
        workspace_id = context.workspace_id
        actor = {"type": context.actor_type, "id": context.subject_id}
        canonical_roles = list(context.canonical_roles)
        request_text = str(payload.get("request") or payload.get("title") or "Governed enterprise request")
        title = str(payload.get("title") or request_text[:80])
        correlation_id = context.correlation_id

        request_object = enterprise_object_envelope(
            object_id=str(payload.get("id") or _new_id("enterprise-request")),
            object_type="Request",
            tenant_id=tenant_id,
            organization_id=context.organization_id,
            workspace_id=workspace_id,
            owner=str(payload.get("owner") or actor["id"]),
            lifecycle_status="SUBMITTED",
            classification=str(payload.get("classification") or "INTERNAL"),
            jurisdiction=context.jurisdiction,
            region=context.region,
            version=str(payload.get("version") or "1.0"),
            correlation_id=correlation_id,
            data={
                "title": title,
                "request": request_text,
                "canonical_roles": canonical_roles,
                "desired_outcomes": list(payload.get("desired_outcomes") or []),
                "constraints": list(payload.get("constraints") or []),
                "requested_metadata": self._non_authority_metadata(payload),
            },
        )
        self._upsert_enterprise_object(request_object)

        workflow = self.platform.create_workflow(
            {
                "title": title,
                "request": request_text,
                "tenant_id": tenant_id,
                "project_id": payload.get("project_id"),
                "template_id": payload.get("template_id") or "unified-operating-fabric",
                "domain": payload.get("domain") or "enterprise",
                "region": context.region,
                "compliance": payload.get("compliance") or "enterprise",
                "surfaces": list(payload.get("surfaces") or []),
            }
        )
        workflow["status"] = "planning"
        workflow["current_stage"] = {"id": "02-register-request", "label": "Register request", "status": "complete"}
        workflow["durability"] = {
            "engine": "local-durable-workflow",
            "replayable": True,
            "idempotency_key": idempotency_key or "",
            "material_execution_blocked": True,
            "compensation_ready": True,
        }
        self.platform.repository.upsert("workflow", workflow)

        capability = self._register_capability(payload, tenant_id, workspace_id, workflow, correlation_id)
        risk = self.platform.evaluate_risk(
            {
                "title": f"{title} operating risk",
                "likelihood": payload.get("likelihood") or "medium",
                "impact": payload.get("impact") or ("high" if str(payload.get("environment") or "").lower() == "production" else "medium"),
                "exposure": payload.get("exposure") or "medium",
                "tenant_id": tenant_id,
                "project_id": workflow["project_id"],
                "workflow_id": workflow["id"],
                "owner": payload.get("risk_owner") or "risk-team",
            }
        )
        plan = self._build_plan(workflow, capability, risk, payload)
        policy = self.platform.evaluate_policy(
            {
                "policy_id": payload.get("policy_id") or "REL-PROD-001",
                "tenant_id": tenant_id,
                "project_id": workflow["project_id"],
                "workflow_id": workflow["id"],
                "environment": payload.get("requested_environment") or payload.get("environment") or "development",
                "criticality": capability["criticality"],
                "risk_classification": risk["classification"],
                "approvals": [],
                "rollback_plan": payload.get("rollback_expectation") or payload.get("rollback_plan") or "rollback through governed workflow",
                "plan": plan,
            }
        )

        plan_hash = self._approval_subject_hash(workflow["id"], 1, plan, risk, policy)
        approval = self.platform.create_approval(
            {
                "gate_type": "ENTERPRISE_OPERATING_FABRIC_APPROVAL",
                "workflow_id": workflow["id"],
                "requested_by": actor["id"],
                "conditions": list(policy.get("conditions") or ["No agent self-approval", "Evidence required before knowledge promotion"]),
                "evidence_ids": [],
                "subject_hash": plan_hash,
                "expires_at": policy.get("expires_at"),
                "required_quorum": policy.get("quorum", 1),
            }
        )
        approval["subject_hash"] = plan_hash
        approval["plan_version"] = 1
        approval["expires_at"] = policy.get("expires_at")
        approval["required_quorum"] = policy.get("quorum", 1)
        self.platform.repository.upsert("approval", approval)
        evidence_contract = canonical_evidence_object(
            evidence_type="ENTERPRISE_REQUEST_DESIGNED",
            subject_type="WORKFLOW",
            subject_id=workflow["id"],
            actor_id=actor["id"],
            authority_reference=",".join(context.authority_grants) or "authority-observe",
            policy_results=[policy["decision_id"]],
            classification=request_object["classification"],
            region=request_object["region"],
            payload={"request_object": request_object["id"], "capability_id": capability["id"], "risk_id": risk["id"]},
        )
        evidence_bundle = self.platform.create_evidence_bundle(
            {
                "id": evidence_contract["evidence_id"],
                "tenant_id": tenant_id,
                "workflow_id": workflow["id"],
                "actor": {"type": actor["type"], "id": actor["id"]},
                "action": "enterprise.request.recorded",
                "policy_id": policy["policy_id"],
                "artifact_ids": [capability["id"], risk["id"], approval["id"]],
                "payload": evidence_contract,
                "verified": True,
            }
        )

        twin = self._register_planning_twin(payload, tenant_id, workflow, capability, evidence_bundle, risk)
        knowledge = self._publish_operating_knowledge(payload, tenant_id, workflow, capability, evidence_bundle, twin)
        graph = self._connect_enterprise_graph(request_object, capability, workflow, twin, knowledge, evidence_bundle)

        target_state = "REVIEW_REQUIRED" if policy.get("outcome") in {PolicyOutcome.REQUIRE_APPROVAL.value, PolicyOutcome.ESCALATE.value} else "PLANNING"
        validate_transition(REQUEST_STATES, request_object["lifecycle_status"], "PLANNING")
        request_object["lifecycle_status"] = "PLANNING"
        if target_state == "REVIEW_REQUIRED":
            validate_transition(REQUEST_STATES, request_object["lifecycle_status"], "REVIEW_REQUIRED")
            request_object["lifecycle_status"] = "REVIEW_REQUIRED"
        request_object["policy_context"] = policy
        request_object["risk_context"] = risk
        request_object["evidence"] = [evidence_bundle["id"]]
        request_object["updated_at"] = _now()
        self._upsert_enterprise_object(request_object)
        self.platform.repository.append_event(
            {
                **canonical_event_contract(
                    event_type="enterprise.request.accepted",
                    tenant_id=tenant_id,
                    organization_id=tenant_id,
                    workspace_id=workspace_id,
                    actor_type=actor["type"],
                    actor_id=actor["id"],
                    subject_type="WORKFLOW",
                    subject_id=workflow["id"],
                    correlation_id=correlation_id,
                    causation_id=request_object["id"],
                    classification=request_object["classification"],
                    region=request_object["region"],
                    data={"request_object_id": request_object["id"], "capability_id": capability["id"], "twin_id": twin["id"]},
                    evidence=[evidence_bundle["id"]],
                ),
                "project_id": workflow["project_id"],
                "workflow_id": workflow["id"],
                "metadata": {"fabric": "novacodepro-unified-enterprise-operating-fabric"},
            }
        )

        result = {
            "request_id": request_object["id"],
            "workflow_id": workflow["id"],
            "status": request_object["lifecycle_status"],
            "correlation_id": correlation_id,
            "status_url": f"/v1/novacodepro/workflows/{workflow['id']}",
            "request_object": request_object,
            "workflow": workflow,
            "capability": capability,
            "policy_decision": policy,
            "risk": risk,
            "approval": approval,
            "agent_executions": [],
            "twin": twin,
            "evidence": evidence_bundle,
            "knowledge": knowledge,
            "graph": graph,
            "command_center": self.command_center(),
        }
        if idempotency_key:
            self.platform.repository.upsert(
                "idempotency_result",
                {
                    "id": f"{context.tenant_id}:{idempotency_key}",
                    "tenant_id": context.tenant_id,
                    "actor_id": context.subject_id,
                    "payload_hash": subject_hash(payload),
                    "result": result,
                },
            )
        return result

    def _reject_authority_mismatch(self, payload: dict[str, Any], context: EnterpriseExecutionContext) -> None:
        requested_tenant = payload.get("tenant_id")
        if requested_tenant and str(requested_tenant) != context.tenant_id:
            raise PermissionError("requested_tenant_mismatch")
        requested_org = payload.get("organization_id")
        if requested_org and str(requested_org) != context.organization_id:
            raise PermissionError("requested_organization_mismatch")
        requested_actor = payload.get("requested_by") or (dict(payload.get("actor") or {}).get("id"))
        if requested_actor and str(requested_actor) != context.subject_id:
            raise PermissionError("requested_actor_mismatch")
        if context.session_risk >= 80:
            raise PermissionError("high_risk_session_requires_mfa")

    def _non_authority_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        forbidden = {"roles", "tenant_id", "organization_id", "requested_by", "actor", "authority_level"}
        return {key: value for key, value in payload.items() if key not in forbidden}

    def _upsert_enterprise_object(self, obj: dict[str, Any]) -> dict[str, Any]:
        existing = self.platform.repository.get("enterprise_object", obj["id"])
        if existing:
            obj["created_at"] = existing.get("created_at", obj["created_at"])
            obj["object_version"] = int(existing.get("object_version") or 1) + 1
            self.platform.repository.upsert(
                "enterprise_object_version",
                {
                    "id": f"{obj['id']}:v{obj['object_version']}",
                    "object_id": obj["id"],
                    "object_version": obj["object_version"],
                    "tenant_id": obj["tenant_id"],
                    "payload": obj,
                },
            )
        return self.platform.repository.upsert("enterprise_object", obj)

    def _build_plan(self, workflow: dict[str, Any], capability: dict[str, Any], risk: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "workflow_id": workflow["id"],
            "plan_version": 1,
            "actions": [
                "resolve_capability",
                "retrieve_knowledge",
                "prepare_agent_plan",
                "evaluate_policy",
                "request_human_approval",
            ],
            "affected_resources": [capability["id"], *capability.get("services", [])],
            "rollback_plan": payload.get("rollback_expectation") or "rollback through governed workflow",
            "risk_result": {"id": risk["id"], "classification": risk["classification"], "score": risk["score"]},
        }

    def _approval_subject_hash(self, workflow_id: str, plan_version: int, plan: dict[str, Any], risk: dict[str, Any], policy: dict[str, Any]) -> str:
        return subject_hash(
            {
                "workflow_id": workflow_id,
                "plan_version": plan_version,
                "actions": plan["actions"],
                "affected_resources": plan["affected_resources"],
                "rollback_plan": plan["rollback_plan"],
                "risk_result": {"id": risk["id"], "classification": risk["classification"], "score": risk["score"]},
                "policy_result": {"decision_id": policy["decision_id"], "outcome": policy["outcome"]},
            }
        )

    def _register_capability(
        self,
        payload: dict[str, Any],
        tenant_id: str,
        workspace_id: str,
        workflow: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]:
        name = str(payload.get("capability_hint") or payload.get("capability") or payload.get("capability_name") or payload.get("domain") or "Enterprise Operating Fabric")
        capability_id = str(payload.get("capability_id") or f"cap-{_slug(name)}")
        capability = {
            **enterprise_object_envelope(
                object_id=capability_id,
                object_type="Capability",
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                owner=str(payload.get("business_owner") or "NovaCodePro"),
                lifecycle_status="READY",
                classification=str(payload.get("classification") or "INTERNAL"),
                jurisdiction=str(payload.get("jurisdiction") or "AU"),
                region=str(payload.get("region") or "Australia"),
                correlation_id=correlation_id,
                data={"name": name, "workflow_id": workflow["id"]},
            ),
            "name": name,
            "business_owner": str(payload.get("business_owner") or "NovaCodePro"),
            "technical_owner": str(payload.get("technical_owner") or "Platform Engineering"),
            "operational_owner": str(payload.get("operational_owner") or "NovaOperations"),
            "data_owner": str(payload.get("data_owner") or "Chief Data & AI Office"),
            "criticality": str(payload.get("criticality") or "TIER_2"),
            "maturity": int(payload.get("maturity") or 3),
            "health": str(payload.get("health") or "READY"),
            "products": list(payload.get("products") or []),
            "services": list(payload.get("services") or ["NovaCodePro Gateway"]),
            "ai_agents": list(payload.get("agents") or ["architect-agent", "developer-agent", "qa-agent"]),
            "policies": [str(payload.get("policy_id") or "REL-PROD-001")],
            "risks": [],
            "controls": ["NovaPolicy", "NovaRisk", "NovaCompliance", "NovaAudit"],
            "digital_twins": [str(payload.get("twin_id") or f"twin-{_slug(name)}")],
            "rto": str(payload.get("rto") or "30m"),
            "rpo": str(payload.get("rpo") or "5m"),
            "dependencies": list(payload.get("dependencies") or []),
            "improvement_roadmap": list(payload.get("improvement_roadmap") or ["Measure health", "Exercise recovery", "Promote lessons"]),
        }
        self.platform.repository.upsert("enterprise_capability", capability)
        self._upsert_enterprise_object(capability)
        return capability

    def _assign_agents(self, payload: dict[str, Any], tenant_id: str, workflow: dict[str, Any], capability: dict[str, Any]) -> list[dict[str, Any]]:
        requested_agents = list(payload.get("agents") or capability.get("ai_agents") or [])
        executions: list[dict[str, Any]] = []
        for agent_id in requested_agents:
            executions.append(
                self.platform.create_agent_execution(
                    {
                        "agent_id": agent_id,
                        "tenant_id": tenant_id,
                        "project_id": workflow["project_id"],
                        "workflow_id": workflow["id"],
                        "stage_id": "enterprise-operating-fabric",
                        "input": {"capability_id": capability["id"], "request": workflow["request"]},
                        "output": {"recommendation": "prepare governed plan", "authority": "NO_SELF_APPROVAL"},
                        "allowed_tools": ["knowledge.query", "artifact.write", "policy.evaluate", "evidence.write"],
                        "forbidden_tools": ["production.deploy_without_approval", "secret.export", "self.approve"],
                        "approval_policy": "human-approval-required-for-material-actions",
                        "evidence": [],
                    }
                )
            )
        return executions

    def _register_planning_twin(
        self,
        payload: dict[str, Any],
        tenant_id: str,
        workflow: dict[str, Any],
        capability: dict[str, Any],
        evidence: dict[str, Any],
        risk: dict[str, Any],
    ) -> dict[str, Any]:
        twin_id = str(payload.get("twin_id") or capability["digital_twins"][0])
        twin = self.platform.create_digital_twin(
            {
                "id": twin_id,
                "name": f"{capability['name']} Capability Twin",
                "type": "CAPABILITY",
                "owner": capability["business_owner"],
                "tenant_id": tenant_id,
                "classification": capability["classification"],
                "jurisdiction": capability["jurisdiction"],
                "region": capability["region"],
                "status": "degraded" if risk["classification"] in {"HIGH", "CRITICAL"} else "healthy",
                "summary": "Capability twin maintained by the unified enterprise operating fabric.",
                "sources": ["workflow", "policy", "risk", "evidence"],
                "controls": capability["controls"],
                "metrics": {"risk_score": risk["score"], "recovery_minutes": 12, "maturity": capability["maturity"]},
                "observed_state": "AT_RISK" if risk["classification"] in {"HIGH", "CRITICAL"} else "HEALTHY",
                "desired_state": "READY",
                "predicted_state": "WATCH" if risk["classification"] in {"HIGH", "CRITICAL"} else "STABLE",
                "simulated_state": "NOT_RUN",
                "approved_state": "PENDING",
                "recovered_state": "NOT_RECOVERED",
                "state_versions": {
                    "observed_state": {"state_version": 1, "confidence": 0.82, "evidence": [evidence["id"]], "created_by": "twin-state-engine", "created_at": _now()},
                    "desired_state": {"state_version": 1, "confidence": 0.9, "evidence": [evidence["id"]], "created_by": "capability-registry", "created_at": _now()},
                    "predicted_state": {"state_version": 1, "confidence": 0.72, "evidence": [risk["id"]], "created_by": "risk-engine", "created_at": _now()},
                    "simulated_state": {"state_version": 0, "confidence": 0.0, "evidence": [], "created_by": "simulation-engine", "created_at": _now()},
                    "approved_state": {"state_version": 0, "confidence": 0.0, "evidence": [], "created_by": "approval-service", "created_at": _now()},
                    "recovered_state": {"state_version": 0, "confidence": 0.0, "evidence": [], "created_by": "eros", "created_at": _now()},
                },
                "confidence": {
                    "source_confidence": 0.82,
                    "observation_freshness": 1.0,
                    "relationship_confidence": 0.92,
                    "state_accuracy": 0.78,
                    "simulation_confidence": 0.0,
                    "recovery_confidence": 0.0,
                    "evidence_completeness": 0.75,
                },
                "relationships": [
                    {
                        "source": twin_id,
                        "target": workflow["id"],
                        "type": "DEPENDS_ON",
                        "criticality": "HIGH",
                        "confidence": 0.92,
                        "evidence": [evidence["id"]],
                    }
                ],
                "evidence": [evidence["id"]],
                "lineage": [workflow["id"]],
            }
        )
        self.platform.observe_twin(
            twin_id,
            {
                "observed_state": twin["observed_state"],
                "observed_detail": "Enterprise operating fabric request updated capability state.",
                "observed_evidence": [evidence["id"]],
                "metrics": twin["metrics"],
                "status": twin["status"],
            },
        )
        return self.platform.get_or_create_digital_twin(twin_id)

    def _update_operating_twin(
        self,
        payload: dict[str, Any],
        tenant_id: str,
        workflow: dict[str, Any],
        capability: dict[str, Any],
        evidence: dict[str, Any],
        risk: dict[str, Any],
    ) -> dict[str, Any]:
        return self._register_planning_twin(payload, tenant_id, workflow, capability, evidence, risk)

    def _publish_operating_knowledge(
        self,
        payload: dict[str, Any],
        tenant_id: str,
        workflow: dict[str, Any],
        capability: dict[str, Any],
        evidence: dict[str, Any],
        twin: dict[str, Any],
    ) -> dict[str, Any]:
        node = self.platform.create_knowledge_node(
            {
                "id": str(payload.get("knowledge_id") or f"knw-{workflow['id']}"),
                "label": f"{workflow['title']} operating knowledge draft",
                "type": "Draft Knowledge",
                "tenant_id": tenant_id,
                "owner": "NovaKnowledge",
                "evidence": [evidence["id"]],
                "links": [capability["id"], twin["id"]],
            }
        )
        node.update(
            {
                "knowledge_type": "OPERATING_LESSON",
                "authority_level": 1,
                "lifecycle_status": "DRAFT",
                "source_type": "ENTERPRISE_REQUEST",
                "source_references": [workflow["id"], capability["id"]],
                "evidence_ids": [evidence["id"]],
                "confidence": 0.65,
                "classification": capability["classification"],
                "review_due_at": _now(),
                "approved_by": [],
                "published_at": "",
                "memory_promotion": "BLOCKED_PENDING_REVIEW",
            }
        )
        self.platform.repository.upsert("knowledge_node", node)
        return node

    def _connect_enterprise_graph(
        self,
        request_object: dict[str, Any],
        capability: dict[str, Any],
        workflow: dict[str, Any],
        twin: dict[str, Any],
        knowledge: dict[str, Any],
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        request_node = self.platform.create_knowledge_node(
            {
                "id": f"graph-{request_object['id']}",
                "label": request_object["data"]["title"],
                "type": "Enterprise Request",
                "tenant_id": request_object["tenant_id"],
                "owner": request_object["owner"],
                "evidence": [evidence["id"]],
                "links": [capability["id"], workflow["id"]],
            }
        )
        for node in (
            {"id": capability["id"], "label": capability["name"], "type": "Capability", "links": [twin["id"], knowledge["id"]]},
            {"id": workflow["id"], "label": workflow["title"], "type": "Workflow", "links": [evidence["id"], twin["id"]]},
            {"id": twin["id"], "label": twin["name"], "type": "Digital Twin", "links": [knowledge["id"]]},
            {"id": evidence["id"], "label": evidence["action"], "type": "Evidence", "links": [knowledge["id"]]},
        ):
            existing = self.platform.repository.get("knowledge_node", node["id"])
            if existing is None:
                self.platform.create_knowledge_node(
                    {
                        "id": node["id"],
                        "label": node["label"],
                        "type": node["type"],
                        "tenant_id": request_object["tenant_id"],
                        "owner": "NovaCodePro",
                        "evidence": [evidence["id"]],
                        "links": node["links"],
                    }
                )
        relationships = [
            self._create_relationship(request_object["tenant_id"], request_object["id"], capability["id"], "DEPENDS_ON", evidence["id"], "DECLARED"),
            self._create_relationship(request_object["tenant_id"], request_object["id"], workflow["id"], "EXECUTES", evidence["id"], "DECLARED"),
            self._create_relationship(request_object["tenant_id"], capability["id"], twin["id"], "REPRESENTS", evidence["id"], "DECLARED"),
            self._create_relationship(request_object["tenant_id"], workflow["id"], evidence["id"], "EVIDENCED_BY", evidence["id"], "APPROVED"),
            self._create_relationship(request_object["tenant_id"], evidence["id"], knowledge["id"], "PRODUCES", evidence["id"], "DECLARED"),
            self._create_relationship(request_object["tenant_id"], twin["id"], knowledge["id"], "OBSERVES", evidence["id"], "OBSERVED"),
        ]
        return {
            "request_node": request_node["id"],
            "relationships": relationships,
        }

    def _create_relationship(
        self,
        tenant_id: str,
        source_id: str,
        target_id: str,
        relationship_type: str,
        evidence_id: str,
        assertion_type: str,
    ) -> dict[str, Any]:
        if relationship_type not in RELATIONSHIP_TYPES:
            raise ValueError("unsupported_relationship_type")
        if assertion_type not in ASSERTION_TYPES:
            raise ValueError("unsupported_assertion_type")
        relationship = {
            "id": f"rel-{_hash_payload({'tenant_id': tenant_id, 'source_id': source_id, 'target_id': target_id, 'relationship_type': relationship_type})[:16]}",
            "tenant_id": tenant_id,
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": relationship_type,
            "assertion_type": assertion_type,
            "criticality": "HIGH" if relationship_type in {"DEPENDS_ON", "RECOVERS", "VALIDATES"} else "MEDIUM",
            "confidence": 0.92 if assertion_type in {"DECLARED", "APPROVED"} else 0.74,
            "evidence_ids": [evidence_id],
            "valid_from": _now(),
            "valid_until": None,
            "created_by": "enterprise-operating-fabric",
            "schema_version": "1.0",
            "metadata": {},
        }
        return self.platform.repository.upsert("enterprise_relationship", relationship)
