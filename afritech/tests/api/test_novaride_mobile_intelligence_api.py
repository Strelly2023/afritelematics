from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore


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


def test_mobile_intelligence_projection_feeds_are_scoped_and_human_readable(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "mobile-intelligence.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-intelligence-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        customer_token = _issue_token(client, role="CUSTOMER", organization_id=org_id, user_id="passenger-1")
        driver_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-1")
        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        customer_headers = {"Authorization": f"Bearer {customer_token}"}
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Intelligence Mobility Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200

        control_plane._STORE.store_trust_score(
            organization_id=org_id,
            trust_score=97,
            classification="stable",
            breakdown={"driver": 98, "payments": 96},
            findings=["Driver network healthy", "Payments verified"],
        )
        control_plane._STORE.store_assurance_alert(
            organization_id=org_id,
            assurance_run_id="assurance-1",
            alert_level="info",
            message="High demand in CBD",
        )
        control_plane._STORE.store_dashboard_analytics_snapshot(
            organization_id=org_id,
            source="operator_dashboard",
            snapshot_type="live",
            trust_score=97,
            trust_health=95,
            replay_health_score=96,
            evidence_coverage=92,
            exception_pressure=4,
            alert_count=1,
            active_drivers=3,
            completed_rides=2,
            total_rides=10,
            guard_count=3,
            replay_failures=0,
            hash_chain_failures=0,
            missing_traces=0,
            receipts_count=2,
            trace_count=8,
            payload={"primary_zone": "CBD"},
        )

        driver_online = client.post(
            "/v1/novaride/phase2/drivers/online",
            headers=driver_headers,
            json={
                "location": {"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
                "trust_score": 97.0,
            },
        )
        assert driver_online.status_code == 200

        driver_intelligence = client.get(
            "/v1/intelligence/driver",
            headers=driver_headers,
            params={"organization_id": org_id},
        )
        assert driver_intelligence.status_code == 200
        driver_feed = driver_intelligence.json()
        assert driver_feed["projection_only"] is True
        assert driver_feed["status"] == "online"
        assert driver_feed["zone"] == "CBD"
        assert driver_feed["demand_level"] == "moderate"
        assert driver_feed["surge"] == 1.3
        assert driver_feed["trust_score"] == 97
        assert driver_feed["autonomous_mode"] is True
        assert driver_feed["predictive_positioning"]["mode"] in {"guided", "fully_autonomous"}
        assert driver_feed["predictive_positioning"]["target_zone"] == "CBD"
        assert driver_feed["city_automation"]["mode"] == "zero_operator"
        assert driver_feed["city_automation"]["zero_operator_mode"] is True
        assert driver_feed["multi_city_orchestration"]["mode"] == "global_zero_operator"
        assert driver_feed["multi_city_orchestration"]["city_count"] >= 2
        assert driver_feed["digital_twin"]["mode"] in {
            "shadow_sync",
            "predictive_closed_loop",
            "city_closed_loop",
            "global_closed_loop",
        }
        assert driver_feed["self_improving_loop"]["mode"] in {"watching", "learning", "recalibrating"}
        assert driver_feed["business_pricing"]["pricing_posture"] in {
            "balanced",
            "demand_rising",
            "surge_guarded",
            "discounted",
        }
        assert driver_feed["business_pricing"]["incentive_plan"]
        assert driver_feed["business_optimization"]["mode"] in {
            "autonomous",
            "supervised",
            "held",
        }
        assert driver_feed["business_optimization"]["budget_allocation"]["city_allocations"]
        assert driver_feed["navigation_intelligence"]["route_optimization"]["route_rows"]
        assert driver_feed["navigation_intelligence"]["traffic_aware_routing"]["mode"] == "traffic_aware"
        assert driver_feed["navigation_intelligence"]["pickup_precision"]["mode"] in {"pin_adjusted", "exact"}
        assert driver_feed["analytics_intelligence"]["revenue_dashboard"]["gross_transaction_volume"] == "0.00"
        assert driver_feed["analytics_intelligence"]["ride_metrics"]["total_rides"] >= 0
        assert driver_feed["analytics_intelligence"]["live_gps_stream"]["streaming_mode"] == "websocket_streaming"
        assert driver_feed["analytics_intelligence"]["learning_engine"]["rl_model"]["name"] == "bounded_feedback_loop_rl"
        assert driver_feed["demand_forecast"]["model"]["name"] == "bounded_demand_forecast_ml"
        assert driver_feed["demand_forecast"]["realtime_analytics"]["live_state"]["zone"] == "CBD"
        assert driver_feed["demand_forecast"]["forecast_windows"]
        assert driver_feed["demand_forecast"]["recommendation"]["primary_city"] == "CBD"
        assert driver_feed["compliance"]["vehicle"] == "verified"
        assert driver_feed["alerts"]

        passenger_intelligence = client.get(
            "/v1/intelligence/passenger",
            headers=customer_headers,
            params={"organization_id": org_id},
        )
        assert passenger_intelligence.status_code == 200
        passenger_feed = passenger_intelligence.json()
        assert passenger_feed["projection_only"] is True
        assert passenger_feed["system_status"] == "stable"
        assert passenger_feed["safety_score"] >= 97
        assert passenger_feed["demand"] == "moderate"
        assert passenger_feed["eta_confidence"] == "high"
        assert passenger_feed["autonomous_mode"] is True
        assert passenger_feed["predictive_positioning"]["mode"] in {"guided", "fully_autonomous"}
        assert passenger_feed["city_automation"]["mode"] == "zero_operator"
        assert passenger_feed["city_automation"]["zero_operator_mode"] is True
        assert passenger_feed["multi_city_orchestration"]["mode"] == "global_zero_operator"
        assert passenger_feed["multi_city_orchestration"]["active_city_count"] >= 2
        assert passenger_feed["digital_twin"]["mode"] in {
            "shadow_sync",
            "predictive_closed_loop",
            "city_closed_loop",
            "global_closed_loop",
        }
        assert passenger_feed["self_improving_loop"]["mode"] in {"watching", "learning", "recalibrating"}
        assert passenger_feed["business_pricing"]["pricing_posture"] in {
            "balanced",
            "demand_rising",
            "surge_guarded",
            "discounted",
        }
        assert passenger_feed["business_pricing"]["rider_message"]
        assert passenger_feed["business_optimization"]["profit_optimization"]["mode"] in {
            "autonomous",
            "supervised",
            "held",
        }
        assert passenger_feed["business_optimization"]["budget_allocation"]["city_allocations"]
        assert passenger_feed["navigation_intelligence"]["route_optimization"]["route_rows"]
        assert passenger_feed["navigation_intelligence"]["heatmaps"]["zones"]
        assert passenger_feed["navigation_intelligence"]["controlled_execution"]["safe_limit_rules"]["projection_only"] is True
        assert passenger_feed["analytics_intelligence"]["revenue_dashboard"]["gross_transaction_volume"] == "0.00"
        assert passenger_feed["analytics_intelligence"]["live_gps_stream"]["active_driver_count"] >= 1
        assert passenger_feed["analytics_intelligence"]["learning_engine"]["feedback_loop"]["update_cycle"] == "realtime_feedback_loop"
        assert passenger_feed["demand_forecast"]["model"]["mode"] == "deterministic_heuristic"
        assert passenger_feed["demand_forecast"]["realtime_analytics"]["live_state"]["zone"] == "CBD"
        assert passenger_feed["demand_forecast"]["forecast_windows"]
        assert passenger_feed["trust"]["driver_verified"] is True
        assert passenger_feed["trust"]["payment_secure"] is True

        forbidden = client.get(
            "/v1/intelligence/driver",
            headers=driver_headers,
            params={"organization_id": "spoofed-org"},
        )
        assert forbidden.status_code == 403
        assert "organization_isolation_violation" in forbidden.text
    finally:
        control_plane._STORE = original_store
