from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/architecture/AfriRide_Data_Dictionary_and_Database_Schema.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL DATA DESIGN SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL DATA DESIGN SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

ENTITIES = (
    "Rider",
    "Driver",
    "Vehicle",
    "Ride",
    "RideEvent",
    "FareEstimate",
    "Payment",
    "Notification",
    "ScheduledRide",
    "AuditReplayRecord",
)

RIDE_STATUSES = (
    "REQUESTED",
    "MATCHED",
    "ACCEPTED",
    "STARTED",
    "COMPLETED",
    "CANCELLED",
    "FAILED",
)

EVENT_TYPES = (
    "ride_created",
    "driver_matched",
    "ride_accepted",
    "ride_started",
    "ride_completed",
    "ride_cancelled",
    "ride_failed",
    "fare_estimated",
    "payment_authorized",
    "payment_completed",
    "notification_sent",
    "continuity_recovered",
)

RELATIONSHIPS = (
    "Rider 1 -> many Ride",
    "Driver 1 -> many Ride",
    "Driver 1 -> many Vehicle",
    "Ride 1 -> many RideEvent",
    "Ride 1 -> one/many FareEstimate",
    "Ride 1 -> one/many Payment",
    "Ride 1 -> many Notification",
    "Ride 1 -> one/many AuditReplayRecord",
    "Rider 1 -> many ScheduledRide",
)

MUST_PRESERVE = (
    "canonical identity",
    "deterministic lifecycle lineage",
    "replay-safe event history",
    "immutable operational audit trail",
    "closed-world execution boundaries",
)

MUST_NOT = (
    "treat UI state as authoritative truth",
    "allow undocumented lifecycle states",
    "mutate completed ride lineage silently",
    "bypass replay/audit event generation",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_data_schema_doc_has_operational_data_design_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine AfriTech constitutional truth" in text
    assert "replay authority" in text
    assert "core admissibility law" in text


def test_data_schema_doc_declares_core_entities() -> None:
    text = read_doc()

    for entity in ENTITIES:
        assert entity in text
        assert f"## 2." in text


def test_data_schema_doc_includes_required_schema_fields() -> None:
    text = read_doc()

    for field in (
        "rider_id",
        "driver_id",
        "make",
        "model",
        "license_plate",
        "ride_id",
        "fare_estimate_id",
        "event_id",
        "previous_status",
        "new_status",
        "payment_id",
        "provider_reference",
        "notification_id",
        "scheduled_time",
        "replay_hash",
        "replay_status",
    ):
        assert field in text


def test_data_schema_doc_preserves_relationships_statuses_and_events() -> None:
    text = read_doc()

    for relationship in RELATIONSHIPS:
        assert relationship in text

    for status in RIDE_STATUSES:
        assert status in text

    for event_type in EVENT_TYPES:
        assert event_type in text


def test_data_schema_doc_preserves_constraints_and_forbidden_behaviors() -> None:
    text = read_doc()

    for constraint in MUST_PRESERVE:
        assert constraint in text

    for forbidden in MUST_NOT:
        assert forbidden in text


def test_data_schema_doc_bounds_final_classification() -> None:
    text = read_doc()

    assert "bounded operational persistence design" in text
    assert "supporting deterministic ride coordination" in text
    assert "replay-safe auditability" in text
    assert "AfriTech constitutional admissibility constraints" in text
