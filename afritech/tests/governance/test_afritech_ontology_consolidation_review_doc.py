from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/reviews/AfriTech_Ontology_Consolidation_Structural_Review.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: STRUCTURAL REVIEW SURFACE",
    "CLASSIFICATION: NON-AUTHORITATIVE ARCHITECTURAL REVIEW",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "execution legality",
    "core invariants",
    "identity ontology",
    "claim admissibility",
    "production readiness",
)

REVIEW_SCOPE = (
    "GitHub CI enforcement pipelines",
    "path ontology governance",
    "enforcement matrices",
    "identity rules",
    "implementation registry/state governance",
    "replay admissibility enforcement",
    "deterministic execution guarantees",
    "claim discipline hardening",
)

FORBIDDEN_INFLATION = (
    "universal correctness achieved",
    "production completeness achieved",
    "global readiness achieved",
    "complete state-space exhaustiveness achieved",
    "validator completeness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_review_has_non_authoritative_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in lowered
    assert "bounded evidence and repository structure only" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_review_declares_scope_and_canonical_pipeline() -> None:
    text = read_doc()

    for item in REVIEW_SCOPE:
        assert item in text

    assert "afritech.ci.constitutional_pipeline" in text
    assert "module identity" in text
    assert "filesystem identity" in text
    assert "conceptual identity" in text


def test_review_covers_ontology_consolidation_surfaces() -> None:
    text = read_doc()

    assert "ontology consolidation" in text

    for surface in (
        "PATH_ONTOLOGY.yaml",
        "identity_rules.yaml",
        "implementation_registry.yaml",
        "implementation_states.yaml",
        "enforcement_matrix.yaml",
    ):
        assert surface in text

    assert "machine-governed constitutional semantics" in text


def test_review_covers_path_and_identity_discipline() -> None:
    text = read_doc()

    for identity_form in ("module_path", "filesystem_path", "conceptual_path"):
        assert identity_form in text

    assert "Module paths are the exclusive constitutional identity form" in text
    assert "no filesystem identity replay" in text
    assert "no reflection resolution" in text
    assert "no extension authority" in text

    for forbidden_form in (
        "reflection identity",
        "symbolic runtime identity",
        "getattr(runtime, name)",
        "__import__(module_name)",
        "eval(module_name)",
        "exec(identity_code)",
    ):
        assert forbidden_form in text


def test_review_covers_enforcement_matrix_and_states() -> None:
    text = read_doc()

    for field in (
        "implementation_state",
        "replay_blocking",
        "runtime_blocking",
        "proof_blocking",
        "witness_dependencies",
        "authority_scope",
    ):
        assert field in text

    for state in (
        "IMPLEMENTED",
        "PARTIAL",
        "PLANNED",
        "FROZEN",
        "DOCUMENTARY",
        "FORBIDDEN_ALIAS",
    ):
        assert state in text


def test_review_covers_ci_and_claim_discipline() -> None:
    text = read_doc()

    assert "1 canonical constitutional pipeline" in text
    assert "python3 -m afritech.ci.constitutional_pipeline" in text

    for risk_reduced in (
        "validator fragmentation",
        "authority ambiguity",
        "pipeline drift",
    ):
        assert risk_reduced in text

    for claim_rule in (
        "forbidden_readiness_claim_rejection",
        "scoped_claim_enforcement",
        "claim-evidence binding",
        "implementation admissibility linkage",
    ):
        assert claim_rule in text


def test_review_covers_remaining_risks() -> None:
    text = read_doc()

    for risk in (
        "Governance Weight Explosion",
        "Validator Overlap",
        "YAML Constitutional Surface Growth",
        "Operational Gap",
    ):
        assert risk in text

    for gap in (
        "real-time geo infrastructure",
        "distributed scaling",
        "payments",
        "security hardening",
        "observability",
        "mobile apps",
        "compliance",
    ):
        assert gap in text


def test_review_preserves_accurate_classification_and_forbidden_claims() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "ga++++ replay-governed constitutional architecture" in lowered
    assert "validated deterministic enforcement" in lowered
    assert "implementation admissibility governance" in lowered
    assert "bounded afriride continuity verification" in lowered

    for forbidden_claim in (
        "universal correctness",
        "production completeness",
        "global readiness",
        "complete state-space exhaustiveness",
        "validator completeness",
    ):
        assert forbidden_claim in lowered


def test_review_recommends_constitutional_ir_compilation() -> None:
    text = read_doc()

    assert "constitutional IR compilation" in text
    assert "YAML governance surfaces\n-> compiled canonical semantic graph" in text
    assert "-> validators generated from IR" in text

    for benefit in (
        "semantic drift",
        "validator duplication",
        "governance entropy",
        "closed-world semantics",
        "replay admissibility",
        "deterministic governance",
    ):
        assert benefit in text


def test_review_has_safe_final_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "bounded replay-governed constitutional" in lowered
    assert "maturing ontology consolidation" in lowered
    assert "claim discipline" in lowered
    assert "implementation admissibility governance" in lowered
    assert "remaining production" in lowered
    assert "infrastructure gap" in lowered
