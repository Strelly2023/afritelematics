from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


DEMO_TENANT_ID = "tenant-novacodepro-enterprise-demo"
DEMO_ORGANIZATION_ID = "org-novatech-demo"
DEMO_REGION = "Australia"
DEMO_REALM = "novatech-enterprise-demo"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_id(prefix: str, suffix: str) -> str:
    return f"{prefix}-{suffix}"


def build_users() -> list[dict[str, Any]]:
    roles = [
        "ADMIN",
        "CTO",
        "CEO",
        "COO",
        "CFO",
        "CISO",
        "LEGAL",
        "RISK",
        "BOARD",
        "OPERATOR",
        "DEVELOPER",
    ]
    users: list[dict[str, Any]] = []
    for index in range(1, 30):
        role = roles[(index - 1) % len(roles)]
        users.append(
            {
                "id": f"demo-user-{index:02d}",
                "name": f"Demo User {index:02d}",
                "role": role,
                "tenant_id": DEMO_TENANT_ID,
                "organization_id": DEMO_ORGANIZATION_ID,
                "realm": DEMO_REALM,
                "active": True,
                "persona": role.lower(),
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
    return users


def build_roles() -> list[dict[str, Any]]:
    return [
        {"id": role.lower(), "name": role, "tenant_id": DEMO_TENANT_ID, "created_at": _now(), "updated_at": _now()}
        for role in ("ADMIN", "CTO", "CEO", "COO", "CFO", "CISO", "LEGAL", "RISK", "BOARD", "OPERATOR", "DEVELOPER", "OBSERVER", "VERIFIER", "SERVICE", "CUSTOMER")
    ]


def build_permissions() -> list[dict[str, Any]]:
    permissions = [
        "identity.read",
        "identity.write",
        "project.read",
        "project.write",
        "solution.read",
        "solution.write",
        "workflow.read",
        "workflow.write",
        "approval.read",
        "approval.write",
        "release.read",
        "release.write",
        "deployment.read",
        "deployment.write",
        "risk.read",
        "risk.write",
        "policy.read",
        "policy.write",
        "graph.read",
        "graph.write",
        "twin.read",
        "twin.simulate",
        "board.read",
        "board.write",
        "sre.read",
        "sre.write",
        "marketplace.read",
        "marketplace.install",
        "command_center.read",
        "evidence.read",
    ]
    return [
        {"id": perm.replace(".", "_"), "name": perm, "tenant_id": DEMO_TENANT_ID, "created_at": _now(), "updated_at": _now()}
        for perm in permissions
    ]


def build_projects() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-novaride",
            "name": "NovaRide",
            "tenant_id": DEMO_TENANT_ID,
            "status": "Active",
            "owner": "CTO Office",
            "solution": "Ride platform demo",
            "region": DEMO_REGION,
            "budget": "$1.4M",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-novapay",
            "name": "NovaPay",
            "tenant_id": DEMO_TENANT_ID,
            "status": "Review",
            "owner": "Payments Engineering",
            "solution": "Transfer platform demo",
            "region": DEMO_REGION,
            "budget": "$2.1M",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-novahealth",
            "name": "NovaHealth",
            "tenant_id": DEMO_TENANT_ID,
            "status": "Discovery",
            "owner": "Product Lab",
            "solution": "Care coordination demo",
            "region": DEMO_REGION,
            "budget": "$900K",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-partner-api",
            "name": "Partner API",
            "tenant_id": DEMO_TENANT_ID,
            "status": "Planning",
            "owner": "Platform Partnerships",
            "solution": "Partner integration demo",
            "region": DEMO_REGION,
            "budget": "$450K",
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]


def build_workflows() -> list[dict[str, Any]]:
    stages = ["intake", "analysis", "architecture", "design", "implementation", "testing", "approval", "release"]
    workflow_blueprint = [
        ("demo-workflow-01", "demo-novaride", "NovaRide rider experience modernization", "active"),
        ("demo-workflow-02", "demo-novapay", "NovaPay controlled expansion", "waiting-approval"),
        ("demo-workflow-03", "demo-novahealth", "NovaHealth care coordination rollout", "active"),
        ("demo-workflow-04", "demo-partner-api", "Partner API federation review", "waiting-approval"),
        ("demo-workflow-05", "demo-novaride", "NovaRide mobile operations hardening", "active"),
        ("demo-workflow-06", "demo-novapay", "NovaPay payment routing modernization", "testing"),
        ("demo-workflow-07", "demo-novahealth", "NovaHealth compliance evidence pack", "approval"),
        ("demo-workflow-08", "demo-partner-api", "Partner API trust agreement renewal", "release"),
    ]
    workflows: list[dict[str, Any]] = []
    for index, (workflow_id, project_id, title, status) in enumerate(workflow_blueprint, start=1):
        project = next(item for item in build_projects() if item["id"] == project_id)
        workflows.append(
            {
                "id": workflow_id,
                "tenant_id": DEMO_TENANT_ID,
                "project_id": project["id"],
                "title": title,
                "request": f"Demo request for {project['name']}",
                "template_id": "enterprise-demo",
                "domain": "enterprise",
                "region": DEMO_REGION,
                "compliance": "enterprise",
                "surfaces": stages,
                "stage_index": (index - 1) % len(stages),
                "status": status,
                "approvals": [],
                "artifacts": [],
                "history": [],
                "stages": [],
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
    return workflows


def build_risks() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-risk-01",
            "title": "Controlled pilot release delay",
            "likelihood": "medium",
            "impact": "high",
            "exposure": "high",
            "score": 18,
            "classification": "HIGH",
            "owner": "risk-team",
            "required_controls": ["security_approval", "rollback_plan"],
            "status": "open",
            "tenant_id": DEMO_TENANT_ID,
            "project_id": "demo-novapay",
            "workflow_id": "demo-workflow-02",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-risk-02",
            "title": "Regional failover capacity",
            "likelihood": "low",
            "impact": "high",
            "exposure": "medium",
            "score": 18,
            "classification": "HIGH",
            "owner": "sre-team",
            "required_controls": ["twin_simulation", "regional_approval"],
            "status": "open",
            "tenant_id": DEMO_TENANT_ID,
            "project_id": "demo-novaride",
            "workflow_id": "demo-workflow-01",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-risk-03",
            "title": "Partner API access drift",
            "likelihood": "medium",
            "impact": "medium",
            "exposure": "medium",
            "score": 27,
            "classification": "HIGH",
            "owner": "security-team",
            "required_controls": ["federation_agreement", "audit_access"],
            "status": "open",
            "tenant_id": DEMO_TENANT_ID,
            "project_id": "demo-partner-api",
            "workflow_id": "demo-workflow-04",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-risk-04",
            "title": "Executive briefing evidence lag",
            "likelihood": "low",
            "impact": "medium",
            "exposure": "medium",
            "score": 9,
            "classification": "MEDIUM",
            "owner": "governance-team",
            "required_controls": ["evidence_pack", "command_center_refresh"],
            "status": "open",
            "tenant_id": DEMO_TENANT_ID,
            "project_id": "demo-novahealth",
            "workflow_id": "demo-workflow-03",
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]


def build_approvals() -> list[dict[str, Any]]:
    approvals = []
    statuses = ["APPROVED", "PENDING", "REJECTED", "ESCALATED", "EXPIRED"]
    for index in range(1, 13):
        status = statuses[index % len(statuses)]
        approvals.append(
            {
                "id": f"demo-approval-{index:02d}",
                "gate_type": ["ARCHITECTURE_APPROVAL", "SECURITY_APPROVAL", "COMPLIANCE_APPROVAL", "RELEASE_APPROVAL"][index % 4],
                "workflow_id": f"demo-workflow-{((index - 1) % 8) + 1:02d}",
                "release_id": f"demo-release-{((index - 1) % 3) + 1:02d}",
                "status": status,
                "requested_by": "demo-requester",
                "approved_by": "demo-approver" if status == "APPROVED" else "",
                "requested_at": _now(),
                "decided_at": _now() if status == "APPROVED" else "",
                "decision": "approve" if status == "APPROVED" else "pending",
                "conditions": ["Demo environment only"],
                "evidence_ids": ["demo-evidence-01"],
                "signature": f"sig-demo-approval-{index:02d}",
                "audit_event_id": f"demo-audit-approval-{index:02d}",
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
    return approvals


def build_federation_agreements() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-federation-01",
            "provider_org": DEMO_ORGANIZATION_ID,
            "consumer_org": "org-partner-demo",
            "status": "ACTIVE",
            "trust_level": "VERIFIED",
            "allowed_capabilities": ["knowledge.read", "evidence.verify"],
            "denied_capabilities": ["production.deploy", "secret.export"],
            "allowed_regions": ["AU"],
            "data_classes": ["PUBLIC", "INTERNAL"],
            "purpose": "Partner demo review",
            "expires_at": "2027-07-01T00:00:00Z",
            "signature": "sig-demo-federation-01",
            "created_at": _now(),
            "updated_at": _now(),
        }
    ]


def build_board_workflows() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-board-meeting-01",
            "title": "Demo Board Meeting",
            "status": "DRAFT",
            "agenda": ["NovaPay East Africa Controlled Expansion"],
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-board-meeting-02",
            "title": "Demo Audit Review",
            "status": "DRAFT",
            "agenda": ["Enterprise demo governance posture"],
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]


def build_board_resolutions() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-board-resolution-01",
            "title": "Approve NovaPay East Africa Controlled Expansion",
            "meeting_id": "demo-board-meeting-01",
            "status": "APPROVED",
            "quorum": {"required": 3, "present": 4, "met": True},
            "votes": {"for": 3, "against": 0, "abstain": 1},
            "conditions": ["Complete regional compliance approval", "Maintain pilot transaction limits"],
            "evidence_ids": ["demo-board-evidence-01", "demo-risk-evidence-01"],
            "signature": "board-resolution-signature",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-board-resolution-02",
            "title": "Approve Demo Tenant Security Review",
            "meeting_id": "demo-board-meeting-02",
            "status": "PENDING",
            "quorum": {"required": 3, "present": 2, "met": False},
            "votes": {"for": 1, "against": 0, "abstain": 1},
            "conditions": ["Security evidence pack complete"],
            "evidence_ids": ["demo-board-evidence-02"],
            "signature": "",
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]


