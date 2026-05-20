from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/requirements/AfriRide_Use_Case_Document.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL REQUIREMENTS SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL REQUIREMENTS SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

USE_CASES = (
    "UC-001 - Request Ride",
    "UC-002 - Match Driver",
    "UC-003 - Accept Ride",
    "UC-004 - Start Ride",
    "UC-005 - Complete Ride",
    "UC-006 - Cancel Ride",
    "UC-007 - Fare Estimation",
    "UC-008 - Share ETA",
    "UC-009 - Scheduled Ride",
    "UC-010 - Continuity During Disruption",
)

ACTORS = (
    "Rider",
    "Driver",
    "System",
    "Payment Service",
    "Notification Service",
    "Admin Operator",
)

LIFECYCLE_STATES = (
    "REQUESTED",
    "MATCHED",
    "ACCEPTED",
    "STARTED",
    "COMPLETED",
    "CANCELLED",
    "FAILED",
)

PRESERVED_CONSTRAINTS = (
    "deterministic execution",
    "closed-world execution",
    "canonical identity resolution",
    "replay admissibility",
    "invariant preservation",
    "claim discipline",
)

FORBIDDEN_BEHAVIORS = (
    "redefine constitutional truth",
    "introduce undeclared execution surfaces",
    "permit observer-relative execution",
    "bypass replay enforcement",
)

FORBIDDEN_INFLATION = (
    "global deployment readiness achieved",
    "unrestricted distributed systems readiness achieved",
    "universal validator completeness achieved",
    "production marketplace readiness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_use_case_doc_has_operational_surface_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine constitutional truth" in text
    assert "replay admissibility" in text
    assert "core enforcement semantics" in text
    assert "current proof boundary" in text


def test_use_case_doc_declares_expected_actors() -> None:
    text = read_doc()

    assert "## Primary Actors" in text
    assert "## Secondary Actors" in text
    for actor in ACTORS:
        assert actor in text


def test_use_case_doc_contains_all_core_use_cases() -> None:
    text = read_doc()

    for use_case in USE_CASES:
        assert f"## {use_case}" in text


def test_use_case_doc_preserves_lifecycle_states() -> None:
    text = read_doc()

    for state in LIFECYCLE_STATES:
        assert state in text


def test_use_case_doc_defines_constitutional_constraints() -> None:
    text = read_doc()

    for constraint in PRESERVED_CONSTRAINTS:
        assert constraint in text

    for behavior in FORBIDDEN_BEHAVIORS:
        assert behavior in text


def test_use_case_doc_requires_replay_and_audit_outputs() -> None:
    text = read_doc()

    assert "replay-safe events" in text
    assert "deterministic lifecycle transitions" in text
    assert "immutable audit lineage" in text
    assert "replay reconstruction compatibility" in text


def test_use_case_doc_bounds_continuity_and_product_claims() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "continuity proof admissible within bounded validated scenarios" in lowered
    assert "bounded operational mobility layer" in lowered
    assert "bounded replay-governed mobility coordination surface" in lowered
    assert "validated under deterministic constitutional admissibility constraints" in lowered

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered

    assert "does not claim global deployment readiness" in lowered
    assert "unrestricted distributed systems readiness" in lowered
    assert "universal validator completeness" in lowered
    assert "production marketplace readiness" in lowered
