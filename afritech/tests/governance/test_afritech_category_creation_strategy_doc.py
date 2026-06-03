from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Category_Creation_Strategy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: STRATEGIC CATEGORY CREATION THESIS",
    "CLASSIFICATION: NON-AUTHORITATIVE STRATEGIC POSITIONING SURFACE",
    "ROLE: DEFINE CATEGORY STRATEGY WITHOUT REDEFINING CONSTITUTIONAL TRUTH",
    "BOUNDARY: DOES NOT DEFINE LEGITIMACY, REPLAY AUTHORITY, OR PRODUCTION CLAIMS",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "invariant semantics",
    "identity ontology",
    "admissibility law",
    "validator authority",
    "production readiness",
    "market proof",
)

SIX_CLAIMS = (
    "Existing Operational Infrastructure Is Legitimacy-Fragile",
    "Replay-Governed Legitimacy Becomes Necessary",
    "Constitutional Execution Changes Infrastructure Economics",
    "Bounded AI Becomes Operationally Critical",
    "Trust Infrastructure Becomes Foundational",
    "Replay-Valid Operational Ecosystems Become Difficult To Replace",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_category_strategy_has_bounded_non_authoritative_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text


def test_category_strategy_preserves_central_thesis() -> None:
    text = read_doc()

    assert "AfriTech does not attempt to become another operational platform." in text
    assert (
        "It attempts to become the constitutional legitimacy layer under operational "
        "ecosystems."
    ) in text
    assert "become structurally difficult to replace" in text
    assert "constitutional operational infrastructure" in text
    assert "constitutional execution legitimacy" in text


def test_category_strategy_declares_strategic_inversion() -> None:
    text = read_doc()

    assert "do not compete on features;" in text
    assert "compete on operational legitimacy." in text
    assert "provable operational integrity" in text

    for proof_surface in (
        "replay admissibility",
        "deterministic lineage",
        "constitutional enforcement",
        "ontology-safe identity",
        "bounded autonomous governance",
        "traceable economic execution",
    ):
        assert proof_surface in text


def test_category_strategy_contains_six_strategic_claims() -> None:
    text = read_doc()

    for claim in SIX_CLAIMS:
        assert claim in text

    for fragility in (
        "opaque runtime behavior",
        "mutable service state",
        "weak identity continuity",
        "non-replayable operational decisions",
        "fragmented authority semantics",
    ):
        assert fragility in text


def test_category_strategy_preserves_replay_legitimacy_claim() -> None:
    text = read_doc()

    assert "replay legitimacy" in text
    assert "replay-governed legitimacy" in text

    for replay_surface in (
        "trace reconstruction",
        "witness validation",
        "replay equivalence",
        "cross-region replay comparison",
        "receipt lineage",
        "deterministic execution history",
        "validator-backed proof bundles",
    ):
        assert replay_surface in text

    assert "already achieved planetary replay infrastructure" in text


def test_category_strategy_bounds_ai_and_autonomy() -> None:
    text = read_doc()

    assert "bounded constitutional intelligence" in text

    for allowed in (
        "recommend",
        "predict",
        "optimize",
        "simulate",
        "summarize",
        "assist",
        "warn",
    ):
        assert allowed in text

    for forbidden in (
        "define truth",
        "define legitimacy",
        "bypass replay",
        "rewrite admissibility",
        "ratify constitutional futures",
        "originate authority semantics",
    ):
        assert forbidden in text

    assert "Capability may evolve indefinitely." in text
    assert "Authority remains constitutionally centralized." in text
    assert "Autonomy may specialize operations." in text
    assert "It may not originate authority." in text


def test_category_strategy_preserves_constitutional_economics_and_trust() -> None:
    text = read_doc()

    assert "economic execution becomes replay-governed." in text
    assert "AfriTrust" in text

    for economic_surface in (
        "trust-weighted markets",
        "anti-fraud economic traces",
        "replay-valid settlement flows",
        "reputation lineage",
        "dispute replay",
        "deterministic economic coordination",
    ):
        assert economic_surface in text

    for trust_surface in (
        "replay-backed identity",
        "behavioral trust lineage",
        "execution reliability scoring",
        "economic trust weighting",
        "admissible reputation evidence",
    ):
        assert trust_surface in text

    assert "hidden social authority" in text
    assert "non-replayable legitimacy" in text


def test_category_strategy_preserves_ecosystem_without_multiplying_constitutions() -> None:
    text = read_doc()

    for ecosystem in (
        "AfriRide",
        "AfriPay",
        "AfriID",
        "AfriTrust",
        "AfriHealth",
        "AfriCommerce",
        "AfriCloud",
        "AfriAI",
    ):
        assert ecosystem in text

    assert "These surfaces must not become separate constitutional systems." in text
    assert "one constitutional authority model" in text
    assert "many bounded operational ecosystems" in text


def test_category_strategy_preserves_tooling_and_institutional_legitimacy() -> None:
    text = read_doc()

    for tooling in (
        "Replay Studio",
        "Constitutional IDE",
        "Runtime Topology Explorer",
        "Economic Flow Inspector",
        "Distributed Replay Dashboard",
        "Constitutional SDKs",
        "Validator assistant tooling",
    ):
        assert tooling in text

    for institution in (
        "universities",
        "formal research",
        "government pilots",
        "critical infrastructure simulations",
        "public auditability",
        "open replay verification",
        "third-party validation",
    ):
        assert institution in text


def test_category_strategy_has_safe_final_positioning() -> None:
    text = read_doc()

    assert "AfriTech is not a super app." in text
    assert "AfriTech is not another backend platform." in text
    assert "AfriTech is not an unbounded AI automation layer." in text
    assert "truth is replay-valid" in text
    assert "identity is ontology-safe" in text
    assert "economics are traceable" in text
    assert "AI is bounded" in text
    assert "execution is deterministic" in text
    assert "operations are admissible" in text
    assert (
        "become the constitutional legitimacy layer\nunder next-generation "
        "operational ecosystems"
    ) in text
