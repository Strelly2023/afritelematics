from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_Operational_Strengthening_Plan.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL STRENGTHENING ROADMAP",
    "CLASSIFICATION: ISOLATED VALIDATION EXPANSION SURFACE",
    "GOVERNANCE MODE: SURFACE -> VALIDATOR -> TEST SYSTEM -> EVIDENCE -> CI GATE",
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

GAP_LAYERS = (
    "Large-Scale Distributed Load Testing",
    "Real GPS and Geo Simulation",
    "Mobile Client Replay Validation",
    "Economic and Marketplace Simulation",
    "Security Adversarial Testing",
)

PROPOSED_SURFACES = (
    "afritech.simulation.scale.cluster_simulator",
    "afritech.simulation.scale.load_generator",
    "afritech.distributed.failure.injector",
    "ecosystems.afriride.geo.simulator",
    "ecosystems.afriride.geo.traffic_model",
    "ecosystems.afriride.geo.map_reconciler",
    "ecosystems.afriride.client.replay_engine",
    "ecosystems.afriride.client.device_model",
    "ecosystems.afriride.market.simulator",
    "ecosystems.afriride.market.surge_engine",
    "ecosystems.afriride.market.fairness_checker",
    "afritech.security.adversarial_engine",
    "afritech.security.mutation_guard",
)

VALIDATORS = (
    "afritech.ci.scale_determinism_validator",
    "afritech.ci.partition_convergence_validator",
    "afritech.ci.worker_recovery_validator",
    "afritech.ci.geo_replay_validator",
    "afritech.ci.route_consistency_validator",
    "afritech.ci.client_replay_validator",
    "afritech.ci.event_normalization_validator",
    "afritech.ci.market_equilibrium_validator",
    "afritech.ci.fairness_validator",
    "afritech.ci.security_integrity_validator",
    "afritech.ci.mutation_guard_validator",
)

NEW_INVARIANTS = (
    "GEO_PHYSICAL_CONSISTENCY",
    "CLIENT_CONSISTENCY",
    "ECONOMIC_FAIRNESS",
    "SECURITY_INTEGRITY",
)

COUNTER_TESTS = (
    "inject_queue_saturation",
    "inject_worker_crash_during_mutation",
    "inject_partition_imbalance",
    "inject_non_canonical_partition_merge",
    "inject_seed_mismatch_between_workers",
    "inject_duplicate_sequence_claim",
    "inject_ack_loss_then_redelivery",
    "inject_stale_snapshot_resurrection",
    "inject_cross_partition_clock_skew",
    "inject_non_canonical_retry_order",
    "inject_noisy_coordinates",
    "inject_physically_impossible_jump",
    "inject_unrecorded_traffic_delay",
    "inject_non_deterministic_reroute",
    "inject_plus_10_minute_clock_skew",
    "inject_out_of_order_client_events",
    "inject_duplicate_delivery",
    "inject_client_side_authority_attempt",
    "inject_expired_access_token_during_sync",
    "inject_reused_refresh_token",
    "inject_revoked_device_resubmission",
    "inject_dual_device_identity_collision",
    "inject_surge_explosion",
    "inject_mass_cancellation_wave",
    "inject_driver_price_gaming",
    "inject_bias_exploitation_scenario",
    "inject_fake_replay_history",
    "inject_modified_witness_hash",
    "inject_mutation_outside_gateway",
    "inject_malformed_queue_event",
)

