from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWT


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
