from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(service))
    return TestClient(app)


def _headers(role: str, user_id: str = "usr_djuma") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def test_solution_package_creates_approval_knowledge_and_event_bus_snapshot(tmp_path: Path) -> None:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "platform.sqlite3"))

    package = service.orchestrate_solution_package(
        {
            "title": "NovaRide payment reconciliation",
            "request": "Build NovaRide payment reconciliation service with audit evidence and compliance checks.",
            "domain": "payments",
            "region": "Australia",
            "risk_level": "medium",
            "execution_enabled": False,
            "comments": ["Review routing", "Attach evidence"],
        }
    )

    assert package["solution"]["title"] == "NovaRide payment reconciliation"
    assert package["approval"]["solution_id"] == package["solution"]["id"]
    assert package["approval"]["knowledge_created"] is True
    assert package["knowledge_entry"]["solution_id"] == package["solution"]["id"]
    assert any(agent["id"] == "security-agent" for agent in package["agent_team"])
    assert any(agent["id"] == "compliance-agent" for agent in package["agent_team"])
    assert len(package["events"]) == 4

    snapshot = service.event_bus_snapshot()
    assert snapshot["domain_events"] >= 5
    assert snapshot["outbox_pending"] >= 1


def test_replay_knowledge_graph_persists_approved_nodes(tmp_path: Path) -> None:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "platform.sqlite3"))

    package = service.orchestrate_solution_package(
        {
            "title": "NovaCodePro architecture decision",
            "request": "Review the approval and knowledge graph lifecycle.",
            "risk_level": "medium",
        }
    )

    nodes = service.replay_knowledge_graph()
    assert nodes
    assert any(node["solution_id"] == package["solution"]["id"] for node in nodes)


def test_platform_api_exposes_solution_packages_and_queue_controls(tmp_path: Path) -> None:
    client = _client(tmp_path)

    package_response = client.post(
        "/v1/novacodepro/solutions/packages",
        headers=_headers("DEVELOPER"),
        json={
            "title": "Enterprise AI operating system",
            "request": "Create a governed AI operating system with approval objects and a knowledge graph.",
            "risk_level": "high",
            "execution_enabled": False,
        },
    )
    assert package_response.status_code == 200
    package = package_response.json()
    assert package["solution"]["title"] == "Enterprise AI operating system"
    assert package["approval"]["status"] in {"APPROVED", "REVIEWED"}

    bus_response = client.get("/v1/novacodepro/event-bus", headers=_headers("OBSERVER"))
    assert bus_response.status_code == 200
    assert "domain_events" in bus_response.json()

    retry_response = client.post(
        "/v1/novacodepro/retry-queue",
        headers=_headers("DEVELOPER"),
        json={
            "event_id": "evt-1001",
            "consumer_name": "knowledge-graph-consumer",
            "aggregate_id": "sol-1001",
            "event_type": "knowledge.entry.promoted",
            "payload": {"solution_id": "sol-1001"},
            "retry_count": 0,
            "next_retry_at": "2026-07-13T12:00:00Z",
            "last_error": "temporary timeout",
        },
    )
    assert retry_response.status_code == 200
    retry_id = retry_response.json()["id"]

    dead_letter_response = client.post(
        f"/v1/novacodepro/retry-queue/{retry_id}/dead-letter",
        headers=_headers("DEVELOPER"),
        json={"failure_reason": "invalid aggregate"},
    )
    assert dead_letter_response.status_code == 200

    queue_response = client.get("/v1/novacodepro/dead-letter-queue", headers=_headers("OBSERVER"))
    assert queue_response.status_code == 200
    assert queue_response.json()