def build_twin_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-twin-scenario-01",
            "twin_id": "twin-novacodepro-demo",
            "scenario": "Australia Region Failure",
            "affected_users": 12000,
            "estimated_revenue_impact": 750000,
            "predicted_recovery_minutes": 28,
            "policy_violations": ["regional_failover_capacity_below_threshold"],
            "recommended_actions": ["activate_secondary_region", "freeze_releases"],
            "approval_required": True,
            "confidence": 0.91,
            "created_at": _now(),
        },
        {
            "id": "demo-twin-scenario-02",
            "twin_id": "twin-novacodepro-demo",
            "scenario": "Database Failure",
            "affected_users": 8500,
            "estimated_revenue_impact": 460000,
            "predicted_recovery_minutes": 18,
            "policy_violations": ["backup_restore_validation_required"],
            "recommended_actions": ["restore_primary_replica", "notify_incident_command"],
            "approval_required": True,
            "confidence": 0.89,
            "created_at": _now(),
        },
        {
            "id": "demo-twin-scenario-03",
            "twin_id": "twin-novacodepro-demo",
            "scenario": "Payment API Failure",
            "affected_users": 6200,
            "estimated_revenue_impact": 180000,
            "predicted_recovery_minutes": 12,
            "policy_violations": ["release_freeze_recommended"],
            "recommended_actions": ["pause_payment_rollout", "open_security_review"],
            "approval_required": True,
            "confidence": 0.87,
            "created_at": _now(),
        },
    ]


