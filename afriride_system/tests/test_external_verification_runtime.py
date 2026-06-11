from __future__ import annotations

from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app
from afriride_system.api.dependencies.runtime import reset_trace_log


def auth(role: str, user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {JWT.create_token(user_id, role)}"}


def setup_function() -> None:
    reset_gateway()
    reset_trace_log()


def _complete_ride(client: TestClient, ride_id: str) -> None:
    client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers={"Idempotency-Key": f"{ride_id}-driver-online", **auth("DRIVER", "driver-1")},
    )
    client.post(
        "/passenger/request-ride",
        json={
            "passenger_id": "rider-1",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": ride_id,
        },
        headers={"Idempotency-Key": f"{ride_id}-request", **auth("RIDER", "rider-1")},
    )
    for action in ("accept", "arrive", "start", "complete"):
        client.post(
            f"/ride/{ride_id}/{action}",
            json={"driver_id": "driver-1"},
            headers={"Idempotency-Key": f"{ride_id}-{action}", **auth("DRIVER", "driver-1")},
        )


def test_external_verification_endpoint_returns_partner_packet_and_signed_receipt() -> None:
    client = TestClient(app)
    _complete_ride(client, "ride-external-1")

    response = client.post(
        "/system/external-verify/ride-external-1",
        json={"publication_target": "public-ledger-test-anchor"},
        headers=auth("OPERATOR", "operator-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ride_id"] == "ride-external-1"
    assert payload["verification_packet"]["verification_status"] == "VERIFIED"
    assert payload["verification_packet"]["authority_boundary"].startswith("trace records authority")
    assert payload["receipt_signature_validation"]["signature_mode"] == "hmac_sha256_receipt_v1"
    assert payload["receipt_signature_validation"]["all_signatures_valid"] is True
    assert payload["authority"]["doc_id"] == "DOC-ARCH-001"
    assert len(payload["authority"]["authority_hash"]) == 64
    assert payload["authority"]["surface"] == "receipt_record"


def test_receipt_contract_returns_signed_receipt_validation() -> None:
    client = TestClient(app)
    _complete_ride(client, "ride-signed-1")

    response = client.get("/ride/ride-signed-1/receipt", headers=auth("RIDER", "rider-1"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["signature_validation"]["signature_mode"] == "hmac_sha256_receipt_v1"
    assert payload["signature_validation"]["all_signatures_valid"] is True
    assert len(payload["signature_validation"]["signature"]) == 64
    assert payload["authority"]["doc_id"] == "DOC-ARCH-001"
    assert len(payload["authority"]["authority_hash"]) == 64
    assert payload["authority"]["surface"] == "receipt_record"


def test_trust_sla_endpoint_and_runtime_stream_surface_current_status() -> None:
    client = TestClient(app)
    response = client.get("/system/trust-sla", headers=auth("OPERATOR", "operator-1"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["sla_status"] in {"GREEN", "WATCH", "BREACH"}
    assert "thresholds" in payload
    assert payload["authority_boundary"].startswith("SLA explains operational thresholds")
    assert payload["authority"]["doc_id"] == "DOC-ARCH-001"
    assert len(payload["authority"]["authority_hash"]) == 64
    assert payload["authority"]["surface"] == "trust_sla"

    token = JWT.create_token("operator-1", "OPERATOR")
    with client.websocket_connect(f"/ws/system/trust?token={token}") as websocket:
        message = websocket.receive_json()

    assert message["stream"] == "trust_runtime"
    assert message["trust_state"] in {"VERIFIED", "REVIEW"}
    assert message["sla_status"] in {"GREEN", "WATCH", "BREACH"}
    assert isinstance(message["alerts"], list)
    assert message["authority"]["doc_id"] == "DOC-ARCH-001"
    assert len(message["authority"]["authority_hash"]) == 64
    assert message["authority"]["surface"] == "trust_runtime_stream"


def test_ride_tracking_websocket_returns_authenticated_subscriber_context() -> None:
    client = TestClient(app)
    token = JWT.create_token("rider-1", "RIDER")

    with client.websocket_connect(f"/ws/ride-stream-1?token={token}") as websocket:
        message = websocket.receive_json()

    assert message["ride_id"] == "ride-stream-1"
    assert message["status"] == "connected"
    assert message["mode"] == "observation_only"
    assert message["subscriber"] == "rider-1"
    assert message["role"] == "RIDER"