def test_platform_api_exposes_edos_capability_state_registry(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/novacodepro/edos/capability-states", headers=_headers("OBSERVER"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FOUR_STATE_GOVERNANCE_MODEL"
    assert body["transition_rule"] == "implemented -> verified -> certified -> approved"
    assert all(record["lifecycle_validation"]["valid"] is True for record in body["records"])
    assert any(
        record["domain"] == "GA Governance" and record["lifecycle_validation"]["current_state"] == "implemented"
        for record in body["records"]
    )


def test_platform_api_exposes_edos_frontend_backend_and_authority_architecture(tmp_path: Path) -> None:
    client = _client(tmp_path)

    frontends = client.get("/v1/novacodepro/edos/frontends", headers=_headers("OBSERVER"))
    assert frontends.status_code == 200
    assert frontends.json()["status"] == "FEDERATED_EXPERIENCE_LAYER"
    assert any(item["name"] == "NovaCodePro Executive" for item in frontends.json()["experiences"])

    backends = client.get("/v1/novacodepro/edos/backends", headers=_headers("OBSERVER"))
    assert backends.status_code == 200
    assert backends.json()["status"] == "FEDERATED_DOMAIN_SEPARATED_BACKENDS"
    assert "No service writes directly to another service database." in backends.json()["data_rules"]

    authority = client.get("/v1/novacodepro/edos/authority-model", headers=_headers("OBSERVER"))
    assert authority.status_code == 200
    assert "GA approval" in authority.json()["non_delegable_decisions"]


def test_platform_api_exposes_production_completion_program_and_ga_gate(tmp_path: Path) -> None:
    client = _client(tmp_path)

    program = client.get("/v1/novacodepro/edos/production-completion", headers=_headers("OBSERVER"))
    assert program.status_code == 200
    body = program.json()
    assert body["status"] == "AUTOMATION_IMPLEMENTED_LIVE_EVIDENCE_PENDING"
    assert body["ga_allowed"] is False
    assert body["real_payments_enabled"] is False
    assert body["prr_workflow"]["status"] == "READY_FOR_PRR_APPROVAL"
    assert body["verifiers"]["device_certification"]["simulation_allowed"] is False

    gate = client.post("/v1/novacodepro/edos/production-completion/ga-gate", headers=_headers("OBSERVER"), json={})
    assert gate.status_code == 200
    assert gate.json()["status"] == "GA_BLOCKED"
    assert gate.json()["ga_allowed"] is False
    assert gate.json()["real_payments_enabled"] is False


def test_platform_api_exposes_operational_readiness_program_and_payment_gates(tmp_path: Path) -> None:
    client = _client(tmp_path)

    program = client.get("/v1/novacodepro/edos/operational-readiness", headers=_headers("OBSERVER"))
    assert program.status_code == 200
    body = program.json()
    assert body["status"] == "REPOSITORY_IMPLEMENTED_LIVE_EVIDENCE_AND_GOVERNANCE_PENDING"
    assert body["ga_allowed"] is False
    assert body["real_payments_enabled"] is False
    assert "Architecture Studio" in [studio["studio"] for studio in body["edos_studios"]]
    assert "Stripe" in body["workstreams"]["enterprise_payment_activation"]["providers"]
    assert "OpenTelemetry" in body["workstreams"]["enterprise_integration_fabric"]["connectors"]["operations"]
    rows = {row["capability"]: row for row in body["readiness_matrix"]["capabilities"]}
    assert rows["Production Payments"]["repository"] is False
    assert rows["General Availability"]["operational"] is False

    blocked = client.post("/v1/novacodepro/edos/operational-readiness/evaluate", headers=_headers("OBSERVER"), json={})
    assert blocked.status_code == 200
    assert blocked.json()["status"] == "OPERATIONAL_READINESS_BLOCKED"
    assert blocked.json()["ga_allowed"] is False
    assert blocked.json()["real_payments_enabled"] is False

    allowed = client.post(
        "/v1/novacodepro/edos/operational-readiness/evaluate",
        headers=_headers("OBSERVER"),
        json={
            "evidence": {
                "design_sync": "PASS",
                "visual_regression": "PASS",
                "accessibility": "PASS",
                "opentelemetry": "PASS",
                "analytics": "PASS",
                "digital_ux_twin": "PASS",
                "automated_prr": "PASS",
            },
            "approvals": {
                "ux": "APPROVED",
                "engineering": "APPROVED",
                "security": "APPROVED",
                "operations": "APPROVED",
                "compliance": "APPROVED",
                "prr": "APPROVED",
                "executive": "APPROVED",
            },
        },
    )
    assert allowed.status_code == 200
    assert allowed.json()["ga_allowed"] is True
    assert allowed.json()["real_payments_enabled"] is False


def test_platform_api_exposes_enterprise_ux_operating_system(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/novacodepro/edos/ux-operating-system", headers=_headers("OBSERVER"))
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "NovaCodePro Enterprise UX Operating System"
    assert body["status"] == "IMPLEMENTED_NOT_PRODUCTION_APPROVED"
    assert body["governance"]["ga_allowed"] is False
    assert "Research Intelligence" in body["lifecycle"]
    assert "GENERAL_AVAILABILITY" in body["state_model"]

    studios = client.get("/v1/novacodepro/edos/ux-operating-system/studios", headers=_headers("OBSERVER"))
    assert studios.status_code == 200
    assert any(studio["name"] == "Accessibility Studio" for studio in studios.json()["studios"])

    validation = client.get("/v1/novacodepro/edos/ux-operating-system/validation", headers=_headers("OBSERVER"))
    assert validation.status_code == 200
    assert validation.json()["accessibility"]["evidence_schema"]["wcag_level"] == "AA"


def test_platform_api_manages_governed_ux_artifacts_and_evidence(tmp_path: Path) -> None:
    client = _client(tmp_path)

    created = client.post(
        "/v1/novacodepro/ux/artifacts",
        headers=_headers("UI_UX_DESIGNER"),
        json={
            "artifact": "Driver onboarding prototype",
            "artifact_type": "prototype",
            "studio": "Prototype Studio",
            "owner": "UX",
            "reviewers": ["Accessibility", "Product"],
            "traceability": {"requirement_id": "req-driver-onboarding", "prototype_id": "proto-driver-onboarding"},
        },
    )
    assert created.status_code == 200
    artifact = created.json()
    assert artifact["approval_state"] == "DRAFT"
    assert artifact["digital_signature"].startswith("sha256:")

    transition = client.post(
        f"/v1/novacodepro/ux/artifacts/{artifact['id']}/transition",
        headers=_headers("UI_UX_DESIGNER"),
        json={"target_state": "RESEARCH_COMPLETE", "note": "Research evidence reviewed."},
    )
    assert transition.status_code == 200
    assert transition.json()["approval_state"] == "RESEARCH_COMPLETE"

    skipped = client.post(
        f"/v1/novacodepro/ux/artifacts/{artifact['id']}/transition",
        headers=_headers("UI_UX_DESIGNER"),
        json={"target_state": "JOURNEYS_APPROVED"},
    )
    assert skipped.status_code == 400

    evidence = client.post(
        f"/v1/novacodepro/ux/artifacts/{artifact['id']}/evidence",
        headers=_headers("UI_UX_DESIGNER"),
        json={"evidence_refs": ["reports/ux/driver-onboarding-prototype.yaml"]},
    )
    assert evidence.status_code == 200
    assert evidence.json()["evidence_package"]["status"] == "EVIDENCE_CAPTURED"

    readiness = client.post("/v1/novacodepro/ux/releases/readiness", headers=_headers("UI_UX_DESIGNER"))
    assert readiness.status_code == 200
    assert readiness.json()["assessment"]["ga_allowed"] is False


def test_platform_api_records_uxos_service_fabric_evidence_pending_work(tmp_path: Path) -> None:
    client = _client(tmp_path)

    services = client.get("/v1/novacodepro/edos/ux-operating-system/services", headers=_headers("OBSERVER"))
    assert services.status_code == 200
    assert services.json()["status"] == "SERVICES_IMPLEMENTED_LIVE_INTEGRATION_PENDING"
    assert "Figma" in services.json()["design_integration_fabric"]["providers"]

    design_sync = client.post(
        "/v1/novacodepro/uxos/design-sync",
        headers=_headers("UI_UX_DESIGNER"),
        json={
            "subject": "NovaRide rider design system sync",
            "provider": "Figma",
            "environment": "integration",
            "evidence_refs": ["reports/ux/design-sync/figma-rider.yaml"],
        },
    )
    assert design_sync.status_code == 200
    assert design_sync.json()["record_type"] == "ux_design_sync"
    assert design_sync.json()["operational_complete"] is False
    assert design_sync.json()["ga_allowed"] is False

    visual = client.post(
        "/v1/novacodepro/uxos/visual-regression",
        headers=_headers("UI_UX_DESIGNER"),
        json={"subject": "Driver dashboard visual baseline", "provider": "Chrome", "environment": "ci"},
    )
    assert visual.status_code == 200
    assert visual.json()["digital_signature"].startswith("sha256:")

    scan = client.post(
        "/v1/novacodepro/uxos/accessibility-scans",
        headers=_headers("UI_UX_DESIGNER"),
        json={"subject": "Rider booking accessibility scan", "provider": "axe", "environment": "ci"},
    )
    assert scan.status_code == 200

    analytics = client.post(
        "/v1/novacodepro/uxos/analytics-events",
        headers=_headers("UI_UX_DESIGNER"),
        json={"subject": "Booking completion telemetry", "provider": "OpenTelemetry", "environment": "production"},
    )
    assert analytics.status_code == 200

    experiment = client.post(
        "/v1/novacodepro/uxos/experiments",
        headers=_headers("UI_UX_DESIGNER"),
        json={"subject": "Rider booking CTA experiment", "provider": "Feature Flags", "environment": "staging"},
    )
    assert experiment.status_code == 200

    graph = client.post(
        "/v1/novacodepro/uxos/knowledge-edges",
        headers=_headers("UI_UX_DESIGNER"),
        json={"subject": "Requirement to prototype lineage", "provider": "Knowledge Graph", "environment": "integration"},
    )
    assert graph.status_code == 200

    twin = client.post(
        "/v1/novacodepro/uxos/digital-twin-simulations",
        headers=_headers("UI_UX_DESIGNER"),
        json={"subject": "Poor network booking simulation", "provider": "Digital UX Twin", "environment": "integration"},
    )
    assert twin.status_code == 200

    status = client.get("/v1/novacodepro/uxos/operational-status", headers=_headers("OBSERVER"))
    assert status.status_code == 200
    body = status.json()
    assert body["operational_complete"] is False
    assert body["ga_allowed"] is False
    assert body["record_counts"]["ux_design_sync"] == 1
    assert body["record_counts"]["ux_visual_regression"] == 1
    assert body["record_counts"]["ux_accessibility_scan"] == 1


def test_platform_api_exposes_dimensional_completion_standard(tmp_path: Path) -> None:
    client = _client(tmp_path)

    standard = client.get("/v1/novacodepro/completion-standard", headers=_headers("OBSERVER"))
    assert standard.status_code == 200
    assert standard.json()["status"] == "STANDARD_IMPLEMENTED"
    assert "Portal UI" in standard.json()["level_1_repository_complete"]["deliverables"]
    assert standard.json()["invariants"]["ga_allowed"] is False

    dashboard = client.get("/v1/novacodepro/completion-standard/dashboard", headers=_headers("OBSERVER"))
    assert dashboard.status_code == 200
    rows = {row["domain"]: row for row in dashboard.json()["rows"]}
    assert rows["UXOS Services"]["repository"] is True
    assert rows["UXOS Services"]["operational"] is False
    assert rows["GA Promotion"]["repository"] is False

    repository_only = client.post(
        "/v1/novacodepro/completion-standard/evaluate",
        headers=_headers("OBSERVER"),
        json={
            "repository_complete": True,
            "operational_verified": False,
            "governance_approved": False,
        },
    )
    assert repository_only.status_code == 200
    assert repository_only.json()["level"] == "Repository Complete"
    assert repository_only.json()["ga_allowed"] is False
    assert repository_only.json()["real_payments_enabled"] is False

    evidence = client.post(
        "/v1/novacodepro/completion-standard/evidence",
        headers=_headers("UI_UX_DESIGNER"),
        json={
            "capability": "Accessibility automation",
            "environment": "production",
            "status": "PASS",
            "artifacts": ["reports/prr/accessibility.yaml"],
            "metrics": {"violations": 0},
            "screenshots": ["reports/prr/accessibility.png"],
        },
    )
    assert evidence.status_code == 200
    assert evidence.json()["capability"] == "Accessibility automation"
    assert evidence.json()["digital_signature"].startswith("sha256:")
