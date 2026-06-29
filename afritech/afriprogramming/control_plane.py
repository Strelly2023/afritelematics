"""NovaProgramming control plane helpers.

This module keeps the internal tooling surface deterministic and shared across
FastAPI and Django adapters. The payloads are intentionally read-mostly and
proposal-oriented so they can be consumed by staff tools without implying any
runtime authority beyond the bounded surfaces in this repo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from afritech.afriprogramming import (
    build_engineering_platform,
    build_engineering_plan_from_mappings,
    build_pr_intelligence_summary,
)
from afritech.afriprogramming.assurance import (
    AssuranceService,
    AssuranceReportService,
    CertificationService,
    ContinuousAssuranceService,
    CryptoStorageHardeningService,
    DistributedTrustNetworkService,
    EventStreamingService,
    PKIService,
    ReplayRegistry,
    SignedAuditChainService,
    RetentionService,
    TrustExchangeService,
    TrustFabricService,
    RiskPredictionService,
    TrustTrendService,
    PolicyRegistryService,
    TrustService,
    WorkflowService,
    ZeroTrustService,
    verify_external_receipt,
)
from afritech.afriprogramming.models import AfriProgrammingEngineeringPlan
from afritech.afriprogramming.persistence import DEFAULT_ORGANIZATION_ID, get_platform_store
from afritech.afriprogramming.rbac import (
    build_rbac_access_check,
    build_rbac_assignments,
    build_rbac_catalog,
    build_rbac_role_dashboard,
    evaluate_rbac_access,
    canonical_role_name,
)
from afritech.afriprogramming.v9 import (
    AssuranceScheduler,
    CertificateTransparencyLogService,
    KeyRevocationAuthority,
    OpenTelemetryTracingService,
    TrustFabricConsensusService,
    build_v9_postgres_schema_sql,
    build_v9_rls_sql,
    build_v9_sqlite_schema_sql,
    ensure_v9_schema,
)
from afritech.afriprogramming.tooling_surfaces import build_governed_tooling_upgrade
from afritech.afroprog_workspace.models import (
    ProjectWorkspace,
    afroprog_seed_projects,
)
from afritech.extensions.afriprog.ai_engine.design_generator import DesignGenerator
from afritech.novascript import get_novascript_service


STAFF_ROLES: tuple[str, ...] = (
    "executives",
    "solutions_architects",
    "project_managers",
    "developers",
    "qa_engineers",
    "devops_engineers",
    "data_engineers",
    "support_engineers",
)

PRODUCT_SURFACES: tuple[dict[str, object], ...] = (
    {
        "id": "studio",
        "name": "NovaProgramming Studio",
        "purpose": "AI-assisted development workspace",
        "status": "available",
        "surface": "build",
    },
    {
        "id": "cloud",
        "name": "NovaProgramming Cloud",
        "purpose": "Deployment and runtime orchestration",
        "status": "available",
        "surface": "operate",
    },
    {
        "id": "governance",
        "name": "NovaProgramming Governance",
        "purpose": "Policy, approvals, and compliance controls",
        "status": "available",
        "surface": "govern",
    },
    {
        "id": "intelligence",
        "name": "NovaProgramming Intelligence",
        "purpose": "Architecture and repository analysis",
        "status": "available",
        "surface": "analyze",
    },
    {
        "id": "verify",
        "name": "NovaProgramming Verify",
        "purpose": "Proof, replay, and trust receipts",
        "status": "available",
        "surface": "verify",
    },
)

STACK_SURFACES: dict[str, tuple[str, ...]] = {
    "frameworks": ("Django", "FastAPI", "Spring"),
    "databases": ("PostgreSQL", "Redis", "Elasticsearch"),
    "cloud": ("AWS", "Azure", "GCP"),
    "devops": ("Docker", "Kubernetes", "Terraform"),
    "ci_cd": ("GitHub Actions", "GitLab CI"),
    "monitoring": ("Prometheus", "Grafana", "ELK"),
    "security": ("Keycloak", "Vault"),
}

ROLE_SURFACES: dict[str, dict[str, Any]] = {
    "executives": {
        "name": "Executives",
        "visible_panels": ("System health", "Trust metrics", "Delivery status"),
        "permissions": ("read:metrics", "read:trust", "read:delivery"),
    },
    "solutions_architects": {
        "name": "Solutions Architects",
        "visible_panels": ("Architecture maps", "Dependency graph", "Risk reports"),
        "permissions": ("read:architecture", "read:dependencies", "read:risk"),
    },
    "project_managers": {
        "name": "Project Managers",
        "visible_panels": ("Milestones", "Delivery plans", "Approvals"),
        "permissions": ("read:delivery", "write:plans", "request:approvals"),
    },
    "developers": {
        "name": "Developers",
        "visible_panels": ("Studio", "Repo intelligence", "Scaffold output"),
        "permissions": ("read:studio", "write:scaffold", "read:analysis"),
    },
    "qa_engineers": {
        "name": "QA Engineers",
        "visible_panels": ("Test pipelines", "Validation reports", "Replay evidence"),
        "permissions": ("read:tests", "read:verification", "read:replay"),
    },
    "devops_engineers": {
        "name": "DevOps Engineers",
        "visible_panels": ("Cloud control", "Deployments", "Monitoring"),
        "permissions": ("read:cloud", "write:deployments", "read:monitoring"),
    },
    "data_engineers": {
        "name": "Data Engineers",
        "visible_panels": ("Pipelines", "Analytics", "Event traces"),
        "permissions": ("read:pipelines", "read:analytics", "read:events"),
    },
    "support_engineers": {
        "name": "Support Engineers",
        "visible_panels": ("Tickets", "Logs", "Replay"),
        "permissions": ("read:support", "read:logs", "read:replay"),
    },
}

PHASE0_MODULES: tuple[dict[str, str], ...] = (
    {"key": "core", "purpose": "Shared platform foundation and base models"},
    {"key": "organizations", "purpose": "Multi-tenant organization registry"},
    {"key": "accounts", "purpose": "User membership and RBAC bridge"},
    {"key": "subscriptions", "purpose": "Plan and entitlement control"},
    {"key": "catalog", "purpose": "Feature definitions and module catalog"},
    {"key": "feature_flags", "purpose": "Scoped feature toggles"},
    {"key": "audit", "purpose": "Audit trail and evidence ledger"},
    {"key": "notifications", "purpose": "Notification outbox and delivery state"},
    {"key": "integrations", "purpose": "External integration registry"},
)

PHASE0_REQUIRED_TABLES: tuple[str, ...] = (
    "organizations",
    "organization_profiles",
    "accounts",
    "subscriptions",
    "catalog_features",
    "feature_flags",
    "audit_events",
    "notifications",
    "integrations",
)

PHASE0_REQUIRED_CONTROLS: tuple[str, ...] = (
    "multi_tenant_registry",
    "subscription_entitlements",
    "feature_catalog",
    "feature_flags",
    "audit_logging",
    "notification_outbox",
    "integration_registry",
    "backend_only_provider_access",
)

PHASE0_PLAN_RANK: dict[str, int] = {
    "free": 0,
    "basic": 1,
    "pro": 2,
    "enterprise": 3,
}

PHASE0_ENDPOINT_MINIMUM_PLANS: dict[str, str] = {
    "organization_onboard": "free",
    "account_create": "free",
    "subscription_create": "free",
    "catalog": "free",
    "feature_flag_set": "pro",
    "notifications": "free",
    "notification_queue": "free",
    "notification_send": "free",
    "integration_register": "pro",
    "integrations": "free",
}

_STORE = get_platform_store()


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _normalize_plan_name(plan: str | None) -> str:
    normalized = str(plan or "free").strip().lower()
    return normalized if normalized in PHASE0_PLAN_RANK else "free"


def _plan_rank(plan: str | None) -> int:
    return PHASE0_PLAN_RANK[_normalize_plan_name(plan)]


def _subscription_is_active(subscription: dict[str, Any] | None) -> bool:
    if not subscription:
        return False
    return str(subscription.get("status", "")).lower() == "active"


def _require_minimum_plan(subscription: dict[str, Any] | None, minimum_plan: str) -> None:
    if not _subscription_is_active(subscription):
        raise ValueError("active subscription required")
    if _plan_rank(subscription.get("plan")) < _plan_rank(minimum_plan):
        raise ValueError(f"{minimum_plan} subscription required")


def _phase0_audit(
    *,
    organization_id: str,
    event_type: str,
    actor_user_id: str,
    actor_role: str,
    target: str,
    status: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return _STORE.record_audit_event(
        organization_id=organization_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=target,
        status=status,
        payload=payload,
    )


def _stable_hash(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _select_project(project_id: str) -> ProjectWorkspace:
    projects = {project.project_id: project for project in afroprog_seed_projects()}
    return projects.get(project_id, next(iter(projects.values())))


def _project_signals(project: ProjectWorkspace) -> dict[str, Any]:
    return {
        "file_count": len(project.files),
        "language_count": len({item.language for item in project.files}),
        "file_paths": [item.path for item in project.files],
        "tags": list(project.tags),
    }


def _build_plan(project: ProjectWorkspace, prompt: str) -> AfriProgrammingEngineeringPlan:
    file_refs = tuple(f"project:{project.project_id}:{item.path}" for item in project.files)
    task = {
        "id": f"task.{project.project_id}",
        "intent": prompt,
        "lifecycle_stage": "build",
        "required_capabilities": (
            "code_generation",
            "test_generation",
            "security_validation",
            "pr_explanation",
            "verification_receipts",
        ),
        "evidence_refs": file_refs,
    }
    agents = (
        {
            "id": "agent.backend",
            "name": "Backend Agent",
            "role": "backend",
            "capabilities": ("code_generation", "pr_explanation"),
        },
        {
            "id": "agent.testing",
            "name": "Testing Agent",
            "role": "testing",
            "capabilities": ("test_generation", "verification_receipts"),
        },
        {
            "id": "agent.security",
            "name": "Security Agent",
            "role": "security",
            "capabilities": ("security_validation",),
        },
    )
    artifacts = (
        {
            "id": f"artifact.{project.project_id}.code",
            "artifact_type": "CODE",
            "title": f"{project.name} scaffold",
            "source_task_id": f"task.{project.project_id}",
            "trace_refs": file_refs or (project.project_id,),
        },
        {
            "id": f"artifact.{project.project_id}.tests",
            "artifact_type": "TEST",
            "title": f"{project.name} tests",
            "source_task_id": f"task.{project.project_id}",
            "trace_refs": file_refs or (project.project_id,),
        },
        {
            "id": f"artifact.{project.project_id}.proof",
            "artifact_type": "VERIFICATION_RECEIPT",
            "title": f"{project.name} verification receipt",
            "source_task_id": f"task.{project.project_id}",
            "trace_refs": file_refs or (project.project_id,),
        },
    )
    return build_engineering_plan_from_mappings(
        plan_id=f"plan.{project.project_id}",
        task=task,
        agents=agents,
        artifacts=artifacts,
    )


def _record_event(
    *,
    organization_id: str,
    action: str,
    actor_user_id: str,
    actor_role: str,
    target: str,
    status: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    return _STORE.record_audit_event(
        organization_id=organization_id,
        event_type=action,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=target,
        status=status,
        payload=details,
    )


def _trust_service() -> TrustService:
    return TrustService(_STORE)


def _assurance_service() -> AssuranceService:
    return AssuranceService(_STORE)


def _replay_registry() -> ReplayRegistry:
    return ReplayRegistry(_STORE)


def _policy_registry() -> PolicyRegistryService:
    return PolicyRegistryService(_STORE)


def _continuous_assurance() -> ContinuousAssuranceService:
    return ContinuousAssuranceService(_STORE)


def _trust_trend_service() -> TrustTrendService:
    return TrustTrendService(_STORE)


def _retention_service() -> RetentionService:
    return RetentionService(_STORE)


def _report_service() -> AssuranceReportService:
    return AssuranceReportService(_STORE)


def _trust_exchange_service() -> TrustExchangeService:
    return TrustExchangeService(_STORE)


def _certification_service() -> CertificationService:
    return CertificationService(_STORE)


def _pki_service() -> PKIService:
    return PKIService(_STORE)


def _signed_audit_service() -> SignedAuditChainService:
    return SignedAuditChainService(_STORE, pki_service=_pki_service())


def _distributed_trust_service() -> DistributedTrustNetworkService:
    return DistributedTrustNetworkService(_STORE, pki_service=_pki_service())


def _event_stream_service() -> EventStreamingService:
    return EventStreamingService(_STORE)


def _crypto_hardening_service() -> CryptoStorageHardeningService:
    return CryptoStorageHardeningService(_STORE, pki_service=_pki_service())


def _trust_fabric_service() -> TrustFabricService:
    return TrustFabricService(_STORE, pki_service=_pki_service())


def _risk_prediction_service() -> RiskPredictionService:
    return RiskPredictionService(_STORE)


def _workflow_service() -> WorkflowService:
    return WorkflowService(_STORE)


def _zero_trust_service() -> ZeroTrustService:
    return ZeroTrustService(_STORE)


def _trust_consensus_service() -> TrustFabricConsensusService:
    return TrustFabricConsensusService(
        _STORE,
        trust_fabric=_trust_fabric_service(),
        risk_prediction=_risk_prediction_service(),
    )


def _ct_log_service() -> CertificateTransparencyLogService:
    return CertificateTransparencyLogService(_STORE, pki_service=_pki_service())


def _key_revocation_service() -> KeyRevocationAuthority:
    return KeyRevocationAuthority(_STORE, pki_service=_pki_service())


def _tracing_service() -> OpenTelemetryTracingService:
    return OpenTelemetryTracingService(_STORE)


def _scheduler_service() -> AssuranceScheduler:
    return AssuranceScheduler(_STORE, assurance_service=_continuous_assurance())


def build_catalog(organization_id: str | None = None) -> dict[str, Any]:
    return {
        "platform": "NovaProgramming",
        "platform_version": "V3",
        "positioning": "Governed software engineering and digital transformation platform",
        "organization_model": "organization_id",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "products": PRODUCT_SURFACES,
        "staff_roles": [
            {
                "id": role,
                "name": payload["name"],
                "visible_panels": payload["visible_panels"],
                "permissions": payload["permissions"],
            }
            for role, payload in ROLE_SURFACES.items()
        ],
        "stack": STACK_SURFACES,
        "tools": build_governed_tooling_upgrade(),
        "read_only": True,
        "creates_authority": False,
        "governance_linked": True,
    }


def seed_phase0_catalog(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    features = _STORE.ensure_phase0_catalog()
    profile = _STORE.get_organization_profile(organization_id=org_id)
    if profile is None:
        profile = _STORE.upsert_organization_profile(
            organization_id=org_id,
            organization_type="internal" if org_id == DEFAULT_ORGANIZATION_ID else "business",
            status="active",
            default_plan="enterprise" if org_id == DEFAULT_ORGANIZATION_ID else "free",
            owner_user_id=None,
            owner_role=None,
        )
    return {
        "organization_id": org_id,
        "features": features,
        "profile": profile,
    }


def build_phase0_status(organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    seed = seed_phase0_catalog(org_id)
    directory = build_organization_directory(organization_id=org_id, limit=limit)
    subscriptions = _STORE.list_subscriptions(organization_id=org_id, limit=limit)
    latest_subscription = subscriptions[0] if subscriptions else None
    active_subscription = _STORE.latest_active_subscription(organization_id=org_id)
    accounts = _STORE.list_accounts(organization_id=org_id, limit=limit)
    feature_flags = _STORE.list_feature_flags(organization_id=org_id, limit=limit)
    integrations = _STORE.list_integrations(organization_id=org_id, limit=limit)
    notifications = _STORE.list_notifications(organization_id=org_id, limit=limit)
    audit_log = build_audit_log(organization_id=org_id)
    catalog = _STORE.list_features(limit=limit)
    billing_preview = build_billing_preview(organization_id=org_id)
    readiness = {
        "multi_tenant_registry": bool(directory.get("organization_count", 0)) and seed["profile"] is not None,
        "subscription_entitlements": _subscription_is_active(active_subscription),
        "feature_catalog": len(catalog) >= len(PHASE0_MODULES),
        "feature_flags": len(feature_flags) > 0,
        "audit_logging": audit_log["count"] > 0,
        "notification_outbox": len(notifications) > 0,
        "integration_registry": len(integrations) > 0,
        "backend_only_provider_access": True,
    }
    return {
        "view": "novaprogramming_phase0_status",
        "phase": "0",
        "product": "NovaRide",
        "platform": "NovaRide Phase 0",
        "organization_id": org_id,
        "seed": seed,
        "modules": PHASE0_MODULES,
        "required_tables": PHASE0_REQUIRED_TABLES,
        "required_controls": PHASE0_REQUIRED_CONTROLS,
        "directory": directory,
        "organization_profile": seed["profile"],
        "billing": billing_preview,
        "subscription": latest_subscription,
        "active_subscription": active_subscription,
        "subscriptions": subscriptions,
        "accounts": accounts,
        "feature_catalog": catalog,
        "feature_flags": feature_flags,
        "notifications": notifications,
        "integrations": integrations,
        "audit_log": audit_log,
        "readiness": readiness,
        "ready": all(readiness.values()),
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_status(organization_id: str | None = None) -> dict[str, Any]:
    snapshot = _STORE.metrics_snapshot(organization_id=organization_id)
    return {
        "platform": "NovaProgramming",
        "status": "ready",
        "platform_version": "V3",
        "organization_id": snapshot["organization_id"],
        "products_live": len(PRODUCT_SURFACES),
        "audit_events": snapshot["audit_events"],
        "proofs": snapshot["proofs"],
        "deployments": snapshot["deployments"],
        "deployment_requests": snapshot["deployment_requests"],
        "roles_supported": list(STAFF_ROLES),
        "stack": STACK_SURFACES,
        "read_only": True,
        "governance_linked": True,
    }


def build_staff_dashboard(role: str, project_id: str, organization_id: str | None = None) -> dict[str, Any]:
    role_key = role.strip().lower().replace(" ", "_")
    role_surface = ROLE_SURFACES.get(role_key, ROLE_SURFACES["developers"])
    project = _select_project(project_id)
    workspace = {
        "title": f"NovaProgramming Staff / {project.name}",
        "mode": "dashboard",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "project_explorer": [
            {
                "path": item.path,
                "language": item.language,
            }
            for item in project.files
        ],
        "editor_panel": project.files[0].canonical_dict() if project.files else None,
        "read_only": True,
        "proposal_only": True,
        "governance_linked": True,
    }
    return {
        "role": role_key,
        "role_surface": role_surface,
        "project": project.canonical_dict(),
        "workspace": workspace,
        "visible_products": PRODUCT_SURFACES,
        "read_only": True,
        "proposal_only": True,
        "creates_authority": False,
    }


def build_studio_context(project_id: str, organization_id: str | None = None) -> dict[str, Any]:
    project = _select_project(project_id)
    plan = _build_plan(project, f"Prepare governed scaffolding for {project.name}")
    platform = build_engineering_platform(plan)
    summary = build_pr_intelligence_summary(plan)
    return {
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "project": project.canonical_dict(),
        "workspace": {
            "title": f"NovaProgramming Studio / {project.name}",
            "mode": "codex_style",
            "project_explorer": [
                {
                    "path": item.path,
                    "language": item.language,
                }
                for item in project.files
            ],
            "editor_panel": project.files[0].canonical_dict() if project.files else None,
            "chat_panel": {
                "prompt": f"Analyze {project.name}",
                "mode": "analysis",
                "response": {
                    "status": "ready",
                    "suggestion": "Use the studio generator to create governed scaffolds.",
                },
            },
            "read_only": True,
            "proposal_only": True,
            "governance_linked": True,
        },
        "signals": _project_signals(project),
        "engineering_plan": plan.canonical_dict(),
        "engineering_platform": platform,
        "pr_intelligence": summary,
        "read_only": True,
        "governance_linked": True,
    }


def _scaffold_files(prompt: str, project: ProjectWorkspace) -> list[dict[str, str]]:
    lowered = prompt.lower()
    base_files = [
        {
            "path": "nova_backend/app/main.py",
            "language": "python",
            "purpose": "FastAPI entrypoint",
        },
        {
            "path": "nova_backend/app/api/router.py",
            "language": "python",
            "purpose": "API aggregation router",
        },
        {
            "path": "nova_backend/app/core/security.py",
            "language": "python",
            "purpose": "JWT and permission helpers",
        },
    ]
    if any(keyword in lowered for keyword in ("studio", "code", "build", "scaffold")):
        base_files.append(
            {
                "path": "nova_backend/app/modules/studio/routes.py",
                "language": "python",
                "purpose": "AI-assisted development routes",
            }
        )
    if any(keyword in lowered for keyword in ("cloud", "deploy", "kubernetes", "docker")):
        base_files.append(
            {
                "path": "nova_backend/app/modules/cloud/routes.py",
                "language": "python",
                "purpose": "Deployment and runtime control routes",
            }
        )
    if any(keyword in lowered for keyword in ("govern", "policy", "audit", "compliance")):
        base_files.append(
            {
                "path": "nova_backend/app/modules/governance/routes.py",
                "language": "python",
                "purpose": "Policy and audit routes",
            }
        )
    if any(keyword in lowered for keyword in ("verify", "proof", "replay", "trust")):
        base_files.append(
            {
                "path": "nova_backend/app/modules/verify/routes.py",
                "language": "python",
                "purpose": "Proof and replay routes",
            }
        )
    if any(keyword in lowered for keyword in ("intelligence", "repo", "analysis", "architecture")):
        base_files.append(
            {
                "path": "nova_backend/app/modules/intelligence/routes.py",
                "language": "python",
                "purpose": "Repository intelligence routes",
            }
        )

    base_files.append(
        {
            "path": f"projects/{project.project_id}/README.md",
            "language": "markdown",
            "purpose": "Workspace overview",
        }
    )
    return base_files


def build_studio_generation(
    *,
    prompt: str,
    mode: str,
    project_id: str,
    organization_id: str | None = None,
    actor_user_id: str = "system",
    actor_role: str = "developer",
) -> dict[str, Any]:
    project = _select_project(project_id)
    plan = _build_plan(project, prompt)
    scaffold_files = _scaffold_files(prompt, project)
    execution_preview = {
        "mode": "preview_only",
        "project_id": project.project_id,
        "line_count": len(prompt.splitlines()) or 1,
        "sandboxed": True,
        "mutation_allowed": False,
        "next_step": "send_to_governance",
    }
    response_hash = _stable_hash(
        {
            "project_id": project.project_id,
            "prompt": prompt,
            "mode": mode,
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "files": scaffold_files,
        }
    )
    event = _record_event(
        organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        action="studio.generate_code",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=project.project_id,
        status="preview",
        details={"prompt": prompt, "mode": mode, "response_hash": response_hash},
    )
    return {
        "view": "novaprogramming_studio",
        "prompt": prompt,
        "mode": mode,
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "project": project.canonical_dict(),
        "workspace": {
            "title": f"NovaProgramming Studio / {project.name}",
            "mode": mode,
            "project_explorer": [
                {
                    "path": item.path,
                    "language": item.language,
                }
                for item in project.files
            ],
            "editor_panel": project.files[0].canonical_dict() if project.files else None,
            "chat_panel": {
                "prompt": prompt,
                "mode": mode,
                "response": {
                    "status": "preview_generated",
                    "response_hash": response_hash,
                },
            },
            "generated_files": scaffold_files,
            "read_only": True,
            "proposal_only": True,
            "governance_linked": True,
        },
        "generated_files": scaffold_files,
        "engineering_plan": plan.canonical_dict(),
        "engineering_platform": build_engineering_platform(plan),
        "execution_preview": execution_preview,
        "audit_event": event,
        "response_hash": response_hash,
        "read_only": True,
        "proposal_only": True,
        "governance_linked": True,
    }


def build_code_explanation(
    *,
    code: str,
    context: str = "",
    organization_id: str | None = None,
    actor_user_id: str = "system",
    actor_role: str = "developer",
) -> dict[str, Any]:
    lines = code.splitlines()
    summary = {
        "line_count": len(lines),
        "has_async": any("async " in line for line in lines),
        "has_test_symbols": any("test" in line.lower() for line in lines),
        "has_route_symbols": any("router" in line.lower() for line in lines),
    }
    event = _record_event(
        organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        action="studio.explain_code",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target="code_snippet",
        status="read_only",
        details={"context": context, "summary": summary},
    )
    return {
        "view": "novaprogramming_explanation",
        "context": context,
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "summary": summary,
        "execution_preview": {
            "mode": "preview_only",
            "line_count": len(lines),
            "sandboxed": True,
            "mutation_allowed": False,
        },
        "audit_event": event,
        "read_only": True,
        "governance_linked": True,
    }


def build_repo_intelligence(
    *,
    project_id: str,
    focus: str = "",
    organization_id: str | None = None,
    actor_user_id: str = "system",
    actor_role: str = "architect",
) -> dict[str, Any]:
    project = _select_project(project_id)
    plan = _build_plan(project, f"Analyze repository for {project.name}")
    platform = build_engineering_platform(plan)
    dependencies = sorted(
        {
            part
            for file in project.files
            for part in file.path.split("/")
            if part and part not in {".", ".."}
        }
    )
    tech_debt_score = min(100, 20 + len(project.files) * 10 + len(focus.split()))
    event = _record_event(
        organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        action="intelligence.analyze_repo",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=project.project_id,
        status="read_only",
        details={"focus": focus, "tech_debt_score": tech_debt_score},
    )
    return {
        "view": "novaprogramming_intelligence",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "project": project.canonical_dict(),
        "focus": focus,
        "architecture_signals": _project_signals(project),
        "dependencies": dependencies,
        "tech_debt_score": tech_debt_score,
        "engineering_platform": platform,
        "pr_intelligence": build_pr_intelligence_summary(plan),
        "audit_event": event,
        "read_only": True,
        "governance_linked": True,
    }


def build_cloud_services(organization_id: str | None = None) -> dict[str, Any]:
    return {
        "view": "novaprogramming_cloud",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "services": (
            "build",
            "deploy",
            "scale",
            "health",
            "registry",
            "monitoring",
        ),
        "runtime_stack": STACK_SURFACES["cloud"] + STACK_SURFACES["devops"],
        "read_only": True,
        "governance_linked": True,
    }


def build_cloud_health(organization_id: str | None = None) -> dict[str, Any]:
    snapshot = _STORE.metrics_snapshot(organization_id=organization_id)
    return {
        "view": "novaprogramming_cloud_health",
        "status": "healthy",
        "deployment_state": "ready",
        "managed_services": len(PRODUCT_SURFACES),
        "organization_id": snapshot["organization_id"],
        "deployments": snapshot["deployments"],
        "observability": STACK_SURFACES["monitoring"],
        "read_only": True,
    }


def build_cloud_request_deployment(
    *,
    service: str,
    environment: str,
    image: str,
    rationale: str,
    organization_id: str | None = None,
    requested_by: str = "system",
    requested_role: str = "operator",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    request = _STORE.request_deployment(
        organization_id=org_id,
        service=service,
        environment=environment,
        image=image,
        rationale=rationale,
        requested_by=requested_by,
        requested_role=requested_role,
    )
    event = _record_event(
        organization_id=org_id,
        action="cloud.request_deploy",
        actor_user_id=requested_by,
        actor_role=requested_role,
        target=service,
        status="pending",
        details=request,
    )
    return {
        "view": "novaprogramming_cloud_request_deploy",
        "organization_id": org_id,
        "request": request,
        "audit_event": event,
        "status": "pending",
        "governance_linked": True,
        "read_only": False,
    }


def build_cloud_deployment(
    *,
    request_id: str,
    service: str,
    organization_id: str | None = None,
    environment: str = "staging",
    image: str = "nova-programming:latest",
    deployed_by: str = "system",
    actor_role: str = "devops",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    request = _STORE.get_deployment_request(request_id=request_id, organization_id=org_id)
    if request is None:
        raise KeyError(request_id)
    trust = _trust_service().compute_for_org(org_id)
    gate = _zero_trust_service().evaluate(
        organization_id=org_id,
        subject=deployed_by,
        action="deploy",
        resource=service,
        context={
            "approved": request["status"] == "approved",
            "environment": request["environment"],
            "actor_role": actor_role,
            "trust_score": trust["trust_score"],
            "signed_audit_valid": _STORE.verify_signed_audit_chain(organization_id=org_id),
            "cross_org": False,
        },
    )
    if not gate["allowed"]:
        raise PermissionError(gate["reason"])
    deployment = _STORE.create_deployment_from_request(
        request_id=request_id,
        organization_id=org_id,
        deployed_by=deployed_by,
    )
    event = _record_event(
        organization_id=org_id,
        action="cloud.deploy",
        actor_user_id=deployed_by,
        actor_role=actor_role,
        target=service,
        status="queued",
        details=deployment,
    )
    return {
        "view": "novaprogramming_cloud_deploy",
        "organization_id": org_id,
        "deployment": deployment,
        "service": service,
        "environment": environment,
        "image": image,
        "status": deployment["status"],
        "runbook": "validate -> build -> deploy -> verify",
        "audit_event": event,
        "governance_linked": True,
        "read_only": False,
    }


def build_cloud_scale(
    *,
    service: str,
    replicas: int,
    organization_id: str | None = None,
    deployed_by: str = "system",
    actor_role: str = "devops",
) -> dict[str, Any]:
    if replicas < 1:
        raise ValueError("replicas must be at least 1")
    event = _record_event(
        organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        action="cloud.scale",
        actor_user_id=deployed_by,
        actor_role=actor_role,
        target=service,
        status="queued",
        details={"replicas": replicas},
    )
    return {
        "view": "novaprogramming_cloud_scale",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "service": service,
        "replicas": replicas,
        "status": "queued",
        "audit_event": event,
        "read_only": False,
    }


def build_governance_policy(
    *,
    policy_name: str,
    target: str,
    description: str,
    organization_id: str | None = None,
    actor_user_id: str = "system",
    actor_role: str = "manager",
) -> dict[str, Any]:
    policy_id = f"policy-{_stable_hash({'policy_name': policy_name, 'target': target, 'description': description})[:12]}"
    event = _record_event(
        organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        action="governance.policy",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=target,
        status="recorded",
        details={"policy_name": policy_name, "policy_id": policy_id},
    )
    return {
        "view": "novaprogramming_governance_policy",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "policy_id": policy_id,
        "policy_name": policy_name,
        "target": target,
        "description": description,
        "status": "recorded",
        "audit_event": event,
        "read_only": False,
    }


def build_governance_check(
    *,
    policy_name: str,
    target: str,
    organization_id: str | None = None,
    actor_user_id: str = "system",
    actor_role: str = "verifier",
) -> dict[str, Any]:
    allowed = not any(keyword in target.lower() for keyword in ("proof", "governance", "runtime"))
    event = _record_event(
        organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        action="governance.check",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=target,
        status="pass" if allowed else "review",
        details={"policy_name": policy_name},
    )
    return {
        "view": "novaprogramming_governance_check",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "policy_name": policy_name,
        "target": target,
        "status": "pass" if allowed else "review",
        "authority_boundary": "read_only_validation",
        "audit_event": event,
        "read_only": True,
    }


def build_audit_log(organization_id: str | None = None) -> dict[str, Any]:
    entries = _STORE.list_audit_events(organization_id=organization_id, limit=500)
    return {
        "view": "novaprogramming_audit_log",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "entries": entries,
        "count": len(entries),
        "read_only": True,
    }


def build_governance_approve(
    *,
    request_id: str,
    decision: str = "approved",
    notes: str = "",
    organization_id: str | None = None,
    actor_user_id: str = "system",
    actor_role: str = "verifier",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    request = _STORE.approve_deployment_request(
        request_id=request_id,
        organization_id=org_id,
        approved_by=actor_user_id,
        decision=decision,
        notes=notes,
    )
    event = _record_event(
        organization_id=org_id,
        action="governance.approve",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=request_id,
        status=request["status"],
        details={"decision": decision, "notes": notes, "request": request},
    )
    return {
        "view": "novaprogramming_governance_approve",
        "organization_id": org_id,
        "request": request,
        "status": request["status"],
        "audit_event": event,
        "read_only": False,
    }


def build_proof(
    *,
    execution_id: str,
    project_id: str,
    payload: dict[str, Any],
    organization_id: str | None = None,
    actor_user_id: str = "system",
    actor_role: str = "verifier",
) -> dict[str, Any]:
    project = _select_project(project_id)
    proof_hash = _stable_hash(
        {
            "execution_id": execution_id,
            "project_id": project.project_id,
            "payload": payload,
        }
    )
    proof = {
        "view": "novaprogramming_verify",
        "execution_id": execution_id,
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "project": project.canonical_dict(),
        "payload": payload,
        "proof_hash": proof_hash,
        "receipt_hash": proof_hash,
        "status": "verified",
        "replayable": True,
        "authority_boundary": "proof_export_only",
        "read_only": True,
    }
    _STORE.store_proof(
        execution_id=execution_id,
        organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        project_id=project.project_id,
        proof_hash=proof_hash,
        payload=payload,
        status="verified",
        replayable=True,
    )
    _record_event(
        organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        action="verify.generate_proof",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=execution_id,
        status="recorded",
        details={"proof_hash": proof_hash, "project_id": project.project_id},
    )
    return proof


def lookup_proof(execution_id: str, organization_id: str | None = None) -> dict[str, Any]:
    proof = _STORE.get_proof(execution_id=execution_id, organization_id=organization_id)
    if proof is None:
        raise KeyError(execution_id)
    return {
        "view": "novaprogramming_verify",
        **proof,
        "receipt_hash": proof["proof_hash"],
        "replayable": True,
        "authority_boundary": "proof_export_only",
        "read_only": True,
    }


def build_replay(
    execution_id: str,
    *,
    organization_id: str | None = None,
    actor_user_id: str = "system",
    actor_role: str = "verifier",
) -> dict[str, Any]:
    proof = lookup_proof(execution_id)
    event = _record_event(
        organization_id=organization_id or proof["organization_id"],
        action="verify.replay",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=execution_id,
        status="verified",
        details={"proof_hash": proof["proof_hash"]},
    )
    return {
        "view": "novaprogramming_replay",
        "execution_id": execution_id,
        "organization_id": organization_id or proof["organization_id"],
        "proof_hash": proof["proof_hash"],
        "replay_verified": True,
        "trace_hash": proof["proof_hash"],
        "audit_event": event,
        "read_only": True,
    }


def build_metrics(organization_id: str | None = None) -> dict[str, Any]:
    snapshot = _STORE.metrics_snapshot(organization_id=organization_id)
    return {
        "view": "novaprogramming_metrics",
        "status": "ok",
        "organization_id": snapshot["organization_id"],
        "products_live": len(PRODUCT_SURFACES),
        "roles_supported": len(STAFF_ROLES),
        "audit_events": snapshot["audit_events"],
        "proofs": snapshot["proofs"],
        "deployments": snapshot["deployments"],
        "deployment_requests": snapshot["deployment_requests"],
        "stack": STACK_SURFACES,
        "read_only": True,
    }


def build_trust(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _trust_service().compute_for_org(org_id)
    return {
        "view": "novaprogramming_trust",
        "organization_id": org_id,
        **result,
        "read_only": True,
    }


def build_trust_stream(organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    events = _trust_service().stream(org_id, limit=limit)
    return {
        "view": "novaprogramming_trust_stream",
        "organization_id": org_id,
        "events": events,
        "count": len(events),
        "read_only": True,
    }


def build_trust_anomalies(organization_id: str | None = None, limit: int = 25) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    anomalies = _trust_service().anomalies(org_id, limit=limit)
    return {
        "view": "novaprogramming_trust_anomalies",
        "organization_id": org_id,
        "anomalies": anomalies,
        "count": len(anomalies),
        "read_only": True,
    }


def build_trust_verify_external(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "view": "novaprogramming_trust_verify_external",
        "result": verify_external_receipt(receipt),
        "read_only": True,
    }


def build_trust_risk(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _trust_service().trust_risk(org_id)
    return {
        "view": "novaprogramming_trust_risk",
        **result,
        "read_only": True,
    }


def build_assurance(
    *,
    deployment_id: str,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _assurance_service().compute_for_deployment(
        deployment_id=deployment_id,
        organization_id=org_id,
    )
    return {
        "view": "novaprogramming_assurance",
        **result,
        "read_only": True,
    }


def build_assurance_certification(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _assurance_service().certification(organization_id=org_id)
    return {
        "view": "novaprogramming_certification",
        **result,
        "read_only": True,
    }


def build_trust_replay(
    *,
    deployment_id: str,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    deployment = _STORE.get_deployment(deployment_id=deployment_id, organization_id=org_id)
    if deployment is None:
        raise KeyError(deployment_id)
    proof = _STORE.latest_proof(organization_id=org_id)
    receipt = _STORE.get_deployment_receipt(deployment_id=deployment_id, organization_id=org_id)
    if receipt is None or proof is None:
        assurance = _assurance_service().compute_for_deployment(deployment_id=deployment_id, organization_id=org_id)
        receipt = assurance["receipt"]
        proof_hash = assurance["proof_hash"]
        audit_hash = assurance["audit_hash"]
        replay = assurance["replay"]
    else:
        replay = _replay_registry().register(
            organization_id=org_id,
            deployment_id=deployment_id,
            proof_id=proof["proof_id"],
            receipt_id=receipt["receipt_id"],
            audit_hash=receipt["audit_hash"],
        )
        proof_hash = proof["proof_hash"]
        audit_hash = receipt["audit_hash"]
    return {
        "view": "novaprogramming_trust_replay",
        "organization_id": org_id,
        "deployment_id": deployment_id,
        "proof_hash": proof_hash,
        "audit_hash": audit_hash,
        "replay": replay,
        "read_only": True,
    }


def build_billing_summary(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    summary = _STORE.billing_summary(organization_id=org_id)
    return {
        "view": "novaprogramming_billing_summary",
        **summary,
        "read_only": True,
    }


def build_billing_preview(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    usage_total = _STORE.count_usage(organization_id=org_id)
    latest = _STORE.latest_trust_score(organization_id=org_id)
    estimated_amount = round(usage_total * 0.05, 2)
    return {
        "view": "novaprogramming_billing_preview",
        "organization_id": org_id,
        "plan": "enterprise",
        "usage_total": usage_total,
        "estimated_amount": estimated_amount,
        "billing_enabled": False,
        "trust_score": latest["trust_score"] if latest else None,
        "classification": latest["classification"] if latest else None,
        "read_only": True,
    }


def build_billing_records(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    records = _STORE.list_billing_records(organization_id=org_id, limit=limit)
    return {
        "view": "novaprogramming_billing_records",
        "organization_id": org_id,
        "count": len(records),
        "billing_records": records,
        "read_only": True,
    }


def build_organization_directory(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    organizations = _STORE.list_organizations(organization_id=organization_id, limit=limit)
    return {
        "view": "novaprogramming_organization_directory",
        "organization_id": org_id,
        "organization_count": len(organizations),
        "organizations": organizations,
        "read_only": True,
    }


def build_policy_registry(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _policy_registry()
    service.seed_defaults(org_id)
    policies = service.list_policies(org_id)
    return {
        "view": "novaprogramming_policy_registry",
        "organization_id": org_id,
        "policies": policies,
        "count": len(policies),
        "read_only": True,
    }


def build_policy_create(
    *,
    policy_name: str,
    version: str,
    rule_type: str,
    rule_payload: dict[str, Any],
    active: bool = True,
    organization_id: str | None = None,
    created_by: str = "system",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    record = _policy_registry().create_policy(
        organization_id=org_id,
        policy_name=policy_name,
        version=version,
        rule_type=rule_type,
        rule_payload=rule_payload,
        active=active,
        created_by=created_by,
    )
    return {
        "view": "novaprogramming_policy_create",
        "organization_id": org_id,
        "policy": record,
        "read_only": False,
    }


def build_policy_evaluate(
    *,
    action: str,
    target: str,
    payload: dict[str, Any],
    organization_id: str | None = None,
    actor_user_id: str = "system",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    decision = _policy_registry().evaluate(
        organization_id=org_id,
        action=action,
        actor_user_id=actor_user_id,
        target=target,
        payload=payload,
    )
    return {
        "view": "novaprogramming_policy_evaluate",
        "organization_id": org_id,
        "decision": decision,
        "read_only": True,
    }


def build_policy_decisions(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    decisions = _policy_registry().decisions(org_id)
    return {
        "view": "novaprogramming_policy_decisions",
        "organization_id": org_id,
        "decisions": decisions,
        "count": len(decisions),
        "read_only": True,
    }


def build_assurance_status(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    status = _continuous_assurance().status(organization_id=org_id)
    return {
        "view": "novaprogramming_assurance_status",
        **status,
        "read_only": True,
    }


def build_assurance_run(organization_id: str | None = None, actor_user_id: str = "system") -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    run = _continuous_assurance().run(organization_id=org_id, actor_user_id=actor_user_id)
    return {
        "view": "novaprogramming_assurance_run",
        "organization_id": org_id,
        "run": run,
        "read_only": False,
    }


def build_assurance_history(organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    runs = _continuous_assurance().history(organization_id=org_id, limit=limit)
    return {
        "view": "novaprogramming_assurance_history",
        "organization_id": org_id,
        "runs": runs,
        "count": len(runs),
        "read_only": True,
    }


def build_assurance_alerts(organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    alerts = _continuous_assurance().alerts(organization_id=org_id, limit=limit)
    return {
        "view": "novaprogramming_assurance_alerts",
        "organization_id": org_id,
        "alerts": alerts,
        "count": len(alerts),
        "read_only": True,
    }


def build_trust_trends(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    trends = _trust_trend_service().compute(org_id)
    return {
        "view": "novaprogramming_trust_trends",
        **trends,
        "read_only": True,
    }


def _analytics_clamp(value: float | int, *, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, int(round(float(value)))))


def _analytics_series(series: list[int]) -> dict[str, Any]:
    if not series:
        return {
            "count": 0,
            "first": 0,
            "latest": 0,
            "delta": 0,
            "slope": 0.0,
            "direction": "stable",
            "average": 0.0,
            "minimum": 0,
            "maximum": 0,
        }
    first = series[0]
    latest = series[-1]
    delta = latest - first
    slope = delta / max(1, len(series) - 1)
    if slope > 0.5:
        direction = "rising"
    elif slope < -0.5:
        direction = "falling"
    else:
        direction = "stable"
    return {
        "count": len(series),
        "first": first,
        "latest": latest,
        "delta": delta,
        "slope": round(slope, 2),
        "direction": direction,
        "average": round(sum(series) / len(series), 2),
        "minimum": min(series),
        "maximum": max(series),
    }


def _analytics_payload_metrics(payload: dict[str, Any]) -> dict[str, int]:
    pilot_evidence = payload.get("pilot_evidence") or {}
    driver_trust_trend = payload.get("driver_trust_trend") or []
    trust_score = int(payload.get("fleet_trust_score") or payload.get("trust_score") or 0)
    active_drivers = int(payload.get("active_drivers") or 0)
    verified_rides_today = int(payload.get("verified_rides_today") or payload.get("completed_rides") or 0)
    evidence_packets_today = int(payload.get("evidence_packets_today") or payload.get("receipts_count") or 0)
    open_replay_exceptions = int(payload.get("open_replay_exceptions") or payload.get("guard_count") or 0)
    replay_exception_rate_pct = float(payload.get("replay_exception_rate_pct") or 0.0)
    shift_count = int(
        pilot_evidence.get("shift_count")
        or payload.get("total_rides")
        or verified_rides_today
        or len(driver_trust_trend)
        or 0
    )
    gps_signal_loss_events = int(pilot_evidence.get("gps_signal_loss_events") or 0)
    route_deviation_events = int(pilot_evidence.get("route_deviation_events") or 0)
    latency_breaches = int(pilot_evidence.get("latency_breaches") or 0)
    total_rides = max(verified_rides_today, shift_count)
    receipts_count = evidence_packets_today
    trace_count = max(total_rides, receipts_count)
    missing_traces = max(0, trace_count - receipts_count)
    replay_failures = open_replay_exceptions + route_deviation_events
    hash_chain_failures = route_deviation_events
    guard_count = open_replay_exceptions
    alert_count = max(0, replay_failures + missing_traces + latency_breaches + gps_signal_loss_events)
    evidence_coverage = 0 if trace_count == 0 else _analytics_clamp((receipts_count / trace_count) * 100)
    trust_health = _analytics_clamp(trust_score - replay_failures * 10 - missing_traces * 4 - alert_count * 2)
    replay_health_score = _analytics_clamp(
        100 - replay_failures * 12 - hash_chain_failures * 6 - gps_signal_loss_events * 4 - latency_breaches * 2
    )
    exception_pressure = max(
        0,
        replay_failures + missing_traces + gps_signal_loss_events + latency_breaches + int(round(replay_exception_rate_pct / 10)),
    )
    return {
        "trust_score": trust_score,
        "trust_health": trust_health,
        "replay_health_score": replay_health_score,
        "evidence_coverage": evidence_coverage,
        "exception_pressure": exception_pressure,
        "alert_count": alert_count,
        "active_drivers": active_drivers,
        "completed_rides": verified_rides_today,
        "total_rides": total_rides,
        "guard_count": guard_count,
        "replay_failures": replay_failures,
        "hash_chain_failures": hash_chain_failures,
        "missing_traces": missing_traces,
        "receipts_count": receipts_count,
        "trace_count": trace_count,
    }


def record_dashboard_analytics_snapshot(
    *,
    payload: dict[str, Any],
    source: str,
    snapshot_type: str = "operator_dashboard",
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    metrics = _analytics_payload_metrics(payload)
    return _STORE.store_dashboard_analytics_snapshot(
        organization_id=org_id,
        source=source,
        snapshot_type=snapshot_type,
        payload=payload,
        **metrics,
    )


def _build_dashboard_analytics_context(
    *,
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    snapshot_type: str = "operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    snapshots = _STORE.list_dashboard_analytics_snapshots(
        organization_id=org_id,
        source=source,
        snapshot_type=snapshot_type,
        limit=limit,
    )
    history = list(reversed(snapshots))
    trust_series = [item["trust_score"] for item in history]
    coverage_series = [item["evidence_coverage"] for item in history]
    exception_series = [item["exception_pressure"] for item in history]
    latest = history[-1] if history else None
    trust_trend = _analytics_series(trust_series)
    coverage_trend = _analytics_series(coverage_series)
    exception_trend = _analytics_series(exception_series)
    source_breakdown: dict[str, int] = {}
    for item in history:
        source_breakdown[item["source"]] = source_breakdown.get(item["source"], 0) + 1

    insights: list[dict[str, Any]] = []
    if latest is not None:
        if trust_trend["direction"] == "rising":
            trust_message = "Trust is improving across the retained history."
            trust_severity = "good"
        elif trust_trend["direction"] == "falling":
            trust_message = "Trust is drifting lower across the retained history."
            trust_severity = "warning"
        else:
            trust_message = "Trust is stable across the retained history."
            trust_severity = "info"
        insights.append(
            {
                "id": "trust-trend",
                "title": "Trust trend",
                "severity": trust_severity,
                "detail": (
                    f"Latest trust score is {latest['trust_score']} with a {trust_trend['direction']} "
                    f"trend and {trust_trend['delta']} net change over {trust_trend['count']} samples. "
                    f"{trust_message}"
                ),
            }
        )

        if coverage_trend["direction"] == "rising":
            coverage_message = "Evidence coverage is strengthening."
            coverage_severity = "good"
        elif coverage_trend["direction"] == "falling":
            coverage_message = "Evidence coverage is weakening."
            coverage_severity = "warning"
        else:
            coverage_message = "Evidence coverage is steady."
            coverage_severity = "info"
        insights.append(
            {
                "id": "evidence-trend",
                "title": "Evidence coverage",
                "severity": coverage_severity,
                "detail": (
                    f"Latest coverage is {latest['evidence_coverage']}% with {latest['receipts_count']} "
                    f"receipts over {latest['trace_count']} traces. {coverage_message}"
                ),
            }
        )

        if exception_trend["direction"] == "rising":
            exception_message = "Exception pressure is increasing and should be watched."
            exception_severity = "critical" if latest["exception_pressure"] > 2 else "warning"
        elif exception_trend["direction"] == "falling":
            exception_message = "Exception pressure is easing."
            exception_severity = "good"
        else:
            exception_message = "Exception pressure is flat."
            exception_severity = "info"
        insights.append(
            {
                "id": "exception-trend",
                "title": "Replay exception pressure",
                "severity": exception_severity,
                "detail": (
                    f"Current pressure is {latest['exception_pressure']} with {latest['replay_failures']} replay "
                    f"failure(s) and {latest['missing_traces']} missing trace(s). {exception_message}"
                ),
            }
        )

        insights.append(
            {
                "id": "history-depth",
                "title": "Persistent history",
                "severity": "info",
                "detail": (
                    f"{len(history)} analytics snapshot(s) are retained in the rolling history from "
                    f"{len(source_breakdown)} source(s)."
                ),
            }
        )

        if latest["guard_count"] > 0:
            insights.append(
                {
                    "id": "guard-pressure",
                    "title": "Guard pressure",
                    "severity": "warning" if latest["guard_count"] <= 2 else "critical",
                    "detail": (
                        f"{latest['guard_count']} guard violation(s) remain visible in the live operating window."
                    ),
                }
            )

    trust_prediction = latest["trust_score"] if latest is not None else 0
    coverage_prediction = latest["evidence_coverage"] if latest is not None else 0
    exception_prediction = latest["exception_pressure"] if latest is not None else 0
    trust_adjustment = trust_trend["slope"] * 3 - exception_trend["slope"] * 2
    coverage_adjustment = coverage_trend["slope"] * 2 - max(0.0, exception_trend["slope"])
    exception_adjustment = exception_trend["slope"] * 2 + max(0.0, 100 - coverage_prediction) / 25
    predicted_trust_score = _analytics_clamp(trust_prediction + trust_adjustment)
    predicted_coverage = _analytics_clamp(coverage_prediction + coverage_adjustment)
    predicted_exception_pressure = _analytics_clamp(exception_prediction + exception_adjustment)
    if predicted_trust_score >= 90 and predicted_exception_pressure <= 2 and predicted_coverage >= 95:
        risk_level = "low"
        headline = "The current operating band should stay stable in the next cycle."
    elif predicted_trust_score >= 80 and predicted_exception_pressure <= 5:
        risk_level = "medium"
        headline = "The next cycle is likely stable, but exception pressure deserves review."
    else:
        risk_level = "high"
        headline = "The next cycle may drift without intervention."
    confidence = 0.55 + min(0.25, len(history) / 40) - abs(exception_trend["slope"]) * 0.02
    confidence = round(max(0.5, min(0.95, confidence)), 2)
    watch_items = [
        item
        for item in [
            "Replay exceptions are increasing." if exception_trend["direction"] == "rising" else None,
            "Evidence coverage is below the ideal band." if predicted_coverage < 95 else None,
            "Trust is trending down." if trust_trend["direction"] == "falling" else None,
            "Guard pressure is present." if latest and latest["guard_count"] > 0 else None,
        ]
        if item is not None
    ]
    if not watch_items:
        watch_items = ["Maintain the current replay-backed operating band."]

    return {
        "view": "novatech_operator_analytics",
        "organization_id": org_id,
        "source": source or "all",
        "history": {
            "count": len(history),
            "items": history,
            "source_breakdown": source_breakdown,
        },
        "latest": latest,
        "trend": {
            "trust": trust_trend,
            "evidence": coverage_trend,
            "exceptions": exception_trend,
        },
        "insights": insights,
        "prediction": {
            "horizon": "next_cycle",
            "predicted_trust_score": predicted_trust_score,
            "predicted_evidence_coverage": predicted_coverage,
            "predicted_exception_pressure": predicted_exception_pressure,
            "risk_level": risk_level,
            "confidence": confidence,
            "headline": headline,
            "watch_items": watch_items,
        },
        "read_only": True,
        "projection_only": True,
    }


def build_dashboard_analytics(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    return _build_dashboard_analytics_context(
        organization_id=organization_id,
        source=source,
        snapshot_type="operator_dashboard",
        limit=limit,
    )


def build_dashboard_analytics_history(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    analytics = _build_dashboard_analytics_context(
        organization_id=organization_id,
        source=source,
        snapshot_type="operator_dashboard",
        limit=limit,
    )
    return {
        "view": "novatech_operator_analytics_history",
        "organization_id": analytics["organization_id"],
        "source": analytics["source"],
        "history": analytics["history"],
        "trend": analytics["trend"],
        "latest": analytics["latest"],
        "read_only": True,
    }


def build_dashboard_analytics_insights(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    analytics = _build_dashboard_analytics_context(
        organization_id=organization_id,
        source=source,
        snapshot_type="operator_dashboard",
        limit=limit,
    )
    return {
        "view": "novatech_operator_analytics_insights",
        "organization_id": analytics["organization_id"],
        "source": analytics["source"],
        "insights": analytics["insights"],
        "trend": analytics["trend"],
        "latest": analytics["latest"],
        "read_only": True,
    }


def build_dashboard_analytics_prediction(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    analytics = _build_dashboard_analytics_context(
        organization_id=organization_id,
        source=source,
        snapshot_type="operator_dashboard",
        limit=limit,
    )
    return {
        "view": "novatech_operator_analytics_prediction",
        "organization_id": analytics["organization_id"],
        "source": analytics["source"],
        "prediction": analytics["prediction"],
        "trend": analytics["trend"],
        "latest": analytics["latest"],
        "read_only": True,
    }


def _demand_city_label(location: dict[str, Any] | None, fallback: str) -> str:
    payload = location or {}
    label = (
        str(payload.get("label") or payload.get("name") or payload.get("city") or fallback)
        .strip()
        or fallback
    )
    return label


def _demand_latest_zone(organization_id: str) -> str:
    snapshot = _STORE.latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        payload = snapshot.get("payload", {})
        if isinstance(payload, dict):
            zone = payload.get("primary_zone") or payload.get("zone") or payload.get("demand_zone")
            if zone:
                return str(zone)
    drivers = _STORE.list_driver_presence(organization_id=organization_id, limit=1)
    if drivers:
        location = drivers[0].get("location") or {}
        label = str(location.get("label") or location.get("name") or "").strip()
        if label:
            return label
    return "CBD"


def _demand_latest_trust_score(organization_id: str) -> int:
    trust = _STORE.latest_trust_score(organization_id=organization_id)
    if trust is not None:
        try:
            return int(trust.get("trust_score") or 92)
        except (TypeError, ValueError):
            return 92
    snapshot = _STORE.latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        try:
            return int(snapshot.get("trust_score") or 92)
        except (TypeError, ValueError):
            return 92
    return 92


def _demand_active_counts(organization_id: str) -> tuple[int, int, int]:
    rides = _STORE.list_rides(organization_id=organization_id, limit=100)
    active_rides = [
        ride
        for ride in rides
        if str(ride.get("status", "")).lower() not in {"completed", "cancelled"}
    ]
    completed_rides = [
        ride
        for ride in rides
        if str(ride.get("status", "")).lower() == "completed"
    ]
    active_drivers = [
        driver
        for driver in _STORE.list_driver_presence(organization_id=organization_id, limit=100)
        if str(driver.get("status", "")).lower() in {"online", "busy"}
    ]
    return len(active_rides), len(completed_rides), len(active_drivers)


def _demand_city_rows(organization_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
    fallback_zone = _demand_latest_zone(organization_id)
    rides = _STORE.list_rides(organization_id=organization_id, limit=limit)
    drivers = [
        row
        for row in _STORE.list_driver_presence(organization_id=organization_id, limit=limit)
        if str(row.get("status", "")).lower() in {"online", "busy"}
    ]
    ride_buckets: dict[str, list[dict[str, Any]]] = {}
    driver_buckets: dict[str, list[dict[str, Any]]] = {}
    for ride in rides:
        city = _demand_city_label(ride.get("pickup_location"), fallback_zone)
        ride_buckets.setdefault(city, []).append(ride)
    for driver in drivers:
        city = _demand_city_label(driver.get("location"), fallback_zone)
        driver_buckets.setdefault(city, []).append(driver)

    city_names = sorted(set(ride_buckets) | set(driver_buckets)) or [fallback_zone]
    latest_trust_score = _demand_latest_trust_score(organization_id)
    rows: list[dict[str, Any]] = []
    for city in city_names:
        city_rides = ride_buckets.get(city, [])
        city_drivers = driver_buckets.get(city, [])
        active_rides = [ride for ride in city_rides if str(ride.get("status", "")).lower() not in {"completed", "cancelled"}]
        completed_rides = [ride for ride in city_rides if str(ride.get("status", "")).lower() == "completed"]
        demand_ratio = (len(active_rides) + 1) / max(1, len(city_drivers) + 1)
        trust_adjustment = max(0.0, (latest_trust_score - 80) * 0.25)
        completion_adjustment = min(8.0, len(completed_rides) * 0.35)
        demand_index = _analytics_clamp((demand_ratio * 38.0) + trust_adjustment + completion_adjustment + 12.0)
        demand_level = (
            "high"
            if demand_index >= 70
            else "moderate"
            if demand_index >= 42
            else "low"
        )
        supply_gap = max(0, len(active_rides) - len(city_drivers))
        if demand_level == "high" and supply_gap > 0:
            recommendation = f"Shift supply toward {city}"
            reasoning = "Active ride pressure exceeds available drivers."
        elif demand_level == "moderate":
            recommendation = f"Hold balanced supply near {city}"
            reasoning = "The city is stable but still benefits from nearby coverage."
        else:
            recommendation = f"Maintain watch around {city}"
            reasoning = "Current pressure does not justify aggressive repositioning."
        rows.append(
            {
                "city": city,
                "active_rides": len(active_rides),
                "completed_rides": len(completed_rides),
                "active_drivers": len(city_drivers),
                "supply_gap": supply_gap,
                "demand_ratio": round(demand_ratio, 6),
                "demand_index": round(float(demand_index), 4),
                "demand_level": demand_level,
                "recommended_action": recommendation,
                "reason": reasoning,
                "trust_score": latest_trust_score,
            }
        )

    if not rows:
        rows.append(
            {
                "city": fallback_zone,
                "active_rides": 0,
                "completed_rides": 0,
                "active_drivers": 0,
                "supply_gap": 0,
                "demand_ratio": 0.0,
                "demand_index": 0.0,
                "demand_level": "low",
                "recommended_action": f"Maintain watch around {fallback_zone}",
                "reason": "No live city pressure is currently visible.",
                "trust_score": latest_trust_score,
            }
        )

    return sorted(rows, key=lambda row: (row["demand_index"], row["active_rides"], row["city"]), reverse=True)


def build_dashboard_demand_forecast(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    analytics = _build_dashboard_analytics_context(
        organization_id=org_id,
        source=source,
        snapshot_type="operator_dashboard",
        limit=limit,
    )
    city_rows = _demand_city_rows(org_id, limit=limit)
    active_rides, completed_rides, active_drivers = _demand_active_counts(org_id)
    top_city = city_rows[0]
    demand_index = float(top_city["demand_index"])
    demand_level = str(top_city["demand_level"])
    if demand_level == "high":
        urgency = "shift_supply"
    elif demand_level == "moderate":
        urgency = "hold_supply"
    else:
        urgency = "monitor"
    feature_vector = {
        "active_rides": active_rides,
        "completed_rides": completed_rides,
        "active_drivers": active_drivers,
        "trust_score": _demand_latest_trust_score(org_id),
        "coverage_score": int(analytics["latest"]["evidence_coverage"]) if analytics["latest"] else 0,
        "exception_pressure": int(analytics["latest"]["exception_pressure"]) if analytics["latest"] else 0,
        "zone_count": len(city_rows),
        "top_city_pressure": round(demand_index, 4),
    }
    forecast_windows = []
    base_rides = active_rides + max(0, completed_rides // 2)
    ratio_boost = max(0.0, demand_index / 25.0)
    for horizon, multiplier in (("15m", 0.35), ("1h", 0.85), ("4h", 1.55)):
        expected_rides = max(0, int(round(base_rides + (ratio_boost * multiplier) + (active_drivers * 0.25))))
        expected_supply_gap = max(0, int(round(expected_rides - max(1, active_drivers))))
        forecast_windows.append(
            {
                "horizon": horizon,
                "expected_rides": expected_rides,
                "expected_supply_gap": expected_supply_gap,
                "confidence": round(min(0.95, 0.72 + (0.04 if horizon == "15m" else 0.02 if horizon == "1h" else 0.0) + min(0.1, active_drivers / 50)), 2),
                "recommended_action": top_city["recommended_action"],
            }
        )
    realtime_analytics = {
        "view": "novatech_operator_realtime_analytics",
        "organization_id": org_id,
        "source": source or "all",
        "live_state": {
            "active_rides": active_rides,
            "completed_rides": completed_rides,
            "active_drivers": active_drivers,
            "zone": top_city["city"],
            "demand_level": demand_level,
            "demand_index": round(demand_index, 4),
            "supply_gap": top_city["supply_gap"],
            "trust_score": feature_vector["trust_score"],
        },
        "trend": analytics["trend"],
        "alerts": [insight["detail"] for insight in analytics["insights"][:3]],
        "updated_at": _now(),
        "projection_only": True,
        "read_only": True,
    }
    return {
        "view": "novatech_operator_demand_forecast",
        "organization_id": org_id,
        "source": source or "all",
        "model": {
            "name": "bounded_demand_forecast_ml",
            "version": "1.0.0",
            "mode": "deterministic_heuristic",
            "projection_only": True,
            "read_only": True,
        },
        "realtime_analytics": realtime_analytics,
        "city_forecasts": city_rows,
        "forecast_windows": forecast_windows,
        "feature_vector": feature_vector,
        "recommendation": {
            "urgency": urgency,
            "primary_city": top_city["city"],
            "action": top_city["recommended_action"],
            "reason": top_city["reason"],
        },
        "read_only": True,
        "projection_only": True,
    }


def _decision_risk_level(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _decision_lane_from_signals(
    *,
    trust_health: int,
    replay_health_score: int,
    evidence_coverage: int,
    exception_pressure: int,
    guard_count: int,
    missing_traces: int,
    risk_score: int,
    trust_trend: dict[str, Any],
) -> str:
    if (
        risk_score >= 75
        or trust_health < 55
        or replay_health_score < 55
        or exception_pressure >= 8
        or guard_count >= 3
        or missing_traces >= 6
    ):
        return "escalate"
    if (
        risk_score >= 50
        or trust_health < 70
        or replay_health_score < 70
        or exception_pressure >= 4
        or guard_count > 0
        or missing_traces > 0
    ):
        return "review"
    if risk_score >= 25 or evidence_coverage < 95 or trust_trend.get("direction") == "falling":
        return "watch"
    return "observe"


def _decision_priority_from_lane(lane: str) -> str:
    return {
        "observe": "low",
        "watch": "medium",
        "review": "high",
        "escalate": "critical",
    }.get(lane, "medium")


def _decision_action_from_lane(lane: str) -> str:
    return {
        "observe": "continue_monitoring",
        "watch": "increase_observation",
        "review": "open_operator_review",
        "escalate": "escalate_incident",
    }.get(lane, "increase_observation")


def _unique_items(*groups: list[str]) -> list[str]:
    items: list[str] = []
    for group in groups:
        for item in group:
            if item not in items:
                items.append(item)
    return items


def _build_dashboard_decision_context(
    *,
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    decision_type: str = "operator_decision",
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    analytics = _build_dashboard_analytics_context(
        organization_id=org_id,
        source=source,
        snapshot_type="operator_dashboard",
        limit=limit,
    )
    latest_analytics = analytics["latest"] or {
        "trust_score": 0,
        "trust_health": 0,
        "replay_health_score": 0,
        "evidence_coverage": 0,
        "exception_pressure": 0,
        "alert_count": 0,
        "active_drivers": 0,
        "completed_rides": 0,
        "total_rides": 0,
        "guard_count": 0,
        "replay_failures": 0,
        "hash_chain_failures": 0,
        "missing_traces": 0,
        "receipts_count": 0,
        "trace_count": 0,
    }
    decision_history = _STORE.list_ai_decision_snapshots(
        organization_id=org_id,
        source=source,
        decision_type=decision_type,
        limit=limit,
    )
    history = list(reversed(decision_history))
    latest = history[-1] if history else None
    risk_service = _risk_prediction_service()
    risk_prediction = risk_service.latest(organization_id=org_id, entity_type="organization")

    trust_score = int(latest_analytics.get("trust_score", 0))
    trust_health = int(latest_analytics.get("trust_health", 0))
    replay_health_score = int(latest_analytics.get("replay_health_score", 0))
    evidence_coverage = int(latest_analytics.get("evidence_coverage", 0))
    exception_pressure = int(latest_analytics.get("exception_pressure", 0))
    alert_count = int(latest_analytics.get("alert_count", 0))
    guard_count = int(latest_analytics.get("guard_count", 0))
    replay_failures = int(latest_analytics.get("replay_failures", 0))
    hash_chain_failures = int(latest_analytics.get("hash_chain_failures", 0))
    missing_traces = int(latest_analytics.get("missing_traces", 0))
    completed_rides = int(latest_analytics.get("completed_rides", 0))
    active_drivers = int(latest_analytics.get("active_drivers", 0))
    total_rides = int(latest_analytics.get("total_rides", 0))
    stability_index = _analytics_clamp(
        (trust_health * 0.35) + (replay_health_score * 0.35) + (evidence_coverage * 0.2)
        - (exception_pressure * 6)
        - (guard_count * 4)
        - (missing_traces * 2),
    )

    if risk_prediction is not None:
        risk_score = int(risk_prediction.get("risk_score", 0))
        confidence = round(float(risk_prediction.get("confidence", 0.0)), 2)
        risk_level = str(risk_prediction.get("risk_level") or _decision_risk_level(risk_score))
        risk_explanation = list(risk_prediction.get("explanation") or [])
        risk_features = dict(risk_prediction.get("features") or {})
    else:
        risk_score = _analytics_clamp(
            100
            - trust_health * 0.45
            - replay_health_score * 0.35
            - evidence_coverage * 0.12
            + exception_pressure * 7
            + guard_count * 6
            + missing_traces * 4,
        )
        confidence = round(
            max(0.55, min(0.92, 0.58 + min(0.2, len(history) / 40) - abs(analytics["trend"]["exceptions"]["slope"]) * 0.02)),
            2,
        )
        risk_level = _decision_risk_level(risk_score)
        risk_explanation = []
        risk_features = {
            "trust_score": trust_score,
            "replay_health_score": replay_health_score,
            "evidence_coverage": evidence_coverage,
        }

    lane = _decision_lane_from_signals(
        trust_health=trust_health,
        replay_health_score=replay_health_score,
        evidence_coverage=evidence_coverage,
        exception_pressure=exception_pressure,
        guard_count=guard_count,
        missing_traces=missing_traces,
        risk_score=risk_score,
        trust_trend=analytics["trend"]["trust"],
    )
    action = _decision_action_from_lane(lane)
    priority = _decision_priority_from_lane(lane)

    if lane == "observe":
        summary = "Operating signals are stable. Continue monitoring and preserve the current replay-backed band."
        recommended_actions = [
            "Maintain the current operating cadence.",
            "Keep live sampling active.",
            "Review the next polling cycle for drift.",
        ]
    elif lane == "watch":
        summary = "The system is still healthy, but trend drift deserves closer observation."
        recommended_actions = [
            "Increase observation on replay exceptions.",
            "Review evidence coverage against the current window.",
            "Keep the current release posture unchanged.",
        ]
    elif lane == "review":
        summary = "Replay, evidence, or guard pressure is visible. Open an operator review before widening activity."
        recommended_actions = [
            "Inspect the latest replay exception list.",
            "Verify evidence gaps and missing traces.",
            "Pause non-essential changes until the review closes.",
        ]
    else:
        summary = "Risk is elevated. Escalate to the operator lead and stabilize the surface before new changes proceed."
        recommended_actions = [
            "Escalate the incident to the operator lead.",
            "Isolate the affected trust window.",
            "Hold non-essential deployments until trust recovers.",
        ]

    watch_items = _unique_items(
        list(analytics["prediction"]["watch_items"]),
        [f"Risk level {risk_level}"] if risk_level else [],
        risk_explanation,
    )
    if not watch_items:
        watch_items = ["Maintain the current replay-backed operating band."]

    signal_map = {
        "trust_score": trust_score,
        "trust_health": trust_health,
        "replay_health_score": replay_health_score,
        "evidence_coverage": evidence_coverage,
        "exception_pressure": exception_pressure,
        "alert_count": alert_count,
        "guard_count": guard_count,
        "replay_failures": replay_failures,
        "hash_chain_failures": hash_chain_failures,
        "missing_traces": missing_traces,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence": confidence,
        "stability_index": stability_index,
        "completed_rides": completed_rides,
        "active_drivers": active_drivers,
        "total_rides": total_rides,
        "latest_risk_prediction": risk_prediction,
        "risk_features": risk_features,
    }

    current = {
        "decision_type": decision_type,
        "organization_id": org_id,
        "source": source or "all",
        "decision_lane": lane,
        "decision_action": action,
        "decision_priority": priority,
        "decision_summary": summary,
        "confidence": confidence,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "stability_index": stability_index,
        "recommended_actions": recommended_actions,
        "watch_items": watch_items,
        "advisory_only": True,
        "execution_authority": False,
        "signals": signal_map,
        "playbook": recommended_actions,
        "reasoning": {
            "trust_trend": analytics["trend"]["trust"],
            "evidence_trend": analytics["trend"]["evidence"],
            "exception_trend": analytics["trend"]["exceptions"],
            "risk_prediction": risk_prediction,
        },
        "analytics_latest": latest_analytics,
        "latest_record_id": latest["decision_id"] if latest else None,
    }

    return {
        "view": "novatech_operator_decision_engine",
        "organization_id": org_id,
        "source": source or "all",
        "current": current,
        "latest": latest,
        "history": {
            "count": len(history),
            "items": history,
            "source_breakdown": {
                item["source"]: sum(1 for row in history if row["source"] == item["source"])
                for item in history
            },
        },
        "signals": signal_map,
        "read_only": True,
        "projection_only": True,
    }


def build_dashboard_decisions(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    return _build_dashboard_decision_context(
        organization_id=organization_id,
        source=source,
        decision_type="operator_decision",
        limit=limit,
    )


def build_dashboard_decisions_history(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    decisions = _build_dashboard_decision_context(
        organization_id=organization_id,
        source=source,
        decision_type="operator_decision",
        limit=limit,
    )
    return {
        "view": "novatech_operator_decision_history",
        "organization_id": decisions["organization_id"],
        "source": decisions["source"],
        "current": decisions["current"],
        "latest": decisions["latest"],
        "history": decisions["history"],
        "signals": decisions["signals"],
        "read_only": True,
    }


def record_dashboard_decision_snapshot(
    *,
    payload: dict[str, Any],
    source: str,
    decision_type: str = "operator_decision",
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    context = _build_dashboard_decision_context(
        organization_id=org_id,
        source=source,
        decision_type=decision_type,
        limit=24,
    )
    current = context["current"]
    record_payload = {
        "trigger_payload": payload,
        "decision": current,
        "signals": context["signals"],
        "history_depth": context["history"]["count"],
    }
    return _STORE.store_ai_decision_snapshot(
        organization_id=org_id,
        source=source,
        decision_type=decision_type,
        decision_lane=current["decision_lane"],
        decision_action=current["decision_action"],
        decision_priority=current["decision_priority"],
        decision_summary=current["decision_summary"],
        trust_score=current["signals"]["trust_score"],
        trust_health=current["signals"]["trust_health"],
        replay_health_score=current["signals"]["replay_health_score"],
        evidence_coverage=current["signals"]["evidence_coverage"],
        exception_pressure=current["signals"]["exception_pressure"],
        alert_count=current["signals"]["alert_count"],
        guard_count=current["signals"]["guard_count"],
        replay_failures=current["signals"]["replay_failures"],
        hash_chain_failures=current["signals"]["hash_chain_failures"],
        missing_traces=current["signals"]["missing_traces"],
        risk_score=current["signals"]["risk_score"],
        risk_level=current["signals"]["risk_level"],
        confidence=current["signals"]["confidence"],
        stability_index=current["signals"]["stability_index"],
        recommended_actions=current["recommended_actions"],
        watch_items=current["watch_items"],
        payload=record_payload,
    )


def _decision_quality_band(score: int) -> str:
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "strong"
    if score >= 55:
        return "guarded"
    return "weak"


def _action_lane_from_decision_lane(lane: str) -> str:
    return {
        "observe": "monitor",
        "watch": "notify",
        "review": "prepare",
        "escalate": "safeguard",
    }.get(lane, "notify")


def _action_mode_from_quality(score: int) -> str:
    if score >= 85:
        return "controlled_autonomy"
    if score >= 70:
        return "guided_control"
    if score >= 55:
        return "guarded_control"
    return "hold_for_review"


def _control_signal_from_action_lane(action_lane: str, quality_band: str) -> str:
    if quality_band == "weak":
        return "require_operator_review"
    return {
        "monitor": "maintain_monitoring",
        "notify": "publish_watch_notification",
        "prepare": "open_operator_review",
        "safeguard": "publish_critical_safeguard",
    }.get(action_lane, "maintain_monitoring")


def _safety_gate_from_quality(action_lane: str, quality_band: str) -> str:
    if quality_band == "weak":
        return "hold"
    if action_lane == "safeguard":
        return "review"
    if quality_band == "guarded":
        return "guarded"
    return "pass"


def _history_alignment_score(
    history: list[dict[str, Any]],
    *,
    trust_health: int,
    replay_health_score: int,
    evidence_coverage: int,
) -> int:
    if not history:
        return _analytics_clamp((trust_health + replay_health_score + evidence_coverage) / 3)

    values: list[int] = []
    for item in history[:5]:
        values.append(int(item.get("stability_index", 0)))
        confidence = item.get("confidence")
        if confidence is not None:
            values.append(_analytics_clamp(float(confidence) * 100))
        calibrated_confidence = item.get("calibrated_confidence")
        if calibrated_confidence is not None:
            values.append(_analytics_clamp(float(calibrated_confidence) * 100))
    if not values:
        return _analytics_clamp((trust_health + replay_health_score + evidence_coverage) / 3)
    return _analytics_clamp(sum(values) / len(values))


def _action_priority_from_quality(action_lane: str, quality_band: str) -> str:
    if action_lane == "safeguard" or quality_band == "weak":
        return "critical"
    if action_lane == "prepare":
        return "high"
    if action_lane == "notify":
        return "medium"
    return "low"


def _execution_tier_from_action_context(
    *,
    action_lane: str,
    quality_band: str,
    calibrated_confidence: float,
    safety_gate: str,
) -> str:
    if safety_gate == "hold" or quality_band == "weak":
        return "advisory"
    if action_lane == "safeguard":
        return "supervised"
    if quality_band == "guarded" or calibrated_confidence < 0.75:
        return "assisted"
    if quality_band in {"strong", "excellent"} and calibrated_confidence >= 0.8:
        return "controlled"
    return "assisted"


def _safe_autonomy_thresholds(
    *,
    trust_health: int,
    replay_health_score: int,
    evidence_coverage: int,
    exception_pressure: int,
    alert_count: int,
    guard_count: int,
    decision_quality_score: int,
    calibrated_confidence: float,
    predicted_trust_score: int,
    predicted_evidence_coverage: int,
    predicted_exception_pressure: int,
    risk_score: int,
) -> dict[str, Any]:
    thresholds = {
        "trust_health": 88,
        "replay_health_score": 92,
        "evidence_coverage": 95,
        "exception_pressure_max": 2,
        "alert_count_max": 1,
        "guard_count_max": 0,
        "decision_quality_score": 82,
        "calibrated_confidence": 0.8,
        "predicted_trust_score": 90,
        "predicted_evidence_coverage": 95,
        "predicted_exception_pressure_max": 2,
        "risk_score_max": 25,
    }
    observed = {
        "trust_health": trust_health,
        "replay_health_score": replay_health_score,
        "evidence_coverage": evidence_coverage,
        "exception_pressure": exception_pressure,
        "alert_count": alert_count,
        "guard_count": guard_count,
        "decision_quality_score": decision_quality_score,
        "calibrated_confidence": round(calibrated_confidence, 2),
        "risk_score": risk_score,
    }
    predicted = {
        "predicted_trust_score": predicted_trust_score,
        "predicted_evidence_coverage": predicted_evidence_coverage,
        "predicted_exception_pressure": predicted_exception_pressure,
    }
    checks = {
        "trust_health": trust_health >= thresholds["trust_health"],
        "replay_health_score": replay_health_score >= thresholds["replay_health_score"],
        "evidence_coverage": evidence_coverage >= thresholds["evidence_coverage"],
        "exception_pressure": exception_pressure <= thresholds["exception_pressure_max"],
        "alert_count": alert_count <= thresholds["alert_count_max"],
        "guard_count": guard_count <= thresholds["guard_count_max"],
        "decision_quality_score": decision_quality_score >= thresholds["decision_quality_score"],
        "calibrated_confidence": calibrated_confidence >= thresholds["calibrated_confidence"],
        "predicted_trust_score": predicted_trust_score >= thresholds["predicted_trust_score"],
        "predicted_evidence_coverage": predicted_evidence_coverage >= thresholds["predicted_evidence_coverage"],
        "predicted_exception_pressure": predicted_exception_pressure <= thresholds["predicted_exception_pressure_max"],
        "risk_score": risk_score <= thresholds["risk_score_max"],
    }
    safe_to_autorun = all(checks.values())
    supervised_ready = (
        trust_health >= 80
        and replay_health_score >= 85
        and evidence_coverage >= 90
        and guard_count == 0
        and risk_score <= 40
    )
    autonomy_mode = "fully_autonomous" if safe_to_autorun else "supervised" if supervised_ready else "advisory"
    release_status = "enabled" if safe_to_autorun else "held"
    if safe_to_autorun:
        summary = "Predictive signals are inside safe thresholds. Fully autonomous execution can be enabled under audit control."
        recommended_next_step = "Allow fully autonomous allocation and keep audit replay active."
    elif supervised_ready:
        summary = "Predictive signals are promising, but one or more safe thresholds are not yet satisfied."
        recommended_next_step = "Stay in supervised mode and close the remaining evidence gap."
    else:
        summary = "Autonomous execution is held. Trust, replay, or evidence pressure is still outside the safe band."
        recommended_next_step = "Keep the surface advisory-only and continue monitoring the next cycle."

    return {
        "mode": autonomy_mode,
        "release_status": release_status,
        "safe_to_autorun": safe_to_autorun,
        "supervised_ready": supervised_ready,
        "summary": summary,
        "recommended_next_step": recommended_next_step,
        "thresholds": thresholds,
        "observed": observed,
        "predicted": predicted,
        "checks": checks,
        "advisory_only": not safe_to_autorun,
        "execution_authority": False,
        "read_only": True,
        "projection_only": True,
    }


def _build_driver_allocation_preview(
    *,
    organization_id: str,
    safe_to_autorun: bool,
    limit: int = 24,
) -> dict[str, Any]:
    drivers = [
        dict(driver)
        for driver in _STORE.list_driver_presence(organization_id=organization_id, status="online", limit=limit)
        if str(driver.get("status")) == "online"
    ]
    ranked_drivers = sorted(
        drivers,
        key=lambda driver: (
            float(driver.get("trust_score", 0.0) or 0.0),
            str(driver.get("updated_at") or ""),
            str(driver.get("driver_id") or ""),
        ),
        reverse=True,
    )
    selected_driver = ranked_drivers[0] if ranked_drivers else None
    allocation_mode = "autonomous" if safe_to_autorun and selected_driver else "supervised" if selected_driver else "held"
    readiness = "ready" if safe_to_autorun and selected_driver else "held"
    selected_driver_id = str(selected_driver.get("driver_id")) if selected_driver else None
    selected_driver_trust_score = int(float(selected_driver.get("trust_score", 0.0) or 0.0)) if selected_driver else 0
    target_zone = str(
        (selected_driver or {}).get("location", {}).get("label")
        or (selected_driver or {}).get("location", {}).get("name")
        or "CBD"
    )
    predictive_positioning = {
        "mode": "fully_autonomous" if safe_to_autorun and selected_driver else "guided" if selected_driver else "held",
        "target_zone": target_zone,
        "confidence": 0.93 if safe_to_autorun and selected_driver else 0.78 if selected_driver else 0.55,
        "instruction": (
            f"Move toward {target_zone} now"
            if safe_to_autorun and selected_driver
            else f"Stay near {target_zone} for guided coverage"
            if selected_driver
            else "Maintain current position until the system detects stronger demand"
        ),
        "reason": (
            "High demand and trusted supply support autonomous positioning"
            if safe_to_autorun and selected_driver
            else "Demand is stable enough for guided positioning"
            if selected_driver
            else "Autonomous positioning is not yet justified"
        ),
        "projection_only": True,
        "read_only": True,
    }
    candidate_drivers = [
        {
            "driver_id": str(driver.get("driver_id") or ""),
            "trust_score": int(float(driver.get("trust_score", 0.0) or 0.0)),
            "status": str(driver.get("status") or "unknown"),
            "location": driver.get("location") or {},
        }
        for driver in ranked_drivers[:3]
    ]
    if safe_to_autorun and selected_driver:
        reason = "Safe thresholds cleared. The system can auto-allocate the highest-trust online driver."
    elif selected_driver:
        reason = "A best available driver is identified, but execution remains held until the safe band clears."
    else:
        reason = "No online driver is available for autonomous allocation."
    return {
        "mode": allocation_mode,
        "readiness": readiness,
        "enabled": bool(safe_to_autorun and selected_driver),
        "available_drivers": len(ranked_drivers),
        "selected_driver_id": selected_driver_id,
        "selected_driver_trust_score": selected_driver_trust_score,
        "candidate_drivers": candidate_drivers,
        "predictive_positioning": predictive_positioning,
        "reason": reason,
        "projection_only": True,
        "read_only": True,
    }


def _build_city_automation_projection(
    *,
    organization_id: str,
    safe_to_autorun: bool,
    limit: int = 24,
) -> dict[str, Any]:
    drivers = [
        dict(driver)
        for driver in _STORE.list_driver_presence(organization_id=organization_id, status="online", limit=limit)
        if str(driver.get("status")) == "online"
    ]
    active_rides = len(
        [
            ride
            for ride in _STORE.list_rides(organization_id=organization_id, limit=limit)
            if str(ride.get("status") or "").lower() not in {"completed", "cancelled"}
        ]
    )
    zone_candidates: list[str] = []
    for driver in drivers:
        location = driver.get("location") or {}
        label = str(location.get("label") or location.get("name") or "").strip()
        if label and label not in zone_candidates:
            zone_candidates.append(label)
    snapshot = _STORE.latest_dashboard_analytics_snapshot(organization_id=organization_id)
    payload = snapshot.get("payload", {}) if snapshot else {}
    if not zone_candidates and isinstance(payload, dict):
        fallback_zone = payload.get("primary_zone") or payload.get("zone") or payload.get("demand_zone")
        if fallback_zone:
            zone_candidates.append(str(fallback_zone))
    if not zone_candidates:
        zone_candidates.append("CBD")
    trust_scores = [int(float(driver.get("trust_score", 0.0) or 0.0)) for driver in drivers]
    average_trust = int(sum(trust_scores) / len(trust_scores)) if trust_scores else 92
    demand_level = "high" if active_rides >= 5 and len(drivers) >= 3 else "moderate" if active_rides >= 2 else "low"
    coverage_score = min(
        100,
        (len(drivers) * 18)
        + (len(zone_candidates) * 12)
        + (average_trust // 2)
        + (10 if demand_level == "high" else 5 if demand_level == "moderate" else 0),
    )
    zero_operator_mode = bool(safe_to_autorun and len(drivers) >= 3 and coverage_score >= 75)
    city_mode = "zero_operator" if zero_operator_mode else "city_autonomous" if safe_to_autorun and coverage_score >= 60 else "city_supervised" if drivers else "city_held"
    recommended_zone = zone_candidates[0]
    if zero_operator_mode:
        instruction = f"Keep city automation active and rebalance drivers toward {recommended_zone}"
        reason = "Safe thresholds and city coverage support zero-operator automation"
    elif safe_to_autorun and drivers:
        instruction = f"Autonomously rebalance supply toward {recommended_zone}"
        reason = "Autonomy is enabled but city coverage is still below zero-operator mode"
    elif drivers:
        instruction = f"Maintain operator-supervised automation around {recommended_zone}"
        reason = "Automation is available but still requires operator oversight"
    else:
        instruction = "Hold city automation until enough drivers come online"
        reason = "No active city supply is available"
    return {
        "mode": city_mode,
        "zero_operator_mode": zero_operator_mode,
        "coverage_score": coverage_score,
        "active_drivers": len(drivers),
        "active_rides": active_rides,
        "city_zones": zone_candidates,
        "recommended_zone": recommended_zone,
        "instruction": instruction,
        "reason": reason,
        "bounded_actions": [
            "reposition drivers toward demand",
            "expand coverage across verified zones",
            "hold operator escalation until a threshold breach",
        ],
        "prediction": {
            "city_zone_count": len(zone_candidates),
            "city_trust_score": average_trust,
            "coverage_score": coverage_score,
            "demand_level": demand_level,
        },
        "projection_only": True,
        "read_only": True,
    }


def _build_multi_city_orchestration_projection(
    *,
    organization_id: str,
    safe_to_autorun: bool,
    limit: int = 24,
) -> dict[str, Any]:
    drivers = [
        dict(driver)
        for driver in _STORE.list_driver_presence(organization_id=organization_id, status="online", limit=limit)
        if str(driver.get("status")) == "online"
    ]
    active_rides = [
        dict(ride)
        for ride in _STORE.list_rides(organization_id=organization_id, limit=limit)
        if str(ride.get("status") or "").lower() not in {"completed", "cancelled"}
    ]
    city_map: dict[str, dict[str, Any]] = {}
    for driver in drivers:
        location = driver.get("location") or {}
        label = str(location.get("label") or location.get("name") or "CBD").strip() or "CBD"
        city_bucket = city_map.setdefault(
            label,
            {
                "city": label,
                "drivers": 0,
                "rides": 0,
                "average_trust_score": 0,
            },
        )
        city_bucket["drivers"] += 1
        city_bucket["average_trust_score"] += int(float(driver.get("trust_score", 0.0) or 0.0))
    for ride in active_rides:
        pickup = ride.get("pickup_location") or {}
        label = str(pickup.get("label") or pickup.get("name") or "CBD").strip() or "CBD"
        city_bucket = city_map.setdefault(
            label,
            {
                "city": label,
                "drivers": 0,
                "rides": 0,
                "average_trust_score": 0,
            },
        )
        city_bucket["rides"] += 1
    cities = []
    for city in sorted(city_map.values(), key=lambda item: (-int(item["drivers"]), item["city"])):
        drivers_count = int(city["drivers"])
        city["average_trust_score"] = int(city["average_trust_score"] / drivers_count) if drivers_count else 0
        city["coverage_score"] = min(100, (drivers_count * 22) + (int(city["rides"]) * 4) + (city["average_trust_score"] // 2))
        city["mode"] = (
            "zero_operator"
            if safe_to_autorun and drivers_count >= 3 and city["coverage_score"] >= 75
            else "city_autonomous"
            if safe_to_autorun and drivers_count >= 2
            else "city_supervised"
            if drivers_count > 0
            else "city_held"
        )
        cities.append(city)
    city_count = len(cities)
    active_city_count = len([city for city in cities if city["drivers"] > 0])
    global_coverage = min(
        100,
        sum(int(city["coverage_score"]) for city in cities) // city_count if city_count else 0,
    )
    global_trust = (
        sum(int(city["average_trust_score"]) for city in cities) // city_count if city_count else 92
    )
    multi_city_mode = (
        "global_zero_operator"
        if safe_to_autorun and active_city_count >= 2 and global_coverage >= 75
        else "global_autonomous"
        if safe_to_autorun and active_city_count >= 2
        else "global_supervised"
        if active_city_count > 0
        else "global_held"
    )
    outcome_learning = build_outcome_learning(organization_id=organization_id, limit=limit)
    learning = outcome_learning.get("learning", {})
    outcome_current = outcome_learning.get("current", {})
    recommendations = list(learning.get("recommendations", []))
    watch_items = list(learning.get("watch_items", []))
    if multi_city_mode == "global_zero_operator":
        instruction = "Keep multi-city orchestration active and rebalance cities toward the highest coverage zones"
        reason = "Global coverage and trust support zero-operator orchestration"
    elif multi_city_mode == "global_autonomous":
        instruction = "Autonomously rebalance supply across cities"
        reason = "Multi-city supply is healthy enough for autonomous orchestration"
    elif multi_city_mode == "global_supervised":
        instruction = "Hold supervised orchestration across active cities"
        reason = "Orchestration is available but still requires oversight"
    else:
        instruction = "Hold orchestration until more cities come online"
        reason = "No active multi-city supply is available"
    return {
        "mode": multi_city_mode,
        "multi_city_ready": bool(active_city_count >= 2 and safe_to_autorun),
        "city_count": city_count,
        "active_city_count": active_city_count,
        "active_drivers": len(drivers),
        "active_rides": len(active_rides),
        "city_map": cities,
        "primary_city": cities[0]["city"] if cities else "CBD",
        "global_coverage_score": global_coverage,
        "global_trust_score": global_trust,
        "instruction": instruction,
        "reason": reason,
        "global_learning": {
            "band": learning.get("band", "hold"),
            "cycle": list(learning.get("cycle", [])),
            "recommendations": recommendations,
            "watch_items": watch_items,
            "outcome_band": outcome_current.get("outcome_band", "guarded"),
            "outcome_score": int(outcome_current.get("outcome_score", 0)),
            "measurement_summary": outcome_current.get("measurement_summary", ""),
            "recalibration_notes": list(learning.get("recalibration_notes", [])),
            "projection_only": True,
            "read_only": True,
        },
        "prediction": {
            "city_count": city_count,
            "active_city_count": active_city_count,
            "coverage_score": global_coverage,
            "trust_score": global_trust,
            "learning_band": learning.get("band", "hold"),
        },
        "bounded_actions": [
            "rebalance drivers across verified city clusters",
            "promote learning signals into city planning",
            "hold operator escalation until the safety band breaks",
        ],
        "projection_only": True,
        "read_only": True,
    }


def _build_dashboard_autonomy_context(
    *,
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    analytics = _build_dashboard_analytics_context(
        organization_id=org_id,
        source=source,
        snapshot_type="operator_dashboard",
        limit=limit,
    )
    decision_context = _build_dashboard_decision_context(
        organization_id=org_id,
        source=source,
        decision_type="operator_decision",
        limit=limit,
    )
    action_context = _build_dashboard_action_context(
        organization_id=org_id,
        source=source,
        action_type="controlled_autonomous_action",
        limit=limit,
    )
    prediction = analytics["prediction"]
    current_decision = decision_context["current"]
    current_action = action_context["current"]
    autonomy = _safe_autonomy_thresholds(
        trust_health=int(current_action.get("trust_health", current_decision["signals"].get("trust_health", 0))),
        replay_health_score=int(
            current_action.get("replay_health_score", current_decision["signals"].get("replay_health_score", 0))
        ),
        evidence_coverage=int(
            current_action.get("evidence_coverage", current_decision["signals"].get("evidence_coverage", 0))
        ),
        exception_pressure=int(
            current_action.get("exception_pressure", current_decision["signals"].get("exception_pressure", 0))
        ),
        alert_count=int(current_action.get("alert_count", current_decision["signals"].get("alert_count", 0))),
        guard_count=int(current_action.get("guard_count", current_decision["signals"].get("guard_count", 0))),
        decision_quality_score=int(current_action.get("decision_quality_score", 0)),
        calibrated_confidence=float(current_action.get("calibrated_confidence", 0.0)),
        predicted_trust_score=int(prediction.get("predicted_trust_score", 0)),
        predicted_evidence_coverage=int(prediction.get("predicted_evidence_coverage", 0)),
        predicted_exception_pressure=int(prediction.get("predicted_exception_pressure", 0)),
        risk_score=int(current_decision.get("risk_score", 0)),
    )
    driver_allocation = _build_driver_allocation_preview(
        organization_id=org_id,
        safe_to_autorun=bool(autonomy.get("safe_to_autorun", False)),
        limit=limit,
    )
    city_automation = _build_city_automation_projection(
        organization_id=org_id,
        safe_to_autorun=bool(autonomy.get("safe_to_autorun", False)),
        limit=limit,
    )
    multi_city_orchestration = _build_multi_city_orchestration_projection(
        organization_id=org_id,
        safe_to_autorun=bool(autonomy.get("safe_to_autorun", False)),
        limit=limit,
    )

    return {
        "view": "novatech_operator_autonomy",
        "organization_id": org_id,
        "source": source or "all",
        "decision": current_decision,
        "action": current_action,
        "prediction": prediction,
        "autonomy": autonomy,
        "driver_allocation": driver_allocation,
        "city_automation": city_automation,
        "multi_city_orchestration": multi_city_orchestration,
        "safety_gate": current_action.get("safety_gate", "hold"),
        "execution_tier": current_action.get("execution_tier", "advisory"),
        "execution_tier_ready": bool(current_action.get("execution_tier_ready", False)),
        "read_only": True,
        "projection_only": True,
    }


def _build_dashboard_action_context(
    *,
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    action_type: str = "controlled_autonomous_action",
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    decision_context = _build_dashboard_decision_context(
        organization_id=org_id,
        source=source,
        decision_type="operator_decision",
        limit=limit,
    )
    decision_current = decision_context["current"]
    decision_latest = decision_context["latest"] or {}
    decision_history = list(decision_context["history"]["items"])
    action_history = _STORE.list_ai_action_snapshots(
        organization_id=org_id,
        source=source,
        action_type=action_type,
        limit=limit,
    )
    history = list(reversed(action_history))
    latest = history[-1] if history else None

    trust_score = int(decision_current["signals"].get("trust_score", 0))
    trust_health = int(decision_current["signals"].get("trust_health", 0))
    replay_health_score = int(decision_current["signals"].get("replay_health_score", 0))
    evidence_coverage = int(decision_current["signals"].get("evidence_coverage", 0))
    exception_pressure = int(decision_current["signals"].get("exception_pressure", 0))
    alert_count = int(decision_current["signals"].get("alert_count", 0))
    guard_count = int(decision_current["signals"].get("guard_count", 0))
    replay_failures = int(decision_current["signals"].get("replay_failures", 0))
    hash_chain_failures = int(decision_current["signals"].get("hash_chain_failures", 0))
    missing_traces = int(decision_current["signals"].get("missing_traces", 0))
    stability_index = int(decision_current["signals"].get("stability_index", 0))
    decision_lane = str(decision_current.get("decision_lane", "observe"))
    decision_priority = str(decision_current.get("decision_priority", "low"))
    raw_confidence = float(decision_current.get("confidence", 0.0))
    evidence_alignment_score = _analytics_clamp(
        evidence_coverage
        - missing_traces * 4
        - replay_failures * 6
        - hash_chain_failures * 5
        - guard_count * 4,
    )
    history_alignment_score = _history_alignment_score(
        history or decision_history,
        trust_health=trust_health,
        replay_health_score=replay_health_score,
        evidence_coverage=evidence_coverage,
    )
    decision_quality_score = _analytics_clamp(
        (trust_health * 0.24)
        + (replay_health_score * 0.24)
        + (evidence_alignment_score * 0.28)
        + (history_alignment_score * 0.18)
        + (stability_index * 0.06),
    )
    quality_band = _decision_quality_band(decision_quality_score)
    calibrated_confidence = round(
        max(
            0.1,
            min(
                0.99,
                (raw_confidence * 0.55)
                + (decision_quality_score / 100 * 0.35)
                + (evidence_alignment_score / 100 * 0.1),
            ),
        ),
        2,
    )
    action_lane = _action_lane_from_decision_lane(decision_lane)
    action_mode = _action_mode_from_quality(decision_quality_score)
    control_signal = _control_signal_from_action_lane(action_lane, quality_band)
    safety_gate = _safety_gate_from_quality(action_lane, quality_band)
    automation_tier = {"monitor": 0, "notify": 1, "prepare": 2, "safeguard": 3}.get(action_lane, 1)
    action_priority = _action_priority_from_quality(action_lane, quality_band)
    execution_tier = _execution_tier_from_action_context(
        action_lane=action_lane,
        quality_band=quality_band,
        calibrated_confidence=calibrated_confidence,
        safety_gate=safety_gate,
    )
    execution_tier_ready = execution_tier == "controlled" and safety_gate == "pass"
    execution_tier_summary = {
        "advisory": "The control plane stays read-only and only explains the current state.",
        "assisted": "The control plane can recommend limited, supervised follow-up actions.",
        "controlled": "The control plane is ready for tightly bounded, operator-supervised execution.",
        "supervised": "The control plane requires explicit human supervision before any escalation.",
    }.get(execution_tier, "The control plane remains read-only.")
    execution_tier_controls = {
        "advisory": [
            "Observe the current operating window.",
            "Keep the dashboard projection-only.",
        ],
        "assisted": [
            "Recommend a limited review action.",
            "Refresh evidence before widening scope.",
        ],
        "controlled": [
            "Allow only bounded, operator-supervised control handoff.",
            "Keep execution authority disabled until the operator confirms.",
        ],
        "supervised": [
            "Escalate to a human reviewer.",
            "Hold automated changes until the safety gate clears.",
        ],
    }.get(execution_tier, ["Keep the dashboard projection-only."])
    calibration_notes = _unique_items(
        [
            f"Quality band {quality_band}",
            f"Evidence alignment {evidence_alignment_score}",
            f"History alignment {history_alignment_score}",
        ],
        decision_current.get("watch_items", []),
    )
    if not calibration_notes:
        calibration_notes = ["Decision quality calibration is awaiting more persistent history."]

    control_actions = {
        "monitor": [
            "Maintain the current monitoring cadence.",
            "Keep the dashboard on read-only projection mode.",
        ],
        "notify": [
            "Publish a watch notification to the operator surface.",
            "Increase live observation for the next window.",
        ],
        "prepare": [
            "Open an operator review for the current trust window.",
            "Refresh evidence before widening activity.",
        ],
        "safeguard": [
            "Escalate the incident to the operator lead.",
            "Hold non-essential changes until calibration recovers.",
        ],
    }.get(action_lane, ["Maintain the current monitoring cadence."])

    operator_guidance = _unique_items(
        list(decision_current.get("recommended_actions") or []),
        control_actions,
        calibration_notes,
    )
    quality_summary = (
        f"Evidence-calibrated decision quality is {decision_quality_score}/100 "
        f"with a {quality_band} band, {execution_tier} execution tier, and {round(calibrated_confidence * 100)}% calibrated confidence."
    )
    risk_prediction = dict(
        decision_current.get("reasoning", {}).get("risk_prediction")
        or decision_current["signals"].get("latest_risk_prediction")
        or {}
    )
    predicted_trust_score = int(
        risk_prediction.get("features", {}).get("trust_score", decision_current["signals"].get("trust_score", trust_score))
    )
    predicted_evidence_coverage = int(
        risk_prediction.get("features", {}).get("evidence_coverage", evidence_coverage)
    )
    predicted_exception_pressure = int(
        risk_prediction.get("features", {}).get("exception_pressure", exception_pressure)
    )
    autonomy = _safe_autonomy_thresholds(
        trust_health=trust_health,
        replay_health_score=replay_health_score,
        evidence_coverage=evidence_coverage,
        exception_pressure=exception_pressure,
        alert_count=alert_count,
        guard_count=guard_count,
        decision_quality_score=decision_quality_score,
        calibrated_confidence=calibrated_confidence,
        predicted_trust_score=predicted_trust_score,
        predicted_evidence_coverage=predicted_evidence_coverage,
        predicted_exception_pressure=predicted_exception_pressure,
        risk_score=int(decision_current["signals"].get("risk_score", 0)),
    )

    current = {
        "action_type": action_type,
        "organization_id": org_id,
        "source": source or "all",
        "decision_id": decision_latest.get("latest_record_id") or decision_current.get("latest_record_id"),
        "decision_lane": decision_lane,
        "decision_priority": decision_priority,
        "action_lane": action_lane,
        "action_mode": action_mode,
        "action_priority": action_priority,
        "action_summary": quality_summary,
        "control_signal": control_signal,
        "safety_gate": safety_gate,
        "automation_tier": automation_tier,
        "execution_tier": execution_tier,
        "execution_tier_ready": execution_tier_ready,
        "execution_tier_summary": execution_tier_summary,
        "execution_tier_controls": execution_tier_controls,
        "autonomy": autonomy,
        "decision_quality_score": decision_quality_score,
        "evidence_alignment_score": evidence_alignment_score,
        "calibrated_confidence": calibrated_confidence,
        "history_alignment_score": history_alignment_score,
        "quality_band": quality_band,
        "decision_quality": {
            "score": decision_quality_score,
            "band": quality_band,
            "calibrated_confidence": calibrated_confidence,
            "evidence_alignment_score": evidence_alignment_score,
            "history_alignment_score": history_alignment_score,
            "trust_alignment_score": trust_health,
            "replay_alignment_score": replay_health_score,
            "evidence_calibrated": True,
            "summary": quality_summary,
        },
        "decision": decision_current,
        "control_actions": control_actions,
        "operator_guidance": operator_guidance,
        "recommended_actions": list(decision_current.get("recommended_actions") or []),
        "watch_items": _unique_items(
            list(decision_current.get("watch_items") or []),
            calibration_notes,
        ),
        "advisory_only": True,
        "execution_authority": False,
        "read_only": True,
        "projection_only": True,
        "signals": {
            **decision_current["signals"],
            "decision_quality_score": decision_quality_score,
            "evidence_alignment_score": evidence_alignment_score,
            "calibrated_confidence": calibrated_confidence,
            "history_alignment_score": history_alignment_score,
            "quality_band": quality_band,
            "execution_tier": execution_tier,
            "execution_tier_ready": execution_tier_ready,
            "autonomy_mode": autonomy["mode"],
            "autonomy_safe_to_autorun": autonomy["safe_to_autorun"],
            "safe_thresholds": autonomy["thresholds"],
            "safe_threshold_checks": autonomy["checks"],
            "action_lane": action_lane,
            "action_mode": action_mode,
            "control_signal": control_signal,
            "safety_gate": safety_gate,
            "predicted_trust_score": predicted_trust_score,
            "predicted_evidence_coverage": predicted_evidence_coverage,
            "predicted_exception_pressure": predicted_exception_pressure,
        },
        "reasoning": {
            "decision": decision_current["reasoning"],
            "calibration": {
                "quality_band": quality_band,
                "decision_quality_score": decision_quality_score,
                "evidence_alignment_score": evidence_alignment_score,
                "history_alignment_score": history_alignment_score,
                "calibrated_confidence": calibrated_confidence,
                "raw_confidence": raw_confidence,
                "safety_gate": safety_gate,
                "execution_tier": execution_tier,
                "execution_tier_ready": execution_tier_ready,
            },
        },
        "latest_record_id": latest["action_id"] if latest else None,
    }

    return {
        "view": "novatech_operator_action_engine",
        "organization_id": org_id,
        "source": source or "all",
        "current": current,
        "latest": latest,
        "history": {
            "count": len(history),
            "items": history,
            "source_breakdown": {
                item["source"]: sum(1 for row in history if row["source"] == item["source"])
                for item in history
            },
        },
        "signals": current["signals"],
        "read_only": True,
        "projection_only": True,
    }


def _outcome_band_from_score(score: int) -> str:
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "strong"
    if score >= 55:
        return "guarded"
    return "weak"


def _outcome_status_from_score(score: int) -> str:
    if score >= 85:
        return "measured"
    if score >= 70:
        return "learning"
    if score >= 55:
        return "review"
    return "recalibrate"


def _learning_band_from_outcome(
    *,
    outcome_score: int,
    trust_trend: dict[str, Any],
    exception_pressure: int,
) -> str:
    if outcome_score >= 85 and trust_trend.get("direction") == "rising" and exception_pressure <= 1:
        return "recalibrate"
    if outcome_score >= 70 and trust_trend.get("direction") != "falling":
        return "learn"
    if outcome_score >= 55:
        return "watch"
    return "hold"


def _build_outcome_context(
    *,
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    outcome_type: str = "measured_outcome",
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    analytics_context = _build_dashboard_analytics_context(
        organization_id=org_id,
        source=source,
        snapshot_type="operator_dashboard",
        limit=limit,
    )
    decision_context = _build_dashboard_decision_context(
        organization_id=org_id,
        source=source,
        decision_type="operator_decision",
        limit=limit,
    )
    action_context = _build_dashboard_action_context(
        organization_id=org_id,
        source=source,
        action_type="controlled_autonomous_action",
        limit=limit,
    )
    stored_outcomes = _STORE.list_outcome_snapshots(
        organization_id=org_id,
        source=source,
        outcome_type=outcome_type,
        limit=limit,
    )
    history = list(reversed(stored_outcomes))
    latest = history[-1] if history else None
    latest_analytics = analytics_context["latest"] or {
        "trust_score": 0,
        "trust_health": 0,
        "replay_health_score": 0,
        "evidence_coverage": 0,
        "exception_pressure": 0,
        "alert_count": 0,
        "guard_count": 0,
        "replay_failures": 0,
        "hash_chain_failures": 0,
        "missing_traces": 0,
        "receipts_count": 0,
        "trace_count": 0,
    }
    current_action = action_context["current"]
    current_decision = decision_context["current"]

    trust_score = int(latest_analytics.get("trust_score", 0))
    trust_health = int(latest_analytics.get("trust_health", 0))
    replay_health_score = int(latest_analytics.get("replay_health_score", 0))
    evidence_coverage = int(latest_analytics.get("evidence_coverage", 0))
    exception_pressure = int(latest_analytics.get("exception_pressure", 0))
    decision_quality_score = int(current_action.get("decision_quality_score", 0))
    evidence_alignment_score = int(current_action.get("evidence_alignment_score", 0))
    calibrated_confidence = float(current_action.get("calibrated_confidence", 0.0))
    history_alignment_score = int(current_action.get("history_alignment_score", 0))
    outcome_score = _analytics_clamp(
        (decision_quality_score * 0.4)
        + (trust_health * 0.2)
        + (replay_health_score * 0.18)
        + (evidence_coverage * 0.14)
        + (history_alignment_score * 0.08)
        - (exception_pressure * 3),
    )
    outcome_band = _outcome_band_from_score(outcome_score)
    learning_band = _learning_band_from_outcome(
        outcome_score=outcome_score,
        trust_trend=analytics_context["trend"]["trust"],
        exception_pressure=exception_pressure,
    )
    outcome_status = _outcome_status_from_score(outcome_score)

    measurement_summary = (
        f"Outcome score {outcome_score}/100 from trust {trust_score}, replay health {replay_health_score}, "
        f"and evidence coverage {evidence_coverage}%."
    )
    learning_actions = {
        "excellent": [
            "Preserve the current control band.",
            "Recalibrate only when new evidence arrives.",
        ],
        "strong": [
            "Continue learning from the current window.",
            "Keep the next review cycle active.",
        ],
        "guarded": [
            "Review exception pressure before widening scope.",
            "Keep the learning loop on watch.",
        ],
        "weak": [
            "Hold further automation changes.",
            "Recalibrate before the next operator review.",
        ],
    }.get(
        outcome_band,
        ["Maintain the current measurement loop."],
    )
    recalibration_notes = _unique_items(
        [
            f"Outcome band {outcome_band}",
            f"Learning band {learning_band}",
            f"Decision quality {decision_quality_score}",
            f"Calibrated confidence {round(calibrated_confidence * 100)}%",
        ],
        current_action.get("watch_items", []),
        analytics_context["prediction"]["watch_items"],
    )
    if not recalibration_notes:
        recalibration_notes = ["Outcome learning is awaiting more persistent evidence."]
    watch_items = _unique_items(
        list(current_action.get("watch_items") or []),
        list(analytics_context["prediction"]["watch_items"] or []),
        [f"Outcome status {outcome_status}"],
    )
    if not watch_items:
        watch_items = ["Maintain the current observation loop."]

    outcome_current = {
        "outcome_type": outcome_type,
        "organization_id": org_id,
        "source": source or "all",
        "decision_id": current_action.get("decision_id") or current_decision.get("latest_record_id"),
        "action_id": current_action.get("latest_record_id") or (latest["action_id"] if latest else ""),
        "outcome_status": outcome_status,
        "outcome_band": outcome_band,
        "learning_band": learning_band,
        "outcome_score": outcome_score,
        "measurement_summary": measurement_summary,
        "decision_quality_score": decision_quality_score,
        "evidence_alignment_score": evidence_alignment_score,
        "calibrated_confidence": calibrated_confidence,
        "history_alignment_score": history_alignment_score,
        "trust_score": trust_score,
        "trust_health": trust_health,
        "replay_health_score": replay_health_score,
        "evidence_coverage": evidence_coverage,
        "exception_pressure": exception_pressure,
        "execution_tier": current_action.get("execution_tier", "advisory"),
        "execution_tier_ready": bool(current_action.get("execution_tier_ready", False)),
        "control_signal": current_action.get("control_signal", "maintain_monitoring"),
        "safety_gate": current_action.get("safety_gate", "hold"),
        "learning_actions": learning_actions,
        "recalibration_notes": recalibration_notes,
        "watch_items": watch_items,
        "signals": {
            **current_action.get("signals", {}),
            "outcome_score": outcome_score,
            "outcome_band": outcome_band,
            "learning_band": learning_band,
            "outcome_status": outcome_status,
        },
        "reasoning": {
            "decision": current_action.get("reasoning", {}),
            "learning": {
                "trend": analytics_context["trend"],
                "prediction": analytics_context["prediction"],
                "measurement_summary": measurement_summary,
            },
        },
        "advisory_only": True,
        "execution_authority": False,
        "read_only": True,
        "projection_only": True,
    }

    outcome_trend = _analytics_series([item["outcome_score"] for item in history] if history else [outcome_score])
    registry = {
        "count": len(history),
        "items": history,
        "source_breakdown": {
            item["source"]: sum(1 for row in history if row["source"] == item["source"])
            for item in history
        },
    }
    if latest is None:
        latest = outcome_current
    scoring = {
        "current": outcome_current,
        "band": outcome_band,
        "score": outcome_score,
        "trend": outcome_trend,
        "breakdown": {
            "decision_quality_score": decision_quality_score,
            "trust_health": trust_health,
            "replay_health_score": replay_health_score,
            "evidence_coverage": evidence_coverage,
            "history_alignment_score": history_alignment_score,
            "exception_pressure_penalty": exception_pressure * 3,
        },
    }
    learning = {
        "cycle": [
            "observe",
            "decide",
            "recommend",
            "measure_outcome",
            "learn",
            "recalibrate",
        ],
        "band": learning_band,
        "trend": outcome_trend,
        "recommendations": learning_actions,
        "recalibration_notes": recalibration_notes,
        "watch_items": watch_items,
    }
    replay_hash = sha256(
        json.dumps(
            {
                "organization_id": org_id,
                "source": source,
                "outcome_type": outcome_type,
                "states": learning["cycle"],
                "score": outcome_score,
                "band": outcome_band,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    replay = {
        "states": learning["cycle"],
        "replayable": True,
        "replay_hash": replay_hash,
        "latest_action_id": outcome_current["action_id"],
        "latest_decision_id": outcome_current["decision_id"],
        "outcome_score": outcome_score,
        "outcome_band": outcome_band,
        "status": outcome_status,
    }
    return {
        "view": "novatech_outcome_intelligence",
        "organization_id": org_id,
        "source": source or "all",
        "current": outcome_current,
        "latest": latest,
        "history": registry,
        "registry": registry,
        "learning": learning,
        "scoring": scoring,
        "replay": replay,
        "signals": outcome_current["signals"],
        "read_only": True,
        "projection_only": True,
    }


def build_outcome_status(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    return _build_outcome_context(
        organization_id=organization_id,
        source=source,
        outcome_type="measured_outcome",
        limit=limit,
    )


def build_outcome_registry(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    outcome = _build_outcome_context(
        organization_id=organization_id,
        source=source,
        outcome_type="measured_outcome",
        limit=limit,
    )
    return {
        "view": "novatech_outcome_registry",
        "organization_id": outcome["organization_id"],
        "source": outcome["source"],
        "current": outcome["current"],
        "latest": outcome["latest"],
        "history": outcome["history"],
        "registry": outcome["registry"],
        "read_only": True,
        "projection_only": True,
    }


def build_outcome_learning(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    outcome = _build_outcome_context(
        organization_id=organization_id,
        source=source,
        outcome_type="measured_outcome",
        limit=limit,
    )
    return {
        "view": "novatech_outcome_learning",
        "organization_id": outcome["organization_id"],
        "source": outcome["source"],
        "current": outcome["current"],
        "latest": outcome["latest"],
        "history": outcome["history"],
        "learning": outcome["learning"],
        "read_only": True,
        "projection_only": True,
    }


def build_outcome_scoring(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    outcome = _build_outcome_context(
        organization_id=organization_id,
        source=source,
        outcome_type="measured_outcome",
        limit=limit,
    )
    return {
        "view": "novatech_outcome_scoring",
        "organization_id": outcome["organization_id"],
        "source": outcome["source"],
        "current": outcome["current"],
        "latest": outcome["latest"],
        "history": outcome["history"],
        "scoring": outcome["scoring"],
        "read_only": True,
        "projection_only": True,
    }


def build_outcome_replay(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    outcome = _build_outcome_context(
        organization_id=organization_id,
        source=source,
        outcome_type="measured_outcome",
        limit=limit,
    )
    return {
        "view": "novatech_outcome_replay",
        "organization_id": outcome["organization_id"],
        "source": outcome["source"],
        "current": outcome["current"],
        "latest": outcome["latest"],
        "history": outcome["history"],
        "replay": outcome["replay"],
        "read_only": True,
        "projection_only": True,
    }


def build_organization_onboarding(
    *,
    organization_id: str,
    legal_name: str,
    sector: str,
    trust_domain: str,
    actor_user_id: str = "system",
    actor_role: str = "system",
) -> dict[str, Any]:
    novascript = get_novascript_service()
    adoption = novascript.onboard_organization(
        organization_id=organization_id,
        legal_name=legal_name,
        sector=sector,
        trust_domain=trust_domain,
    )
    _STORE.upsert_organization_profile(
        organization_id=organization_id,
        organization_type="business",
        status="active",
        default_plan="free",
        owner_user_id=None,
        owner_role=None,
    )
    if _STORE.latest_subscription(organization_id=organization_id) is None:
        _STORE.store_subscription(
            organization_id=organization_id,
            plan="free",
            status="active",
            billing_cycle="monthly",
            seats=1,
            auto_renew=True,
        )
    _phase0_audit(
        organization_id=organization_id,
        event_type="phase0.organization_onboard",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=organization_id,
        status="recorded",
        payload={
            "legal_name": legal_name,
            "sector": sector,
            "trust_domain": trust_domain,
        },
    )
    return {
        "view": "novatech_organization_onboarding",
        "organization_id": organization_id,
        "status": "onboarded",
        "organization": adoption,
        "global_trust": novascript.global_trust_status(),
        "trust_graph": novascript.trust_graph(),
        "read_only": False,
        "projection_only": False,
        "governance_linked": True,
    }


def _normalize_controlled_execution_tier(value: str | None) -> str:
    tier = str(value or "controlled").strip().lower()
    if tier in {"advisory", "assisted", "controlled", "supervised"}:
        return tier
    return "controlled"


def build_controlled_execution_activation(
    *,
    organization_id: str | None = None,
    source: str | None = "novatech_controlled_execution_activation",
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    directory = build_organization_directory(organization_id=org_id, limit=limit)
    billing_preview = build_billing_preview(organization_id=org_id)
    billing_ready = bool(billing_preview.get("plan"))
    tenants = list(directory.get("organizations", []))
    current_tenant = next(
        (tenant for tenant in tenants if tenant.get("organization_id") == org_id),
        tenants[0] if tenants else None,
    )
    tenant_ready = bool(current_tenant and current_tenant.get("status") in {"active", "pilot_ready", "certified"})
    action_surface = build_dashboard_actions(
        organization_id=org_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )
    autonomy_surface = build_dashboard_autonomy(
        organization_id=org_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )
    execution = action_surface["current"]
    autonomy = autonomy_surface["autonomy"]
    driver_allocation = autonomy_surface.get("driver_allocation", {})
    city_automation = autonomy_surface.get("city_automation", {})
    multi_city_orchestration = autonomy_surface.get("multi_city_orchestration", {})
    activation_history = _STORE.list_ai_action_snapshots(
        organization_id=org_id,
        source=source,
        action_type="controlled_execution_activation",
        limit=limit,
    )
    history = list(reversed(activation_history))
    latest = history[-1] if history else None
    trigger_payload = {}
    if latest:
        payload = latest.get("payload", {})
        if isinstance(payload, dict):
            maybe_trigger_payload = payload.get("trigger_payload", {})
            if isinstance(maybe_trigger_payload, dict):
                trigger_payload = maybe_trigger_payload

    requested_tier = _normalize_controlled_execution_tier(trigger_payload.get("requested_tier"))
    acknowledged = bool(trigger_payload.get("acknowledged", False))
    operator_note = str(trigger_payload.get("operator_note") or "").strip()
    activation_ready = bool(
        tenant_ready
        and billing_ready
        and bool(execution.get("execution_tier_ready", False))
        and execution.get("safety_gate") == "pass"
        and bool(autonomy.get("safe_to_autorun", False))
    )
    activation_status = "enabled" if activation_ready and acknowledged and requested_tier == "controlled" else "held"
    activation_reason = _unique_items(
        [
            f"tenant ready: {tenant_ready}",
            f"billing ready: {billing_ready}",
            f"execution tier ready: {bool(execution.get('execution_tier_ready', False))}",
            f"safety gate: {execution.get('safety_gate', 'hold')}",
            f"autonomy safe: {bool(autonomy.get('safe_to_autorun', False))}",
            f"city zero-operator: {bool(city_automation.get('zero_operator_mode', False))}",
            f"multi-city zero-operator: {bool(multi_city_orchestration.get('mode') == 'global_zero_operator')}",
            f"requested tier: {requested_tier}",
            f"acknowledged: {acknowledged}",
        ],
        [
            f"tenant status: {(current_tenant or {}).get('status', 'discovered')}",
            f"billing plan: {billing_preview.get('plan', 'enterprise')}",
            f"execution tier: {execution.get('execution_tier', 'advisory')}",
            f"autonomy mode: {autonomy.get('mode', 'advisory')}",
            f"city mode: {city_automation.get('mode', 'city_held')}",
            f"multi-city mode: {multi_city_orchestration.get('mode', 'global_held')}",
        ],
    )
    activation_scope = [
        "operator-supervised review only",
        "bounded execution recommendations",
        "projection-only dashboard updates",
        "no execution authority",
    ]
    activation_guardrails = [
        "advisory_only remains true",
        "execution_authority remains false",
        "read_only remains true",
        "projection_only remains true",
        "safety gate must stay pass or guarded",
    ]
    return {
        "view": "novatech_controlled_execution_activation",
        "organization_id": org_id,
        "status": activation_status,
        "activation": {
            "activation_status": activation_status,
            "activation_ready": activation_ready,
            "requested_tier": requested_tier,
            "acknowledged": acknowledged,
            "operator_note": operator_note,
            "safe_execution_enabled": activation_ready,
            "execution_tier": execution.get("execution_tier", "advisory"),
            "execution_tier_ready": bool(execution.get("execution_tier_ready", False)),
            "execution_tier_summary": execution.get("execution_tier_summary", ""),
            "execution_tier_controls": list(execution.get("execution_tier_controls", [])),
            "control_signal": execution.get("control_signal", "maintain_monitoring"),
            "safety_gate": execution.get("safety_gate", "hold"),
            "decision_quality_score": int(execution.get("decision_quality_score", 0) or 0),
            "calibrated_confidence": float(execution.get("calibrated_confidence", 0) or 0),
            "autonomy": autonomy,
            "activation_scope": activation_scope,
            "activation_guardrails": activation_guardrails,
            "activation_reason": activation_reason,
            "city_automation": city_automation,
            "multi_city_orchestration": multi_city_orchestration,
            "advisory_only": True,
            "execution_authority": False,
            "read_only": True,
            "projection_only": True,
        },
        "safe_execution": execution,
        "autonomy": autonomy,
        "driver_allocation": driver_allocation,
        "city_automation": city_automation,
        "multi_city_orchestration": multi_city_orchestration,
        "directory": directory,
        "billing": billing_preview,
        "readiness": {
            "tenant_ready": tenant_ready,
            "billing_ready": billing_ready,
            "execution_tier_ready": bool(execution.get("execution_tier_ready", False)),
            "safety_gate": execution.get("safety_gate", "hold"),
        },
        "history": {
            "count": len(history),
            "items": history,
            "source_breakdown": {
                item["source"]: sum(1 for row in history if row["source"] == item["source"])
                for item in history
            },
        },
        "latest": latest,
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def build_federated_trust_network(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    novascript = get_novascript_service()
    global_trust = novascript.global_trust_status()
    trust_graph = novascript.trust_graph()
    distributed = build_distributed_trust_network(organization_id=org_id)
    members = list(global_trust.get("members", []))
    member_ids = [
        str(member.get("organization_id") or "").strip()
        for member in members
        if str(member.get("organization_id") or "").strip()
    ]
    tenant_pairs: list[dict[str, Any]] = []
    for issuer_org in member_ids:
        for subject_org in member_ids:
            if issuer_org == subject_org:
                continue
            tenant_pairs.append(
                {
                    "issuer_org": issuer_org,
                    "subject_org": subject_org,
                    "exchange_modes": ["trust_exchange", "proof_exchange", "certification_exchange"],
                    "routes": {
                        "trust_exchange": "/v1/novascript/federation/trust-exchange",
                        "proof_exchange": "/v1/novaprogramming/verify/replay/{execution_id}",
                        "certification_exchange": "/v1/novaprogramming/certification",
                    },
                    "status": "ready",
                }
            )
            if len(tenant_pairs) >= 12:
                break
        if len(tenant_pairs) >= 12:
            break
    exchange_catalog = [
        {
            "service_id": "trust-exchange",
            "service_type": "Trust Services",
            "name": "Trust Exchange",
            "description": "Cross-tenant trust exchange and federation verification.",
            "consumable_across_tenants": True,
            "status": "ready",
            "routes": [
                "/v1/novascript/federation/trust-exchange",
                "/v1/novaprogramming/trust/exchange/events",
                "/v1/novaprogramming/trust/exchange/verify",
            ],
        },
        {
            "service_id": "proof-exchange",
            "service_type": "Verification Services",
            "name": "Proof Exchange",
            "description": "Replay-backed receipts and verification packages consumable across tenants.",
            "consumable_across_tenants": True,
            "status": "ready",
            "routes": [
                "/v1/novaprogramming/verify/replay/{execution_id}",
                "/public/trust/{receipt_id}",
                "/public/trust/{receipt_id}/package",
                "/public/verify/portal",
            ],
        },
        {
            "service_id": "certification-exchange",
            "service_type": "Certification Services",
            "name": "Certification Exchange",
            "description": "Certification status, standards, and attestation exchanges across tenants.",
            "consumable_across_tenants": True,
            "status": "ready",
            "routes": [
                "/v1/novaprogramming/certification",
                "/v1/novaprogramming/certification/issue",
                "/v1/novaprogramming/certification/verify",
                "/v1/novaprogramming/certificate/transparency/log",
            ],
        },
        {
            "service_id": "replay-exchange",
            "service_type": "Replay Services",
            "name": "Replay Exchange",
            "description": "Outcome replay, proof reconstruction, and audit replay surfaces.",
            "consumable_across_tenants": True,
            "status": "ready",
            "routes": [
                "/v1/novatech/outcomes/replay",
                "/v1/novatech/outcomes/status",
                "/v1/novatech/intranet/actions",
            ],
        },
    ]
    return {
        "view": "novatech_federated_trust_network",
        "organization_id": org_id,
        "status": "ready" if global_trust.get("member_count", len(member_ids)) else "bootstrapping",
        "global_trust": global_trust,
        "trust_graph": trust_graph,
        "distributed_trust_network": distributed,
        "exchange_catalog": exchange_catalog,
        "tenant_pairs": tenant_pairs,
        "member_count": global_trust.get("member_count", len(member_ids)),
        "organization_count": global_trust.get("member_count", len(member_ids)),
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def build_trust_marketplace_services(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    novascript = get_novascript_service()
    global_trust = novascript.global_trust_status()
    trust_graph = novascript.trust_graph()
    adoption_status = novascript.field_adoption_status()
    services = [
        {
            "service_id": "trust-services",
            "service_type": "Trust Services",
            "name": "Trust Exchange",
            "summary": "Cross-tenant trust scoring, exchange, and federation routing.",
            "consumable_across_tenants": True,
            "status": "ready",
            "routes": [
                "/v1/novascript/federation/trust-exchange",
                "/v1/novaprogramming/trust/exchange/events",
            ],
        },
        {
            "service_id": "verification-services",
            "service_type": "Verification Services",
            "name": "Proof Verification",
            "summary": "Receipt verification, proof lookup, and replay-backed receipt packages.",
            "consumable_across_tenants": True,
            "status": "ready",
            "routes": [
                "/public/trust/{receipt_id}",
                "/public/trust/{receipt_id}/package",
                "/public/verify/portal",
            ],
        },
        {
            "service_id": "certification-services",
            "service_type": "Certification Services",
            "name": "Certification Exchange",
            "summary": "Certification issuance, transparency, and attestation exchange.",
            "consumable_across_tenants": True,
            "status": "ready",
            "routes": [
                "/v1/novaprogramming/certification",
                "/v1/novaprogramming/certification/issue",
                "/v1/novaprogramming/certification/verify",
                "/v1/novaprogramming/certificate/transparency/log",
            ],
        },
        {
            "service_id": "replay-services",
            "service_type": "Replay Services",
            "name": "Replay Exchange",
            "summary": "Outcome replay, proof replay, and governed audit reconstruction.",
            "consumable_across_tenants": True,
            "status": "ready",
            "routes": [
                "/v1/novatech/outcomes/replay",
                "/v1/novaprogramming/verify/replay/{execution_id}",
                "/v1/novatech/outcomes/status",
            ],
        },
    ]
    return {
        "view": "novatech_trust_marketplace_services",
        "organization_id": org_id,
        "status": "ready",
        "service_count": len(services),
        "tenant_count": adoption_status.get("organization_count", 0),
        "global_trust": global_trust,
        "trust_graph": trust_graph,
        "services": services,
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def build_trust_marketplace(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    services = build_trust_marketplace_services(organization_id=org_id)
    federation = build_federated_trust_network(organization_id=org_id)
    return {
        "view": "novatech_trust_marketplace",
        "organization_id": org_id,
        "status": "ready",
        "summary": {
            "service_count": services["service_count"],
            "tenant_count": services["tenant_count"],
            "trust_member_count": federation["member_count"],
            "exchange_modes": ["trust_exchange", "proof_exchange", "certification_exchange", "replay_exchange"],
        },
        "services": services["services"],
        "federated_trust_network": federation,
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def build_marketplace_onboarding_strategy(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    marketplace = build_trust_marketplace(organization_id=org_id)
    partner_cohort = [
        {
            "name": "City mobility operator",
            "role": "Pilot launch partner",
            "goal": "Use replay-backed dispute evidence and registry publication in a live city corridor sandbox.",
        },
        {
            "name": "Enterprise fleet platform",
            "role": "Compliance integration partner",
            "goal": "Adopt verification API and audit export bundles for fleet exception handling.",
        },
        {
            "name": "Insurance or claims workflow",
            "role": "Verification partner",
            "goal": "Validate receipt and trace evidence packets for post-ride disputes.",
        },
        {
            "name": "Government mobility observer",
            "role": "Public-interest pilot",
            "goal": "Review replay-linked audit packets without receiving runtime mutation authority.",
        },
        {
            "name": "Marketplace infrastructure partner",
            "role": "Trust network node",
            "goal": "Participate in quorum verification and registry-backed trust packet exchange.",
        },
    ]
    phases = [
        {
            "phase": "discover",
            "title": "Discover",
            "goal": "Identify a partner cohort and map the trust domain before any exchange begins.",
            "entry_criteria": [
                "organization onboarded",
                "public trust surfaces available",
            ],
        },
        {
            "phase": "verify",
            "title": "Verify",
            "goal": "Run proof exchange, verification sessions, and registry publication checks.",
            "entry_criteria": [
                "replay-backed receipt available",
                "verification package generated",
            ],
        },
        {
            "phase": "certify",
            "title": "Certify",
            "goal": "Issue certification and link the tenant into the federated trust graph.",
            "entry_criteria": [
                "verification quorum complete",
                "trust score threshold met",
            ],
        },
        {
            "phase": "publish",
            "title": "Publish",
            "goal": "Expose the partner in the marketplace catalog with bounded read-only surfaces.",
            "entry_criteria": [
                "certification issued",
                "partner registry entry published",
            ],
        },
        {
            "phase": "exchange",
            "title": "Exchange",
            "goal": "Allow cross-tenant trust, proof, certification, and replay services to be consumed.",
            "entry_criteria": [
                "federated trust edge established",
                "marketplace service published",
            ],
        },
    ]
    requirements = [
        "organization onboarding completed",
        "public verification packet available",
        "trust score and replay score meet minimum thresholds",
        "operator acknowledges read-only governance boundary",
    ]
    return {
        "view": "novatech_marketplace_onboarding",
        "organization_id": org_id,
        "status": "ready",
        "summary": {
            "service_count": marketplace["summary"]["service_count"],
            "tenant_count": marketplace["summary"]["tenant_count"],
            "trust_member_count": marketplace["summary"]["trust_member_count"],
            "exchange_modes": list(marketplace["summary"]["exchange_modes"]),
        },
        "partner_cohort": partner_cohort,
        "phases": phases,
        "requirements": requirements,
        "marketplace": marketplace,
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def build_dashboard_actions(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    return _build_dashboard_action_context(
        organization_id=organization_id,
        source=source,
        action_type="controlled_autonomous_action",
        limit=limit,
    )


def build_dashboard_actions_history(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    actions = _build_dashboard_action_context(
        organization_id=organization_id,
        source=source,
        action_type="controlled_autonomous_action",
        limit=limit,
    )
    return {
        "view": "novatech_operator_action_history",
        "organization_id": actions["organization_id"],
        "source": actions["source"],
        "current": actions["current"],
        "latest": actions["latest"],
        "history": actions["history"],
        "signals": actions["signals"],
        "read_only": True,
    }


def build_dashboard_autonomy(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    return _build_dashboard_autonomy_context(
        organization_id=organization_id,
        source=source,
        limit=limit,
    )


def build_dashboard_city_automation(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    autonomy_context = _build_dashboard_autonomy_context(
        organization_id=organization_id,
        source=source,
        limit=limit,
    )
    city_automation = dict(autonomy_context.get("city_automation", {}))
    return {
        "view": "novatech_city_automation",
        "organization_id": autonomy_context.get("organization_id"),
        "source": autonomy_context.get("source"),
        "autonomy": autonomy_context.get("autonomy", {}),
        "driver_allocation": autonomy_context.get("driver_allocation", {}),
        "city_automation": city_automation,
        "prediction": city_automation.get("prediction", {}),
        "read_only": True,
        "projection_only": True,
    }


def build_dashboard_multi_city_orchestration(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    autonomy_context = _build_dashboard_autonomy_context(
        organization_id=organization_id,
        source=source,
        limit=limit,
    )
    multi_city_orchestration = dict(autonomy_context.get("multi_city_orchestration", {}))
    return {
        "view": "novatech_multi_city_orchestration",
        "organization_id": autonomy_context.get("organization_id"),
        "source": autonomy_context.get("source"),
        "autonomy": autonomy_context.get("autonomy", {}),
        "city_automation": autonomy_context.get("city_automation", {}),
        "multi_city_orchestration": multi_city_orchestration,
        "global_learning": multi_city_orchestration.get("global_learning", {}),
        "prediction": multi_city_orchestration.get("prediction", {}),
        "read_only": True,
        "projection_only": True,
    }


def build_dashboard_digital_twin(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    autonomy_context = _build_dashboard_autonomy_context(
        organization_id=organization_id,
        source=source,
        limit=limit,
    )
    outcome_learning = build_outcome_learning(
        organization_id=organization_id,
        source=source,
        limit=limit,
    )

    org_id = autonomy_context.get("organization_id") or organization_id or DEFAULT_ORGANIZATION_ID
    autonomy = dict(autonomy_context.get("autonomy", {}))
    current_action = dict(autonomy_context.get("action", {}))
    driver_allocation = dict(autonomy_context.get("driver_allocation", {}))
    city_automation = dict(autonomy_context.get("city_automation", {}))
    multi_city_orchestration = dict(autonomy_context.get("multi_city_orchestration", {}))
    current_learning = dict(outcome_learning.get("current", {}))
    learning = dict(outcome_learning.get("learning", {}))
    prediction = dict(autonomy_context.get("prediction", {}))

    observed = dict(autonomy.get("observed", {}))
    trust_health = int(observed.get("trust_health", current_action.get("trust_health", 0)) or 0)
    replay_health_score = int(observed.get("replay_health_score", current_action.get("replay_health_score", 0)) or 0)
    evidence_coverage = int(observed.get("evidence_coverage", current_action.get("evidence_coverage", 0)) or 0)
    confidence_score = int(round(float(current_action.get("calibrated_confidence", 0.0) or 0.0) * 100))
    city_coverage = int(city_automation.get("coverage_score", 0) or 0)
    global_coverage = int(multi_city_orchestration.get("global_coverage_score", 0) or 0)
    live_sync_score = min(
        100,
        max(
            0,
            (trust_health + replay_health_score + evidence_coverage + confidence_score + city_coverage + global_coverage) // 6,
        ),
    )
    twin_mode = (
        "global_closed_loop"
        if multi_city_orchestration.get("mode") == "global_zero_operator"
        else "city_closed_loop"
        if city_automation.get("mode") == "zero_operator"
        else "predictive_closed_loop"
        if bool(autonomy.get("safe_to_autorun", False))
        else "shadow_sync"
    )
    learning_mode = (
        "learning"
        if str(learning.get("band", "hold")) in {"excellent", "strong"}
        else "recalibrating"
        if str(learning.get("band", "hold")) in {"guarded", "weak"}
        else "watching"
    )
    twin_health_score = min(
        100,
        max(
            0,
            (live_sync_score + int(prediction.get("predicted_trust_score", 0) or 0) + int(prediction.get("predicted_evidence_coverage", 0) or 0)) // 3,
        ),
    )
    next_state = (
        "global_zero_operator"
        if multi_city_orchestration.get("mode") == "global_zero_operator"
        else "city_zero_operator"
        if city_automation.get("mode") == "zero_operator"
        else "predictive_autonomous"
        if bool(autonomy.get("safe_to_autorun", False))
        else "supervised_shadow"
    )
    recommendation = (
        multi_city_orchestration.get("instruction")
        or city_automation.get("instruction")
        or driver_allocation.get("predictive_positioning", {}).get("instruction")
        or current_action.get("recommended_next_step")
        or "Keep the digital twin in projection-only mode."
    )
    reason = (
        multi_city_orchestration.get("reason")
        or city_automation.get("reason")
        or driver_allocation.get("reason")
        or current_action.get("decision_summary")
        or "The twin is mirroring live signals and learning from the latest outcomes."
    )
    self_improving_loop = {
        "mode": learning_mode,
        "cycle": list(learning.get("cycle", [])),
        "band": learning.get("band", "hold"),
        "trend": dict(learning.get("trend", {})),
        "recommendations": list(learning.get("recommendations", [])),
        "recalibration_notes": list(learning.get("recalibration_notes", [])),
        "watch_items": list(learning.get("watch_items", [])),
        "outcome_score": int(current_learning.get("outcome_score", 0) or 0),
        "measurement_summary": current_learning.get("measurement_summary", ""),
        "projection_only": True,
        "read_only": True,
    }
    digital_twin = {
        "mode": twin_mode,
        "live_sync_score": live_sync_score,
        "twin_health_score": twin_health_score,
        "live_state": {
            "active_drivers": int(city_automation.get("active_drivers", driver_allocation.get("available_drivers", 0)) or 0),
            "active_rides": int(city_automation.get("active_rides", multi_city_orchestration.get("active_rides", 0)) or 0),
            "zone": str(city_automation.get("recommended_zone") or driver_allocation.get("predictive_positioning", {}).get("target_zone") or "CBD"),
            "demand_level": str(prediction.get("demand_level", "low")),
            "trust_score": int(prediction.get("trust_score", multi_city_orchestration.get("global_trust_score", 0)) or 0),
            "city_coverage_score": city_coverage,
            "global_coverage_score": global_coverage,
        },
        "prediction": {
            "next_state": next_state,
            "confidence": round(twin_health_score / 100, 2),
            "trust_score": int(prediction.get("predicted_trust_score", current_learning.get("trust_score", 0)) or 0),
            "evidence_coverage": int(prediction.get("predicted_evidence_coverage", current_learning.get("evidence_coverage", 0)) or 0),
            "exception_pressure": int(prediction.get("predicted_exception_pressure", 0) or 0),
        },
        "autonomy": autonomy,
        "driver_allocation": driver_allocation,
        "city_automation": city_automation,
        "multi_city_orchestration": multi_city_orchestration,
        "self_improving_loop": self_improving_loop,
        "recommendation": recommendation,
        "reason": reason,
        "bounded_actions": [
            "mirror live ride, driver, and trust signals",
            "learn from the latest outcome band",
            "keep execution read-only until thresholds clear",
        ],
        "projection_only": True,
        "read_only": True,
    }
    return {
        "view": "novatech_digital_twin",
        "organization_id": org_id,
        "source": autonomy_context.get("source", source or "all"),
        "digital_twin": digital_twin,
        "self_improving_loop": self_improving_loop,
        "mode": twin_mode,
        "live_sync_score": live_sync_score,
        "twin_health_score": twin_health_score,
        "live_state": digital_twin["live_state"],
        "prediction": digital_twin["prediction"],
        "autonomy": autonomy,
        "driver_allocation": driver_allocation,
        "city_automation": city_automation,
        "multi_city_orchestration": multi_city_orchestration,
        "recommendation": recommendation,
        "reason": reason,
        "bounded_actions": digital_twin["bounded_actions"],
        "projection_only": True,
        "read_only": True,
    }


def build_dashboard_meta_learning_redesign(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    digital_twin = build_dashboard_digital_twin(
        organization_id=org_id,
        source=source,
        limit=limit,
    )
    outcome_learning = build_outcome_learning(
        organization_id=org_id,
        source=source,
        limit=limit,
    )
    learning = dict(outcome_learning.get("learning", {}))
    current_outcome = dict(outcome_learning.get("current", {}))
    twin = dict(digital_twin.get("digital_twin", {}))
    twin_state = dict(twin.get("live_state", {}))
    prediction = dict(twin.get("prediction", {}))
    design_intent = (
        "Redesign the NovaRide architecture as a governed meta-learning system with "
        "a real-time digital twin, self-improving control loop, bounded autonomous "
        "execution, and proposal-only architecture evolution."
    )
    design_output = DesignGenerator().generate(design_intent).canonical_dict()
    architecture = dict(design_output.get("architecture", {}))
    review = dict(design_output.get("review", {}))
    implementation_plan = dict(design_output.get("implementation_plan", {}))
    meta_learning_mode = (
        "adaptive_redesign"
        if review.get("admitted") and current_outcome.get("outcome_band") in {"excellent", "strong"}
        else "proposal_watch"
        if current_outcome.get("outcome_band") == "guarded"
        else "design_hold"
    )
    redesign_triggers = [
        f"Outcome band: {current_outcome.get('outcome_band', 'unknown')}",
        f"Learning band: {learning.get('band', 'hold')}",
        f"Twin mode: {twin.get('mode', 'shadow_sync')}",
        f"Trust score: {twin_state.get('trust_score', 0)}",
        f"Prediction confidence: {prediction.get('confidence', 0)}",
    ]
    self_redesign_rules = [
        "proposal_only",
        "read_only",
        "no_runtime_mutation",
        "no_auto_deploy",
        "human_review_required",
        "guardrails_preserve_authority_boundaries",
    ]
    candidate_redesign = {
        "intent": design_output.get("intent", design_intent),
        "domain": design_output.get("domain", {}),
        "requirements": design_output.get("requirements", {}),
        "architecture": architecture,
        "contracts": design_output.get("contracts", {}),
        "implementation_plan": implementation_plan,
        "evidence": design_output.get("evidence", {}),
        "review": review,
        "authority_boundary": "proposal_only",
        "write_enabled": False,
    }
    architecture_change_summary = [
        "Keep the governed control plane as the execution authority.",
        "Add a meta-learning proposal surface that studies outcomes and twin drift.",
        "Use the digital twin to rank redesign candidates before human review.",
        "Preserve tenant isolation, auditability, and replay safety.",
    ]
    return {
        "view": "novatech_meta_learning_redesign",
        "organization_id": org_id,
        "source": source or "afriride_operator_dashboard",
        "mode": meta_learning_mode,
        "trigger_window": {
            "outcome_band": current_outcome.get("outcome_band", "unknown"),
            "learning_band": learning.get("band", "hold"),
            "twin_mode": twin.get("mode", "shadow_sync"),
            "twin_health_score": twin.get("twin_health_score", 0),
            "live_sync_score": twin.get("live_sync_score", 0),
        },
        "digital_twin": twin,
        "outcome_learning": outcome_learning,
        "self_redesign_rules": self_redesign_rules,
        "redesign_triggers": redesign_triggers,
        "candidate_redesign": candidate_redesign,
        "architecture_change_summary": architecture_change_summary,
        "bounded_actions": [
            "observe architecture drift",
            "generate a proposal-only redesign",
            "require human approval before any implementation",
        ],
        "projection_only": True,
        "read_only": True,
    }


def build_dashboard_business_pricing(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    from afritech.afriprogramming.phase3 import build_business_pricing_projection

    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    projection = build_business_pricing_projection(
        organization_id=org_id,
        limit=limit,
        source=source,
    )
    return {
        "view": "novatech_business_pricing",
        "organization_id": org_id,
        "source": source or "afriride_operator_dashboard",
        "pricing": projection.get("pricing", {}),
        "incentives": projection.get("incentives", {}),
        "market_signals": projection.get("market_signals", {}),
        "market": projection.get("market", {}),
        "decision": projection.get("decision", {}),
        "invariant_report": projection.get("invariant_report", {}),
        "validation_report": projection.get("validation_report", {}),
        "readiness": projection.get("readiness", {}),
        "ready": bool(projection.get("ready", False)),
        "controls": projection.get("controls", {}),
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_dashboard_city_profit_optimization(
    organization_id: str | None = None,
    source: str | None = "afriride_operator_dashboard",
    limit: int = 24,
) -> dict[str, Any]:
    from afritech.afriprogramming.phase4 import build_business_budget_allocation_projection

    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    projection = build_business_budget_allocation_projection(
        organization_id=org_id,
        limit=limit,
        source=source,
    )
    return {
        "view": "novatech_city_profit_optimization",
        "organization_id": org_id,
        "source": source or "afriride_operator_dashboard",
        "phase3": projection.get("phase3", {}),
        "budget_allocation": projection.get("budget_allocation", {}),
        "profit_optimization": projection.get("profit_optimization", {}),
        "city_signals": projection.get("city_signals", {}),
        "readiness": projection.get("readiness", {}),
        "ready": bool(projection.get("ready", False)),
        "controls": projection.get("controls", {}),
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_workflow_instances(
    organization_id: str | None = None,
    limit: int = 24,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    workflows = _workflow_service().instances(organization_id=org_id, limit=limit)
    templates = [
        {
            "workflow_name": "deployment",
            "steps": list(("requested", "approved", "deployed", "verified", "certified")),
            "purpose": "Controlled delivery lifecycle",
        },
        {
            "workflow_name": "assurance",
            "steps": list(("collected", "recomputed", "checked", "alerted", "closed")),
            "purpose": "Continuous evidence and trust checking",
        },
        {
            "workflow_name": "federation",
            "steps": list(("registered", "validated", "published", "verified")),
            "purpose": "Partner and trust network publication",
        },
    ]
    return {
        "view": "novaprogramming_workflows",
        "organization_id": org_id,
        "workflow_count": len(workflows),
        "workflows": workflows,
        "templates": templates,
        "read_only": True,
    }


def record_dashboard_outcome_snapshot(
    *,
    payload: dict[str, Any],
    source: str,
    outcome_type: str = "measured_outcome",
    action_snapshot_id: str | None = None,
    decision_snapshot_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    context = _build_outcome_context(
        organization_id=org_id,
        source=source,
        outcome_type=outcome_type,
        limit=24,
    )
    current = context["current"]
    action_id = action_snapshot_id or current["action_id"] or "action-unbound"
    decision_id = decision_snapshot_id or current["decision_id"] or "decision-unbound"
    record_payload = {
        "trigger_payload": payload,
        "outcome": current,
        "signals": context["signals"],
        "history_depth": context["history"]["count"],
    }
    return _STORE.store_outcome_snapshot(
        organization_id=org_id,
        source=source,
        outcome_type=outcome_type,
        decision_id=decision_id,
        action_id=action_id,
        outcome_status=current["outcome_status"],
        outcome_band=current["outcome_band"],
        learning_band=current["learning_band"],
        outcome_score=current["outcome_score"],
        trust_score=current["trust_score"],
        trust_health=current["trust_health"],
        replay_health_score=current["replay_health_score"],
        evidence_coverage=current["evidence_coverage"],
        exception_pressure=current["exception_pressure"],
        decision_quality_score=current["decision_quality_score"],
        evidence_alignment_score=current["evidence_alignment_score"],
        calibrated_confidence=current["calibrated_confidence"],
        history_alignment_score=current["history_alignment_score"],
        execution_tier=current["execution_tier"],
        execution_tier_ready=current["execution_tier_ready"],
        measurement_summary=current["measurement_summary"],
        learning_actions=current["learning_actions"],
        recalibration_notes=current["recalibration_notes"],
        watch_items=current["watch_items"],
        payload=record_payload,
    )


def record_dashboard_action_snapshot(
    *,
    payload: dict[str, Any],
    source: str,
    action_type: str = "controlled_autonomous_action",
    decision_snapshot_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    context = _build_dashboard_action_context(
        organization_id=org_id,
        source=source,
        action_type=action_type,
        limit=24,
    )
    current = context["current"]
    record_payload = {
        "trigger_payload": payload,
        "decision": current["decision"],
        "action": current,
        "signals": context["signals"],
        "history_depth": context["history"]["count"],
    }
    decision_id = decision_snapshot_id or current["decision_id"] or "decision-unbound"
    action_record = _STORE.store_ai_action_snapshot(
        organization_id=org_id,
        source=source,
        action_type=action_type,
        decision_id=decision_id,
        decision_lane=current["decision_lane"],
        action_lane=current["action_lane"],
        action_mode=current["action_mode"],
        action_priority=current["action_priority"],
        action_summary=current["action_summary"],
        control_signal=current["control_signal"],
        safety_gate=current["safety_gate"],
        automation_tier=current["automation_tier"],
        decision_quality_score=current["decision_quality_score"],
        evidence_alignment_score=current["evidence_alignment_score"],
        calibrated_confidence=current["calibrated_confidence"],
        history_alignment_score=current["history_alignment_score"],
        quality_band=current["quality_band"],
        trust_score=current["signals"]["trust_score"],
        trust_health=current["signals"]["trust_health"],
        replay_health_score=current["signals"]["replay_health_score"],
        evidence_coverage=current["signals"]["evidence_coverage"],
        exception_pressure=current["signals"]["exception_pressure"],
        alert_count=current["signals"]["alert_count"],
        guard_count=current["signals"]["guard_count"],
        replay_failures=current["signals"]["replay_failures"],
        hash_chain_failures=current["signals"]["hash_chain_failures"],
        missing_traces=current["signals"]["missing_traces"],
        stability_index=current["signals"]["stability_index"],
        recommended_actions=current["recommended_actions"],
        watch_items=current["watch_items"],
        payload=record_payload,
    )
    record_dashboard_outcome_snapshot(
        payload=payload,
        source=source,
        outcome_type="measured_outcome",
        action_snapshot_id=action_record["action_id"],
        decision_snapshot_id=decision_id,
        organization_id=org_id,
    )
    return action_record


def build_retention(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _retention_service()
    service.ensure_defaults(org_id)
    policies = service.list_policies(org_id)
    return {
        "view": "novaprogramming_retention",
        "organization_id": org_id,
        "policies": policies,
        "count": len(policies),
        "read_only": True,
    }


def build_retention_set(
    *,
    record_type: str,
    retention_days: int,
    legal_hold: bool,
    deletion_allowed: bool,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    policy = _retention_service().set_policy(
        organization_id=org_id,
        record_type=record_type,
        retention_days=retention_days,
        legal_hold=legal_hold,
        deletion_allowed=deletion_allowed,
    )
    return {
        "view": "novaprogramming_retention_set",
        "organization_id": org_id,
        "policy": policy,
        "read_only": False,
    }


def build_retention_check(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    check = _retention_service().check(org_id)
    return {
        "view": "novaprogramming_retention_check",
        **check,
        "read_only": True,
    }


def build_assurance_report(
    organization_id: str | None = None,
    report_classification: str = "INTERNAL_ASSURANCE_REPORT",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    latest = _report_service().latest(org_id)
    if latest is None:
        latest = _report_service().build(organization_id=org_id, report_classification=report_classification)
    return {
        "view": "novaprogramming_assurance_report",
        "organization_id": org_id,
        "report": latest,
        "read_only": True,
    }


def build_assurance_report_generate(
    *,
    report_classification: str = "INTERNAL_ASSURANCE_REPORT",
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    report = _report_service().build(organization_id=org_id, report_classification=report_classification)
    return {
        "view": "novaprogramming_assurance_report_generate",
        "organization_id": org_id,
        "report": report,
        "read_only": False,
    }


def build_trust_exchange_verify(
    *,
    receipt: dict[str, Any],
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _trust_exchange_service().verify_public_receipt(organization_id=org_id, receipt=receipt)
    return {
        "view": "novaprogramming_trust_exchange_verify",
        "organization_id": org_id,
        "result": result,
        "read_only": True,
    }


def build_trust_exchange_events(organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    events = _trust_exchange_service().events(organization_id=org_id, limit=limit)
    return {
        "view": "novaprogramming_trust_exchange_events",
        "organization_id": org_id,
        "events": events,
        "count": len(events),
        "read_only": True,
    }


def build_certification(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _certification_service().summary(org_id)
    return {
        "view": "novaprogramming_certification",
        **result,
        "read_only": True,
    }


def build_certification_issue(
    *,
    organization_id: str | None = None,
    certification_type: str = "CONTROLLED_OPERATIONAL_STATE",
    actor_user_id: str = "system",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    certification = _certification_service().issue(
        organization_id=org_id,
        certification_type=certification_type,
    )
    _record_event(
        organization_id=org_id,
        action="certification.issue",
        actor_user_id=actor_user_id,
        actor_role="verifier",
        target=certification_type,
        status="recorded",
        details=certification,
    )
    return {
        "view": "novaprogramming_certification_issue",
        "organization_id": org_id,
        "certification": certification,
        "read_only": False,
    }


def build_certification_verify(certification: dict[str, Any]) -> dict[str, Any]:
    return {
        "view": "novaprogramming_certification_verify",
        "result": _certification_service().verify(certification),
        "read_only": True,
    }


def build_key_registry(
    organization_id: str | None = None,
    key_family: str = "audit",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _pki_service()
    service.current_key(organization_id=org_id, key_family=key_family)
    return {
        "view": "novaprogramming_key_registry",
        "organization_id": org_id,
        "key_family": key_family,
        "keys": service.list_keys(organization_id=org_id, key_family=key_family),
        "rotations": service.list_rotations(organization_id=org_id),
        "read_only": True,
    }


def build_key_rotation(
    *,
    organization_id: str | None = None,
    key_family: str = "audit",
    rotated_by: str = "system",
    reason: str = "rotation",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    rotation = _pki_service().rotate(
        organization_id=org_id,
        key_family=key_family,
        rotated_by=rotated_by,
        reason=reason,
    )
    _record_event(
        organization_id=org_id,
        action="keys.rotate",
        actor_user_id=rotated_by,
        actor_role="security",
        target=key_family,
        status="recorded",
        details=rotation,
    )
    return {
        "view": "novaprogramming_key_rotation",
        "organization_id": org_id,
        "rotation": rotation,
        "read_only": False,
    }


def build_signed_audit_chain(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _signed_audit_service()
    return {
        "view": "novaprogramming_signed_audit_chain",
        "organization_id": org_id,
        "valid": _STORE.verify_signed_audit_chain(organization_id=org_id),
        "events": service.history(org_id, limit=500),
        "count": len(service.history(org_id, limit=500)),
        "current_key": _pki_service().current_key(organization_id=org_id, key_family="audit"),
        "read_only": True,
    }


def build_signed_audit_verify(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    return {
        "view": "novaprogramming_signed_audit_verify",
        "organization_id": org_id,
        "valid": _STORE.verify_signed_audit_chain(organization_id=org_id),
        "read_only": True,
    }


def build_distributed_trust_network(organization_id: str | None = None, quorum: int = 2) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _distributed_trust_service()
    certificate_bundle = service.federation_certificate(quorum=quorum)
    return {
        "view": "novaprogramming_distributed_trust_network",
        "organization_id": org_id,
        "peers": service.peers(org_id),
        "certificate": certificate_bundle["certificate"],
        "verification": certificate_bundle["verification"],
        "read_only": True,
    }


def build_federation_register(
    *,
    peer_organization_id: str,
    jurisdiction: str,
    role: str,
    endpoint: str,
    public_key_id: str,
    trust_level: str = "TRUSTED",
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    node = _distributed_trust_service().register_peer(
        organization_id=org_id,
        peer_organization_id=peer_organization_id,
        jurisdiction=jurisdiction,
        role=role,
        public_key_id=public_key_id,
        endpoint=endpoint,
        trust_level=trust_level,
    )
    return {
        "view": "novaprogramming_federation_register",
        "organization_id": org_id,
        "node": node,
        "read_only": False,
    }


def build_federation_claim(
    *,
    peer_organization_id: str,
    claim_type: str,
    payload: dict[str, Any],
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    claim = _distributed_trust_service().issue_claim(
        organization_id=org_id,
        peer_organization_id=peer_organization_id,
        claim_type=claim_type,
        payload=payload,
    )
    return {
        "view": "novaprogramming_federation_claim",
        "organization_id": org_id,
        "claim": claim,
        "read_only": False,
    }


def build_federation_verify(
    *,
    claim: dict[str, Any],
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _distributed_trust_service().verify_claim(claim)
    _distributed_trust_service().repository.store_federation_event(
        organization_id=org_id,
        peer_organization_id=str(claim.get("peer_organization_id", claim.get("organization_id", org_id))),
        event_type="federation.claim.verified",
        details={"claim": claim, "result": result},
    )
    return {
        "view": "novaprogramming_federation_verify",
        "organization_id": org_id,
        "result": result,
        "read_only": True,
    }


def build_event_topics(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    return {
        "view": "novaprogramming_event_topics",
        "organization_id": org_id,
        "topics": _event_stream_service().topics(org_id),
        "read_only": True,
    }


def build_event_topic_create(
    *,
    topic_name: str,
    description: str = "",
    retention_days: int = 0,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    topic = _event_stream_service().create_topic(
        organization_id=org_id,
        topic_name=topic_name,
        description=description,
        retention_days=retention_days,
    )
    return {
        "view": "novaprogramming_event_topic_create",
        "organization_id": org_id,
        "topic": topic,
        "read_only": False,
    }


def build_event_publish(
    *,
    topic_name: str,
    event_type: str,
    payload: dict[str, Any],
    partition_key: str = "",
    headers: dict[str, Any] | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    event = _event_stream_service().publish(
        organization_id=org_id,
        topic_name=topic_name,
        event_type=event_type,
        payload=payload,
        partition_key=partition_key,
        headers=headers,
    )
    return {
        "view": "novaprogramming_event_publish",
        "organization_id": org_id,
        "event": event,
        "read_only": False,
    }


def build_event_consume(
    *,
    topic_name: str | None = None,
    after_offset: int = 0,
    limit: int = 100,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    events = _event_stream_service().consume(
        organization_id=org_id,
        topic_name=topic_name,
        after_offset=after_offset,
        limit=limit,
    )
    return {
        "view": "novaprogramming_event_consume",
        "organization_id": org_id,
        "events": events,
        "count": len(events),
        "read_only": True,
    }


def build_workflow_start(
    *,
    workflow_name: str,
    input_payload: dict[str, Any],
    organization_id: str | None = None,
    steps: list[str] | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    workflow = _workflow_service().start(
        organization_id=org_id,
        workflow_name=workflow_name,
        input_payload=input_payload,
        steps=steps,
    )
    return {
        "view": "novaprogramming_workflow_start",
        "organization_id": org_id,
        "workflow": workflow,
        "read_only": False,
    }


def build_workflow_signal(
    *,
    workflow_id: str,
    signal_name: str,
    payload: dict[str, Any],
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    workflow = _workflow_service().signal(
        organization_id=org_id,
        workflow_id=workflow_id,
        signal_name=signal_name,
        payload=payload,
    )
    return {
        "view": "novaprogramming_workflow_signal",
        "organization_id": org_id,
        "workflow": workflow,
        "read_only": False,
    }


def build_workflow_status(
    *,
    workflow_id: str,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    workflow = _workflow_service().status(organization_id=org_id, workflow_id=workflow_id)
    return {
        "view": "novaprogramming_workflow_status",
        "organization_id": org_id,
        "workflow_id": workflow_id,
        "state": workflow["state"],
        "current_step": workflow["current_step"],
        "workflow": workflow,
        "step_count": len(workflow.get("steps", [])),
        "read_only": True,
    }


def build_workflow_history(
    *,
    workflow_id: str,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    events = _workflow_service().history(organization_id=org_id, workflow_id=workflow_id)
    return {
        "view": "novaprogramming_workflow_history",
        "organization_id": org_id,
        "workflow_id": workflow_id,
        "events": events,
        "count": len(events),
        "read_only": True,
    }


def build_zero_trust_policies(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _zero_trust_service()
    service.seed_defaults(org_id)
    return {
        "view": "novaprogramming_zero_trust_policies",
        "organization_id": org_id,
        "policies": service.list_policies(org_id),
        "read_only": True,
    }


def build_zero_trust_create(
    *,
    policy_name: str,
    version: str,
    rule_type: str,
    rule_payload: dict[str, Any],
    active: bool = True,
    organization_id: str | None = None,
    created_by: str = "system",
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    policy = _zero_trust_service().create_policy(
        organization_id=org_id,
        policy_name=policy_name,
        version=version,
        rule_type=rule_type,
        rule_payload=rule_payload,
        active=active,
        created_by=created_by,
    )
    return {
        "view": "novaprogramming_zero_trust_create",
        "organization_id": org_id,
        "policy": policy,
        "read_only": False,
    }


def build_zero_trust_evaluate(
    *,
    subject: str,
    action: str,
    resource: str,
    context: dict[str, Any],
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    decision = _zero_trust_service().evaluate(
        organization_id=org_id,
        subject=subject,
        action=action,
        resource=resource,
        context=context,
    )
    return {
        "view": "novaprogramming_zero_trust_evaluate",
        "organization_id": org_id,
        "allowed": decision["allowed"],
        "reason": decision["reason"],
        "decision_id": decision["decision_id"],
        "decision": decision,
        "read_only": True,
    }


def build_zero_trust_decisions(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    return {
        "view": "novaprogramming_zero_trust_decisions",
        "organization_id": org_id,
        "decisions": _zero_trust_service().decisions(org_id),
        "read_only": True,
    }


def build_crypto_backends(
    organization_id: str | None = None,
    key_family: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _crypto_hardening_service()
    return {
        "view": "novaprogramming_crypto_backends",
        "organization_id": org_id,
        "key_family": key_family,
        "status": service.status(org_id, key_family),
        "read_only": True,
    }


def build_crypto_backend_register(
    *,
    backend_name: str,
    provider_ref: str,
    key_family: str = "audit",
    key_arn: str | None = None,
    hardware_bound: bool = False,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    backend = _crypto_hardening_service().register_backend(
        organization_id=org_id,
        key_family=key_family,
        backend_name=backend_name,
        provider_ref=provider_ref,
        key_arn=key_arn,
        hardware_bound=hardware_bound,
    )
    return {
        "view": "novaprogramming_crypto_backend_register",
        "organization_id": org_id,
        "backend": backend,
        "read_only": False,
    }


def build_certificate_chains(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _crypto_hardening_service()
    return {
        "view": "novaprogramming_certificate_chains",
        "organization_id": org_id,
        "chains": service.certificate_chains(org_id),
        "certificate_valid": service.verify_certificate_chain(org_id)["valid"],
        "read_only": True,
    }


def build_certificate_issue(
    *,
    subject: str,
    issuer: str = "NovaProgramming PKI",
    key_family: str = "audit",
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    chain = _crypto_hardening_service().issue_certificate_chain(
        organization_id=org_id,
        key_family=key_family,
        subject=subject,
        issuer=issuer,
    )
    return {
        "view": "novaprogramming_certificate_issue",
        "organization_id": org_id,
        "chain": chain,
        "read_only": False,
    }


def build_certificate_verify(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _crypto_hardening_service().verify_certificate_chain(org_id)
    return {
        "view": "novaprogramming_certificate_verify",
        "organization_id": org_id,
        **result,
        "read_only": True,
    }


def build_stream_backends(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _event_stream_service()
    return {
        "view": "novaprogramming_stream_backends",
        "organization_id": org_id,
        "backends": service.backends(org_id),
        "topics": service.topics(org_id),
        "read_only": True,
    }


def build_stream_backend_register(
    *,
    backend_name: str,
    provider: str,
    region: str,
    partitions: int,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    backend = _event_stream_service().register_backend(
        organization_id=org_id,
        backend_name=backend_name,
        provider=provider,
        region=region,
        partitions=partitions,
    )
    return {
        "view": "novaprogramming_stream_backend_register",
        "organization_id": org_id,
        "backend": backend,
        "read_only": False,
    }


def build_trust_fabric_regions(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _trust_fabric_service()
    return {
        "view": "novaprogramming_trust_fabric_regions",
        "organization_id": org_id,
        "regions": service.regions(org_id),
        "links": service.links(org_id),
        "read_only": True,
    }


def build_trust_fabric_region_register(
    *,
    region_name: str,
    country_code: str,
    provider: str,
    status: str = "active",
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    region = _trust_fabric_service().register_region(
        organization_id=org_id,
        region_name=region_name,
        country_code=country_code,
        provider=provider,
        status=status,
    )
    return {
        "view": "novaprogramming_trust_fabric_region_register",
        "organization_id": org_id,
        "region": region,
        "read_only": False,
    }


def build_trust_fabric_link(
    *,
    source_region_id: str,
    target_region_id: str,
    latency_ms: int,
    trust_score: int,
    status: str = "active",
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    link = _trust_fabric_service().link_regions(
        organization_id=org_id,
        source_region_id=source_region_id,
        target_region_id=target_region_id,
        latency_ms=latency_ms,
        trust_score=trust_score,
        status=status,
    )
    return {
        "view": "novaprogramming_trust_fabric_link",
        "organization_id": org_id,
        "link": link,
        "read_only": False,
    }


def build_trust_fabric_signed_request(
    *,
    peer_organization_id: str,
    method: str,
    url: str,
    headers: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    request = _trust_fabric_service().sign_request(
        organization_id=org_id,
        peer_organization_id=peer_organization_id,
        method=method,
        url=url,
        headers=headers,
        body=body,
    )
    return {
        "view": "novaprogramming_trust_fabric_signed_request",
        "organization_id": org_id,
        "request": request,
        "read_only": False,
    }


def build_trust_fabric_signed_request_verify(
    *,
    envelope: dict[str, Any],
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _trust_fabric_service().verify_request(envelope)
    return {
        "view": "novaprogramming_trust_fabric_signed_request_verify",
        "organization_id": org_id,
        **result,
        "read_only": True,
    }


def build_decentralized_trust_graph(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    graph = _trust_fabric_service().decentralized_trust_graph(org_id)
    return {
        "view": "novaprogramming_decentralized_trust_graph",
        "organization_id": org_id,
        **graph,
        "read_only": True,
    }


def build_identity_bind(
    *,
    user_id: str,
    device_id: str,
    human_trust_score: int,
    device_trust_score: int,
    attestation: dict[str, Any],
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    binding = _trust_fabric_service().identity_bind(
        organization_id=org_id,
        user_id=user_id,
        device_id=device_id,
        human_trust_score=human_trust_score,
        device_trust_score=device_trust_score,
        attestation=attestation,
    )
    return {
        "view": "novaprogramming_identity_bind",
        "organization_id": org_id,
        "binding": binding,
        "read_only": False,
    }


def build_identity_bindings(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _trust_fabric_service()
    return {
        "view": "novaprogramming_identity_bindings",
        "organization_id": org_id,
        "bindings": service.identity_bindings(org_id),
        "identity_bound_score": service.identity_score(org_id),
        "read_only": True,
    }


def build_risk_prediction(
    *,
    entity_type: str = "organization",
    entity_id: str | None = None,
    horizon_days: int = 30,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    prediction = _risk_prediction_service().predict(
        organization_id=org_id,
        entity_type=entity_type,
        entity_id=entity_id,
        horizon_days=horizon_days,
    )
    return {
        "view": "novaprogramming_risk_prediction",
        "organization_id": org_id,
        **prediction,
        "read_only": True,
    }


def build_risk_predictions(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _risk_prediction_service()
    return {
        "view": "novaprogramming_risk_predictions",
        "organization_id": org_id,
        "predictions": service.history(org_id),
        "read_only": True,
    }


def build_trust_negotiation(
    *,
    peer_organization_id: str,
    proposed_terms: dict[str, Any],
    trust_offer: int,
    trust_floor: int,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    result = _trust_fabric_service().negotiate(
        organization_id=org_id,
        peer_organization_id=peer_organization_id,
        proposed_terms=proposed_terms,
        trust_offer=trust_offer,
        trust_floor=trust_floor,
    )
    return {
        "view": "novaprogramming_trust_negotiation",
        "organization_id": org_id,
        **result,
        "read_only": False,
    }


def build_trust_negotiations(organization_id: str | None = None) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    service = _trust_fabric_service()
    return {
        "view": "novaprogramming_trust_negotiations",
        "organization_id": org_id,
        "sessions": service.negotiation_sessions(org_id),
        "events": service.negotiation_events(org_id),
        "read_only": True,
    }


def build_insights(organization_id: str | None = None) -> dict[str, Any]:
    snapshot = _STORE.insights(organization_id=organization_id)
    return {
        "view": "novaprogramming_insights",
        "platform": "NovaProgramming",
        "platform_version": "V3",
        "read_only": True,
        **snapshot,
    }


def build_v9_schema(partition_count: int = 4) -> dict[str, Any]:
    schema_sql = build_v9_postgres_schema_sql(partition_count=partition_count)
    rls_sql = build_v9_rls_sql()
    return {
        "view": "novaprogramming_v9_schema",
        "platform": "NovaProgramming",
        "platform_version": "V9",
        "partition_count": partition_count,
        "tables": [
            "trust_consensus_rounds",
            "trust_consensus_votes",
            "certificate_transparency_log",
            "key_revocation_events",
            "trace_spans",
            "assurance_scheduler_runs",
        ],
        "schema_sql": schema_sql,
        "sqlite_schema_sql": build_v9_sqlite_schema_sql(),
        "rls_sql": rls_sql,
        "read_only": True,
    }


def build_trust_consensus(
    *,
    organization_id: str,
    proposal: dict[str, Any],
    peer_votes: list[dict[str, Any]] | None = None,
    quorum: int | None = None,
) -> dict[str, Any]:
    return _trust_consensus_service().evaluate(
        organization_id=organization_id,
        proposal=proposal,
        peer_votes=peer_votes,
        quorum=quorum,
    )


def build_certificate_transparency_append(
    *,
    organization_id: str,
    subject: str,
    issuer: str,
    key_family: str = "audit",
    status: str = "active",
    certificate_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _ct_log_service().append(
        organization_id=organization_id,
        subject=subject,
        issuer=issuer,
        key_family=key_family,
        status=status,
        certificate_payload=certificate_payload,
    )


def build_certificate_transparency_log(organization_id: str | None = None) -> dict[str, Any]:
    service = _ct_log_service()
    entries = service.list(organization_id=organization_id)
    return {
        "view": "novaprogramming_certificate_transparency_log",
        "platform": "NovaProgramming",
        "platform_version": "V9",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "entries": entries,
        "verification": service.verify(organization_id=organization_id),
    }


def build_key_revocation(
    *,
    organization_id: str,
    key_id: str,
    reason: str,
    revoked_by: str = "system",
) -> dict[str, Any]:
    return _key_revocation_service().revoke(
        organization_id=organization_id,
        key_id=key_id,
        reason=reason,
        revoked_by=revoked_by,
    )


def build_key_revocations(organization_id: str | None = None) -> dict[str, Any]:
    service = _key_revocation_service()
    return {
        "view": "novaprogramming_key_revocations",
        "platform": "NovaProgramming",
        "platform_version": "V9",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "revocations": service.revocations(organization_id=organization_id),
    }


def build_trace_span(
    *,
    organization_id: str,
    actor_user_id: str,
    operation_name: str,
    endpoint: str,
    latency_ms: int,
    status_code: int,
    policy_decision_id: str | None = None,
    proof_hash: str | None = None,
    deployment_id: str | None = None,
    parent_span_id: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _tracing_service().trace_http_request(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        operation_name=operation_name,
        endpoint=endpoint,
        latency_ms=latency_ms,
        status_code=status_code,
        policy_decision_id=policy_decision_id,
        proof_hash=proof_hash,
        deployment_id=deployment_id,
        parent_span_id=parent_span_id,
        attributes=attributes,
        method=operation_name.split(" ", 1)[0] if " " in operation_name else "TRACE",
    )


def build_trace_spans(organization_id: str | None = None) -> dict[str, Any]:
    service = _tracing_service()
    return {
        "view": "novaprogramming_trace_spans",
        "platform": "NovaProgramming",
        "platform_version": "V9",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "spans": service.spans(organization_id=organization_id),
    }


def build_assurance_scheduler_run(organization_ids: list[str] | None = None) -> dict[str, Any]:
    service = _scheduler_service()
    runs = service.run_once(organization_ids=organization_ids)
    return {
        "view": "novaprogramming_assurance_scheduler_run",
        "platform": "NovaProgramming",
        "platform_version": "V9",
        "runs": runs,
        "scheduler_status": service.status(organization_ids[0] if organization_ids else None),
    }


def build_assurance_scheduler_history(organization_id: str | None = None) -> dict[str, Any]:
    service = _scheduler_service()
    return {
        "view": "novaprogramming_assurance_scheduler_history",
        "platform": "NovaProgramming",
        "platform_version": "V9",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "history": service.history(organization_id=organization_id),
    }


default_control_plane = None


def get_control_plane():
    global default_control_plane
    if default_control_plane is None:
        default_control_plane = NovaProgrammingControlPlane()
    return default_control_plane


@dataclass
class NovaProgrammingControlPlane:
    """Stateful helper used by API adapters."""

    project_id: str = "project-employee-rbac"
    extra_metadata: dict[str, Any] = field(default_factory=dict)

    def status(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_status(organization_id=organization_id)

    def catalog(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_catalog(organization_id=organization_id)

    def staff_dashboard(
        self,
        role: str,
        project_id: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_staff_dashboard(role, project_id or self.project_id, organization_id=organization_id)

    def studio_context(
        self,
        project_id: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_studio_context(project_id or self.project_id, organization_id=organization_id)

    def studio_generate(
        self,
        *,
        prompt: str,
        mode: str,
        project_id: str | None = None,
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "developer",
    ) -> dict[str, Any]:
        return build_studio_generation(
            prompt=prompt,
            mode=mode,
            project_id=project_id or self.project_id,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def studio_explain(
        self,
        *,
        code: str,
        context: str = "",
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "developer",
    ) -> dict[str, Any]:
        return build_code_explanation(
            code=code,
            context=context,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def studio_analyze(
        self,
        *,
        project_id: str | None = None,
        focus: str = "",
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "architect",
    ) -> dict[str, Any]:
        return build_repo_intelligence(
            project_id=project_id or self.project_id,
            focus=focus,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def cloud_services(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_cloud_services(organization_id=organization_id)

    def cloud_health(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_cloud_health(organization_id=organization_id)

    def cloud_request_deploy(
        self,
        *,
        service: str,
        environment: str = "staging",
        image: str = "nova-programming:latest",
        rationale: str = "",
        organization_id: str | None = None,
        requested_by: str = "system",
        requested_role: str = "operator",
    ) -> dict[str, Any]:
        return build_cloud_request_deployment(
            service=service,
            environment=environment,
            image=image,
            rationale=rationale,
            organization_id=organization_id,
            requested_by=requested_by,
            requested_role=requested_role,
        )

    def cloud_deploy(
        self,
        *,
        request_id: str,
        service: str,
        environment: str = "staging",
        image: str = "nova-programming:latest",
        organization_id: str | None = None,
        deployed_by: str = "system",
        actor_role: str = "devops",
    ) -> dict[str, Any]:
        return build_cloud_deployment(
            request_id=request_id,
            service=service,
            environment=environment,
            image=image,
            organization_id=organization_id,
            deployed_by=deployed_by,
            actor_role=actor_role,
        )

    def cloud_scale(
        self,
        *,
        service: str,
        replicas: int,
        organization_id: str | None = None,
        deployed_by: str = "system",
        actor_role: str = "devops",
    ) -> dict[str, Any]:
        return build_cloud_scale(
            service=service,
            replicas=replicas,
            organization_id=organization_id,
            deployed_by=deployed_by,
            actor_role=actor_role,
        )

    def governance_policy(
        self,
        *,
        policy_name: str,
        target: str,
        description: str,
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "manager",
    ) -> dict[str, Any]:
        return build_governance_policy(
            policy_name=policy_name,
            target=target,
            description=description,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def governance_check(
        self,
        *,
        policy_name: str,
        target: str,
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "verifier",
    ) -> dict[str, Any]:
        return build_governance_check(
            policy_name=policy_name,
            target=target,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def governance_approve(
        self,
        *,
        request_id: str,
        decision: str = "approved",
        notes: str = "",
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "verifier",
    ) -> dict[str, Any]:
        return build_governance_approve(
            request_id=request_id,
            decision=decision,
            notes=notes,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def audit_log(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_audit_log(organization_id=organization_id)

    def verify_generate(
        self,
        *,
        execution_id: str,
        project_id: str | None = None,
        payload: dict[str, Any] | None = None,
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "verifier",
    ) -> dict[str, Any]:
        return build_proof(
            execution_id=execution_id,
            project_id=project_id or self.project_id,
            payload=payload or {},
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def verify_lookup(self, execution_id: str, *, organization_id: str | None = None) -> dict[str, Any]:
        return lookup_proof(execution_id, organization_id=organization_id)

    def verify_replay(
        self,
        execution_id: str,
        *,
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "verifier",
    ) -> dict[str, Any]:
        return build_replay(
            execution_id,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def metrics(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_metrics(organization_id=organization_id)

    def trust(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_trust(organization_id=organization_id)

    def trust_stream(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return build_trust_stream(organization_id=organization_id, limit=limit)

    def trust_anomalies(self, organization_id: str | None = None, limit: int = 25) -> dict[str, Any]:
        return build_trust_anomalies(organization_id=organization_id, limit=limit)

    def trust_verify_external(self, receipt: dict[str, Any]) -> dict[str, Any]:
        return build_trust_verify_external(receipt)

    def trust_risk(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_trust_risk(organization_id=organization_id)

    def assurance(self, deployment_id: str, organization_id: str | None = None) -> dict[str, Any]:
        return build_assurance(deployment_id=deployment_id, organization_id=organization_id)

    def certification(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_certification(organization_id=organization_id)

    def policy_registry(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_policy_registry(organization_id=organization_id)

    def policy_create(
        self,
        *,
        policy_name: str,
        version: str,
        rule_type: str,
        rule_payload: dict[str, Any],
        active: bool = True,
        organization_id: str | None = None,
        created_by: str = "system",
    ) -> dict[str, Any]:
        return build_policy_create(
            policy_name=policy_name,
            version=version,
            rule_type=rule_type,
            rule_payload=rule_payload,
            active=active,
            organization_id=organization_id,
            created_by=created_by,
        )

    def policy_evaluate(
        self,
        *,
        action: str,
        target: str,
        payload: dict[str, Any],
        organization_id: str | None = None,
        actor_user_id: str = "system",
    ) -> dict[str, Any]:
        return build_policy_evaluate(
            action=action,
            target=target,
            payload=payload,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
        )

    def policy_decisions(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_policy_decisions(organization_id=organization_id)

    def assurance_status(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_assurance_status(organization_id=organization_id)

    def assurance_run(
        self,
        *,
        organization_id: str | None = None,
        actor_user_id: str = "system",
    ) -> dict[str, Any]:
        return build_assurance_run(organization_id=organization_id, actor_user_id=actor_user_id)

    def assurance_history(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return build_assurance_history(organization_id=organization_id, limit=limit)

    def assurance_alerts(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return build_assurance_alerts(organization_id=organization_id, limit=limit)

    def trust_trends(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_trust_trends(organization_id=organization_id)

    def dashboard_analytics(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_analytics(organization_id=organization_id, source=source, limit=limit)

    def dashboard_analytics_history(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_analytics_history(organization_id=organization_id, source=source, limit=limit)

    def dashboard_analytics_insights(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_analytics_insights(organization_id=organization_id, source=source, limit=limit)

    def dashboard_analytics_prediction(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_analytics_prediction(organization_id=organization_id, source=source, limit=limit)

    def dashboard_demand_forecast(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_demand_forecast(organization_id=organization_id, source=source, limit=limit)

    def dashboard_decisions(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_decisions(organization_id=organization_id, source=source, limit=limit)

    def dashboard_decisions_history(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_decisions_history(organization_id=organization_id, source=source, limit=limit)

    def dashboard_actions(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_actions(organization_id=organization_id, source=source, limit=limit)

    def dashboard_autonomy(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_autonomy(organization_id=organization_id, source=source, limit=limit)

    def dashboard_city_automation(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_city_automation(organization_id=organization_id, source=source, limit=limit)

    def dashboard_multi_city_orchestration(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_multi_city_orchestration(organization_id=organization_id, source=source, limit=limit)

    def dashboard_digital_twin(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_digital_twin(organization_id=organization_id, source=source, limit=limit)

    def dashboard_meta_learning_redesign(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_meta_learning_redesign(organization_id=organization_id, source=source, limit=limit)

    def dashboard_business_pricing(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_business_pricing(organization_id=organization_id, source=source, limit=limit)

    def dashboard_city_profit_optimization(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_city_profit_optimization(organization_id=organization_id, source=source, limit=limit)

    def dashboard_actions_history(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_dashboard_actions_history(organization_id=organization_id, source=source, limit=limit)

    def outcome_status(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_outcome_status(organization_id=organization_id, source=source, limit=limit)

    def outcome_registry(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_outcome_registry(organization_id=organization_id, source=source, limit=limit)

    def outcome_learning(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_outcome_learning(organization_id=organization_id, source=source, limit=limit)

    def outcome_scoring(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_outcome_scoring(organization_id=organization_id, source=source, limit=limit)

    def outcome_replay(
        self,
        *,
        organization_id: str | None = None,
        source: str | None = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_outcome_replay(organization_id=organization_id, source=source, limit=limit)

    def workflow_instances(
        self,
        *,
        organization_id: str | None = None,
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_workflow_instances(organization_id=organization_id, limit=limit)

    def record_dashboard_analytics_snapshot(
        self,
        *,
        payload: dict[str, Any],
        source: str,
        snapshot_type: str = "operator_dashboard",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return record_dashboard_analytics_snapshot(
            payload=payload,
            source=source,
            snapshot_type=snapshot_type,
            organization_id=organization_id,
        )

    def record_dashboard_decision_snapshot(
        self,
        *,
        payload: dict[str, Any],
        source: str,
        decision_type: str = "operator_decision",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return record_dashboard_decision_snapshot(
            payload=payload,
            source=source,
            decision_type=decision_type,
            organization_id=organization_id,
        )

    def record_dashboard_action_snapshot(
        self,
        *,
        payload: dict[str, Any],
        source: str,
        action_type: str = "controlled_autonomous_action",
        decision_snapshot_id: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return record_dashboard_action_snapshot(
            payload=payload,
            source=source,
            action_type=action_type,
            decision_snapshot_id=decision_snapshot_id,
            organization_id=organization_id,
        )

    def retention(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_retention(organization_id=organization_id)

    def retention_set(
        self,
        *,
        record_type: str,
        retention_days: int,
        legal_hold: bool,
        deletion_allowed: bool,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_retention_set(
            record_type=record_type,
            retention_days=retention_days,
            legal_hold=legal_hold,
            deletion_allowed=deletion_allowed,
            organization_id=organization_id,
        )

    def retention_check(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_retention_check(organization_id=organization_id)

    def assurance_report(
        self,
        organization_id: str | None = None,
        report_classification: str = "INTERNAL_ASSURANCE_REPORT",
    ) -> dict[str, Any]:
        return build_assurance_report(
            organization_id=organization_id,
            report_classification=report_classification,
        )

    def assurance_report_generate(
        self,
        *,
        report_classification: str = "INTERNAL_ASSURANCE_REPORT",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_assurance_report_generate(
            report_classification=report_classification,
            organization_id=organization_id,
        )

    def trust_exchange_verify(
        self,
        *,
        receipt: dict[str, Any],
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_trust_exchange_verify(receipt=receipt, organization_id=organization_id)

    def trust_exchange_events(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return build_trust_exchange_events(organization_id=organization_id, limit=limit)

    def certification_issue(
        self,
        *,
        organization_id: str | None = None,
        certification_type: str = "CONTROLLED_OPERATIONAL_STATE",
        actor_user_id: str = "system",
    ) -> dict[str, Any]:
        return build_certification_issue(
            organization_id=organization_id,
            certification_type=certification_type,
            actor_user_id=actor_user_id,
        )

    def certification_verify(self, certification: dict[str, Any]) -> dict[str, Any]:
        return build_certification_verify(certification)

    def key_registry(self, organization_id: str | None = None, key_family: str = "audit") -> dict[str, Any]:
        return build_key_registry(organization_id=organization_id, key_family=key_family)

    def key_rotate(
        self,
        *,
        organization_id: str | None = None,
        key_family: str = "audit",
        rotated_by: str = "system",
        reason: str = "rotation",
    ) -> dict[str, Any]:
        return build_key_rotation(
            organization_id=organization_id,
            key_family=key_family,
            rotated_by=rotated_by,
            reason=reason,
        )

    def signed_audit_chain(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_signed_audit_chain(organization_id=organization_id)

    def signed_audit_verify(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_signed_audit_verify(organization_id=organization_id)

    def distributed_trust_network(self, organization_id: str | None = None, quorum: int = 2) -> dict[str, Any]:
        return build_distributed_trust_network(organization_id=organization_id, quorum=quorum)

    def federation_register(
        self,
        *,
        peer_organization_id: str,
        jurisdiction: str,
        role: str,
        endpoint: str,
        public_key_id: str,
        trust_level: str = "TRUSTED",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_federation_register(
            peer_organization_id=peer_organization_id,
            jurisdiction=jurisdiction,
            role=role,
            endpoint=endpoint,
            public_key_id=public_key_id,
            trust_level=trust_level,
            organization_id=organization_id,
        )

    def federation_claim(
        self,
        *,
        peer_organization_id: str,
        claim_type: str,
        payload: dict[str, Any],
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_federation_claim(
            peer_organization_id=peer_organization_id,
            claim_type=claim_type,
            payload=payload,
            organization_id=organization_id,
        )

    def federation_verify(
        self,
        *,
        claim: dict[str, Any],
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_federation_verify(claim=claim, organization_id=organization_id)

    def event_topics(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_event_topics(organization_id=organization_id)

    def event_topic_create(
        self,
        *,
        topic_name: str,
        description: str = "",
        retention_days: int = 0,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_event_topic_create(
            topic_name=topic_name,
            description=description,
            retention_days=retention_days,
            organization_id=organization_id,
        )

    def event_publish(
        self,
        *,
        topic_name: str,
        event_type: str,
        payload: dict[str, Any],
        partition_key: str = "",
        headers: dict[str, Any] | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_event_publish(
            topic_name=topic_name,
            event_type=event_type,
            payload=payload,
            partition_key=partition_key,
            headers=headers,
            organization_id=organization_id,
        )

    def event_consume(
        self,
        *,
        topic_name: str | None = None,
        after_offset: int = 0,
        limit: int = 100,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_event_consume(
            topic_name=topic_name,
            after_offset=after_offset,
            limit=limit,
            organization_id=organization_id,
        )

    def workflow_start(
        self,
        *,
        workflow_name: str,
        input_payload: dict[str, Any],
        organization_id: str | None = None,
        steps: list[str] | None = None,
    ) -> dict[str, Any]:
        return build_workflow_start(
            workflow_name=workflow_name,
            input_payload=input_payload,
            organization_id=organization_id,
            steps=steps,
        )

    def workflow_signal(
        self,
        *,
        workflow_id: str,
        signal_name: str,
        payload: dict[str, Any],
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_workflow_signal(
            workflow_id=workflow_id,
            signal_name=signal_name,
            payload=payload,
            organization_id=organization_id,
        )

    def workflow_status(
        self,
        *,
        workflow_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_workflow_status(workflow_id=workflow_id, organization_id=organization_id)

    def workflow_history(
        self,
        *,
        workflow_id: str,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_workflow_history(workflow_id=workflow_id, organization_id=organization_id)

    def zero_trust_policies(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_zero_trust_policies(organization_id=organization_id)

    def zero_trust_create(
        self,
        *,
        policy_name: str,
        version: str,
        rule_type: str,
        rule_payload: dict[str, Any],
        active: bool = True,
        organization_id: str | None = None,
        created_by: str = "system",
    ) -> dict[str, Any]:
        return build_zero_trust_create(
            policy_name=policy_name,
            version=version,
            rule_type=rule_type,
            rule_payload=rule_payload,
            active=active,
            organization_id=organization_id,
            created_by=created_by,
        )

    def zero_trust_evaluate(
        self,
        *,
        subject: str,
        action: str,
        resource: str,
        context: dict[str, Any],
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_zero_trust_evaluate(
            subject=subject,
            action=action,
            resource=resource,
            context=context,
            organization_id=organization_id,
        )

    def zero_trust_decisions(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_zero_trust_decisions(organization_id=organization_id)

    def crypto_backends(self, organization_id: str | None = None, key_family: str | None = None) -> dict[str, Any]:
        return build_crypto_backends(organization_id=organization_id, key_family=key_family)

    def crypto_backend_register(
        self,
        *,
        backend_name: str,
        provider_ref: str,
        key_family: str = "audit",
        key_arn: str | None = None,
        hardware_bound: bool = False,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_crypto_backend_register(
            backend_name=backend_name,
            provider_ref=provider_ref,
            key_family=key_family,
            key_arn=key_arn,
            hardware_bound=hardware_bound,
            organization_id=organization_id,
        )

    def certificate_chains(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_certificate_chains(organization_id=organization_id)

    def certificate_issue(
        self,
        *,
        subject: str,
        issuer: str = "NovaProgramming PKI",
        key_family: str = "audit",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_certificate_issue(
            subject=subject,
            issuer=issuer,
            key_family=key_family,
            organization_id=organization_id,
        )

    def certificate_verify(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_certificate_verify(organization_id=organization_id)

    def stream_backends(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_stream_backends(organization_id=organization_id)

    def stream_backend_register(
        self,
        *,
        backend_name: str,
        provider: str,
        region: str,
        partitions: int,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_stream_backend_register(
            backend_name=backend_name,
            provider=provider,
            region=region,
            partitions=partitions,
            organization_id=organization_id,
        )

    def trust_fabric_regions(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_trust_fabric_regions(organization_id=organization_id)

    def trust_fabric_region_register(
        self,
        *,
        region_name: str,
        country_code: str,
        provider: str,
        status: str = "active",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_trust_fabric_region_register(
            region_name=region_name,
            country_code=country_code,
            provider=provider,
            status=status,
            organization_id=organization_id,
        )

    def trust_fabric_link(
        self,
        *,
        source_region_id: str,
        target_region_id: str,
        latency_ms: int,
        trust_score: int,
        status: str = "active",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_trust_fabric_link(
            source_region_id=source_region_id,
            target_region_id=target_region_id,
            latency_ms=latency_ms,
            trust_score=trust_score,
            status=status,
            organization_id=organization_id,
        )

    def trust_fabric_signed_request(
        self,
        *,
        peer_organization_id: str,
        method: str,
        url: str,
        headers: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_trust_fabric_signed_request(
            peer_organization_id=peer_organization_id,
            method=method,
            url=url,
            headers=headers,
            body=body,
            organization_id=organization_id,
        )

    def trust_fabric_signed_request_verify(
        self,
        *,
        envelope: dict[str, Any],
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_trust_fabric_signed_request_verify(envelope=envelope, organization_id=organization_id)

    def decentralized_trust_graph(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_decentralized_trust_graph(organization_id=organization_id)

    def identity_bind(
        self,
        *,
        user_id: str,
        device_id: str,
        human_trust_score: int,
        device_trust_score: int,
        attestation: dict[str, Any],
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_identity_bind(
            user_id=user_id,
            device_id=device_id,
            human_trust_score=human_trust_score,
            device_trust_score=device_trust_score,
            attestation=attestation,
            organization_id=organization_id,
        )

    def identity_bindings(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_identity_bindings(organization_id=organization_id)

    def risk_prediction(
        self,
        *,
        entity_type: str = "organization",
        entity_id: str | None = None,
        horizon_days: int = 30,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_risk_prediction(
            entity_type=entity_type,
            entity_id=entity_id,
            horizon_days=horizon_days,
            organization_id=organization_id,
        )

    def risk_predictions(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_risk_predictions(organization_id=organization_id)

    def trust_negotiation(
        self,
        *,
        peer_organization_id: str,
        proposed_terms: dict[str, Any],
        trust_offer: int,
        trust_floor: int,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        return build_trust_negotiation(
            peer_organization_id=peer_organization_id,
            proposed_terms=proposed_terms,
            trust_offer=trust_offer,
            trust_floor=trust_floor,
            organization_id=organization_id,
        )

    def trust_negotiations(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_trust_negotiations(organization_id=organization_id)

    def trust_replay(self, deployment_id: str, organization_id: str | None = None) -> dict[str, Any]:
        return build_trust_replay(deployment_id=deployment_id, organization_id=organization_id)

    def billing_summary(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_billing_summary(organization_id=organization_id)

    def billing_preview(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_billing_preview(organization_id=organization_id)

    def billing_records(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return build_billing_records(organization_id=organization_id, limit=limit)

    def organizations(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return build_organization_directory(organization_id=organization_id, limit=limit)

    def rbac_catalog(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        assignments = _STORE.list_rbac_role_assignments(organization_id=organization_id, limit=limit)
        return build_rbac_catalog(organization_id=organization_id, assignments=assignments)

    def rbac_role(
        self,
        role: str,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        assignments = _STORE.list_rbac_role_assignments(organization_id=organization_id, limit=limit)
        return build_rbac_role_dashboard(
            role=role,
            assignments=assignments,
            organization_id=organization_id or DEFAULT_ORGANIZATION_ID,
        )

    def rbac_assign_role(
        self,
        *,
        organization_id: str | None = None,
        subject_type: str,
        subject_id: str,
        role: str,
        granted_by: str,
        granted_role: str = "ADMIN",
        status: str = "active",
        notes: list[str] | None = None,
    ) -> dict[str, Any]:
        return _STORE.store_rbac_role_assignment(
            organization_id=organization_id,
            subject_type=subject_type,
            subject_id=subject_id,
            role=role,
            granted_by=granted_by,
            granted_role=granted_role,
            status=status,
            notes=notes,
        )

    def rbac_assignments(
        self,
        *,
        organization_id: str | None = None,
        subject_type: str | None = None,
        subject_id: str | None = None,
        role: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        assignments = _STORE.list_rbac_role_assignments(
            organization_id=organization_id,
            subject_type=subject_type,
            subject_id=subject_id,
            role=role,
            status=status,
            limit=limit,
        )
        return build_rbac_assignments(organization_id=organization_id, assignments=assignments)

    def rbac_check_access(
        self,
        *,
        role: str,
        permission: str,
        actor_id: str | None = None,
        owner_id: str | None = None,
        assigned_driver_id: str | None = None,
        privileged_roles: tuple[str, ...] = ("ADMIN",),
    ) -> dict[str, Any]:
        if actor_id is None and owner_id is None and assigned_driver_id is None:
            return build_rbac_access_check(role=role, permission=permission)
        return evaluate_rbac_access(
            role=role,
            permission=permission,
            actor_id=actor_id,
            owner_id=owner_id,
            assigned_driver_id=assigned_driver_id,
            privileged_roles=privileged_roles,
        )

    def rbac_role_dashboard(
        self,
        *,
        role: str,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        assignments = _STORE.list_rbac_role_assignments(organization_id=organization_id, limit=limit)
        return build_rbac_role_dashboard(
            role=role,
            organization_id=organization_id,
            assignments=assignments,
        )

    def onboard_organization(
        self,
        *,
        organization_id: str,
        legal_name: str,
        sector: str,
        trust_domain: str,
    ) -> dict[str, Any]:
        return build_organization_onboarding(
            organization_id=organization_id,
            legal_name=legal_name,
            sector=sector,
            trust_domain=trust_domain,
        )

    def federated_trust_network(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_federated_trust_network(organization_id=organization_id)

    def trust_marketplace_services(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_trust_marketplace_services(organization_id=organization_id)

    def trust_marketplace(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_trust_marketplace(organization_id=organization_id)

    def marketplace_onboarding_strategy(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_marketplace_onboarding_strategy(organization_id=organization_id)

    def activate_controlled_execution(
        self,
        *,
        organization_id: str | None = None,
        acknowledged: bool = True,
        requested_tier: str = "controlled",
        operator_note: str = "Operator acknowledged controlled execution readiness.",
        source: str = "novatech_controlled_execution_activation",
        limit: int = 24,
    ) -> dict[str, Any]:
        org_id = organization_id or DEFAULT_ORGANIZATION_ID
        record_dashboard_action_snapshot(
            organization_id=org_id,
            payload={
                "acknowledged": bool(acknowledged),
                "requested_tier": requested_tier,
                "operator_note": operator_note,
            },
            source=source,
            action_type="controlled_execution_activation",
        )
        return build_controlled_execution_activation(
            organization_id=org_id,
            source=source,
            limit=limit,
        )

    def controlled_execution_activation(
        self,
        *,
        organization_id: str | None = None,
        source: str = "novatech_controlled_execution_activation",
        limit: int = 24,
    ) -> dict[str, Any]:
        return build_controlled_execution_activation(
            organization_id=organization_id,
            source=source,
            limit=limit,
        )

    def insights(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_insights(organization_id=organization_id)

    def v9_schema(self, partition_count: int = 4) -> dict[str, Any]:
        return build_v9_schema(partition_count=partition_count)

    def trust_consensus(
        self,
        *,
        organization_id: str,
        proposal: dict[str, Any],
        peer_votes: list[dict[str, Any]] | None = None,
        quorum: int | None = None,
    ) -> dict[str, Any]:
        return build_trust_consensus(
            organization_id=organization_id,
            proposal=proposal,
            peer_votes=peer_votes,
            quorum=quorum,
        )

    def certificate_transparency_append(
        self,
        *,
        organization_id: str,
        subject: str,
        issuer: str = "NovaProgramming PKI",
        key_family: str = "audit",
        status: str = "active",
        certificate_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return build_certificate_transparency_append(
            organization_id=organization_id,
            subject=subject,
            issuer=issuer,
            key_family=key_family,
            status=status,
            certificate_payload=certificate_payload,
        )

    def certificate_transparency_log(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_certificate_transparency_log(organization_id=organization_id)

    def key_revocation(
        self,
        *,
        organization_id: str,
        key_id: str,
        reason: str,
        revoked_by: str = "system",
    ) -> dict[str, Any]:
        return build_key_revocation(
            organization_id=organization_id,
            key_id=key_id,
            reason=reason,
            revoked_by=revoked_by,
        )

    def key_revocations(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_key_revocations(organization_id=organization_id)

    def trace_span(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        operation_name: str,
        endpoint: str,
        latency_ms: int,
        status_code: int,
        policy_decision_id: str | None = None,
        proof_hash: str | None = None,
        deployment_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return build_trace_span(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            operation_name=operation_name,
            endpoint=endpoint,
            latency_ms=latency_ms,
            status_code=status_code,
            policy_decision_id=policy_decision_id,
            proof_hash=proof_hash,
            deployment_id=deployment_id,
            parent_span_id=parent_span_id,
            attributes=attributes,
        )

    def trace_spans(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_trace_spans(organization_id=organization_id)

    def assurance_scheduler_run(self, organization_ids: list[str] | None = None) -> dict[str, Any]:
        return build_assurance_scheduler_run(organization_ids=organization_ids)

    def assurance_scheduler_history(self, organization_id: str | None = None) -> dict[str, Any]:
        return build_assurance_scheduler_history(organization_id=organization_id)

    def phase0_status(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return build_phase0_status(organization_id=organization_id, limit=limit)

    def phase0_organization_onboard(
        self,
        *,
        organization_id: str,
        legal_name: str,
        sector: str,
        trust_domain: str,
        actor_user_id: str = "system",
        actor_role: str = "system",
    ) -> dict[str, Any]:
        return build_organization_onboarding(
            organization_id=organization_id,
            legal_name=legal_name,
            sector=sector,
            trust_domain=trust_domain,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def phase0_accounts(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        accounts = _STORE.list_accounts(organization_id=organization_id, limit=limit)
        return {
            "view": "novaprogramming_phase0_accounts",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "count": len(accounts),
            "accounts": accounts,
            "read_only": True,
        }

    def phase0_account_create(
        self,
        *,
        organization_id: str,
        user_id: str,
        role: str,
        status: str = "active",
        is_primary: bool = False,
        actor_user_id: str = "system",
        actor_role: str = "system",
    ) -> dict[str, Any]:
        account = _STORE.store_account(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            status=status,
            is_primary=is_primary,
        )
        _phase0_audit(
            organization_id=organization_id,
            event_type="phase0.account_create",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=user_id,
            status="recorded",
            payload={
                "organization_id": organization_id,
                "user_id": user_id,
                "role": role,
                "is_primary": is_primary,
            },
        )
        return {
            "view": "novaprogramming_phase0_account",
            "organization_id": organization_id,
            "account": account,
            "read_only": False,
        }

    def phase0_subscriptions(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        subscriptions = _STORE.list_subscriptions(organization_id=organization_id, limit=limit)
        return {
            "view": "novaprogramming_phase0_subscriptions",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "count": len(subscriptions),
            "subscriptions": subscriptions,
            "read_only": True,
        }

    def phase0_subscription_create(
        self,
        *,
        organization_id: str,
        plan: str,
        status: str = "active",
        billing_cycle: str = "monthly",
        seats: int = 1,
        start_date: str | None = None,
        end_date: str | None = None,
        auto_renew: bool = True,
        actor_user_id: str = "system",
        actor_role: str = "system",
    ) -> dict[str, Any]:
        subscription = _STORE.store_subscription(
            organization_id=organization_id,
            plan=plan,
            status=status,
            billing_cycle=billing_cycle,
            seats=seats,
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew,
        )
        _phase0_audit(
            organization_id=organization_id,
            event_type="phase0.subscription_create",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=subscription["subscription_id"],
            status="recorded",
            payload=subscription,
        )
        return {
            "view": "novaprogramming_phase0_subscription",
            "organization_id": organization_id,
            "subscription": subscription,
            "read_only": False,
        }

    def phase0_catalog(self, organization_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        seed_phase0_catalog(organization_id)
        features = _STORE.list_features(limit=limit)
        return {
            "view": "novaprogramming_phase0_catalog",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "count": len(features),
            "features": features,
            "read_only": True,
        }

    def phase0_feature_flag_set(
        self,
        *,
        organization_id: str,
        feature_key: str,
        enabled: bool,
        reason: str = "platform_control",
        updated_by: str = "system",
        actor_user_id: str = "system",
        actor_role: str = "system",
    ) -> dict[str, Any]:
        flag = _STORE.set_feature_flag(
            organization_id=organization_id,
            feature_key=feature_key,
            enabled=enabled,
            reason=reason,
            updated_by=updated_by,
        )
        _phase0_audit(
            organization_id=organization_id,
            event_type="phase0.feature_flag_set",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=feature_key,
            status="recorded",
            payload=flag,
        )
        return {
            "view": "novaprogramming_phase0_feature_flag",
            "organization_id": organization_id,
            "flag": flag,
            "read_only": False,
        }

    def phase0_feature_flags(
        self,
        *,
        organization_id: str | None = None,
        feature_key: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        flags = _STORE.list_feature_flags(
            organization_id=organization_id,
            feature_key=feature_key,
            limit=limit,
        )
        return {
            "view": "novaprogramming_phase0_feature_flags",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "count": len(flags),
            "feature_flags": flags,
            "read_only": True,
        }

    def phase0_notification_queue(
        self,
        *,
        organization_id: str,
        recipient_id: str,
        channel: str,
        message: str,
        status: str = "queued",
        actor_user_id: str = "system",
        actor_role: str = "system",
    ) -> dict[str, Any]:
        notification = _STORE.queue_notification(
            organization_id=organization_id,
            recipient_id=recipient_id,
            channel=channel,
            message=message,
            status=status,
        )
        _phase0_audit(
            organization_id=organization_id,
            event_type="phase0.notification_queue",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=recipient_id,
            status="recorded",
            payload=notification,
        )
        return {
            "view": "novaprogramming_phase0_notification",
            "organization_id": organization_id,
            "notification": notification,
            "read_only": False,
        }

    def phase0_notification_send(
        self,
        *,
        notification_id: str,
        organization_id: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "system",
    ) -> dict[str, Any]:
        notification = _STORE.mark_notification_sent(
            notification_id=notification_id,
            organization_id=organization_id,
        )
        if notification is None:
            raise ValueError("notification not found")
        _phase0_audit(
            organization_id=notification["organization_id"],
            event_type="phase0.notification_send",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=notification_id,
            status="recorded",
            payload=notification,
        )
        return {
            "view": "novaprogramming_phase0_notification_delivery",
            "organization_id": notification["organization_id"],
            "notification": notification,
            "read_only": False,
        }

    def phase0_notifications(
        self,
        *,
        organization_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        notifications = _STORE.list_notifications(
            organization_id=organization_id,
            status=status,
            limit=limit,
        )
        return {
            "view": "novaprogramming_phase0_notifications",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "count": len(notifications),
            "notifications": notifications,
            "read_only": True,
        }

    def phase0_integration_register(
        self,
        *,
        organization_id: str,
        name: str,
        type: str,
        config: dict[str, Any] | None = None,
        status: str = "active",
        last_synced_at: str | None = None,
        actor_user_id: str = "system",
        actor_role: str = "system",
    ) -> dict[str, Any]:
        integration = _STORE.register_integration(
            organization_id=organization_id,
            name=name,
            type=type,
            config=config,
            status=status,
            last_synced_at=last_synced_at,
        )
        _phase0_audit(
            organization_id=organization_id,
            event_type="phase0.integration_register",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=name,
            status="recorded",
            payload=integration,
        )
        return {
            "view": "novaprogramming_phase0_integration",
            "organization_id": organization_id,
            "integration": integration,
            "read_only": False,
        }

    def phase0_integrations(
        self,
        *,
        organization_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        integrations = _STORE.list_integrations(
            organization_id=organization_id,
            status=status,
            limit=limit,
        )
        return {
            "view": "novaprogramming_phase0_integrations",
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
            "count": len(integrations),
            "integrations": integrations,
            "read_only": True,
        }


__all__ = [

    "NovaProgrammingControlPlane",
    "STACK_SURFACES",
    "PRODUCT_SURFACES",
    "ROLE_SURFACES",
    "STAFF_ROLES",
    "build_audit_log",
    "build_assurance_alerts",
    "build_assurance_certification",
    "build_assurance_history",
    "build_assurance_report",
    "build_assurance_report_generate",
    "build_assurance_run",
    "build_assurance_status",
    "build_dashboard_analytics",
    "build_dashboard_analytics_history",
    "build_dashboard_analytics_insights",
    "build_dashboard_analytics_prediction",
    "build_dashboard_demand_forecast",
    "build_dashboard_decisions",
    "build_dashboard_decisions_history",
    "build_dashboard_actions",
    "build_dashboard_actions_history",
    "build_dashboard_autonomy",
    "build_dashboard_city_automation",
    "build_dashboard_multi_city_orchestration",
    "build_dashboard_digital_twin",
    "build_dashboard_meta_learning_redesign",
    "build_dashboard_business_pricing",
    "build_dashboard_city_profit_optimization",
    "build_outcome_status",
    "build_outcome_registry",
    "build_outcome_learning",
    "build_outcome_scoring",
    "build_outcome_replay",
    "build_organization_onboarding",
    "build_phase0_status",
    "seed_phase0_catalog",
    "build_federated_trust_network",
    "build_trust_marketplace_services",
    "build_trust_marketplace",
    "build_workflow_instances",
    "build_organization_directory",
    "build_rbac_catalog",
    "build_rbac_assignments",
    "build_rbac_access_check",
    "build_rbac_role_dashboard",
    "build_catalog",
    "build_certificate_chains",
    "build_certificate_issue",
    "build_certificate_verify",
    "build_cloud_deployment",
    "build_cloud_health",
    "build_cloud_request_deployment",
    "build_cloud_scale",
    "build_cloud_services",
    "build_code_explanation",
    "build_assurance",
    "build_billing_summary",
    "build_crypto_backend_register",
    "build_crypto_backends",
    "build_decentralized_trust_graph",
    "build_distributed_trust_network",
    "build_event_topic_create",
    "build_event_topics",
    "build_event_publish",
    "build_event_consume",
    "build_identity_bind",
    "build_identity_bindings",
    "build_governance_check",
    "build_governance_approve",
    "build_governance_policy",
    "build_insights",
    "build_v9_schema",
    "build_billing_preview",
    "build_trust_consensus",
    "build_certificate_transparency_append",
    "build_certificate_transparency_log",
    "build_key_revocation",
    "build_key_revocations",
    "build_trace_span",
    "build_trace_spans",
    "build_assurance_scheduler_run",
    "build_assurance_scheduler_history",
    "build_billing_records",
    "build_federation_claim",
    "build_federation_register",
    "build_federation_verify",
    "build_risk_prediction",
    "build_risk_predictions",
    "build_key_registry",
    "build_key_rotation",
    "build_policy_create",
    "build_policy_decisions",
    "build_policy_evaluate",
    "build_policy_registry",
    "build_metrics",
    "build_certification",
    "build_signed_audit_chain",
    "build_signed_audit_verify",
    "build_repo_intelligence",
    "build_retention",
    "build_retention_check",
    "build_retention_set",
    "build_stream_backends",
    "build_stream_backend_register",
    "build_workflow_history",
    "build_workflow_signal",
    "build_workflow_start",
    "build_workflow_status",
    "build_trust",
    "build_trust_anomalies",
    "build_trust_replay",
    "build_trust_risk",
    "build_trust_exchange_events",
    "build_trust_exchange_verify",
    "build_trust_trends",
    "build_trust_stream",
    "build_trust_verify_external",
    "build_trust_fabric_link",
    "build_trust_fabric_region_register",
    "build_trust_fabric_regions",
    "build_trust_fabric_signed_request",
    "build_trust_fabric_signed_request_verify",
    "build_trust_negotiation",
    "build_trust_negotiations",
    "build_controlled_execution_activation",
    "build_marketplace_onboarding_strategy",
    "build_staff_dashboard",
    "build_status",
    "build_studio_context",
    "build_studio_generation",
    "build_zero_trust_create",
    "build_zero_trust_decisions",
    "build_zero_trust_evaluate",
    "build_zero_trust_policies",
    "build_proof",
    "build_replay",
    "default_control_plane",
    "get_control_plane",
    "lookup_proof",
    "record_dashboard_analytics_snapshot",
    "record_dashboard_decision_snapshot",
    "record_dashboard_action_snapshot",
]
