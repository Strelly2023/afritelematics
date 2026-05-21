from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_Real_World_Mobility_Transition_Plan.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: REAL-WORLD MOBILITY TRANSITION ROADMAP",
    "CLASSIFICATION: ISOLATED OPERATIONAL HARDENING SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "replay admissibility",
    "execution legality",
    "core invariants",
    "identity ontology",
    "claim admissibility",
    "production deployment proof",
    "multi-region readiness proof",
)

PHASES = (
    "Phase 1 - Controlled Realism",
    "Phase 2 - Distributed Deterministic Runtime",
    "Phase 3 - Real-World Interface Layer",
    "Phase 4 - Market-Scale Chaos Validation",
)

FUTURE_SURFACES = (
    "ecosystems.afriride.geo.engine",
    "ecosystems.afriride.client.mobile_model",
    "ecosystems.afriride.market.engine",
    "afritech.distributed.network_model",
    "afritech.distributed.convergence",
    "afritech.execution.partition.fabric",
    "afritech.api.gateway.public_edges",
)

INVARIANT_CLASSES = (
    "Geo-Consistency Invariant",
    "Economic Fairness Invariant",
    "Distributed Consistency Invariant",
    "Edge Normalization Invariant",
)

FORBIDDEN_INFLATION = (
    "real-world mobility network readiness achieved",
    "controlled realism layer implemented",
    "distributed deterministic runtime proven",
    "real-world interface layer deployed",
    "market-scale chaos validation achieved",
    "geo-consistency invariant implemented",
    "economic fairness invariant implemented",
    "distributed consistency invariant implemented",
    "edge normalization invariant fully proven",
    "1m concurrent ride events validated",
    "controlled city pilot completed",
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_transition_plan_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not runtime authority" in lowered
    assert "not evidence that AfriRide has already proven real-world mobility operation under scale".lower() in lowered
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    before_non_claims = lowered.split("# 9. bounded non-claims")[0]
    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in before_non_claims


def test_transition_plan_declares_master_principle_and_phase_model() -> None:
    text = read_doc()

    assert "Expand only by proving new domains." in text
    assert "Do not expand by merely adding features." in text

    for phase in PHASES:
        assert phase in text

    for required_capability in (
        "declared surface",
        "deterministic contract",
        "recorded input model",
        "replay validation",
        "witness coverage",
        "claim boundary",
        "counter-test",
        "CI enforcement",
    ):
        assert required_capability in text


def test_transition_plan_declares_future_surfaces_and_constraints() -> None:
    text = read_doc()

    for surface in FUTURE_SURFACES:
        assert surface in text

    for realism_constraint in (
        "no unseeded randomness",
        "all location updates replayable",
        "client timestamps are observational",
        "pricing rules are pure functions over recorded state",
        "no hidden business logic",
    ):
        assert realism_constraint in text

    assert "These are future surfaces until implementation registry entries" in text


def test_transition_plan_defines_distributed_and_edge_expansion() -> None:
    text = read_doc()

    for distributed_requirement in (
        "multi-node execution clusters",
        "deterministic partition ownership",
        "replay-stable scheduling",
        "worker crash recovery",
        "cross-partition replay verification",
        "duplicate authority prevention",
    ):
        assert distributed_requirement in text

    for edge_requirement in (
        "GPS ingestion adapter",
        "mobile action adapter",
        "map provider response adapter",
        "timestamp normalization",
        "coordinate smoothing",
        "duplicate rejection",
        "source adapter version binding",
    ):
        assert edge_requirement in text

    assert "API is not source of truth" in text


def test_transition_plan_defines_chaos_validation_and_pilot_constraints() -> None:
    text = read_doc()

    for chaos_item in (
        "100K concurrent rides",
        "1M concurrent ride events",
        "malicious_event_injection",
        "duplicate_acceptance_attack",
        "driver_identity_spoof",
        "queue_poisoning",
        "driver shortages",
        "cancellation waves",
        "one city",
        "controlled drivers",
        "production == replay-verifiable",
    ):
        assert chaos_item in text


def test_transition_plan_defines_new_invariants_and_approval_gates() -> None:
    text = read_doc()

    for invariant in INVARIANT_CLASSES:
        assert invariant in text

    for invariant_statement in (
        "location evolution must be physically plausible",
        "no actor can exploit system beyond defined rules",
        "all partitions converge to canonical state",
        "raw external data must never enter runtime without normalization",
    ):
        assert invariant_statement in text

    for gate in (
        "CLAIM",
        "EVIDENCE",
        "VALIDATOR",
        "COUNTER-TEST",
        "CI ENFORCEMENT",
        "No claim without evidence.",
        "No phase graduation without CI enforcement.",
        "afritech.ci.scale_validator",
    ):
        assert gate in text


def test_transition_plan_preserves_final_architectural_boundary() -> None:
    text = read_doc()

    assert "deterministic core" in text
    assert "normalized non-deterministic edge" in text
    assert "distributed replay-verifiable execution fabric" in text
    assert "Reality must be approximated." in text
    assert "Execution must remain deterministic." in text
