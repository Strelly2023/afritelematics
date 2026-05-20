from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/requirements/AfriRide_Business_Requirements_Document.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL REQUIREMENTS SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL REQUIREMENTS SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

BUSINESS_OBJECTIVES = (
    "BO-001 - Reliable Ride Coordination",
    "BO-002 - Deterministic Lifecycle Management",
    "BO-003 - Transparent Pricing",
    "BO-004 - Operational Continuity",
    "BO-005 - Identity Integrity",
    "BO-006 - Replay-Safe Auditability",
)

FUNCTIONAL_REQUIREMENTS = (
    "FR-001 - Ride Request Creation",
    "FR-002 - Driver Matching",
    "FR-003 - Ride Lifecycle Transitions",
    "FR-004 - Fare Estimation",
    "FR-005 - Ride Cancellation",
    "FR-006 - ETA Sharing",
    "FR-007 - Scheduled Rides",
    "FR-008 - Notifications",
    "FR-009 - Replay Auditability",
    "FR-010 - Continuity Recovery",
)

NON_FUNCTIONAL_REQUIREMENTS = (
    "NFR-001 - Deterministic Execution",
    "NFR-002 - Replay Admissibility",
    "NFR-003 - Closed-World Enforcement",
    "NFR-004 - Identity Integrity",
    "NFR-005 - Audit Visibility",
    "NFR-006 - Failure Containment",
)

EXCLUDED_SCOPE = (
    "global dispatch optimization",
    "fully autonomous fleet management",
    "real-time dynamic surge prediction",
    "cross-market regulatory automation",
    "unbounded distributed marketplace scaling",
)

MUST_PRESERVE = (
    "replay admissibility",
    "deterministic execution",
    "canonical identity semantics",
    "constitutional boundaries",
    "invariant preservation",
)

MUST_NOT = (
    "introduce undeclared runtime surfaces",
    "permit observer-relative execution",
    "bypass replay validation",
    "mutate constitutional truth",
)

FORBIDDEN_INFLATION = (
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "state-space exhaustiveness achieved",
    "infinite-scale marketplace guarantees achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_brd_has_operational_surface_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in text
    assert "constitutional truth" in text
    assert "replay admissibility" in text
    assert "core invariants" in text
    assert "execution legality" in text


def test_brd_contains_business_objectives() -> None:
    text = read_doc()

    for objective in BUSINESS_OBJECTIVES:
        assert objective in text


def test_brd_contains_functional_and_non_functional_requirements() -> None:
    text = read_doc()

    for requirement in FUNCTIONAL_REQUIREMENTS:
        assert requirement in text

    for requirement in NON_FUNCTIONAL_REQUIREMENTS:
        assert requirement in text


def test_brd_bounds_scope_and_excludes_unvalidated_claims() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "outside current validated scope" in lowered
    for item in EXCLUDED_SCOPE:
        assert item in lowered

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered

    assert "global deployment readiness" in lowered
    assert "universal fault tolerance" in lowered
    assert "state-space exhaustiveness" in lowered
    assert "infinite-scale marketplace guarantees" in lowered


def test_brd_preserves_operational_constraints() -> None:
    text = read_doc()

    for constraint in MUST_PRESERVE:
        assert constraint in text

    for forbidden in MUST_NOT:
        assert forbidden in text


def test_brd_declares_success_criteria_and_final_classification() -> None:
    text = read_doc()

    assert "ride flows execute successfully" in text
    assert "deterministic replay succeeds" in text
    assert "continuity validation passes" in text
    assert "constitutional validation passes" in text
    assert "claim-evidence binding remains valid" in text
    assert "bounded validated correctness" in text
    assert "bounded replay-governed mobility coordination platform" in text
    assert "validated deterministic lifecycle behavior" in text
