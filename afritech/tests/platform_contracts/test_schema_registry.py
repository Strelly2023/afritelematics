from __future__ import annotations

import copy
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from afritech.platform_contracts.schema_registry import (
    SchemaRegistry,
    SchemaRegistryError,
    build_schema_registry,
)


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _valid_ride_requested_event() -> dict[str, object]:
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


def test_schema_registry_generates_schema_and_certs_events() -> None:
    registry = build_schema_registry()

    schema = registry.generate_json_schema("ride.requested.v1")
    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["properties"]["event_type"]["const"] == "ride.requested.v1"
    assert schema["properties"]["decision_trace"]["required"] == [
        "policy_id",
        "policy_version",
        "rule_ids",
        "flag_evaluations",
        "evaluation_result",
    ]

    certification = registry.certification_check("ride.requested.v1")
    assert certification["certified"] is True
    assert certification["publication"]["signature"]["scheme"] == "ed25519"


def test_schema_registry_validates_event_and_enforces_registry_lookup() -> None:
    registry = build_schema_registry()
    event = _valid_ride_requested_event()

    result = registry.validate_event(event)
    assert result["valid"] is True
    assert result["schema_version"] == 1

    broken = copy.deepcopy(event)
    broken["schema_ref"]["registry_id"] = "WRONG"
    with pytest.raises(SchemaRegistryError, match="registry_lookup_enforcement_failed"):
        registry.validate_event(broken)


def test_schema_registry_requires_certification_before_runtime_admission(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = build_schema_registry()
    event = _valid_ride_requested_event()

    monkeypatch.setattr(
        "afritech.platform_contracts.schema_registry.verify_packet_signature",
        lambda *args, **kwargs: False,
    )

    with pytest.raises(SchemaRegistryError, match="schema_not_certified"):
        registry.validate_event(event)


def test_schema_registry_compatibility_detects_breaking_change() -> None:
    registry = SchemaRegistry()
    previous = registry.generate_json_schema("ride.requested.v1")
    current = copy.deepcopy(previous)
    current["required"] = list(previous["required"]) + ["new_required_field"]
    current["properties"]["new_required_field"] = {"type": "string"}

    report = registry.compare_schemas(previous, current)

    assert report.backward_compatible is False
    assert any("added_required" in change or "required_added" in change for change in report.breaking_changes)
