from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/reviews/AfriTech_Ecosystem_Vision_Commit_Review.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: BOUNDED STRATEGIC ECOSYSTEM DOCUMENTATION REVIEW",
    "CLASSIFICATION: NON-AUTHORITATIVE GOVERNANCE REVIEW",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "runtime authority",
    "replay authority",
    "operational deployment proof",
    "claim admissibility",
    "production readiness",
)

FORBIDDEN_INFLATION = (
    "afritech ecosystem already exists operationally",
    "already-realized continental operating system achieved",
    "documentation is now authority",
    "vision is now proof",
    "roadmap is runtime truth",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_commit_review_has_bounded_non_authoritative_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_commit_review_preserves_final_classification() -> None:
    text = read_doc()

    assert "BOUNDED STRATEGIC ECOSYSTEM DOCUMENTATION" in text

    for non_authority in (
        "runtime authority",
        "constitutional truth",
        "replay authority",
        "operational deployment proof",
    ):
        assert non_authority in text

    assert "That separation remains preserved." in text


def test_commit_review_covers_vision_isolation_and_guard_test() -> None:
    text = read_doc()

    assert "AfriTech_Ecosystem_Vision_Roadmap.md" in text
    assert "docs/vision/" in text

    for preserved in (
        "strategic roadmap isolation",
        "non-authoritative classification",
        "preserve-or-isolate compliance",
        "doctrine/runtime separation",
    ):
        assert preserved in text

    for guard in (
        "aspirational infrastructure remains aspirational",
        "forbidden claims remain forbidden",
        "executable proof remains the authority anchor",
        "AfriAI remains non-sovereign",
        "ecosystem vision cannot silently mutate into operational truth",
    ):
        assert guard in text


def test_commit_review_covers_forbidden_claim_refinement() -> None:
    text = read_doc()

    assert "mentioning forbidden claims" in text
    assert "asserting forbidden claims" in text

    for improvement in (
        "validator precision",
        "doctrinal clarity",
        "semantic admissibility",
        "governance usability",
    ):
        assert improvement in text

    assert "negative capability declarations trigger false positives" in text


def test_commit_review_covers_validation_surface_coherence() -> None:
    text = read_doc()

    for surface in (
        "replay admissibility",
        "deterministic execution semantics",
        "witness integrity",
        "ontology alignment",
        "closed-world enforcement",
        "enforcement integrity",
        "claim discipline",
    ):
        assert surface in text

    assert "Global readiness claims remain forbidden" in text
    assert "Negative capabilities explicitly bounded" in text


def test_commit_review_covers_layer_authority_separation() -> None:
    text = read_doc()

    for row in (
        "| Constitutional proof | authoritative |",
        "| Runtime execution | admissibility-bound |",
        "| Validators | enforcement |",
        "| Documentation | descriptive only |",
        "| Ecosystem roadmap | strategic vision only |",
    ):
        assert row in text

    for failure_mode in (
        "vision becomes doctrine",
        "documentation becomes authority",
        "marketing becomes runtime truth",
    ):
        assert failure_mode in text


def test_commit_review_covers_path_ontology_and_remaining_risks() -> None:
    text = read_doc()

    for mature_element in (
        "canonical module-path identity",
        "replay-safe identity resolution",
        "observer-independent execution semantics",
        "anti-reflection enforcement",
        "filesystem/non-runtime identity separation",
    ):
        assert mature_element in text

    for risk in (
        "very high semantic density",
        "extensive governance surfaces",
        "significant conceptual overhead",
        "large terminology expansion",
        "abstraction growth outpacing executable necessity",
    ):
        assert risk in text


def test_commit_review_preserves_most_important_truth_and_assessment() -> None:
    text = read_doc()

    assert "bounded executable constitutional core" in text
    assert "long-term infrastructure roadmap" in text
    assert "already-realized continental operating system" in text

    for assessment in (
        "claim discipline integration",
        "roadmap isolation",
        "forbidden-claim enforcement",
        "validator coherence",
        "constitutional boundary preservation",
        "ontology enforcement continuity",
        "operational deployment proof",
        "ecosystem execution reality",
        "real-world distributed continuity validation",
    ):
        assert assessment in text


def test_commit_review_has_safe_final_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "bounded strategic" in lowered
    assert "long-term ecosystem coherence" in lowered
    assert "executable constitutional proof" in lowered
    assert "runtime authority" in lowered
    assert "aspirational infrastructure roadmap claims" in lowered
