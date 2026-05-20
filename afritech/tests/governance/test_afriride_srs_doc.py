from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/requirements/AfriRide_Software_Requirements_Specification.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL SOFTWARE REQUIREMENTS SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL REQUIREMENTS SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

FUNCTIONAL_REQUIREMENTS = (
    "FR-001 - Create Ride Intent",
    "FR-002 - Validate Ride Request",
    "FR-003 - Deterministic Driver Matching",
    "FR-004 - Ride Acceptance",
    "FR-005 - Ride Rejection",
    "FR-006 - Ride Start",
    "FR-007 - Ride Completion",
    "FR-008 - Ride Cancellation",
    "FR-009 - Fare Estimation",
    "FR-010 - ETA Sharing",
    "FR-011 - Scheduled Rides",
    "FR-012 - Notification Delivery",
    "FR-013 - Replay Reconstruction",
    "FR-014 - Continuity Recovery",
)

NON_FUNCTIONAL_REQUIREMENTS = (
    "NFR-001 - Determinism",
    "NFR-002 - Replay Safety",
    "NFR-003 - Identity Integrity",
    "NFR-004 - Closed-World Enforcement",
    "NFR-005 - Audit Visibility",
    "NFR-006 - Failure Containment",
    "NFR-007 - Observational Isolation",
)

COMPONENTS = (
    "Rider Services",
    "Driver Services",
    "Matching Services",
    "Lifecycle Services",
    "Pricing Services",
    "Notification Services",
    "Replay and Audit Services",
)

VALID_STATES = (
    "REQUESTED",
    "MATCHED",
    "ACCEPTED",
    "STARTED",
    "COMPLETED",
    "CANCELLED",
    "FAILED",
)

VALID_TRANSITIONS = (
    "REQUESTED -> MATCHED",
    "MATCHED -> ACCEPTED",
    "ACCEPTED -> STARTED",
    "STARTED -> COMPLETED",
    "REQUESTED -> CANCELLED",
    "MATCHED -> CANCELLED",
    "ACCEPTED -> CANCELLED",
)

API_ENDPOINTS = (
    "POST /api/v1/rides",
    "GET /api/v1/rides/{ride_id}",
    "POST /api/v1/rides/{ride_id}/transition",
)

FORBIDDEN_INFLATION = (
    "global marketplace readiness achieved",
    "universal fault tolerance achieved",
    "state-space exhaustiveness achieved",
    "infinite-scale dispatch guarantees achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_srs_has_software_requirements_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in text
    assert "constitutional truth" in text
    assert "replay admissibility" in text
    assert "execution legality" in text
    assert "core invariants" in text
    assert "identity ontology" in text


def test_srs_declares_scope_perspective_and_components() -> None:
    text = read_doc()

    assert "bounded replay-governed mobility coordination surface" in text
    assert "a product-layer execution surface" in text
    assert "Core truth and admissibility remain governed" in text
    for component in COMPONENTS:
        assert component in text


def test_srs_contains_functional_and_non_functional_requirements() -> None:
    text = read_doc()

    for requirement in FUNCTIONAL_REQUIREMENTS:
        assert requirement in text

    for requirement in NON_FUNCTIONAL_REQUIREMENTS:
        assert requirement in text


def test_srs_preserves_lifecycle_model() -> None:
    text = read_doc()

    for state in VALID_STATES:
        assert state in text

    for transition in VALID_TRANSITIONS:
        assert transition in text


def test_srs_declares_data_and_api_requirements() -> None:
    text = read_doc()

    for field in ("ride_id", "rider_id", "driver_id", "origin", "destination"):
        assert field in text

    for field in ("availability_status", "vehicle_information", "profile_information"):
        assert field in text

    for endpoint in API_ENDPOINTS:
        assert endpoint in text


def test_srs_includes_replay_audit_and_testing_requirements() -> None:
    text = read_doc()

    assert "replay-safe events" in text
    assert "deterministic lifecycle lineage" in text
    assert "immutable audit visibility" in text
    assert "replay reconstruction compatibility" in text

    for test_surface in (
        "unit testing",
        "integration testing",
        "continuity validation",
        "replay validation",
        "constitutional validation",
        "adversarial mutation testing",
    ):
        assert test_surface in text


def test_srs_bounds_operational_claims() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "bounded deterministic correctness" in lowered
    assert "bounded replay-governed mobility coordination software system" in lowered
    assert "validated deterministic lifecycle execution" in lowered

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered

    assert "global marketplace readiness" in lowered
    assert "universal fault tolerance" in lowered
    assert "state-space exhaustiveness" in lowered
    assert "infinite-scale dispatch guarantees" in lowered
