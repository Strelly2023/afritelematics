from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


WORKFLOW_BLUEPRINT: list[dict[str, str]] = [
    {
        "id": "intent",
        "label": "Intent Engine",
        "kind": "automation",
        "service": "Intent Engine",
        "api": "POST /v1/novacodepro/workflows",
        "storage": "workflows",
        "audit": "workflow.intent.created",
        "ui": "Solution Studio",
        "output": "Intent brief",
    },
    {
        "id": "analysis",
        "label": "Business Analysis",
        "kind": "automation",
        "service": "Business Analysis Service",
        "api": "POST /v1/novacodepro/workflows/{workflow_id}/transition",
        "storage": "workflows",
        "audit": "workflow.analysis.generated",
        "ui": "Solution Studio",
        "output": "Requirements",
    },
    {
        "id": "architecture",
        "label": "Architecture",
        "kind": "automation",
        "service": "Architecture Service",
        "api": "POST /v1/novacodepro/workflows/{workflow_id}/transition",
        "storage": "workflows",
        "audit": "workflow.architecture.generated",
        "ui": "Architecture Studio",
        "output": "Architecture pack",
    },
    {
        "id": "uiux",
        "label": "UI/UX",
        "kind": "automation",
        "service": "UI/UX Service",
        "api": "POST /v1/novacodepro/workflows/{workflow_id}/transition",
        "storage": "workflows",
        "audit": "workflow.uiux.generated",
        "ui": "UI/UX Studio",
        "output": "Wireframes",
    },
    {
        "id": "implementation",
        "label": "Implementation",
        "kind": "automation",
        "service": "Engineering Service",
        "api": "POST /v1/novacodepro/workflows/{workflow_id}/transition",
        "storage": "artifacts",
        "audit": "workflow.implementation.generated",
        "ui": "Engineering Studio",
        "output": "Source scaffold",
    },
    {
        "id": "testing",
        "label": "Testing",
        "kind": "automation",
        "service": "Test Service",
        "api": "POST /v1/novacodepro/workflows/{workflow_id}/transition",
        "storage": "artifacts",
        "audit": "workflow.tests.executed",
        "ui": "Test Studio",
        "output": "Test report",
    },
    {
        "id": "security",
        "label": "Security Review",
        "kind": "automation",
        "service": "Security Service",
        "api": "POST /v1/novacodepro/workflows/{workflow_id}/transition",
        "storage": "artifacts",
        "audit": "workflow.security.reviewed",
        "ui": "Security Studio",
        "output": "Security findings",
    },
    {
        "id": "approval",
        "label": "Human Approval",
        "kind": "human",
        "service": "Governance Service",
        "api": "POST /v1/novacodepro/workflows/{workflow_id}/transition",
        "storage": "audit_events",
        "audit": "workflow.approved",
        "ui": "Governance Center",
        "output": "Approval record",
    },
    {
        "id": "release",
        "label": "Release",
        "kind": "automation",
        "service": "Release Factory",
        "api": "POST /v1/novacodepro/releases",
        "storage": "releases",
        "audit": "workflow.release.prepared",
        "ui": "Release Center",
        "output": "Release bundle",
    },
    {
        "id": "deployment",
        "label": "Deployment",
        "kind": "automation",
        "service": "Deployment Service",
        "api": "POST /v1/novacodepro/releases/{release_id}/transition",
        "storage": "releases",
        "audit": "workflow.deployment.exercised",
        "ui": "Deployment Studio",
        "output": "Deployment manifest",
    },
    {
        "id": "operations",
        "label": "Operations",
        "kind": "automation",
        "service": "Operations Center",
        "api": "GET /v1/novacodepro/status",
        "storage": "audit_events",
        "audit": "workflow.operations.monitored",
        "ui": "Operations Center",
        "output": "Operational telemetry",
    },
]

RELEASE_BLUEPRINT: list[dict[str, str]] = [
    {"id": "build", "label": "Build", "kind": "automation"},
    {"id": "test", "label": "Test", "kind": "automation"},
    {"id": "security", "label": "Security Scan", "kind": "automation"},
    {"id": "compliance", "label": "Compliance", "kind": "human"},
    {"id": "sign", "label": "Sign", "kind": "automation"},
    {"id": "publish", "label": "Publish", "kind": "automation"},
    {"id": "deploy", "label": "Deploy", "kind": "automation"},
    {"id": "verify", "label": "Verify", "kind": "automation"},
]

DEFAULT_TENANTS: list[dict[str, Any]] = [
    {
        "id": "novatech",
        "name": "NovaTech",
        "tier": "Enterprise",
        "regions": ["Australia", "Africa", "Europe"],
        "billing": "active",
        "quota": "12,000 seats",
        "branding": "NovaTech Blue",
        "residency": "AU + EU",
    },
    {
        "id": "pilot-mobility",
        "name": "Pilot Mobility",
        "tier": "Pilot",
        "regions": ["Australia"],
        "billing": "metered",
        "quota": "500 seats",
        "branding": "NovaRide",
        "residency": "AU",
    },
    {
        "id": "partner-labs",
        "name": "Partner Labs",
        "tier": "Sandbox",
        "regions": ["Australia", "Asia"],
        "billing": "sandbox",
        "quota": "200 seats",
        "branding": "NovaPartner",
        "residency": "AU + APAC",
    },
]

DEFAULT_PROJECTS: list[dict[str, Any]] = [
    {
        "id": "nova-ride-platform",
        "name": "NovaRide Platform",
        "tenant_id": "novatech",
        "status": "Active",
        "owner": "Platform Engineering",
        "solution": "Ride-hailing platform",
        "region": "Melbourne",
        "budget": "$1.8M",
    },
    {
        "id": "nova-pay-core",
        "name": "NovaPay Core",
        "tenant_id": "novatech",
        "status": "Review",
        "owner": "Payments Engineering",
        "solution": "Money transfer platform",
        "region": "Sydney",
        "budget": "$2.4M",
    },
]

DEFAULT_THREADS: list[dict[str, Any]] = [
    {
        "id": "thread-requirements",
        "tenant_id": "novatech",
        "project_id": "nova-ride-platform",
        "scope": "Requirements review",
        "participants": ["Product", "Finance", "Security"],
        "state": "waiting-approval",
        "messages": [
            {
                "id": "msg-req-1",
                "author": "NovaCodePro",
                "body": "Requirements need a privacy note before the next approval gate.",
                "at": "2026-07-11T00:00:00+00:00",
            }
        ],
    },
    {
        "id": "thread-architecture",
        "tenant_id": "novatech",
        "project_id": "nova-ride-platform",
        "scope": "Architecture discussion",
        "participants": ["Architecture", "DevOps", "Governance"],
        "state": "active",
        "messages": [
            {
                "id": "msg-arch-1",
                "author": "NovaCodePro",
                "body": "The trust boundary should remain explicit in the C4 export.",
                "at": "2026-07-11T00:00:00+00:00",
            }
        ],
    },
]

