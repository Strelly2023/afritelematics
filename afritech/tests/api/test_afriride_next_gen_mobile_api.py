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