FORBIDDEN_INFLATION = (
    "large-scale distributed load testing implemented",
    "real GPS simulation implemented",
    "mobile client replay validation implemented",
    "economic marketplace simulation implemented",
    "security adversarial testing implemented",
    "geo_physical_consistency implemented",
    "client_consistency implemented",
    "economic_fairness implemented",
    "security_integrity implemented",
    "100k concurrent ride flows validated",
    "1m concurrent ride events validated",
    "worker crash recovery proven",
    "partition split and merge proven",
    "real-world mobility chaos proven",
    "production mobility readiness achieved",
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_operational_strengthening_plan_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not runtime authority" in lowered
    assert "not evidence that afriride has already proven correctness under" in lowered
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    before_non_claims = lowered.split("## bounded non-claims")[0]
    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in before_non_claims


def test_operational_strengthening_plan_preserves_execution_rule_and_gap_model() -> None:
    text = read_doc()

    assert "proof of correctness in bounded environments" in text
    assert "proof of correctness under adversarial real-world stress" in text
    assert "validation layers, not by treating features as proof" in text
    assert "IMPLEMENT\n+-> REPLAY\n+-> VALIDATE\n+-> CLAIM".replace("+", "") in text
    assert "IMPLEMENT\n+-> DEPLOY\n+-> HOPE".replace("+", "") in text

    for item in (
        "surface",
        "validator",
        "test system",
        "evidence",
        "CI gate",
        "counter-test",
        "claim boundary",
    ):
        assert item in text

    for layer in GAP_LAYERS:
        assert layer in text


def test_operational_strengthening_plan_declares_surfaces_validators_invariants_and_counter_tests() -> None:
    text = read_doc()

    for surface in PROPOSED_SURFACES:
        assert surface in text

    for validator in VALIDATORS:
        assert validator in text

    for invariant in NEW_INVARIANTS:
        assert invariant in text

    for counter_test in COUNTER_TESTS:
        assert counter_test in text


def test_operational_strengthening_plan_defines_load_and_geo_validation() -> None:
    text = read_doc()

    for item in (
        "100K concurrent ride flows",
        "1M concurrent ride events",
        "partition imbalance",
        "queue backpressure",
        "worker crashes",
        "network partitions",
        "queue_saturation_10x_traffic_spike",
        "worker_crash_recovery_40_percent_failure",
        "partition_split_and_merge",
        "GPS jitter",
        "route drift",
        "map mismatches",
        "traffic delays",
        "low-precision devices",
        "gps_noise_stabilization",
        "route_correction",
        "traffic_delay_injection",
        "Movement must be physically plausible and replay-stable.",
        "break determinism on purpose",
        "silent corruption never allowed",
        "replay hash mismatch surfaced immediately",
        "failure_injection_plan_id",
        "divergence_receipt",
    ):
        assert item in text


def test_operational_strengthening_plan_defines_client_market_and_security_validation() -> None:
    text = read_doc()

    for item in (
        "Android versus iOS inconsistencies",
        "offline mode",
        "reconnect bursts",
        "out-of-order delivery",
        "clock drift",
        "duplicate delivery",
        "Client-originated events must converge deterministically after normalization.",
        "device registration",
        "pilot token issuance",
        "refresh token rotation",
        "token_jti recorded for every authenticated session",
        "revoked_device_block_trace",
        "supply shortage",
        "demand spikes",
        "cancellations",
        "price fluctuations",
        "adversarial drivers",
        "No participant can gain advantage outside declared rules.",
        "forged events",
        "replay injection",
        "witness tampering",
        "queue poisoning",
        "unauthorized mutations",
        "Only admissible, authenticated, and traceable events may mutate system state.",
    ):
        assert item in text


def test_operational_strengthening_plan_binds_observability_to_trace_and_replay() -> None:
    text = read_doc()

    for item in (
        "Observability Design Tied to Trace/Replay",
        "observability explains trace and replay",
        "observability never overrides trace and replay",
        "trace_id",
        "token_jti",
        "replay_hash",
        "receipt_hash",
        "trace ingestion timeline",
        "device and token exception board",
        "failure injection evidence board",
        "every alert links back to trace evidence",
        "afritech.ci.observability_authority_validator",
        "afritech.ci.observability_evidence_validator",
        "afritech.ci.traceability_bridge_validator",
        "dashboard_non_authority_receipt",
    ):
        assert item in text


def test_operational_strengthening_plan_preserves_stack_build_order_and_safe_classification() -> None:
    text = read_doc()

    for stack_item in (
        "CORE",
        "deterministic execution and replay",
        "geo realism, mobile realism, and economic realism",
        "distributed execution and convergence",
        "edge normalization and real-world ingestion",
        "large-scale and adversarial validation",
    ):
        assert stack_item in text

    for build_item in (
        "ADR-101 geo simulation",
        "ADR-102 client replay",
        "ADR-401 scale testing",
    ):
        assert build_item in text

    assert "bounded validation" in text.lower()
    assert "real-world mobility stress evidence" in text
    assert "claim discipline" in text
    assert "constitutional admissibility boundaries" in text
