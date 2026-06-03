from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Optimization_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS OPTIMIZATION GOVERNANCE POLICY",
    "ROLE: PREVENT SELF-TUNING, SELF-PRIORITIZING, SELF-REWEIGHTING, SELF-RECOMMENDING, AND SELF-ORCHESTRATING SYSTEMS FROM REDEFINING AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

OPTIMIZATION_RISK_SURFACES = (
    "Objective Admissibility",
    "Weight Stability",
    "Autonomous Recommendation Governance",
    "Autonomous Orchestration",
    "Autonomous Salience Optimization",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_autonomous_optimization_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "shared evidence -> autonomous optimization pressure -> system-generated authority drift" in text
    assert "Optimization may improve how operations run." in text
    assert "Optimization must not change what\nthe system treats as legitimate, true, severe, or governance-bearing." in text


def test_autonomous_optimization_policy_preserves_authority_stack() -> None:
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
        "Optimization systems -> execution improvement only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous optimization governance constrains optimization objectives" in text
    assert "It does not validate truth." in text


def test_autonomous_optimization_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in OPTIMIZATION_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Optimization objectives silently target truth friction instead of operational friction",
        "Self-tuning weights autonomously reclassify what matters",
        "Self-optimizing recommendations become operational authority",
        "Self-orchestration changes governance order or authority boundaries",
        "Self-prioritization makes operational convenience look like evidence importance",
    ):
        assert risk in text


def test_autonomous_optimization_policy_defines_allowed_and_forbidden_targets() -> None:
    text = read_doc()

    for allowed in (
        "latency",
        "throughput",
        "resource efficiency",
        "scheduling efficiency",
        "queue utilization",
        "retry efficiency",
        "workflow ergonomics",
        "cognitive navigation speed",
        "operational routing efficiency",
        "duplicate work reduction",
    ):
        assert allowed in text

    for forbidden in (
        "replay severity weighting",
        "validator interpretation",
        "hard failure visibility",
        "authority hierarchy",
        "legitimacy implication",
        "replay truth meaning",
        "salience baseline",
        "governance gate order",
        "source evidence lineage",
        "constitutional importance",
    ):
        assert forbidden in text


def test_autonomous_optimization_policy_contains_weight_and_recommendation_boundaries() -> None:
    text = read_doc()

    for invariant_weight in (
        "replay severity",
        "validator priority",
        "constitutional importance",
        "authority hierarchy",
        "governance visibility",
        "hard failure prominence",
        "replay mismatch significance",
        "legitimacy implication",
    ):
        assert invariant_weight in text

    for recommendation_boundary in (
        "infer legitimacy",
        "override validators",
        "suppress rejected-but-valid checks",
        "optimize away truth friction",
        "create hidden recommendation priority",
        "increase severity confidence from acceptance",
        "decrease severity from non-use",
        "Recommendation optimization remains advisory.",
    ):
        assert recommendation_boundary in text


def test_autonomous_optimization_policy_contains_orchestration_and_salience_boundaries() -> None:
    text = read_doc()

    for forbidden_orchestration in (
        "validator execution requirement",
        "replay validation requirement",
        "governance gate ordering",
        "authority hierarchy",
        "failure visibility",
        "admissibility meaning",
    ):
        assert forbidden_orchestration in text

    for salience_boundary in (
        "urgency meaning",
        "salience baseline",
        "hard failure emphasis",
        "replay conflict priority",
        "validator severity",
        "constitutional risk visibility",
    ):
        assert salience_boundary in text


def test_autonomous_optimization_policy_requires_transparency_and_drift_detection() -> None:
    text = read_doc()

    for transparency_field in (
        "optimization id",
        "optimization type",
        "objective function",
        "allowed optimization target",
        "forbidden optimization targets",
        "tunable weights",
        "invariant weights",
        "constraint set",
        "replay or validator boundary reference",
        "rollback path",
        "authority disclaimer",
    ):
        assert transparency_field in text

    for drift in (
        "autonomous salience drift",
        "autonomous urgency normalization",
        "recommendation convergence bias",
        "replay avoidance optimization",
        "governance friction suppression",
        "optimization-induced semantic drift",
        "hard failure visibility reduction",
        "validator priority reweighting",
        "authority hierarchy mutation",
        "source evidence lineage weakening",
    ):
        assert drift in text


def test_autonomous_optimization_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_optimization_policy.yaml" in text
    assert "schema: afritech.autonomous_optimization_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_optimization_validator" in text
    assert "This guard validates autonomous optimization governance." in text
    assert "It must not validate\nreplay truth or define legitimacy." in text
    assert (
        "Optimization may improve execution.\n"
        "Optimization may not redefine authority."
    ) in text
