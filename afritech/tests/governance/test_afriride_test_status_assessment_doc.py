from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/qa/AfriRide_Test_Status_Assessment.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: TEST POSTURE ASSESSMENT",
    "CLASSIFICATION: ISOLATED OPERATIONAL VALIDATION SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay admissibility",
    "execution legality",
    "core invariants",
    "identity ontology",
    "claim admissibility",
    "production deployment proof",
)

VALIDATED_CATEGORIES = (
    "Deterministic Replay",
    "Continuity Simulation",
    "Closed-World Enforcement",
    "Witness Integrity",
    "Deterministic Product Logic",
)

PARTIAL_AREAS = (
    "Large-Scale Distributed Load Testing",
    "Real GPS and Geo Simulation",
    "Mobile Client Replay Validation",
    "Economic and Marketplace Simulation",
    "Security Adversarial Testing",
)

FORBIDDEN_INFLATION = (
    "feature-complete production testing achieved",
    "large-scale distributed load proof achieved",
    "real-world gps correctness achieved",
    "mobile replay validation achieved",
    "marketplace economics validation achieved",
    "security adversarial completeness achieved",
    "massive multi-region deployment proof achieved",
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_test_status_assessment_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not runtime authority" in lowered
    assert "not a traditional\nfeature-complete production test posture" in text
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    before_non_claims = lowered.split("# 6. bounded non-claims")[0]
    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in before_non_claims


def test_test_status_assessment_defines_validated_categories() -> None:
    text = read_doc()

    for category in VALIDATED_CATEGORIES:
        assert category in text

    for validation_surface in (
        "afritech.storage.replay_engine",
        "afritech.tests.governance.test_production_mvp_pipeline_replay",
        "afritech.ci.continuity_resilience_validator",
        "afritech.ci.import_topology_enforcement",
        "afritech.ci.witness_proof_validator",
        "afritech.core.matching_engine",
    ):
        assert validation_surface in text


def test_test_status_assessment_distinguishes_strengths_from_partial_areas() -> None:
    text = read_doc()

    for strength_row in (
        "| Deterministic architecture | Strong |",
        "| Replay equivalence | Strong |",
        "| Constitutional enforcement | Strong |",
        "| Witness lineage | Strong |",
        "| Continuity simulation | Strong |",
        "| Operational distributed scale | Partial |",
        "| Marketplace economics | Early |",
        "| Massive multi-region deployment proof | Not proven |",
    ):
        assert strength_row in text

    for partial_area in PARTIAL_AREAS:
        assert partial_area in text


def test_test_status_assessment_lists_operational_test_gaps() -> None:
    text = read_doc()

    for gap in (
        "queue saturation testing",
        "partition imbalance testing",
        "worker crash recovery",
        "route drift",
        "mobile jitter simulation",
        "offline synchronization replay",
        "surge coordination",
        "forged witness attempts",
        "queue poisoning",
        "forged event lineage",
    ):
        assert gap in text


def test_test_status_assessment_recommends_next_expansion_order() -> None:
    text = read_doc()

    for priority in (
        "1. Partition and worker failure simulation",
        "2. Queue poisoning and forged event rejection tests",
        "3. Recorded GPS jitter replay tests",
        "4. Mobile offline retry and idempotency tests",
        "5. Matching fairness and supply imbalance tests",
        "6. Long-running event_log replay verification tests",
        "7. Multi-region imported-event replay drills",
    ):
        assert priority in text

    for invariant in (
        "recorded inputs",
        "deterministic normalization",
        "worker-mediated core invocation",
        "append-only replay ledger",
        "claim discipline",
        "bounded operational classification",
    ):
        assert invariant in text