def build_marketplace_packages() -> list[dict[str, Any]]:
    packages = [
        ("demo-solution-pack", "Solution Pack"),
        ("demo-industry-pack", "Industry Pack"),
        ("demo-agent-pack", "Agent Pack"),
        ("demo-governance-pack", "Governance Pack"),
        ("demo-workflow-pack", "Workflow Pack"),
        ("demo-ui-pack", "UI Pack"),
    ]
    return [
        {
            "id": package_id,
            "name": label,
            "category": "solution",
            "version": "2027.1.0",
            "installed": index < 2,
            "tenant_id": DEMO_TENANT_ID,
            "region": DEMO_REGION,
            "permissions": ["knowledge.read", "evidence.verify"],
            "signature": "sigstore-reference",
            "checksum": f"sha256-{package_id}",
            "publisher": "NovaTech Demo",
            "created_at": _now(),
            "updated_at": _now(),
        }
        for index, (package_id, label) in enumerate(packages)
    ]


def build_command_center_snapshot() -> dict[str, Any]:
    return {
        "id": "demo-command-center-snapshot-01",
        "metric": "enterprise_health",
        "value": 96,
        "classification": "DEMO_DATA",
        "source": "enterprise-demo-seed",
        "observed_at": _now(),
        "region": DEMO_REGION,
        "confidence": 0.93,
        "freshness_seconds": 12,
        "created_at": _now(),
        "updated_at": _now(),
    }


