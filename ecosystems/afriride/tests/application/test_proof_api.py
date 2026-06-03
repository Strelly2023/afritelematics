from fastapi.testclient import TestClient

from ecosystems.afriride.core.application.adapters.http.proof_api import router


def client():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def ride_payload():
    return {
        "id": "RIDE-001",
        "passenger_id": "PASSENGER-001",
        "pickup_location": {"zone": "ZONE-A", "node_id": "A", "lat": 0.0, "lng": 0.0},
        "dropoff_location": {"zone": "ZONE-B", "node_id": "D", "lat": 1.0, "lng": 1.0},
        "requested_at": "2026-05-25T09:00:00Z",
    }


def drivers_payload():
    return [{"id": "DRIVER-001", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0}]


def graph_payload():
    return {
        "nodes": {"A": {"zone": "ZONE-A"}, "B": {}, "D": {"zone": "ZONE-B"}},
        "edges": [
            {"from": "A", "to": "B", "distance": 2.0, "estimated_time": 3.0},
            {"from": "B", "to": "D", "distance": 3.0, "estimated_time": 7.0},
        ],
    }


def pricing_payload():
    return {
        "base_fare": "4.00",
        "per_distance_rate": "1.50",
        "per_time_rate": "0.25",
        "currency": "AUD",
    }


def declared_ride():
    response = client().post("/proof/rides", json=ride_payload())
    assert response.status_code == 200
    return response.json()


def test_proof_api_declares_canonical_ride():
    result = declared_ride()

    assert result["canonical_ride"]["id"] == "RIDE-001"
    assert result["ride_hash"]


def test_proof_api_computes_optimization_bundle():
    declared = declared_ride()
    response = client().post(
        f"/proof/rides/{declared['ride_hash']}/optimize",
        json={
            "drivers": drivers_payload(),
            "map_graph": graph_payload(),
            "pricing_config": pricing_payload(),
            "ride": ride_payload(),
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["assignment"]["driver_id"] == "DRIVER-001"
    assert result["route_plan"]["path"] == ["A", "B", "D"]
    assert result["price_plan"]["total_cost"] == "14.00"
    assert result["price_hash"]


def test_proof_api_executes_transition_step():
    declared = declared_ride()
    response = client().post(
        f"/proof/rides/{declared['ride_hash']}/transition",
        json={
            "current_state": "REQUESTED",
            "ride": ride_payload(),
            "target_state": "MATCHED",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["execution_step"]["from_state"] == "REQUESTED"
    assert result["execution_step"]["to_state"] == "MATCHED"
    assert result["step_hash"]


def test_proof_api_builds_trace_and_replays_it():
    declared = declared_ride()
    trace_response = client().post(
        f"/proof/rides/{declared['ride_hash']}/trace",
        json={
            "drivers": drivers_payload(),
            "execution_requests": [
                {"current_state": "REQUESTED", "target_state": "MATCHED"},
                {"current_state": "MATCHED", "target_state": "DRIVER_ACCEPTED"},
            ],
            "map_graph": graph_payload(),
            "pricing_config": pricing_payload(),
            "ride": ride_payload(),
        },
    )
    assert trace_response.status_code == 200
    trace = trace_response.json()["trace"]

    replay_response = client().post(
        "/proof/replay",
        json={
            "drivers": drivers_payload(),
            "execution_requests": [
                {"current_state": "REQUESTED", "target_state": "MATCHED"},
                {"current_state": "MATCHED", "target_state": "DRIVER_ACCEPTED"},
            ],
            "map_graph": graph_payload(),
            "pricing_config": pricing_payload(),
            "ride": ride_payload(),
            "trace": trace,
        },
    )

    assert replay_response.status_code == 200
    assert replay_response.json()["replay_valid"] is True


def test_proof_api_replay_reports_false_for_missing_pricing_config():
    declared = declared_ride()
    trace_response = client().post(
        f"/proof/rides/{declared['ride_hash']}/trace",
        json={
            "drivers": drivers_payload(),
            "map_graph": graph_payload(),
            "pricing_config": pricing_payload(),
            "ride": ride_payload(),
        },
    )
    trace = trace_response.json()["trace"]

    replay_response = client().post(
        "/proof/replay",
        json={
            "drivers": drivers_payload(),
            "map_graph": graph_payload(),
            "ride": ride_payload(),
            "trace": trace,
        },
    )

    assert replay_response.status_code == 200
    assert replay_response.json()["replay_valid"] is False


def test_proof_api_builds_read_only_audit_report():
    response = client().post(
        "/proof/audit",
        json={
            "drivers": drivers_payload(),
            "execution_requests": [
                {"current_state": "REQUESTED", "target_state": "MATCHED"},
                {"current_state": "MATCHED", "target_state": "DRIVER_ACCEPTED"},
            ],
            "map_graph": graph_payload(),
            "pricing_config": pricing_payload(),
            "ride": ride_payload(),
        },
    )

    assert response.status_code == 200
    audit = response.json()
    assert audit["canonical_ride"]["id"] == "RIDE-001"
    assert audit["assignment"]["driver_id"] == "DRIVER-001"
    assert audit["route_plan"]["path"] == ["A", "B", "D"]
    assert audit["price_plan"]["total_cost"] == "14.00"
    assert audit["execution_steps"][0]["step"]["to_state"] == "MATCHED"
    assert audit["trace_hash"]
    assert audit["replay"]["replay_valid"] is True


def test_proof_api_builds_read_only_replay_report():
    trace_response = client().post(
        "/proof/audit",
        json={
            "drivers": drivers_payload(),
            "map_graph": graph_payload(),
            "pricing_config": pricing_payload(),
            "ride": ride_payload(),
        },
    )
    audit = trace_response.json()

    replay_response = client().post(
        "/proof/replay-report",
        json={
            "drivers": drivers_payload(),
            "map_graph": graph_payload(),
            "pricing_config": pricing_payload(),
            "ride": ride_payload(),
            "trace": audit["trace"],
        },
    )

    assert replay_response.status_code == 200
    assert replay_response.json()["replay_valid"] is True


def test_proof_api_explains_audit_report_without_new_authority():
    response = client().post(
        "/proof/explain",
        json={
            "drivers": drivers_payload(),
            "map_graph": graph_payload(),
            "pricing_config": pricing_payload(),
            "ride": ride_payload(),
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert "deterministic score" in result["assignment_reason"]
    assert "base fare plus distance cost plus time cost" in result["price_reason"]
    assert result["replay_valid"] is True
