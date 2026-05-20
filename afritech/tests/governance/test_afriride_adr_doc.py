from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/adr/AfriRide_Architecture_Decision_Records.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: GOVERNED ARCHITECTURAL DECISION SURFACE",
    "CLASSIFICATION: ISOLATED ARCHITECTURAL DECISION SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "core invariants",
    "execution legality",
    "identity ontology",
)

ADRS = (
    "ADR-0001 - Replay-Governed Ride Lifecycle",
    "ADR-0002 - Deterministic Driver Matching",
    "ADR-0003 - Django Product Layer Isolation",
    "ADR-0004 - Closed-World Execution Enforcement",
    "ADR-0005 - Documentation Isolation",
    "ADR-0006 - Claim-Evidence-Implementation Binding",
    "ADR-0007 - Continuity Validation as Operational Requirement",
    "ADR-0008 - Replay as Operational Truth Gate",
    "ADR-0009 - CI Authority Compression",
    "ADR-0010 - Observability Isolation",
    "ADR-0011 - Bounded Correctness Classification",
)

REQUIRED_DECISIONS = (
    "Ride lifecycle transitions shall be governed through deterministic lifecycle validation",
    "Driver assignment shall use deterministic matching logic.",
    "AfriRide operational logic shall remain isolated under:",
    "Only declared execution surfaces may participate in operational runtime execution.",
    "Documentation shall remain:",
    "Implemented claims must include:",
    "AfriRide shall support deterministic continuity validation scenarios",
    "Replay validation shall function as the final operational admissibility gate.",
    "Constitutional validation authority shall progressively collapse toward:",
    "Observability layers shall remain:",
    "AfriRide and AfriTech shall classify current validation state as:",
)

FORBIDDEN_BEHAVIORS = (
    "reflection-based execution",
    "dynamic runtime discovery",
    "observer-relative execution",
    "undeclared lifecycle mutation",
)

FORBIDDEN_INFLATION = (
    "global deployment readiness achieved",
    "state-space exhaustiveness achieved",
    "universal fault tolerance achieved",
    "infinite-scale marketplace guarantees achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_adr_doc_has_governed_architectural_decision_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "do not redefine" in text
    for surface in NON_REDEFINED_SURFACES:
        assert surface in text


def test_adr_doc_contains_all_expected_adrs_with_accepted_status() -> None:
    text = read_doc()

    for adr in ADRS:
        assert f"## {adr}" in text

    assert text.count("ACCEPTED") >= len(ADRS)


def test_adr_doc_declares_expected_decisions() -> None:
    text = read_doc()

    for decision in REQUIRED_DECISIONS:
        assert decision in text


def test_adr_doc_preserves_lifecycle_matching_and_closed_world_boundaries() -> None:
    text = read_doc()

    for state in (
        "REQUESTED",
        "MATCHED",
        "ACCEPTED",
        "STARTED",
        "COMPLETED",
        "CANCELLED",
        "FAILED",
    ):
        assert state in text

    assert "identity-safe" in text
    assert "replay-safe" in text
    assert "observer-independent" in text
    for behavior in FORBIDDEN_BEHAVIORS:
        assert behavior in text


def test_adr_doc_preserves_isolation_and_binding_decisions() -> None:
    text = read_doc()

    assert "afriride_system/django_app/" in text
    assert "afritech/" in text
    assert "non-authoritative" in text
    assert "descriptive only" in text
    assert "operationally isolated" in text
    assert "implementation_refs" in text
    assert "implementation_registry.yaml" in text
    assert "claim_discipline_validator.py" in text
    assert "proof admissible" in text


def test_adr_doc_preserves_continuity_replay_ci_and_observability_decisions() -> None:
    text = read_doc()

    for item in (
        "driver dropout",
        "timeout handling",
        "deterministic reassignment",
        "duplicate authority prevention",
        "Replay divergence invalidates admissibility.",
        "1 canonical constitutional pipeline",
        "Supporting validators remain subordinate",
        "observational only",
        "runtime-isolated",
        "Observability failures must not alter lawful ride state.",
    ):
        assert item in text


def test_adr_doc_bounds_current_correctness_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "bounded validated correctness" in lowered
    assert "not universal deployment guarantees" in lowered
    assert "without additional evidence" in lowered

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered

    assert "global deployment readiness" in lowered
    assert "state-space exhaustiveness" in lowered
    assert "universal fault tolerance" in lowered
    assert "infinite-scale marketplace guarantees" in lowered
    assert "under afritech replay-governed constitutional admissibility enforcement" in lowered
