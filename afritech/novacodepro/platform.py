from __future__ import annotations

import json
import hashlib
import hmac
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from afritech.novacodepro.enterprise_framework import (
    build_enterprise_ai_architecture,
    build_enterprise_architecture_framework,
    build_enterprise_capability_model,
    build_enterprise_data_architecture,
    build_enterprise_digital_twin_model,
    build_enterprise_governance_model,
    build_enterprise_meta_model,
    build_enterprise_operating_model,
    build_enterprise_plane_model,
    build_enterprise_resilience_model,
    build_enterprise_technology_model,
    build_nera_manifest,
)
from afritech.novacodepro.enterprise_os import (
    build_approval_object,
    build_event_record,
    build_knowledge_entry,
    build_solution_package,
    default_agent_registry,
    knowledge_projection,
    replay_events,
)
from afritech.novacodepro.eros import (
    apply_observation,
    build_eros_manifest,
    build_recovery_plan,
    build_twin_record,
    build_twin_relationship,
    derive_resilience_scores,
    execute_recovery,
    simulate_twin,
)
from afritech.novacodepro.operating_fabric import EnterpriseExecutionContext, EnterpriseOperatingFabric, normalize_role
from afritech.novacodepro.production_readiness import validate_production_dependencies
from afritech.novacodepro.ux_operating_system import (
    assess_ux_release_readiness,
    build_ux_artifact_record,
    build_ux_evidence_package,
    build_uxos_service_record,
    sign_ux_record,
    ux_operating_system_summary,
    uxos_operational_completion_matrix,
    validate_ux_state_transition,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _default_database_url() -> str | None:
    for env_var in (
        "NOVACODEPRO_DATABASE_URL",
        "NOVACODEPRO_GATEWAY_DATABASE_URL",
        "NOVACODEPRO_SOLUTION_DATABASE_URL",
        "NOVACODEPRO_WORKFLOW_DATABASE_URL",
        "NOVACODEPRO_APPROVAL_DATABASE_URL",
        "NOVACODEPRO_AGENT_DATABASE_URL",
        "NOVACODEPRO_EVIDENCE_DATABASE_URL",
        "NOVACODEPRO_RISK_DATABASE_URL",
        "NOVACODEPRO_POLICY_DATABASE_URL",
        "NOVACODEPRO_KNOWLEDGE_DATABASE_URL",
        "NOVACODEPRO_RELEASE_DATABASE_URL",
        "NOVACODEPRO_DEPLOYMENT_DATABASE_URL",
        "NOVACODEPRO_MARKETPLACE_DATABASE_URL",
        "NOVACODEPRO_OPERATIONS_DATABASE_URL",
        "NOVACODEPRO_EXECUTIVE_DATABASE_URL",
    ):
        value = os.environ.get(env_var)
        if value:
            return value
    return None


def _runtime_environment() -> str:
    for env_var in ("NOVACODEPRO_ENVIRONMENT", "AFRITECH_ENV", "ENVIRONMENT"):
        value = os.environ.get(env_var)
        if value:
            return value
    return "development"


def validate_database_runtime(database_url: str | None, environment: str | None = None) -> None:
    runtime = str(environment or _runtime_environment()).strip().lower()
    if runtime not in {"production", "prod"}:
        return
    if not database_url:
        raise RuntimeError("sqlite_not_allowed_in_production")
    if str(database_url).startswith("sqlite"):
        raise RuntimeError("sqlite_not_allowed_in_production")


def _split_sql_script(script: str) -> list[str]:
    statements: list[str] = []
    for raw_statement in script.split(";"):
        statement = raw_statement.strip()
        if not statement or statement.startswith("PRAGMA "):
            continue
        statements.append(f"{statement};")
    return statements


def _rewrite_sql_for_postgres(sql: str) -> str:
    rewritten = sql.strip()
    if rewritten.startswith("PRAGMA "):
        return ""
    if "?" in rewritten:
        rewritten = rewritten.replace("?", "%s")
    if re.match(r"INSERT\s+OR\s+REPLACE\s+INTO", rewritten, flags=re.IGNORECASE):
        raise RuntimeError("INSERT OR REPLACE statements are not supported in NovaCodePro production mode")
    return rewritten


class _PostgresCursorAdapter:
    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return list(self._cursor.fetchall())

    def __iter__(self):
        return iter(self._cursor)


class _PostgresConnectionAdapter:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, sql: str, params: Any = ()) -> _PostgresCursorAdapter:
        rewritten = _rewrite_sql_for_postgres(sql)
        if not rewritten:
            return _PostgresCursorAdapter(self._connection.cursor())
        cursor = self._connection.cursor()
        cursor.execute(rewritten, params)
        return _PostgresCursorAdapter(cursor)

    def executescript(self, script: str) -> None:
        for statement in _split_sql_script(script):
            self.execute(statement)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "_PostgresConnectionAdapter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


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
    {
        "id": "evidence-service",
        "name": "Evidence Service",
        "category": "governance",
        "status": "healthy",
        "api": "/api/v1/evidence/bundles",
    },
    {
        "id": "risk-service",
        "name": "Risk Service",
        "category": "governance",
        "status": "healthy",
        "api": "/api/v1/risks/evaluate",
    },
    {
        "id": "policy-service",
        "name": "Policy Service",
        "category": "governance",
        "status": "healthy",
        "api": "/api/v1/policies/evaluate",
    },
    {
        "id": "knowledge-graph-service",
        "name": "Knowledge Graph Service",
        "category": "knowledge",
        "status": "healthy",
        "api": "/api/v1/knowledge/query",
    },
    {
        "id": "operations-service",
        "name": "Operations Service",
        "category": "observability",
        "status": "healthy",
        "api": "/api/v1/operations/health",
    },
    {
        "id": "executive-intelligence-service",
        "name": "Executive Intelligence Service",
        "category": "leadership",
        "status": "healthy",
        "api": "/api/v1/executive/briefings",
    },
]

DEFAULT_POLICY_RULES: list[dict[str, Any]] = [
    {
        "id": "REL-PROD-001",
        "name": "Production Release",
        "scope": "production",
        "required_approvals": ["SECURITY", "RELEASE"],
        "quorum": 2,
        "timeout_hours": 48,
        "active": True,
        "description": "Production deployments require security and release approval, plus rollback evidence.",
    },
    {
        "id": "SEC-EXC-001",
        "name": "Security Exception",
        "scope": "security_exception",
        "required_approvals": ["SECURITY", "CISO"],
        "quorum": 2,
        "timeout_hours": 24,
        "active": True,
        "description": "Security exceptions require independent security authority.",
    },
]

DEFAULT_RISK_RECORDS: list[dict[str, Any]] = [
    {
        "id": "risk-production-release",
        "title": "Production payment-service release",
        "likelihood": "medium",
        "impact": "high",
        "exposure": "high",
        "score": 18,
        "classification": "HIGH",
        "owner": "security-team",
        "required_controls": [
            "security_approval",
            "release_approval",
            "canary_deployment",
            "automatic_rollback",
        ],
        "status": "open",
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    }
]

DEFAULT_EVIDENCE_BUNDLES: list[dict[str, Any]] = [
    {
        "id": "evidence-release-ride-platform",
        "tenant_id": "novatech",
        "workflow_id": "workflow-ride-platform",
        "actor": {"type": "user", "id": "platform-admin"},
        "action": "release.approved",
        "policy_id": "REL-PROD-001",
        "artifact_ids": ["evidence-threat-model", "evidence-sbom"],
        "hash": "sha256-demo-evidence",
        "signature": "signature-reference",
        "occurred_at": "2026-07-11T00:00:00+00:00",
        "verified": True,
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    }
]

DEFAULT_OPERATION_RECORDS: list[dict[str, Any]] = [
    {
        "id": "incident-platform-latency",
        "title": "Platform latency spike",
        "severity": "medium",
        "status": "open",
        "service": "NovaCodePro Gateway",
        "region": "Australia",
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    }
]

