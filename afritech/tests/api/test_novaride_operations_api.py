from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.app import app as fastapi_app
from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novaride_operations_api import build_novaride_operations_router
from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.geography import AddressRef, GeoPoint
from afritech.novaride_runtime.common.money import Money
from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.models import (
    ActorType,
    DriverAvailability,
    DriverAvailabilityState,
    DriverOffer,
    DriverProfile,
    EmergencyCase,
    Incident,
    IncidentState as RuntimeIncidentState,
    EmergencyState,
    OfferState,
    Trip,
    TripState,
)
from afritech.novaride_runtime.operations_workspace import (
    IncidentState as WorkspaceIncidentState,
    OperationalIncident,
    OperationsWorkspaceService,
)
from afritech.novaride_runtime.services import create_runtime


TENANT_ID = "novaride-tenant"
ORGANIZATION_ID = "novaride-org"
REGION = "AU"


def _headers(role: str, user_id: str, tenant_id: str = TENANT_ID, organization_id: str = ORGANIZATION_ID) -> dict[str, str]:
    token = JWT.create_token(
        user_id,
        role=role,
        organization_id=organization_id,
        tenant_id=tenant_id,
        region=REGION,
    )
    return {"Authorization": f"Bearer {token}"}


def _client() -> TestClient:
    runtime = create_runtime()
    runtime.repositories.drivers.save(
        DriverProfile(
            id="driver_1",
            tenant_id=TENANT_ID,
            organization_id=ORGANIZATION_ID,
            region_code=REGION,
            identity_id="identity_driver_1",
            display_name="Amina Driver",
            vehicle_id="vehicle_1",
        )
    )
    runtime.repositories.availability.save(
        DriverAvailability(
            id="availability_1",
            tenant_id=TENANT_ID,
            organization_id=ORGANIZATION_ID,
            region_code=REGION,
            driver_id="driver_1",
            requested_state=DriverAvailabilityState.AVAILABLE,
            authoritative_state=DriverAvailabilityState.AVAILABLE,
            dispatchable=True,
            vehicle_id="vehicle_1",
            location_fresh=True,
            server_confirmed_at=utc_now(),
        )
    )
    runtime.repositories.trips.save(
        Trip(
            id="trip_1",
            tenant_id=TENANT_ID,
            organization_id=ORGANIZATION_ID,
            region_code=REGION,
            booking_id="booking_1",
            rider_id="rider_1",
            driver_id="driver_1",
            vehicle_id="vehicle_1",
            service_type="economy",
            pickup=AddressRef("City Pickup", GeoPoint(-37.8136, 144.9631)),
            destination=AddressRef("City Destination", GeoPoint(-37.816, 144.97)),
            lifecycle_state=TripState.IN_PROGRESS,
            safety_state="NORMAL",
        )
    )
    runtime.repositories.offers.save(
        DriverOffer(
            id="offer_1",
            tenant_id=TENANT_ID,
            organization_id=ORGANIZATION_ID,
            region_code=REGION,
            driver_id="driver_1",
            trip_id="trip_1",
            estimated_earnings=Money.of("12.50", "AUD"),
            state=OfferState.CREATED,
        )
    )
    runtime.repositories.events.append(
        MobilityEvent(
            event_type="TripLocationUpdated",
            aggregate_id="trip_1",
            aggregate_type="Trip",
            aggregate_version=1,
            tenant_id=TENANT_ID,
            region=REGION,
            actor_type=ActorType.SYSTEM.value,
            actor_id="system",
            correlation_id="corr_trip_1",
            causation_id=None,
            payload={
                "point": {
                    "lat": -37.8135,
                    "lng": 144.965,
                    "heading": 90,
                    "speed": 32,
                    "label": "Live city route",
                }
            },
        )
    )
    runtime.repositories.emergencies.save(
        EmergencyCase(
            id="emergency_1",
            tenant_id=TENANT_ID,
            organization_id=ORGANIZATION_ID,
            region_code=REGION,
            source=ActorType.RIDER,
            source_id="rider_1",
            trip_id="trip_1",
            state=EmergencyState.TRIGGERED,
            evidence_locked=True,
            visible_reference="safety-case-1",
        )
    )
    runtime.repositories.incidents.save(
        Incident(
            id="runtime_incident_1",
            tenant_id=TENANT_ID,
            organization_id=ORGANIZATION_ID,
            region_code=REGION,
            category="Dispatch delay",
            state=RuntimeIncidentState.REPORTED,
            severity="SEV2",
            owner_id="ops-team",
        )
    )
    workspace = OperationsWorkspaceService(runtime)
    workspace.incidents["ops_incident_1"] = OperationalIncident(
        incident_id="ops_incident_1",
        tenant_id=TENANT_ID,
        region_id=REGION,
        title="Dispatch delay",
        severity="SEV2",
        status=WorkspaceIncidentState.DETECTED,
        description="Trip linked incident for operations testing",
        affected_trips=("trip_1",),
        created_by="ops_1",
        updated_by="ops_1",
    )

    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novaride_operations_router(workspace))
    return TestClient(app)


