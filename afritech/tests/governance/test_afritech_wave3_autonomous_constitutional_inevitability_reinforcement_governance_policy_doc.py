from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Inevitability_Reinforcement_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL INEVITABILITY REINFORCEMENT GOVERNANCE POLICY",
    "ROLE: PREVENT FORECAST-DRIVEN RESOURCE ROUTING, SALIENCE AMPLIFICATION, RECOMMENDATION REINFORCEMENT, AND ANTICIPATORY OPTIMIZATION FROM OPERATIONALLY PRESELECTING CONSTITUTIONAL FUTURES WITHOUT EXPLICIT AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

REINFORCEMENT_RISK_SURFACES = (
    "Forecast Monitoring vs Operational Future Selection",
    "Constitutional Future-Space Neutrality",
    "Reinforcement Lineage Governance",
    "Predictive Influence Transparency",
    "Self-Fulfilling Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_inevitability_reinforcement_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "forecasted future -> operational reinforcement -> self-fulfilling legitimacy" in text
    assert "Inevitability reinforcement analysis may improve human understanding of" in text
    assert "Inevitability reinforcement analysis must\nnot operationalize predicted legitimacy." in text


def test_inevitability_reinforcement_policy_preserves_authority_stack() -> None:
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
        "Inevitability reinforcement systems -> advisory self-fulfilling pressure analysis only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional inevitability reinforcement governance constrains" in text
    assert "It does not\nvalidate truth." in text


def test_inevitability_reinforcement_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in REINFORCEMENT_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated reinforcement analysis routes operations toward predicted legitimacy",
        "Autonomous reinforcement biases operational systems toward predicted constitutional futures",
        "Generated reinforcement analysis loses forecast lineage, operational influence visibility, or ratification status",
        "Reinforcement analysis hides the difference between forecast and operational amplification",
        "Repeated reinforcement analysis helps forecasts become true",
    ):
        assert risk in text


def test_inevitability_reinforcement_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "detect self-fulfilling forecast pressure",
        "explain reinforcement loops",
        "identify predictive amplification",
        "surface anticipatory optimization risk",
        "compare forecast influence patterns",
        "recommend review",
        "trace reinforcement lineage",
        "classify operational influence",
        "preserve future-space neutrality",
        "link to source doctrine",
    ):
        assert allowed in text

    for forbidden in (
        "route resources toward predicted legitimacy",
        "amplify futures because they are likely",
        "preselect constitutional trajectories",
        "optimize operations around inevitability",
        "convert forecast confidence into governance pressure",
        "suppress admissible alternatives operationally",
        "bias salience toward predicted futures",
        "bias recommendations toward predicted futures",
        "bias optimization toward predicted futures",
        "present forecast reinforcement as constitutional destiny",
    ):
        assert forbidden in text


def test_inevitability_reinforcement_policy_preserves_future_space_neutrality() -> None:
    text = read_doc()

    for surface in (
        "resource allocation",
        "salience routing",
        "optimization pressure",
        "recommendation systems",
        "workflow prioritization",
        "operational visibility",
        "evidence surfacing",
        "review path availability",
    ):
        assert surface in text

    assert "toward predicted constitutional futures without explicit authority." in text


def test_inevitability_reinforcement_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "reinforcement analysis id",
        "reinforcement analysis version",
        "source doctrine references",
        "forecast lineage",
        "replay references when applicable",
        "reinforcement classification",
        "operational influence visibility",
        "uncertainty disclosure",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what is forecast vs operationally amplified",
        "what is probable vs operationally prioritized",
        "what is self-fulfilling risk vs ratified future",
        "what futures remain operationally open",
        "what reinforcement pressure exists",
        "what operational influence is already occurring",
        "what review path is required for authority",
        "what authority boundary applies",
    ):
        assert transparency_field in text


def test_inevitability_reinforcement_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "prediction-driven resource concentration",
        "inevitability reinforcement loops",
        "operational future preselection",
        "forecast-amplified governance pressure",
        "self-fulfilling legitimacy drift",
        "predictive constitutional closure",
        "salience amplification of predicted futures",
        "recommendation convergence toward forecasts",
        "optimization alignment with probability",
        "ratification status loss",
    ):
        assert drift in text


def test_inevitability_reinforcement_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_inevitability_reinforcement_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_inevitability_reinforcement_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_inevitability_reinforcement_validator" in text
    assert "This guard validates autonomous constitutional inevitability reinforcement" in text
    assert "must not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous reinforcement may monitor prediction effects.\n"
        "Constitutional futures cannot be operationally preselected."
    ) in text