DEFAULT_EXECUTIVE_BRIEFINGS: list[dict[str, Any]] = [
    {
        "id": "briefing-q3-risk",
        "subject": "NovaCodePro strategic risks",
        "summary": "Delivery, security remediation, and region scaling remain the top cross-domain risks.",
        "recommendations": [
            "Increase staffing for release automation",
            "Complete security remediation backlog",
            "Stage regional expansion with explicit approvals",
        ],
        "scorecard": {
            "enterprise_health": 96,
            "trust_score": 94,
            "risk_score": 18,
            "compliance_score": 98,
            "delivery_score": 91,
        },
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    }
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

DEFAULT_AGENT_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "product-agent",
        "name": "Product Agent",
        "category": "product",
        "version": "2027.1.0",
        "status": "available",
        "allowed_tools": ["knowledge.query", "artifact.read", "artifact.write"],
        "forbidden_tools": ["production.deploy", "secret.export"],
        "created_at": "2026-07-11T00:00:00+00:00",
        "updated_at": "2026-07-11T00:00:00+00:00",
    },
    {
        "id": "architecture-agent",
        "name": "Architecture Agent",
        "category": "engineering",
        "version": "2027.1.0",
        "status": "available",
        "allowed_tools": ["knowledge.query", "artifact.read", "artifact.write"],
        "forbidden_tools": ["production.deploy", "secret.export"],
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
        "identity": {
            "id": "twin-novacodepro",
            "type": "PLATFORM",
            "owner": "NovaCodePro",
            "jurisdiction": "AU",
            "classification": "INTERNAL",
            "version": 1,
            "lifecycle_state": "ACTIVE",
            "trust_state": "TRUSTED",
        },
        "observed_state": "HEALTHY",
        "desired_state": "AVAILABLE",
        "predicted_state": "STABLE",
        "simulated_state": "NOT_RUN",
        "approved_state": "APPROVED",
        "recovered_state": "HEALTHY",
        "metrics": {
            "availability": 0.999,
            "latency_p95_ms": 118,
            "error_rate": 0.0002,
            "risk_score": 18,
            "recovery_minutes": 8,
        },
        "state": {
            "observed": {
                "label": "Observed State",
                "status": "HEALTHY",
                "detail": "Live telemetry indicates the platform is healthy.",
                "evidence": ["prometheus", "opentelemetry"],
            },
            "desired": {
                "label": "Desired State",
                "status": "AVAILABLE",
                "detail": "Platform should remain available to all teams.",
                "evidence": ["sla-availability"],
            },
            "predicted": {
                "label": "Predicted State",
                "status": "STABLE",
                "detail": "No high-risk change is pending.",
                "evidence": [],
            },
            "simulated": {
                "label": "Simulated State",
                "status": "NOT_RUN",
                "detail": "No resilience simulation has been executed yet.",
                "evidence": [],
            },
            "approved": {
                "label": "Approved State",
                "status": "APPROVED",
                "detail": "Approved operational posture.",
                "evidence": ["governance-approval"],
            },
            "recovered": {
                "label": "Recovered State",
                "status": "HEALTHY",
                "detail": "Recovery has been validated.",
                "evidence": ["recovery-evidence"],
            },
        },
        "relationships": [
            {
                "id": "rel-novacodepro-gateway",
                "source": "twin-novacodepro",
                "target": "NovaCodePro Gateway",
                "type": "DEPENDS_ON",
                "criticality": "CRITICAL",
                "weight": 4.8,
                "rto": "15m",
                "rpo": "5m",
                "recovery_difficulty": 3.4,
                "confidence": 0.98,
                "evidence": ["service-registry", "dependency-map"],
            },
            {
                "id": "rel-novacodepro-workflow",
                "source": "twin-novacodepro",
                "target": "Workflow Service",
                "type": "DEPENDS_ON",
                "criticality": "HIGH",
                "weight": 4.2,
                "rto": "30m",
                "rpo": "10m",
                "recovery_difficulty": 2.6,
                "confidence": 0.95,
                "evidence": ["workflow-topology"],
            },
        ],
        "sources": ["Prometheus", "OpenTelemetry", "Knowledge Graph", "Approval Ledger"],
        "controls": ["NovaPolicy", "NovaRisk", "NovaCompliance", "NovaAudit"],
        "evidence": ["prometheus", "approval-ledger", "incident-log"],
        "lineage": ["workflow-ride-platform", "release-ride-platform"],
        "summary": "Enterprise platform twin for NovaCodePro governed operations.",
        "resilience": {
            "twin_fidelity_score": 84,
            "dependency_confidence_score": 96,
            "simulation_confidence_score": 88,
            "recovery_confidence_score": 91,
            "enterprise_resilience_score": 90,
        },
        "recovery": {
            "status": "VERIFIED",
            "plan_id": "recovery-plan-novacodepro",
            "workflow": {
                "id": "recovery-plan-novacodepro",
                "scenario": "regional_outage",
                "expected_rto": "15m",
                "expected_rpo": "5m",
                "steps": ["verify_failure", "activate_replica", "switch_traffic", "validate_health", "capture_evidence"],
            },
            "evidence_id": "evidence-recovery-novacodepro",
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
    def __init__(self, db_path: str | Path, database_url: str | None = None) -> None:
        self.database_url = database_url or _default_database_url()
        validate_database_runtime(self.database_url, _runtime_environment())
        self._use_postgres = bool(self.database_url and self.database_url.startswith(("postgres://", "postgresql://")))
        self.path = Path(db_path)
        if self._use_postgres:
            self.path = Path(":postgres:")
        elif str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> Any:
        if self._use_postgres:
            try:
                import psycopg
                from psycopg.rows import dict_row
            except Exception as exc:  # pragma: no cover - optional production dependency
                raise RuntimeError("psycopg is required when NOVACODEPRO_*_DATABASE_URL points to PostgreSQL") from exc

            connection = psycopg.connect(self.database_url, row_factory=dict_row)
            return _PostgresConnectionAdapter(connection)
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

                CREATE TABLE IF NOT EXISTS outbox_events (
                    event_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    last_error TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    published_at TEXT
                );

                CREATE TABLE IF NOT EXISTS retry_queue (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    consumer_name TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    next_retry_at TEXT NOT NULL,
                    last_error TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dead_letter_queue (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    consumer_name TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    failure_reason TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    failed_at TEXT NOT NULL,
                    last_attempt_at TEXT NOT NULL,
                    status TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projection_checkpoints (
                    projection_name TEXT PRIMARY KEY,
                    last_event_id TEXT NOT NULL,
                    updated_at TEXT NOT NULL
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
            "agent_registry": DEFAULT_AGENT_REGISTRY,
            "approval": DEFAULT_APPROVALS,
            "deployment": DEFAULT_DEPLOYMENTS,
            "digital_twin": DEFAULT_DIGITAL_TWINS,
            "service": DEFAULT_SERVICE_REGISTRY,
            "policy_rule": DEFAULT_POLICY_RULES,
            "risk_record": DEFAULT_RISK_RECORDS,
            "evidence_bundle": DEFAULT_EVIDENCE_BUNDLES,
            "operation_record": DEFAULT_OPERATION_RECORDS,
            "executive_briefing": DEFAULT_EXECUTIVE_BRIEFINGS,
        }
        with self._connect() as connection:
            for kind, payloads in seeds.items():
                row = connection.execute("SELECT COUNT(*) AS count FROM records WHERE kind = ?", (kind,)).fetchone()
                if row is None:
                    count = 0
                elif isinstance(row, dict):
                    count = int(row.get("count") or next(iter(row.values()), 0))
                else:
                    count = int(row[0])
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

    def delete(self, kind: str, record_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM records WHERE kind = ? AND record_id = ?",
                (kind, record_id),
            )

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
            connection.execute(
                """
                INSERT INTO outbox_events (
                    event_id,
                    topic,
                    payload_json,
                    status,
                    attempts,
                    last_error,
                    created_at,
                    published_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    status = excluded.status,
                    attempts = excluded.attempts,
                    last_error = excluded.last_error,
                    created_at = excluded.created_at,
                    published_at = excluded.published_at
                """,
                (
                    event["event_id"],
                    event["event_type"],
                    json.dumps(event, sort_keys=True),
                    "pending",
                    0,
                    "",
                    event["occurred_at"],
                    None,
                ),
            )
        return event

    def list_outbox(self, limit: int = 100, status: str | None = "pending") -> list[dict[str, Any]]:
        query = "SELECT payload_json FROM outbox_events"
        params: list[Any] = []
        if status is not None:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at ASC, event_id ASC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def ack_outbox_event(self, event_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE outbox_events
                SET status = 'published', published_at = ?, last_error = ''
                WHERE event_id = ?
                """,
                (_now(), event_id),
            )

    def fail_outbox_event(self, event_id: str, error: str) -> None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT attempts FROM outbox_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            attempts = int(row["attempts"] if row else 0) + 1
            connection.execute(
                """
                UPDATE outbox_events
                SET status = 'failed', attempts = ?, last_error = ?, published_at = NULL
                WHERE event_id = ?
                """,
                (attempts, error, event_id),
            )

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM domain_events ORDER BY occurred_at DESC, event_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def list_events_for_aggregate(self, aggregate_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM domain_events
                WHERE project_id = ? OR workflow_id = ? OR correlation_id = ?
                ORDER BY occurred_at ASC, event_id ASC
                LIMIT ?
                """,
                (aggregate_id, aggregate_id, aggregate_id, limit),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def enqueue_retry(
        self,
        *,
        event_id: str,
        consumer_name: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any],
        retry_count: int,
        next_retry_at: str,
        last_error: str,
    ) -> dict[str, Any]:
        record = {
            "id": _new_id("retry"),
            "event_id": event_id,
            "consumer_name": consumer_name,
            "aggregate_id": aggregate_id,
            "event_type": event_type,
            "payload": dict(payload),
            "retry_count": int(retry_count),
            "next_retry_at": next_retry_at,
            "last_error": last_error,
            "status": "PENDING",
            "created_at": _now(),
            "updated_at": _now(),
        }
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO retry_queue (
                    id,
                    event_id,
                    consumer_name,
                    aggregate_id,
                    event_type,
                    payload_json,
                    retry_count,
                    next_retry_at,
                    last_error,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["event_id"],
                    record["consumer_name"],
                    record["aggregate_id"],
                    record["event_type"],
                    json.dumps(record["payload"], sort_keys=True),
                    record["retry_count"],
                    record["next_retry_at"],
                    record["last_error"],
                    record["status"],
                    record["created_at"],
                    record["updated_at"],
                ),
            )
        return record

    def list_retry_queue(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM retry_queue ORDER BY next_retry_at ASC, id ASC",
            ).fetchall()
        return [
            {
                **dict(row),
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]

    def move_retry_to_dead_letter(self, retry_id: str, *, failure_reason: str) -> dict[str, Any]:
        retry = None
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT * FROM retry_queue WHERE id = ?", (retry_id,)).fetchone()
            if row is None:
                raise KeyError("retry_not_found")
            retry = dict(row)
            connection.execute("DELETE FROM retry_queue WHERE id = ?", (retry_id,))
            dead_letter = {
                "id": _new_id("dlq"),
                "event_id": retry["event_id"],
                "consumer_name": retry["consumer_name"],
                "aggregate_id": retry["aggregate_id"],
                "event_type": retry["event_type"],
                "payload_json": retry["payload_json"],
                "failure_reason": failure_reason,
                "retry_count": int(retry["retry_count"] or 0),
                "failed_at": _now(),
                "last_attempt_at": str(retry["updated_at"]),
                "status": "DEAD",
            }
            connection.execute(
                """
                INSERT INTO dead_letter_queue (
                    id,
                    event_id,
                    consumer_name,
                    aggregate_id,
                    event_type,
                    payload_json,
                    failure_reason,
                    retry_count,
                    failed_at,
                    last_attempt_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dead_letter["id"],
                    dead_letter["event_id"],
                    dead_letter["consumer_name"],
                    dead_letter["aggregate_id"],
                    dead_letter["event_type"],
                    dead_letter["payload_json"],
                    dead_letter["failure_reason"],
                    dead_letter["retry_count"],
                    dead_letter["failed_at"],
                    dead_letter["last_attempt_at"],
                    dead_letter["status"],
                ),
            )
        return {
            **dead_letter,
            "payload": json.loads(dead_letter["payload_json"]),
        }

    def list_dead_letter_queue(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM dead_letter_queue ORDER BY failed_at DESC, id DESC",
            ).fetchall()
        return [
            {
                **dict(row),
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]

    def save_projection_checkpoint(self, projection_name: str, last_event_id: str) -> dict[str, Any]:
        checkpoint = {
            "projection_name": projection_name,
            "last_event_id": last_event_id,
            "updated_at": _now(),
        }
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projection_checkpoints (projection_name, last_event_id, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(projection_name) DO UPDATE SET
                    last_event_id = excluded.last_event_id,
                    updated_at = excluded.updated_at
                """,
                (checkpoint["projection_name"], checkpoint["last_event_id"], checkpoint["updated_at"]),
            )
        return checkpoint

    def get_projection_checkpoint(self, projection_name: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM projection_checkpoints WHERE projection_name = ?",
                (projection_name,),
            ).fetchone()
        return dict(row) if row is not None else None


class NovaCodeProPlatform:
    def __init__(self, repository: NovaCodeProRepository) -> None:
        self.repository = repository

    def service_registry(self) -> list[dict[str, Any]]:
        services = self.repository.list("service")
        if services:
            return services
        try:
            from afritech.novacodepro.demo.factories._catalog import build_service_registry
        except Exception:
            return services
        seeded = [self.repository.upsert("service", item) for item in build_service_registry()]
        return seeded

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

    def agents(self) -> list[dict[str, Any]]:
        return self.repository.list("agent_registry")

    def register_agent(self, payload: dict[str, Any]) -> dict[str, Any]:
        agent = {
            "id": str(payload.get("id") or payload.get("agent_id") or _new_id("agent")),
            "name": str(payload.get("name") or payload.get("id") or payload.get("agent_id") or "NovaCodePro Agent"),
            "category": str(payload.get("category") or "general"),
            "version": str(payload.get("version") or "2027.1.0"),
            "status": str(payload.get("status") or "available"),
            "allowed_tools": list(payload.get("allowed_tools") or []),
            "forbidden_tools": list(payload.get("forbidden_tools") or []),
            "tenant_id": str(payload.get("tenant_id") or self.tenants()[0]["id"]),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("agent_registry", agent)
        return agent

    def retry_agent_execution(self, execution_id: str, actor: str = "NovaID") -> dict[str, Any]:
        execution = self.get_agent_execution(execution_id)
        if execution is None:
            raise KeyError("agent_execution_not_found")
        execution["status"] = "running"
        execution["retried_at"] = _now()
        execution["retry_count"] = int(execution.get("retry_count", 0)) + 1
        execution["updated_at"] = _now()
        self.repository.upsert("agent_execution", execution)
        self.repository.append_event(
            _event_envelope(
                event_type="agent.execution.retried",
                actor_type="user",
                actor_id=actor,
                tenant_id=str(execution.get("tenant_id") or self.tenants()[0]["id"]),
                organization_id=str(execution.get("tenant_id") or self.tenants()[0]["id"]),
                project_id=str(execution.get("project_id") or "") or None,
                workflow_id=str(execution.get("workflow_id") or "") or None,
                correlation_id=execution["id"],
                causation_id=execution["id"],
                data={"agent_execution_id": execution["id"], "status": execution["status"]},
            )
        )
        return execution

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

    def digital_twin_registry(self) -> list[dict[str, Any]]:
        return self.digital_twins()

    def create_digital_twin(self, payload: dict[str, Any]) -> dict[str, Any]:
        twin = build_twin_record(payload)
        twin["id"] = str(payload.get("id") or twin["id"])
        twin["kind"] = str(payload.get("kind") or twin.get("type") or "service").lower()
        twin["topology"] = dict(payload.get("topology") or {"services": []})
        twin["children"] = list(payload.get("children") or [])
        twin["scores"] = derive_resilience_scores(twin)
        twin["resilience"] = dict(twin["scores"])
        self.repository.upsert("digital_twin", twin)
        self.repository.append_event(
            _event_envelope(
                event_type="digital_twin.created",
                actor_type="service",
                actor_id="digital-twin-registry",
                tenant_id=str(twin.get("tenant_id") or self.tenants()[0]["id"]),
                organization_id=str(twin.get("tenant_id") or self.tenants()[0]["id"]),
                project_id=None,
                workflow_id=None,
                correlation_id=twin["id"],
                causation_id=twin["id"],
                data={"twin_id": twin["id"], "status": twin.get("status"), "region": twin.get("region")},
            )
        )
        return twin

    def _normalize_digital_twin(self, twin: dict[str, Any]) -> dict[str, Any]:
        if "identity" in twin and "state" in twin and "resilience" in twin:
            return twin
        payload = {
            "id": twin.get("id"),
            "name": twin.get("name"),
            "type": twin.get("kind") or twin.get("type") or "SERVICE",
            "owner": twin.get("owner") or "NovaCodePro",
            "tenant_id": twin.get("tenant_id") or self.tenants()[0]["id"],
            "classification": twin.get("classification") or "INTERNAL",
            "jurisdiction": twin.get("jurisdiction") or "AU",
            "status": twin.get("status") or "healthy",
            "region": twin.get("region") or "Australia",
            "observed_state": twin.get("observed_state") or "HEALTHY",
            "desired_state": twin.get("desired_state") or "AVAILABLE",
            "predicted_state": twin.get("predicted_state") or "STABLE",
            "simulated_state": twin.get("simulated_state") or "NOT_RUN",
            "approved_state": twin.get("approved_state") or "APPROVED",
            "recovered_state": twin.get("recovered_state") or "HEALTHY",
            "metrics": twin.get("metrics") or twin.get("health") or {},
            "relationships": twin.get("relationships") or [],
            "sources": twin.get("sources") or [],
            "controls": twin.get("controls") or [],
            "evidence": twin.get("evidence") or [],
            "lineage": twin.get("lineage") or [],
        }
        normalized = build_twin_record(payload)
        normalized["kind"] = twin.get("kind") or normalized["type"].lower()
        normalized["topology"] = dict(twin.get("topology") or {"services": []})
        normalized["children"] = list(twin.get("children") or [])
        normalized["scores"] = derive_resilience_scores(normalized)
        normalized["resilience"] = dict(normalized["scores"])
        normalized["created_at"] = twin.get("created_at") or normalized["created_at"]
        normalized["updated_at"] = twin.get("updated_at") or normalized["updated_at"]
        self.repository.upsert("digital_twin", normalized)
        return normalized

    def twin_relationships(self, twin_id: str) -> list[dict[str, Any]]:
        twin = self.get_or_create_digital_twin(twin_id)
        return list(twin.get("relationships") or [])

    def create_twin_relationship(self, twin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        relationship = build_twin_relationship({
            "id": payload.get("id"),
            "source": payload.get("source") or twin["id"],
            "target": payload.get("target") or "",
            "type": payload.get("type") or "DEPENDS_ON",
            "criticality": payload.get("criticality") or "MEDIUM",
            "weight": payload.get("weight") or 1.0,
            "rto": payload.get("rto") or "15m",
            "rpo": payload.get("rpo") or "5m",
            "recovery_difficulty": payload.get("recovery_difficulty") or 1.0,
            "confidence": payload.get("confidence") or 0.9,
            "evidence": payload.get("evidence") or [],
        })
        relationships = list(twin.get("relationships") or [])
        relationships.append(relationship)
        twin["relationships"] = relationships
        twin["scores"] = derive_resilience_scores(twin)
        twin["updated_at"] = _now()
        self.repository.upsert("digital_twin", twin)
        self.repository.upsert("twin_relationship", {"id": relationship["id"], "twin_id": twin["id"], **relationship, "created_at": relationship["created_at"], "updated_at": _now()})
        return relationship

    def twin_snapshots(self, twin_id: str) -> list[dict[str, Any]]:
        twin = self.get_or_create_digital_twin(twin_id)
        snapshots = [
            snapshot
            for snapshot in self.repository.list("twin_snapshot")
            if str(snapshot.get("twin_id") or "") == twin["id"]
        ]
        simulations = [
            snapshot
            for snapshot in self.repository.list("twin_simulation")
            if str(snapshot.get("twin_id") or "") == twin["id"]
        ]
        return snapshots + simulations

    def create_twin_snapshot(self, twin_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        snapshot = {
            "id": str((payload or {}).get("id") or _new_id("twin-snapshot")),
            "twin_id": twin["id"],
            "state": dict(twin.get("state") or {}),
            "metrics": dict(twin.get("metrics") or {}),
            "resilience": dict(twin.get("resilience") or {}),
            "status": twin.get("status"),
            "region": twin.get("region"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("twin_snapshot", snapshot)
        return snapshot

    def twin_scores(self, twin_id: str) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        scores = derive_resilience_scores(twin)
        twin["scores"] = scores
        twin["resilience"] = scores
        self.repository.upsert("digital_twin", twin)
        return {"twin_id": twin["id"], **scores}

    def observe_twin(self, twin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        updated = apply_observation(twin, payload)
        self.repository.upsert("digital_twin", updated)
        snapshot = self.create_twin_snapshot(twin_id, {"id": _new_id("snapshot")})
        self.repository.append_event(
            _event_envelope(
                event_type="digital_twin.observed",
                actor_type="service",
                actor_id=str(payload.get("actor") or "digital-twin-engine"),
                tenant_id=str(updated.get("tenant_id") or self.tenants()[0]["id"]),
                organization_id=str(updated.get("tenant_id") or self.tenants()[0]["id"]),
                project_id=None,
                workflow_id=None,
                correlation_id=updated["id"],
                causation_id=updated["id"],
                data={"twin_id": updated["id"], "snapshot_id": snapshot["id"], "observed_state": updated.get("observed_state")},
            )
        )
        return {"twin": updated, "snapshot": snapshot, "scores": updated.get("scores") or {}}

    def simulate_twin(self, twin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        result = simulate_twin(twin, payload)
        self.repository.upsert("twin_simulation", result)
        twin["simulated_state"] = result["simulated_twin"]["simulated_state"]
        twin["state"] = dict(result["simulated_twin"].get("state") or twin.get("state") or {})
        twin["metrics"] = dict(result["simulated_twin"].get("metrics") or twin.get("metrics") or {})
        twin["scores"] = dict(result["simulated_twin"].get("resilience") or twin.get("scores") or {})
        twin["resilience"] = dict(twin["scores"])
        twin["updated_at"] = _now()
        self.repository.upsert("digital_twin", twin)
        self.repository.append_event(
            _event_envelope(
                event_type="digital_twin.simulated",
                actor_type="service",
                actor_id="digital-twin-engine",
                tenant_id=str(twin.get("tenant_id") or self.tenants()[0]["id"]),
                organization_id=str(twin.get("tenant_id") or self.tenants()[0]["id"]),
                project_id=None,
                workflow_id=None,
                correlation_id=twin["id"],
                causation_id=twin["id"],
                data={"twin_id": twin["id"], "simulation_id": result["id"], "scenario": result["scenario"]},
            )
        )
        return result

    def create_twin_recovery_plan(self, twin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        plan = build_recovery_plan(twin, payload)
        twin["recovery"] = {
            "status": "READY",
            "plan_id": plan["id"],
            "workflow": plan,
            "evidence_id": str((payload or {}).get("evidence_id") or ""),
        }
        self.repository.upsert("digital_twin", twin)
        self.repository.upsert("twin_recovery_plan", plan)
        return plan

    def recover_twin(self, twin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        result = execute_recovery(twin, payload)
        self.repository.upsert("digital_twin", result["twin"])
        self.repository.upsert("twin_recovery_plan", result["recovery_plan"])
        self.repository.upsert("twin_evidence", result["evidence"])
        self.repository.append_event(
            _event_envelope(
                event_type="digital_twin.recovered",
                actor_type="service",
                actor_id=str(payload.get("actor") or "recovery-orchestrator"),
                tenant_id=str(result["twin"].get("tenant_id") or self.tenants()[0]["id"]),
                organization_id=str(result["twin"].get("tenant_id") or self.tenants()[0]["id"]),
                project_id=None,
                workflow_id=None,
                correlation_id=result["twin"]["id"],
                causation_id=result["twin"]["id"],
                data={"twin_id": result["twin"]["id"], "recovery_plan_id": result["recovery_plan"]["id"], "evidence_id": result["evidence"]["id"]},
            )
        )
        return result

    def twin_evidence(self, twin_id: str) -> list[dict[str, Any]]:
        twin = self.get_or_create_digital_twin(twin_id)
        evidence = [
            item
            for item in self.repository.list("twin_evidence")
            if str(item.get("twin_id") or "") == twin["id"]
        ]
        return evidence

    def digital_twin_summary(self, twin_id: str | None = None) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        scores = derive_resilience_scores(twin)
        return {
            "id": twin["id"],
            "name": twin.get("name"),
            "type": twin.get("type"),
            "status": twin.get("status"),
            "region": twin.get("region"),
            "observed_state": twin.get("observed_state"),
            "desired_state": twin.get("desired_state"),
            "predicted_state": twin.get("predicted_state"),
            "simulated_state": twin.get("simulated_state"),
            "approved_state": twin.get("approved_state"),
            "recovered_state": twin.get("recovered_state"),
            "relationships": len(twin.get("relationships") or []),
            "evidence_count": len(twin.get("evidence") or []),
            "scores": scores,
            "resilience": scores,
            "updated_at": twin.get("updated_at"),
        }

    def events(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_events(limit=limit)

    def audit(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_audit(limit=limit)

    def _tenant_id(self, tenant_id: str | None = None) -> str:
        return str(tenant_id or self.tenants()[0]["id"])

    def _risk_scale(self, value: str | int | float | None) -> int:
        if isinstance(value, (int, float)):
            return max(int(value), 0)
        scale = {"low": 1, "medium": 3, "high": 6, "critical": 9}
        return scale.get(str(value or "low").strip().lower(), 1)

    def _payload_hash(self, payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _policy_rules(self) -> list[dict[str, Any]]:
        return self.repository.list("policy_rule")

    def policies(self) -> list[dict[str, Any]]:
        return self._policy_rules()

    def _find_policy_rule(self, policy_id: str) -> dict[str, Any] | None:
        return self.repository.get("policy_rule", policy_id)

    def create_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        policy = {
            "id": str(payload.get("id") or _new_id("policy")),
            "name": str(payload.get("name") or payload.get("id") or "NovaCodePro Policy"),
            "scope": str(payload.get("scope") or "general"),
            "required_approvals": list(payload.get("required_approvals") or []),
            "quorum": int(payload.get("quorum") or 1),
            "timeout_hours": int(payload.get("timeout_hours") or 24),
            "active": bool(payload.get("active", True)),
            "description": str(payload.get("description") or ""),
            "rules": dict(payload.get("rules") or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("policy_rule", policy)
        self.repository.append_event(
            _event_envelope(
                event_type="policy.created",
                actor_type="service",
                actor_id="policy-service",
                tenant_id=self._tenant_id(str(payload.get("tenant_id") or "")),
                organization_id=self._tenant_id(str(payload.get("tenant_id") or "")),
                project_id=None,
                workflow_id=str(payload.get("workflow_id") or "") or None,
                correlation_id=policy["id"],
                causation_id=policy["id"],
                data={"policy_id": policy["id"], "name": policy["name"], "scope": policy["scope"]},
            )
        )
        return policy

    def evaluate_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        policy_id = str(payload.get("policy_id") or "REL-PROD-001")
        policy = self._find_policy_rule(policy_id)
        if policy is None:
            policy = self.create_policy({"id": policy_id, "name": policy_id, "scope": "general"})
        approvals = [str(item).upper() for item in list(payload.get("approvals") or [])]
        required = [str(item).upper() for item in list(policy.get("required_approvals") or [])]
        missing = [item for item in required if item not in approvals]
        reasons: list[str] = []
        if not policy.get("active", True):
            reasons.append("policy_inactive")
        if missing:
            reasons.extend(f"{item.lower()}_approval_missing" for item in missing)
        if str(payload.get("environment") or "").lower() == "production" and not payload.get("rollback_plan"):
            reasons.append("rollback_plan_missing")
        conditions: list[dict[str, Any]] = []
        reason_codes = [reason.upper() for reason in reasons]
        production = str(payload.get("environment") or "").lower() == "production"
        criticality = str(payload.get("criticality") or "").upper()
        risk_classification = str(payload.get("risk_classification") or "").upper()
        if production:
            reason_codes.append("PRODUCTION_ENVIRONMENT")
        if criticality in {"TIER_0", "TIER_1"}:
            reason_codes.append(f"{criticality}_CAPABILITY")
        if risk_classification in {"HIGH", "CRITICAL"}:
            reason_codes.append(f"{risk_classification}_RISK")
        if required:
            conditions.append({"type": "APPROVAL", "required_roles": required, "quorum": int(policy.get("quorum") or 1)})
        if production or criticality in {"TIER_0", "TIER_1"}:
            conditions.append({"type": "EVIDENCE", "required": ["SIMULATION_RESULT", "ROLLBACK_VALIDATION"]})
        if "policy_inactive" in reasons or "rollback_plan_missing" in reasons:
            outcome = "DENY"
        elif missing or production or criticality in {"TIER_0", "TIER_1"} or risk_classification in {"HIGH", "CRITICAL"}:
            outcome = "REQUIRE_APPROVAL"
        elif conditions:
            outcome = "PERMIT_WITH_CONDITIONS"
        else:
            outcome = "PERMIT"
        decision = "ALLOW" if outcome in {"PERMIT", "PERMIT_WITH_CONDITIONS"} else "DENY"
        evaluated_at = _now()
        input_hash = self._payload_hash(
            {
                "policy_id": policy_id,
                "environment": payload.get("environment"),
                "criticality": payload.get("criticality"),
                "risk_classification": payload.get("risk_classification"),
                "approvals": approvals,
                "rollback_plan": payload.get("rollback_plan"),
            }
        )
        decision_id = _new_id("pdec")
        result = {
            "id": decision_id,
            "decision_id": decision_id,
            "policy_id": policy["id"],
            "policy": policy,
            "decision": decision,
            "outcome": outcome,
            "policy_version": f"{policy['id']}@{policy.get('version', '1')}",
            "matched_rules": [code.lower() for code in reason_codes] or ["default-permit"],
            "conditions": conditions,
            "reason_codes": sorted(set(reason_codes)),
            "evaluated_at": evaluated_at,
            "expires_at": evaluated_at,
            "input_hash": f"sha256:{input_hash}",
            "engine_version": "novapolicy-local-2.0",
            "reasons": reasons,
            "required_approvals": required,
            "quorum": int(policy.get("quorum") or 1),
            "tenant_id": self._tenant_id(str(payload.get("tenant_id") or "")),
            "environment": str(payload.get("environment") or "development"),
        }
        self.repository.upsert("policy_decision", result)
        self.repository.append_event(
            _event_envelope(
                event_type="policy.evaluated",
                actor_type="service",
                actor_id="policy-engine",
                tenant_id=result["tenant_id"],
                organization_id=result["tenant_id"],
                project_id=str(payload.get("project_id") or "") or None,
                workflow_id=str(payload.get("workflow_id") or "") or None,
                correlation_id=policy["id"],
                causation_id=policy["id"],
                data=result,
            )
        )
        return result

    def activate_policy(self, policy_id: str, active: bool = True) -> dict[str, Any]:
        policy = self._find_policy_rule(policy_id)
        if policy is None:
            raise KeyError("policy_not_found")
        policy["active"] = active
        policy["updated_at"] = _now()
        self.repository.upsert("policy_rule", policy)
        return policy

    def risks(self) -> list[dict[str, Any]]:
        return self.repository.list("risk_record")

    def get_risk(self, risk_id: str) -> dict[str, Any] | None:
        return self.repository.get("risk_record", risk_id)

    def evaluate_risk(self, payload: dict[str, Any]) -> dict[str, Any]:
        likelihood = self._risk_scale(payload.get("likelihood"))
        impact = self._risk_scale(payload.get("impact"))
        exposure = self._risk_scale(payload.get("exposure"))
        score = likelihood * impact * exposure
        classification = "LOW"
        if score >= 50:
            classification = "CRITICAL"
        elif score >= 24:
            classification = "HIGH"
        elif score >= 8:
            classification = "MEDIUM"
        risk = {
            "id": str(payload.get("id") or _new_id("risk")),
            "title": str(payload.get("title") or "NovaCodePro Risk"),
            "likelihood": str(payload.get("likelihood") or "low"),
            "impact": str(payload.get("impact") or "low"),
            "exposure": str(payload.get("exposure") or "low"),
            "score": score,
            "classification": classification,
            "owner": str(payload.get("owner") or "risk-team"),
            "required_controls": list(payload.get("required_controls") or []),
            "status": "open",
            "tenant_id": self._tenant_id(str(payload.get("tenant_id") or "")),
            "project_id": str(payload.get("project_id") or ""),
            "workflow_id": str(payload.get("workflow_id") or ""),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("risk_record", risk)
        self.repository.append_event(
            _event_envelope(
                event_type="risk.evaluated",
                actor_type="service",
                actor_id="risk-engine",
                tenant_id=risk["tenant_id"],
                organization_id=risk["tenant_id"],
                project_id=risk["project_id"] or None,
                workflow_id=risk["workflow_id"] or None,
                correlation_id=risk["id"],
                causation_id=risk["id"],
                data=risk,
            )
        )
        return risk

    def treat_risk(self, risk_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        risk = self.get_risk(risk_id)
        if risk is None:
            raise KeyError("risk_not_found")
        risk["status"] = "mitigating"
        risk["treatment"] = list(payload.get("treatment") or [])
        risk["owner"] = str(payload.get("owner") or risk.get("owner") or "risk-team")
        risk["updated_at"] = _now()
        self.repository.upsert("risk_record", risk)
        return risk

    def accept_risk(self, risk_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        risk = self.get_risk(risk_id)
        if risk is None:
            raise KeyError("risk_not_found")
        risk["status"] = "accepted"
        risk["accepted_by"] = str(payload.get("accepted_by") or "NovaID")
        risk["expiry"] = str(payload.get("expiry") or "")
        risk["updated_at"] = _now()
        self.repository.upsert("risk_record", risk)
        return risk

    def close_risk(self, risk_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        risk = self.get_risk(risk_id)
        if risk is None:
            raise KeyError("risk_not_found")
        risk["status"] = "closed"
        risk["closure_note"] = str((payload or {}).get("note") or "")
        risk["updated_at"] = _now()
        self.repository.upsert("risk_record", risk)
        return risk

    def evidence_bundles(self) -> list[dict[str, Any]]:
        return self.repository.list("evidence_bundle")

    def get_evidence_bundle(self, evidence_id: str) -> dict[str, Any] | None:
        return self.repository.get("evidence_bundle", evidence_id)

    def create_evidence_bundle(self, payload: dict[str, Any]) -> dict[str, Any]:
        verification_status = str(payload.get("verification_status") or "")
        local_signature_mode = bool(payload.get("local_signature_mode", True))
        bundle = {
            "id": str(payload.get("id") or _new_id("evidence")),
            "tenant_id": self._tenant_id(str(payload.get("tenant_id") or "")),
            "workflow_id": str(payload.get("workflow_id") or ""),
            "actor": dict(payload.get("actor") or {"type": "user", "id": "NovaID"}),
            "action": str(payload.get("action") or "protected.action"),
            "policy_id": str(payload.get("policy_id") or "REL-PROD-001"),
            "artifact_ids": list(payload.get("artifact_ids") or []),
            "occurred_at": str(payload.get("occurred_at") or _now()),
            "payload": dict(payload.get("payload") or {}),
            "verified": bool(payload.get("verified", True)),
            "created_at": _now(),
            "updated_at": _now(),
        }
        canonical = {k: bundle[k] for k in ("tenant_id", "workflow_id", "actor", "action", "policy_id", "artifact_ids", "occurred_at", "payload")}
        bundle["hash"] = str(payload.get("hash") or self._payload_hash(canonical))
        signature_payload = f"NOVATECH_EVIDENCE:sha256:{bundle['hash']}".encode("utf-8")
        bundle["signature_algorithm"] = str(payload.get("signature_algorithm") or "HMAC_SHA_256_LOCAL")
        bundle["signing_key_id"] = str(payload.get("signing_key_id") or "local://novacodepro/evidence-development-key")
        bundle["signature"] = str(
            payload.get("signature")
            or hmac.new(b"novacodepro-local-evidence-key", signature_payload, hashlib.sha256).hexdigest()
        )
        if not verification_status:
            verification_status = "DEVELOPMENT_VERIFIED" if local_signature_mode and bundle["verified"] else "LEGACY_UNVERIFIED"
        bundle["verification_status"] = verification_status
        self.repository.upsert("evidence_bundle", bundle)
        self.repository.append_event(
            _event_envelope(
                event_type="evidence.created",
                actor_type=bundle["actor"].get("type", "user"),
                actor_id=bundle["actor"].get("id", "NovaID"),
                tenant_id=bundle["tenant_id"],
                organization_id=bundle["tenant_id"],
                project_id=str(payload.get("project_id") or "") or None,
                workflow_id=bundle["workflow_id"] or None,
                correlation_id=bundle["id"],
                causation_id=bundle["id"],
                data=bundle,
            )
        )
        return bundle

    def verify_evidence_bundle(self, evidence_id: str) -> dict[str, Any]:
        bundle = self.get_evidence_bundle(evidence_id)
        if bundle is None:
            raise KeyError("evidence_not_found")
        canonical = {k: bundle[k] for k in ("tenant_id", "workflow_id", "actor", "action", "policy_id", "artifact_ids", "occurred_at", "payload")}
        expected_hash = self._payload_hash(canonical)
        signature_payload = f"NOVATECH_EVIDENCE:sha256:{expected_hash}".encode("utf-8")
        expected_signature = hmac.new(b"novacodepro-local-evidence-key", signature_payload, hashlib.sha256).hexdigest()
        verified = bundle.get("hash") == expected_hash and bundle.get("signature") == expected_signature
        bundle["verified"] = verified
        bundle["verification_status"] = "DEVELOPMENT_VERIFIED" if verified else "LEGACY_UNVERIFIED"
        bundle["updated_at"] = _now()
        self.repository.upsert("evidence_bundle", bundle)
        return {"evidence_id": evidence_id, "verified": verified, "verification_status": bundle["verification_status"], "bundle": bundle}

    def search_evidence_bundles(self, query: str) -> list[dict[str, Any]]:
        needle = query.lower().strip()
        return [
            bundle
            for bundle in self.evidence_bundles()
            if needle in bundle.get("action", "").lower()
            or needle in bundle.get("policy_id", "").lower()
            or needle in bundle.get("id", "").lower()
        ]

    def knowledge_nodes(self) -> list[dict[str, Any]]:
        return self.repository.list("knowledge_node")

    def create_knowledge_node(self, payload: dict[str, Any]) -> dict[str, Any]:
        node = {
            "id": str(payload.get("id") or _new_id("node")),
            "label": str(payload.get("label") or payload.get("id") or "Knowledge Node"),
            "type": str(payload.get("type") or "artifact"),
            "links": list(payload.get("links") or []),
            "tenant_id": self._tenant_id(str(payload.get("tenant_id") or "")),
            "owner": str(payload.get("owner") or "NovaCodePro"),
            "evidence": list(payload.get("evidence") or []),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("knowledge_node", node)
        self.repository.append_event(
            _event_envelope(
                event_type="knowledge.node.created",
                actor_type="service",
                actor_id="knowledge-graph-service",
                tenant_id=node["tenant_id"],
                organization_id=node["tenant_id"],
                project_id=None,
                workflow_id=None,
                correlation_id=node["id"],
                causation_id=node["id"],
                data=node,
            )
        )
        return node

    def create_knowledge_relationship(self, source_id: str, target_id: str) -> dict[str, Any]:
        return self.link_nodes(source_id, target_id)

    def knowledge_query(self, query: str) -> dict[str, Any]:
        needle = query.lower().strip()
        matches = [node for node in self.knowledge_nodes() if needle in node.get("label", "").lower() or needle in node.get("id", "").lower()]
        return {"query": query, "matches": matches, "match_count": len(matches)}

    def _knowledge_path(self, start_id: str, target_id: str) -> list[dict[str, Any]]:
        nodes = {node["id"]: node for node in self.knowledge_nodes()}
        if start_id not in nodes or target_id not in nodes:
            raise KeyError("knowledge_node_not_found")
        frontier: list[tuple[str, list[str]]] = [(start_id, [start_id])]
        visited = {start_id}
        while frontier:
            current, path = frontier.pop(0)
            if current == target_id:
                return [nodes[node_id] for node_id in path]
            for linked in nodes[current].get("links") or []:
                if linked not in visited and linked in nodes:
                    visited.add(linked)
                    frontier.append((linked, path + [linked]))
        return []

    def knowledge_trace(self, node_id: str) -> dict[str, Any]:
        node = self.repository.get("knowledge_node", node_id)
        if node is None:
            raise KeyError("knowledge_node_not_found")
        outgoing = list(node.get("links") or [])
        incoming = [candidate["id"] for candidate in self.knowledge_nodes() if node_id in (candidate.get("links") or [])]
        return {"node": node, "outgoing": outgoing, "incoming": incoming}

    def knowledge_impact(self, node_id: str) -> dict[str, Any]:
        trace = self.knowledge_trace(node_id)
        impacted = [self.repository.get("knowledge_node", linked) for linked in trace["outgoing"] if self.repository.get("knowledge_node", linked)]
        return {"node": trace["node"], "impacted": impacted, "impact_count": len(impacted)}

    def graph_query(self, query: str) -> dict[str, Any]:
        matches = self.knowledge_query(query)
        return {
            "query": query,
            "nodes": matches["matches"],
            "count": matches["match_count"],
        }

    def graph_federation_query(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = str(payload.get("query") or "")
        region = str(payload.get("region") or "AU")
        capability = str(payload.get("capability") or "knowledge.read")
        authorization = self.federation_authorize({"capability": capability, "region": region})
        result = self.graph_query(query) if authorization["decision"] == "ALLOW" else {"query": query, "nodes": [], "count": 0}
        return {
            "query": query,
            "region": region,
            "capability": capability,
            "authorization": authorization,
            "result": result,
        }

    def graph_blast_radius(self, node_id: str) -> dict[str, Any]:
        impact = self.knowledge_impact(node_id)
        services = [node for node in impact["impacted"] if str(node.get("type") or "").lower() in {"service", "deployment", "release"}]
        return {
            "node_id": node_id,
            "blast_radius": len(impact["impacted"]),
            "impacted": impact["impacted"],
            "affected_services": services,
        }

    def graph_root_cause(self, node_id: str) -> dict[str, Any]:
        trace = self.knowledge_trace(node_id)
        return {
            "node_id": node_id,
            "likely_root_causes": trace["incoming"][:5],
            "evidence_nodes": trace["incoming"],
        }

    def graph_critical_path(self, start_id: str, end_id: str) -> dict[str, Any]:
        path = self._knowledge_path(start_id, end_id)
        return {"start_id": start_id, "end_id": end_id, "path": path, "path_length": len(path)}

    def graph_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = {
            "id": str(payload.get("id") or _new_id("graph-snapshot")),
            "tenant_id": self._tenant_id(str(payload.get("tenant_id") or "")),
            "region": str(payload.get("region") or "Australia"),
            "classification": str(payload.get("classification") or "INTERNAL"),
            "node_count": len(self.knowledge_nodes()),
            "edge_count": sum(len(node.get("links") or []) for node in self.knowledge_nodes()),
            "created_at": _now(),
            "updated_at": _now(),
            "payload": dict(payload),
        }
        self.repository.upsert("graph_snapshot", snapshot)
        self.repository.append_event(
            _event_envelope(
                event_type="graph.snapshot.created",
                actor_type="service",
                actor_id="graph-fabric",
                tenant_id=snapshot["tenant_id"],
                organization_id=snapshot["tenant_id"],
                project_id=None,
                workflow_id=None,
                correlation_id=snapshot["id"],
                causation_id=snapshot["id"],
                data=snapshot,
            )
        )
        return snapshot

    def graph_reconcile(self) -> dict[str, Any]:
        nodes = self.knowledge_nodes()
        return {
            "status": "reconciled",
            "node_count": len(nodes),
            "orphan_nodes": [node["id"] for node in nodes if not node.get("links")],
            "updated_at": _now(),
        }

    def create_federation_agreement(self, payload: dict[str, Any]) -> dict[str, Any]:
        agreement = {
            "id": str(payload.get("id") or _new_id("federation")),
            "provider_org": str(payload.get("provider_org") or self.tenants()[0]["id"]),
            "consumer_org": str(payload.get("consumer_org") or self.tenants()[0]["id"]),
            "status": str(payload.get("status") or "ACTIVE"),
            "trust_level": str(payload.get("trust_level") or "VERIFIED"),
            "allowed_capabilities": list(payload.get("allowed_capabilities") or []),
            "denied_capabilities": list(payload.get("denied_capabilities") or []),
            "allowed_regions": list(payload.get("allowed_regions") or ["AU"]),
            "data_classes": list(payload.get("data_classes") or ["PUBLIC", "INTERNAL"]),
            "purpose": str(payload.get("purpose") or ""),
            "expires_at": str(payload.get("expires_at") or "2027-07-01T00:00:00Z"),
            "signature": str(payload.get("signature") or f"sig-{_new_id('federation')}"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("federation_agreement", agreement)
        self.repository.append_event(
            _event_envelope(
                event_type="federation.agreement.created",
                actor_type="service",
                actor_id="federation-service",
                tenant_id=agreement["provider_org"],
                organization_id=agreement["provider_org"],
                project_id=None,
                workflow_id=None,
                correlation_id=agreement["id"],
                causation_id=agreement["id"],
                data=agreement,
            )
        )
        return agreement

    def federation_agreements(self) -> list[dict[str, Any]]:
        return self.repository.list("federation_agreement")

    def approve_federation_agreement(self, agreement_id: str, actor: str = "NovaID") -> dict[str, Any]:
        agreement = self.repository.get("federation_agreement", agreement_id)
        if agreement is None:
            raise KeyError("federation_agreement_not_found")
        agreement["status"] = "ACTIVE"
        agreement["approved_by"] = actor
        agreement["approved_at"] = _now()
        agreement["updated_at"] = _now()
        self.repository.upsert("federation_agreement", agreement)
        return agreement

    def revoke_federation_agreement(self, agreement_id: str, reason: str = "") -> dict[str, Any]:
        agreement = self.repository.get("federation_agreement", agreement_id)
        if agreement is None:
            raise KeyError("federation_agreement_not_found")
        agreement["status"] = "REVOKED"
        agreement["revoked_reason"] = reason
        agreement["revoked_at"] = _now()
        agreement["updated_at"] = _now()
        self.repository.upsert("federation_agreement", agreement)
        return agreement

    def federation_authorize(self, payload: dict[str, Any]) -> dict[str, Any]:
        agreements = self.federation_agreements()
        capability = str(payload.get("capability") or "")
        region = str(payload.get("region") or "AU")
        matching = [
            agreement
            for agreement in agreements
            if str(agreement.get("status") or "").upper() == "ACTIVE"
            and capability in (agreement.get("allowed_capabilities") or [])
            and region in (agreement.get("allowed_regions") or [])
        ]
        return {
            "decision": "ALLOW" if matching else "DENY",
            "agreement_ids": [agreement["id"] for agreement in matching],
            "capability": capability,
            "region": region,
        }

    def federation_hierarchy(self) -> dict[str, Any]:
        return {
            "enterprise": "NovaTech",
            "regions": [
                {"id": "australia", "countries": ["AU"]},
                {"id": "africa", "countries": ["KE", "UG", "CD", "ZA"]},
                {"id": "europe", "countries": ["EU"]},
                {"id": "americas", "countries": ["US", "CA"]},
            ],
        }

    def federation_share_resource(self, payload: dict[str, Any]) -> dict[str, Any]:
        record = {
            "id": str(payload.get("id") or _new_id("share")),
            "resource_id": str(payload.get("resource_id") or ""),
            "consumer_org": str(payload.get("consumer_org") or ""),
            "tenant_id": self._tenant_id(str(payload.get("tenant_id") or "")),
            "status": "SHARED",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("federation_share", record)
        return record

    def federation_unshare_resource(self, share_id: str) -> dict[str, Any]:
        record = self.repository.get("federation_share", share_id)
        if record is None:
            raise KeyError("federation_share_not_found")
        record["status"] = "UNSHARED"
        record["updated_at"] = _now()
        self.repository.upsert("federation_share", record)
        return record

    def federation_audit(self) -> list[dict[str, Any]]:
        return self.repository.list("federation_agreement") + self.repository.list("federation_share")

    def region_health(self, region_id: str) -> dict[str, Any]:
        deployments = [deployment for deployment in self.deployments() if str(deployment.get("region") or "").lower() == region_id.lower()]
        return {
            "region": region_id,
            "status": "healthy" if all(str(item.get("status") or "").lower() not in {"failed", "rolling_back"} for item in deployments) else "degraded",
            "deployment_count": len(deployments),
            "updated_at": _now(),
        }

    def region_governance(self, region_id: str) -> dict[str, Any]:
        return {
            "region": region_id,
            "policies": self.policies(),
            "agreements": [agreement for agreement in self.federation_agreements() if region_id.upper() in [str(item).upper() for item in agreement.get("allowed_regions") or []]],
        }

    def evaluate_region_eligibility(self, region_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        prerequisites = []
        if not payload.get("capacity_ok", True):
            prerequisites.append("capacity_insufficient")
        if not payload.get("keys_available", True):
            prerequisites.append("encryption_keys_missing")
        if not payload.get("replication_healthy", True):
            prerequisites.append("replication_lag_above_threshold")
        return {
            "region": region_id,
            "eligible": not prerequisites,
            "reasons": prerequisites,
        }

    def plan_region_failover(self, region_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "region": region_id,
            "target_region": str(payload.get("target_region") or ""),
            "eligible": False,
            "reasons": list(payload.get("reasons") or ["replication_lag_above_threshold"]),
            "required_actions": list(payload.get("required_actions") or ["restore_approved_replica", "obtain_emergency_compliance_approval"]),
        }

    def approve_region_failover(self, region_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"region": region_id, "status": "approved", "approver": str(payload.get("approver") or "NovaID"), "updated_at": _now()}

    def execute_region_failover(self, region_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"region": region_id, "status": "executed", "target_region": str(payload.get("target_region") or ""), "updated_at": _now()}

    def reconcile_region(self, region_id: str) -> dict[str, Any]:
        return {"region": region_id, "status": "reconciled", "updated_at": _now()}

    def twin_history(self, twin_id: str) -> list[dict[str, Any]]:
        twin = self.get_or_create_digital_twin(twin_id)
        snapshots = [record for record in self.repository.list("twin_snapshot") if str(record.get("twin_id") or "") == twin["id"]]
        simulations = [record for record in self.repository.list("twin_simulation") if str(record.get("twin_id") or "") == twin["id"]]
        evidence = [record for record in self.repository.list("twin_evidence") if str(record.get("twin_id") or "") == twin["id"]]
        return snapshots + simulations + evidence

    def compare_twins(self, twin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        baseline = self.get_or_create_digital_twin(twin_id)
        other = self.get_or_create_digital_twin(str(payload.get("compare_to") or twin_id))
        return {
            "baseline": baseline,
            "compare_to": other,
            "differences": {
                "status": [baseline.get("status"), other.get("status")],
                "region": [baseline.get("region"), other.get("region")],
            },
        }

    def replay_twin(self, twin_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"twin_id": twin_id, "status": "replayed", "observed_at": _now(), "payload": dict(payload or {})}

    def refresh_twin(self, twin_id: str) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        twin["updated_at"] = _now()
        self.repository.upsert("digital_twin", twin)
        return twin

    def executive_council_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = {
            "id": str(payload.get("id") or _new_id("council")),
            "subject": str(payload.get("subject") or ""),
            "question": str(payload.get("question") or ""),
            "status": "OPEN",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("executive_council_session", session)
        return session

    def executive_agent_analyze(self, role: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "agent": role,
            "position": str(payload.get("position") or "DEFER"),
            "confidence": float(payload.get("confidence") or 0.88),
            "findings": list(payload.get("findings") or []),
            "recommendations": list(payload.get("recommendations") or []),
            "evidence_ids": list(payload.get("evidence_ids") or []),
            "authority": "ADVISORY_ONLY",
        }

    def executive_council_synthesize(self, payload: dict[str, Any]) -> dict[str, Any]:
        report = {
            "subject": str(payload.get("subject") or ""),
            "consensus": str(payload.get("consensus") or "CONDITIONAL_APPROVAL_RECOMMENDED"),
            "supporting_agents": list(payload.get("supporting_agents") or []),
            "dissenting_agents": list(payload.get("dissenting_agents") or []),
            "conditions": list(payload.get("conditions") or []),
            "escalation": str(payload.get("escalation") or "BOARD_REVIEW_REQUIRED"),
        }
        self.repository.upsert("executive_briefing", {"id": _new_id("briefing"), **report, "created_at": _now(), "updated_at": _now()})
        return report

    def board_meeting(self, payload: dict[str, Any]) -> dict[str, Any]:
        meeting = {
            "id": str(payload.get("id") or _new_id("meeting")),
            "title": str(payload.get("title") or "NovaCodePro Board Meeting"),
            "status": "DRAFT",
            "agenda": list(payload.get("agenda") or []),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("board_meeting", meeting)
        return meeting

    def board_resolution(self, payload: dict[str, Any]) -> dict[str, Any]:
        resolution = {
            "id": str(payload.get("id") or _new_id("resolution")),
            "title": str(payload.get("title") or ""),
            "meeting_id": str(payload.get("meeting_id") or ""),
            "status": str(payload.get("status") or "DRAFT"),
            "quorum": dict(payload.get("quorum") or {"required": 3, "present": 0, "met": False}),
            "votes": dict(payload.get("votes") or {"for": 0, "against": 0, "abstain": 0}),
            "conditions": list(payload.get("conditions") or []),
            "evidence_ids": list(payload.get("evidence_ids") or []),
            "signature": str(payload.get("signature") or ""),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("board_resolution", resolution)
        return resolution

    def board_vote(self, resolution_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        resolution = self.repository.get("board_resolution", resolution_id)
        if resolution is None:
            raise KeyError("board_resolution_not_found")
        votes = dict(resolution.get("votes") or {})
        choice = str(payload.get("vote") or "abstain").lower()
        votes[choice] = int(votes.get(choice, 0)) + 1
        resolution["votes"] = votes
        resolution["updated_at"] = _now()
        self.repository.upsert("board_resolution", resolution)
        return resolution

    def board_close_resolution(self, resolution_id: str) -> dict[str, Any]:
        resolution = self.repository.get("board_resolution", resolution_id)
        if resolution is None:
            raise KeyError("board_resolution_not_found")
        resolution["status"] = "CLOSED"
        resolution["updated_at"] = _now()
        self.repository.upsert("board_resolution", resolution)
        return resolution

    def board_resolution_evidence(self, resolution_id: str) -> list[dict[str, Any]]:
        resolution = self.repository.get("board_resolution", resolution_id)
        if resolution is None:
            raise KeyError("board_resolution_not_found")
        return [self.repository.get("evidence_bundle", evidence_id) for evidence_id in resolution.get("evidence_ids") or [] if self.repository.get("evidence_bundle", evidence_id)]

    def sli_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        record = {
            "id": str(payload.get("id") or _new_id("sli")),
            "service": str(payload.get("service") or "novacodepro-gateway"),
            "metric": str(payload.get("metric") or "availability"),
            "target": float(payload.get("target") or 99.95),
            "measurement": float(payload.get("measurement") or 99.97),
            "window": str(payload.get("window") or "30d"),
            "status": str(payload.get("status") or "WITHIN_TARGET"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("sli_record", record)
        return record

    def slo_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        record = {
            "id": str(payload.get("id") or _new_id("slo")),
            "service": str(payload.get("service") or "novacodepro-gateway"),
            "metric": str(payload.get("metric") or "availability"),
            "target": float(payload.get("target") or 99.95),
            "window": str(payload.get("window") or "30d"),
            "measurement": float(payload.get("measurement") or 99.97),
            "status": str(payload.get("status") or "WITHIN_TARGET"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("slo_record", record)
        return record

    def error_budget(self, service_name: str, window: str = "30d") -> dict[str, Any]:
        sli = [item for item in self.repository.list("sli_record") if item.get("service") == service_name]
        target = sli[0].get("target") if sli else 99.95
        consumed = 5.2
        allowed = 21.6
        return {
            "service": service_name,
            "window": window,
            "allowed_minutes": allowed,
            "consumed_minutes": consumed,
            "remaining_minutes": max(allowed - consumed, 0),
            "burn_rate": round(consumed / allowed, 2),
            "release_policy": "NORMAL" if consumed < allowed else "FREEZE",
            "target": target,
        }

    def capacity(self) -> dict[str, Any]:
        deployments = self.deployments()
        return {
            "cpu": "68%",
            "memory": "61%",
            "storage": "74%",
            "queue_depth": len(self.repository.list("outbox_events")),
            "worker_saturation": len([item for item in self.agent_executions() if str(item.get("status") or "") == "queued"]),
            "database_connections": len(self.service_registry()),
            "broker_partitions": 12,
            "graph_query_latency_ms": 42,
            "deployments": len(deployments),
            "updated_at": _now(),
        }

    def chaos_experiment(self, payload: dict[str, Any]) -> dict[str, Any]:
        experiment = {
            "id": str(payload.get("id") or _new_id("chaos")),
            "scenario": str(payload.get("scenario") or ""),
            "scope": str(payload.get("scope") or "regional"),
            "owner": str(payload.get("owner") or "SRE"),
            "status": "DRAFT",
            "approval_id": str(payload.get("approval_id") or ""),
            "evidence_ids": list(payload.get("evidence_ids") or []),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("chaos_experiment", experiment)
        return experiment

    def create_event_topic(self, payload: dict[str, Any]) -> dict[str, Any]:
        topic = {
            "id": str(payload.get("id") or _new_id("topic")),
            "name": str(payload.get("name") or ""),
            "owner": str(payload.get("owner") or "NovaCodePro"),
            "retention": str(payload.get("retention") or "30d"),
            "classification": str(payload.get("classification") or "INTERNAL"),
            "region": str(payload.get("region") or "Australia"),
            "replay_policy": str(payload.get("replay_policy") or "isolated"),
            "status": str(payload.get("status") or "ACTIVE"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("event_topic", topic)
        return topic

    def event_topics(self) -> list[dict[str, Any]]:
        return self.repository.list("event_topic")

    def create_event_schema(self, payload: dict[str, Any]) -> dict[str, Any]:
        schema = {
            "id": str(payload.get("id") or _new_id("schema")),
            "topic": str(payload.get("topic") or ""),
            "version": str(payload.get("version") or "1.0"),
            "schema": dict(payload.get("schema") or {}),
            "compatibility": str(payload.get("compatibility") or "BACKWARD"),
            "status": "ACTIVE",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("event_schema", schema)
        return schema

    def create_event_replay(self, payload: dict[str, Any]) -> dict[str, Any]:
        replay = {
            "id": str(payload.get("id") or _new_id("replay")),
            "topic": str(payload.get("topic") or ""),
            "tenant_id": self._tenant_id(str(payload.get("tenant_id") or "")),
            "region": str(payload.get("region") or "Australia"),
            "status": "DRAFT",
            "started_at": None,
            "ended_at": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("event_replay", replay)
        return replay

    def event_replays(self) -> list[dict[str, Any]]:
        return self.repository.list("event_replay")

    def release_manifest(self, release_id: str) -> dict[str, Any] | None:
        return self.repository.get("release", release_id)

    def build_release(self, release_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        release = self.release_manifest(release_id)
        if release is None:
            raise KeyError("release_not_found")
        release["status"] = "building"
        release["build"] = dict(payload or {})
        release["updated_at"] = _now()
        self.repository.upsert("release", release)
        return release

    def sign_release(self, release_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        release = self.release_manifest(release_id)
        if release is None:
            raise KeyError("release_not_found")
        release["signature"] = str((payload or {}).get("signature") or f"sig-{_new_id('release')}")
        release["status"] = "signed"
        release["signed_at"] = _now()
        release["updated_at"] = _now()
        self.repository.upsert("release", release)
        return release

    def publish_release(self, release_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        release = self.release_manifest(release_id)
        if release is None:
            raise KeyError("release_not_found")
        release["status"] = "published"
        release["published_at"] = _now()
        release["updated_at"] = _now()
        release["channel"] = str((payload or {}).get("channel") or release.get("channel") or "pilot")
        self.repository.upsert("release", release)
        return release

    def promote_release(self, release_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        release = self.release_manifest(release_id)
        if release is None:
            raise KeyError("release_not_found")
        release["status"] = "release_ready"
        release["target"] = str((payload or {}).get("target") or release.get("target") or "staging")
        release["updated_at"] = _now()
        self.repository.upsert("release", release)
        return release

    def revoke_release(self, release_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        release = self.release_manifest(release_id)
        if release is None:
            raise KeyError("release_not_found")
        release["status"] = "revoked"
        release["revoked_reason"] = str((payload or {}).get("reason") or "")
        release["updated_at"] = _now()
        self.repository.upsert("release", release)
        return release

    def deployment_prerequisites(self, release_id: str, environment: str) -> dict[str, Any]:
        release = self.release_manifest(release_id)
        if release is None:
            raise KeyError("release_not_found")
        approvals = [
            approval
            for approval in self.approvals()
            if str(approval.get("release_id") or "") == release_id and str(approval.get("status") or "").upper() == "APPROVED"
        ]
        missing = []
        if environment.lower() == "production":
            if not approvals:
                missing.append("security_approval_missing")
            if str(release.get("status") or "").lower() not in {"signed", "published", "release_ready", "healthy"}:
                missing.append("release_not_ready")
            if not release.get("rollback_ref") and not release.get("rollback_plan"):
                missing.append("rollback_plan_missing")
        return {"release_id": release_id, "environment": environment, "missing": missing, "approved_count": len(approvals)}

    def start_deployment(self, deployment_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        deployment = self.get_deployment(deployment_id)
        if deployment is None:
            raise KeyError("deployment_not_found")
        environment = str((payload or {}).get("environment") or deployment.get("environment") or "staging")
        prereqs = self.deployment_prerequisites(str(deployment.get("release_id") or ""), environment)
        if prereqs["missing"]:
            raise ValueError(json.dumps({"code": "deployment_prerequisites_failed", "missing": prereqs["missing"]}))
        deployment["status"] = "running"
        deployment["health"] = "green"
        deployment["started_at"] = _now()
        deployment["updated_at"] = _now()
        self.repository.upsert("deployment", deployment)
        self.update_digital_twin_from_deployment(deployment)
        return deployment

    def pause_deployment(self, deployment_id: str) -> dict[str, Any]:
        return self.transition_deployment(deployment_id, "pause")

    def resume_deployment(self, deployment_id: str) -> dict[str, Any]:
        return self.transition_deployment(deployment_id, "resume")

    def verify_deployment(self, deployment_id: str) -> dict[str, Any]:
        return self.transition_deployment(deployment_id, "verify")

    def rollback_deployment(self, deployment_id: str, note: str = "", actor: str = "NovaID") -> dict[str, Any]:
        return self.transition_deployment(deployment_id, "rollback", note=note, actor=actor)

    def complete_deployment(self, deployment_id: str) -> dict[str, Any]:
        return self.transition_deployment(deployment_id, "complete")

    def marketplace_packages(self) -> list[dict[str, Any]]:
        return self.repository.list("marketplace_item")

    def marketplace_installations(self) -> list[dict[str, Any]]:
        return [item for item in self.marketplace_packages() if item.get("installed")]

    def install_marketplace_package(self, payload: dict[str, Any]) -> dict[str, Any]:
        package_id = str(payload["package_id"])
        package = self.repository.get("marketplace_item", package_id)
        if package is None:
            package = {
                "id": package_id,
                "name": package_id.replace("-", " ").title(),
                "category": str(payload.get("category") or "solution"),
                "version": str(payload.get("version") or "2027.1.0"),
                "installed": False,
                "tenant_id": self._tenant_id(str(payload.get("tenant_id") or "")),
                "region": str(payload.get("region") or "Australia"),
                "permissions": list(payload.get("permissions") or []),
                "signature": str(payload.get("signature") or "sigstore-reference"),
                "checksum": str(payload.get("checksum") or _new_id("checksum")),
                "publisher": str(payload.get("publisher") or "NovaTech"),
                "created_at": _now(),
                "updated_at": _now(),
            }
        if str(payload.get("signature") or package.get("signature") or "").startswith("invalid"):
            raise ValueError("invalid_signature")
        package["installed"] = True
        package["installed_at"] = _now()
        package["updated_at"] = _now()
        self.repository.upsert("marketplace_item", package)
        self.repository.append_event(
            _event_envelope(
                event_type="marketplace.installed",
                actor_type="user",
                actor_id="NovaID",
                tenant_id=package["tenant_id"],
                organization_id=package["tenant_id"],
                project_id=None,
                workflow_id=None,
                correlation_id=package["id"],
                causation_id=package["id"],
                data=package,
            )
        )
        return package

    def uninstall_marketplace_package(self, package_id: str) -> dict[str, Any]:
        package = self.repository.get("marketplace_item", package_id)
        if package is None:
            raise KeyError("marketplace_package_not_found")
        package["installed"] = False
        package["updated_at"] = _now()
        self.repository.upsert("marketplace_item", package)
        return package

    def operations_health(self) -> dict[str, Any]:
        incidents = self.operations_incidents()
        deployments = self.deployments()
        unhealthy = sum(1 for item in deployments if str(item.get("health") or "").lower() in {"amber", "red"})
        return {
            "status": "healthy" if not incidents or all(str(item.get("status") or "").lower() == "closed" for item in incidents) else "degraded",
            "incident_count": len(incidents),
            "open_incident_count": sum(1 for item in incidents if str(item.get("status") or "").lower() != "closed"),
            "deployment_count": len(deployments),
            "degraded_deployment_count": unhealthy,
            "updated_at": _now(),
        }

    def operations_metrics(self) -> dict[str, Any]:
        workflows = self.workflows()
        releases = self.releases()
        deployments = self.deployments()
        approvals = self.approvals()
        return {
            "workflow_duration_seconds_p50": 42,
            "agent_executions_total": len(self.agent_executions()),
            "approval_wait_seconds_p95": 180,
            "release_success_total": sum(1 for item in releases if str(item.get("status") or "").lower() in {"signed", "published", "release_ready", "healthy"}),
            "deployment_failures_total": sum(1 for item in deployments if str(item.get("status") or "").lower() == "failed"),
            "approval_count": len(approvals),
            "workflow_count": len(workflows),
            "timestamp": _now(),
        }

    def operations_incidents(self) -> list[dict[str, Any]]:
        return self.repository.list("operation_record")

    def create_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        incident = {
            "id": str(payload.get("id") or _new_id("incident")),
            "title": str(payload.get("title") or "NovaCodePro Incident"),
            "severity": str(payload.get("severity") or "medium"),
            "status": str(payload.get("status") or "open"),
            "service": str(payload.get("service") or "NovaCodePro Gateway"),
            "region": str(payload.get("region") or "Australia"),
            "details": dict(payload.get("details") or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("operation_record", incident)
        return incident

    def restore_backup(self, backup_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        incident = {
            "id": _new_id("restore"),
            "backup_id": backup_id,
            "status": "restoring",
            "snapshot": str((payload or {}).get("snapshot") or ""),
            "requested_by": str((payload or {}).get("requested_by") or "NovaID"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.append_event(
            _event_envelope(
                event_type="backup.restore.requested",
                actor_type="user",
                actor_id=incident["requested_by"],
                tenant_id=self._tenant_id(str((payload or {}).get("tenant_id") or "")),
                organization_id=self._tenant_id(str((payload or {}).get("tenant_id") or "")),
                project_id=None,
                workflow_id=None,
                correlation_id=incident["id"],
                causation_id=incident["id"],
                data=incident,
            )
        )
        return incident

    def create_briefing(self, payload: dict[str, Any]) -> dict[str, Any]:
        briefing = {
            "id": str(payload.get("id") or _new_id("briefing")),
            "subject": str(payload.get("subject") or "NovaCodePro executive briefing"),
            "summary": str(payload.get("summary") or ""),
            "recommendations": list(payload.get("recommendations") or []),
            "scorecard": dict(payload.get("scorecard") or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.upsert("executive_briefing", briefing)
        return briefing

    def briefings(self) -> list[dict[str, Any]]:
        return self.repository.list("executive_briefing")

    def command_center(self) -> dict[str, Any]:
        status = self.status()
        health = self.operations_health()
        risk_list = self.risks()
        event_bus = self.event_bus_snapshot()
        return {
            "enterprise_health": 96,
            "trust_score": 94,
            "risk_score": max((item.get("score") or 0) for item in risk_list) if risk_list else 0,
            "security_score": 92,
            "compliance_score": 98,
            "delivery_score": 91,
            "operations": health,
            "status": status,
            "event_bus": event_bus,
            "plane_model": self.neaf_manifest(),
            "reference_architecture": self.nera_manifest(),
            "eros": self.eros_manifest(),
            "architecture_framework": self.architecture_framework(),
            "latest_briefing": self.briefings()[0] if self.briefings() else None,
            "incident_count": health["incident_count"],
            "pending_approval_count": status.get("approval_count", 0),
        }

    def command_center_refresh(self) -> dict[str, Any]:
        snapshot = self.command_center()
        event_id = _new_id("command")
        self.repository.append_event(
            _event_envelope(
                event_type="command_center.refreshed",
                actor_type="service",
                actor_id="command-service",
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=None,
                workflow_id=None,
                correlation_id=event_id,
                causation_id=event_id,
                data=snapshot,
            )
        )
        return snapshot

    def status(self) -> dict[str, Any]:
        services = self.service_registry()
        tenants = self.tenants()
        projects = self.projects()
        workflows = self.workflows()
        releases = self.releases()
        artifacts = self.artifacts()
        solutions = self.solutions()
        agents = self.agent_executions()
        agent_registry = self.agents()
        approvals = self.approvals()
        deployments = self.deployments()
        twins = self.digital_twins()
        threads = self.collaboration_threads()
        integrations = self.integrations()
        evidence_bundles = self.evidence_bundles()
        risks = self.risks()
        policies = self._policy_rules()
        incidents = self.operations_incidents()
        briefings = self.briefings()
        federations = self.federation_agreements()
        board_meetings = self.repository.list("board_meeting")
        board_resolutions = self.repository.list("board_resolution")
        slis = self.repository.list("sli_record")
        slots = self.repository.list("slo_record")
        chaos = self.repository.list("chaos_experiment")
        topics = self.repository.list("event_topic")
        schemas = self.repository.list("event_schema")
        replays = self.repository.list("event_replay")
        simulations = self.repository.list("twin_simulation")
        event_bus = self.event_bus_snapshot()
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
            "agent_registry_count": len(agent_registry),
            "approval_count": len(approvals),
            "deployment_count": len(deployments),
            "digital_twin_count": len(twins),
            "thread_count": len(threads),
            "integration_count": len(integrations),
            "evidence_bundle_count": len(evidence_bundles),
            "risk_count": len(risks),
            "policy_count": len(policies),
            "incident_count": len(incidents),
            "briefing_count": len(briefings),
            "federation_count": len(federations),
            "board_meeting_count": len(board_meetings),
            "board_resolution_count": len(board_resolutions),
            "sli_count": len(slis),
            "slo_count": len(slots),
            "chaos_experiment_count": len(chaos),
            "event_topic_count": len(topics),
            "event_schema_count": len(schemas),
            "event_replay_count": len(replays),
            "twin_simulation_count": len(simulations),
            "retry_queue_count": event_bus["retry_queue"],
            "dead_letter_queue_count": event_bus["dead_letter_queue"],
            "nera_layer_count": len(self.nera_manifest()["layers"]),
            "plane_count": len(self.neaf_manifest()["planes"]),
            "architecture_model_count": len(self.architecture_framework()["models"]),
            "eros_core_views": len(self.eros_manifest()["core_views"]),
            "main_twin_resilience_score": self.digital_twin_summary().get("scores", {}).get("enterprise_resilience_score", 0),
            "connected_integration_count": sum(1 for item in integrations if item.get("status") == "connected"),
            "audit_event_count": len(self.audit(limit=500)),
            "domain_event_count": len(self.events(limit=500)),
            "marketplace_count": len(self.marketplace()["agents"]),
            "automation_ready": True,
            "command_center_ready": True,
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
                "Federation Service",
                "Graph Fabric",
                "Digital Twin Fabric",
                "Evidence Fabric",
                "Risk Fabric",
                "Approval Fabric",
                "SRE Fabric",
                "Audit Fabric",
                "Executive AI Council",
                "Board Governance Fabric",
                "Global Command Center",
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
        async_mode = str(
            payload.get("async_mode")
            or getattr(self, "default_agent_async_execution", False)
            or os.environ.get("NOVACODEPRO_AGENT_ASYNC_EXECUTION")
            or os.environ.get("NOVACODEPRO_ASYNC_EXECUTION")
            or "false"
        ).lower() in {"1", "true", "yes", "on"}
        execution = {
            "id": _new_id("agent-execution"),
            "agent_id": str(payload["agent_id"]),
            "version": str(payload.get("version") or "2027.1.0"),
            "category": str(payload.get("category") or "general"),
            "tenant_id": tenant_id,
            "project_id": project_id,
            "workflow_id": workflow_id,
            "stage_id": str(payload.get("stage_id") or "intake"),
            "status": "queued" if async_mode else "completed",
            "input": dict(payload.get("input") or {}),
            "output": dict(payload.get("output") or ({} if async_mode else {"result": "completed"})),
            "allowed_tools": list(payload.get("allowed_tools") or []),
            "forbidden_tools": list(payload.get("forbidden_tools") or []),
            "timeout_seconds": int(payload.get("timeout_seconds") or 900),
            "maximum_cost": float(payload.get("maximum_cost") or 0.0),
            "approval_policy": str(payload.get("approval_policy") or "standard"),
            "evidence": list(payload.get("evidence") or []),
            "logs": [
                {
                    "at": _now(),
                    "message": "Agent execution queued in the asynchronous backend." if async_mode else "Agent execution completed through the orchestrated backend.",
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
        if async_mode:
            self.repository.append_event(
                _event_envelope(
                    event_type="agent.execution.queued",
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
            return execution
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

    def complete_agent_execution(self, execution_id: str, *, output: dict[str, Any] | None = None, actor: str = "agent-worker") -> dict[str, Any]:
        execution = self.repository.get("agent_execution", execution_id)
        if execution is None:
            raise KeyError("agent_execution_not_found")
        execution["status"] = "completed"
        if output is not None:
            execution["output"] = dict(output)
        execution.setdefault("logs", [])
        execution["logs"] = [
            {"at": _now(), "message": "Agent execution completed by async worker."},
            *list(execution["logs"]),
        ]
        execution["completed_at"] = _now()
        execution["updated_at"] = _now()
        self.repository.upsert("agent_execution", execution)
        self.repository.append_event(
            _event_envelope(
                event_type="agent.execution.completed",
                actor_type="service",
                actor_id=actor,
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
        return execution

    def pending_agent_executions(self, limit: int = 25) -> list[dict[str, Any]]:
        return [
            execution
            for execution in self.agent_executions()
            if str(execution.get("status") or "").lower() in {"queued", "running"}
        ][:limit]

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
        if str(approval.get("requested_by") or "") == actor and decision == "approve":
            raise PermissionError("segregation_of_duties_violation")
        votes = list(approval.get("votes") or [])
        votes.append(
            {
                "subject_id": actor,
                "decision": "APPROVE" if decision == "approve" else "REJECT",
                "role": "APPROVER",
                "decided_at": _now(),
                "note": note,
            }
        )
        approval["votes"] = votes
        required_quorum = int(approval.get("required_quorum") or approval.get("quorum") or 1)
        approval["required_quorum"] = required_quorum
        approved_votes = [vote for vote in votes if vote.get("decision") == "APPROVE"]
        if decision == "reject":
            approval["status"] = "REJECTED"
        elif len(approved_votes) >= required_quorum:
            approval["status"] = "APPROVED"
        else:
            approval["status"] = "PARTIALLY_APPROVED"
        approval["approved_by"] = actor
        approval["decided_at"] = _now()
        approval["decision"] = decision
        approval["signature"] = self._payload_hash(
            {
                "approval_id": approval["id"],
                "subject_hash": approval.get("subject_hash", ""),
                "votes": votes,
                "status": approval["status"],
            }
        )
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

    def verify_approval_integrity(self, approval_id: str, plan: dict[str, Any], actor_authorities: dict[str, set[str]] | None = None) -> dict[str, Any]:
        approval = self.repository.get("approval", approval_id)
        if approval is None:
            raise KeyError("approval_not_found")
        if str(approval.get("status") or "") != "APPROVED":
            raise PermissionError("approval_not_approved")
        if approval.get("consumed_at") and not approval.get("reusable"):
            raise PermissionError("approval_already_consumed")
        expires_at = str(approval.get("expires_at") or "")
        if expires_at and expires_at <= _now():
            raise PermissionError("approval_expired")
        expected_hash = str(approval.get("subject_hash") or "")
        current_hash = f"sha256:{self._payload_hash(plan)}"
        if expected_hash and current_hash != expected_hash:
            raise PermissionError("approved_subject_changed")
        votes = [vote for vote in list(approval.get("votes") or []) if vote.get("decision") == "APPROVE"]
        authorities = actor_authorities or {str(vote.get("subject_id")): {str(vote.get("role") or "APPROVER")} for vote in votes}
        valid_votes = [
            vote
            for vote in votes
            if str(vote.get("role") or "APPROVER") in authorities.get(str(vote.get("subject_id")), set())
        ]
        if len(valid_votes) < int(approval.get("required_quorum") or 1):
            raise PermissionError("approval_quorum_not_met")
        requester_id = str(approval.get("requested_by") or "")
        if any(str(vote.get("subject_id") or "") == requester_id for vote in valid_votes):
            raise PermissionError("segregation_of_duties_violation")
        unsatisfied = [
            condition
            for condition in list(approval.get("conditions") or [])
            if isinstance(condition, dict) and condition.get("status") not in {None, "SATISFIED"}
        ]
        if unsatisfied:
            raise PermissionError("approval_conditions_unsatisfied")
        return {"approval_id": approval_id, "verified": True, "valid_votes": len(valid_votes), "subject_hash": expected_hash}

    def consume_approval(self, approval_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        result = self.verify_approval_integrity(approval_id, plan)
        approval = self.repository.get("approval", approval_id)
        if approval is None:
            raise KeyError("approval_not_found")
        approval["status"] = "CONSUMED"
        approval["consumed_at"] = _now()
        approval["updated_at"] = _now()
        self.repository.upsert("approval", approval)
        return {**result, "status": "CONSUMED"}

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
            if "identity" not in twin or "state" not in twin or "resilience" not in twin:
                return self._normalize_digital_twin(twin)
            return twin
        twin = self.create_digital_twin(
            {
                "id": target_id,
                "name": "NovaCodePro Twin",
                "type": "PLATFORM",
                "kind": "solution",
                "owner": "NovaCodePro",
                "tenant_id": self.tenants()[0]["id"],
                "classification": "INTERNAL",
                "jurisdiction": "AU",
                "status": "healthy",
                "region": "Australia",
                "children": [],
                "sources": ["service-registry", "event-bus", "knowledge-graph"],
                "controls": ["NovaPolicy", "NovaRisk", "NovaCompliance", "NovaAudit"],
                "metrics": {
                    "availability": 1.0,
                    "latency_p95_ms": 120,
                    "error_rate": 0.0,
                    "risk_score": 18,
                },
                "observed_state": "HEALTHY",
                "desired_state": "AVAILABLE",
                "predicted_state": "STABLE",
                "simulated_state": "NOT_RUN",
                "approved_state": "APPROVED",
                "recovered_state": "HEALTHY",
                "summary": "NovaCodePro governed platform twin.",
                "topology": {"services": [service["name"] for service in self.service_registry()]},
                "relationships": [
                    {
                        "source": target_id,
                        "target": service["name"],
                        "type": "DEPENDS_ON",
                        "criticality": "MEDIUM",
                        "weight": 3.0,
                        "rto": "30m",
                        "rpo": "5m",
                        "recovery_difficulty": 2.0,
                        "confidence": 0.92,
                    }
                    for service in self.service_registry()[:3]
                ],
                "evidence": ["governance-approval", "service-registry"],
                "lineage": ["workflow-ride-platform"],
                "resilience": {
                    "twin_fidelity_score": 82,
                    "dependency_confidence_score": 92,
                    "simulation_confidence_score": 86,
                    "recovery_confidence_score": 88,
                    "enterprise_resilience_score": 88,
                },
                "recovery": {
                    "status": "READY",
                    "workflow": {
                        "id": "recovery-plan-default",
                        "scenario": "regional_outage",
                        "expected_rto": "30m",
                        "expected_rpo": "5m",
                        "steps": ["verify_failure", "activate_replica", "switch_traffic", "validate_health", "capture_evidence"],
                    },
                },
            }
        )
        return twin

    def digital_twin_health(self, twin_id: str | None = None) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        return {
            "id": twin["id"],
            "status": twin["status"],
            "health": twin.get("metrics") or twin.get("health") or {},
            "region": twin.get("region"),
            "updated_at": twin.get("updated_at"),
        }

    def digital_twin_topology(self, twin_id: str | None = None) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin(twin_id)
        services = list((twin.get("topology") or {}).get("services") or [])
        if not services and str(twin.get("id") or "") == "twin-novacodepro":
            services = [service["name"] for service in self.service_registry()]
        return {
            "id": twin["id"],
            "name": twin["name"],
            "kind": twin.get("kind") or twin.get("type"),
            "children": list(twin.get("children") or []),
            "services": services,
            "relationships": list(twin.get("relationships") or []),
        }

    def update_digital_twin_from_deployment(self, deployment: dict[str, Any]) -> dict[str, Any]:
        twin = self.get_or_create_digital_twin()
        twins = list(twin.get("children") or [])
        if deployment["id"] not in twins:
            twins.append(deployment["id"])
        twin["children"] = twins
        twin["status"] = "healthy" if deployment.get("health") in {"green", "healthy"} else "degraded"
        metrics = {
            "availability": deployment.get("metrics", {}).get("availability", 1.0),
            "latency_p95_ms": deployment.get("metrics", {}).get("latency_p95_ms", 120),
            "error_rate": deployment.get("metrics", {}).get("error_rate", 0.0),
            "risk_score": deployment.get("metrics", {}).get("risk_score", 18),
        }
        twin["metrics"] = metrics
        twin["observed_state"] = "HEALTHY" if twin["status"] == "healthy" else "DEGRADED"
        twin["predicted_state"] = "STABLE" if twin["status"] == "healthy" else "AT_RISK"
        twin["state"] = {
            **dict(twin.get("state") or {}),
            "observed": {
                "label": "Observed State",
                "status": twin["observed_state"],
                "detail": "Deployment telemetry updated the twin.",
                "evidence": [deployment["id"]],
            },
            "predicted": {
                "label": "Predicted State",
                "status": twin["predicted_state"],
                "detail": "Deployment posture recalculated from the latest rollout.",
                "evidence": [deployment["id"]],
            },
        }
        twin["resilience"] = derive_resilience_scores(twin)
        twin["scores"] = dict(twin["resilience"])
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
                data={"twin_id": twin["id"], "deployment_id": deployment["id"], "metrics": twin["metrics"], "status": twin["status"]},
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

    def ux_operating_system(self) -> dict[str, Any]:
        return ux_operating_system_summary()

    def uxos_operational_status(self) -> dict[str, Any]:
        records = {
            kind: self.repository.list(kind)
            for kind in (
                "ux_design_sync",
                "ux_visual_regression",
                "ux_accessibility_scan",
                "ux_analytics_event",
                "ux_experiment",
                "ux_knowledge_edge",
                "ux_digital_twin_simulation",
            )
        }
        return {
            **uxos_operational_completion_matrix(),
            "record_counts": {kind: len(items) for kind, items in records.items()},
            "latest_records": {kind: items[:3] for kind, items in records.items()},
        }

    def ux_artifacts(self) -> list[dict[str, Any]]:
        return self.repository.list("ux_artifact")

    def create_ux_artifact(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        artifact = build_ux_artifact_record(payload, now, _new_id("uxart"))
        artifact = sign_ux_record(artifact)
        self.repository.upsert("ux_artifact", artifact)
        self.repository.append_audit(
            kind="ux",
            actor=str(payload.get("actor") or "NovaCodePro"),
            service="UX Governance Center",
            subject=artifact["artifact"],
            action="ux.artifact.created",
            evidence=artifact["digital_signature"],
            detail="Versioned UX artifact stored with traceability and governance metadata.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="ux.artifact.created",
                actor_type="service",
                actor_id="ux-governance-center",
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=str(payload.get("project_id") or ""),
                workflow_id=str(payload.get("workflow_id") or ""),
                correlation_id=artifact["id"],
                causation_id=artifact["id"],
                data={"artifact_id": artifact["id"], "artifact_type": artifact["artifact_type"], "state": artifact["approval_state"]},
            )
        )
        return artifact

    def transition_ux_artifact(self, artifact_id: str, target_state: str, actor: str = "NovaID", note: str = "") -> dict[str, Any]:
        artifact = self.repository.get("ux_artifact", artifact_id)
        if artifact is None:
            raise KeyError("ux_artifact_not_found")
        validation = validate_ux_state_transition(str(artifact.get("approval_state") or "DRAFT"), target_state)
        if not validation["valid"]:
            raise ValueError(str(validation["reason"]))
        now = _now()
        artifact["approval_state"] = target_state
        artifact["status"] = target_state
        artifact["history"] = [
            {
                "at": now,
                "action": "ux_artifact.transitioned",
                "state": target_state,
                "actor": actor,
                "note": note,
            },
            *list(artifact.get("history") or []),
        ]
        artifact["updated_at"] = now
        artifact = sign_ux_record(artifact)
        self.repository.upsert("ux_artifact", artifact)
        self.repository.append_audit(
            kind="ux",
            actor=actor,
            service="UX Governance Center",
            subject=artifact["artifact"],
            action="ux.artifact.transitioned",
            evidence=artifact["digital_signature"],
            detail=f"UX artifact moved to {target_state}.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type="ux.artifact.transitioned",
                actor_type="user",
                actor_id=actor,
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id="",
                workflow_id="",
                correlation_id=artifact_id,
                causation_id=artifact_id,
                data={"artifact_id": artifact_id, "state": target_state, "note": note},
            )
        )
        return artifact

    def attach_ux_evidence(self, artifact_id: str, evidence_refs: list[str], actor: str = "NovaTrust") -> dict[str, Any]:
        artifact = self.repository.get("ux_artifact", artifact_id)
        if artifact is None:
            raise KeyError("ux_artifact_not_found")
        refs = list(dict.fromkeys([*list(artifact.get("evidence") or []), *evidence_refs]))
        artifact["evidence"] = refs
        artifact["history"] = [
            {
                "at": _now(),
                "action": "ux_artifact.evidence_attached",
                "state": artifact.get("approval_state") or "DRAFT",
                "actor": actor,
                "evidence_refs": evidence_refs,
            },
            *list(artifact.get("history") or []),
        ]
        artifact["updated_at"] = _now()
        artifact = sign_ux_record(artifact)
        package = build_ux_evidence_package(artifact, refs, _now(), _new_id("uxevidence"))
        self.repository.upsert("ux_artifact", artifact)
        self.repository.upsert("ux_evidence_package", package)
        self.repository.append_audit(
            kind="ux",
            actor=actor,
            service="Evidence Studio",
            subject=artifact["artifact"],
            action="ux.evidence.attached",
            evidence=package["digital_signature"],
            detail="UX evidence package generated and linked to artifact traceability.",
        )
        return {"artifact": artifact, "evidence_package": package}

    def ux_release_readiness(self) -> dict[str, Any]:
        artifacts = self.ux_artifacts()
        assessment = assess_ux_release_readiness(artifacts)
        release = {
            "id": _new_id("uxrel"),
            "status": assessment["status"],
            "complete": assessment["complete"],
            "artifact_count": len(artifacts),
            "assessment": assessment,
            "created_at": _now(),
            "updated_at": _now(),
        }
        release["digital_signature"] = sign_ux_record(release)["digital_signature"]
        self.repository.upsert("ux_release_readiness", release)
        self.repository.append_audit(
            kind="ux",
            actor="NovaCodePro",
            service="UX Verification Center",
            subject="Production UX release readiness",
            action="ux.release.assessed",
            evidence=release["digital_signature"],
            detail="Production UX release readiness assessed against traceability, evidence, and governance gates.",
        )
        return release

    def create_uxos_service_record(self, kind: str, payload: dict[str, Any], actor: str = "NovaCodePro") -> dict[str, Any]:
        record = build_uxos_service_record(kind, payload, _now(), _new_id(kind.replace("ux_", "uxos")))
        self.repository.upsert(kind, record)
        self.repository.append_audit(
            kind="uxos",
            actor=actor,
            service=str(payload.get("service") or "UXOS Service Fabric"),
            subject=record["subject"],
            action=f"{kind}.recorded",
            evidence=record["digital_signature"],
            detail="UXOS service record captured; operational completion remains pending until live evidence is verified.",
        )
        self.repository.append_event(
            _event_envelope(
                event_type=f"{kind}.recorded",
                actor_type="service",
                actor_id=str(payload.get("service") or "uxos-service-fabric"),
                tenant_id=self.tenants()[0]["id"],
                organization_id=self.tenants()[0]["id"],
                project_id=str(payload.get("project_id") or ""),
                workflow_id=str(payload.get("workflow_id") or ""),
                correlation_id=record["id"],
                causation_id=record["id"],
                data={"record_id": record["id"], "record_type": kind, "status": record["status"]},
            )
        )
        return record

    def create_ux_design_sync(self, payload: dict[str, Any], actor: str = "NovaCodePro") -> dict[str, Any]:
        data = {
            "service": "Design Integration Service",
            "status": "SYNC_CONFIGURED_EVIDENCE_PENDING",
            **payload,
        }
        return self.create_uxos_service_record("ux_design_sync", data, actor=actor)

    def create_ux_visual_regression(self, payload: dict[str, Any], actor: str = "NovaCodePro") -> dict[str, Any]:
        data = {
            "service": "Visual Regression Service",
            "status": "COMPARISON_RECORDED_BASELINE_APPROVAL_PENDING",
            **payload,
        }
        return self.create_uxos_service_record("ux_visual_regression", data, actor=actor)

    def create_ux_accessibility_scan(self, payload: dict[str, Any], actor: str = "NovaCodePro") -> dict[str, Any]:
        data = {
            "service": "Accessibility Service",
            "status": "SCAN_RECORDED_RELEASE_APPROVAL_PENDING",
            **payload,
        }
        return self.create_uxos_service_record("ux_accessibility_scan", data, actor=actor)

    def record_ux_analytics_event(self, payload: dict[str, Any], actor: str = "NovaCodePro") -> dict[str, Any]:
        data = {
            "service": "Analytics Service",
            "status": "TELEMETRY_RECORDED_PRODUCTION_VALIDATION_PENDING",
            **payload,
        }
        return self.create_uxos_service_record("ux_analytics_event", data, actor=actor)

    def create_ux_experiment(self, payload: dict[str, Any], actor: str = "NovaCodePro") -> dict[str, Any]:
        data = {
            "service": "Experiment Service",
            "status": "EXPERIMENT_DRAFT_APPROVAL_PENDING",
            **payload,
        }
        return self.create_uxos_service_record("ux_experiment", data, actor=actor)

    def create_ux_knowledge_edge(self, payload: dict[str, Any], actor: str = "NovaCodePro") -> dict[str, Any]:
        data = {
            "service": "Knowledge Graph Service",
            "status": "EDGE_RECORDED_GRAPH_POPULATION_PENDING",
            **payload,
        }
        return self.create_uxos_service_record("ux_knowledge_edge", data, actor=actor)

    def create_ux_digital_twin_simulation(self, payload: dict[str, Any], actor: str = "NovaCodePro") -> dict[str, Any]:
        data = {
            "service": "Digital Twin Service",
            "status": "SIMULATION_RECORDED_PRODUCTION_TELEMETRY_PENDING",
            **payload,
        }
        return self.create_uxos_service_record("ux_digital_twin_simulation", data, actor=actor)

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

    def agent_registry_catalog(self) -> list[dict[str, Any]]:
        registry = self.agents()
        return registry if registry else default_agent_registry()

    def orchestrate_solution_package(self, payload: dict[str, Any]) -> dict[str, Any]:
        solution = self.create_solution(
            {
                "title": str(payload.get("title") or payload.get("request") or "Enterprise solution"),
                "request": str(payload.get("request") or payload.get("title") or "Enterprise solution"),
                "tenant_id": payload.get("tenant_id"),
                "project_id": payload.get("project_id"),
                "template_id": payload.get("template_id") or "solution-factory",
                "domain": payload.get("domain") or "general",
                "region": payload.get("region") or "Australia",
                "compliance": payload.get("compliance") or "enterprise",
                "surfaces": list(payload.get("surfaces") or []),
                "version": str(payload.get("version") or "1"),
            }
        )
        workflow = self.get_workflow(solution["workflow_id"]) or {
            "id": solution["workflow_id"],
            "title": solution["title"],
            "request": solution["request"],
        }
        package = build_solution_package(
            {
                **payload,
                "solution_id": solution["id"],
                "workflow_id": solution["workflow_id"],
                "project_id": solution["project_id"],
                "version": solution["version"],
            },
            registry=default_agent_registry(),
        )
        package["solution"] = solution
        package["workflow"] = workflow
        package["approval"] = {
            **package["approval"],
            "workflow_id": solution["workflow_id"],
            "release_id": str(payload.get("release_id") or ""),
        }
        self.repository.upsert("approval", package["approval"])
        self.repository.append_event(
            _event_envelope(
                event_type="approval.requested",
                actor_type="user",
                actor_id=str(payload.get("requested_by") or "NovaAI"),
                tenant_id=solution["tenant_id"],
                organization_id=solution["tenant_id"],
                project_id=solution["project_id"],
                workflow_id=solution["workflow_id"],
                correlation_id=solution["id"],
                causation_id=solution["id"],
                data={"approval_id": package["approval"]["id"], "solution_id": solution["id"]},
            )
        )
        if str(package["approval"].get("status") or "").upper() == "APPROVED":
            package["knowledge_entry"] = self.publish_knowledge_from_approval(solution["id"], package["approval"]["id"])
        for event in package["events"]:
            self.repository.append_event(
                _event_envelope(
                    event_type=str(event["event_type"]),
                    actor_type="service",
                    actor_id=str(event.get("actor") or "NovaAI"),
                    tenant_id=solution["tenant_id"],
                    organization_id=solution["tenant_id"],
                    project_id=solution["project_id"],
                    workflow_id=solution["workflow_id"],
                    correlation_id=solution["id"],
                    causation_id=solution["id"],
                    data={"event_id": event["event_id"], **dict(event.get("payload") or {})},
                )
            )
        return package

    def publish_knowledge_from_approval(self, solution_id: str, approval_id: str, *, previous_version: str = "") -> dict[str, Any]:
        solution = self.get_solution(solution_id)
        approval = self.get_approval(approval_id)
        if solution is None:
            raise KeyError("solution_not_found")
        if approval is None:
            raise KeyError("approval_not_found")
        if str(approval.get("status") or "").upper() != "APPROVED":
            raise ValueError("approval_not_approved")
        knowledge = build_knowledge_entry(
            solution=solution,
            approval=approval,
            previous_version=previous_version,
            evidence_ids=list(approval.get("evidence_ids") or []),
        )
        self.repository.upsert(
            "knowledge_node",
            {
                "id": knowledge["id"],
                "label": knowledge["title"],
                "type": knowledge["type"],
                "domain": "Knowledge Graph",
                "owner": "NovaCodePro",
                "evidence": knowledge["evidence_ids"],
                "links": list(knowledge["links"]),
                "solution_id": knowledge["solution_id"],
                "approval_id": knowledge["approval_id"],
                "version": knowledge["version"],
                "status": knowledge["status"],
                "approved": knowledge["approved"],
                "previous_version": knowledge["previous_version"],
                "hash": knowledge["hash"],
                "created_at": knowledge["created_at"],
                "updated_at": knowledge["updated_at"],
            },
        )
        self.repository.append_event(
            _event_envelope(
                event_type="knowledge.entry.promoted",
                actor_type="service",
                actor_id="knowledge-graph-service",
                tenant_id=str(solution.get("tenant_id") or self.tenants()[0]["id"]),
                organization_id=str(solution.get("tenant_id") or self.tenants()[0]["id"]),
                project_id=str(solution.get("project_id") or "") or None,
                workflow_id=str(solution.get("workflow_id") or "") or None,
                correlation_id=solution_id,
                causation_id=approval_id,
                data={
                    "knowledge_id": knowledge["id"],
                    "solution_id": solution_id,
                    "approval_id": approval_id,
                    "version": knowledge["version"],
                },
            )
        )
        return knowledge

    def replay_knowledge_graph(self, limit: int = 500) -> list[dict[str, Any]]:
        events = self.events(limit=limit)
        projection = knowledge_projection(events)
        for node in projection:
            self.repository.upsert(
                "knowledge_node",
                {
                    "id": node["id"],
                    "label": node["id"],
                    "type": "approved-solution",
                    "domain": "Knowledge Graph",
                    "owner": "NovaCodePro",
                    "evidence": [],
                    "links": list(node.get("links") or []),
                    "solution_id": node.get("solution_id"),
                    "approval_id": node.get("approval_id"),
                    "version": node.get("version") or 1,
                    "status": node.get("status") or "APPROVED",
                    "approved": True,
                    "created_at": _now(),
                    "updated_at": _now(),
                },
            )
        if events:
            self.repository.save_projection_checkpoint("knowledge_graph", str(events[0]["event_id"]))
        return projection

    def event_bus_snapshot(self) -> dict[str, Any]:
        return {
            "domain_events": len(self.events(limit=1000)),
            "outbox_pending": len(self.repository.list_outbox(limit=1000, status="pending")),
            "retry_queue": len(self.repository.list_retry_queue()),
            "dead_letter_queue": len(self.repository.list_dead_letter_queue()),
            "projection_checkpoints": [
                self.repository.get_projection_checkpoint("knowledge_graph"),
            ],
        }

    def operating_fabric(self) -> EnterpriseOperatingFabric:
        return EnterpriseOperatingFabric(self)

    def operating_fabric_manifest(self) -> dict[str, Any]:
        return self.operating_fabric().manifest()

    def enterprise_objects(self) -> list[dict[str, Any]]:
        return self.operating_fabric().enterprise_objects()

    def enterprise_capabilities(self) -> list[dict[str, Any]]:
        return self.operating_fabric().capability_registry()

    def submit_enterprise_request(
        self,
        payload: dict[str, Any],
        *,
        context: EnterpriseExecutionContext | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return self.operating_fabric().submit_enterprise_request(payload, context=context, idempotency_key=idempotency_key)

    def enterprise_relationships(self) -> list[dict[str, Any]]:
        return self.repository.list("enterprise_relationship")

    def enterprise_command_center(self) -> dict[str, Any]:
        return self.operating_fabric().command_center()

    def normalize_authority_role(self, role: str) -> dict[str, Any]:
        return {"input": role, "canonical_role": normalize_role(role)}

    def sovereign_maturity_report(self) -> dict[str, Any]:
        production_dependencies = validate_production_dependencies()
        outbox = self.repository.list_outbox(limit=1000, status=None)
        evidence = self.evidence_bundles()
        relationships = self.enterprise_relationships()
        workflows = self.workflows()
        development_verified = [item for item in evidence if item.get("verification_status") == "DEVELOPMENT_VERIFIED"]
        kms_verified = [item for item in evidence if item.get("verification_status") == "KMS_VERIFIED"]
        domains = [
            {
                "domain": "Trusted Execution Context",
                "level": "ENFORCED",
                "score": 8,
                "evidence": ["JWT-derived EnterpriseExecutionContext", "payload authority rejection tests"],
                "exceptions": ["NovaID membership lookup is simulated by JWT claims in local tests"],
            },
            {
                "domain": "Workflow Runtime",
                "level": "IMPLEMENTED",
                "score": 7,
                "evidence": [f"{len(workflows)} workflow records", "approval-first planning"],
                "exceptions": ["Temporal worker restart and deterministic replay not proven in this environment"]
                + (["Temporal target not configured"] if "NOVACODEPRO_TEMPORAL_TARGET" in production_dependencies["missing"] else []),
            },
            {
                "domain": "Event Fabric",
                "level": "INTEGRATED",
                "score": 7,
                "evidence": [f"{len(outbox)} outbox records", "domain event persistence"],
                "exceptions": ["Kafka/Redpanda broker failure, replay, and consumer lag proof not executed"]
                + (["Event brokers not configured"] if "NOVACODEPRO_EVENT_BROKERS" in production_dependencies["missing"] else []),
            },
            {
                "domain": "Cryptographic Evidence",
                "level": "AUTOMATED_CHECKED",
                "score": 7,
                "evidence": [f"{len(development_verified)} locally verified evidence bundles"],
                "exceptions": ["AWS KMS asymmetric signatures and S3 Object Lock are not configured locally"]
                + (
                    ["KMS signing key or immutable bucket missing"]
                    if {"NOVACODEPRO_EVIDENCE_KMS_KEY_ID", "NOVACODEPRO_EVIDENCE_BUCKET"} & set(production_dependencies["missing"])
                    else []
                ),
            },
            {
                "domain": "Typed Enterprise Graph",
                "level": "INTEGRATED",
                "score": 8,
                "evidence": [f"{len(relationships)} typed relationships"],
                "exceptions": ["Neo4j projection rebuild proof not executed"],
            },
            {
                "domain": "Independent Verification",
                "level": "UNASSESSED",
                "score": 4,
                "evidence": [f"{len(kms_verified)} KMS-verified evidence bundles"],
                "exceptions": ["Separate signer/verifier/audit roles require cloud deployment"],
            },
            {
                "domain": "Multi-Region Recovery",
                "level": "DOCUMENTED",
                "score": 5,
                "evidence": ["EROS and NERM manifests", "local twin/recovery APIs"],
                "exceptions": ["Route 53/Global Accelerator failover and failback evidence not available locally"],
            },
        ]
        overall_score = min(domain["score"] for domain in domains)
        return {
            "id": "novacodepro-sovereign-maturity",
            "status": "ADVANCED_IMPLEMENTATION_IN_PROGRESS",
            "score": overall_score,
            "as_of": _now(),
            "production_dependencies": production_dependencies,
            "scoring_rule": "A domain reaches 10 only when implemented, enforced, failure-tested, observable, recoverable, independently verified, and supported by immutable evidence.",
            "domains": domains,
        }

    def production_readiness(self, environment: str | None = None) -> dict[str, Any]:
        return validate_production_dependencies(environment)

    def nera_manifest(self) -> dict[str, Any]:
        return build_nera_manifest()

    def neaf_manifest(self) -> dict[str, Any]:
        return build_enterprise_plane_model()

    def eros_manifest(self) -> dict[str, Any]:
        return build_eros_manifest()

    def capability_model(self) -> dict[str, Any]:
        return build_enterprise_capability_model()

    def operating_model(self) -> dict[str, Any]:
        return build_enterprise_operating_model()

    def data_model(self) -> dict[str, Any]:
        return build_enterprise_data_architecture()

    def knowledge_model(self) -> dict[str, Any]:
        return build_enterprise_meta_model()

    def technology_model(self) -> dict[str, Any]:
        return build_enterprise_technology_model()

    def governance_model(self) -> dict[str, Any]:
        return build_enterprise_governance_model()

    def ai_model(self) -> dict[str, Any]:
        return build_enterprise_ai_architecture()

    def digital_twin_model(self) -> dict[str, Any]:
        return build_enterprise_digital_twin_model()

    def resilience_model(self) -> dict[str, Any]:
        return build_enterprise_resilience_model()

    def architecture_framework(self) -> dict[str, Any]:
        return build_enterprise_architecture_framework()


def get_novacodepro_platform(db_path: str | Path | None = None, database_url: str | None = None) -> NovaCodeProPlatform:
    path = Path(db_path or Path.cwd() / "var" / "novacodepro-platform.sqlite3")
    return NovaCodeProPlatform(NovaCodeProRepository(path, database_url=database_url))


__all__ = [
    "NovaCodeProPlatform",
    "NovaCodeProRepository",
    "get_novacodepro_platform",
    "validate_database_runtime",
]
