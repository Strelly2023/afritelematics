from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/implementation/AfriRide_GA_Elite_Implementation_Plan.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: IMPLEMENTATION PLAN",
    "CLASSIFICATION: ISOLATED OPERATIONAL IMPLEMENTATION SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

CURRENT_FOUNDATION_ITEMS = (
    "deterministic runtime",
    "replay engine",
    "invariant enforcement",
    "four-gate validator",
    "enforcement-integrity validator",
    "constitutional validation pipeline",
    "proof surface",
    "bounded AfriRide continuity proof behavior",
)

PLANNED_PHASE_HEADINGS = (
    "## Phase 1 - Mobility Core Kernel",
    "## Phase 2 - Ride Lifecycle Engine",
    "## Phase 3 - Marketplace and Pricing Layer",
    "## Phase 4 - Rider Experience Layer",
    "## Phase 5 - Safety and Support Systems",
)

PHASE_SECTION_BOUNDARIES = (
    ("## Phase 1 - Mobility Core Kernel", "## Phase 2 - Ride Lifecycle Engine"),
    ("## Phase 2 - Ride Lifecycle Engine", "## Phase 3 - Marketplace and Pricing Layer"),
    ("## Phase 3 - Marketplace and Pricing Layer", "## Phase 4 - Rider Experience Layer"),
    ("## Phase 4 - Rider Experience Layer", "## Phase 5 - Safety and Support Systems"),
    ("## Phase 5 - Safety and Support Systems", "## Phase 6 - Ecosystem Expansion"),
)

VALIDATION_COMMANDS = (
    "python3 -m afritech.ci.enforcement_integrity_validator",
    "python3 -m afritech.ci.four_gate_validator",
    "python3 -m afritech.demo.proof",
    "python3 -m afritech.ci.constitutional_validation",
)

DRIFT_REJECTION_ITEMS = (
    "randomness as core authority",
    "replay inconsistency",
    "validator bypass",
    "UI logic as truth",
    "API logic as core decision authority",
    "undocumented state mutation",
    "hidden execution paths",
    "proof-scope expansion",
)

FORBIDDEN_INFLATION = (
    "currently deployed consumer marketplace",
    "global deployment readiness achieved",
    "implemented rider marketplace",
    "active global ride operations",
    "probabilistic matching allowed",
    "dynamic surge pricing allowed",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def test_implementation_plan_has_isolated_operational_status() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not define proof truth" in text
    assert "does not claim global deployment readiness" in text
    assert "Implementation planning must preserve or isolate all claims." in text


def test_implementation_plan_preserves_two_plane_boundary() -> None:
    text = read_doc()

    assert "Plane 1: Constitutional Core (AfriTech) -> PRESERVE" in text
    assert "Plane 2: Product and Operations (AfriRide) -> ISOLATE" in text
    assert "The constitutional core is a protected surface." in text
    assert "Product and operational work may evolve only while remaining fully external" in text


def test_phase_zero_is_current_foundation_and_later_phases_are_not_current() -> None:
    text = read_doc()
    phase_zero = section(text, "## Phase 0 - Constitutional Foundation", "## Phase 1 - Mobility Core Kernel")

    assert "Status: [Implemented / In Development]" in phase_zero
    for item in CURRENT_FOUNDATION_ITEMS:
        assert item in phase_zero

    for heading, next_heading in PHASE_SECTION_BOUNDARIES:
        phase = section(text, heading, next_heading)
        assert "Status: [Planned]" in phase

    phase_six = section(text, "## Phase 6 - Ecosystem Expansion", "## Implementation Architecture View")
    assert "Status: [Exploratory]" in phase_six
    assert "isolated ecosystem expansion candidates" in phase_six


def test_implementation_plan_requires_validator_and_proof_gates() -> None:
    text = read_doc()
    validation = section(text, "## Mandatory Validation Integration", "## Drift Detection Rules")

    for command in VALIDATION_COMMANDS:
        assert command in validation

    assert "Phase claims remain invalid until the relevant implementation and tests pass." in validation


def test_implementation_plan_rejects_drift_vectors() -> None:
    text = read_doc()
    drift = section(text, "## Drift Detection Rules", "## Delivery Model")

    for item in DRIFT_REJECTION_ITEMS:
        assert item in drift


def test_implementation_plan_encodes_replay_before_admission() -> None:
    text = read_doc()

    assert "If a feature cannot be replay-verified," in text
    assert "it is not part of AfriRide's admitted execution surface." in text
    assert "executable system" in text
    assert "replay-valid traces" in text
    assert "passing validators" in text
    assert "bounded claims" in text


def test_implementation_plan_keeps_dfm_non_authoritative() -> None:
    text = read_doc()
    dfm = section(text, "## DFM Integration", "## Final Implementation Truth")

    assert "operations optimize reproducibility" in dfm
    assert "but never redefine admissibility" in dfm
    assert "These tools are DFM surfaces." in dfm
    assert "without acquiring authority over admissibility" in dfm


def test_implementation_plan_preserves_proof_boundary_and_avoids_inflation() -> None:
    text = read_doc()

    assert "does not modify `afritech.demo.proof`" in text
    assert "does not expand proof scope beyond the bounded AfriRide domain" in text
    assert "does not claim global deployment readiness" in text
    assert "deployed consumer marketplace" in text
    assert "implemented rider features beyond the current validator-backed system surface" in text

    lowered = text.lower()
    for claim in FORBIDDEN_INFLATION:
        assert claim not in lowered
