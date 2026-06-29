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


def test_phase9_partner_ecosystem_is_tenant_scoped_and_partner_ready(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase9.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase9-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        partner_token = _issue_token(client, role="PARTNER", organization_id=org_id, user_id="partner-1")
        admin_token = _issue_token(client, role="ADMIN", organization_id=org_id, user_id="admin-1")

        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        partner_headers = {"Authorization": f"Bearer {partner_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 9 Partner Mobility Pty Ltd",
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
                "seats": 10,
            },
        )
        assert subscription.status_code == 200

        store = control_plane._STORE
        store.upsert_organization_profile(
            organization_id=org_id,
            organization_type="partner",
            status="active",
            default_plan="enterprise",
            owner_user_id="partner-1",
            owner_role="PARTNER",
        )
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
            user_id="partner-1",
            role="PARTNER",
        )
        store.store_account(
            organization_id=org_id,
            user_id="partner-2",
            role="PARTNER",
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

        store.register_integration(
            organization_id=org_id,
            name="Hotel Booking Widget",
            type="widget_api",
            config={"surface": "widget", "channel": "hotel"},
        )
        store.register_integration(
            organization_id=org_id,
            name="Airport Partner API",
            type="api",
            config={"surface": "api", "channel": "airport"},
        )
        store.register_integration(
            organization_id=org_id,
            name="Partner Billing",
            type="billing",
            config={"settlement": "postpaid"},
        )
        store.store_trust_score(
            organization_id=org_id,
            trust_score=97,
            classification="stable",
            breakdown={"partner": 97, "billing": 96, "dispatch": 95},
            findings=["Partner ecosystem stable", "Booking channels active"],
        )
        store.store_dashboard_analytics_snapshot(
            organization_id=org_id,
            source="afriride_operator_dashboard",
            snapshot_type="partner",
            trust_score=97,
            trust_health=96,
            replay_health_score=95,
            evidence_coverage=94,
            exception_pressure=2,
            alert_count=1,
            active_drivers=2,
            completed_rides=4,
            total_rides=4,
            guard_count=2,
            replay_failures=0,
            hash_chain_failures=0,
            missing_traces=0,
            receipts_count=4,
            trace_count=10,
            payload={"primary_zone": "CBD"},
        )
        store.track_usage(
            organization_id=org_id,
            metric="partner_bookings",
            amount=4,
            context={"surface": "partner_portal", "partner_type": "hotel"},
        )
        store.track_usage(
            organization_id=org_id,
            metric="partner_bulk_requests",
            amount=2,
            context={"surface": "partner_portal", "partner_type": "airport"},
        )
        store.track_usage(
            organization_id=org_id,
            metric="partner_event_transport",
            amount=1,
            context={"surface": "partner_portal", "partner_type": "event"},
        )
        store.store_billing_record(
            organization_id=org_id,
            plan="enterprise",
            usage_total=7,
            estimated_amount=14.2,
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
            trust_score=92,
            metadata={"zone": "Southbank"},
        )
        store.store_ride(
            ride_id="ride-1",
            organization_id=org_id,
            passenger_id="guest-1",
            driver_id="driver-1",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "Hotel CBD"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Airport"},
            fare_estimate="48.00",
            currency="AUD",
            status="completed",
            final_fare="48.00",
        )
        store.store_ride(
            ride_id="ride-2",
            organization_id=org_id,
            passenger_id="guest-2",
            driver_id="driver-1",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "Hotel CBD"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Conference Center"},
            fare_estimate="31.00",
            currency="AUD",
            status="completed",
            final_fare="31.00",
        )
        store.store_ride(
            ride_id="ride-3",
            organization_id=org_id,
            passenger_id="guest-3",
            driver_id="driver-2",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "Airport"},
            destination_location={"lat": -37.8100, "lng": 144.9800, "label": "Hotel CBD"},
            fare_estimate="28.00",
            currency="AUD",
            status="completed",
            final_fare="28.00",
        )
        store.store_ride(
            ride_id="ride-4",
            organization_id=org_id,
            passenger_id="guest-4",
            driver_id="driver-2",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "Event Venue"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Hotel CBD"},
            fare_estimate="19.00",
            currency="AUD",
            status="completed",
            final_fare="19.00",
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-1",
            driver_id="driver-1",
            status="accepted",
            decision={"source": "phase9-test", "driver_id": "driver-1"},
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-2",
            driver_id="driver-1",
            status="accepted",
            decision={"source": "phase9-test", "driver_id": "driver-1"},
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-3",
            driver_id="driver-2",
            status="accepted",
            decision={"source": "phase9-test", "driver_id": "driver-2"},
        )
        store.store_dispatch_assignment(
            organization_id=org_id,
            ride_id="ride-4",
            driver_id="driver-2",
            status="accepted",
            decision={"source": "phase9-test", "driver_id": "driver-2"},
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-1",
            user_id="guest-1",
            counterparty_user_id="driver-1",
            amount="48.00",
            currency="AUD",
            transaction_type="debit",
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-1",
            user_id="driver-1",
            counterparty_user_id="guest-1",
            amount="48.00",
            currency="AUD",
            transaction_type="credit",
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-2",
            user_id="guest-2",
            counterparty_user_id="driver-1",
            amount="31.00",
            currency="AUD",
            transaction_type="debit",
        )
        store.store_transaction(
            organization_id=org_id,
            ride_id="ride-2",
            user_id="driver-1",
            counterparty_user_id="guest-2",
            amount="31.00",
            currency="AUD",
            transaction_type="credit",
        )

        status = client.get("/v1/novaride/phase9/status", headers=operator_headers, params={"limit": 50})
        assert status.status_code == 200
        status_payload = status.json()
        assert status_payload["view"] == "novaride_phase9_status"
        assert status_payload["ready"] is True
        assert status_payload["readiness"]["partner_portal_ready"] is True
        assert status_payload["readiness"]["booking_api_ready"] is True
        assert status_payload["readiness"]["bulk_scheduling_ready"] is True
        assert status_payload["readiness"]["event_transport_ready"] is True
        assert status_payload["readiness"]["reporting_ready"] is True
        assert status_payload["readiness"]["billing_ready"] is True
        assert status_payload["readiness"]["configuration_ready"] is True
        assert status_payload["readiness"]["live_dispatch_influence_ready"] is True
        assert status_payload["readiness"]["automated_incentives_ready"] is True
        assert status_payload["readiness"]["enterprise_automation_ready"] is True

        portal = client.get(
            "/v1/novaride/phase9/partner-portal",
            headers=partner_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert portal.status_code == 200
        portal_payload = portal.json()
        assert portal_payload["view"] == "novaride_phase9_partner_portal"
        assert portal_payload["partner_portal"]["booking_api_enabled"] is True
        assert portal_payload["partner_portal"]["booking_widget_enabled"] is True
        assert portal_payload["partner_portal"]["partner_account_count"] == 2

        bookings = client.get(
            "/v1/novaride/phase9/bookings",
            headers=partner_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert bookings.status_code == 200
        bookings_payload = bookings.json()
        assert bookings_payload["view"] == "novaride_phase9_bookings"
        assert bookings_payload["bookings"]["guest_booking_volume"] == 4
        assert bookings_payload["bookings"]["completed_booking_volume"] == 4
        assert bookings_payload["bookings"]["cancellation_rate"] == 0.0

        bulk_requests = client.get(
            "/v1/novaride/phase9/bulk-requests",
            headers=admin_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert bulk_requests.status_code == 200
        bulk_payload = bulk_requests.json()
        assert bulk_payload["view"] == "novaride_phase9_bulk_requests"
        assert bulk_payload["bulk_scheduling"]["estimated_batches"] >= 1
        assert bulk_payload["automated_incentives"]["incentive_band"] == "strong"

        event_transport = client.get(
            "/v1/novaride/phase9/event-transport",
            headers=partner_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert event_transport.status_code == 200
        event_transport_payload = event_transport.json()
        assert event_transport_payload["view"] == "novaride_phase9_event_transport"
        assert event_transport_payload["event_transport"]["event_transport_volume"] == 1

        reports = client.get(
            "/v1/novaride/phase9/reports",
            headers=partner_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert reports.status_code == 200
        reports_payload = reports.json()
        assert reports_payload["view"] == "novaride_phase9_partner_reporting"
        assert reports_payload["reporting"]["ride_success_rate"] == 1.0
        assert reports_payload["reporting"]["rides_booked"] == 4

        billing = client.get(
            "/v1/novaride/phase9/billing",
            headers=partner_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert billing.status_code == 200
        billing_payload = billing.json()
        assert billing_payload["view"] == "novaride_phase9_partner_billing"
        assert billing_payload["billing"]["billing_mode"] == "postpaid_invoicing"
        assert float(billing_payload["billing"]["estimated_monthly_invoice"]) > 0.0

        automation = client.get(
            "/v1/novaride/phase9/enterprise-automation",
            headers=partner_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert automation.status_code == 200
        automation_payload = automation.json()
        assert automation_payload["view"] == "novaride_phase9_enterprise_automation"
        assert automation_payload["enterprise_automation"]["automation_mode"] == "partner_automation_ready"

        revenue = client.get(
            "/v1/novaride/phase9/partner-revenue",
            headers=partner_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert revenue.status_code == 200
        revenue_payload = revenue.json()
        assert revenue_payload["view"] == "novaride_phase9_partner_revenue"
        assert float(revenue_payload["revenue_proxy"]) > 0.0

        forbidden = client.get(
            "/v1/novaride/phase9/partner-portal",
            headers=partner_headers,
            params={"organization_id": "spoofed-org", "limit": 50},
        )
        assert forbidden.status_code == 403
        assert "organization_isolation_violation" in forbidden.text
    finally:
        control_plane._STORE = original_store