DEFAULT_KNOWLEDGE_GRAPH: list[dict[str, Any]] = [
    {"id": "kg-request", "label": "Business Request", "type": "intent", "links": ["kg-requirements", "kg-approval"]},
    {"id": "kg-requirements", "label": "Requirements", "type": "artifact", "links": ["kg-architecture", "kg-design"]},
    {"id": "kg-architecture", "label": "Architecture", "type": "artifact", "links": ["kg-api", "kg-deployment"]},
    {"id": "kg-api", "label": "API Spec", "type": "artifact", "links": ["kg-tests", "kg-release"]},
    {"id": "kg-tests", "label": "Test Report", "type": "evidence", "links": ["kg-security", "kg-audit"]},
    {"id": "kg-security", "label": "Security Review", "type": "evidence", "links": ["kg-audit"]},
    {"id": "kg-deployment", "label": "Deployment", "type": "runtime", "links": ["kg-operations"]},
    {"id": "kg-release", "label": "Release", "type": "artifact", "links": ["kg-operations", "kg-audit"]},
    {"id": "kg-operations", "label": "Operations", "type": "runtime", "links": ["kg-audit"]},
    {"id": "kg-audit", "label": "Audit Trail", "type": "governance", "links": []},
    {"id": "kg-design", "label": "UI/UX", "type": "artifact", "links": ["kg-implementation"]},
    {"id": "kg-implementation", "label": "Code", "type": "artifact", "links": ["kg-tests", "kg-deployment"]},
    {"id": "kg-approval", "label": "Approval Gate", "type": "governance", "links": ["kg-audit", "kg-release"]},
]

DEFAULT_INTEGRATIONS: list[dict[str, Any]] = [
    {"id": "github", "name": "GitHub", "kind": "source control", "status": "connected", "purpose": "repositories and pull requests"},
    {"id": "gitlab", "name": "GitLab", "kind": "source control", "status": "available", "purpose": "mirrored repositories"},
    {"id": "jira", "name": "Jira", "kind": "workflow", "status": "available", "purpose": "issue tracking and approvals"},
    {"id": "slack", "name": "Slack", "kind": "notifications", "status": "connected", "purpose": "review alerts and approvals"},
    {"id": "kubernetes", "name": "Kubernetes", "kind": "runtime", "status": "connected", "purpose": "deployment targets and rollouts"},
    {"id": "postgres", "name": "PostgreSQL", "kind": "storage", "status": "connected", "purpose": "solution and audit storage"},
    {"id": "grafana", "name": "Grafana", "kind": "observability", "status": "available", "purpose": "dashboards and service health"},
]

DEFAULT_MARKETPLACE: list[dict[str, Any]] = [
    {
        "id": "banking-agent",
        "name": "Banking Agent",
        "category": "solution",
        "version": "2026.1",
    },
    {
        "id": "healthcare-agent",
        "name": "Healthcare Agent",
        "category": "solution",
        "version": "2026.1",
    },
    {
        "id": "ride-hailing-agent",
        "name": "Ride Platform Agent",
        "category": "solution",
        "version": "2026.1",
    },
    {
        "id": "erp-agent",
        "name": "ERP Agent",
        "category": "solution",
        "version": "2026.1",
    },
]

DEFAULT_DEVELOPER_SURFACES: list[dict[str, str]] = [
    {
        "id": "rest-apis",
        "name": "REST APIs",
        "description": "Solution, workflow, audit, artifact, and release APIs.",
    },
    {
        "id": "graphql",
        "name": "GraphQL",
        "description": "Cross-surface query model for the enterprise graph.",
    },
    {
        "id": "webhooks",
        "name": "Webhooks",
        "description": "Event delivery for approvals, deployments, and incidents.",
    },
    {
        "id": "cli",
        "name": "CLI",
        "description": "Command-line access for automation and local workflows.",
    },
    {
        "id": "sdks",
        "name": "SDKs",
        "description": "TypeScript, Python, Java, and Go integration kits.",
    },
    {
        "id": "policy-packs",
        "name": "Policy Packs",
        "description": "Reusable governance rules for solution execution.",
    },
]

DEFAULT_SERVICE_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "gateway-service",
        "name": "NovaCodePro Gateway",
        "category": "control-plane",
        "status": "healthy",
        "api": "/api/v1/solutions",
    },
    {
        "id": "workflow-service",
        "name": "Workflow Service",
        "category": "orchestration",
        "status": "healthy",
        "api": "/api/v1/workflows",
    },
    {
        "id": "agent-orchestrator",
        "name": "Agent Orchestrator",
        "category": "execution",
        "status": "healthy",
        "api": "/api/v1/agents/executions",
    },
    {
        "id": "artifact-service",
        "name": "Artifact Service",
        "category": "storage",
        "status": "healthy",
        "api": "/api/v1/artifacts",
    },
    {
        "id": "approval-service",
        "name": "Approval Service",
        "category": "governance",
        "status": "healthy",
        "api": "/api/v1/approvals",
    },
    {
        "id": "release-factory",
        "name": "Release Factory",
        "category": "delivery",
        "status": "healthy",
        "api": "/api/v1/releases",
    },
    {
        "id": "digital-twin",
        "name": "Digital Twin Engine",
        "category": "observability",
        "status": "healthy",
        "api": "/api/v1/digital-twins",
    },
]

DEFAULT_SOLUTIONS: list[dict[str, Any]] = [
    {
        "id": "solution-ride-platform",
        "tenant_id": "novatech",
        "project_id": "nova-ride-platform",
        "title": "NovaRide Platform",
        "request": "Build a governed ride-hailing platform.",
        "status": "release_ready",
        "workflow_id": "workflow-ride-platform",
        "version": "2026.1",
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    },
]

DEFAULT_AGENT_EXECUTIONS: list[dict[str, Any]] = [
    {
        "id": "agent-execution-architecture",
        "agent_id": "architecture-agent",
        "version": "2027.1.0",
        "category": "engineering",
        "tenant_id": "novatech",
        "project_id": "nova-ride-platform",
        "workflow_id": "workflow-ride-platform",
        "stage_id": "architecture",
        "status": "completed",
        "input": {"brief": "Ride-hailing platform for Melbourne"},
        "output": {"artifact": "architecture-pack"},
        "allowed_tools": ["artifact.read", "artifact.write", "knowledge.query"],
        "forbidden_tools": ["production.deploy", "secret.export"],
        "timeout_seconds": 900,
        "maximum_cost": 10.0,
        "approval_policy": "architecture-review-required",
        "evidence": ["architecture-pack", "traceability-links"],
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    },
]

DEFAULT_APPROVALS: list[dict[str, Any]] = [
    {
        "id": "approval-security-ride-platform",
        "gate_type": "SECURITY_APPROVAL",
        "workflow_id": "workflow-ride-platform",
        "release_id": "release-ride-platform",
        "status": "APPROVED",
        "requested_by": "platform-admin",
        "approved_by": "security-officer-8",
        "requested_at": "2026-07-11T00:00:00+00:00",
        "decided_at": "2026-07-11T00:00:00+00:00",
        "decision": "approve",
        "conditions": ["Enable enhanced monitoring for 48 hours"],
        "evidence_ids": ["evidence-threat-model", "evidence-sbom", "evidence-security-scan"],
        "signature": "digital-signature",
        "audit_event_id": "audit-approval-security-ride-platform",
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    },
]

