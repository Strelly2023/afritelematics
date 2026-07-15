from __future__ import annotations

from time import time

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWT
from afritech.novaride_runtime.sync_security import sign_sync_payload


RUNTIME_PERMISSIONS = (
    "novaride.runtime.read",
    "novaride.replay.create",
    "novaride.replay.review",
    "novaride.replay.validate",
    "novaride.replay.execute",
    "novaride.replay.approve",
    "novaride.replay.promote",
    "novaride.dispatch.manage",
    "novaride.driver.shift.manage",
    "novaride.driver.availability.manage",
    "novaride.operator.command.execute",
    "novaride.fleet.manage",
    "novaride.logistics.manage",
    "novaride.corporate.manage",
)


def _headers(*, subject_id: str, role: str, permissions: tuple[str, ...] = RUNTIME_PERMISSIONS, tenant_id: str = "tenant-novaride", organization_id: str = "org-novaride") -> dict[str, str]:
    token = JWT.create_token(
        subject_id,
        role=role,
        organization_id=organization_id,
        tenant_id=tenant_id,
        workspace_id="workspace-runtime",
        roles=(role,),
        permissions=permissions,
        region="australia-southeast",
    )
    return {"Authorization": f"Bearer {token}"}


def test_runtime_status_requires_verified_claims() -> None:
    client = TestClient(app)
    assert client.get("/v1/novaride/runtime/status").status_code == 401


def test_runtime_status_and_contract_status_are_release_candidate() -> None:
    client = TestClient(app)
    headers = _headers(subject_id="runtime-admin", role="PLATFORM_ADMIN")

    status = client.get("/v1/novaride/runtime/status", headers=headers).json()
    contract = client.get("/v1/novaride/next-generation").json()

    assert status["status"] == "runtime_capabilities_complete_release_candidate"
    assert status["GA_ALLOWED"] is False
    assert status["REAL_PAYMENTS_ENABLED"] is False
    assert contract["honest_status"] == "runtime_capabilities_complete_release_candidate"
    assert contract["runtime_metadata"]["release_gates_passed"]["fresh_apk_builds"] is False


def test_runtime_api_executes_booking_and_event_replay_with_verified_context() -> None:
    client = TestClient(app)
    headers = _headers(subject_id="admin-runtime", role="PLATFORM_ADMIN")

    driver = client.post(
        "/v1/drivers/onboarding",
        headers=headers,
        json={"display_name": "Driver", "identity_id": "novaid_driver", "vehicle_id": "vehicle_api"},
    )
    assert driver.status_code == 200

    start_shift = client.post("/v1/novaride/runtime/driver/shifts/start", headers=headers)
    assert start_shift.status_code == 200

    availability = client.put("/v1/novaride/runtime/driver/admin-runtime/availability", headers=headers)
    assert availability.status_code == 200

    quote = client.post("/v1/rider/fares/quote", headers=headers, json={"service_type": "economy", "currency": "AUD"}).json()
    booking = client.post(
        "/v1/rider/bookings",
        headers={**headers, "Idempotency-Key": "api-booking-1"},
        json={"rider_id": "admin-runtime", "service_type": "economy", "quote_id": quote["id"]},
    ).json()
    offer = client.post(f"/v1/novaride/runtime/dispatch/{booking['id']}", headers=headers).json()
    trip = client.post(f"/v1/driver/offers/{offer['id']}/accept", headers=headers).json()

    assert trip["lifecycle_state"] == "DRIVER_ACCEPTED"
    events = client.get(f"/v1/novaride/runtime/events/aggregate/{trip['id']}", headers=headers).json()["events"]
    assert any(event["event_type"] == "DriverAssigned" for event in events)


def test_mobile_sync_batch_status_and_conflict_resolution_are_exposed() -> None:
    client = TestClient(app)
    headers = _headers(subject_id="sync-admin", role="PLATFORM_ADMIN")
    body = {
        "device_id": "device_123",
        "last_server_cursor": "cursor_981",
        "operations": [
            {
                "id": "op_01",
                "idempotency_key": "booking-01",
                "operation_type": "booking_request",
                "aggregate_version": 1,
                "server_version": 2,
                "authority_required": True,
                "payload": {"pickup": "Westlands", "destination": "JKIA"},
            }
        ],
    }
    timestamp = str(int(time()))
    nonce = "contract-sync-nonce"
    signed_headers = {
        **headers,
        "X-NovaRide-Device-Id": "device_123",
        "X-NovaRide-Nonce": nonce,
        "X-NovaRide-Timestamp": timestamp,
        "X-NovaRide-Signature": sign_sync_payload(secret="test-device-secret", timestamp=timestamp, nonce=nonce, payload=body),
    }

    response = client.post(
        "/v1/novaride/mobile/sync/batch",
        headers=signed_headers,
        json=body,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sync_id"].startswith("sync")
    assert payload["results"] == [{"operation_id": "op_01", "status": "CONFLICT"}]
    assert payload["conflicts"]

    status = client.get(f"/v1/novaride/mobile/sync/status/{payload['sync_id']}", headers=headers)
    assert status.status_code == 200
    assert status.json()["status"] == "CONFLICTS_RECORDED"

    conflict_id = payload["conflicts"][0]["conflict_id"]
    resolved = client.post(
        f"/v1/novaride/mobile/sync/conflicts/{conflict_id}/resolve",
        headers=headers,
        json={"resolution": "server"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["reason"] == "resolved_by_server"


def test_signed_mobile_sync_rejects_replay_nonce() -> None:
    client = TestClient(app)
    headers = _headers(subject_id="sync-replay-admin", role="PLATFORM_ADMIN")
    body = {"device_id": "device_123", "last_server_cursor": None, "operations": []}
    signature_body = {"device_id": "device_123"}
    timestamp = str(int(time()))
    nonce = "replay-nonce"
    signed_headers = {
        **headers,
        "X-NovaRide-Device-Id": "device_123",
        "X-NovaRide-Nonce": nonce,
        "X-NovaRide-Timestamp": timestamp,
        "X-NovaRide-Signature": sign_sync_payload(secret="test-device-secret", timestamp=timestamp, nonce=nonce, payload=signature_body),
    }

    assert client.post("/v1/novaride/mobile/sync/batch", headers=signed_headers, json=body).status_code == 200
    replay = client.post("/v1/novaride/mobile/sync/batch", headers=signed_headers, json=body)
    assert replay.status_code == 403
    assert replay.json()["error"]["message"] == "reused_nonce"


def test_operations_status_commands_metrics_and_readiness_are_exposed() -> None:
    client = TestClient(app)
    headers = _headers(subject_id="ops-admin", role="PLATFORM_ADMIN")

    assert client.get("/v1/novaride/operations/resilience/status", headers=headers).status_code == 200
    assert client.get("/v1/novaride/operations/regions", headers=headers).json()["regions"]
    circuit = client.post(
        "/v1/novaride/operations/circuits/payment:primary/open",
        headers=headers,
        json={"reason": "provider outage rehearsal"},
    )
    assert circuit.status_code == 200
    assert circuit.json()["evidence_hash"].startswith("sha256:")
    metrics = client.get("/v1/novaride/metrics", headers=headers)
    assert metrics.status_code == 200
    assert "novaride_offline_queue_depth" in metrics.text
    certificate = client.get("/v1/novaride/operations/readiness-certificate", headers=headers).json()
    assert certificate["final_status"] != "READY_FOR_GA"
    assert "live_kafka_not_verified" in certificate["unresolved_risks"]
