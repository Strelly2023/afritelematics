from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/architecture/AfriRide_System_Architecture_Document.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL ARCHITECTURE SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL ARCHITECTURE SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "core admissibility law",
    "replay authority",
    "identity ontology",
    "execution legality",
)

ARCHITECTURAL_LAYERS = (
    "Layer 1 - Constitutional Core (AfriTech)",
    "Layer 2 - AfriRide Operational Layer",
    "Layer 3 - Interface and Observability Layer",
)

COMPONENTS = (
    "Ride Request Service",
    "Matching Service",
    "Ride Lifecycle Service",
    "Pricing Service",
    "Notification Service",
    "Payment Coordination Service",
    "Replay and Audit Services",
)

EXECUTION_FLOWS = (
    "Ride Request Flow",
    "Driver Matching Flow",
    "Ride Lifecycle Flow",
    "Continuity Recovery Flow",
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

PRESERVED_PRINCIPLES = (
    "deterministic execution",
    "replay admissibility",
    "closed-world execution",
    "canonical identity resolution",
    "invariant preservation",
    "claim discipline",
)

FORBIDDEN_BEHAVIORS = (
    "observer-relative execution",
    "reflection-based runtime discovery",
    "undeclared execution surfaces",
    "probabilistic lifecycle mutation",
    "filesystem-derived authority",
)

FORBIDDEN_INFLATION = (
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale operational guarantees achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_sad_has_operational_architecture_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in text
    for surface in NON_REDEFINED_SURFACES:
        assert surface in text


def test_sad_declares_scope_and_exclusions() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "a bounded replay-governed mobility coordination architecture" in text
    assert "ride request orchestration" in lowered
    assert "continuity validation" in lowered
    assert "global marketplace scaling guarantees" in lowered
    assert "autonomous dispatch intelligence" in lowered
    assert "infinite-scale distributed consensus" in lowered
    assert "unbounded dynamic optimization" in lowered


def test_sad_preserves_architectural_principles_and_forbids_drift() -> None:
    text = read_doc()

    for principle in PRESERVED_PRINCIPLES:
        assert principle in text

    for behavior in FORBIDDEN_BEHAVIORS:
        assert behavior in text


def test_sad_defines_layers_components_and_flows() -> None:
    text = read_doc()

    for layer in ARCHITECTURAL_LAYERS:
        assert layer in text

    for component in COMPONENTS:
        assert component in text

    for flow in EXECUTION_FLOWS:
        assert flow in text


def test_sad_preserves_lifecycle_and_data_architecture() -> None:
    text = read_doc()

    for state in VALID_STATES:
        assert state in text

    for field in ("ride_id", "rider_id", "driver_id", "origin", "destination", "status"):
        assert field in text

    for field in ("availability", "vehicle_data", "profile", "payment_reference"):
        assert field in text


def test_sad_defines_deployment_api_and_documentation_boundaries() -> None:
    text = read_doc()

    assert "afriride_system/django_app/" in text
    assert "afritech/" in text
    assert "docs/" in text
    assert "api/v1/ride/" in text
    assert "non-authoritative" in text
    assert "descriptive only" in text
    assert "isolated from proof truth" in text
    assert "bypass lifecycle legality" in text
    assert "mutate replay lineage" in text
    assert "introduce undeclared state" in text


def test_sad_declares_security_continuity_testing_and_claim_binding() -> None:
    text = read_doc()

    assert "canonical module-path ontology" in text
    assert "Replay divergence invalidates admissibility" in text
    assert "evidence binding" in text
    assert "implementation registry linkage" in text
    assert "proof admissibility" in text
    assert "duplicate authority prevention" in text
    assert "adversarial mutation testing" in text


def test_sad_bounds_operational_claims() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "bounded deterministic correctness" in lowered
    assert "bounded replay-governed mobility coordination architecture" in lowered
    assert "validated deterministic lifecycle execution and continuity verification" in lowered

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered

    assert "global deployment readiness" in lowered
    assert "universal fault tolerance" in lowered
    assert "complete state-space exhaustiveness" in lowered
    assert "infinite-scale operational guarantees" in lowered
