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


class NovaCodeProPlatform:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository

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

    def audit(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_audit(limit=limit)

    def status(self) -> dict[str, Any]:
        tenants = self.tenants()
        projects = self.projects()
        workflows = self.workflows()
        releases = self.releases()
        artifacts = self.artifacts()
        threads = self.collaboration_threads()
        integrations = self.integrations()
        return {
            "service": "novacodepro-platform",
            "status": "operational",
            "tenant_count": len(tenants),
            "project_count": len(projects),
            "workflow_count": len(workflows),
            "release_count": len(releases),
            "artifact_count": len(artifacts),
            "thread_count": len(threads),
            "integration_count": len(integrations),
            "connected_integration_count": sum(1 for item in integrations if item.get("status") == "connected"),
            "audit_event_count": len(self.audit(limit=500)),
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
        return project

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
        return transitioned

    def run_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        command = command.strip()
        normalized = command.lower()
        outcome: dict[str, Any] = {"command": command, "status": "recorded"}
        if any(token in normalized for token in ("create", "generate")) and any(
            token in normalized for token in ("solution", "platform", "workflow", "app", "portal")
        ):
            workflow = self.create_workflow(
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
                }
            )
            outcome = {"command": command, "status": "workflow_created", "workflow": workflow}
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
