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


def test_phase10_support_dispute_system_is_tenant_scoped_and_support_ready(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase10.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase10-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        admin_token = _issue_token(client, role="ADMIN", organization_id=org_id, user_id="admin-1")
        observer_token = _issue_token(client, role="OBSERVER", organization_id=org_id, user_id="observer-1")

        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        observer_headers = {"Authorization": f"Bearer {observer_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 10 Support Mobility Pty Ltd",
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
                "seats": 8,
            },
        )
        assert subscription.status_code == 200

        store = control_plane._STORE
        store.upsert_organization_profile(
            organization_id=org_id,
            organization_type="internal",
            status="active",
            default_plan="enterprise",
            owner_user_id="operator-1",
            owner_role="OPERATOR",
        )
        store.store_account(organization_id=org_id, user_id="operator-1", role="OPERATOR")
        store.store_account(organization_id=org_id, user_id="admin-1", role="ADMIN")
        store.store_account(organization_id=org_id, user_id="customer-1", role="CUSTOMER")
        store.store_account(organization_id=org_id, user_id="driver-1", role="DRIVER")

        store.store_trust_score(
            organization_id=org_id,
            trust_score=95,
            classification="stable",
            breakdown={"support": 96, "billing": 94, "replay": 95},
            findings=["Support evidence available", "Audit chain stable"],
        )
        store.store_dashboard_analytics_snapshot(
            organization_id=org_id,
            source="afriride_operator_dashboard",
            snapshot_type="support",
            trust_score=95,
            trust_health=94,
            replay_health_score=96,
            evidence_coverage=93,
            exception_pressure=2,
            alert_count=1,
            active_drivers=1,
            completed_rides=2,
            total_rides=3,
            guard_count=2,
            replay_failures=0,
            hash_chain_failures=0,
            missing_traces=0,
            receipts_count=2,
            trace_count=6,
            payload={"primary_zone": "CBD"},
        )
        store.store_billing_record(
            organization_id=org_id,
            plan="enterprise",
            usage_total=44,
            estimated_amount=9.8,
            billing_enabled=True,
        )
        store.store_driver_presence(
            organization_id=org_id,
            driver_id="driver-1",
            status="online",
            location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            trust_score=97,
            metadata={"zone": "CBD"},
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
            passenger_id="customer-1",
            driver_id="driver-1",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Airport"},
            fare_estimate="25.00",
            currency="AUD",
            status="completed",
            final_fare="35.00",
        )
        store.store_ride(
            ride_id="ride-3",
            organization_id=org_id,
            passenger_id="customer-1",
            driver_id="driver-1",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            destination_location={"lat": -37.8000, "lng": 144.9600, "label": "Southbank"},
            fare_estimate="18.00",
            currency="AUD",
            status="cancelled",
        )

        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-1",
            driver_id="driver-1",
            status="accepted",
            decision={"source": "phase10-test", "support": True},
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-2",
            driver_id="driver-1",
            status="accepted",
            decision={"source": "phase10-test", "support": True},
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-3",
            driver_id="driver-1",
            status="cancelled",
            decision={"source": "phase10-test", "support": True},
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
            ride_id="ride-2",
            user_id="customer-1",
            counterparty_user_id="driver-1",
            amount="35.00",
            currency="AUD",
            transaction_type="debit",
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-2",
            user_id="driver-1",
            counterparty_user_id="customer-1",
            amount="35.00",
            currency="AUD",
            transaction_type="credit",
        )

        support_event_specs = [
            ("support_ticket_created", "ticket-1", "open", {"ticket_id": "ticket-1", "ride_id": "ride-1", "category": "ride_issue", "priority": "medium"}),
            ("support_ticket_assigned", "ticket-1", "in_progress", {"ticket_id": "ticket-1", "ride_id": "ride-1", "category": "ride_issue", "priority": "medium"}),
            ("support_ticket_resolved", "ticket-1", "resolved", {"ticket_id": "ticket-1", "ride_id": "ride-1", "category": "ride_issue", "priority": "medium"}),
            ("support_ticket_closed", "ticket-1", "closed", {"ticket_id": "ticket-1", "ride_id": "ride-1", "category": "ride_issue", "priority": "medium"}),
            ("support_ticket_created", "ticket-2", "open", {"ticket_id": "ticket-2", "ride_id": "ride-2", "category": "payment_issue", "priority": "high"}),
            ("support_ticket_assigned", "ticket-2", "in_progress", {"ticket_id": "ticket-2", "ride_id": "ride-2", "category": "payment_issue", "priority": "high"}),
            ("support_ticket_created", "ticket-3", "open", {"ticket_id": "ticket-3", "ride_id": "ride-3", "category": "lost_and_found", "priority": "low"}),
            ("support_ticket_created", "ticket-4", "open", {"ticket_id": "ticket-4", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
            ("support_ticket_assigned", "ticket-4", "in_progress", {"ticket_id": "ticket-4", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
            ("support_ticket_resolved", "ticket-4", "resolved", {"ticket_id": "ticket-4", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
            ("refund_requested", "refund-1", "open", {"refund_id": "refund-1", "ticket_id": "ticket-2", "ride_id": "ride-2", "amount": "10.00", "currency": "AUD", "category": "fare_adjustment"}),
            ("refund_approved", "refund-1", "approved", {"refund_id": "refund-1", "ticket_id": "ticket-2", "ride_id": "ride-2", "amount": "10.00", "currency": "AUD", "category": "fare_adjustment"}),
            ("refund_requested", "refund-2", "open", {"refund_id": "refund-2", "ticket_id": "ticket-3", "ride_id": "ride-3", "amount": "18.00", "currency": "AUD", "category": "cancellation"}),
            ("refund_rejected", "refund-2", "rejected", {"refund_id": "refund-2", "ticket_id": "ticket-3", "ride_id": "ride-3", "amount": "18.00", "currency": "AUD", "category": "cancellation"}),
            ("dispute_opened", "dispute-1", "open", {"dispute_id": "dispute-1", "ride_id": "ride-2", "reason": "fare_variance"}),
            ("dispute_resolved", "dispute-1", "resolved", {"dispute_id": "dispute-1", "ride_id": "ride-2", "reason": "fare_variance"}),
            ("support_escalated", "escalation-1", "level_2", {"escalation_id": "escalation-1", "ticket_id": "ticket-2", "escalation_level": "level_2", "reason": "payment_issue"}),
            ("ride_investigation_opened", "investigation-1", "in_progress", {"investigation_id": "investigation-1", "ride_id": "ride-2", "reason": "fare_variance"}),
        ]
        for event_type, target, status, payload in support_event_specs:
            store.record_audit_event(
                organization_id=org_id,
                event_type=event_type,
                actor_user_id="operator-1",
                actor_role="OPERATOR",
                target=target,
                status=status,
                payload=payload,
            )

        status_response = client.get("/v1/novaride/phase10/status", headers=operator_headers, params={"limit": 50})
        assert status_response.status_code == 200
        status_payload = status_response.json()
        assert status_payload["view"] == "novaride_phase10_status"
        assert status_payload["ready"] is True
        assert status_payload["readiness"]["subscription_active"] is True
        assert status_payload["readiness"]["replay_evidence_ready"] is True

        contract_response = client.get("/v1/novaride/phase10/support-contract", headers=observer_headers)
        assert contract_response.status_code == 200
        contract_payload = contract_response.json()
        assert contract_payload["view"] == "novaride_phase10_support_contract"
        assert contract_payload["rbac"]["role"] == "OPERATOR"
        assert "request_refunds" in contract_payload["rbac"]["allowed"]

        workspace_response = client.get("/v1/novaride/phase10/support-workspace", headers=operator_headers, params={"limit": 50})
        assert workspace_response.status_code == 200
        workspace_payload = workspace_response.json()
        assert workspace_payload["view"] == "novaride_phase10_support_workspace"
        assert workspace_payload["summary"]["ticket_total"] == 4
        assert workspace_payload["tickets"]["ticket_status_counts"]["open"] == 1
        assert workspace_payload["tickets"]["ticket_status_counts"]["in_progress"] == 1
        assert workspace_payload["tickets"]["ticket_status_counts"]["resolved"] == 1
        assert workspace_payload["tickets"]["ticket_status_counts"]["closed"] == 1
        assert workspace_payload["refunds"]["refund_authority"] == "NovaPay_backend_only"
        assert workspace_payload["refunds"]["approved_refund_count"] == 1
        assert workspace_payload["refunds"]["rejected_refund_count"] == 1
        assert workspace_payload["disputes"]["audit_chain_verified"] is True
        assert workspace_payload["ride_lookup"]["ride_total"] == 3
        assert workspace_payload["escalations"]["queue_by_level"]["level_2"] == 1
        assert workspace_payload["replay_evidence"]["audit_chain_verified"] is True
        assert workspace_payload["customer_experience"]["experience_band"] in {"stable", "excellent"}

        tickets_response = client.get("/v1/novaride/phase10/tickets", headers=admin_headers, params={"limit": 50})
        assert tickets_response.status_code == 200
        tickets_payload = tickets_response.json()
        assert tickets_payload["ticket_total"] == 4

        refunds_response = client.get("/v1/novaride/phase10/refunds", headers=operator_headers, params={"limit": 50})
        assert refunds_response.status_code == 200
        refunds_payload = refunds_response.json()
        assert refunds_payload["suggested_refund_total"] == "10.00"

        disputes_response = client.get("/v1/novaride/phase10/disputes", headers=operator_headers, params={"limit": 50})
        assert disputes_response.status_code == 200
        disputes_payload = disputes_response.json()
        assert disputes_payload["dispute_total"] == 1
        assert disputes_payload["resolution_band"] == "verified"

        ride_lookup_response = client.get("/v1/novaride/phase10/ride-lookup", headers=operator_headers, params={"limit": 50})
        assert ride_lookup_response.status_code == 200
        ride_lookup_payload = ride_lookup_response.json()
        assert ride_lookup_payload["ride_total"] == 3
        assert ride_lookup_payload["evidence_ready_count"] == 3

        escalations_response = client.get("/v1/novaride/phase10/escalations", headers=operator_headers, params={"limit": 50})
        assert escalations_response.status_code == 200
        escalations_payload = escalations_response.json()
        assert escalations_payload["escalation_total"] == 1

        replay_response = client.get("/v1/novaride/phase10/replay-evidence", headers=operator_headers, params={"limit": 50})
        assert replay_response.status_code == 200
        replay_payload = replay_response.json()
        assert replay_payload["audit_chain_verified"] is True
        assert replay_payload["evidence_ready"] is True

        experience_response = client.get("/v1/novaride/phase10/customer-experience", headers=operator_headers, params={"limit": 50})
        assert experience_response.status_code == 200
        experience_payload = experience_response.json()
        assert experience_payload["experience_band"] in {"stable", "excellent"}

        forbidden = client.get(
            "/v1/novaride/phase10/support-workspace",
            headers=operator_headers,
            params={"organization_id": "org-phase10-foreign"},
        )
        assert forbidden.status_code == 403
    finally:
        control_plane._STORE = original_store
