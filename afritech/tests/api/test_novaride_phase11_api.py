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


def _seed_phase11_store(store: PlatformStore, *, org_id: str) -> None:
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
    store.store_account(organization_id=org_id, user_id="verifier-1", role="VERIFIER")
    store.store_account(organization_id=org_id, user_id="observer-1", role="OBSERVER")
    store.store_account(organization_id=org_id, user_id="customer-1", role="CUSTOMER")
    store.store_account(organization_id=org_id, user_id="driver-1", role="DRIVER")
    store.store_account(organization_id=org_id, user_id="driver-2", role="DRIVER")

    store.store_subscription(
        organization_id=org_id,
        plan="enterprise",
        status="active",
        billing_cycle="monthly",
        seats=12,
    )

    store.store_trust_score(
        organization_id=org_id,
        trust_score=91,
        classification="stable",
        breakdown={"compliance": 94, "support": 89, "replay": 92},
        findings=["Audit chain stable", "Inspection evidence available", "Compliance review ready"],
    )
    store.store_dashboard_analytics_snapshot(
        organization_id=org_id,
        source="afriride_operator_dashboard",
        snapshot_type="compliance",
        trust_score=91,
        trust_health=90,
        replay_health_score=92,
        evidence_coverage=94,
        exception_pressure=2,
        alert_count=1,
        active_drivers=2,
        completed_rides=3,
        total_rides=4,
        guard_count=2,
        replay_failures=0,
        hash_chain_failures=0,
        missing_traces=0,
        receipts_count=3,
        trace_count=7,
        payload={"primary_zone": "CBD"},
    )

    store.store_driver_presence(
        organization_id=org_id,
        driver_id="driver-1",
        status="online",
        location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
        trust_score=96,
        metadata={"zone": "CBD"},
    )
    store.store_driver_presence(
        organization_id=org_id,
        driver_id="driver-2",
        status="online",
        location={"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
        trust_score=84,
        metadata={"zone": "Docklands"},
    )

    store.store_ride(
        ride_id="ride-1",
        organization_id=org_id,
        passenger_id="customer-1",
        driver_id="driver-1",
        pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
        destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
        fare_estimate="25.00",
        currency="AUD",
        status="completed",
        final_fare="25.00",
    )
    store.store_ride(
        ride_id="ride-2",
        organization_id=org_id,
        passenger_id="customer-1",
        driver_id="driver-2",
        pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
        destination_location={"lat": -37.8300, "lng": 144.9400, "label": "Airport"},
        fare_estimate="30.00",
        currency="AUD",
        status="completed",
        final_fare="35.00",
    )
    store.store_ride(
        ride_id="ride-3",
        organization_id=org_id,
        passenger_id="customer-1",
        driver_id="driver-2",
        pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
        destination_location={"lat": -37.8000, "lng": 144.9600, "label": "Southbank"},
        fare_estimate="18.00",
        currency="AUD",
        status="cancelled",
    )
    store.store_ride(
        ride_id="ride-4",
        organization_id=org_id,
        passenger_id="customer-1",
        driver_id="driver-1",
        pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
        destination_location={"lat": -37.8250, "lng": 144.9480, "label": "St Kilda"},
        fare_estimate="40.00",
        currency="AUD",
        status="completed",
        final_fare="40.00",
    )

    store.store_dispatch_assignment(
        organization_id=org_id,
        ride_id="ride-1",
        driver_id="driver-1",
        status="accepted",
        decision={"source": "phase11-test", "support": True},
    )
    store.store_dispatch_assignment(
        organization_id=org_id,
        ride_id="ride-2",
        driver_id="driver-2",
        status="accepted",
        decision={"source": "phase11-test", "support": True},
    )
    store.store_dispatch_assignment(
        organization_id=org_id,
        ride_id="ride-3",
        driver_id="driver-2",
        status="cancelled",
        decision={"source": "phase11-test", "support": True},
    )
    store.store_dispatch_assignment(
        organization_id=org_id,
        ride_id="ride-4",
        driver_id="driver-1",
        status="accepted",
        decision={"source": "phase11-test", "support": True},
    )

    store.store_transaction(
        organization_id=org_id,
        ride_id="ride-1",
        user_id="customer-1",
        counterparty_user_id="driver-1",
        amount="25.00",
        currency="AUD",
        transaction_type="debit",
    )
    store.store_transaction(
        organization_id=org_id,
        ride_id="ride-1",
        user_id="driver-1",
        counterparty_user_id="customer-1",
        amount="25.00",
        currency="AUD",
        transaction_type="credit",
    )
    store.store_transaction(
        organization_id=org_id,
        ride_id="ride-2",
        user_id="customer-1",
        counterparty_user_id="driver-2",
        amount="35.00",
        currency="AUD",
        transaction_type="debit",
    )
    store.store_transaction(
        organization_id=org_id,
        ride_id="ride-2",
        user_id="driver-2",
        counterparty_user_id="customer-1",
        amount="35.00",
        currency="AUD",
        transaction_type="credit",
    )
    store.store_transaction(
        organization_id=org_id,
        ride_id="ride-3",
        user_id="customer-1",
        counterparty_user_id="driver-2",
        amount="18.00",
        currency="AUD",
        transaction_type="debit",
    )
    store.store_transaction(
        organization_id=org_id,
        ride_id="ride-4",
        user_id="customer-1",
        counterparty_user_id="driver-1",
        amount="40.00",
        currency="AUD",
        transaction_type="debit",
    )
    store.store_transaction(
        organization_id=org_id,
        ride_id="ride-4",
        user_id="driver-1",
        counterparty_user_id="customer-1",
        amount="40.00",
        currency="AUD",
        transaction_type="credit",
    )

    events = [
        ("support_ticket_created", "ticket-1", "open", {"ticket_id": "ticket-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
        ("support_ticket_assigned", "ticket-1", "in_progress", {"ticket_id": "ticket-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
        ("support_ticket_resolved", "ticket-1", "resolved", {"ticket_id": "ticket-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
        ("support_ticket_closed", "ticket-1", "closed", {"ticket_id": "ticket-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
        ("refund_requested", "refund-1", "open", {"refund_id": "refund-1", "ticket_id": "ticket-1", "ride_id": "ride-3", "amount": "18.00", "currency": "AUD", "category": "cancellation"}),
        ("refund_approved", "refund-1", "approved", {"refund_id": "refund-1", "ticket_id": "ticket-1", "ride_id": "ride-3", "amount": "18.00", "currency": "AUD", "category": "cancellation"}),
        ("dispute_opened", "dispute-1", "open", {"dispute_id": "dispute-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
        ("dispute_resolved", "dispute-1", "resolved", {"dispute_id": "dispute-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}),
        ("inspection_started", "inspection-1", "pending", {"inspection_id": "inspection-1", "driver_id": "driver-1", "vehicle_id": "vehicle-1", "category": "vehicle_inspection"}),
        ("document_verified", "doc-1", "verified", {"document_id": "doc-1", "driver_id": "driver-1", "document_type": "license", "category": "document_verification"}),
        ("inspection_report_submitted", "report-1", "approved", {"report_id": "report-1", "inspection_id": "inspection-1", "driver_id": "driver-1", "vehicle_id": "vehicle-1", "category": "inspection_report"}),
        ("inspection_approved", "inspection-1", "approved", {"inspection_id": "inspection-1", "driver_id": "driver-1", "vehicle_id": "vehicle-1", "category": "vehicle_inspection"}),
        ("fraud_flagged", "fraud-1", "watch", {"fraud_id": "fraud-1", "ride_id": "ride-2", "category": "overcharge_pattern", "severity": "medium"}),
    ]

    for event_type, target, status, payload in events:
        store.record_audit_event(
            organization_id=org_id,
            event_type=event_type,
            actor_user_id="operator-1",
            actor_role="OPERATOR" if "inspection" not in event_type and "document" not in event_type else "VERIFIER",
            target=target,
            status=status,
            payload=payload,
        )


def test_phase11_compliance_and_inspection_system_is_tenant_scoped_and_ready(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase11.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase11-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        verifier_token = _issue_token(client, role="VERIFIER", organization_id=org_id, user_id="verifier-1")
        other_token = _issue_token(client, role="OPERATOR", organization_id="org-phase11-999", user_id="operator-9")

        _seed_phase11_store(control_plane._STORE, org_id=org_id)

        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        verifier_headers = {"Authorization": f"Bearer {verifier_token}"}
        other_headers = {"Authorization": f"Bearer {other_token}"}

        status_response = client.get("/v1/novaride/phase11/status", headers=operator_headers)
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["view"] == "novaride_phase11_status"
        assert status["ready"] is True
        assert status["support_dashboard"]["ticket_total"] >= 1
        assert status["support_dashboard"]["driver_average_score"] >= 0
        assert status["support_dashboard"]["regulatory_readiness_band"] in {"government_review_ready", "controlled_review", "watch"}
        assert status["compliance_workspace"]["ticket_classification"]["auto_classification_ready"] is True
        assert status["compliance_workspace"]["inspections"]["inspection_total"] >= 1
        assert status["compliance_workspace"]["documents"]["verified_count"] >= 1
        assert status["compliance_workspace"]["inspection_reports"]["report_total"] >= 1
        assert status["compliance_workspace"]["driver_scoring"]["driver_total"] >= 2
        assert status["compliance_workspace"]["fraud_detection"]["risk_band"] in {"low", "watch"}
        assert status["compliance_workspace"]["smart_refunds"]["refund_total"] >= 1
        assert status["compliance_workspace"]["regulatory_readiness"]["regulatory_ready"] is True
        assert status["support_dashboard"]["dashboard_cards"][0]["label"] == "Support Dashboard UI"

        support_response = client.get(
            "/v1/novaride/phase11/support-dashboard",
            headers=operator_headers,
            params={"organization_id": org_id},
        )
        assert support_response.status_code == 200
        support_dashboard = support_response.json()
        assert support_dashboard["view"] == "novaride_phase11_support_dashboard"
        assert support_dashboard["driver_average_score"] >= 0
        assert support_dashboard["smart_refund_mode"] in {"safe_suggest", "review_required"}

        verifier_response = client.get(
            "/v1/novaride/phase11/compliance-workspace",
            headers=verifier_headers,
            params={"organization_id": org_id},
        )
        assert verifier_response.status_code == 200
        workspace = verifier_response.json()
        assert workspace["view"] == "novaride_phase11_compliance_workspace"
        assert workspace["inspections"]["inspection_band"] in {"compliant", "watch"}
        assert workspace["documents"]["verification_band"] in {"verified", "watch"}

        driver_scoring_response = client.get(
            "/v1/novaride/phase11/driver-scoring",
            headers=operator_headers,
            params={"organization_id": org_id},
        )
        assert driver_scoring_response.status_code == 200
        driver_scoring = driver_scoring_response.json()
        assert driver_scoring["driver_total"] >= 2
        assert driver_scoring["driver_scores"][0]["score"] >= driver_scoring["driver_scores"][-1]["score"]

        fraud_response = client.get(
            "/v1/novaride/phase11/fraud-detection",
            headers=operator_headers,
            params={"organization_id": org_id},
        )
        assert fraud_response.status_code == 200
        fraud = fraud_response.json()
        assert fraud["fraud_signal_count"] >= 1
        assert fraud["risk_band"] in {"low", "watch"}

        cross_tenant = client.get(
            "/v1/novaride/phase11/support-dashboard",
            headers=other_headers,
            params={"organization_id": org_id},
        )
        assert cross_tenant.status_code == 403
    finally:
        control_plane._STORE = original_store
