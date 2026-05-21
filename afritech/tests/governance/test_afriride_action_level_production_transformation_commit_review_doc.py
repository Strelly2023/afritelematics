from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/reviews/AfriRide_Action_Level_Production_Transformation_Commit_Review.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: BOUNDED PRODUCTION TRANSFORMATION COMMIT REVIEW",
    "CLASSIFICATION: NON-AUTHORITATIVE ENGINEERING REVIEW",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "runtime authority",
    "replay authority",
    "execution legality",
    "core invariants",
    "claim admissibility",
    "operational deployment proof",
    "production readiness",
)

FORBIDDEN_INFLATION = (
    "afriride is now production-ready",
    "production readiness has now been achieved",
    "production execution topology is now implemented",
    "edge-layer implementation is now complete",
    "commercial readiness proof has been achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_commit_review_has_bounded_non_authoritative_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in lowered
    assert "not runtime authority" in lowered
    assert "not evidence of production deployment" not in lowered
    assert "not a declaration that AfriRide is production-ready" in text

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_commit_review_preserves_commit_identity_and_classification() -> None:
    text = read_doc()

    assert "2881ca0 Add AfriRide action-level production transformation plan" in text
    assert "GOVERNED PRODUCTION TRANSFORMATION ROADMAP" in text

    for non_authority in (
        "production execution topology",
        "runtime proof",
        "deployment evidence",
        "edge-layer implementation",
        "commercial readiness proof",
    ):
        assert non_authority in text

    assert "That separation remains essential." in text


def test_commit_review_covers_strategy_to_governance_artifact() -> None:
    text = read_doc()

    assert "AfriRide_Action_Level_Production_Transformation_Plan.md" in text

    for governed_property in (
        "versioned",
        "test-bound",
        "CI-validated",
        "reviewable",
        "regression-protected",
    ):
        assert governed_property in text

    assert "governed transformation contract" in text


def test_commit_review_covers_documentation_ci_binding_and_gates() -> None:
    text = read_doc()

    assert "test_afriride_action_level_production_transformation_doc.py" in text

    for bounded_property in (
        "bounded",
        "non-authoritative",
        "constitutionally constrained",
        "claim-disciplined",
        "regression-protected",
    ):
        assert bounded_property in text

    for gate in (
        "pytest execution",
        "claim discipline validator",
        "constitutional pipeline",
        "commit hook validation",
    ):
        assert gate in text

    assert "bounded operational roadmap" in text
    assert "It does not mean production readiness has been achieved." in text


def test_commit_review_covers_proof_integrity_and_working_state() -> None:
    text = read_doc()

    assert "afritech/proof/completeness.json" in text

    for preserved in (
        "reproducibility",
        "trace alignment",
        "repository cleanliness",
        "generated-artifact discipline",
    ):
        assert preserved in text

    assert "AfriTech_Main.txt" in text
    assert "afriTech2.txt" in text
    assert "No hidden state, no ambiguity." in text


def test_commit_review_covers_architectural_meaning() -> None:
    text = read_doc()

    assert "Planning\n-> Constitutional Governance\n-> Enforced Execution Roadmap" in text

    for roadmap_property in (
        "testable",
        "enforceable",
        "reviewable",
        "bounded by validation",
    ):
        assert roadmap_property in text

    assert "controlled system evolution" in text


def test_commit_review_covers_open_world_transition_risk() -> None:
    text = read_doc()

    assert "AfriTech = closed, controlled constitutional system" in text
    assert "AfriTech = constitutional system preparing for controlled open-world interaction" in text

    for risk in (
        "external inputs",
        "queues",
        "provider responses",
        "mobile clients",
        "payments",
        "maps",
        "concurrency",
        "partial failure",
    ):
        assert risk in text

    assert "production disorder must be absorbed at the edge" in text


def test_commit_review_covers_missing_enforcement_bridge_and_adapter_gap() -> None:
    text = read_doc()

    for missing_surface in (
        "afritech.edge.adapter",
        "afritech.edge.normalization",
        "afritech.edge.ingestion",
        "afritech.runtime.queue",
        "afritech.runtime.partitioning",
    ):
        assert missing_surface in text

    assert "plan exists outside execution topology" in text

    for missing_binding in (
        "declared in the architecture registry",
        "bound to implementation surfaces",
        "validated as execution topology",
        "represented in authority registries",
        "covered by production replay tests",
    ):
        assert missing_binding in text

    assert "conceptually valid but not yet constitutionally integrated" in text


def test_commit_review_defines_immediate_next_steps() -> None:
    text = read_doc()

    for registry in (
        "implementation_registry.yaml",
        "surface_authority_registry.yaml",
        "surface_implementation_binding.yaml",
    ):
        assert registry in text

    assert "API\n-> Adapter\n-> Queue\n-> Worker\n-> Core\n-> Event Log" in text
    assert "1 queue" in text
    assert "1 worker" in text
    assert "1 event log" in text
    assert "1 replay integration test" in text

    for event_log_property in (
        "append-only",
        "replay-compatible",
        "trace-emitting",
        "hash-bound",
        "partition-aware",
    ):
        assert event_log_property in text

    assert "test_production_pipeline_replay.py" in text


def test_commit_review_defines_replay_integration_targets_and_maturity_update() -> None:
    text = read_doc()

    for replay_target in (
        "external input normalization",
        "queue ordering",
        "worker execution",
        "core invocation boundary",
        "event log emission",
        "replay hash stability",
        "materialized state reconstruction",
    ):
        assert replay_target in text

    for row in (
        "| Core system | GA Elite |",
        "| Production roadmap | Governed |",
        "| Production execution | Not implemented yet |",
    ):
        assert row in text

    assert "system evolution under control" in text


def test_commit_review_has_safe_final_classification() -> None:
    text = read_doc()

    for final_phrase in (
        "bounded engineering review",
        "governed production transformation roadmap",
        "versioned, test-bound, CI-validated",
        "constitutionally admissible as documentation",
        "edge-layer surfaces",
        "queue execution",
        "event-log authority",
        "production replay integration",
        "next implementation steps",
        "completed production readiness",
    ):
        assert final_phrase in text
