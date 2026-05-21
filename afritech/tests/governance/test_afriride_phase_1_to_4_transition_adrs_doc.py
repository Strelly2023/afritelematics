from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/adr/AfriRide_Phase_1_to_4_Production_Transition_ADRs.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: PROPOSED ARCHITECTURAL TRANSITION SURFACE",
    "CLASSIFICATION: ISOLATED FUTURE EXECUTION TOPOLOGY SURFACE",
    "GOVERNANCE MODE: ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> CI",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "replay admissibility",
    "core invariants",
    "execution legality",
    "identity ontology",
    "claim admissibility",
    "production deployment proof",
)

ADRS = (
    "ADR-101 - Deterministic Geo-Spatial Execution Layer",
    "ADR-102 - Deterministic Mobile Client Replay Model",
    "ADR-103 - Deterministic Economic Simulation Engine",
    "ADR-201 - Deterministic Multi-Node Execution Fabric",
    "ADR-202 - Deterministic Network Simulation Model",
    "ADR-203 - Deterministic Cross-Partition Convergence",
    "ADR-301 - Edge Adapter Normalization Boundary",
    "ADR-302 - Deterministic Normalization Pipeline",
    "ADR-303 - Public API Gateway Isolation",
    "ADR-401 - Deterministic Load Simulation Framework",
    "ADR-402 - Adversarial Integrity Enforcement",
    "ADR-403 - Economic Fairness Invariant Enforcement",
    "ADR-404 - Controlled Real-World Pilot Deployment",
)

PHASES = (
    "Phase 1 - Controlled Realism",
    "Phase 2 - Distributed Deterministic Runtime",
    "Phase 3 - Real-World Interface Layer",
    "Phase 4 - Chaos and Market-Scale Validation",
)

PROPOSED_SURFACES = (
    "ecosystems.afriride.geo.engine",
    "ecosystems.afriride.geo.route_model",
    "ecosystems.afriride.geo.drift_simulator",
    "ecosystems.afriride.client.mobile_model",
    "ecosystems.afriride.client.sync_engine",
    "ecosystems.afriride.market.engine",
    "ecosystems.afriride.market.pricing_model",
    "afritech.execution.cluster",
    "afritech.execution.node",
    "afritech.execution.scheduler",
    "afritech.execution.partition.fabric",
    "afritech.distributed.network_model",
    "afritech.distributed.simulated_transport",
    "afritech.distributed.convergence",
    "afritech.distributed.merge_engine",
    "afritech.edge.adapter.runtime_adapter",
    "afritech.edge.ingestion.queue_ingestor",
    "afritech.edge.normalization.normalizer",
    "afritech.api.gateway.public_edges",
    "afritech.simulation.load.engine",
    "afritech.security.adversarial_engine",
    "ecosystems.afriride.market.fairness_engine",
    "ecosystems.afriride.runtime.production_adapter",
)

VALIDATORS = (
    "afritech.ci.geo_determinism_validator",
    "afritech.ci.mobile_replay_validator",
    "afritech.ci.market_determinism_validator",
    "afritech.ci.distributed_execution_validator",
    "afritech.ci.network_determinism_validator",
    "afritech.ci.convergence_validator",
    "afritech.ci.edge_input_validator",
    "afritech.ci.normalization_validator",
    "afritech.ci.api_boundary_validator",
    "afritech.ci.scale_validator",
    "afritech.ci.security_validator",
    "afritech.ci.fairness_validator",
    "afritech.ci.production_validator",
)

INVARIANTS = (
    "Geo-Consistency Invariant",
    "Economic Fairness Invariant",
    "Distributed Consistency Invariant",
    "Edge Normalization Invariant",
)

