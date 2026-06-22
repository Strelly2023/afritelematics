from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from uuid import uuid4

from afritech.api.app import app as full_app
from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novatech_intranet_api import build_novatech_intranet_router
from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore
from afritech.novascript import get_novascript_service


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novatech_intranet_router())
    return TestClient(app)


def build_full_client() -> TestClient:
    return TestClient(full_app)


def auth_headers(role: str = "DEVELOPER", user_id: str = "dev-1", organization_id: str = "org-nova") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_intranet_html_entrypoint_is_available() -> None:
    client = build_client()

    response = client.get("/novatech/intranet/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "NovaTech Intranet" in response.text
    assert "/v1/novascript/dashboard" in response.text


def test_intranet_status_and_dashboard_compose_existing_surfaces() -> None:
    client = build_client()

    status = client.get("/v1/novatech/intranet/status", headers=auth_headers(role="OPERATOR"))
    assert status.status_code == 200
    assert status.json()["product"] == "NovaTech Intranet"
    assert status.json()["dashboards"]["novatech_platform"] == "/v1/novatech/intranet/platform"

    dashboard = client.get(
        "/v1/novatech/intranet/dashboard?role=developers&project_id=project-employee-rbac",
        headers=auth_headers(role="DEVELOPER"),
    )
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["view"] == "novatech_intranet_dashboard"
    assert body["novascript_dashboard"]["status"]["product"] == "NovaScript"
    assert body["novaprogramming_dashboard"]["status"]["platform"] == "NovaProgramming"
    assert body["read_only"] is True


def test_novatech_platform_surfaces_expose_org_os_sections() -> None:
    client = build_client()

    platform = client.get(
        "/v1/novatech/intranet/platform",
        headers=auth_headers(role="OPERATOR"),
    )
    assert platform.status_code == 200
    payload = platform.json()
    assert payload["view"] == "novatech_intranet_platform"
    assert payload["surfaces"]["intranet"]["route"] == "/novatech/intranet/"
    assert payload["surfaces"]["extranet"]["audiences"] == [
        "CLIENT",
        "PARTNER",
        "SUPPLIER",
        "INVESTOR",
    ]
    assert payload["surfaces"]["knowledge"]["project_count"] >= 1
    assert payload["surfaces"]["workflows"]["read_only"] is True
    assert payload["surfaces"]["comms"]["message_count"] >= 0

    extranet = client.get("/v1/novatech/extranet/status", headers=auth_headers(role="OPERATOR"))
    assert extranet.status_code == 200
    assert extranet.json()["route"] == "/novatech/extranet/"

    knowledge = client.get("/v1/novatech/intranet/knowledge", headers=auth_headers(role="OPERATOR"))
    assert knowledge.status_code == 200
    assert knowledge.json()["workspace"]["workspace_mode"] == "codex_style"

    workflows = client.get("/v1/novatech/intranet/workflows", headers=auth_headers(role="OPERATOR"))
    assert workflows.status_code == 200
    assert "templates" in workflows.json()

    comms = client.get("/v1/novatech/intranet/comms", headers=auth_headers(role="OPERATOR"))
    assert comms.status_code == 200
    assert comms.json()["channels"][0]["name"] == "operations"


def test_novatech_saas_surfaces_expose_tenants_billing_and_safe_execution() -> None:
    client = build_client()
    tenant_id = f"tenant-{uuid4().hex[:8]}"
    get_novascript_service().onboard_organization(
        organization_id=tenant_id,
        legal_name="Tenant Mobility Group",
        sector="Mobility",
        trust_domain="tenant-ops",
    )

    saas = client.get("/v1/novatech/saas/status", headers=auth_headers(role="OPERATOR", organization_id=tenant_id))
    assert saas.status_code == 200
    saas_payload = saas.json()
    assert saas_payload["view"] == "novatech_saas_status"
    assert saas_payload["tenant_count"] >= 1
    assert any(item["organization_id"] == tenant_id for item in saas_payload["organizations"])
    assert saas_payload["safe_execution"]["advisory_only"] is True
    assert saas_payload["safe_execution"]["execution_authority"] is False
    assert saas_payload["billing_surface"]["subscription_preview"]["status"] == "active"

    directory = client.get("/v1/novatech/organizations", headers=auth_headers(role="OPERATOR", organization_id=tenant_id))
    assert directory.status_code == 200
    directory_payload = directory.json()
    assert directory_payload["view"] == "novatech_organization_directory"
    assert any(item["organization_id"] == tenant_id for item in directory_payload["tenants"])

    detail = client.get(
        f"/v1/novatech/organizations/{tenant_id}",
        headers=auth_headers(role="OPERATOR", organization_id=tenant_id),
    )
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["view"] == "novatech_organization_detail"
    assert detail_payload["safe_execution"]["advisory_only"] is True
    assert detail_payload["billing"]["subscription_preview"]["status"] == "active"

    billing = client.get(
        f"/v1/novatech/organizations/{tenant_id}/billing",
        headers=auth_headers(role="OPERATOR", organization_id=tenant_id),
    )
    assert billing.status_code == 200
    assert billing.json()["invoice_preview"]["status"] == "open"

    execution = client.get(
        f"/v1/novatech/organizations/{tenant_id}/execution",
        headers=auth_headers(role="OPERATOR", organization_id=tenant_id),
    )
    assert execution.status_code == 200
    execution_payload = execution.json()
    assert execution_payload["view"] == "novatech_safe_execution"
    assert execution_payload["execution"]["advisory_only"] is True
    assert execution_payload["execution"]["execution_authority"] is False


def test_novatech_outcome_trust_marketplace_and_onboarding_surfaces(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "novatech-outcomes.sqlite3")
    try:
        client = build_client()
        tenant_ids = [f"tenant-{uuid4().hex[:8]}" for _ in range(3)]
        for tenant_id in tenant_ids:
            onboard = client.post(
                "/v1/novatech/organizations/onboard",
                headers=auth_headers(role="OPERATOR", organization_id=tenant_ids[0]),
                json={
                    "organization_id": tenant_id,
                    "legal_name": f"Tenant {tenant_id[-4:]} Group",
                    "sector": "Mobility",
                    "trust_domain": "tenant-ops",
                },
            )
            assert onboard.status_code == 200
            assert onboard.json()["status"] == "onboarded"

        directory = client.get("/v1/novatech/organizations", headers=auth_headers(role="OPERATOR", organization_id=tenant_ids[0]))
        assert directory.status_code == 200
        directory_payload = directory.json()
        assert all(
            any(item["organization_id"] == tenant_id for item in directory_payload["tenants"])
            for tenant_id in tenant_ids
        )

        org_id = tenant_ids[0]
        control_plane.record_dashboard_analytics_snapshot(
            organization_id=org_id,
            payload={
                "fleet_trust_score": 95,
                "active_drivers": 10,
                "verified_rides_today": 44,
                "evidence_packets_today": 35,
                "open_replay_exceptions": 1,
                "replay_exception_rate_pct": 2.5,
                "driver_trust_trend": [{"driver_id": "driver-1", "score": 93}],
                "pilot_evidence": {
                    "shift_count": 44,
                    "gps_signal_loss_events": 0,
                    "route_deviation_events": 1,
                    "latency_breaches": 0,
                },
            },
            source="afriride_operator_dashboard",
        )
        decision_snapshot = control_plane.record_dashboard_decision_snapshot(
            organization_id=org_id,
            payload={
                "fleet_trust_score": 95,
                "active_drivers": 10,
                "verified_rides_today": 44,
                "evidence_packets_today": 35,
                "open_replay_exceptions": 1,
                "replay_exception_rate_pct": 2.5,
                "driver_trust_trend": [{"driver_id": "driver-1", "score": 93}],
                "pilot_evidence": {
                    "shift_count": 44,
                    "gps_signal_loss_events": 0,
                    "route_deviation_events": 1,
                    "latency_breaches": 0,
                },
            },
            source="afriride_operator_dashboard",
            decision_type="operator_decision",
        )
        control_plane.record_dashboard_action_snapshot(
            organization_id=org_id,
            payload={
                "fleet_trust_score": 95,
                "active_drivers": 10,
                "verified_rides_today": 44,
                "evidence_packets_today": 35,
                "open_replay_exceptions": 1,
                "replay_exception_rate_pct": 2.5,
                "driver_trust_trend": [{"driver_id": "driver-1", "score": 93}],
                "pilot_evidence": {
                    "shift_count": 44,
                    "gps_signal_loss_events": 0,
                    "route_deviation_events": 1,
                    "latency_breaches": 0,
                },
            },
            source="afriride_operator_dashboard",
            decision_snapshot_id=decision_snapshot["decision_id"],
            action_type="controlled_autonomous_action",
        )

        outcomes = client.get("/v1/novatech/outcomes/status", headers=auth_headers(role="OPERATOR", organization_id=org_id))
        assert outcomes.status_code == 200
        outcomes_payload = outcomes.json()
        assert outcomes_payload["view"] == "novatech_outcome_intelligence"
        assert outcomes_payload["read_only"] is True
        assert outcomes_payload["projection_only"] is True
        assert outcomes_payload["history"]["count"] >= 1
        assert outcomes_payload["learning"]["band"] in {"learn", "watch", "hold", "recalibrate"}
        assert outcomes_payload["replay"]["replayable"] is True

        organization_outcomes = client.get(
            f"/v1/novatech/organizations/{org_id}/outcomes",
            headers=auth_headers(role="OPERATOR", organization_id=org_id),
        )
        assert organization_outcomes.status_code == 200
        assert organization_outcomes.json()["current"]["outcome_status"] in {
            "measured",
            "learning",
            "review",
            "recalibrate",
        }

        registry = client.get("/v1/novatech/outcomes/registry", headers=auth_headers(role="OPERATOR", organization_id=org_id))
        assert registry.status_code == 200
        assert registry.json()["registry"]["count"] >= 1

        learning = client.get("/v1/novatech/outcomes/learning", headers=auth_headers(role="OPERATOR", organization_id=org_id))
        assert learning.status_code == 200
        assert learning.json()["learning"]["cycle"][-1] == "recalibrate"

        scoring = client.get("/v1/novatech/outcomes/scoring", headers=auth_headers(role="OPERATOR", organization_id=org_id))
        assert scoring.status_code == 200
        assert scoring.json()["scoring"]["score"] >= 0

        replay = client.get("/v1/novatech/outcomes/replay", headers=auth_headers(role="OPERATOR", organization_id=org_id))
        assert replay.status_code == 200
        assert replay.json()["replay"]["status"] in {"measured", "learning", "review", "recalibrate"}

        trust_network = client.get(
            "/v1/novatech/trust-network/status",
            headers=auth_headers(role="OPERATOR", organization_id=org_id),
        )
        assert trust_network.status_code == 200
        trust_network_payload = trust_network.json()
        assert trust_network_payload["member_count"] >= 3
        assert trust_network_payload["exchange_catalog"]
        assert trust_network_payload["tenant_pairs"]

        marketplace = client.get(
            "/v1/novatech/marketplace/status",
            headers=auth_headers(role="OPERATOR", organization_id=org_id),
        )
        assert marketplace.status_code == 200
        marketplace_payload = marketplace.json()
        assert marketplace_payload["summary"]["service_count"] == 4
        assert marketplace_payload["services"][0]["consumable_across_tenants"] is True

        marketplace_services = client.get(
            "/v1/novatech/marketplace/services",
            headers=auth_headers(role="OPERATOR", organization_id=org_id),
        )
        assert marketplace_services.status_code == 200
        assert marketplace_services.json()["service_count"] == 4
    finally:
        control_plane._STORE = original_store


def test_controlled_execution_activation_and_marketplace_onboarding_strategy(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "novatech-controlled-execution.sqlite3")
    try:
        client = build_client()
        tenant_id = f"tenant-{uuid4().hex[:8]}"
        onboard = client.post(
            "/v1/novatech/organizations/onboard",
            headers=auth_headers(role="OPERATOR", organization_id=tenant_id),
            json={
                "organization_id": tenant_id,
                "legal_name": "Controlled Execution Fleet",
                "sector": "Mobility",
                "trust_domain": "tenant-ops",
            },
        )
        assert onboard.status_code == 200

        payload = {
            "fleet_trust_score": 99,
            "active_drivers": 14,
            "verified_rides_today": 58,
            "evidence_packets_today": 58,
            "open_replay_exceptions": 0,
            "replay_exception_rate_pct": 0.0,
            "driver_trust_trend": [{"driver_id": "driver-1", "score": 98}],
            "pilot_evidence": {
                "shift_count": 58,
                "gps_signal_loss_events": 0,
                "route_deviation_events": 0,
                "latency_breaches": 0,
            },
        }
        decision_snapshot = None
        for _ in range(8):
            control_plane.record_dashboard_analytics_snapshot(
                organization_id=tenant_id,
                payload=payload,
                source="afriride_operator_dashboard",
            )
            decision_snapshot = control_plane.record_dashboard_decision_snapshot(
                organization_id=tenant_id,
                payload=payload,
                source="afriride_operator_dashboard",
                decision_type="operator_decision",
            )
            control_plane.record_dashboard_action_snapshot(
                organization_id=tenant_id,
                payload=payload,
                source="afriride_operator_dashboard",
                decision_snapshot_id=decision_snapshot["decision_id"],
                action_type="controlled_autonomous_action",
            )

        activation = client.get(
            f"/v1/novatech/organizations/{tenant_id}/execution/activation",
            headers=auth_headers(role="OPERATOR", organization_id=tenant_id),
        )
        assert activation.status_code == 200
        activation_payload = activation.json()
        assert activation_payload["view"] == "novatech_controlled_execution_activation"
        assert activation_payload["activation"]["safe_execution_enabled"] is True
        assert activation_payload["activation"]["activation_status"] == "held"

        activate = client.post(
            f"/v1/novatech/organizations/{tenant_id}/execution/activate",
            headers=auth_headers(role="OPERATOR", organization_id=tenant_id),
            json={
                "acknowledged": True,
                "requested_tier": "controlled",
                "operator_note": "Operator confirmed readiness for controlled execution.",
            },
        )
        assert activate.status_code == 200
        activate_payload = activate.json()
        assert activate_payload["activation"]["safe_execution_enabled"] is True
        assert activate_payload["activation"]["activation_status"] == "enabled"
        assert activate_payload["activation"]["execution_tier"] == "controlled"
        assert activate_payload["activation"]["execution_authority"] is False

        marketplace_onboarding = client.get(
            "/v1/novatech/marketplace/onboarding",
            headers=auth_headers(role="OPERATOR", organization_id=tenant_id),
        )
        assert marketplace_onboarding.status_code == 200
        marketplace_onboarding_payload = marketplace_onboarding.json()
        assert marketplace_onboarding_payload["view"] == "novatech_marketplace_onboarding"
        assert len(marketplace_onboarding_payload["phases"]) == 5
        assert marketplace_onboarding_payload["partner_cohort"][0]["role"] == "Pilot launch partner"
    finally:
        control_plane._STORE = original_store


def test_intranet_analytics_exposes_persisted_operator_intelligence(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "novatech-analytics.sqlite3")
    try:
        control_plane.record_dashboard_analytics_snapshot(
            organization_id="org-nova",
            payload={
                "fleet_trust_score": 96,
                "active_drivers": 12,
                "verified_rides_today": 48,
                "evidence_packets_today": 37,
                "open_replay_exceptions": 1,
                "replay_exception_rate_pct": 2.1,
                "driver_trust_trend": [{"driver_id": "driver-1", "score": 94}],
                "pilot_evidence": {
                    "shift_count": 48,
                    "gps_signal_loss_events": 0,
                    "route_deviation_events": 1,
                    "latency_breaches": 0,
                },
            },
            source="afriride_operator_dashboard",
        )
        decision_snapshot = control_plane.record_dashboard_decision_snapshot(
            organization_id="org-nova",
            payload={
                "fleet_trust_score": 96,
                "active_drivers": 12,
                "verified_rides_today": 48,
                "evidence_packets_today": 37,
                "open_replay_exceptions": 1,
                "replay_exception_rate_pct": 2.1,
                "driver_trust_trend": [{"driver_id": "driver-1", "score": 94}],
                "pilot_evidence": {
                    "shift_count": 48,
                    "gps_signal_loss_events": 0,
                    "route_deviation_events": 1,
                    "latency_breaches": 0,
                },
            },
            source="afriride_operator_dashboard",
            decision_type="operator_decision",
        )
        control_plane.record_dashboard_action_snapshot(
            organization_id="org-nova",
            payload={
                "fleet_trust_score": 96,
                "active_drivers": 12,
                "verified_rides_today": 48,
                "evidence_packets_today": 37,
                "open_replay_exceptions": 1,
                "replay_exception_rate_pct": 2.1,
                "driver_trust_trend": [{"driver_id": "driver-1", "score": 94}],
                "pilot_evidence": {
                    "shift_count": 48,
                    "gps_signal_loss_events": 0,
                    "route_deviation_events": 1,
                    "latency_breaches": 0,
                },
            },
            source="afriride_operator_dashboard",
            decision_snapshot_id=decision_snapshot["decision_id"],
            action_type="controlled_autonomous_action",
        )

        client = build_client()
        response = client.get(
            "/v1/novatech/intranet/analytics",
            headers=auth_headers(role="OPERATOR"),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["operator_analytics"]["history"]["count"] >= 1
        assert payload["operator_analytics"]["latest"]["source"] == "afriride_operator_dashboard"
        assert payload["operator_analytics"]["prediction"]["risk_level"] in {"low", "medium", "high"}
        assert payload["novaprogramming_insights"]["status"] == "ok"

        decisions = client.get(
            "/v1/novatech/intranet/decisions",
            headers=auth_headers(role="OPERATOR"),
        )
        assert decisions.status_code == 200
        decisions_payload = decisions.json()
        assert decisions_payload["operator_decisions"]["history"]["count"] >= 1
        assert decisions_payload["operator_decisions"]["current"]["decision_lane"] in {
            "observe",
            "watch",
            "review",
            "escalate",
        }

        actions = client.get(
            "/v1/novatech/intranet/actions",
            headers=auth_headers(role="OPERATOR"),
        )
        assert actions.status_code == 200
        actions_payload = actions.json()
        assert actions_payload["operator_actions"]["history"]["count"] >= 1
        assert actions_payload["operator_actions"]["current"]["advisory_only"] is True
    finally:
        control_plane._STORE = original_store


def test_dashboard_websocket_receives_live_published_event() -> None:
    client = build_full_client()
    token = JWT.create_token("operator-1", role="OPERATOR", organization_id="org-nova")

    with client.websocket_connect(f"/ws/dashboard?token={token}") as websocket:
        connected = websocket.receive_json()
        assert connected["channel"] == "dashboard"
        assert connected["status"] == "connected"

        response = client.post(
            "/v1/realtime/dashboard/publish",
            json={
                "type": "LIVE_DASHBOARD_TICK",
                "data": {
                    "source": "test",
                    "summary": {"status": "ready"},
                },
            },
            headers=auth_headers(role="OPERATOR"),
        )

        assert response.status_code == 200
        payload = websocket.receive_json()
        assert payload["type"] == "LIVE_DASHBOARD_TICK"
        assert payload["authority"] == "projection_only"
        assert payload["channel"] == "dashboard"
        assert payload["data"]["source"] == "test"
