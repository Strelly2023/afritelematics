from __future__ import annotations

from importlib import import_module

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore

_runtime = import_module("afriride_system.api.dependencies.runtime")
reset_gateway = _runtime.reset_gateway
reset_trace_log = _runtime.reset_trace_log


def test_next_gen_mobile_api_supports_rider_driver_and_operator_flows(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "next-gen-mobile.sqlite3"))
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "dashboard-analytics.sqlite3")
    reset_gateway()
    reset_trace_log()

    try:
        client = TestClient(app)

        rider_session = client.post(
            "/v1/mobile/auth/session",
            json={
                "actor_id": "rider-1",
                "role": "RIDER",
                "device_id": "device-1",
                "app_version": "1.0.0",
                "platform": "ios",
            },
        )
        assert rider_session.status_code == 200
        assert rider_session.json()["actor_id"] == "rider-1"

        operator_session = client.post(
            "/v1/mobile/auth/session",
            json={
                "actor_id": "operator-1",
                "role": "OPERATOR",
                "device_id": "device-2",
                "app_version": "1.0.0",
                "platform": "android",
            },
        )
        assert operator_session.status_code == 200
        assert operator_session.json()["actor_id"] == "operator-1"

        driver_online = client.post(
            "/v1/driver/driver-1/availability",
            json={"status": "available"},
        )
        assert driver_online.status_code == 200
        assert driver_online.json()["status"] == "available"

        requested = client.post(
            "/v1/rider/rides",
            json={
                "rider_id": "rider-1",
                "pickup": "Melbourne CBD",
                "dropoff": "Melbourne Airport",
                "ride_id": "ride-next-gen-001",
                "ride_type": "Airport",
            },
            headers={"Idempotency-Key": "ride-next-gen-request-001"},
        )
        assert requested.status_code == 200
        assert requested.json()["status"] == "requested"

        queue = client.get("/v1/driver/driver-1/ride-queue")
        assert queue.status_code == 200
        assert queue.json()["items"][0]["ride_id"] == "ride-next-gen-001"

        accepted = client.post(
            "/v1/driver/rides/ride-next-gen-001/accept",
            json={"driver_id": "driver-1"},
        )
        assert accepted.status_code == 200
        assert accepted.json()["status"] == "accepted"

        arrived = client.post(
            "/v1/driver/rides/ride-next-gen-001/arrive",
            json={"driver_id": "driver-1"},
        )
        assert arrived.status_code == 200
        assert arrived.json()["status"] == "arrived"

        started = client.post(
            "/v1/driver/rides/ride-next-gen-001/start",
            json={"driver_id": "driver-1"},
        )
        assert started.status_code == 200
        assert started.json()["status"] == "started"

        completed = client.post(
            "/v1/driver/rides/ride-next-gen-001/complete",
            json={"driver_id": "driver-1"},
        )
        assert completed.status_code == 200
        assert completed.json()["status"] == "completed"

        receipt = client.get("/v1/rider/rides/ride-next-gen-001/receipt")
        assert receipt.status_code == 200
        assert receipt.json()["verification_status"] == "PASSED"

        replay = client.get("/v1/rider/rides/ride-next-gen-001/replay")
        assert replay.status_code == 200
        assert replay.json()["replay_verified"] is True

        rider_history = client.get("/v1/rider/rides/history")
        assert rider_history.status_code == 200
        assert rider_history.json()["items"][0]["ride_id"] == "ride-next-gen-001"

        operator = client.get("/v1/operator/dashboard")
        assert operator.status_code == 200
        payload = operator.json()
        assert "fleet_trust_score" in payload
        assert "driver_trust_trend" in payload
        assert "public_verification" in payload

        analytics = client.get("/v1/operator/analytics")
        assert analytics.status_code == 200
        analytics_payload = analytics.json()
        assert analytics_payload["history"]["count"] >= 1
        assert analytics_payload["latest"]["source"] == "afriride_operator_dashboard"
        assert analytics_payload["prediction"]["risk_level"] in {"low", "medium", "high"}
        assert analytics_payload["insights"]

        analytics_history = client.get("/v1/operator/analytics/history")
        assert analytics_history.status_code == 200
        assert analytics_history.json()["history"]["count"] >= 1

        analytics_prediction = client.get("/v1/operator/analytics/predictions")
        assert analytics_prediction.status_code == 200
        assert analytics_prediction.json()["prediction"]["headline"]

        operator_decisions = client.get(
            "/v1/operator/decisions",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_decisions.status_code == 200
        operator_decisions_payload = operator_decisions.json()
        assert operator_decisions_payload["current"]["decision_lane"] in {
            "observe",
            "watch",
            "review",
            "escalate",
        }
        assert operator_decisions_payload["history"]["count"] >= 1

        operator_decisions_history = client.get(
            "/v1/operator/decisions/history",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_decisions_history.status_code == 200
        assert operator_decisions_history.json()["history"]["count"] >= 1

        operator_actions = client.get(
            "/v1/operator/actions",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_actions.status_code == 200
        operator_actions_payload = operator_actions.json()
        assert operator_actions_payload["current"]["quality_band"] in {
            "excellent",
            "strong",
            "guarded",
            "weak",
            "unknown",
        }
        assert operator_actions_payload["current"]["advisory_only"] is True
        assert operator_actions_payload["current"]["execution_tier"] in {
            "advisory",
            "assisted",
            "controlled",
            "supervised",
        }
        assert "execution_tier_ready" in operator_actions_payload["current"]

        operator_actions_history = client.get(
            "/v1/operator/actions/history",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_actions_history.status_code == 200
        assert operator_actions_history.json()["history"]["count"] >= 1

        operator_autonomy = client.get(
            "/v1/operator/autonomy",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_autonomy.status_code == 200
        operator_autonomy_payload = operator_autonomy.json()
        assert operator_autonomy_payload["autonomy"]["mode"] in {
            "advisory",
            "supervised",
            "autonomous",
            "fully_autonomous",
        }
        assert "safe_to_autorun" in operator_autonomy_payload["autonomy"]
        assert "thresholds" in operator_autonomy_payload["autonomy"]
        assert "driver_allocation" in operator_autonomy_payload
        assert "candidate_drivers" in operator_autonomy_payload["driver_allocation"]

        city_automation = client.get(
            "/v1/operator/city-automation",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert city_automation.status_code == 200
        city_automation_payload = city_automation.json()
        assert city_automation_payload["city_automation"]["mode"] in {
            "city_held",
            "city_supervised",
            "city_autonomous",
            "zero_operator",
        }
        assert "zero_operator_mode" in city_automation_payload["city_automation"]
        assert "coverage_score" in city_automation_payload["city_automation"]

        multi_city = client.get(
            "/v1/operator/multi-city-orchestration",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert multi_city.status_code == 200
        multi_city_payload = multi_city.json()
        assert multi_city_payload["multi_city_orchestration"]["mode"] in {
            "global_held",
            "global_supervised",
            "global_autonomous",
            "global_zero_operator",
        }
        assert "global_learning" in multi_city_payload
        assert "city_count" in multi_city_payload["multi_city_orchestration"]

        digital_twin = client.get(
            "/v1/operator/digital-twin",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert digital_twin.status_code == 200
        digital_twin_payload = digital_twin.json()
        assert digital_twin_payload["digital_twin"]["mode"] in {
            "shadow_sync",
            "predictive_closed_loop",
            "city_closed_loop",
            "global_closed_loop",
        }
        assert "self_improving_loop" in digital_twin_payload
        assert "live_sync_score" in digital_twin_payload["digital_twin"]

        business_pricing = client.get(
            "/v1/operator/business-pricing",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert business_pricing.status_code == 200
        business_pricing_payload = business_pricing.json()
        assert business_pricing_payload["view"] == "novatech_business_pricing"
        assert "pricing" in business_pricing_payload
        assert "incentives" in business_pricing_payload

        city_profit_optimization = client.get(
            "/v1/operator/city-profit-optimization",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert city_profit_optimization.status_code == 200
        city_profit_payload = city_profit_optimization.json()
        assert city_profit_payload["view"] == "novatech_city_profit_optimization"
        assert "budget_allocation" in city_profit_payload
        assert "profit_optimization" in city_profit_payload

        meta_learning = client.get(
            "/v1/operator/meta-learning-redesign",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert meta_learning.status_code == 200
        meta_learning_payload = meta_learning.json()
        assert meta_learning_payload["view"] == "novatech_meta_learning_redesign"
        assert meta_learning_payload["candidate_redesign"]["authority_boundary"] == "proposal_only"
        assert meta_learning_payload["mode"] in {"adaptive_redesign", "proposal_watch", "design_hold"}
        assert "self_redesign_rules" in meta_learning_payload
        assert "redesign_triggers" in meta_learning_payload

        intranet_analytics = client.get(
            "/v1/novatech/intranet/analytics",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert intranet_analytics.status_code == 200
        intranet_payload = intranet_analytics.json()
        assert intranet_payload["operator_analytics"]["history"]["count"] >= 1
        assert intranet_payload["novaprogramming_insights"]["status"] == "ok"
    finally:
        control_plane._STORE = original_store


def test_novaride_ecosystem_exposes_next_generation_app_family() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/ecosystem")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_ecosystem"
    assert payload["platform"] == "NovaRide"
    assert payload["app_count"] == 13
    assert payload["authority_boundary"]["payments"] == "NovaPay_backend_only"
    assert payload["authority_boundary"]["mobile_apps"] == "request_and_observe_only"
    assert payload["lifecycle"] == [
        "passenger_requests_ride",
        "nearest_driver_matched",
        "driver_accepts",
        "driver_arrives",
        "passenger_pickup",
        "trip_in_progress",
        "destination_reached",
        "payment_via_novapay",
        "driver_settlement",
        "ratings_and_feedback",
    ]
    app_names = {app_surface["name"] for app_surface in payload["apps"]}
    assert app_names == {
        "NovaRide Passenger",
        "NovaRide Driver",
        "NovaRide Operator App / Portal",
        "NovaRide Fleet",
        "NovaRide Business",
        "NovaRide Merchant Portal",
        "NovaRide Corporate Portal",
        "NovaRide Admin",
        "NovaRide Inspector App / Portal",
        "NovaRide Trust & Safety Portal",
        "NovaRide Support",
        "NovaRide Partner",
        "NovaRide Developer Portal",
    }
    route_families = payload["route_families"]
    assert route_families["passenger"] == "/v1/novaride/passenger"
    assert route_families["partner"] == "/v1/novaride/partner"
    assert route_families["operator"] == "/v1/novaride/operator"
    assert route_families["inspector"] == "/v1/novaride/inspector"
    assert route_families["merchant"] == "/v1/novaride/merchant"
    assert route_families["corporate"] == "/v1/novaride/corporate"
    assert route_families["developer"] == "/v1/novaride/developer"
    assert any(service["name"] == "NovaPay" for service in payload["shared_platform"])
    assert any(service["name"] == "Audit & Replay" for service in payload["shared_platform"])
    assert any(service["name"] == "Inspection Registry" for service in payload["shared_platform"])
    assert any(service["name"] == "Incident Registry" for service in payload["shared_platform"])
    enterprise_names = {capability["name"] for capability in payload["enterprise_operations_layer"]}
    assert enterprise_names == {
        "Unified Command Center",
        "City Operations / Zone Model",
        "Operational Digital Twin",
        "AI Decision Explanation Layer",
        "Workflow / Incident Engine",
        "Fleet Intelligence",
        "Public Trust Portal",
        "Partner / Developer Ecosystem",
        "SRE Observability",
        "Multi-Tenant Governance",
    }
    assert payload["enterprise_operations_score"] == "10/10"
    assert (
        payload["enterprise_operations_classification"]
        == "governed_evidence_backed_ai_assisted_mobility_control_platform"
    )
    assert "Demand Forecasting" in payload["intelligence_layer"]
    assert "Verification Package" in payload["trust_proof_flow"]
    assert "Control Plane decides" in payload["upgrade_principle"]


def test_novaride_platform_architecture_contract_exposes_authority_boundary_and_flow() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/platform/architecture-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_shared_platform_architecture_contract"
    assert payload["principle"] == (
        "Apps request and display; Control Plane decides; Execution Plane performs; Event Platform proves"
    )
    app_names = {app["app"] for app in payload["layers"]["app_layer"]}
    assert app_names == {"Passenger App", "Driver App", "Operator Dashboard"}
    assert payload["layers"]["api_gateway"]["role"] == "single_entry_point"
    assert payload["layers"]["api_gateway"]["responsibilities"] == [
        "request_validation",
        "novaid_authentication",
        "rbac_enforcement",
        "backend_service_routing",
    ]
    service_names = {service["name"] for service in payload["layers"]["execution_layer"]["services"]}
    assert {
        "NovaID",
        "NovaPay",
        "Dispatch Engine",
        "Pricing Engine",
        "Maps & Routing",
        "Trust Engine",
        "NovaNotify",
        "Analytics Engine",
        "Audit & Replay",
    } <= service_names
    assert payload["authority_boundary"]["payments"] == "NovaPay_backend_only"
    assert "dispatch_decisions" in payload["authority_boundary"]["backend_full_control"]
    assert "direct_provider_access" in payload["authority_boundary"]["apps_no_authority"]
    assert payload["ride_request_flow"] == [
        "passenger_app_requests_ride",
        "api_validates_request_with_novaid",
        "pricing_engine_estimates_fare",
        "dispatch_engine_matches_driver",
        "driver_app_receives_request",
        "driver_accepts",
        "maps_tracks_trip",
        "trip_completes",
        "novapay_processes_payment",
        "audit_engine_stores_logs",
        "analytics_updated",
    ]
    matrix = {row["app"]: row["services"] for row in payload["cross_app_service_matrix"]}
    assert matrix["Partner"] == ["Dispatch", "Billing"]
    assert matrix["Support"] == ["Replay", "NovaPay"]
    assert "saas_ready_structure" in payload["strategic_outcomes"]


def test_novaride_workspace_maps_apps_to_existing_governed_routes() -> None:
    client = TestClient(app)

    passenger = client.get("/v1/novaride/passenger/workspace")
    fleet = client.get("/v1/novaride/fleet/workspace")
    inspector = client.get("/v1/novaride/inspector/workspace")
    missing = client.get("/v1/novaride/unknown/workspace")

    assert passenger.status_code == 200
    passenger_payload = passenger.json()
    assert passenger_payload["surface"]["role"] == "CUSTOMER"
    assert passenger_payload["readiness"]["backend_authority"] == "centralized"
    assert passenger_payload["readiness"]["novapay_required"] is True
    assert "/v1/rider/rides" in passenger_payload["surface"]["primary_routes"]

    assert fleet.status_code == 200
    assert fleet.json()["surface"]["role"] == "FLEET_OWNER"

    assert inspector.status_code == 200
    assert inspector.json()["surface"]["role"] == "VERIFIER"
    assert inspector.json()["readiness"]["provider_integrations"] == "backend_only"

    assert missing.status_code == 404
    assert missing.json()["error"]["message"] == "novaride_surface_not_found"


def test_novaride_operator_dashboard_contract_exposes_modules_and_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/operator/dashboard-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_operator_dashboard_contract"
    assert payload["status"] == "controlled_pilot_ready"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Operations",
        "Ride Management",
        "Driver Monitoring",
        "Safety & Emergency",
        "Analytics Dashboard",
        "Predictive Demand ML",
        "Autonomous Strategy Engine",
        "Business Pricing & Incentives",
        "Budget Allocation & Profit Optimization",
        "NovaRide Ecosystem Panel",
        "Support & Escalation",
    }
    implemented_modules = {
        module["key"]
        for module in payload["modules"]
        if module["status"] == "implemented"
    }
    assert {"analytics", "ecosystem"}.issubset(implemented_modules)
    assert "manual_dispatch" in payload["authority_model"]["allowed"]
    assert "direct_payment_execution" in payload["authority_model"]["forbidden"]
    assert payload["authority_model"]["backend_authority"]["payments"] == "NovaPay"
    assert payload["layout"]["left_navigation"] == [
        "Operations",
        "Rides",
        "Drivers",
        "Safety",
        "Analytics",
        "Support",
    ]
    assert payload["workflow"] == [
        "passenger_requests_ride",
        "dispatch_assigns_driver",
        "operator_monitors_live_map",
        "driver_delayed_operator_reassigns",
        "risk_flag_operator_intervenes",
        "trip_completed",
        "payment_processed_by_novapay",
        "operator_reviews_analytics",
    ]
    assert "/v1/operator/dashboard" in payload["api_alignment"]["implemented"]
    assert payload["api_alignment"]["contract"] == "/v1/novaride/operator/dashboard-contract"
    assert "/v1/operator/demand-forecast" in payload["api_alignment"]["implemented"]
    assert "/v1/operator/strategy-engine" in payload["api_alignment"]["implemented"]
    assert "/v1/operator/city-profit-optimization" in payload["api_alignment"]["implemented"]


def test_novaride_fleet_manager_contract_exposes_modules_rbac_and_payment_boundary() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/fleet/manager-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_fleet_manager_contract"
    assert payload["role"] == "FLEET_OWNER"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Fleet Management",
        "Driver Management",
        "Vehicle Management",
        "Maintenance & Compliance",
        "Financial Management",
        "Fleet Analytics",
    }
    assert payload["navigation"] == [
        "Dashboard",
        "Vehicles",
        "Drivers",
        "Maintenance",
        "Finance",
        "Reports",
    ]
    assert "manage_vehicles" in payload["rbac"]["allowed"]
    assert "direct_payment_provider_access" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["payments"] == "NovaPay_backend_only"
    assert payload["authority_model"]["trust_compliance"] == "Trust_Engine_required"
    assert payload["workflow"] == [
        "fleet_adds_vehicles",
        "fleet_registers_drivers",
        "fleet_assigns_drivers_to_vehicles",
        "drivers_go_online",
        "dispatch_assigns_rides",
        "trips_completed",
        "payments_processed_via_novapay",
        "fleet_receives_earnings",
        "drivers_get_payouts",
        "fleet_monitors_analytics",
    ]
    assert "/v1/afriride/fleet/summary" in payload["api_alignment"]["implemented"]
    assert "/v1/fleet/vehicles" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "earnings_and_payouts"


def test_novaride_business_portal_contract_exposes_client_rbac_billing_and_workflow() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/business/portal-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_business_portal_contract"
    assert payload["role"] == "CLIENT"
    assert payload["sub_roles"] == ["Admin", "Manager", "Employee"]
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Corporate Travel Management",
        "Employee Management",
        "Approval Workflow",
        "Business Wallet & Billing",
        "Pricing & Incentives",
        "Budget Allocation & Profit Optimization",
        "Department Budgets",
        "Reporting & Analytics",
    }
    assert payload["navigation"] == [
        "Dashboard",
        "Employees",
        "Bookings",
        "Approvals",
        "Finance",
        "Budgets",
        "Reports",
    ]
    assert "book_rides" in payload["rbac"]["allowed"]
    assert "direct_payment_execution" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["payments"] == "NovaPay_backend_only"
    assert payload["authority_model"]["approvals"] == "workflow_engine_required"
    assert payload["workflow"] == [
        "company_onboarded",
        "employees_added",
        "budgets_assigned",
        "employee_requests_ride",
        "approval_if_required",
        "ride_booked",
        "trip_completed",
        "novapay_processes_payment",
        "monthly_invoice_generated",
        "admin_reviews_reports",
    ]
    assert "/v1/novatech/organizations/{organization_id}/billing" in payload["api_alignment"]["implemented"]
    assert "/v1/novaride/phase3/business/pricing" in payload["api_alignment"]["implemented"]
    assert "/v1/novaride/phase3/business/incentives" in payload["api_alignment"]["implemented"]
    assert "/v1/novaride/phase4/business/budget-allocation" in payload["api_alignment"]["implemented"]
    assert "/v1/novaride/phase4/business/profit-optimization" in payload["api_alignment"]["implemented"]
    assert "/v1/business/approvals" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "billing_wallet_invoices"


def test_novaride_admin_contract_exposes_governance_rbac_and_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/admin/contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_admin_contract"
    assert payload["role"] == "ADMIN"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "User & Role Management",
        "Driver & Vehicle Approval",
        "Pricing & Service Configuration",
        "Geography & Service Zones",
        "Promotions & Campaigns",
        "Compliance & Audit",
        "System Health & Monitoring",
    }
    assert payload["navigation"] == [
        "Dashboard",
        "Users",
        "Drivers & Vehicles",
        "Pricing",
        "Zones",
        "Promotions",
        "Audit",
        "System",
    ]
    assert "ADMIN" in payload["rbac"]["managed_roles"]
    assert "configure_platform_rules" in payload["rbac"]["allowed"]
    assert "manual_payment_processing" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["payments"] == "NovaPay_policy_level_only"
    assert payload["authority_model"]["logs"] == "Audit_Engine_required"
    assert payload["workflow"] == [
        "driver_registers",
        "admin_reviews_documents",
        "admin_approves_driver_vehicle",
        "driver_becomes_active",
        "admin_configures_pricing",
        "admin_sets_surge_rules",
        "admin_defines_service_zones",
        "system_runs_rides_automatically",
        "novapay_processes_payments",
        "audit_logs_captured",
        "admin_monitors_system_health",
        "admin_reviews_alerts",
        "admin_adjusts_rules_if_needed",
    ]
    assert "/v1/afriride/rbac/catalog" in payload["api_alignment"]["implemented"]
    assert "/v1/admin/pricing" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "policy_level_control_only"


def test_novaride_inspector_app_contract_exposes_verifier_workflow_and_trust_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/inspector/app-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_inspector_app_contract"
    assert payload["role"] == "VERIFIER"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Inspection Workflow",
        "Driver Verification",
        "Vehicle Inspection",
        "Document Validation",
        "Photo & Evidence Capture",
        "Inspection Reports",
        "Compliance Status",
    }
    assert payload["navigation"] == ["Home", "Inspection", "Reports", "Profile"]
    status_types = {status["status"]: status["meaning"] for status in payload["status_types"]}
    assert status_types == {
        "compliant": "allowed_to_operate",
        "pending": "requires_review",
        "non_compliant": "suspended",
    }
    assert "perform_inspections" in payload["rbac"]["allowed"]
    assert "trust_engine_bypass" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["compliance"] == "Trust_Engine_final_authority"
    assert payload["authority_model"]["evidence"] == "Audit_Engine_replay_required"
    assert payload["workflow"] == [
        "inspector_logs_in",
        "selects_driver_vehicle",
        "starts_inspection",
        "completes_checklist",
        "captures_photos",
        "submits_report",
        "trust_engine_evaluates_compliance",
        "status_updated",
        "driver_approved_or_suspended",
    ]
    assert "/v1/operator/public-verification/status" in payload["api_alignment"]["implemented"]
    assert "/v1/inspector/inspections" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["trust_engine"] == "final_authority"


def test_novaride_support_contract_exposes_ticket_refund_and_replay_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/support/contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_support_contract"
    assert payload["role"] == "OPERATOR"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Customer Ticket Management",
        "Ride Lookup & Investigation",
        "Refund & Dispute Handling",
        "Driver & Passenger Assistance",
        "Escalation Management",
        "Audit & Replay Integration",
    }
    assert payload["navigation"] == ["Tickets", "Ride Lookup", "Refunds", "Escalations", "Reports"]
    assert payload["ticket_statuses"] == ["Open", "In Progress", "Resolved", "Closed"]
    escalation_levels = {level["level"]: level["meaning"] for level in payload["escalation_levels"]}
    assert escalation_levels == {
        "level_1": "standard_support",
        "level_2": "supervisor",
        "level_3": "critical_admin",
    }
    assert "request_refunds" in payload["rbac"]["allowed"]
    assert "direct_payment_execution" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["refund_execution"] == "NovaPay_backend_only"
    assert payload["authority_model"]["ride_evidence"] == "Audit_Engine_replay_required"
    assert payload["workflow"] == [
        "passenger_raises_issue",
        "ticket_created",
        "support_agent_reviews_ride",
        "replay_trip_data",
        "verify_fare_via_pricing_engine",
        "decide_refund_or_action",
        "novapay_processes_refund",
        "ticket_closed",
    ]
    assert "/v1/operator/replay-exceptions" in payload["api_alignment"]["implemented"]
    assert "/v1/support/tickets" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "processes_refunds"


def test_novaride_partner_portal_contract_exposes_b2b_workflow_and_backend_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/partner/portal-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_partner_portal_contract"
    assert payload["role"] == "PARTNER"
    assert payload["partner_types"] == [
        "airports",
        "hotels",
        "event_organizers",
        "corporations",
        "travel_agencies",
    ]
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Ride Booking & Widget Integration",
        "Guest Transport Management",
        "Bulk Ride Requests",
        "Partner Reporting",
        "Billing & Payments",
        "Partner Configuration",
    }
    assert payload["navigation"] == [
        "Dashboard",
        "Bookings",
        "Guests",
        "Tracking",
        "Reports",
        "Billing",
        "Settings",
    ]
    assert "book_guest_rides" in payload["rbac"]["allowed"]
    assert "direct_payment_processing" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["payments"] == "NovaPay_backend_only"
    assert payload["authority_model"]["dispatch"] == "Dispatch_Engine_required"
    assert payload["workflow"] == [
        "hotel_staff_logs_in",
        "books_ride_for_guest",
        "guest_receives_ride_details",
        "driver_picks_up_guest",
        "trip_completed",
        "novapay_charges_partner_account",
        "monthly_invoice_generated",
        "partner_reviews_reports",
    ]
    assert "/v1/partners/registry" in payload["api_alignment"]["implemented"]
    assert "/v1/partner/bookings" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "billing_and_payments"