DEFAULT_DEPLOYMENTS: list[dict[str, Any]] = [
    {
        "id": "deployment-ride-platform-staging",
        "workflow_id": "workflow-ride-platform",
        "release_id": "release-ride-platform",
        "environment": "staging",
        "region": "Australia",
        "status": "healthy",
        "health": "green",
        "version": "2026.1.3",
        "metrics": {
            "availability": 0.999,
            "latency_p95_ms": 118,
            "error_rate": 0.0002,
        },
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    },
]

DEFAULT_DIGITAL_TWINS: list[dict[str, Any]] = [
    {
        "id": "twin-novacodepro",
        "name": "NovaCodePro Platform Twin",
        "kind": "organization",
        "status": "healthy",
        "region": "Australia",
        "children": ["twin-ride-platform", "twin-release-factory"],
        "health": {
            "availability": 0.999,
            "latency_p95_ms": 118,
            "error_rate": 0.0002,
        },
        "topology": {
            "services": [
                "NovaCodePro Gateway",
                "Workflow Service",
                "Agent Orchestrator",
                "Artifact Service",
                "Release Factory",
                "Deployment Service",
            ]
        },
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    },
]


def _stage_view(blueprint: list[dict[str, str]], stage_index: int, flow_status: str) -> list[dict[str, str]]:
    stages: list[dict[str, str]] = []
    for index, stage in enumerate(blueprint):
        if index < stage_index:
            status = "completed"
        elif index > stage_index:
            status = "pending"
        elif flow_status == "paused":
            status = "paused"
        elif flow_status == "rejected":
            status = "rejected"
        elif flow_status == "waiting-approval" and stage["kind"] == "human":
            status = "waiting-approval"
        else:
            status = "in_progress"
        stages.append({**stage, "status": status})
    return stages


