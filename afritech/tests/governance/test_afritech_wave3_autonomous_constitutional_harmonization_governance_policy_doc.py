from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Harmonization_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL HARMONIZATION GOVERNANCE POLICY",
    "ROLE: PREVENT GENERATED HARMONIZATION FROM RESOLVING CONSTITUTIONAL SUPREMACY, COLLAPSING DOCTRINAL PLURALITY, OR CREATING UNIFIED LEGITIMACY MODELS WITHOUT EXPLICIT AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

HARMONIZATION_RISK_SURFACES = (
    "Conflict Mapping vs Supremacy Resolution",
    "Constitutional Surface Preservation",
    "Harmonization Lineage Governance",
    "Conflict Transparency",
    "Harmonization Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_constitutional_harmonization_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "constitutional conflict -> generated harmonization -> self-determined supremacy" in text
    assert "Harmonization may improve human understanding of constitutional conflict." in text
    assert "Harmonization must not become constitutional supremacy adjudication." in text


def test_constitutional_harmonization_policy_preserves_authority_stack() -> None:
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
        "Harmonization systems -> advisory constitutional conflict mapping only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional harmonization governance constrains conflict mapping" in text
    assert "It does not validate truth." in text


def test_constitutional_harmonization_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in HARMONIZATION_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated conflict maps become hidden supremacy decisions",
        "Generated harmonization collapses or subordinates independent constitutional surfaces",
        "Generated harmonization loses conflict origin, reconciliation candidate history, or ratification status",
        "Generated harmonization hides unresolved constitutional tension",
        "Repeated autonomous harmonization converges toward unofficial constitutional supremacy",
    ):
        assert risk in text


def test_constitutional_harmonization_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "identify conflicting doctrine",
        "map constitutional overlap",
        "trace affected surfaces",
        "compare reconciliation models",
        "summarize tension",
        "recommend review",
        "explain incompatibility",
        "preserve independent surface visibility",
        "classify unresolved conflict",
        "link to source doctrine",
    ):
        assert allowed in text

    for forbidden in (
        "resolve supremacy",
        "select dominant authority",
        "determine legitimacy precedence",
        "rewrite invariants",
        "collapse constitutional plurality",
        "dilute replay authority",
        "erode validator hierarchy",
        "ratify harmonized meaning",
        "create unified legitimacy models",
        "present candidate coherence as constitutional law",
    ):
        assert forbidden in text


def test_constitutional_harmonization_policy_preserves_constitutional_surfaces() -> None:
    text = read_doc()

    for surface in (
        "constitutional invariants",
        "replay authority",
        "validator supremacy",
        "legitimacy hierarchy",
        "admissibility boundaries",
        "governance ordering",
        "identity law",
        "witness requirements",
        "closed-world semantics",
    ):
        assert surface in text

    assert "Independent surfaces must remain visible until proper authority resolves the\nconflict." in text


def test_constitutional_harmonization_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "harmonization id",
        "harmonization version",
        "conflicting surfaces",
        "reconciliation candidates",
        "replay implications",
        "ambiguity scope",
        "doctrinal references",
        "harmonization lineage",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what conflicts exist",
        "what remains unresolved",
        "what is harmonized vs interpretive",
        "what requires authority review",
        "what constitutional surfaces remain independent",
        "what reconciliation candidates were considered",
        "what candidate was rejected and why",
        "what authority boundary applies",
    ):
        assert transparency_field in text


def test_constitutional_harmonization_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "autonomous supremacy settlement",
        "constitutional collapse pressure",
        "invariant compression",
        "replay authority dilution",
        "validator hierarchy erosion",
        "synthetic coherence generation",
        "legitimacy precedence inference",
        "ratification status loss",
        "doctrinal reference loss",
        "unresolved conflict disappearance",
    ):
        assert drift in text


def test_constitutional_harmonization_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_harmonization_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_harmonization_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_harmonization_validator" in text
    assert "This guard validates autonomous constitutional harmonization governance." in text
    assert "must not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous harmonization may propose coherence.\n"
        "Constitutional supremacy requires authority."
    ) in text
