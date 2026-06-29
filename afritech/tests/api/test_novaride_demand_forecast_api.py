from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import DEFAULT_ORGANIZATION_ID, PlatformStore
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


def test_operator_demand_forecast_is_read_only_and_tenant_scoped(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "demand-forecast.sqlite3")

    try:
        client = TestClient(app)
        organization_id = DEFAULT_ORGANIZATION_ID
        other_organization_id = "org-demand-forecast-isolated"

        operator_token = _issue_token(
            client,
            role="OPERATOR",
            organization_id=organization_id,
            user_id="operator-1",
        )
        headers = {"Authorization": f"Bearer {operator_token}"}

        control_plane._STORE.upsert_organization_profile(
            organization_id=organization_id,
            organization_type="business",
            status="active",
            default_plan="enterprise",
            owner_user_id="operator-1",
            owner_role="OPERATOR",
        )
        control_plane._STORE.store_subscription(
            organization_id=organization_id,
            plan="enterprise",
            status="active",
            billing_cycle="monthly",
            seats=50,
        )
        control_plane._STORE.store_trust_score(
            organization_id=organization_id,
            trust_score=97,
            classification="stable",
            breakdown={"driver": 98, "payments": 96},
            findings=["Driver network healthy", "Payments verified"],
        )
        control_plane._STORE.store_dashboard_analytics_snapshot(
            organization_id=organization_id,
            source="afriride_operator_dashboard",
            snapshot_type="operator_dashboard",
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
        control_plane._STORE.store_driver_presence(
            organization_id=organization_id,
            driver_id="driver-1",
            status="online",
            location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            trust_score=97,
        )
        control_plane._STORE.store_driver_presence(
            organization_id=other_organization_id,
            driver_id="driver-9",
            status="online",
            location={"lat": -33.8688, "lng": 151.2093, "label": "Sydney"},
            trust_score=88,
        )
        control_plane._STORE.store_ride(
            ride_id="ride-demand-001",
            organization_id=organization_id,
            passenger_id="passenger-1",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
            fare_estimate=30,
            currency="AUD",
            status="requested",
        )
        control_plane._STORE.store_ride(
            ride_id="ride-demand-002",
            organization_id=organization_id,
            passenger_id="passenger-2",
            pickup_location={"lat": -37.8150, "lng": 144.9700, "label": "CBD"},
            destination_location={"lat": -37.8000, "lng": 144.9600, "label": "Southbank"},
            fare_estimate=24,
            currency="AUD",
            status="completed",
            final_fare=27,
        )

        response = client.get(
            "/v1/operator/demand-forecast",
            headers=headers,
            params={"organization_id": organization_id},
        )
        assert response.status_code == 200
        payload = response.json()

        assert payload["view"] == "novatech_operator_demand_forecast"
        assert payload["organization_id"] == organization_id
        assert payload["model"]["name"] == "bounded_demand_forecast_ml"
        assert payload["model"]["mode"] == "deterministic_heuristic"
        assert payload["realtime_analytics"]["live_state"]["zone"] == "CBD"
        assert payload["realtime_analytics"]["read_only"] is True
        assert payload["realtime_analytics"]["projection_only"] is True
        assert payload["forecast_windows"]
        assert payload["recommendation"]["primary_city"] == "CBD"
        assert payload["read_only"] is True
        assert payload["projection_only"] is True
        assert payload["city_forecasts"][0]["city"] == "CBD"
        assert payload["city_forecasts"][0]["demand_level"] in {"low", "moderate", "high"}
        assert payload["feature_vector"]["trust_score"] == 97
        assert payload["feature_vector"]["zone_count"] >= 1

        isolated = client.get(
            "/v1/operator/demand-forecast",
            headers=headers,
            params={"organization_id": other_organization_id},
        )
        assert isolated.status_code == 200
        isolated_payload = isolated.json()
        assert isolated_payload["organization_id"] == other_organization_id
        assert isolated_payload["recommendation"]["primary_city"] == "Sydney"
        assert isolated_payload["city_forecasts"][0]["city"] == "Sydney"
    finally:
        control_plane._STORE = original_store