COUNTER_TESTS = (
    "inject_route_drift_variance",
    "inject_non_deterministic_gps_noise",
    "inject_clock_skew",
    "inject_out_of_order_events",
    "inject_surge_race_conditions",
    "inject_worker_reordering",
    "inject_concurrent_execution_race",
    "inject_random_latency",
    "inject_non_replayable_packet_loss",
    "inject_conflicting_partition_acceptance",
    "bypass_normalization_layer",
    "inject_direct_state_mutation_attempt",
    "inject_queue_saturation",
    "inject_duplicate_acceptance",
    "inject_forged_identity",
    "inject_bias_exploitation_scenario",
    "inject_real_world_divergence",
)

FORBIDDEN_INFLATION = (
    "controlled realism implemented",
    "geo-spatial execution implemented",
    "mobile client replay implemented",
    "economic simulation implemented",
    "distributed runtime implemented",
    "network simulation implemented",
    "cross-partition convergence implemented",
    "public api gateway deployed",
    "load simulation implemented",
    "adversarial defense implemented",
    "fairness enforcement implemented",
    "real-world pilot completed",
    "production mobility readiness achieved",
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_transition_adrs_have_bounded_proposed_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not runtime authority" in lowered
    assert "not evidence that afriride has implemented" in lowered
    assert "do not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    before_non_claims = lowered.split("## bounded non-claims")[0]
    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in before_non_claims


def test_transition_adrs_preserve_adr_chain_and_phase_model() -> None:
    text = read_doc()

    assert "AfriRide may expand only by proving new domains." in text
    assert "AfriRide must not expand by merely adding features." in text
    assert "ADR\n-> invariant extension\n-> implementation binding\n-> governance rule\n-> guard test\n-> CI enforcement" in text

    for phase in PHASES:
        assert phase in text

    for adr in ADRS:
        assert f"### {adr}" in text

    assert text.count("PROPOSED") >= len(ADRS)


def test_transition_adrs_declare_surfaces_invariants_validators_and_counter_tests() -> None:
    text = read_doc()

    for surface in PROPOSED_SURFACES:
        assert surface in text

    for invariant in INVARIANTS:
        assert invariant in text

    for validator in VALIDATORS:
        assert validator in text

    for counter_test in COUNTER_TESTS:
        assert counter_test in text


def test_transition_adrs_require_deterministic_constraints_for_realism_and_mobile() -> None:
    text = read_doc()

    for constraint in (
        "all location updates must be event-derived",
        "no real-time randomness",
        "seeded simulation only",
        "route computation must be deterministic for identical inputs",
        "all client events must be timestamp-normalized",
        "event ordering must be reconstructed deterministically",
        "client clocks are observational",
        "no client-side authority",
        "pricing must be a pure function of recorded state",
        "all economic mutations must emit mutation witnesses",
    ):
        assert constraint in text


def test_transition_adrs_require_distributed_edge_and_chaos_controls() -> None:
    text = read_doc()

    for control in (
        "partition routing must be deterministic",
        "scheduling must be replay-stable",
        "worker execution must be pure",
        "all network effects must be event-driven",
        "replay must reproduce network behavior exactly",
        "convergence must be deterministic",
        "raw data must never enter runtime directly",
        "all inputs must be normalized",
        "API cannot mutate state directly",
        "API is not source of truth",
        "load must be event-driven",
        "invalid mutations must be rejected deterministically",
        "fairness must be computable and deterministic",
        "production == replay-verifiable",
        "pilot claims must remain evidence-scoped",
    ):
        assert control in text


def test_transition_adrs_require_evidence_and_safe_final_classification() -> None:
    text = read_doc()

    for evidence in (
        "geo_trace_reconstruction",
        "offline_replay_convergence",
        "pricing_replay_equivalence",
        "multi_node_replay_equivalence",
        "network_event_replay",
        "convergence_trace_validation",
        "normalized_event_trace",
        "api_event_trace_validation",
        "load_trace_equivalence",
        "rejection_trace",
        "fairness_trace_validation",
        "production_replay_trace",
        "real_trip_reconstruction",
    ):
        assert evidence in text

    lowered = text.lower()
    assert "proposed" in lowered
    assert "bounded architectural decisions" in lowered
    assert "counter-tests, validator coverage, and CI-enforced claim discipline" in text
