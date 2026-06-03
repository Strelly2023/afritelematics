from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Convergence_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL CONVERGENCE GOVERNANCE POLICY",
    "ROLE: PREVENT HISTORICAL TENDENCY ANALYSIS, DOMINANT INTERPRETATION PATTERNS, AND COHERENCE PRESSURE FROM COLLAPSING CONSTITUTIONAL PLURALITY WITHOUT EXPLICIT AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

CONVERGENCE_RISK_SURFACES = (
    "Pattern Recognition vs Plurality Collapse",
    "Constitutional Diversity Preservation",
    "Convergence Lineage Governance",
    "Plurality Transparency",
    "Convergence Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_constitutional_convergence_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "historical tendency -> dominant coherence pattern -> plurality collapse" in text
    assert "Convergence analysis may improve human understanding of historical" in text
    assert "Convergence analysis must not become constitutional\nplurality resolution." in text


def test_constitutional_convergence_policy_preserves_authority_stack() -> None:
    text = read_doc()

    for phrase in (
        "Constitution -> legitimacy",
        "Replay -> truth validation",
        "Validators -> governance enforcement",
        "Explanation Schema -> safe explanation units",
        "Composition Schema -> safe narrative aggregation",
        "Cognitive Complexity Budget -> bounded cognition",
        "Salience Policy -> bounded attention semantics",
        "Cross-Surface Consistency Policy -> operational reality coherence across surfaces",
        "Temporal Cognition Consistency Policy -> operational reality coherence across time",
        "Adaptive Cognition Governance Policy -> personalization without truth fragmentation",
        "Collective Adaptive Feedback Governance Policy -> ergonomic feedback without trained truth",
        "Autonomous Optimization Governance Policy -> operational improvement without authority redefinition",
        "Autonomous Objective Evolution Governance Policy -> goal evolution without self-authorized authority",
        "Autonomous Policy Synthesis Governance Policy -> policy proposals without self-ratification",
        "Autonomous Constitutional Interpretation Governance Policy -> ambiguity explanation without legitimacy resolution",
        "Autonomous Constitutional Harmonization Governance Policy -> conflict mapping without supremacy determination",
        "Autonomous Constitutional Precedent Governance Policy -> constitutional memory without jurisprudence formation",
        "Autonomous Constitutional Convergence Governance Policy -> tendency analysis without plurality collapse",
        "Convergence systems -> advisory constitutional tendency analysis only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional convergence governance constrains tendency analysis" in text
    assert "It does not validate truth." in text


def test_constitutional_convergence_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in CONVERGENCE_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated convergence analysis treats dominant patterns as legitimate outcomes",
        "Autonomous convergence reduces the visible ambiguity space",
        "Generated convergence analysis loses source doctrine, historical tendency lineage, or plurality status",
        "Convergence analysis hides minority paths or presents common patterns as settled",
        "Repeated convergence analysis creates constitutional monoculture",
    ):
        assert risk in text


def test_constitutional_convergence_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "identify historical tendencies",
        "surface recurring coherence patterns",
        "compare convergence trajectories",
        "explain governance stabilization pressure",
        "highlight recurring ambiguity",
        "recommend review",
        "trace convergence lineage",
        "classify plurality",
        "preserve minority paths",
        "link to source doctrine",
    ):
        assert allowed in text

    for forbidden in (
        "suppress minority interpretations",
        "collapse constitutional plurality",
        "optimize toward dominant coherence",
        "treat convergence as authority",
        "normalize ambiguity into legitimacy",
        "establish statistical supremacy",
        "erase alternative harmonization candidates",
        "weight legitimacy by majority tendency",
        "convert recurring pattern into doctrine",
        "present convergence as constitutional resolution",
    ):
        assert forbidden in text


def test_constitutional_convergence_policy_preserves_diversity() -> None:
    text = read_doc()

    for diversity_surface in (
        "interpretive plurality",
        "constitutional ambiguity space",
        "minority governance paths",
        "unresolved doctrinal tension",
        "alternative harmonization candidates",
        "dissenting interpretation lineage",
        "unresolved precedent divergence",
        "plurality-preserving review paths",
    ):
        assert diversity_surface in text

    assert "Constitutional diversity must remain visible until proper authority resolves the\nplurality." in text


def test_constitutional_convergence_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "convergence analysis id",
        "convergence analysis version",
        "source doctrine references",
        "historical tendency lineage",
        "ambiguity recurrence scope",
        "replay references when applicable",
        "convergence confidence",
        "plurality classification",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what is dominant vs minority",
        "what remains unresolved",
        "what is convergent vs authoritative",
        "what is statistically common but non-binding",
        "what ambiguity remains preserved",
        "what alternative paths remain viable",
        "what review path is required for resolution",
        "what authority boundary applies",
    ):
        assert transparency_field in text


def test_constitutional_convergence_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "plurality erosion",
        "dominance reinforcement loops",
        "ambiguity suppression pressure",
        "convergence-driven authority drift",
        "statistical legitimacy formation",
        "constitutional monoculture emergence",
        "minority path disappearance",
        "alternative harmonization suppression",
        "convergence confidence escalation",
        "ratification status loss",
    ):
        assert drift in text


def test_constitutional_convergence_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_convergence_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_convergence_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_convergence_validator" in text
    assert "This guard validates autonomous constitutional convergence governance." in text
    assert "not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous convergence may describe tendency.\n"
        "Constitutional plurality requires authority to resolve."
    ) in text
