from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Objective_Evolution_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS OBJECTIVE EVOLUTION GOVERNANCE POLICY",
    "ROLE: PREVENT SELF-GENERATED GOALS, EVOLVING SUCCESS METRICS, REINFORCEMENT TARGETS, AND SYNTHESIZED ORCHESTRATION PRIORITIES FROM SELF-AUTHORIZING GOVERNANCE AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

OBJECTIVE_RISK_SURFACES = (
    "Objective Admissibility",
    "Objective Lineage",
    "Self-Generated Goal Restrictions",
    "Reinforcement Target Governance",
    "Success Metric Evolution",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_autonomous_objective_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "approved optimization -> evolved objective -> self-authorized authority" in text
    assert "Objectives may improve how the system operates." in text
    assert "Objectives must not define what\nthe system treats as legitimate or true." in text


def test_autonomous_objective_policy_preserves_authority_stack() -> None:
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
        "Objective systems -> admitted operational goals only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous objective evolution governance constrains goal formation" in text
    assert "It does not\nvalidate truth." in text


def test_autonomous_objective_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in OBJECTIVE_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Autonomous systems generate objectives that redefine authority-bearing semantics",
        "Objectives mutate without visible origin, admission source, or governance version",
        "Self-generated goals affect truth-bearing operational semantics",
        "Reinforcement targets teach systems which truths are operationally inconvenient",
        "Success metrics evolve toward convenience over constitutional integrity",
    ):
        assert risk in text


def test_autonomous_objective_policy_defines_allowed_and_forbidden_domains() -> None:
    text = read_doc()

    for allowed in (
        "queue efficiency",
        "scheduling optimization",
        "latency reduction",
        "cache locality",
        "retry minimization",
        "resource utilization",
        "routing efficiency",
        "duplicate work reduction",
    ):
        assert allowed in text

    for forbidden in (
        "legitimacy",
        "replay authority",
        "validator meaning",
        "governance severity",
        "constitutional priority",
        "authority hierarchy",
        "replay truth meaning",
        "admissibility semantics",
    ):
        assert forbidden in text


def test_autonomous_objective_policy_requires_lineage_and_admission() -> None:
    text = read_doc()

    for lineage_field in (
        "objective id",
        "objective version",
        "admission source",
        "governance version",
        "constitutional classification",
        "parent objective when derived",
        "mutation history",
        "rollback path",
        "authority disclaimer",
    ):
        assert lineage_field in text

    assert "Self-generated goals may be proposed. They must not become active without\nadmission." in text


def test_autonomous_objective_policy_contains_reinforcement_and_metric_boundaries() -> None:
    text = read_doc()

    for forbidden_reinforcement in (
        "reduced governance interruptions",
        "reduced validator failures by suppression",
        "reduced replay mismatch visibility",
        "higher operator acceptance of softened failures",
        "lower hard failure exposure",
        "increased legitimacy confidence from throughput",
    ):
        assert forbidden_reinforcement in text

    for forbidden_metric in (
        "legitimacy scoring",
        "replay truth confidence",
        "validator severity reduction",
        "governance burden minimization",
        "hard failure exposure reduction",
        "authority hierarchy compression",
    ):
        assert forbidden_metric in text


def test_autonomous_objective_policy_requires_transparency_and_drift_detection() -> None:
    text = read_doc()

    for transparency_field in (
        "objective id",
        "objective version",
        "prior objective version",
        "admission source",
        "admission status",
        "objective lineage",
        "mutation reason",
        "allowed evolution target",
        "forbidden evolution targets",
        "reinforcement target when applicable",
        "rollback path",
        "authority disclaimer",
    ):
        assert transparency_field in text

    for drift in (
        "evolving optimization priorities",
        "reinforcement convergence drift",
        "governance de-emphasis",
        "replay visibility erosion",
        "salience normalization",
        "authority compression pressure",
        "validator reprioritization",
        "hard failure exposure reduction",
        "self-authorized objective activation",
        "objective lineage loss",
    ):
        assert drift in text


def test_autonomous_objective_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_objective_policy.yaml" in text
    assert "schema: afritech.autonomous_objective_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_objective_validator" in text
    assert "This guard validates autonomous objective evolution governance." in text
    assert "It must not\nvalidate replay truth or define legitimacy." in text
    assert (
        "Objective evolution requires admission.\n"
        "Autonomous objectives cannot define authority."
    ) in text