def build_evidence_bundles() -> list[dict[str, Any]]:
    bundles = []
    for index in range(1, 11):
        bundles.append(
            {
                "id": f"demo-evidence-{index:02d}",
                "tenant_id": DEMO_TENANT_ID,
                "workflow_id": f"demo-workflow-{((index - 1) % 8) + 1:02d}",
                "actor": {"type": "user", "id": f"demo-user-{((index - 1) % 29) + 1:02d}"},
                "action": "release.approved" if index % 2 else "approval.recorded",
                "policy_id": "REL-PROD-001",
                "artifact_ids": [f"demo-artifact-{index:02d}"],
                "occurred_at": _now(),
                "payload": {"classification": "DEMO_DATA"},
                "verified": True,
                "hash": f"sha256-demo-evidence-{index:02d}",
                "signature": f"sig-demo-evidence-{index:02d}",
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
    return bundles


def build_releases() -> list[dict[str, Any]]:
    return [
        {
            "id": f"demo-release-{index:02d}",
            "workflow_id": f"demo-workflow-{index:02d}",
            "tenant_id": DEMO_TENANT_ID,
            "title": f"Demo Release {index:02d}",
            "channel": "demo",
            "target": "staging",
            "status": "release_ready" if index == 1 else "signed",
            "version": f"2027.1.{index}",
            "rollback_ref": f"demo-rollback-{index:02d}",
            "created_at": _now(),
            "updated_at": _now(),
        }
        for index in range(1, 4)
    ]


def build_deployments() -> list[dict[str, Any]]:
    releases = build_releases()
    return [
        {
            "id": f"demo-deployment-{index:02d}",
            "workflow_id": releases[index - 1]["workflow_id"],
            "release_id": releases[index - 1]["id"],
            "environment": "staging" if index < 3 else "pilot",
            "region": DEMO_REGION,
            "status": "healthy" if index != 3 else "running",
            "health": "green",
            "version": releases[index - 1]["version"],
            "metrics": {"availability": 0.999, "latency_p95_ms": 105 + index, "error_rate": 0.0001},
            "created_at": _now(),
            "updated_at": _now(),
        }
        for index in range(1, 4)
    ] + [
        {
            "id": "demo-deployment-04",
            "workflow_id": "demo-workflow-04",
            "release_id": "demo-release-01",
            "environment": "production",
            "region": DEMO_REGION,
            "status": "paused",
            "health": "amber",
            "version": "2027.1.4",
            "metrics": {"availability": 0.998, "latency_p95_ms": 111, "error_rate": 0.0002},
            "created_at": _now(),
            "updated_at": _now(),
        }
    ]


def build_incidents() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-incident-01",
            "title": "Demo deployment latency spike",
            "severity": "medium",
            "status": "open",
            "service": "NovaCodePro Gateway",
            "region": DEMO_REGION,
            "details": {"classification": "DEMO_DATA"},
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-incident-02",
            "title": "Demo partner access review",
            "severity": "low",
            "status": "closed",
            "service": "NovaCodePro Federation",
            "region": DEMO_REGION,
            "details": {"classification": "DEMO_DATA"},
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]


def build_service_registry() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-gateway-service",
            "name": "NovaCodePro Gateway",
            "category": "control-plane",
            "status": "healthy",
            "api": "/api/v1/solutions",
            "tenant_id": DEMO_TENANT_ID,
            "classification": "DEMO_DATA",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-graph-service",
            "name": "NovaCodePro Graph Service",
            "category": "knowledge",
            "status": "healthy",
            "api": "/v1/novacodepro/graph/query",
            "tenant_id": DEMO_TENANT_ID,
            "classification": "DEMO_DATA",
            "created_at": _now(),
            "updated_at": _now(),
        },
        {
            "id": "demo-board-service",
            "name": "NovaCodePro Board Governance Service",
            "category": "governance",
            "status": "healthy",
            "api": "/v1/novacodepro/board/resolutions",
            "tenant_id": DEMO_TENANT_ID,
            "classification": "DEMO_DATA",
            "created_at": _now(),
            "updated_at": _now(),
        },
    ]