def _event_envelope(
    *,
    event_type: str,
    actor_type: str,
    actor_id: str,
    tenant_id: str,
    organization_id: str,
    project_id: str | None,
    workflow_id: str | None,
    correlation_id: str | None,
    causation_id: str | None,
    data: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = _now()
    return {
        "event_id": _new_id("event"),
        "event_type": event_type,
        "schema_version": "1.0",
        "occurred_at": now,
        "correlation_id": correlation_id or _new_id("correlation"),
        "causation_id": causation_id or _new_id("causation"),
        "tenant_id": tenant_id,
        "organization_id": organization_id,
        "project_id": project_id,
        "workflow_id": workflow_id,
        "actor": {
            "type": actor_type,
            "id": actor_id,
        },
        "data": data,
        "metadata": {
            "environment": "production",
            "region": "Australia",
            **(metadata or {}),
        },
    }


class NovaCodeProRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.path = Path(db_path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS records (
                    kind TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (kind, record_id)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    service TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    action TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS domain_events (
                    event_id TEXT PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    project_id TEXT,
                    workflow_id TEXT,
                    actor_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    causation_id TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                """
            )
        self._seed()

    def _seed(self) -> None:
        seeds = {
            "tenant": DEFAULT_TENANTS,
            "project": DEFAULT_PROJECTS,
            "collaboration_thread": DEFAULT_THREADS,
            "knowledge_node": DEFAULT_KNOWLEDGE_GRAPH,
            "integration": DEFAULT_INTEGRATIONS,
            "marketplace_item": DEFAULT_MARKETPLACE,
            "developer_surface": DEFAULT_DEVELOPER_SURFACES,
            "solution": DEFAULT_SOLUTIONS,
            "agent_execution": DEFAULT_AGENT_EXECUTIONS,
            "approval": DEFAULT_APPROVALS,
            "deployment": DEFAULT_DEPLOYMENTS,
            "digital_twin": DEFAULT_DIGITAL_TWINS,
            "service": DEFAULT_SERVICE_REGISTRY,
        }
        with self._connect() as connection:
            for kind, payloads in seeds.items():
                count = connection.execute("SELECT COUNT(*) FROM records WHERE kind = ?", (kind,)).fetchone()[0]
                if count:
                    continue
                for payload in payloads:
                    now = _now()
                    record = dict(payload)
                    record.setdefault("created_at", now)
                    record.setdefault("updated_at", now)
                    connection.execute(
                        """
                        INSERT INTO records (kind, record_id, payload_json, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            kind,
                            str(record["id"]),
                            json.dumps(record, sort_keys=True),
                            str(record["created_at"]),
                            str(record["updated_at"]),
                        ),
                    )

    def get(self, kind: str, record_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM records WHERE kind = ? AND record_id = ?",
                (kind, record_id),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload_json"])

    def list(self, kind: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM records WHERE kind = ? ORDER BY updated_at DESC, record_id DESC",
                (kind,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def upsert(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload = dict(payload)
        record_id = str(payload["id"])
        now = _now()
        existing = self.get(kind, record_id)
        payload.setdefault("created_at", existing.get("created_at") if existing else now)
        payload["updated_at"] = now
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO records (kind, record_id, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(kind, record_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    kind,
                    record_id,
                    json.dumps(payload, sort_keys=True),
                    str(payload["created_at"]),
                    str(payload["updated_at"]),
                ),
            )
        return payload

    def append_audit(self, *, kind: str, actor: str, service: str, subject: str, action: str, evidence: str, detail: str) -> dict[str, Any]:
        event = {
            "id": _new_id("audit"),
            "at": _now(),
            "kind": kind,
            "actor": actor,
            "service": service,
            "subject": subject,
            "action": action,
            "evidence": evidence,
            "detail": detail,
        }
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (id, at, kind, actor, service, subject, action, evidence, detail, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["id"],
                    event["at"],
                    kind,
                    actor,
                    service,
                    subject,
                    action,
                    evidence,
                    detail,
                    json.dumps(event, sort_keys=True),
                ),
            )
        return event

    def list_audit(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM audit_events ORDER BY at DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def append_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = dict(payload)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO domain_events (
                    event_id,
                    occurred_at,
                    event_type,
                    tenant_id,
                    organization_id,
                    project_id,
                    workflow_id,
                    actor_type,
                    actor_id,
                    correlation_id,
                    causation_id,
                    metadata_json,
                    data_json,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["occurred_at"],
                    event["event_type"],
                    event["tenant_id"],
                    event["organization_id"],
                    event.get("project_id"),
                    event.get("workflow_id"),
                    event["actor"]["type"],
                    event["actor"]["id"],
                    event["correlation_id"],
                    event["causation_id"],
                    json.dumps(event.get("metadata") or {}, sort_keys=True),
                    json.dumps(event.get("data") or {}, sort_keys=True),
                    json.dumps(event, sort_keys=True),
                ),
            )
        return event

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM domain_events ORDER BY occurred_at DESC, event_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]


class NovaCodeProPlatform:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository

    def service_registry(self) -> list[dict[str, Any]]:
        return self.repository.list("service")

    def tenants(self) -> list[dict[str, Any]]:
        return self.repository.list("tenant")

    def projects(self) -> list[dict[str, Any]]:
        return self.repository.list("project")

    def collaboration_threads(self) -> list[dict[str, Any]]:
        return self.repository.list("collaboration_thread")

    def knowledge_graph(self) -> list[dict[str, Any]]:
        return self.repository.list("knowledge_node")

    def integrations(self) -> list[dict[str, Any]]:
        return self.repository.list("integration")

    def marketplace(self) -> dict[str, Any]:
        return {
            "agents": self.repository.list("marketplace_item"),
            "developer_surfaces": self.repository.list("developer_surface"),
        }

    def workflows(self) -> list[dict[str, Any]]:
        return self.repository.list("workflow")

    def releases(self) -> list[dict[str, Any]]:
        return self.repository.list("release")

    def artifacts(self) -> list[dict[str, Any]]:
        return self.repository.list("artifact")

    def solutions(self) -> list[dict[str, Any]]:
        return self.repository.list("solution")

    def get_solution(self, solution_id: str) -> dict[str, Any] | None:
        return self.repository.get("solution", solution_id)

    def agent_executions(self) -> list[dict[str, Any]]:
        return self.repository.list("agent_execution")

    def get_agent_execution(self, execution_id: str) -> dict[str, Any] | None:
        return self.repository.get("agent_execution", execution_id)

    def approvals(self) -> list[dict[str, Any]]:
        return self.repository.list("approval")

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        return self.repository.get("approval", approval_id)

    def deployments(self) -> list[dict[str, Any]]:
        return self.repository.list("deployment")

    def get_deployment(self, deployment_id: str) -> dict[str, Any] | None:
        return self.repository.get("deployment", deployment_id)

    def digital_twins(self) -> list[dict[str, Any]]:
        return self.repository.list("digital_twin")

    def get_digital_twin(self, twin_id: str) -> dict[str, Any] | None:
        return self.repository.get("digital_twin", twin_id)

    def events(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_events(limit=limit)

    def audit(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_audit(limit=limit)

    def status(self) -> dict[str, Any]:
        services = self.service_registry()
        tenants = self.tenants()
        projects = self.projects()
        workflows = self.workflows()
        releases = self.releases()
        artifacts = self.artifacts()
        solutions = self.solutions()
        agents = self.agent_executions()
        approvals = self.approvals()
        deployments = self.deployments()
        twins = self.digital_twins()
        threads = self.collaboration_threads()
        integrations = self.integrations()
        return {
            "service": "novacodepro-platform",
            "status": "operational",
            "service_count": len(services),
            "tenant_count": len(tenants),
            "project_count": len(projects),
            "workflow_count": len(workflows),
            "release_count": len(releases),
            "artifact_count": len(artifacts),
            "solution_count": len(solutions),
            "agent_execution_count": len(agents),
            "approval_count": len(approvals),
            "deployment_count": len(deployments),
            "digital_twin_count": len(twins),
            "thread_count": len(threads),
            "integration_count": len(integrations),
            "connected_integration_count": sum(1 for item in integrations if item.get("status") == "connected"),
            "audit_event_count": len(self.audit(limit=500)),
            "domain_event_count": len(self.events(limit=500)),
            "marketplace_count": len(self.marketplace()["agents"]),
            "automation_ready": True,
            "distributed_services": [
                "Gateway Service",
                "NovaID Service",
                "Workflow Service",
                "Agent Orchestrator",
                "Artifact Service",
                "Audit Service",
                "Policy Engine",
                "Notification Service",
                "Marketplace Service",
                "Search Service",
                "Deployment Service",
                "Billing Service",
                "Licensing Service",
                "Observability Service",
            ],
            "service_registry": services,
        }

    def admin_summary(self) -> dict[str, Any]:
        status = self.status()
        workflows = self.workflows()
        releases = self.releases()
        deployments = self.deployments()
        approvals = self.approvals()
        service_registry = list(status.get("service_registry") or [])

        def _count(items: list[dict[str, Any]], key: str, value: str) -> int:
            return sum(1 for item in items if str(item.get(key) or "").lower() == value)

        service_health = {
            "healthy": _count(service_registry, "status", "healthy"),
            "degraded": _count(service_registry, "status", "degraded"),
            "unhealthy": _count(service_registry, "status", "unhealthy"),
        }
        workflow_statuses = {
            "active": _count(workflows, "status", "active"),
            "waiting-approval": _count(workflows, "status", "waiting-approval"),
            "paused": _count(workflows, "status", "paused"),
            "rejected": _count(workflows, "status", "rejected"),
            "completed": _count(workflows, "status", "completed"),
        }
        release_statuses = {
            "active": _count(releases, "status", "active"),
            "completed": _count(releases, "status", "completed"),
            "failed": _count(releases, "status", "failed"),
        }
        deployment_statuses = {
            "healthy": _count(deployments, "health", "green") + _count(deployments, "status", "healthy"),
            "degraded": _count(deployments, "health", "amber"),
            "failed": _count(deployments, "health", "red") + _count(deployments, "status", "failed"),
        }
        pending_approvals = [approval for approval in approvals if str(approval.get("status") or "").upper() == "PENDING"]
        ready_release_queue = [release for release in releases if str(release.get("status") or "").lower() != "completed"]
        platform_health = "healthy"
        if service_health["degraded"] or service_health["unhealthy"] or deployment_statuses["failed"]:
            platform_health = "attention"
        return {
            **status,
            "platform_health": platform_health,
            "service_health": service_health,
            "workflow_statuses": workflow_statuses,
            "release_statuses": release_statuses,
            "deployment_statuses": deployment_statuses,
            "pending_approval_count": len(pending_approvals),
            "ready_release_queue_count": len(ready_release_queue),
            "pending_approvals": pending_approvals[:5],
            "ready_release_queue": ready_release_queue[:5],
            "governance_queue": [
                "Security review",
                "Compliance review",
                "Release approval",
                "Policy review",
            ],
            "administration_areas": [
                "Identity & Access",
                "Organizations",
                "Tenants",
                "Projects",
                "Licenses",
                "Marketplace",
                "Users",
                "Roles",
                "Permissions",
                "Infrastructure",
                "Kubernetes",
                "Storage",
                "Databases",
                "Networking",
                "Release Center",
                "Deployment Center",
                "Artifact Repository",
                "Knowledge Graph",
                "Digital Twin",
                "Audit",
                "Compliance",
                "Security",
                "Risk",
                "Policy",
                "Certificates",
                "Evidence",
                "Approvals",
                "Metrics",
                "Logs",
                "Tracing",
                "Alerts",
                "Health",
                "Cost",
                "Branding",
                "Notifications",
                "SSO",
                "Backups",
                "Maintenance",
            ],
        }

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        project = {
            "id": _new_id("project"),
            "name": str(payload["name"]),
            "tenant_id": str(payload.get("tenant_id") or self.tenants()[0]["id"]),
            "status": str(payload.get("status") or "Discovery"),
            "owner": str(payload.get("owner") or "NovaCodePro"),
            "solution": str(payload.get("solution") or "Generated solution"),
            "region": str(payload.get("region") or "Australia"),
            "budget": str(payload.get("budget") or "$0"),
            "metadata": dict(payload.get("metadata") or {}),
        }
        self.repository.upsert("project", project)
        self.repository.append_audit(
            kind="project",
            actor="NovaID",
            service="Project Service",
            subject=project["name"],
            action="project.created",
            evidence=project["solution"],
            detail="Project created through the governed NovaCodePro platform.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="project.created",
                actor_type="user",
                actor_id="NovaID",
                tenant_id=project["tenant_id"],
                organization_id=project["tenant_id"],
                project_id=project["id"],
                workflow_id=None,
                correlation_id=project["id"],
                causation_id=project["id"],
                data={"project_id": project["id"], "name": project["name"], "solution": project["solution"]},
            )
        )
        return project

    def create_solution(self, payload: dict[str, Any]) -> dict[str, Any]:
        workflow = self.create_workflow(
            {
                "title": payload["title"],
                "request": payload["request"],
                "tenant_id": payload.get("tenant_id"),
                "project_id": payload.get("project_id"),
                "template_id": payload.get("template_id") or "solution-factory",
                "domain": payload.get("domain") or "general",
                "region": payload.get("region") or "Australia",
                "compliance": payload.get("compliance") or "enterprise",
                "surfaces": list(payload.get("surfaces") or []),
            }
        )
        solution = {
            "id": _new_id("solution"),
            "tenant_id": workflow["tenant_id"],
            "project_id": workflow["project_id"],
            "workflow_id": workflow["id"],
            "title": workflow["title"],
            "request": workflow["request"],
            "domain": workflow["domain"],
            "region": workflow["region"],
            "compliance": workflow["compliance"],
            "status": "solution_factory_running",
            "version": str(payload.get("version") or "2027.1.0"),
            "surfaces": workflow.get("surfaces") or [],
            "package_manifest": {
                "solution_id": None,
                "workflow_id": workflow["id"],
                "tenant_id": workflow["tenant_id"],
                "version": str(payload.get("version") or "2027.1.0"),
                "status": "draft",
            },
            "artifacts": [],
            "approvals": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        solution["package_manifest"]["solution_id"] = solution["id"]
        self.repository.upsert("solution", solution)
        self.repository.append_event(
            _event_envelope(
                event_type="solution.created",
                actor_type="service",
                actor_id="solution-factory",
                tenant_id=solution["tenant_id"],
                organization_id=solution["tenant_id"],
                project_id=solution["project_id"],
                workflow_id=solution["workflow_id"],
                correlation_id=solution["workflow_id"],
                causation_id=workflow["id"],
                data={"solution_id": solution["id"], "title": solution["title"], "status": solution["status"]},
            )
        )
        self.repository.append_audit(
            kind="solution",
            actor="NovaID",
            service="Solution Factory",
            subject=solution["title"],
            action="solution.created",
            evidence=solution["workflow_id"],
            detail="Solution package created and linked to a durable workflow.",
        )
        return solution

    def create_agent_execution(self, payload: dict[str, Any]) -> dict[str, Any]:
        workflow = self.repository.get("workflow", str(payload.get("workflow_id") or ""))
        project_id = str(payload.get("project_id") or (workflow.get("project_id") if workflow else self.projects()[0]["id"]))
        tenant_id = str(payload.get("tenant_id") or (workflow.get("tenant_id") if workflow else self.tenants()[0]["id"]))
        workflow_id = str(payload.get("workflow_id") or (workflow.get("id") if workflow else ""))
        execution = {
            "id": _new_id("agent-execution"),
            "agent_id": str(payload["agent_id"]),
            "version": str(payload.get("version") or "2027.1.0"),
            "category": str(payload.get("category") or "general"),
            "tenant_id": tenant_id,
            "project_id": project_id,
            "workflow_id": workflow_id,
            "stage_id": str(payload.get("stage_id") or "intake"),
            "status": "completed",
            "input": dict(payload.get("input") or {}),
            "output": dict(payload.get("output") or {"result": "completed"}),
            "allowed_tools": list(payload.get("allowed_tools") or []),
            "forbidden_tools": list(payload.get("forbidden_tools") or []),
            "timeout_seconds": int(payload.get("timeout_seconds") or 900),
            "maximum_cost": float(payload.get("maximum_cost") or 0.0),
            "approval_policy": str(payload.get("approval_policy") or "standard"),
            "evidence": list(payload.get("evidence") or []),
            "logs": [
                {
                    "at": _now(),
                    "message": "Agent execution completed through the orchestrated backend.",
                }
            ],
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("agent_execution", execution)
        self.repository.append_event(
            _event_envelope(
                event_type="agent.execution.completed",
                actor_type="service",
                actor_id=execution["agent_id"],
                tenant_id=execution["tenant_id"],
                organization_id=execution["tenant_id"],
                project_id=execution["project_id"],
                workflow_id=execution["workflow_id"],
                correlation_id=execution["workflow_id"],
                causation_id=execution["id"],
                data={
                    "agent_execution_id": execution["id"],
                    "stage_id": execution["stage_id"],
                    "status": execution["status"],
                },
            )
        )
        self.repository.append_audit(
            kind="agent_execution",
            actor="NovaID",
            service="Agent Orchestrator",
            subject=execution["agent_id"],
            action="agent.execution.completed",
            evidence=execution["stage_id"],
            detail="Specialist agent execution completed in the durable backend runtime.",
        )
        return execution

    def create_approval(self, payload: dict[str, Any]) -> dict[str, Any]:
        workflow = self.repository.get("workflow", str(payload.get("workflow_id") or ""))
        tenant_id = str(workflow.get("tenant_id") if workflow else self.tenants()[0]["id"])
        approval = {
            "id": _new_id("approval"),
            "gate_type": str(payload["gate_type"]),
            "workflow_id": str(payload.get("workflow_id") or ""),
            "release_id": str(payload.get("release_id") or ""),
            "status": "PENDING",
            "requested_by": str(payload.get("requested_by") or "NovaID"),
            "approved_by": "",
            "requested_at": _now(),
            "decided_at": "",
            "decision": "",
            "conditions": list(payload.get("conditions") or []),
            "evidence_ids": list(payload.get("evidence_ids") or []),
            "signature": "",
            "audit_event_id": "",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("approval", approval)
        self.repository.append_event(
            _event_envelope(
                event_type="approval.requested",
                actor_type="user",
                actor_id=approval["requested_by"],
                tenant_id=tenant_id,
                organization_id=tenant_id,
                project_id=None,
                workflow_id=approval["workflow_id"] or None,
                correlation_id=approval["workflow_id"] or approval["id"],
                causation_id=approval["id"],
                data={"approval_id": approval["id"], "gate_type": approval["gate_type"]},
            )
        )
        self.repository.append_audit(
            kind="approval",
            actor=approval["requested_by"],
            service="Approval Service",
            subject=approval["gate_type"],
            action="approval.requested",
            evidence="; ".join(approval["evidence_ids"]),
            detail="Protected approval request created for a governed gate.",
        )
        return approval

    def decide_approval(self, approval_id: str, decision: str, actor: str, note: str = "") -> dict[str, Any]:
        approval = self.repository.get("approval", approval_id)
        if approval is None:
            raise KeyError("approval_not_found")
        decision = decision.lower().strip()
        if decision not in {"approve", "reject"}:
            raise ValueError("unsupported_decision")
        approval["status"] = "APPROVED" if decision == "approve" else "REJECTED"
        approval["approved_by"] = actor
        approval["decided_at"] = _now()
        approval["decision"] = decision
        approval["signature"] = f"sig-{_new_id('approval')}"
        approval["audit_event_id"] = _new_id("audit")
        approval["updated_at"] = _now()
        approval.setdefault("notes", [])
        if note:
            approval["notes"] = [note, *approval["notes"]]
        self.repository.upsert("approval", approval)
        self.repository.append_event(
            _event_envelope(
                event_type=f"approval.{decision}ed",
                actor_type="user",
                actor_id=actor,
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=approval["workflow_id"] or None,
                correlation_id=approval["workflow_id"] or approval["id"],
                causation_id=approval["id"],
                data={"approval_id": approval["id"], "decision": approval["status"], "note": note},
            )
        )
        self.repository.append_audit(
            kind="approval",
            actor=actor,
            service="Approval Service",
            subject=approval["gate_type"],
            action=f"approval.{decision}",
            evidence=note or approval["status"],
            detail="Protected approval decision recorded in the durable backend.",
        )
        return approval

    def create_deployment(self, payload: dict[str, Any]) -> dict[str, Any]:
        workflow = self.repository.get("workflow", str(payload.get("workflow_id") or ""))
        tenant_id = str(workflow.get("tenant_id") if workflow else self.tenants()[0]["id"])
        deployment = {
            "id": _new_id("deployment"),
            "workflow_id": str(payload["workflow_id"]),
            "release_id": str(payload["release_id"]),
            "environment": str(payload.get("environment") or "staging"),
            "region": str(payload.get("region") or "Australia"),
            "status": "provisioning",
            "health": "unknown",
            "version": str(payload.get("version") or "2027.1.0"),
            "metrics": dict(payload.get("metrics") or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("deployment", deployment)
        self.repository.append_event(
            _event_envelope(
                event_type="deployment.created",
                actor_type="service",
                actor_id="deployment-service",
                tenant_id=tenant_id,
                organization_id=tenant_id,
                project_id=None,
                workflow_id=deployment["workflow_id"],
                correlation_id=deployment["release_id"],
                causation_id=deployment["id"],
                data={"deployment_id": deployment["id"], "status": deployment["status"]},
            )
        )
        self.repository.append_audit(
            kind="deployment",
            actor="NovaID",
            service="Deployment Service",
            subject=deployment["release_id"],
            action="deployment.created",
            evidence=deployment["environment"],
            detail="Deployment prepared by the governed backend runtime.",
        )
        return deployment

    def transition_deployment(self, deployment_id: str, action: str, note: str = "", actor: str = "NovaID") -> dict[str, Any]:
        deployment = self.repository.get("deployment", deployment_id)
        if deployment is None:
            raise KeyError("deployment_not_found")
        workflow = self.repository.get("workflow", str(deployment.get("workflow_id") or ""))
        tenant_id = str(workflow.get("tenant_id") if workflow else self.tenants()[0]["id"])
        action = action.lower().strip()
        if action not in {"start", "pause", "resume", "rollback", "verify", "complete", "fail"}:
            raise ValueError("unsupported_action")
        if action == "start":
            deployment["status"] = "running"
            deployment["health"] = "green"
        elif action == "pause":
            deployment["status"] = "paused"
        elif action == "resume":
            deployment["status"] = "running"
        elif action == "rollback":
            deployment["status"] = "rolling_back"
            deployment["health"] = "amber"
        elif action == "verify":
            deployment["status"] = "verifying"
        elif action == "complete":
            deployment["status"] = "healthy"
            deployment["health"] = "green"
        elif action == "fail":
            deployment["status"] = "failed"
            deployment["health"] = "red"
        deployment["updated_at"] = _now()
        self.repository.upsert("deployment", deployment)
        self.update_digital_twin_from_deployment(deployment)
        self.repository.append_event(
            _event_envelope(
                event_type=f"deployment.{action}",
                actor_type="user",
                actor_id=actor,
                tenant_id=tenant_id,
                organization_id=tenant_id,
                project_id=None,
                workflow_id=deployment["workflow_id"],
                correlation_id=deployment["release_id"],
                causation_id=deployment["id"],
                data={"deployment_id": deployment["id"], "status": deployment["status"], "note": note},
            )
        )
        self.repository.append_audit(
            kind="deployment",
            actor=actor,
            service="Deployment Service",
            subject=deployment["release_id"],
            action=f"deployment.{action}",
            evidence=note or deployment["status"],
            detail="Deployment lifecycle advanced in the durable backend.",
        )
        return deployment

    def get_or_create_digital_twin(self, twin_id: str | None = None) -> dict[str, Any]:
        target_id = twin_id or "twin-novacodepro"
        twin = self.repository.get("digital_twin", target_id)
        if twin is not None:
            return twin
        twin = {
            "id": target_id,
            "name": "NovaCodePro Twin",
            "kind": "solution",
            "status": "healthy",
            "region": "Australia",
            "children": [],
            "health": {
                "availability": 1.0,
                "latency_p95_ms": 120,
                "error_rate": 0.0,
            },
            "topology": {"services": [service["name"] for service in self.service_registry()]},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("digital_twin", twin)
        return twin

    def digital_twin_health(self, twin_id: str | None = None) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        return {
            "id": twin["id"],
            "status": twin["status"],
            "health": twin.get("health") or {},
            "region": twin.get("region"),
            "updated_at": twin.get("updated_at"),
        }

    def digital_twin_topology(self, twin_id: str | None = None) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        return {
            "id": twin["id"],
            "name": twin["name"],
            "kind": twin["kind"],
            "children": list(twin.get("children") or []),
            "services": list((twin.get("topology") or {}).get("services") or []),
        }

    def update_digital_twin_from_deployment(self, deployment: dict[str, Any]) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin()
        twins = list(twin.get("children") or [])
        if deployment["id"] not in twins:
            twins.append(deployment["id"])
        twin["children"] = twins
        twin["status"] = "healthy" if deployment.get("health") in {"green", "healthy"} else "degraded"
        twin["health"] = {
            "availability": deployment.get("metrics", {}).get("availability", 1.0),
            "latency_p95_ms": deployment.get("metrics", {}).get("latency_p95_ms", 120),
            "error_rate": deployment.get("metrics", {}).get("error_rate", 0.0),
        }
        twin["updated_at"] = _now()
        self.repository.upsert("digital_twin", twin)
        self.repository.append_event(
            _event_envelope(
                event_type="digital_twin.updated",
                actor_type="service",
                actor_id="digital-twin-engine",
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=deployment["workflow_id"],
                correlation_id=deployment["release_id"],
                causation_id=deployment["id"],
                data={"twin_id": twin["id"], "deployment_id": deployment["id"], "health": twin["health"]},
            )
        )
        return twin

    def create_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        created_at = _now()
        workflow = {
            "id": _new_id("workflow"),
            "tenant_id": str(payload.get("tenant_id") or self.tenants()[0]["id"]),
            "project_id": str(payload.get("project_id") or self.projects()[0]["id"]),
            "title": str(payload["title"]),
            "request": str(payload["request"]),
            "template_id": str(payload.get("template_id") or "custom"),
            "domain": str(payload.get("domain") or "general"),
            "region": str(payload.get("region") or "Australia"),
            "compliance": str(payload.get("compliance") or "enterprise"),
            "surfaces": list(payload.get("surfaces") or []),
            "stage_index": 0,
            "status": "active",
            "retries": 0,
            "approvals": [],
            "artifacts": [],
            "history": [
                {
                    "action": "created",
                    "actor": "NovaID",
                    "service": "Intent Engine",
                    "at": created_at,
                    "detail": "Workflow created from business intent.",
                }
            ],
            "stages": _stage_view(WORKFLOW_BLUEPRINT, 0, "active"),
            "created_at": created_at,
            "updated_at": created_at,
        }
        self.repository.upsert("workflow", workflow)
        self.repository.append_audit(
            kind="workflow",
            actor="NovaID",
            service="Solution Orchestrator",
            subject=workflow["title"],
            action="workflow.created",
            evidence=workflow["request"],
            detail="Business request entered the distributed workflow engine.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="workflow.created",
                actor_type="user",
                actor_id="NovaID",
                tenant_id=workflow["tenant_id"],
                organization_id=workflow["tenant_id"],
                project_id=workflow["project_id"],
                workflow_id=workflow["id"],
                correlation_id=workflow["id"],
                causation_id=workflow["id"],
                data={"workflow_id": workflow["id"], "title": workflow["title"], "stage_index": workflow["stage_index"]},
            )
        )
        return workflow

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        return self.repository.get("workflow", workflow_id)

    def transition_workflow(self, workflow_id: str, action: str, note: str = "", actor: str = "NovaID") -> dict[str, Any]:
        workflow = self.repository.get("workflow", workflow_id)
        if workflow is None:
            raise KeyError("workflow_not_found")
        transitioned = self._transition_flow(
            flow=workflow,
            flow_kind="workflow",
            blueprint=WORKFLOW_BLUEPRINT,
            action=action,
            note=note,
            actor=actor,
            service="Workflow Service",
        )
        self.repository.upsert("workflow", transitioned)
        self.repository.append_audit(
            kind="workflow",
            actor=actor,
            service="Workflow Service",
            subject=transitioned["title"],
            action=f"workflow.{action}",
            evidence=note or transitioned["current_stage"]["label"],
            detail=f"Workflow transition executed: {action}.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type=f"workflow.{action}",
                actor_type="user",
                actor_id=actor,
                tenant_id=transitioned["tenant_id"],
                organization_id=transitioned["tenant_id"],
                project_id=transitioned["project_id"],
                workflow_id=transitioned["id"],
                correlation_id=transitioned["id"],
                causation_id=transitioned["id"],
                data={
                    "workflow_id": transitioned["id"],
                    "stage_index": transitioned["stage_index"],
                    "status": transitioned["status"],
                    "action": action,
                },
            )
        )
        return transitioned

    def create_artifact(self, payload: dict[str, Any]) -> dict[str, Any]:
        artifact = {
            "id": _new_id("artifact"),
            "workflow_id": str(payload["workflow_id"]),
            "kind": str(payload["kind"]),
            "title": str(payload["title"]),
            "uri": str(payload.get("uri") or ""),
            "version": str(payload.get("version") or "v1"),
            "checksum": str(payload.get("checksum") or ""),
            "metadata": dict(payload.get("metadata") or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("artifact", artifact)
        self.repository.append_audit(
            kind="artifact",
            actor="NovaCodePro",
            service="Artifact Service",
            subject=artifact["title"],
            action="artifact.created",
            evidence=artifact["kind"],
            detail="Artifact stored in the governed repository.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="artifact.created",
                actor_type="service",
                actor_id="artifact-service",
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=artifact["workflow_id"],
                correlation_id=artifact["workflow_id"],
                causation_id=artifact["id"],
                data={"artifact_id": artifact["id"], "kind": artifact["kind"], "title": artifact["title"]},
            )
        )
        return artifact

    def create_thread(self, payload: dict[str, Any]) -> dict[str, Any]:
        thread = {
            "id": _new_id("thread"),
            "tenant_id": str(payload.get("tenant_id") or self.tenants()[0]["id"]),
            "project_id": str(payload.get("project_id") or self.projects()[0]["id"]),
            "scope": str(payload["scope"]),
            "participants": list(payload.get("participants") or []),
            "state": "active",
            "messages": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("collaboration_thread", thread)
        self.repository.append_audit(
            kind="collaboration",
            actor="NovaID",
            service="Collaboration Service",
            subject=thread["scope"],
            action="thread.created",
            evidence=", ".join(thread["participants"]),
            detail="Thread created for a governed workspace discussion.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="collaboration.thread.created",
                actor_type="user",
                actor_id="NovaID",
                tenant_id=thread["tenant_id"],
                organization_id=thread["tenant_id"],
                project_id=thread["project_id"],
                workflow_id=None,
                correlation_id=thread["id"],
                causation_id=thread["id"],
                data={"thread_id": thread["id"], "scope": thread["scope"]},
            )
        )
        return thread

    def post_comment(self, thread_id: str, body: str, author: str = "NovaCodePro") -> dict[str, Any]:
        thread = self.repository.get("collaboration_thread", thread_id)
        if thread is None:
            raise KeyError("thread_not_found")
        message = {
            "id": _new_id("message"),
            "author": author,
            "body": body,
            "at": _now(),
        }
        thread.setdefault("messages", [])
        thread["messages"] = [message, *thread["messages"]]
        thread["state"] = "active"
        thread["updated_at"] = _now()
        self.repository.upsert("collaboration_thread", thread)
        self.repository.append_audit(
            kind="collaboration",
            actor=author,
            service="Collaboration Service",
            subject=thread["scope"],
            action="comment.posted",
            evidence=body,
            detail="Collaborative comment appended to the active thread.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="collaboration.message.posted",
                actor_type="user",
                actor_id=author,
                tenant_id=thread["tenant_id"],
                organization_id=thread["tenant_id"],
                project_id=thread["project_id"],
                workflow_id=None,
                correlation_id=thread["id"],
                causation_id=message["id"],
                data={"thread_id": thread["id"], "message_id": message["id"], "body": body},
            )
        )
        return thread

    def focus_node(self, node_id: str) -> dict[str, Any]:
        node = self.repository.get("knowledge_node", node_id)
        if node is None:
            raise KeyError("knowledge_node_not_found")
        self.repository.append_audit(
            kind="knowledge_graph",
            actor="NovaID",
            service="Knowledge Graph Service",
            subject=node["label"],
            action="knowledge.focused",
            evidence=", ".join(node.get("links") or []),
            detail="Knowledge graph node inspected from the distributed platform.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="knowledge.node.focused",
                actor_type="user",
                actor_id="NovaID",
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=None,
                correlation_id=node_id,
                causation_id=node_id,
                data={"node_id": node_id, "label": node["label"]},
            )
        )
        return node

    def link_nodes(self, source_id: str, target_id: str) -> dict[str, Any]:
        source = self.repository.get("knowledge_node", source_id)
        target = self.repository.get("knowledge_node", target_id)
        if source is None or target is None:
            raise KeyError("knowledge_node_not_found")
        links = list(source.get("links") or [])
        if target_id not in links:
            links.append(target_id)
            source["links"] = links
            source["updated_at"] = _now()
            self.repository.upsert("knowledge_node", source)
        self.repository.append_audit(
            kind="knowledge_graph",
            actor="NovaID",
            service="Knowledge Graph Service",
            subject=source["label"],
            action="knowledge.linked",
            evidence=f"{source_id}->{target_id}",
            detail="Knowledge graph traceability updated.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="knowledge.linked",
                actor_type="user",
                actor_id="NovaID",
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=None,
                correlation_id=source_id,
                causation_id=target_id,
                data={"source_id": source_id, "target_id": target_id},
            )
        )
        return {"source": source, "target": target}

    def connect_integration(self, integration_id: str) -> dict[str, Any]:
        integration = self.repository.get("integration", integration_id)
        if integration is None:
            raise KeyError("integration_not_found")
        integration["status"] = "connected"
        integration["connected_at"] = _now()
        integration["updated_at"] = _now()
        self.repository.upsert("integration", integration)
        self.repository.append_audit(
            kind="integration",
            actor="NovaID",
            service="Integration Hub",
            subject=integration["name"],
            action="integration.connected",
            evidence=integration.get("purpose", ""),
            detail="Integration connected through governed platform controls.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="integration.connected",
                actor_type="user",
                actor_id="NovaID",
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=None,
                correlation_id=integration_id,
                causation_id=integration_id,
                data={"integration_id": integration_id, "status": integration["status"]},
            )
        )
        return integration

    def create_release(self, payload: dict[str, Any]) -> dict[str, Any]:
        release = {
            "id": _new_id("release"),
            "workflow_id": str(payload["workflow_id"]),
            "title": str(payload.get("title") or "NovaCodePro release"),
            "channel": str(payload.get("channel") or "pilot"),
            "target": str(payload.get("target") or "staging"),
            "notes": str(payload.get("notes") or ""),
            "stage_index": 0,
            "status": "active",
            "stages": _stage_view(RELEASE_BLUEPRINT, 0, "active"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("release", release)
        self.repository.append_audit(
            kind="release",
            actor="NovaID",
            service="Release Factory",
            subject=release["title"],
            action="release.created",
            evidence=release["workflow_id"],
            detail="Release bundle created from the governed workflow.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="release.created",
                actor_type="user",
                actor_id="NovaID",
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=release["workflow_id"],
                correlation_id=release["id"],
                causation_id=release["id"],
                data={"release_id": release["id"], "workflow_id": release["workflow_id"], "status": release["status"]},
            )
        )
        return release

    def transition_release(self, release_id: str, action: str, note: str = "", actor: str = "NovaID") -> dict[str, Any]:
        release = self.repository.get("release", release_id)
        if release is None:
            raise KeyError("release_not_found")
        transitioned = self._transition_flow(
            flow=release,
            flow_kind="release",
            blueprint=RELEASE_BLUEPRINT,
            action=action,
            note=note,
            actor=actor,
            service="Release Factory",
        )
        self.repository.upsert("release", transitioned)
        self.repository.append_audit(
            kind="release",
            actor=actor,
            service="Release Factory",
            subject=transitioned["title"],
            action=f"release.{action}",
            evidence=note or transitioned["current_stage"]["label"],
            detail=f"Release transition executed: {action}.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type=f"release.{action}",
                actor_type="user",
                actor_id=actor,
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=transitioned["workflow_id"],
                correlation_id=transitioned["id"],
                causation_id=transitioned["id"],
                data={"release_id": transitioned["id"], "stage_index": transitioned["stage_index"], "status": transitioned["status"]},
            )
        )
        return transitioned

    def run_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        command = command.strip()
        normalized = command.lower()
        outcome: dict[str, Any] = {"command": command, "status": "recorded"}
        if any(token in normalized for token in ("create", "generate")) and any(
            token in normalized for token in ("solution", "platform", "workflow", "app", "portal")
        ):
            solution = self.create_solution(
                {
                    "title": command,
                    "request": command,
                    "tenant_id": (context or {}).get("tenant_id"),
                    "project_id": (context or {}).get("project_id"),
                    "domain": (context or {}).get("domain") or "general",
                    "region": (context or {}).get("region") or "Australia",
                    "compliance": (context or {}).get("compliance") or "enterprise",
                    "surfaces": list((context or {}).get("surfaces") or []),
                    "template_id": (context or {}).get("template_id") or "command",
                    "version": (context or {}).get("version") or "2027.1.0",
                }
            )
            outcome = {"command": command, "status": "solution_created", "solution": solution, "workflow_id": solution["workflow_id"]}
        elif "deploy" in normalized or "release" in normalized:
            workflows = self.workflows()
            workflow_id = (context or {}).get("workflow_id") or (workflows[0]["id"] if workflows else None)
            if workflow_id:
                release = self.create_release(
                    {
                        "workflow_id": workflow_id,
                        "title": command,
                        "channel": (context or {}).get("channel") or "pilot",
                        "target": (context or {}).get("target") or "staging",
                        "notes": command,
                    }
                )
                outcome = {"command": command, "status": "release_created", "release": release}
        self.repository.append_audit(
            kind="command",
            actor="NovaID",
            service="AI Command Center",
            subject=command,
            action="command.executed",
            evidence=json.dumps(outcome, sort_keys=True),
            detail="Natural language command routed through the distributed backend.",
        )
        return outcome

    def _transition_flow(
        self,
        *,
        flow: dict[str, Any],
        flow_kind: str,
        blueprint: list[dict[str, str]],
        action: str,
        note: str,
        actor: str,
        service: str,
    ) -> dict[str, Any]:
        stage_index = int(flow.get("stage_index", 0))
        current_stage = blueprint[stage_index]
        if action == "pause":
            flow["status"] = "paused"
        elif action == "resume":
            flow["status"] = "active"
        elif action == "retry":
            flow["retries"] = int(flow.get("retries", 0)) + 1
            flow["status"] = "active"
        elif action == "rollback":
            stage_index = max(stage_index - 1, 0)
            flow["status"] = "active"
        elif action == "reject":
            flow["status"] = "rejected"
        elif action == "approve":
            if current_stage["kind"] != "human":
                raise ValueError("approval gate required")
            approvals = list(flow.get("approvals") or [])
            approvals.append(
                {
                    "id": _new_id("approval"),
                    "gate": current_stage["label"],
                    "by": actor,
                    "at": _now(),
                    "evidence": note or "approved",
                }
            )
            flow["approvals"] = approvals
            stage_index = min(stage_index + 1, len(blueprint) - 1)
            flow["status"] = "waiting-approval" if blueprint[stage_index]["kind"] == "human" else "active"
        elif action == "advance":
            if current_stage["kind"] == "human":
                flow["status"] = "waiting-approval"
            else:
                stage_index = min(stage_index + 1, len(blueprint) - 1)
                flow["status"] = "waiting-approval" if blueprint[stage_index]["kind"] == "human" else "active"
        elif action == "replay":
            return flow
        else:
            raise ValueError("unsupported_action")

        flow["stage_index"] = stage_index
        flow["current_stage"] = blueprint[stage_index]
        flow["stages"] = _stage_view(blueprint, stage_index, str(flow.get("status") or "active"))
        flow["updated_at"] = _now()
        history = list(flow.get("history") or [])
        history.append(
            {
                "action": action,
                "actor": actor,
                "service": service,
                "at": _now(),
                "detail": note or f"{flow_kind} transition executed",
            }
        )
        flow["history"] = history
        return flow


def get_novacodepro_platform(db_path: str | Path | None = None) -> NovaCodeProPlatform:
    path = Path(db_path or Path.cwd() / "var" / "novacodepro-platform.sqlite3")
    return NovaCodeProPlatform(NovaCodeProRepository(path))
