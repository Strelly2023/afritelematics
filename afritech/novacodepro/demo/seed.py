from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml

from afritech.novacodepro.demo.factories.approvals import build_approvals
from afritech.novacodepro.demo.factories.board import build_board_resolutions, build_board_workflows
from afritech.novacodepro.demo.factories.command_center import build_command_center_snapshot
from afritech.novacodepro.demo.factories.federation import build_federation_agreements
from afritech.novacodepro.demo.factories.incidents import build_incidents
from afritech.novacodepro.demo.factories.marketplace import build_marketplace_packages
from afritech.novacodepro.demo.factories.projects import build_projects
from afritech.novacodepro.demo.factories.risks import build_risks
from afritech.novacodepro.demo.factories._catalog import (
    build_deployments,
    build_evidence_bundles,
    build_permissions,
    build_releases,
    build_roles,
    build_service_registry,
)
from afritech.novacodepro.demo.factories.twins import build_twin_scenarios
from afritech.novacodepro.demo.factories.users import build_users
from afritech.novacodepro.demo.factories.workflows import build_workflows
from afritech.novacodepro.demo.guard import DemoEnvironmentGuard
from afritech.novacodepro.demo.personas import DEMO_PERSONAS, build_demo_persona_token
from afritech.novacodepro.platform import NovaCodeProPlatform, get_novacodepro_platform


DEMO_TENANT_ID = "tenant-novacodepro-enterprise-demo"
DEMO_ORGANIZATION_ID = "org-novatech-demo"
DEMO_REALM = "novatech-enterprise-demo"


@dataclass(frozen=True)
class EnterpriseDemoSeed:
    manifest_path: Path
    reset: bool = True
    create_users: bool = True
    create_projects: bool = True
    create_workflows: bool = True
    create_risks: bool = True
    create_approvals: bool = True
    create_incidents: bool = True
    create_marketplace: bool = True
    create_command_center: bool = True


