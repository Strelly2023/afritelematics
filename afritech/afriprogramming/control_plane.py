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

_STORE = get_platform_store()


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


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
    "build_trust_consensus",
    "build_certificate_transparency_append",
    "build_certificate_transparency_log",
    "build_key_revocation",
    "build_key_revocations",
    "build_trace_span",
    "build_trace_spans",
    "build_assurance_scheduler_run",
    "build_assurance_scheduler_history",
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
]
