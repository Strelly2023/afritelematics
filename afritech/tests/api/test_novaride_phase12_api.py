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


def _seed_phase12_store(store: PlatformStore, *, org_id: str) -> None:
    store.upsert_organization_profile(
        organization_id=org_id,
        organization_type="internal",
        status="active",
        default_plan="enterprise",
        owner_user_id="operator-1",
        owner_role="OPERATOR",
    )
    for user_id, role in (
        ("operator-1", "OPERATOR"),
        ("admin-1", "ADMIN"),
        ("verifier-1", "VERIFIER"),
        ("observer-1", "OBSERVER"),
        ("customer-1", "CUSTOMER"),
        ("driver-1", "DRIVER"),
        ("driver-2", "DRIVER"),
    ):
        store.store_account(organization_id=org_id, user_id=user_id, role=role)

    store.store_subscription(
        organization_id=org_id,
        plan="enterprise",
        status="active",
        billing_cycle="monthly",
        seats=12,
    )
    store.store_trust_score(
        organization_id=org_id,
        trust_score=96,
        classification="stable",
        breakdown={"support": 96, "compliance": 95, "replay": 97},
        findings=["Global scaling ready", "Multi-city evidence available"],
    )
    store.store_dashboard_analytics_snapshot(
        organization_id=org_id,
        source="afriride_operator_dashboard",
        snapshot_type="global_scale",
        trust_score=96,
        trust_health=95,
        replay_health_score=96,
        evidence_coverage=94,
        exception_pressure=2,
        alert_count=1,
        active_drivers=2,
        completed_rides=4,
        total_rides=5,
        guard_count=2,
        replay_failures=0,
        hash_chain_failures=0,
        missing_traces=0,
        receipts_count=4,
        trace_count=9,
        payload={
            "primary_zone": "Melbourne CBD",
            "default_currency": "AUD",
            "default_language": "en",
            "market_regions": [
                {
                    "city": "Melbourne",
                    "country_code": "AU",
                    "currency": "AUD",
                    "language": "en",
                    "geo_fence": "AU-MEL-CBD",
                    "region_price_multiplier": 1.0,
                },
                {
                    "city": "Nairobi",
                    "country_code": "KE",
                    "currency": "KES",
                    "language": "sw",
                    "geo_fence": "KE-NBO-CBD",
                    "region_price_multiplier": 1.18,
                },
            ],
        },
    )
    store.store_billing_record(
        organization_id=org_id,
        plan="enterprise",
        usage_total=66,
        estimated_amount=18.4,
        billing_enabled=True,
    )
    store.store_driver_presence(
        organization_id=org_id,
        driver_id="driver-1",
        status="online",
        location={"lat": -37.8136, "lng": 144.9631, "label": "Melbourne CBD", "country_code": "AU", "currency": "AUD"},
        trust_score=97,
        metadata={"country_code": "AU", "currency": "AUD", "language": "en", "geo_fence": "AU-MEL-CBD", "region_price_multiplier": 1.0},
    )
    store.store_driver_presence(
        organization_id=org_id,
        driver_id="driver-2",
        status="online",
        location={"lat": -1.286389, "lng": 36.817223, "label": "Nairobi CBD", "country_code": "KE", "currency": "KES"},
        trust_score=94,
        metadata={"country_code": "KE", "currency": "KES", "language": "sw", "geo_fence": "KE-NBO-CBD", "region_price_multiplier": 1.18},
    )

    rides = (
        ("ride-1", "Melbourne CBD", "Docklands", "AUD", "completed", "25.00", "25.00", "driver-1"),
        ("ride-2", "Nairobi CBD", "Westlands", "KES", "completed", "1800.00", "2100.00", "driver-2"),
        ("ride-3", "Melbourne CBD", "St Kilda", "AUD", "cancelled", "18.00", None, "driver-1"),
        ("ride-4", "Nairobi CBD", "Airport", "KES", "completed", "2300.00", "2300.00", "driver-2"),
    )
    for ride_id, pickup_label, dropoff_label, currency, status, fare_estimate, final_fare, driver_id in rides:
        store.store_ride(
            ride_id=ride_id,
            organization_id=org_id,
            passenger_id="customer-1",
            driver_id=driver_id,
            pickup_location={"lat": 0.0, "lng": 0.0, "label": pickup_label},
            destination_location={"lat": 0.1, "lng": 0.1, "label": dropoff_label},
            fare_estimate=fare_estimate,
            currency=currency,
            status=status,
            final_fare=final_fare,
        )

    store.store_dispatch_assignment(
        organization_id=org_id,
        ride_id="ride-1",
        driver_id="driver-1",
        status="accepted",
        decision={"source": "phase12-test"},
    )
    store.store_dispatch_assignment(
        organization_id=org_id,
        ride_id="ride-2",
        driver_id="driver-2",
        status="accepted",
        decision={"source": "phase12-test"},
    )
    store.store_dispatch_assignment(
        organization_id=org_id,
        ride_id="ride-3",
        driver_id="driver-1",
        status="cancelled",
        decision={"source": "phase12-test"},
    )
    store.store_dispatch_assignment(
        organization_id=org_id,
        ride_id="ride-4",
        driver_id="driver-2",
        status="accepted",
        decision={"source": "phase12-test"},
    )

    for ride_id, user_id, counterparty_user_id, amount, currency, transaction_type in (
        ("ride-1", "customer-1", "driver-1", "25.00", "AUD", "debit"),
        ("ride-1", "driver-1", "customer-1", "25.00", "AUD", "credit"),
        ("ride-2", "customer-1", "driver-2", "2100.00", "KES", "debit"),
        ("ride-2", "driver-2", "customer-1", "2100.00", "KES", "credit"),
        ("ride-3", "customer-1", "driver-1", "18.00", "AUD", "debit"),
        ("ride-4", "customer-1", "driver-2", "2300.00", "KES", "debit"),
        ("ride-4", "driver-2", "customer-1", "2300.00", "KES", "credit"),
    ):
        store.store_transaction(
            organization_id=org_id,
            ride_id=ride_id,
            user_id=user_id,
            counterparty_user_id=counterparty_user_id,
            amount=amount,
            currency=currency,
            transaction_type=transaction_type,
        )

    for event_type, target, status, payload, actor_role in (
        ("support_ticket_created", "ticket-1", "open", {"ticket_id": "ticket-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}, "OPERATOR"),
        ("support_ticket_assigned", "ticket-1", "in_progress", {"ticket_id": "ticket-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}, "OPERATOR"),
        ("support_ticket_resolved", "ticket-1", "resolved", {"ticket_id": "ticket-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}, "OPERATOR"),
        ("support_ticket_closed", "ticket-1", "closed", {"ticket_id": "ticket-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}, "OPERATOR"),
        ("refund_requested", "refund-1", "open", {"refund_id": "refund-1", "ticket_id": "ticket-1", "ride_id": "ride-3", "amount": "18.00", "currency": "AUD", "category": "cancellation"}, "OPERATOR"),
        ("refund_approved", "refund-1", "approved", {"refund_id": "refund-1", "ticket_id": "ticket-1", "ride_id": "ride-3", "amount": "18.00", "currency": "AUD", "category": "cancellation"}, "OPERATOR"),
        ("dispute_opened", "dispute-1", "open", {"dispute_id": "dispute-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}, "OPERATOR"),
        ("dispute_resolved", "dispute-1", "resolved", {"dispute_id": "dispute-1", "ride_id": "ride-2", "category": "fare_dispute", "priority": "high"}, "OPERATOR"),
        ("inspection_started", "inspection-1", "pending", {"inspection_id": "inspection-1", "driver_id": "driver-1", "vehicle_id": "vehicle-1", "category": "vehicle_inspection"}, "VERIFIER"),
        ("inspection_approved", "inspection-1", "approved", {"inspection_id": "inspection-1", "driver_id": "driver-1", "vehicle_id": "vehicle-1", "category": "vehicle_inspection"}, "VERIFIER"),
        ("document_verified", "doc-1", "verified", {"document_id": "doc-1", "driver_id": "driver-1", "document_type": "license", "category": "document_verification"}, "VERIFIER"),
        ("inspection_report_submitted", "report-1", "approved", {"report_id": "report-1", "inspection_id": "inspection-1", "driver_id": "driver-1", "vehicle_id": "vehicle-1", "category": "inspection_report"}, "VERIFIER"),
        ("fraud_flagged", "fraud-1", "watch", {"fraud_id": "fraud-1", "ride_id": "ride-2", "category": "overcharge_pattern", "severity": "medium"}, "OPERATOR"),
    ):
        store.record_audit_event(
            organization_id=org_id,
            event_type=event_type,
            actor_user_id="operator-1",
            actor_role=actor_role,
            target=target,
            status=status,
            payload=payload,
        )


def test_phase12_global_scale_is_tenant_scoped_and_ready(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase12.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase12-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        observer_token = _issue_token(client, role="OBSERVER", organization_id=org_id, user_id="observer-1")

        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        observer_headers = {"Authorization": f"Bearer {observer_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 12 Global Scale Mobility Pty Ltd",
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
        _seed_phase12_store(store, org_id=org_id)

        response = client.get(
            "/v1/novaride/phase12/status",
            headers=operator_headers,
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["view"] == "novaride_phase12_status"
        assert payload["ready"] is True
        assert payload["readiness"]["multi_city_ready"] is True
        assert payload["readiness"]["geo_fencing_ready"] is True
        assert payload["readiness"]["currency_support_ready"] is True
        assert payload["readiness"]["localization_ready"] is True
        assert payload["readiness"]["region_pricing_ready"] is True
        assert payload["readiness"]["distributed_infrastructure_ready"] is True
        assert payload["readiness"]["auto_decision_engine_ready"] is True
        assert payload["readiness"]["fraud_prediction_ready"] is True
        assert payload["readiness"]["driver_incentives_ready"] is True

        workspace = payload["global_scale_workspace"]
        assert workspace["multi_city_management"]["city_count"] >= 2
        assert workspace["multi_city_management"]["active_city_count"] >= 2
        assert workspace["multi_city_management"]["supported_currencies"] == ["AUD", "KES"]
        assert workspace["multi_city_management"]["supported_languages"] == ["en", "sw"]
        assert workspace["currency_support"]["currency_support_ready"] is True
        assert workspace["localization"]["localization_ready"] is True
        assert workspace["region_pricing"]["region_pricing_ready"] is True
        assert workspace["distributed_infrastructure"]["distributed_ready"] is True
        assert workspace["auto_decision_engine"]["decision_lane"] in {"scale", "review"}
        assert workspace["fraud_prediction"]["risk_band"] in {"low", "watch"}
        assert workspace["driver_incentives"]["optimization_ready"] is True
        assert workspace["global_learning"]["recommendation"]

        contract = client.get(
            "/v1/novaride/phase12/global-scale-contract",
            headers=observer_headers,
        )
        assert contract.status_code == 200
        contract_payload = contract.json()
        assert contract_payload["status"] == "controlled_global_scaling_ready"
        assert "Multi-City Management" in {module["name"] for module in contract_payload["modules"]}
    finally:
        control_plane._STORE = original_store
