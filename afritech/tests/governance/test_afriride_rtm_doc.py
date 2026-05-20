from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/requirements/AfriRide_Requirements_Traceability_Matrix.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL TRACEABILITY SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL TRACEABILITY SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "execution legality",
    "core invariants",
)

TRACEABILITY_LINKS = (
    "BRD objectives",
    "SRS requirements",
    "SAD components",
    "SDD design elements",
    "test cases",
    "governance constraints",
)

VALIDATION_COMMANDS = (
    "python3 -m afritech.ci.claim_discipline_validator",
    "python3 -m afritech.ci.constitutional_validation",
    "python3 -m afritech.demo.proof",
    "pytest -q",
)

FORBIDDEN_INFLATION = (
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale marketplace guarantees achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_rtm_has_operational_traceability_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in lowered
    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_rtm_declares_traceability_scope() -> None:
    text = read_doc()

    for link in TRACEABILITY_LINKS:
        assert link in text

    assert "business, software, design, test, and governance requirements" in text


def test_rtm_maps_business_requirements() -> None:
    text = read_doc()

    for row in (
        "| BR-001 | Reliable ride coordination | BRD | RideRequestService, RideLifecycleService | TC-001, TC-013 | Covered |",
        "| BR-002 | Deterministic lifecycle management | BRD / SRS | RideLifecycleService | TC-007-TC-013 | Covered |",
        "| BR-003 | Transparent fare estimation | BRD / SRS | PricingService | TC-018, TC-019 | Covered |",
        "| BR-004 | Operational continuity | BRD / SAD | Continuity validation layer | TC-027-TC-030 | Covered |",
        "| BR-005 | Rider and driver identity integrity | BRD / SRS | Rider, Driver, MatchingService | TC-014, TC-030 | Covered |",
        "| BR-006 | Replay-safe auditability | BRD / SAD | RideEvent, AuditReplayRecord | TC-024-TC-026 | Covered |",
    ):
        assert row in text


def test_rtm_maps_functional_requirements_and_partials() -> None:
    text = read_doc()

    for requirement_id in (
        "FR-001",
        "FR-002",
        "FR-003",
        "FR-004",
        "FR-005",
        "FR-006",
        "FR-007",
        "FR-008",
        "FR-009",
        "FR-010",
        "FR-011",
        "FR-012",
        "FR-013",
        "FR-014",
    ):
        assert f"| {requirement_id} " in text

    for partial in (
        "Future rejection test | Partial",
        "Future ETA test | Partial",
        "Future scheduled ride test | Partial",
    ):
        assert partial in text


def test_rtm_maps_nonfunctional_governance_and_api_requirements() -> None:
    text = read_doc()

    for requirement_id in (
        "NFR-001",
        "NFR-002",
        "NFR-003",
        "NFR-004",
        "NFR-005",
        "NFR-006",
        "NFR-007",
        "GOV-001",
        "GOV-002",
        "GOV-003",
        "GOV-004",
        "API-001",
        "API-002",
    ):
        assert f"| {requirement_id} " in text

    for component in (
        "CLAIM_EVIDENCE_BINDINGS.yaml",
        "implementation_registry.yaml",
        "claim_discipline_validator.py",
        "`POST /api/v1/rides`",
        "`POST /api/v1/rides/{ride_id}/transition`",
    ):
        assert component in text


def test_rtm_declares_coverage_summary_and_partial_followups() -> None:
    text = read_doc()

    for row in (
        "| Business Requirements | 6 | 0 | 0 |",
        "| Functional Requirements | 11 | 3 | 0 |",
        "| Non-Functional Requirements | 7 | 0 | 0 |",
        "| Governance Requirements | 4 | 0 | 0 |",
        "| API Requirements | 2 | 0 | 0 |",
    ):
        assert row in text

    for follow_up in (
        "Add driver rejection lifecycle test",
        "Add ETA sharing token/test",
        "Add scheduled ride activation test",
    ):
        assert follow_up in text


def test_rtm_preserves_governance_traceability_rules() -> None:
    text = read_doc()

    assert "claim\n-> evidence\n-> implementation_refs" in text
    assert "-> implementation_registry\n-> admissibility validation\n-> CI enforcement" in text

    for rule in (
        "every implemented claim must have evidence",
        "every implemented claim must reference implementation",
        "referenced implementation must be IMPLEMENTED",
        "referenced implementation must be replay admissible",
        "referenced implementation must be proof admissible",
        "referenced implementation must be deterministic",
    ):
        assert rule in text


def test_rtm_declares_validation_commands_and_acceptance_criteria() -> None:
    text = read_doc()

    for command in VALIDATION_COMMANDS:
        assert command in text

    for criterion in (
        "all critical requirements map to test cases",
        "all implemented claims map to implementation registry entries",
        "all governance tests pass",
        "all replay and continuity requirements remain bounded",
        "all documentation surfaces remain non-authoritative",
    ):
        assert criterion in text


def test_rtm_has_safe_final_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "bounded requirement-to-test coverage" in lowered
    assert "replay-governed mobility coordination" in lowered
    assert "under afritech constitutional" in lowered
    assert "admissibility constraints" in lowered
