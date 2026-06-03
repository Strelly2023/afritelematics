from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Collective_Adaptive_Feedback_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: COLLECTIVE ADAPTIVE FEEDBACK GOVERNANCE POLICY",
    "ROLE: PREVENT AGGREGATE OPERATOR BEHAVIOR, USAGE ANALYTICS, AI REINFORCEMENT, AND RECOMMENDATION SUCCESS METRICS FROM TRAINING OPERATIONAL TRUTH",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

FEEDBACK_RISK_SURFACES = (
    "Aggregate Operator Behavior",
    "Click Pattern Optimization",
    "Recommendation Success Metrics",
    "Workflow Shortcut Reinforcement",
    "AI Reinforcement Feedback",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_collective_feedback_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "shared evidence -> aggregate behavior feedback -> organizationally trained operational reality" in text
    assert "Feedback may improve how humans reach evidence." in text
    assert "Feedback must not teach the\norganization which truths are operationally preferred." in text


def test_collective_feedback_policy_preserves_authority_stack() -> None:
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
        "Collective adaptive systems -> feedback-bounded ergonomic improvement only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Collective adaptive feedback governance constrains behavior-driven optimization." in text
    assert "It does not validate truth." in text


def test_collective_feedback_policy_declares_feedback_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in FEEDBACK_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Frequently ignored evidence becomes less visible because operators ignore it",
        "High-click narratives receive stronger operational emphasis than replay-valid evidence",
        "Accepted recommendations become self-reinforcing operational authority",
        "Shortcut usage trains systems to bypass difficult evidence",
        "AI learns which truths humans prefer and optimizes cognition around preference",
    ):
        assert risk in text


def test_collective_feedback_policy_defines_allowed_and_forbidden_feedback_targets() -> None:
    text = read_doc()

    for allowed in (
        "navigation friction",
        "workflow ergonomics",
        "layout usability",
        "disclosure pacing",
        "accessibility optimization",
        "interaction efficiency",
        "terminology clarity where meaning is preserved",
        "redundant action reduction",
    ):
        assert allowed in text

    for forbidden in (
        "replay severity weighting",
        "validator interpretation",
        "hard failure visibility",
        "salience normalization",
        "narrative truth adaptation",
        "authority hierarchy modification",
        "legitimacy implication",
        "replay mismatch meaning",
        "source evidence lineage",
        "governance failure visibility",
    ):
        assert forbidden in text


def test_collective_feedback_policy_contains_recommendation_and_ai_boundaries() -> None:
    text = read_doc()

    for recommendation_boundary in (
        "which failures operators ignore",
        "which replay traces operators avoid",
        "which governance warnings get dismissed",
        "which incidents operators prefer minimized",
        "which authority disclaimers are skipped",
        "Recommendation acceptance is not evidence.",
    ):
        assert recommendation_boundary in text

    for ai_boundary in (
        "improving phrasing clarity",
        "source reference navigation",
        "omitted detail warnings",
        "legitimacy inference",
        "replay truth synthesis",
        "urgency escalation",
        "severity softening",
        "hidden evidence suppression",
        "behaviorally preferred narrative conclusions",
    ):
        assert ai_boundary in text


def test_collective_feedback_policy_names_behavioral_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "replay avoidance reinforcement",
        "salience desensitization",
        "failure suppression trends",
        "narrative shortcut reinforcement",
        "recommendation bias accumulation",
        "operator habituation patterns",
        "truth-friction optimization",
        "low-engagement evidence demotion",
        "AI convenience overfitting",
        "authority disclaimer erosion",
    ):
        assert drift in text


def test_collective_feedback_policy_requires_feedback_transparency() -> None:
    text = read_doc()

    for transparency_field in (
        "feedback signal id",
        "feedback signal type",
        "optimization objective",
        "allowed optimization target",
        "forbidden optimization targets",
        "source evidence protection rule",
        "salience baseline protection rule",
        "AI feedback boundary when applicable",
        "authority disclaimer",
        "opt-out or inspection path for feedback influence",
    ):
        assert transparency_field in text

    assert "how humans reach truth" in text
    assert "what truth becomes operationally emphasized" in text


def test_collective_feedback_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/collective_adaptive_feedback_policy.yaml" in text
    assert "schema: afritech.collective_adaptive_feedback_policy.v1" in text
    assert "python3 -m afritech.ci.collective_adaptive_feedback_validator" in text
    assert "This guard validates collective adaptive feedback governance." in text
    assert "It must not\nvalidate replay truth or define legitimacy." in text
    assert (
        "Feedback may improve ergonomics.\n"
        "Feedback may not train truth."
    ) in text
