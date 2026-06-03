from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Adaptive_Cognition_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: ADAPTIVE COGNITION GOVERNANCE POLICY",
    "ROLE: PREVENT ROLE-AWARE, AI-ASSISTED, WORKFLOW-ADAPTIVE, AND PREFERENCE-SENSITIVE SYSTEMS FROM PRODUCING PERSONALIZED OPERATIONAL REALITIES",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

ADAPTIVE_RISK_SURFACES = (
    "Role-Aware Cognition",
    "AI-Assisted Adaptation",
    "Workflow-Adaptive Cognition",
    "Preference-Sensitive Cognition",
    "Context-Personalized Cognition",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_adaptive_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "same evidence -> adaptive cognition surface -> personalized operational reality" in text
    assert "Adaptation may improve ergonomics." in text
    assert "Adaptation must not fork shared operational\nreality." in text


def test_adaptive_policy_preserves_authority_stack() -> None:
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
        "Adaptive systems -> ergonomic variation only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Adaptive cognition governance constrains personalization boundaries." in text
    assert "It does\nnot validate truth." in text


def test_adaptive_policy_declares_adaptive_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in ADAPTIVE_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Different roles receive different operational realities",
        "AI personalizes summaries, recommendations, or salience into user-specific truth",
        "Workflow optimization hides, reorders, or compresses evidence",
        "Operator preferences personalize evidence perception",
        "Local context changes the meaning of shared replay-valid evidence",
    ):
        assert risk in text


def test_adaptive_policy_defines_allowed_and_forbidden_adaptation_classes() -> None:
    text = read_doc()

    for allowed in (
        "density",
        "layout",
        "navigation",
        "disclosure pacing",
        "workflow ergonomics",
        "accessibility mode",
        "interaction affordances",
        "terminology where meaning is preserved",
    ):
        assert allowed in text

    for forbidden in (
        "replay severity",
        "evidence visibility for hard failures",
        "validator meaning",
        "legitimacy interpretation",
        "salience weighting",
        "narrative truth",
        "source evidence lineage",
        "replay mismatch meaning",
        "governance failure visibility",
    ):
        assert forbidden in text


def test_adaptive_policy_contains_salience_narrative_and_visibility_boundaries() -> None:
    text = read_doc()

    for salience_boundary in (
        "urgency meaning",
        "constitutional severity",
        "replay conflict importance",
        "validator failure importance",
        "governance escalation",
        "unchanged shared salience baseline",
    ):
        assert salience_boundary in text

    for narrative_requirement in (
        "source explanation ids",
        "composition source ids",
        "replay references",
        "validator references",
        "narrative template version",
        "omitted detail indicators",
    ):
        assert narrative_requirement in text

    for visibility_boundary in (
        "critical replay-valid evidence",
        "hard validator failures",
        "source evidence references",
        "replay mismatch indicators",
        "governance failure indicators",
        "Hidden critical evidence is adaptive truth fragmentation.",
    ):
        assert visibility_boundary in text


def test_adaptive_policy_requires_cross_user_equivalence_and_transparency() -> None:
    text = read_doc()

    for shared_requirement in (
        "replay truth status",
        "validator outcome",
        "hard failure visibility",
        "source evidence lineage",
        "authority boundary",
        "salience baseline",
        "operational meaning",
    ):
        assert shared_requirement in text

    for transparency_field in (
        "adaptation id",
        "adaptation type",
        "role scope when applicable",
        "user preference scope when applicable",
        "workflow scope when applicable",
        "AI model version when applicable",
        "unchanged shared evidence baseline",
        "source evidence references",
        "salience policy reference",
        "cognitive complexity budget reference",
        "authority disclaimer",
    ):
        assert transparency_field in text


def test_adaptive_policy_names_drift_detection_patterns() -> None:
    text = read_doc()

    for drift in (
        "user-specific salience divergence",
        "role-specific hard failure suppression",
        "AI personalization drift",
        "replay visibility asymmetry",
        "adaptive narrative mutation",
        "workflow-specific validator reinterpretation",
        "preference-specific severity drift",
        "hidden adaptive filtering",
        "source reference loss",
        "authority disclaimer loss",
    ):
        assert drift in text


def test_adaptive_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/adaptive_cognition_policy.yaml" in text
    assert "schema: afritech.adaptive_cognition_policy.v1" in text
    assert "python3 -m afritech.ci.adaptive_cognition_validator" in text
    assert "This guard validates adaptive cognition governance." in text
    assert "It must not validate replay\ntruth or define legitimacy." in text
    assert (
        "Adaptation may personalize presentation.\n"
        "Adaptation may not personalize truth."
    ) in text