def test_operations_cors_allows_approved_browser_origin_and_rejects_unapproved_origin() -> None:
    client = TestClient(fastapi_app)

    approved = client.options(
        "/api/v1/novaride/operations/overview",
        headers={
            "Origin": "http://127.0.0.1:14173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert approved.status_code == 200
    assert approved.headers["access-control-allow-origin"] == "http://127.0.0.1:14173"

    unapproved = client.options(
        "/api/v1/novaride/operations/overview",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert unapproved.status_code == 400
    assert "access-control-allow-origin" not in unapproved.headers


def test_operations_routes_require_authentication() -> None:
    client = _client()

    response = client.get("/api/v1/novaride/operations/overview")

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/json")


def test_overview_and_live_views_use_live_runtime_data() -> None:
    client = _client()
    headers = _headers("OPERATIONS_TEAM", "ops_1")

    overview = client.get("/api/v1/novaride/operations/overview", headers=headers)
    dependencies = client.get("/api/v1/novaride/operations/dependencies", headers=headers)
    live_map = client.get("/api/v1/novaride/operations/map", headers=headers)
    live_trips = client.get("/api/v1/novaride/operations/trips/live", headers=headers)
    live_drivers = client.get("/api/v1/novaride/operations/drivers/live", headers=headers)
    dispatch_health = client.get("/api/v1/novaride/operations/dispatch/health", headers=headers)

    assert overview.status_code == 200
    assert overview.headers["content-type"].startswith("application/json")
    overview_body = overview.json()
    assert overview_body["environment"] == "production"
    assert overview_body["summary"]["active_trips"] == 1
    assert overview_body["summary"]["drivers_online"] == 1
    assert overview_body["summary"]["drivers_available"] == 1
    assert overview_body["summary"]["open_incidents"] >= 1
    assert overview_body["summary"]["open_safety_cases"] >= 1
    assert overview_body["dependencies"][0]["status"] == "unknown"

    assert dependencies.status_code == 200
    assert len(dependencies.json()["dependencies"]) >= 1

    assert live_map.status_code == 200
    map_item = live_map.json()["items"][0]
    assert map_item["trip_id"] == "trip_1"
    assert map_item["driver_id"] == "driver_1"
    assert map_item["current_location"]["heading"] == 90
    assert map_item["incident_status"] == "detected"
    assert map_item["safety_status"] == "new"

    assert live_trips.status_code == 200
    assert live_trips.json()["items"][0]["trip_id"] == "trip_1"

    assert live_drivers.status_code == 200
    assert live_drivers.json()["items"][0]["driver_id"] == "driver_1"

    assert dispatch_health.status_code == 200
    assert dispatch_health.json()["queue_depth"] == 1


def test_incident_support_refund_and_action_governance() -> None:
    client = _client()
    ops_headers = _headers("OPERATIONS_TEAM", "ops_1")
    admin_headers = _headers("PLATFORM_ADMIN", "admin_1")

    incident = client.post(
        "/api/v1/novaride/operations/incidents",
        headers={**ops_headers, "Idempotency-Key": "incident-1"},
        json={
            "title": "Dispatch delay",
            "severity": "SEV2",
            "description": "Testing operational workflow",
            "affected_trips": ["trip_1"],
        },
    )
    assert incident.status_code == 201
    incident_id = incident.json()["incident_id"]

    assigned = client.post(
        f"/api/v1/novaride/operations/incidents/{incident_id}/assign",
        headers=ops_headers,
        json={"assigned_to": "incident-commander"},
    )
    assert assigned.status_code == 200
    assert assigned.json()["current_state"] == "declared"

    invalid_transition = client.post(
        f"/api/v1/novaride/operations/incidents/{incident_id}/transition",
        headers=ops_headers,
        json={"status": "closed"},
    )
    assert invalid_transition.status_code == 400
    assert invalid_transition.json()["detail"] == "invalid_incident_transition"

    incident_evidence = client.get(
        f"/api/v1/novaride/operations/incidents/{incident_id}/evidence",
        headers=ops_headers,
    )
    assert incident_evidence.status_code == 200
    assert incident_evidence.json()["items"]

    support_create = client.post(
        "/api/v1/novaride/operations/support/cases",
        headers={**ops_headers, "Idempotency-Key": "support-1"},
        json={"case_type": "booking_problem", "trip_id": "trip_1", "phone": "+61 400 000 000"},
    )
    assert support_create.status_code == 201
    support_case_id = support_create.json()["case_id"]

    sensitive_search_forbidden = client.get(
        "/api/v1/novaride/operations/support/cases",
        headers=ops_headers,
        params={"phone": "+61 400 000 000"},
    )
    assert sensitive_search_forbidden.status_code == 403

    sensitive_search_allowed = client.get(
        "/api/v1/novaride/operations/support/cases",
        headers=admin_headers,
        params={"phone": "+61 400 000 000"},
    )
    assert sensitive_search_allowed.status_code == 200
    assert sensitive_search_allowed.json()["items"][0]["case_id"] == support_case_id

    refund_one = client.post(
        "/api/v1/novaride/operations/refunds",
        headers={**ops_headers, "Idempotency-Key": "refund-1"},
        json={"amount": "75", "currency": "AUD", "payment_id": "payment_1", "trip_id": "trip_1", "idempotency_key": "refund-1"},
    )
    assert refund_one.status_code == 201
    refund_id = refund_one.json()["refund_id"]

    refund_two = client.post(
        "/api/v1/novaride/operations/refunds",
        headers={**ops_headers, "Idempotency-Key": "refund-1"},
        json={"amount": "75", "currency": "AUD", "payment_id": "payment_1", "trip_id": "trip_1", "idempotency_key": "refund-1"},
    )
    assert refund_two.status_code == 201
    assert refund_two.json()["refund_id"] == refund_id

    self_approval = client.post(
        f"/api/v1/novaride/operations/refunds/{refund_id}/approve",
        headers=ops_headers,
        json={"approval_reference": "self"},
    )
    assert self_approval.status_code == 403

    approver = client.post(
        f"/api/v1/novaride/operations/refunds/{refund_id}/approve",
        headers=admin_headers,
        json={"approval_reference": "ops-review"},
    )
    assert approver.status_code == 200
    executed = client.post(
        f"/api/v1/novaride/operations/refunds/{refund_id}/execute",
        headers=admin_headers,
        json={"provider_reference": "sandbox-confirmed"},
    )
    assert executed.status_code == 200
    assert executed.json()["current_state"] == "completed"

    action = client.post(
        "/api/v1/novaride/operations/actions",
        headers={**ops_headers, "Idempotency-Key": "action-1"},
        json={"action_type": "manual_dispatch", "target_id": "trip_1", "reason": "ops review"},
    )
    assert action.status_code == 201
    action_id = action.json()["action_id"]

    action_self_approval = client.post(
        f"/api/v1/novaride/operations/actions/{action_id}/approve",
        headers=ops_headers,
        json={"approval_reference": "self"},
    )
    assert action_self_approval.status_code == 403

    action_approved = client.post(
        f"/api/v1/novaride/operations/actions/{action_id}/approve",
        headers=admin_headers,
        json={"approval_reference": "ops-review"},
    )
    assert action_approved.status_code == 200
    action_verified = client.post(
        f"/api/v1/novaride/operations/actions/{action_id}/verify",
        headers=admin_headers,
        json={"result": "verified"},
    )
    assert action_verified.status_code == 200

    other_tenant = _headers("OPERATIONS_TEAM", "ops_2", tenant_id="other-tenant", organization_id="other-org")
    cross_tenant = client.get(f"/api/v1/novaride/operations/incidents/{incident_id}", headers=other_tenant)
    assert cross_tenant.status_code == 404


def test_idempotency_conflicts_reject_payload_drift_across_governed_creates() -> None:
    client = _client()
    ops_headers = _headers("OPERATIONS_TEAM", "ops_1")
    admin_headers = _headers("PLATFORM_ADMIN", "admin_1")

    incident_one = client.post(
        "/api/v1/novaride/operations/incidents",
        headers={**ops_headers, "Idempotency-Key": "idem-incident"},
        json={"title": "Dispatch delay", "severity": "SEV2", "description": "first"},
    )
    assert incident_one.status_code == 201
    incident_again = client.post(
        "/api/v1/novaride/operations/incidents",
        headers={**ops_headers, "Idempotency-Key": "idem-incident"},
        json={"title": "Dispatch delay", "severity": "SEV2", "description": "first"},
    )
    assert incident_again.status_code == 201
    assert incident_again.json()["incident_id"] == incident_one.json()["incident_id"]
    incident_conflict = client.post(
        "/api/v1/novaride/operations/incidents",
        headers={**ops_headers, "Idempotency-Key": "idem-incident"},
        json={"title": "Dispatch delay", "severity": "SEV1", "description": "changed"},
    )
    assert incident_conflict.status_code == 409
    assert incident_conflict.json()["detail"] == "idempotency_conflict"

    refund_one = client.post(
        "/api/v1/novaride/operations/refunds",
        headers={**ops_headers, "Idempotency-Key": "idem-refund"},
        json={"amount": "75", "currency": "AUD", "payment_id": "payment_1", "trip_id": "trip_1"},
    )
    assert refund_one.status_code == 201
    refund_again = client.post(
        "/api/v1/novaride/operations/refunds",
        headers={**ops_headers, "Idempotency-Key": "idem-refund"},
        json={"amount": "75.0", "currency": "aud", "payment_id": "payment_1", "trip_id": "trip_1"},
    )
    assert refund_again.status_code == 201
    assert refund_again.json()["refund_id"] == refund_one.json()["refund_id"]
    refund_conflict = client.post(
        "/api/v1/novaride/operations/refunds",
        headers={**ops_headers, "Idempotency-Key": "idem-refund"},
        json={"amount": "80", "currency": "AUD", "payment_id": "payment_1", "trip_id": "trip_1"},
    )
    assert refund_conflict.status_code == 409
    assert refund_conflict.json()["detail"] == "idempotency_conflict"

    support_one = client.post(
        "/api/v1/novaride/operations/support/cases",
        headers={**ops_headers, "Idempotency-Key": "idem-support"},
        json={"case_type": "booking_problem", "trip_id": "trip_1"},
    )
    assert support_one.status_code == 201
    support_again = client.post(
        "/api/v1/novaride/operations/support/cases",
        headers={**ops_headers, "Idempotency-Key": "idem-support"},
        json={"case_type": "booking_problem", "trip_id": "trip_1"},
    )
    assert support_again.status_code == 201
    assert support_again.json()["case_id"] == support_one.json()["case_id"]
    support_conflict = client.post(
        "/api/v1/novaride/operations/support/cases",
        headers={**ops_headers, "Idempotency-Key": "idem-support"},
        json={"case_type": "booking_problem", "trip_id": "trip_2"},
    )
    assert support_conflict.status_code == 409

    investigation_one = client.post(
        "/api/v1/novaride/operations/payments/investigations",
        headers={**ops_headers, "Idempotency-Key": "idem-investigation"},
        json={"payment_id": "payment_1", "reason": "suspected mismatch"},
    )
    assert investigation_one.status_code == 201
    investigation_again = client.post(
        "/api/v1/novaride/operations/payments/investigations",
        headers={**ops_headers, "Idempotency-Key": "idem-investigation"},
        json={"payment_id": "payment_1", "reason": "suspected mismatch"},
    )
    assert investigation_again.status_code == 201
    assert investigation_again.json()["investigation_id"] == investigation_one.json()["investigation_id"]
    investigation_conflict = client.post(
        "/api/v1/novaride/operations/payments/investigations",
        headers={**ops_headers, "Idempotency-Key": "idem-investigation"},
        json={"payment_id": "payment_2", "reason": "suspected mismatch"},
    )
    assert investigation_conflict.status_code == 409

    dispute_one = client.post(
        "/api/v1/novaride/operations/disputes",
        headers={**ops_headers, "Idempotency-Key": "idem-dispute"},
        json={"trip_id": "trip_1", "payment_id": "payment_1"},
    )
    assert dispute_one.status_code == 201
    dispute_again = client.post(
        "/api/v1/novaride/operations/disputes",
        headers={**ops_headers, "Idempotency-Key": "idem-dispute"},
        json={"trip_id": "trip_1", "payment_id": "payment_1"},
    )
    assert dispute_again.status_code == 201
    assert dispute_again.json()["dispute_id"] == dispute_one.json()["dispute_id"]
    dispute_conflict = client.post(
        "/api/v1/novaride/operations/disputes",
        headers={**ops_headers, "Idempotency-Key": "idem-dispute"},
        json={"trip_id": "trip_2", "payment_id": "payment_1"},
    )
    assert dispute_conflict.status_code == 409

    action_one = client.post(
        "/api/v1/novaride/operations/actions",
        headers={**ops_headers, "Idempotency-Key": "idem-action"},
        json={"action_type": "manual_dispatch", "target_id": "trip_1", "reason": "ops review"},
    )
    assert action_one.status_code == 201
    action_again = client.post(
        "/api/v1/novaride/operations/actions",
        headers={**ops_headers, "Idempotency-Key": "idem-action"},
        json={"action_type": "manual_dispatch", "target_id": "trip_1", "reason": "ops review"},
    )
    assert action_again.status_code == 201
    assert action_again.json()["action_id"] == action_one.json()["action_id"]
    action_conflict = client.post(
        "/api/v1/novaride/operations/actions",
        headers={**ops_headers, "Idempotency-Key": "idem-action"},
        json={"action_type": "manual_dispatch", "target_id": "trip_2", "reason": "ops review"},
    )
    assert action_conflict.status_code == 409
