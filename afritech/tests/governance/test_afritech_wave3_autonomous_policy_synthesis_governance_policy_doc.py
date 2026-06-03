from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Policy_Synthesis_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS POLICY SYNTHESIS GOVERNANCE POLICY",
    "ROLE: PREVENT GENERATED GOVERNANCE RULES, ADMISSIBILITY POLICIES, VALIDATOR LOGIC, LEGITIMACY BOUNDARIES, AND CONSTITUTIONAL CONSTRAINTS FROM SELF-RATIFYING AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

POLICY_SYNTHESIS_RISK_SURFACES = (
    "Governance Rule Generation",
    "Admissibility Policy Synthesis",
    "Validator Logic Generation",
    "Legitimacy Boundary Recommendation",
    "Constitutional Constraint Evolution",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_autonomous_policy_synthesis_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "governance need -> generated policy proposal -> self-ratified authority" in text
    assert "Policy synthesis may assist governance." in text
    assert "Policy synthesis must not become\ngovernance." in text


def test_autonomous_policy_synthesis_preserves_authority_stack() -> None:
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
        "Policy synthesis systems -> advisory proposal generation only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous policy synthesis governance constrains generated policy proposals" in text
    assert "It does not validate truth." in text


def test_autonomous_policy_synthesis_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in POLICY_SYNTHESIS_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Generated governance rules become active without ratification",
        "Generated admissibility policies redefine what the system admits as legitimate",
        "Generated validator logic becomes enforcement authority without governance review",
        "Generated recommendations redefine legitimacy by framing boundaries as accepted",
        "Generated constraints become shadow constitutional amendments",
    ):
        assert risk in text


def test_autonomous_policy_synthesis_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "draft",
        "compare",
        "explain",
        "summarize impact",
        "identify conflicts",
        "recommend review",
        "generate non-authoritative tests",
        "link to source doctrine",
        "propose ratification workflow",
        "produce advisory diffs",
    ):
        assert allowed in text

    for forbidden in (
        "ratify policy",
        "activate governance rules",
        "define legitimacy",
        "validate replay truth",
        "enforce validators",
        "modify authority hierarchy",
        "self-approve admissibility",
        "weaken existing guards",
        "mutate constitutional constraints",
        "present proposals as law",
    ):
        assert forbidden in text


def test_autonomous_policy_synthesis_requires_ratification_and_lineage() -> None:
    text = read_doc()

    for ratified_surface in (
        "admissibility",
        "replay validation",
        "validator enforcement",
        "constitutional invariants",
        "identity law",
        "witness requirements",
        "topology law",
        "authority hierarchy",
    ):
        assert ratified_surface in text

    for lineage_field in (
        "proposal id",
        "proposal version",
        "synthesis source",
        "source doctrine references",
        "affected authority surfaces",
        "affected validators",
        "affected replay fixtures",
        "ratification status",
        "reviewer or admitting authority when applicable",
        "authority disclaimer",
    ):
        assert lineage_field in text


def test_autonomous_policy_synthesis_requires_transparency_and_drift_detection() -> None:
    text = read_doc()

    for transparency_field in (
        "synthesis id",
        "synthesis type",
        "proposal status",
        "ratification status",
        "source doctrine references",
        "affected governance surfaces",
        "affected validation surfaces",
        "non-authoritative status",
        "required ratification path",
        "authority disclaimer",
    ):
        assert transparency_field in text

    for drift in (
        "self-ratified policy activation",
        "generated admissibility authority",
        "generated validator enforcement authority",
        "legitimacy boundary synthesis",
        "constitutional constraint mutation",
        "proposal presented as law",
        "ratification status loss",
        "source doctrine reference loss",
        "guard weakening through generated policy",
        "autonomous authority hierarchy modification",
    ):
        assert drift in text


def test_autonomous_policy_synthesis_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_policy_synthesis_policy.yaml" in text
    assert "schema: afritech.autonomous_policy_synthesis_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_policy_synthesis_validator" in text
    assert "This guard validates autonomous policy synthesis governance." in text
    assert "It must not\nvalidate replay truth or define legitimacy." in text
    assert (
        "Autonomous policy proposals require ratification.\n"
        "Generated policy cannot define legitimacy."
    ) in text
