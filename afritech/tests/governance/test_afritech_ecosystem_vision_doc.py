from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/vision/AfriTech_Ecosystem_Vision_Roadmap.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: STRATEGIC ECOSYSTEM VISION ROADMAP",
    "CLASSIFICATION: BOUNDED NON-AUTHORITATIVE VISION SURFACE",
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

INFRASTRUCTURE_LAYERS = (
    "Identity Infrastructure - AfriID",
    "Financial Infrastructure - AfriPay",
    "Mobility Continuity Layer - AfriRide",
    "Logistics Infrastructure - AfriConnect",
    "Digital Health Infrastructure - AfriHealth",
    "Commerce Infrastructure",
    "Learning and Work Infrastructure",
    "Civic and Governance Coordination",
)

FORBIDDEN_INFLATION = (
    "afritech has achieved universal operational deployment",
    "afritech has complete continental infrastructure",
    "afritech has achieved global dominance",
    "afritech controls society autonomously",
    "afritech is proven agi infrastructure",
    "afritech has already-realized ecosystem scale",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_ecosystem_vision_has_bounded_non_authoritative_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_ecosystem_vision_preserves_final_positioning() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "long-term constitutional infrastructure roadmap" in lowered
    assert "bounded, executable constitutional core proof surface" in lowered
    assert "preserve-or-isolate compliant" in lowered
    assert "inflated universality claims" in lowered
    assert "unbounded super app rhetoric" in lowered
    assert "continental-scale ambition" in lowered


def test_ecosystem_vision_declares_core_thesis_and_problem() -> None:
    text = read_doc()

    for value in (
        "continuity",
        "legitimacy",
        "replayability",
        "deterministic coordination",
        "infrastructure resilience",
        "identity stability",
        "operational accountability",
    ):
        assert value in text

    for failure_mode in (
        "infrastructure instability",
        "institutional fragmentation",
        "low-trust environments",
        "identity discontinuity",
        "operational opacity",
    ):
        assert failure_mode in text

    assert "transactions" in text
    assert "continuity of life systems" in text


def test_ecosystem_vision_preserves_constitutional_core_boundary() -> None:
    text = read_doc()

    for core_rule in (
        "Proof defines truth.",
        "Runtime executes admitted behavior.",
        "Replay verifies legitimacy.",
        "Operations improve reproducibility without redefining truth.",
    ):
        assert core_rule in text

    for proof_surface in (
        "deterministic execution",
        "validator-bound enforcement",
        "bounded continuity simulations",
        "trace reconstruction",
        "witness bundles",
        "admissible replay enforcement",
    ):
        assert proof_surface in text

    assert "The constitutional core is the only authoritative proof surface." in text


def test_ecosystem_vision_covers_infrastructure_layers() -> None:
    text = read_doc()

    for layer in INFRASTRUCTURE_LAYERS:
        assert layer in text

    for component in (
        "ShopConnectSpace",
        "AfriVirtualMall",
        "AfriAgro",
        "AfriHome",
        "AfriLearn",
        "AfriTalent",
        "AfriWork",
        "AfriCivic",
        "AfriTrust",
    ):
        assert component in text


def test_ecosystem_vision_bounds_ai_and_cloud_layers() -> None:
    text = read_doc()

    assert "AfriAI is not sovereign." in text
    assert "an assistive intelligence layer operating within constitutional boundaries" in text

    for role in (
        "prediction",
        "optimization",
        "recommendation",
        "anomaly detection",
        "continuity forecasting",
        "operational assistance",
    ):
        assert role in text

    for forbidden_role in (
        "redefining admissibility",
        "overriding constitutional truth",
        "bypassing validators",
        "redefining replay legitimacy",
    ):
        assert forbidden_role in text

    assert "AfriCloud - Infrastructure Layer" in text
    assert "Infrastructure hosting does not redefine execution legitimacy." in text


def test_ecosystem_vision_preserves_execution_doctrine() -> None:
    text = read_doc()

    assert "Expand only from proven constitutional foundations." in text

    for stage in (
        "Stage 1 - Core Constitutional Integrity",
        "Stage 2 - Bounded Operational Ecosystems",
        "Stage 3 - Interoperable Infrastructure",
        "Stage 4 - Continental Coordination Layers",
    ):
        assert stage in text

    for doctrine_item in (
        "replay legitimacy",
        "validator integrity",
        "identity continuity",
        "logistics continuity",
        "civic coordination",
        "distributed continuity infrastructure",
    ):
        assert doctrine_item in text


def test_ecosystem_vision_preserves_permanent_claim_discipline() -> None:
    text = read_doc()
    lowered = text.lower()

    for forbidden_claim in (
        "universal operational deployment",
        "complete continental infrastructure",
        "achieved global dominance",
        "autonomous societal control",
        "proven AGI infrastructure",
        "already-realized ecosystem scale",
    ):
        assert forbidden_claim in text

    for bounded_term in (
        "aspirational",
        "strategic",
        "phased",
        "bounded by executable evidence",
    ):
        assert bounded_term in lowered


def test_ecosystem_vision_preserves_long_term_proof_requirements() -> None:
    text = read_doc()

    for exceptional in (
        "systems coherence",
        "constitutional philosophy",
        "replay-centered governance",
        "continuity-first thinking",
        "bounded epistemic discipline",
    ):
        assert exceptional in text

    for required_proof in (
        "operational scale",
        "economic viability",
        "ecosystem adoption",
        "infrastructure deployment",
        "distributed coordination",
        "real-world resilience",
        "continental interoperability",
    ):
        assert required_proof in text


def test_ecosystem_vision_has_safe_final_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "next-generation constitutional infrastructure roadmap" in lowered
    assert "bounded executable proof core" in lowered
    assert "replay-safe" in lowered
    assert "continuity-preserving" in lowered
    assert "admissibility boundaries" in lowered
    assert "operational accountability" in lowered
    assert "bounded strategic infrastructure roadmap" in lowered
    assert "preserve-or-isolate claim discipline" in lowered
