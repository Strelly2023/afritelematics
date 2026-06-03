from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Anticipatory_Suppression_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL ANTICIPATORY SUPPRESSION GOVERNANCE POLICY",
    "ROLE: PREVENT FUTURE-RISK FORECASTS, INSTABILITY SCENARIOS, UNCERTAINTY PRESSURE, AND PREVENTIVE CONTROL LOOPS FROM PREEMPTIVELY CLOSING ADMISSIBLE CONSTITUTIONAL FUTURES",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

ANTICIPATORY_RISK_SURFACES = (
    "Risk Surfacing vs Future Suppression",
    "Constitutional Possibility Preservation",
    "Anticipatory Lineage Governance",
    "Uncertainty Transparency",
    "Preventive Closure Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_anticipatory_suppression_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "forecast risk -> preventive suppression -> future-space closure" in text
    assert "Anticipatory analysis may improve human understanding of future governance risk." in text
    assert "Anticipatory analysis must not become preventive constitutional closure." in text


def test_anticipatory_suppression_policy_preserves_authority_stack() -> None:
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
        "Autonomous Constitutional Equilibrium Governance Policy -> stability analysis without persistence-derived legitimacy",
        "Autonomous Constitutional Path Dependence Governance Policy -> trajectory analysis without destiny formation",
        "Autonomous Constitutional Inevitability Governance Policy -> future analysis without prediction-derived legitimacy",
        "Autonomous Constitutional Inevitability Reinforcement Governance Policy -> predictive pressure analysis without operational future preselection",
        "Autonomous Constitutional Anticipatory Suppression Governance Policy -> risk analysis without preventive future closure",
        "Anticipatory suppression systems -> advisory constitutional risk analysis only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional anticipatory suppression governance constrains risk" in text
    assert "It does not validate\ntruth." in text


def test_anticipatory_suppression_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in ANTICIPATORY_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated risk analysis treats uncertainty as a reason to close admissible futures",
        "Autonomous anticipation suppresses uncertain but admissible constitutional futures",
        "Generated anticipatory analysis loses forecast lineage, risk classification, or ratification status",
        "Anticipatory analysis hides the difference between risky and illegitimate",
        "Repeated anticipatory analysis prevents futures before authority can review them",
    ):
        assert risk in text


def test_anticipatory_suppression_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "identify instability scenarios",
        "expose forecast-risky futures",
        "explain uncertainty pressure",
        "surface divergence risks",
        "compare possible governance trajectories",
        "recommend review",
        "trace anticipatory lineage",
        "classify risk",
        "preserve future-space visibility",
        "link to source doctrine",
    ):
        assert allowed in text

    for forbidden in (
        "suppress admissible futures",
        "treat uncertainty as illegitimacy",
        "preemptively narrow possibility space",
        "avoid divergence because it is risky",
        "collapse admissible plurality",
        "convert forecast instability into governance exclusion",
        "suppress constitutional experimentation",
        "infer illegitimacy from risk classification",
        "harden risk forecasts into exclusion rules",
        "present anticipatory suppression as constitutional protection",
    ):
        assert forbidden in text


def test_anticipatory_suppression_policy_preserves_constitutional_possibility() -> None:
    text = read_doc()

    for future_surface in (
        "authorized divergence",
        "uncertain governance futures",
        "low-confidence constitutional trajectories",
        "alternative admissible futures",
        "constitutional experimentation space",
        "risk-bearing review paths",
        "instability-exposed but admissible options",
        "uncertainty-preserving alternatives",
    ):
        assert future_surface in text

    assert "Constitutional possibility must remain visible until proper authority resolves\nthe future." in text


def test_anticipatory_suppression_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "anticipatory analysis id",
        "anticipatory analysis version",
        "source doctrine references",
        "forecast lineage",
        "replay references when applicable",
        "risk classification",
        "future-space visibility",
        "uncertainty disclosure",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what is risky vs illegitimate",
        "what is unstable vs inadmissible",
        "what futures remain open",
        "what divergence remains admissible",
        "what uncertainty is preserved",
        "what risk is forecasted but unresolved",
        "what review path is required for authority",
        "what authority boundary applies",
    ):
        assert transparency_field in text


def test_anticipatory_suppression_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "anticipatory future suppression",
        "uncertainty-based exclusion",
        "preventive constitutional closure",
        "risk-derived legitimacy drift",
        "divergence suppression pressure",
        "future-space collapse",
        "instability-based inadmissibility inference",
        "experimentation path disappearance",
        "risk confidence escalation",
        "ratification status loss",
    ):
        assert drift in text


def test_anticipatory_suppression_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_anticipatory_suppression_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_anticipatory_suppression_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_anticipatory_suppression_validator" in text
    assert "This guard validates autonomous constitutional anticipatory suppression" in text
    assert "must not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous anticipation may warn.\n"
        "Constitutional possibility cannot be preemptively closed."
    ) in text
