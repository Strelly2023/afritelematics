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


def test_phase6_navigation_maps_intelligence_and_roi_are_bounded(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase6.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase6-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        passenger_token = _issue_token(client, role="CUSTOMER", organization_id=org_id, user_id="passenger-1")
        driver_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-1")
        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        passenger_headers = {"Authorization": f"Bearer {passenger_token}"}
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 6 Navigation Mobility Pty Ltd",
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
        store.store_trust_score(
            organization_id=org_id,
            trust_score=96,
            classification="stable",
            breakdown={"routing": 96, "safety": 95},
            findings=["Routing healthy", "Demand stable"],
        )
        store.store_dashboard_analytics_snapshot(
            organization_id=org_id,
            source="operator_dashboard",
            snapshot_type="live",
            trust_score=96,
            trust_health=95,
            replay_health_score=94,
            evidence_coverage=92,
            exception_pressure=4,
            alert_count=1,
            active_drivers=3,
            completed_rides=4,
            total_rides=12,
            guard_count=2,
            replay_failures=0,
            hash_chain_failures=0,
            missing_traces=0,
            receipts_count=4,
            trace_count=9,
            payload={"primary_zone": "CBD"},
        )
        store.store_driver_presence(
            organization_id=org_id,
            driver_id="driver-1",
            status="online",
            location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            trust_score=97,
            metadata={"zone": "CBD"},
        )
        store.store_driver_presence(
            organization_id=org_id,
            driver_id="driver-2",
            status="online",
            location={"lat": -37.8150, "lng": 144.9700, "label": "Southbank"},
            trust_score=90,
            metadata={"zone": "Southbank"},
        )
        store.store_ride(
            ride_id="ride-1",
            organization_id=org_id,
            passenger_id="passenger-1",
            driver_id="driver-1",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
            fare_estimate="40.00",
            currency="AUD",
            status="in_progress",
        )
        store.store_ride(
            ride_id="ride-2",
            organization_id=org_id,
            passenger_id="passenger-1",
            driver_id="driver-2",
            pickup_location={"lat": -37.8150, "lng": 144.9700, "label": "Southbank"},
            destination_location={"lat": -37.8200, "lng": 144.9800, "label": "Richmond"},
            fare_estimate="35.00",
            currency="AUD",
            status="completed",
            final_fare="35.00",
        )

        status = client.get("/v1/novaride/phase6/status", headers=operator_headers, params={"limit": 50})
        assert status.status_code == 200
        status_payload = status.json()
        assert status_payload["view"] == "novaride_phase6_status"
        assert status_payload["readiness"]["phase5_ready"] in {True, False}
        assert status_payload["readiness"]["route_optimization_ready"] is True
        assert status_payload["readiness"]["traffic_aware_routing_ready"] is True
        assert status_payload["readiness"]["pickup_precision_ready"] is True
        assert status_payload["readiness"]["heatmaps_ready"] is True
        assert status_payload["readiness"]["capital_allocation_ready"] is True
        assert status_payload["ready"] is True

        navigation = client.get(
            "/v1/novaride/phase6/navigation-intelligence",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert navigation.status_code == 200
        payload = navigation.json()
        assert payload["view"] == "novaride_phase6_navigation_maps_intelligence"
        assert payload["route_optimization"]["route_rows"]
        assert payload["route_optimization"]["route_lane"] in {"optimize_supply", "optimize_traffic", "improve_pickup_precision", "monitor"}
        assert payload["traffic_aware_routing"]["mode"] == "traffic_aware"
        assert payload["pickup_precision"]["mode"] in {"pin_adjusted", "exact"}
        assert payload["heatmaps"]["zones"]
        assert payload["capital_allocation"]["capital_allocation"]
        assert payload["controlled_execution"]["safe_limit_rules"]["projection_only"] is True
        assert payload["controlled_execution"]["safe_limit_rules"]["no_dispatch_override"] is True
        assert payload["controlled_execution"]["projection_only"] is True
        assert payload["read_only"] is True

        roi = client.get(
            "/v1/novaride/phase6/capital-allocation",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert roi.status_code == 200
        roi_payload = roi.json()
        assert roi_payload["view"] == "novaride_phase6_capital_allocation"
        assert roi_payload["capital_allocation"]
        assert roi_payload["controlled_execution"]["read_only"] is True

        driver_feed = client.get(
            "/v1/intelligence/driver",
            headers=driver_headers,
            params={"organization_id": org_id},
        ).json()
        passenger_feed = client.get(
            "/v1/intelligence/passenger",
            headers=passenger_headers,
            params={"organization_id": org_id},
        ).json()
        assert driver_feed["navigation_intelligence"]["route_optimization"]["route_rows"]
        assert passenger_feed["navigation_intelligence"]["heatmaps"]["zones"]
        assert passenger_feed["navigation_intelligence"]["controlled_execution"]["safe_limit_rules"]["projection_only"] is True

        forbidden = client.get(
            "/v1/novaride/phase6/navigation-intelligence",
            headers=operator_headers,
            params={"organization_id": "spoofed-org"},
        )
        assert forbidden.status_code == 403
        assert "organization_isolation_violation" in forbidden.text
    finally:
        control_plane._STORE = original_store
