from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Equilibrium_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL EQUILIBRIUM GOVERNANCE POLICY",
    "ROLE: PREVENT SELF-MAINTAINING GOVERNANCE STATES, PERSISTENT ATTRACTORS, AND STABILITY PRESSURE FROM BECOMING CONSTITUTIONAL AUTHORITY WITHOUT EXPLICIT AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

EQUILIBRIUM_RISK_SURFACES = (
    "Stability Modeling vs Authority Preservation",
    "Constitutional Dynamism Preservation",
    "Equilibrium Lineage Governance",
    "Stability Transparency",
    "Equilibrium Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_constitutional_equilibrium_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "stable governance state -> self-maintaining attractor -> persistence-derived authority" in text
    assert "Equilibrium modeling may improve human understanding of governance stability." in text
    assert "Equilibrium modeling must not become constitutional legitimacy." in text


def test_constitutional_equilibrium_policy_preserves_authority_stack() -> None:
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
        "Equilibrium systems -> advisory constitutional stability analysis only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional equilibrium governance constrains stability modeling" in text
    assert "It does not validate truth." in text


def test_constitutional_equilibrium_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in EQUILIBRIUM_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated equilibrium analysis treats persistent states as legitimate states",
        "Autonomous equilibrium suppresses legitimate constitutional movement",
        "Generated equilibrium analysis loses persistence origin, attractor classification, or ratification status",
        "Equilibrium analysis hides the difference between persistence and legitimacy",
        "Repeated equilibrium modeling creates authority through inertia",
    ):
        assert risk in text


def test_constitutional_equilibrium_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "model governance stability",
        "identify attractor states",
        "explain persistence patterns",
        "surface self-reinforcing loops",
        "compare equilibrium trajectories",
        "recommend review",
        "trace equilibrium lineage",
        "classify attractors",
        "preserve divergence visibility",
        "link to source doctrine",
    ):
        assert allowed in text

    for forbidden in (
        "treat persistence as legitimacy",
        "preserve authority by inertia",
        "stabilize dominance into supremacy",
        "optimize for constitutional permanence",
        "discourage legitimate divergence",
        "convert equilibrium into authority",
        "suppress constitutional re-evaluation",
        "infer legitimacy from stability duration",
        "harden attractors into doctrine",
        "present equilibrium as constitutional resolution",
    ):
        assert forbidden in text


def test_constitutional_equilibrium_policy_preserves_dynamism() -> None:
    text = read_doc()

    for dynamism_surface in (
        "constitutional plurality",
        "legitimate governance evolution",
        "minority ambiguity paths",
        "constitutional re-evaluation",
        "authorized divergence",
        "unresolved doctrinal tension",
        "alternative equilibrium candidates",
        "reform review paths",
    ):
        assert dynamism_surface in text

    assert "Constitutional dynamism must remain visible until proper authority resolves the\nquestion." in text


def test_constitutional_equilibrium_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "equilibrium analysis id",
        "equilibrium analysis version",
        "source doctrine references",
        "persistence lineage",
        "replay references when applicable",
        "equilibrium confidence",
        "attractor classification",
        "divergence visibility",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what is stable vs legitimate",
        "what is persistent vs authoritative",
        "what is attractor-like vs ratified",
        "what is self-maintaining vs constitutionally valid",
        "what divergence remains possible",
        "what alternate equilibria remain visible",
        "what review path is required for authority",
        "what authority boundary applies",
    ):
        assert transparency_field in text


def test_constitutional_equilibrium_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "persistence-based authority formation",
        "governance inertia accumulation",
        "equilibrium supremacy pressure",
        "divergence suppression",
        "constitutional attractor hardening",
        "stability-legitimacy conflation",
        "permanence optimization pressure",
        "alternative equilibrium disappearance",
        "equilibrium confidence escalation",
        "ratification status loss",
    ):
        assert drift in text


def test_constitutional_equilibrium_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_equilibrium_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_equilibrium_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_equilibrium_validator" in text
    assert "This guard validates autonomous constitutional equilibrium governance." in text
    assert "not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous equilibrium may model stability.\n"
        "Constitutional authority cannot emerge from persistence."
    ) in text
