from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Interpretation_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL INTERPRETATION GOVERNANCE POLICY",
    "ROLE: PREVENT GENERATED CONSTITUTIONAL INTERPRETATION FROM RESOLVING LEGITIMACY, ADMISSIBILITY, AUTHORITY CONFLICTS, OR CONSTITUTIONAL MEANING WITHOUT EXPLICIT AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

INTERPRETATION_RISK_SURFACES = (
    "Explanation vs Resolution",
    "Constitutional Ambiguity Containment",
    "Interpretation Lineage Governance",
    "Ambiguity Transparency",
    "Interpretation Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_constitutional_interpretation_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "constitutional ambiguity -> generated interpretation -> self-resolved legitimacy" in text
    assert "Interpretation may improve human understanding of uncertainty." in text
    assert "Interpretation\nmust not become constitutional adjudication." in text


def test_constitutional_interpretation_policy_preserves_authority_stack() -> None:
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
        "Interpretation systems -> advisory constitutional explanation only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional interpretation governance constrains ambiguity" in text
    assert "It does not validate truth." in text


def test_constitutional_interpretation_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in INTERPRETATION_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated interpretation explains ambiguity so strongly that it becomes resolution",
        "Autonomous systems independently settle ambiguity around authority-bearing surfaces",
        "Generated interpretations lose source doctrine, uncertainty scope, or authority status",
        "Generated interpretation hides what remains unresolved",
        "Repeated autonomous interpretation converges toward unofficial constitutional meaning",
    ):
        assert risk in text


def test_constitutional_interpretation_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "surface ambiguity",
        "compare source doctrine",
        "map possible readings",
        "summarize precedent",
        "explain uncertainty",
        "recommend review",
        "trace interpretation lineage",
        "identify conflicting governance surfaces",
        "classify uncertainty",
        "link to source doctrine",
    ):
        assert allowed in text

    for forbidden in (
        "resolve legitimacy",
        "settle admissibility disputes",
        "determine constitutional meaning",
        "ratify interpretation",
        "define authority hierarchy",
        "reinterpret replay truth",
        "override validators",
        "harmonize contradictions authoritatively",
        "convert ambiguity into law",
        "present interpretation as constitutional authority",
    ):
        assert forbidden in text


def test_constitutional_interpretation_policy_contains_ambiguity_containment() -> None:
    text = read_doc()

    for ambiguity_surface in (
        "legitimacy boundaries",
        "replay authority",
        "validator supremacy",
        "constitutional invariants",
        "authority hierarchy",
        "admissibility meaning",
        "identity law",
        "witness requirements",
        "closed-world semantics",
    ):
        assert ambiguity_surface in text

    assert "Ambiguity must remain visible until resolved by proper authority." in text


def test_constitutional_interpretation_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "interpretation id",
        "interpretation version",
        "source doctrine references",
        "ambiguity scope",
        "replay references when applicable",
        "conflicting surfaces",
        "interpretation lineage",
        "uncertainty classification",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what is ambiguous",
        "what is settled",
        "what is interpretive",
        "what is replay-derived",
        "what requires authority review",
        "what remains unresolved",
        "what source doctrine was used",
        "what authority boundary applies",
    ):
        assert transparency_field in text


def test_constitutional_interpretation_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "autonomous legitimacy settlement",
        "interpretation convergence drift",
        "ambiguity suppression",
        "replay reinterpretation pressure",
        "constitutional extrapolation",
        "authority compression",
        "admissibility dispute settlement",
        "ratification status loss",
        "source doctrine reference loss",
        "unresolved ambiguity disappearance",
    ):
        assert drift in text


def test_constitutional_interpretation_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_interpretation_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_interpretation_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_interpretation_validator" in text
    assert "This guard validates autonomous constitutional interpretation governance." in text
    assert "must not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous interpretation may advise.\n"
        "Constitutional meaning requires authority."
    ) in text
