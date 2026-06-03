from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave2_Temporal_Cognition_Consistency_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 2 CONTROL ARTIFACT",
    "CLASSIFICATION: TEMPORAL COGNITION CONSISTENCY POLICY",
    "ROLE: PREVENT HUMAN-FACING COGNITION FROM PRODUCING DIFFERENT OPERATIONAL REALITIES FROM THE SAME EVIDENCE OVER TIME",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

DRIFT_SURFACES = (
    "Epoch Evolution",
    "Translator Evolution",
    "UI Redesign",
    "AI Model Upgrade",
    "Summary Template Evolution",
    "Policy Evolution",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_temporal_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "same evidence -> future cognition surface -> different operational reality" in text
    assert "Time may improve cognition. Time must not rewrite operational meaning." in text


def test_temporal_policy_preserves_authority_stack() -> None:
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
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Temporal cognition consistency governs longitudinal interpretation stability." in text
    assert "It\ndoes not validate truth." in text


def test_temporal_policy_declares_drift_surfaces() -> None:
    text = read_doc()

    for drift_surface in DRIFT_SURFACES:
        assert drift_surface in text

    for containment in (
        "epoch context must remain visible",
        "translator version must be visible",
        "status semantics remain stable",
        "model version must be visible",
        "template version must be visible",
        "policy version must be visible",
    ):
        assert containment in text


def test_temporal_policy_defines_explanation_salience_and_narrative_stability() -> None:
    text = read_doc()

    for explanation_requirement in (
        "explanation identifiers",
        "source references",
        "replay implications",
        "validator semantics",
        "status meaning",
        "authority boundary",
    ):
        assert explanation_requirement in text

    for salience_requirement in (
        "salience policy version visible",
        "ordering rule version visible",
        "urgency classification version visible",
        "AI salience model version visible",
        "old and new salience classifications comparable",
    ):
        assert salience_requirement in text

    for narrative_requirement in (
        "preserve composition source ids",
        "preserve transformation steps",
        "preserve authority disclaimers",
        "expose narrative template version",
        "expose summarization policy version",
    ):
        assert narrative_requirement in text


def test_temporal_policy_contains_ai_and_ordering_boundaries() -> None:
    text = read_doc()

    for ai_field in (
        "model identifier",
        "prompt or template version",
        "source explanation ids",
        "salience policy version",
        "advisory status",
        "omitted detail indicator",
        "authority disclaimer",
    ):
        assert ai_field in text

    for forbidden_ai in (
        "infer legitimacy from old evidence",
        "synthesize replay truth",
        "change hard failure severity",
        "hide old evidence",
        "create model-version-dependent operational reality",
    ):
        assert forbidden_ai in text

    for forbidden_ordering in (
        "hidden priority rewrite",
        "AI model preference ordering",
        "dashboard redesign ordering without declaration",
        "runtime-order-dependent historical replay display",
        "removing hard failures from top-level historical view",
    ):
        assert forbidden_ordering in text


def test_temporal_policy_requires_evolution_transparency_and_drift_detection() -> None:
    text = read_doc()

    for context_field in (
        "evidence id",
        "explanation schema version",
        "composition schema version",
        "cognitive complexity budget version",
        "salience policy version",
        "summary template version",
        "AI model version when applicable",
        "epoch context when applicable",
        "translator context when applicable",
        "authority disclaimer",
    ):
        assert context_field in text

    for drift_check in (
        "summary drift",
        "salience drift",
        "explanation reinterpretation",
        "narrative divergence",
        "AI model cognition instability",
        "hard failure softening",
        "source reference loss",
        "authority disclaimer loss",
        "epoch context loss",
        "translator context loss",
    ):
        assert drift_check in text


def test_temporal_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/temporal_cognition_policy.yaml" in text
    assert "schema: afritech.temporal_cognition_policy.v1" in text
    assert "python3 -m afritech.ci.temporal_cognition_validator" in text
    assert "This guard validates temporal cognition consistency." in text
    assert "It must not validate replay\ntruth or define legitimacy." in text
    assert (
        "Evolution may improve cognition.\n"
        "Evidence meaning must persist.\n"
        "Operational reality must remain time-stable."
    ) in text
