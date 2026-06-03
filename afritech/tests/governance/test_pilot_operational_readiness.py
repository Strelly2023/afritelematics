from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWTService
from afritech.api.trace_api import TraceStoreAPI
from afritech.payments.payment_events import PaymentEventFactory, PaymentIntentRequest, StripePilotService
from afritech.security.ed25519 import generate_keypair
from afritech.trace.pilot_trace_recorder import PilotTraceRecorder


ROOT = Path(__file__).resolve().parents[3]


def test_trace_api_lists_loads_and_checks_recorded_trace(tmp_path: Path) -> None:
    trace = {
        "trace_id": "trip_123",
        "events": [{"event_id": "evt_1"}],
        "normalized_events": [{"normalized_event_id": "norm_1"}],
        "execution_states": [{"state": "applied"}],
        "witnesses": [{"witness_id": "wit_1"}],
    }
    PilotTraceRecorder(tmp_path).record(trace)
    api = TraceStoreAPI(tmp_path)

    assert api.list_traces() == ["trip_123.json"]

    loaded = api.load_trace("trip_123")
    readiness = api.inspect_replay_readiness("trip_123")

    assert loaded["trace_id"] == "trip_123"
    assert readiness["status"] == "ready"
    assert readiness["hash_matches"] is True


def test_fastapi_auth_token_and_device_registration() -> None:
    client = TestClient(app)
    _, public_key = generate_keypair()

    token_response = client.post("/v1/auth/token", json={"user_id": "driver_45"})
    assert token_response.status_code == 200
    token = token_response.json()["token"]

    register_response = client.post(
        "/v1/devices/register",
        headers={"authorization": f"Bearer {token}"},
        json={
            "device_id": "driver_45_phone_1",
            "user_id": "driver_45",
            "public_key": public_key,
            "registered_at": 1710000000000,
        },
    )

    assert register_response.status_code == 200
    assert register_response.json()["device_id"] == "driver_45_phone_1"


def test_jwt_rejects_tampered_token() -> None:
    service = JWTService("secret", ttl_seconds=60)
    token = service.create_token("driver_45", issued_at=100)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    try:
        service.verify_token(tampered, now=120)
        assert False
    except ValueError as exc:
        assert str(exc) == "invalid_signature"


def test_payment_adapters_emit_events_not_mutations() -> None:
    intent = StripePilotService().create_payment(
        PaymentIntentRequest(ride_id="ride_123", amount_minor=1500, currency="aud")
    )
    event = PaymentEventFactory().mobile_money_confirmed(
        event_id="mm_1",
        transaction_id="txn_1",
        ride_id="ride_123",
        status="SUCCESS",
        amount_minor=1500,
        timestamp=1710000000000,
    )

    assert intent["mode"] == "pilot_stub"
    assert intent["client_secret"].startswith("pi_pilot_")
    assert event["event_type"] == "PAYMENT_CONFIRMED"
    assert event["payload"]["provider"] == "mobile_money"


def test_replay_dashboard_and_melbourne_checklist_are_claim_bounded() -> None:
    dashboard_files = [
        ROOT / "replay_dashboard/src/App.jsx",
        ROOT / "replay_dashboard/src/TraceList.jsx",
        ROOT / "replay_dashboard/src/TraceViewer.jsx",
    ]
    for path in dashboard_files:
        assert path.exists(), f"missing dashboard artifact: {path}"

    checklist = (ROOT / "afritech/docs/operations/melbourne_pilot_execution_checklist.md").read_text()
    assert "does not claim production readiness" in checklist
    assert "Stop Conditions" in checklist
    assert "Airport to CBD corridor" in checklist
