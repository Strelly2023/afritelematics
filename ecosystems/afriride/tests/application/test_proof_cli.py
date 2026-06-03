import io
import json

from ecosystems.afriride.core.application.adapters.cli.proof_cli import run
from ecosystems.afriride.core.application.adapters.http.proof_api import build_audit_report


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


def pricing_payload(**overrides):
    payload = {
        "base_fare": "4.00",
        "per_distance_rate": "1.50",
        "per_time_rate": "0.25",
        "currency": "AUD",
    }
    payload.update(overrides)
    return payload


def proof_bundle(**overrides):
    payload = {
        "drivers": drivers_payload(),
        "execution_requests": [
            {"current_state": "REQUESTED", "target_state": "MATCHED"},
            {"current_state": "MATCHED", "target_state": "DRIVER_ACCEPTED"},
        ],
        "map_graph": graph_payload(),
        "pricing_config": pricing_payload(),
        "ride": ride_payload(),
    }
    payload.update(overrides)
    return payload


def run_cli(command, payload):
    stdin = io.StringIO(json.dumps(payload))
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run([command, "-"], stdin=stdin, stdout=stdout, stderr=stderr)

    output = json.loads(stdout.getvalue()) if stdout.getvalue() else None
    error = json.loads(stderr.getvalue()) if stderr.getvalue() else None
    return exit_code, output, error


def test_proof_cli_audits_declared_bundle_from_stdin():
    exit_code, output, error = run_cli("audit", proof_bundle())

    assert exit_code == 0
    assert error is None
    assert output["canonical_ride"]["id"] == "RIDE-001"
    assert output["assignment"]["driver_id"] == "DRIVER-001"
    assert output["price_plan"]["total_cost"] == "14.00"
    assert output["replay"]["replay_valid"] is True


def test_proof_cli_explains_without_new_authority():
    exit_code, output, error = run_cli("explain", proof_bundle())

    assert exit_code == 0
    assert error is None
    assert "deterministic score" in output["assignment_reason"]
    assert output["replay_valid"] is True


def test_proof_cli_replay_exits_nonzero_when_replay_fails():
    audit = build_audit_report(proof_bundle())
    replay_payload = proof_bundle(
        pricing_config=pricing_payload(base_fare="9.00"),
        trace=audit["trace"],
    )

    exit_code, output, error = run_cli("replay", replay_payload)

    assert exit_code == 1
    assert error is None
    assert output["replay_valid"] is False


def test_proof_cli_verify_store_validates_evidence_on_write_and_read():
    exit_code, output, error = run_cli("verify-store", proof_bundle())

    assert exit_code == 0
    assert error is None
    assert output["replay_valid"] is True
    assert output["evidence"]["trace_hash"] == output["trace_hash"]


def test_proof_cli_reports_bad_input_to_stderr():
    exit_code, output, error = run_cli("audit", {"ride": ride_payload()})

    assert exit_code == 1
    assert output is None
    assert error["ok"] is False
    assert "No admissible driver assignment" in error["error"]
