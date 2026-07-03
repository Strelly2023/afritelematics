from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app
from afriride_system.operations.intelligent_dispatch import (
    DispatchCandidate,
    WeightedDispatchEngine,
    operational_alerts,
)


def candidate(driver_id: str, **overrides):
    values = {
        "driver_id": driver_id,
        "distance_km": 1,
        "traffic_factor": 1,
        "driver_rating": 4.9,
        "vehicle_type": "standard",
        "acceptance_rate": 0.98,
        "trust_score": 96,
        "battery_level": 90,
        "estimated_arrival_minutes": 3,
        "surge_demand": 0.9,
        "online": True,
        "device_trusted": True,
        "open_safety_incidents": 0,
        "fraud_risk_score": 0.05,
    }
    values.update(overrides)
    return values


def auth(role: str, actor: str = "ops-1") -> dict[str, str]:
    return {"Authorization": f"Bearer {JWT.create_token(actor, role)}"}


def test_weighted_dispatch_is_deterministic_explainable_and_not_nearest_only() -> None:
    engine = WeightedDispatchEngine()
    nearest_low_trust = DispatchCandidate(
        **candidate("nearest", distance_km=0.1, trust_score=40)
    )
    balanced = DispatchCandidate(**candidate("balanced", distance_km=2))
    decision = engine.rank(
        [nearest_low_trust, balanced],
        requested_vehicle_type="standard",
        trace_id="trace-1",
    )
    assert decision["selected_driver_id"] == "balanced"
    assert decision["candidates"][1]["exclusions"] == ["trust"]
    assert set(decision["candidates"][0]["contributions"]) == set(decision["policy"]["weights"])
    assert decision["authority"] == "advisory_until_dispatcher_accepts"


def test_fraud_safety_integrity_and_battery_generate_operational_alerts() -> None:
    alerts = operational_alerts([
        DispatchCandidate(**candidate(
            "risk-driver",
            battery_level=5,
            device_trusted=False,
            fraud_risk_score=0.95,
            open_safety_incidents=1,
        ))
    ])
    assert {alert["alert_type"] for alert in alerts} == {
        "driver_low_battery",
        "driver_integrity_hold",
        "fraud_risk_high",
        "open_safety_incident",
    }


def test_operations_routes_require_privileged_role_and_expose_dashboard() -> None:
    client = TestClient(app)
    payload = {
        "ride_id": "ride-ops-1",
        "requested_vehicle_type": "standard",
        "candidates": [candidate("driver-1")],
        "trace_id": "trace-ops-1",
    }
    assert client.post("/v1/operations/dispatch/optimize", json=payload).status_code == 401
    response = client.post(
        "/v1/operations/dispatch/optimize", json=payload, headers=auth("DISPATCHER")
    )
    assert response.status_code == 200
    assert response.json()["selected_driver_id"] == "driver-1"
    dashboard = client.get("/v1/operations/dashboard", headers=auth("OPERATOR"))
    assert dashboard.status_code == 200
    assert dashboard.json()["dispatch"]["decisions"] >= 1


def test_automatic_dispatch_still_uses_authoritative_dispatcher() -> None:
    gateway = reset_gateway()
    gateway.driver.status({"driver_id": "driver-auto", "online": True})
    gateway.passenger.request_ride({
        "ride_id": "ride-auto",
        "passenger_id": "rider-auto",
        "pickup": "A",
        "destination": "B",
    })
    response = TestClient(app).post(
        "/v1/operations/dispatch/execute",
        json={
            "ride_id": "ride-auto",
            "requested_vehicle_type": "standard",
            "candidates": [candidate("driver-auto")],
            "trace_id": "trace-auto",
        },
        headers={"Idempotency-Key": "dispatch-auto-1", **auth("DISPATCHER")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["authority"] == "authoritative_dispatcher_accepted"
    assert body["assignment"]["status"] == "DRIVER_ASSIGNED"
    replay = TestClient(app).post(
        "/v1/operations/dispatch/execute",
        json={
            "ride_id": "ride-auto",
            "requested_vehicle_type": "standard",
            "candidates": [candidate("driver-auto")],
            "trace_id": "trace-auto",
        },
        headers={"Idempotency-Key": "dispatch-auto-1", **auth("DISPATCHER")},
    )
    assert replay.status_code == 200
    assert replay.json() == body