def _load_manifest(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("enterprise demo manifest must be a mapping")
    return payload


def _validate_manifest(path: Path) -> dict[str, Any]:
    manifest = _load_manifest(path)
    required = {"tenant", "organization", "realms", "demo_guard"}
    missing = required - set(manifest)
    if missing:
        raise ValueError(f"missing manifest sections: {sorted(missing)}")
    if manifest["tenant"].get("id") != DEMO_TENANT_ID:
        raise ValueError("unexpected demo tenant id")
    if manifest["organization"].get("id") != DEMO_ORGANIZATION_ID:
        raise ValueError("unexpected demo organization id")
    return manifest


def seed_enterprise_demo(
    platform: NovaCodeProPlatform,
    *,
    manifest_path: Path,
    reset: bool = True,
    seed: EnterpriseDemoSeed | None = None,
) -> dict[str, Any]:
    manifest = _validate_manifest(manifest_path)
    if reset:
        reset_enterprise_demo(platform)

    guard = DemoEnvironmentGuard()
    if guard.enforce("production.deploy")["status"] != "blocked":
        raise RuntimeError("demo guard must block production deploy")

    snapshot = build_command_center_snapshot()

    config = seed or EnterpriseDemoSeed(manifest_path=manifest_path, reset=reset)
    records: dict[str, list[dict[str, Any]]] = {}
    records["users"] = [platform.repository.upsert("user", item) for item in build_users()] if config.create_users else []
    records["roles"] = [platform.repository.upsert("role", item) for item in build_roles()] if config.create_users else []
    records["permissions"] = [platform.repository.upsert("permission", item) for item in build_permissions()] if config.create_users else []
    records["projects"] = [platform.repository.upsert("project", item) for item in build_projects()] if config.create_projects else []
    records["workflows"] = [platform.repository.upsert("workflow", item) for item in build_workflows()] if config.create_workflows else []
    records["approvals"] = [platform.repository.upsert("approval", item) for item in build_approvals()] if config.create_approvals else []
    records["risks"] = [platform.repository.upsert("risk_record", item) for item in build_risks()] if config.create_risks else []
    records["federation"] = [platform.repository.upsert("federation_agreement", item) for item in build_federation_agreements()]
    records["board_meetings"] = [platform.repository.upsert("board_meeting", item) for item in build_board_workflows()]
    records["board_resolutions"] = [platform.repository.upsert("board_resolution", item) for item in build_board_resolutions()]
    records["incidents"] = [platform.repository.upsert("operation_record", item) for item in build_incidents()] if config.create_incidents else []
    records["marketplace"] = [platform.repository.upsert("marketplace_item", item) for item in build_marketplace_packages()] if config.create_marketplace else []
    records["twin_simulations"] = [platform.repository.upsert("twin_simulation", item) for item in build_twin_scenarios()]
    records["evidence"] = [platform.repository.upsert("evidence_bundle", item) for item in build_evidence_bundles()]
    records["releases"] = [platform.repository.upsert("release", item) for item in build_releases()]
    records["deployments"] = [platform.repository.upsert("deployment", item) for item in build_deployments()]
    records["services"] = [platform.repository.upsert("service", item) for item in build_service_registry()]
    records["command_center"] = [platform.repository.upsert("command_center_snapshot", snapshot)] if config.create_command_center else []

    persona_tokens = [build_demo_persona_token(persona, realm=DEMO_REALM) for persona in DEMO_PERSONAS]
    for persona in persona_tokens:
        platform.repository.upsert(
            "persona_token",
            {
                "id": persona["claims"]["sub"],
                "tenant_id": DEMO_TENANT_ID,
                "organization_id": DEMO_ORGANIZATION_ID,
                "realm": DEMO_REALM,
                "token": persona["token"],
                "claims": persona["claims"],
                "created_at": snapshot["created_at"],
                "updated_at": snapshot["updated_at"],
            },
        )

    summary = {
        "organization": 1,
        "tenant": 1,
        "users": len(records["users"]),
        "roles": len(records["roles"]),
        "permissions": len(records["permissions"]),
        "projects": len(records["projects"]),
        "workflows": len(records["workflows"]),
        "approvals": len(records["approvals"]),
        "risks": len(records["risks"]),
        "incidents": len(records["incidents"]),
        "evidence_bundles": len(records["evidence"]),
        "releases": len(records["releases"]),
        "deployments": len(records["deployments"]),
        "marketplace_packages": len(records["marketplace"]),
        "board_workflows": len(records["board_meetings"]),
        "board_resolutions": len(records["board_resolutions"]),
        "twin_scenarios": len(records["twin_simulations"]),
        "persona_tokens": len(persona_tokens),
        "command_center_snapshots": len(records["command_center"]),
        "demo_guard": guard.enforce("production.deploy"),
        "manifest": manifest,
        "status": "SUCCESS",
    }
    platform.repository.upsert(
        "demo_manifest",
        {
            "id": "enterprise-demo-manifest",
            "tenant_id": DEMO_TENANT_ID,
            "organization_id": DEMO_ORGANIZATION_ID,
            "manifest_path": str(manifest_path),
            "summary": summary,
            "created_at": snapshot["created_at"],
            "updated_at": snapshot["updated_at"],
        },
    )
    return summary


def reset_enterprise_demo(platform: NovaCodeProPlatform) -> dict[str, int]:
    deleted = 0
    demo_ids = {
        "user": [f"demo-user-{index:02d}" for index in range(1, 30)],
        "role": [role.lower() for role in ("ADMIN", "CTO", "CEO", "COO", "CFO", "CISO", "LEGAL", "RISK", "BOARD", "OPERATOR", "DEVELOPER", "OBSERVER", "VERIFIER", "SERVICE", "CUSTOMER")],
        "permission": [
            "identity_read",
            "identity_write",
            "project_read",
            "project_write",
            "solution_read",
            "solution_write",
            "workflow_read",
            "workflow_write",
            "approval_read",
            "approval_write",
            "release_read",
            "release_write",
            "deployment_read",
            "deployment_write",
            "risk_read",
            "risk_write",
            "policy_read",
            "policy_write",
            "graph_read",
            "graph_write",
            "twin_read",
            "twin_simulate",
            "board_read",
            "board_write",
            "sre_read",
            "sre_write",
            "marketplace_read",
            "marketplace_install",
            "command_center_read",
            "evidence_read",
        ],
        "project": ["demo-novaride", "demo-novapay", "demo-novahealth", "demo-partner-api"],
        "workflow": [f"demo-workflow-{index:02d}" for index in range(1, 9)],
        "approval": [f"demo-approval-{index:02d}" for index in range(1, 13)],
        "risk_record": [f"demo-risk-{index:02d}" for index in range(1, 5)],
        "federation_agreement": ["demo-federation-01"],
        "board_meeting": ["demo-board-meeting-01", "demo-board-meeting-02"],
        "board_resolution": ["demo-board-resolution-01", "demo-board-resolution-02"],
        "operation_record": ["demo-incident-01", "demo-incident-02"],
        "marketplace_item": ["demo-solution-pack", "demo-industry-pack", "demo-agent-pack", "demo-governance-pack", "demo-workflow-pack", "demo-ui-pack"],
        "twin_simulation": ["demo-twin-scenario-01", "demo-twin-scenario-02", "demo-twin-scenario-03"],
        "evidence_bundle": [f"demo-evidence-{index:02d}" for index in range(1, 11)],
        "release": [f"demo-release-{index:02d}" for index in range(1, 4)],
        "deployment": [f"demo-deployment-{index:02d}" for index in range(1, 5)],
        "service": ["demo-gateway-service", "demo-graph-service", "demo-board-service"],
        "persona_token": [persona.sub for persona in DEMO_PERSONAS],
        "demo_manifest": ["enterprise-demo-manifest"],
        "command_center_snapshot": ["demo-command-center-snapshot-01"],
    }
    for kind, ids in demo_ids.items():
        for record_id in ids:
            platform.repository.delete(kind, record_id)
            deleted += 1
    return {"deleted": deleted}


def build_releases() -> list[dict[str, Any]]:
    from afritech.novacodepro.demo.factories._catalog import build_releases as _build_releases

    return _build_releases()


def build_deployments() -> list[dict[str, Any]]:
    from afritech.novacodepro.demo.factories._catalog import build_deployments as _build_deployments

    return _build_deployments()


def build_evidence_bundles() -> list[dict[str, Any]]:
    from afritech.novacodepro.demo.factories._catalog import build_evidence_bundles as _build_evidence_bundles

    return _build_evidence_bundles()


def build_service_registry() -> list[dict[str, Any]]:
    from afritech.novacodepro.demo.factories._catalog import build_service_registry as _build_service_registry

    return _build_service_registry()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the NovaCodePro enterprise demo tenant")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--create-users", action="store_true")
    parser.add_argument("--create-projects", action="store_true")
    parser.add_argument("--create-workflows", action="store_true")
    parser.add_argument("--create-risks", action="store_true")
    parser.add_argument("--create-approvals", action="store_true")
    parser.add_argument("--create-incidents", action="store_true")
    parser.add_argument("--create-marketplace", action="store_true")
    parser.add_argument("--create-command-center", action="store_true")
    args = parser.parse_args(argv)
    create_flags = {
        "create_users": args.create_users,
        "create_projects": args.create_projects,
        "create_workflows": args.create_workflows,
        "create_risks": args.create_risks,
        "create_approvals": args.create_approvals,
        "create_incidents": args.create_incidents,
        "create_marketplace": args.create_marketplace,
        "create_command_center": args.create_command_center,
    }
    if not any(create_flags.values()):
        create_flags = {key: True for key in create_flags}
    platform = get_novacodepro_platform()
    seed = EnterpriseDemoSeed(
        manifest_path=Path(args.manifest),
        reset=args.reset,
        **create_flags,
    )
    summary = seed_enterprise_demo(platform, manifest_path=seed.manifest_path, reset=seed.reset, seed=seed)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
