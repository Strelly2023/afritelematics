from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from afritech.api.app import app


def _issue_token(client: TestClient, *, role: str = "OPERATOR") -> str:
    response = client.post(
        "/v1/auth/token",
        json={
            "user_id": "schema-registry-operator",
            "role": role,
            "organization_id": "org-novaride",
        },
    )
    assert response.status_code == 200
    return response.json()["token"]


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _valid_event() -> dict[str, object]:
    ride_id = f"ride-{uuid4().hex[:12]}"
    return {
        "event_id": f"event-{uuid4().hex}",
        "event_type": "ride.requested.v1",
        "schema_version": 1,
        "occurred_at": _now(),
        "recorded_at": _now(),
        "tenant_id": "tenant-novaride",
        "organization_id": "org-novaride",
        "subject": {"type": "passenger", "id": "passenger-1"},
        "actor": {"type": "customer_app", "id": "passenger-1", "role": "CUSTOMER"},
        "resource": {"type": "ride", "id": ride_id},
        "correlation_id": f"corr-{uuid4().hex}",
        "causation_id": f"cause-{uuid4().hex}",
        "idempotency_key": f"idem-{uuid4().hex}",
        "sequence": 1,
        "partition_key": ride_id,
        "source": "rider-app",
        "visibility": "tenant",
        "decision_trace": {
            "policy_id": "policy.dispatch.001",
            "policy_version": "2026.06",
            "rule_ids": ["TRUST-001", "DISPATCH-002"],
            "flag_evaluations": {"phase13.execution.enabled": {"enabled": True}},
            "evaluation_result": "ALLOW",
        },
        "schema_ref": {
            "registry_id": "NOVARIDE_EVENT_REGISTRY_V1",
            "document_id": "ride.requested.v1",
            "revision": "1",
        },
        "payload": {
            "ride_id": ride_id,
            "passenger_id": "passenger-1",
            "organization_id": "org-novaride",
            "pickup_location": {"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            "destination_location": {"lat": -37.818, "lng": 144.956},
            "requested_at": _now(),
            "currency": "AUD",
            "fare_estimate": "18.40",
            "status": "requested",
        },
    }


def test_schema_registry_api_exposes_schema_and_validation() -> None:
    client = TestClient(app)
    token = _issue_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    schema_response = client.get(
        "/v1/contracts/events/registry/ride.requested.v1/schema",
        headers=headers,
    )
    assert schema_response.status_code == 200
    schema_payload = schema_response.json()
    assert schema_payload["event_type"] == "ride.requested.v1"
    assert schema_payload["schema"]["properties"]["event_type"]["const"] == "ride.requested.v1"
    assert schema_payload["certification"]["certified"] is True

    validate_response = client.post(
        "/v1/contracts/events/validate",
        headers=headers,
        json={"event": _valid_event()},
    )
    assert validate_response.status_code == 200
    validate_payload = validate_response.json()
    assert validate_payload["all_valid"] is True
    assert validate_payload["accepted"][0]["event_type"] == "ride.requested.v1"

    compatibility_response = client.post(
        "/v1/contracts/events/compatibility",
        headers=headers,
        json={
            "previous_event_type": "ride.requested.v1",
            "current_event_type": "trip.completed.v1",
        },
    )
    assert compatibility_response.status_code == 200
    compatibility = compatibility_response.json()
    assert "breaking_changes" in compatibility


def test_schema_registry_middleware_rejects_invalid_event_payload() -> None:
    client = TestClient(app)
    token = _issue_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    invalid = _valid_event()
    invalid["schema_ref"] = {
        "registry_id": "WRONG_REGISTRY",
        "document_id": "ride.requested.v1",
        "revision": "1",
    }

    response = client.post(
        "/v1/contracts/events/publish",
        headers=headers,
        json={"event": invalid},
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "SCHEMA_CONTRACT_REJECTED"


def test_schema_registry_publish_path_admits_valid_event() -> None:
    client = TestClient(app)
    token = _issue_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/v1/contracts/events/publish",
        headers=headers,
        json={"event": _valid_event()},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "admitted"
    assert payload["admission"]["mode"] == "single"
