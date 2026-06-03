from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Inevitability_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL INEVITABILITY GOVERNANCE POLICY",
    "ROLE: PREVENT FORECASTED GOVERNANCE TRAJECTORIES, PROBABILITY-WEIGHTED FUTURES, AND SELF-FULFILLING PREDICTION PRESSURE FROM BECOMING LEGITIMACY WITHOUT EXPLICIT AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

INEVITABILITY_RISK_SURFACES = (
    "Forecast Modeling vs Legitimacy Determination",
    "Constitutional Future Plurality Preservation",
    "Inevitability Lineage Governance",
    "Forecast Transparency",
    "Predictive Destiny Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_constitutional_inevitability_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "forecasted trajectory -> probability pressure -> prediction-derived legitimacy" in text
    assert "Inevitability analysis may improve human understanding of future governance" in text
    assert "Inevitability analysis must not pre-ratify constitutional futures." in text


def test_constitutional_inevitability_policy_preserves_authority_stack() -> None:
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
        "Inevitability systems -> advisory constitutional future analysis only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional inevitability governance constrains forecast modeling" in text
    assert "It does not validate truth." in text


def test_constitutional_inevitability_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in INEVITABILITY_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated forecasts treat high-probability futures as legitimate futures",
        "Autonomous inevitability analysis suppresses low-probability constitutional futures",
        "Generated inevitability analysis loses trajectory origin, probability classification, or ratification status",
        "Forecast analysis hides the difference between probability and legitimacy",
        "Repeated inevitability analysis creates authority through prediction",
    ):
        assert risk in text


def test_constitutional_inevitability_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "forecast governance pressure",
        "model likely trajectories",
        "identify self-fulfilling risks",
        "explain probability concentration",
        "compare future-space scenarios",
        "recommend review",
        "trace forecast lineage",
        "classify probability",
        "preserve future-space visibility",
        "link to source doctrine",
    ):
        assert allowed in text

    for forbidden in (
        "treat prediction as legitimacy",
        "pre-ratify constitutional futures",
        "optimize around inevitability pressure",
        "collapse future plurality into confidence",
        "convert forecasts into authority",
        "discourage admissible divergence",
        "suppress low-probability futures",
        "infer legitimacy from forecast confidence",
        "harden likely trajectories into doctrine",
        "present inevitability as constitutional destiny",
    ):
        assert forbidden in text


def test_constitutional_inevitability_policy_preserves_future_plurality() -> None:
    text = read_doc()

    for future_surface in (
        "low-probability constitutional futures",
        "authorized divergence",
        "alternative governance trajectories",
        "constitutional re-imagination",
        "future admissible possibility space",
        "minority future paths",
        "forecast-defying review paths",
        "uncertainty-preserving alternatives",
    ):
        assert future_surface in text

    assert "Constitutional futures must remain visible until proper authority resolves the\nfuture." in text


def test_constitutional_inevitability_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "inevitability analysis id",
        "inevitability analysis version",
        "source doctrine references",
        "trajectory lineage",
        "replay references when applicable",
        "probability classification",
        "future-space visibility",
        "forecast uncertainty",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what is probable vs legitimate",
        "what is forecasted vs authoritative",
        "what is self-fulfilling risk vs ratified future",
        "what futures remain open",
        "what divergence remains admissible",
        "what forecast uncertainty remains",
        "what review path is required for authority",
        "what authority boundary applies",
    ):
        assert transparency_field in text


def test_constitutional_inevitability_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "inevitability-based authority formation",
        "forecast supremacy pressure",
        "future-space collapse",
        "self-fulfilling legitimacy loops",
        "probability-derived governance drift",
        "predictive constitutional closure",
        "low-probability path suppression",
        "forecast-defying divergence discouragement",
        "forecast confidence escalation",
        "ratification status loss",
    ):
        assert drift in text


def test_constitutional_inevitability_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_inevitability_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_inevitability_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_inevitability_validator" in text
    assert "This guard validates autonomous constitutional inevitability governance." in text
    assert "not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous inevitability analysis may model futures.\n"
        "Constitutional futures cannot be pre-ratified by prediction."
    ) in text
