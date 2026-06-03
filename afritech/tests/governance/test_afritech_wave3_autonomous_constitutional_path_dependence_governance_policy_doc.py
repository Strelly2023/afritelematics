from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Path_Dependence_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL PATH DEPENDENCE GOVERNANCE POLICY",
    "ROLE: PREVENT HISTORICAL TRAJECTORY, STRUCTURAL LOCK-IN, CONTINUITY PRESSURE, AND NARROWING POSSIBILITY SPACES FROM BECOMING CONSTITUTIONAL DESTINY WITHOUT EXPLICIT AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

PATH_DEPENDENCE_RISK_SURFACES = (
    "Historical Constraint vs Constitutional Destiny",
    "Constitutional Future Preservation",
    "Path Dependence Lineage Governance",
    "Constraint Transparency",
    "Path Inertia Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_constitutional_path_dependence_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "historical trajectory -> inherited constraint -> trajectory-derived destiny" in text
    assert "Path dependence analysis may improve human understanding of inherited" in text
    assert "Path dependence analysis must not foreclose\nconstitutional futures." in text


def test_constitutional_path_dependence_policy_preserves_authority_stack() -> None:
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
        "Path dependence systems -> advisory constitutional trajectory analysis only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional path dependence governance constrains historical" in text
    assert "It does not validate truth." in text


def test_constitutional_path_dependence_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in PATH_DEPENDENCE_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated path analysis treats inherited trajectory as constitutional destiny",
        "Autonomous path analysis narrows future constitutional possibility space",
        "Generated path analysis loses trajectory origin, lock-in classification, or ratification status",
        "Path analysis hides the difference between inherited constraint and authority",
        "Repeated path analysis turns inherited trajectory into constitutional inevitability",
    ):
        assert risk in text


def test_constitutional_path_dependence_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "expose inherited constraints",
        "identify trajectory lock-in",
        "explain continuity pressure",
        "map narrowing possibility spaces",
        "compare alternative governance paths",
        "recommend review",
        "trace path lineage",
        "classify lock-in",
        "preserve future-space visibility",
        "link to source doctrine",
    ):
        assert allowed in text

    for forbidden in (
        "treat historical trajectory as legitimacy",
        "foreclose constitutional futures",
        "optimize toward inherited continuity",
        "convert lock-in into authority",
        "discourage authorized divergence",
        "suppress governance re-imagination",
        "infer legitimacy from continuity duration",
        "harden trajectory into doctrine",
        "collapse future admissible possibility space",
        "present path dependence as constitutional destiny",
    ):
        assert forbidden in text


def test_constitutional_path_dependence_policy_preserves_future_space() -> None:
    text = read_doc()

    for future_surface in (
        "alternative constitutional futures",
        "authorized divergence",
        "governance re-imagination",
        "constitutional plurality",
        "future admissible possibility space",
        "reform review paths",
        "minority future trajectories",
        "trajectory-breaking authority paths",
    ):
        assert future_surface in text

    assert "Constitutional futures must remain visible until proper authority resolves the\npath." in text


def test_constitutional_path_dependence_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "path analysis id",
        "path analysis version",
        "source doctrine references",
        "historical trajectory lineage",
        "replay references when applicable",
        "lock-in classification",
        "future-space visibility",
        "divergence potential",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what is inherited vs legitimate",
        "what is constrained vs authoritative",
        "what is path-dependent vs constitutionally required",
        "what futures remain open",
        "what divergence remains possible",
        "what lock-in remains reversible",
        "what review path is required for authority",
        "what authority boundary applies",
    ):
        assert transparency_field in text


def test_constitutional_path_dependence_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "constitutional destiny formation",
        "inherited continuity supremacy",
        "future-space collapse",
        "path lock-in hardening",
        "trajectory-based legitimacy drift",
        "constitutional inevitability pressure",
        "divergence discouragement",
        "trajectory-breaking path disappearance",
        "lock-in confidence escalation",
        "ratification status loss",
    ):
        assert drift in text


def test_constitutional_path_dependence_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_path_dependence_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_path_dependence_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_path_dependence_validator" in text
    assert "This guard validates autonomous constitutional path dependence governance." in text
    assert "not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous path analysis may reveal lock-in.\n"
        "Constitutional futures require authority."
    ) in text
