from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore
from afritech.api.app import app


def _issue_token(client: TestClient, *, role: str, organization_id: str, user_id: str) -> str:
    response = client.post(
        "/v1/auth/token",
        json={
            "user_id": user_id,
            "role": role,
            "organization_id": organization_id,
        },
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_phase8_business_fleet_systems_are_tenant_scoped_and_enterprise_ready(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase8.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase8-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        admin_token = _issue_token(client, role="ADMIN", organization_id=org_id, user_id="admin-1")
        client_token = _issue_token(client, role="CLIENT", organization_id=org_id, user_id="client-1")
        customer_token = _issue_token(client, role="CUSTOMER", organization_id=org_id, user_id="customer-1")
        driver_1_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-1")
        driver_2_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-2")

        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        client_headers = {"Authorization": f"Bearer {client_token}"}
        customer_headers = {"Authorization": f"Bearer {customer_token}"}
        driver_1_headers = {"Authorization": f"Bearer {driver_1_token}"}
        driver_2_headers = {"Authorization": f"Bearer {driver_2_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 8 Fleet & Business Mobility Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200

        subscription = client.post(
            "/v1/novatech/phase0/subscriptions",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "plan": "enterprise",
                "status": "active",
                "billing_cycle": "monthly",
                "seats": 12,
            },
        )
        assert subscription.status_code == 200

        store = control_plane._STORE
        store.store_account(
            organization_id=org_id,
            user_id="admin-1",
            role="ADMIN",
        )
        store.store_account(
            organization_id=org_id,
            user_id="client-1",
            role="CLIENT",
        )
        store.store_account(
            organization_id=org_id,
            user_id="customer-1",
            role="CUSTOMER",
        )
        store.store_account(
            organization_id=org_id,
            user_id="driver-1",
            role="DRIVER",
        )
        store.store_account(
            organization_id=org_id,
            user_id="driver-2",
            role="DRIVER",
        )

        store.store_trust_score(
            organization_id=org_id,
            trust_score=96,
            classification="stable",
            breakdown={"routing": 97, "safety": 95, "billing": 94},
            findings=["Enterprise tenant stable", "Billing verified"],
        )
        store.store_dashboard_analytics_snapshot(
            organization_id=org_id,
            source="afriride_operator_dashboard",
            snapshot_type="business_fleet",
            trust_score=96,
            trust_health=95,
            replay_health_score=94,
            evidence_coverage=93,
            exception_pressure=3,
            alert_count=1,
            active_drivers=2,
            completed_rides=4,
            total_rides=8,
            guard_count=2,
            replay_failures=0,
            hash_chain_failures=0,
            missing_traces=0,
            receipts_count=4,
            trace_count=8,
            payload={"primary_zone": "CBD"},
        )
        store.track_usage(
            organization_id=org_id,
            metric="business_portal_action",
            amount=60,
            context={"surface": "fleet", "action": "monthly_billing"},
        )
        store.track_usage(
            organization_id=org_id,
            metric="business_portal_action",
            amount=40,
            context={"surface": "business", "action": "employee_booking"},
        )
        store.store_billing_record(
            organization_id=org_id,
            plan="enterprise",
            usage_total=100,
            estimated_amount=11.7,
            billing_enabled=True,
        )
        store.store_driver_presence(
            organization_id=org_id,
            driver_id="driver-1",
            status="online",
            location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            trust_score=98,
            metadata={"zone": "CBD"},
        )
        store.store_driver_presence(
            organization_id=org_id,
            driver_id="driver-2",
            status="busy",
            location={"lat": -37.8150, "lng": 144.9700, "label": "Southbank"},
            busy_ride_id="ride-4",
            trust_score=91,
            metadata={"zone": "Southbank"},
        )
        store.store_ride(
            ride_id="ride-1",
            organization_id=org_id,
            passenger_id="customer-1",
            driver_id="driver-1",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
            fare_estimate="42.00",
            currency="AUD",
            status="completed",
            final_fare="42.00",
        )
        store.store_ride(
            ride_id="ride-2",
            organization_id=org_id,
            passenger_id="client-1",
            driver_id="driver-1",
            pickup_location={"lat": -37.8150, "lng": 144.9700, "label": "Southbank"},
            destination_location={"lat": -37.8000, "lng": 144.9600, "label": "Richmond"},
            fare_estimate="30.00",
            currency="AUD",
            status="cancelled",
        )
        store.store_ride(
            ride_id="ride-3",
            organization_id=org_id,
            passenger_id="customer-1",
            driver_id="driver-2",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            destination_location={"lat": -37.8100, "lng": 144.9800, "label": "Carlton"},
            fare_estimate="25.00",
            currency="AUD",
            status="completed",
            final_fare="35.00",
        )
        store.store_ride(
            ride_id="ride-4",
            organization_id=org_id,
            passenger_id="client-1",
            driver_id="driver-2",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
            fare_estimate="18.00",
            currency="AUD",
            status="requested",
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-1",
            driver_id="driver-1",
            status="accepted",
            decision={"source": "phase8-test", "driver_id": "driver-1"},
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-2",
            driver_id="driver-1",
            status="accepted",
            decision={"source": "phase8-test", "driver_id": "driver-1"},
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-3",
            driver_id="driver-2",
            status="accepted",
            decision={"source": "phase8-test", "driver_id": "driver-2"},
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-4",
            driver_id="driver-2",
            status="assigned",
            decision={"source": "phase8-test", "driver_id": "driver-2"},
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-1",
            user_id="customer-1",
            counterparty_user_id="driver-1",
            amount="42.00",
            currency="AUD",
            transaction_type="debit",
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-1",
            user_id="driver-1",
            counterparty_user_id="customer-1",
            amount="42.00",
            currency="AUD",
            transaction_type="credit",
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-3",
            user_id="customer-1",
            counterparty_user_id="driver-2",
            amount="35.00",
            currency="AUD",
            transaction_type="debit",
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-3",
            user_id="driver-2",
            counterparty_user_id="customer-1",
            amount="35.00",
            currency="AUD",
            transaction_type="credit",
        )
        decision = store.store_ai_decision_snapshot(
            organization_id=org_id,
            source="afriride_operator_dashboard",
            decision_type="operator_decision",
            decision_lane="dispatch",
            decision_action="rebalance_supply",
            decision_priority="high",
            decision_summary="Shift supply toward CBD",
            trust_score=96,
            trust_health=95,
            replay_health_score=94,
            evidence_coverage=93,
            exception_pressure=3,
            alert_count=1,
            guard_count=2,
            replay_failures=0,
            hash_chain_failures=0,
            missing_traces=0,
            risk_score=14,
            risk_level="low",
            confidence=0.94,
            stability_index=92,
            recommended_actions=["Hold supply around CBD", "Monitor cancellations"],
            watch_items=["Track demand"],
            payload={"zone": "CBD"},
        )
        action = store.store_ai_action_snapshot(
            organization_id=org_id,
            source="afriride_operator_dashboard",
            action_type="controlled_autonomous_action",
            decision_id=decision["decision_id"],
            decision_lane="dispatch",
            action_lane="dispatch",
            action_mode="supervised",
            action_priority="high",
            action_summary="Supervised dispatch recommendation",
            control_signal="maintain_coverage",
            safety_gate="pass",
            automation_tier=2,
            decision_quality_score=89,
            evidence_alignment_score=90,
            calibrated_confidence=0.91,
            history_alignment_score=88,
            quality_band="strong",
            trust_score=96,
            trust_health=95,
            replay_health_score=94,
            evidence_coverage=93,
            exception_pressure=3,
            alert_count=1,
            guard_count=2,
            replay_failures=0,
            hash_chain_failures=0,
            missing_traces=0,
            stability_index=92,
            recommended_actions=["Keep supervised autonomy", "Continue calibration"],
            watch_items=["Monitor churn"],
            payload={"action": {"execution_tier": "supervised", "execution_tier_ready": True}},
        )
        store.store_outcome_snapshot(
            organization_id=org_id,
            source="afriride_operator_dashboard",
            outcome_type="measured_outcome",
            decision_id=decision["decision_id"],
            action_id=action["action_id"],
            outcome_status="verified",
            outcome_band="strong",
            learning_band="learning",
            outcome_score=88,
            trust_score=96,
            trust_health=95,
            replay_health_score=94,
            evidence_coverage=93,
            exception_pressure=3,
            decision_quality_score=89,
            evidence_alignment_score=90,
            calibrated_confidence=0.91,
            history_alignment_score=88,
            execution_tier="supervised",
            execution_tier_ready=True,
            measurement_summary="Learning loop confirms stable operating band.",
            learning_actions=["Preserve the current control band."],
            recalibration_notes=["Continue monitoring cancellation pressure."],
            watch_items=["Track demand", "Monitor churn"],
            payload={"outcome": "stable"},
        )

        status = client.get("/v1/novaride/phase8/status", headers=operator_headers, params={"limit": 50})
        assert status.status_code == 200
        status_payload = status.json()
        assert status_payload["view"] == "novaride_phase8_status"
        assert status_payload["ready"] is True
        assert status_payload["readiness"]["tenant_isolation_preserved"] is True
        assert status_payload["readiness"]["fleet_summary_ready"] is True
        assert status_payload["readiness"]["corporate_accounts_ready"] is True
        assert status_payload["readiness"]["employee_booking_ready"] is True
        assert status_payload["readiness"]["invoicing_ready"] is True
        assert status_payload["readiness"]["budgeting_ready"] is True
        assert status_payload["readiness"]["monthly_billing_ready"] is True
        assert status_payload["readiness"]["adaptive_markets_ready"] is True
        assert status_payload["readiness"]["policy_enforcement_ready"] is True
        assert status_payload["readiness"]["enterprise_revenue_ready"] is True

        business_fleet = client.get(
            "/v1/novaride/phase8/business-fleet",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert business_fleet.status_code == 200
        business_fleet_payload = business_fleet.json()
        assert business_fleet_payload["view"] == "novaride_phase8_business_fleet_systems"
        assert business_fleet_payload["fleet_summary"]["vehicle_count"] == 2
        assert business_fleet_payload["fleet_summary"]["active_driver_count"] == 2
        assert business_fleet_payload["fleet_summary"]["driver_utilization_rate"] == 0.5
        assert business_fleet_payload["corporate_accounts"]["business_account_count"] == 2
        assert business_fleet_payload["employee_booking"]["employee_count"] == 2
        assert business_fleet_payload["monthly_billing"]["billing_cycle"] == "monthly"
        assert business_fleet_payload["policy_enforcement"]["tenant_isolation_preserved"] is True
        assert business_fleet_payload["real_execution"]["mode"] in {"adaptive", "supervised", "projection_only", "watch"}

        corporate_accounts = client.get(
            "/v1/novaride/phase8/corporate-accounts",
            headers=admin_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert corporate_accounts.status_code == 200
        corporate_accounts_payload = corporate_accounts.json()
        assert corporate_accounts_payload["view"] == "novaride_phase8_corporate_accounts"
        assert corporate_accounts_payload["business_account_count"] == 2
        assert corporate_accounts_payload["employee_account_count"] == 2
        assert corporate_accounts_payload["organization_count"] == 1

        employee_booking = client.get(
            "/v1/novaride/phase8/employee-booking",
            headers=client_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert employee_booking.status_code == 200
        employee_booking_payload = employee_booking.json()
        assert employee_booking_payload["view"] == "novaride_phase8_employee_booking"
        assert employee_booking_payload["ride_count"] == 4
        assert employee_booking_payload["scheduled_ride_count"] == 1
        assert employee_booking_payload["completed_ride_count"] == 2
        assert employee_booking_payload["cancelled_ride_count"] == 1
        assert employee_booking_payload["policy_status"] == "within_budget"

        invoicing = client.get(
            "/v1/novaride/phase8/invoicing",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert invoicing.status_code == 200
        invoicing_payload = invoicing.json()
        assert invoicing_payload["view"] == "novaride_phase8_invoicing"
        assert invoicing_payload["invoice_status"] == "open"
        assert invoicing_payload["billing_records"]
        assert float(invoicing_payload["estimated_monthly_invoice"]) > 11.0

        budgeting = client.get(
            "/v1/novaride/phase8/budgeting",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert budgeting.status_code == 200
        budgeting_payload = budgeting.json()
        assert budgeting_payload["view"] == "novaride_phase8_budgeting"
        assert budgeting_payload["budget_policy"]["tenant_scoped"] is True
        assert budgeting_payload["budget_policy"]["subscription_guarded"] is True

        monthly_billing = client.get(
            "/v1/novaride/phase8/monthly-billing",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert monthly_billing.status_code == 200
        monthly_billing_payload = monthly_billing.json()
        assert monthly_billing_payload["view"] == "novaride_phase8_monthly_billing"
        assert monthly_billing_payload["billing_cycle"] == "monthly"
        assert monthly_billing_payload["invoice_status"] == "open"

        adaptive_markets = client.get(
            "/v1/novaride/phase8/adaptive-markets",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert adaptive_markets.status_code == 200
        adaptive_markets_payload = adaptive_markets.json()
        assert adaptive_markets_payload["view"] == "novaride_phase8_adaptive_markets"
        assert adaptive_markets_payload["policy_enforcement"]["tenant_isolation_preserved"] is True
        assert adaptive_markets_payload["execution_mode"] in {
            "gradual_real_execution",
            "policy_enforced_supervision",
            "projection_only",
        }

        enterprise_revenue = client.get(
            "/v1/novaride/phase8/enterprise-revenue",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert enterprise_revenue.status_code == 200
        enterprise_revenue_payload = enterprise_revenue.json()
        assert enterprise_revenue_payload["view"] == "novaride_phase8_enterprise_revenue"
        assert enterprise_revenue_payload["enterprise_revenue_streams"]
        assert enterprise_revenue_payload["monthly_billing"]["billing_cycle"] == "monthly"
        assert enterprise_revenue_payload["invoicing"]["invoice_status"] == "open"
        assert enterprise_revenue_payload["real_execution"]["policy_enforcement"]["tenant_isolation_preserved"] is True
        assert enterprise_revenue_payload["real_execution"]["mode"] in {"adaptive", "supervised", "projection_only", "watch"}
        assert float(enterprise_revenue_payload["monthly_billing"]["monthly_billed_total"]) > 0

        forbidden = client.get(
            "/v1/novaride/phase8/business-fleet",
            headers=operator_headers,
            params={"organization_id": "spoofed-org", "limit": 50},
        )
        assert forbidden.status_code == 403
        assert "organization_isolation_violation" in forbidden.text
    finally:
        control_plane._STORE = original_store
