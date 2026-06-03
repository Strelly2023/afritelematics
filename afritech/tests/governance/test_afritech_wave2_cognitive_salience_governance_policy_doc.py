from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave2_Cognitive_Salience_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 2 CONTROL ARTIFACT",
    "CLASSIFICATION: COGNITIVE SALIENCE GOVERNANCE POLICY",
    "ROLE: PREVENT ATTENTION, PRIORITIZATION, HIGHLIGHTING, AND RECOMMENDATIONS FROM BECOMING HIDDEN SEMANTIC AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

RISK_SURFACES = (
    "Ordering Salience",
    "Visual Emphasis",
    "Urgency Classification",
    "Recommendation Priority",
    "AI Salience",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_salience_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "salience becomes a hidden semantic force" in text
    assert "Salience may direct attention." in text
    assert "It must not create truth, legitimacy, or hidden\nsemantic priority." in text


def test_salience_policy_preserves_authority_stack() -> None:
    text = read_doc()

    for phrase in (
        "Constitution -> legitimacy",
        "Replay -> truth validation",
        "Validators -> governance enforcement",
        "Explanation Schema -> safe explanation units",
        "Composition Schema -> safe narrative aggregation",
        "Cognitive Complexity Budget -> bounded cognition",
        "Salience Governance Policy -> bounded attention semantics",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Salience governance constrains ordering, emphasis, urgency, and recommendation." in text
    assert "It does not validate truth." in text


def test_salience_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in RISK_SURFACES:
        assert risk_surface in text

    for containment in (
        "deterministic ordering source",
        "bounded color escalation",
        "validator-linked urgency",
        "recommendation source disclosed",
        "AI salience must be advisory",
    ):
        assert containment in text


def test_salience_policy_defines_allowed_and_forbidden_sources() -> None:
    text = read_doc()

    for allowed_source in (
        "validator severity",
        "replay mismatch status",
        "declared lifecycle state",
        "declared incident severity",
        "canonical id ordering",
        "declared timestamp ordering",
        "role-specific operational need",
    ):
        assert allowed_source in text

    for forbidden_source in (
        "hidden heuristics",
        "AI preference",
        "dashboard-local urgency rules",
        "user-specific semantic inference",
        "runtime environment ordering",
    ):
        assert forbidden_source in text


def test_salience_policy_contains_prioritization_and_highlighting_rules() -> None:
    text = read_doc()

    for priority_field in (
        "primary ordering key",
        "secondary tie-breaker",
        "source authority",
        "unknown-state handling",
        "stable deterministic fallback",
    ):
        assert priority_field in text

    for highlight_level in (
        "neutral",
        "informational",
        "warning",
        "critical",
    ):
        assert highlight_level in text

    assert "critical requires validator failure, replay mismatch, or declared incident severity" in text


def test_salience_policy_contains_recommendation_transparency_and_attention_budgets() -> None:
    text = read_doc()

    for transparency_field in (
        "salience id",
        "salience type",
        "salience level",
        "source signal",
        "ordering key",
        "tie-breaker",
        "source evidence reference",
        "authority disclaimer",
    ):
        assert transparency_field in text

    for budget_item in (
        "one critical banner",
        "three highlighted items",
        "five recommended next actions",
        "one pinned investigation path",
        "one AI-generated summary",
    ):
        assert budget_item in text


def test_salience_policy_contains_role_and_ai_boundaries() -> None:
    text = read_doc()

    for role_rule in (
        "role-specific truth",
        "role-specific replay result",
        "role-specific validator severity",
        "role-specific hidden evidence",
        "role-specific legitimacy claims",
    ):
        assert role_rule in text

    for ai_rule in (
        "AI may:",
        "AI must not:",
        "create urgency from speculation",
        "infer causality",
        "override deterministic ordering",
        "prioritize without source evidence",
        "AI salience must remain advisory, source-bound, and reversible.",
    ):
        assert ai_rule in text


def test_salience_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/cognitive_salience_policy.yaml" in text
    assert "schema: afritech.cognitive_salience_policy.v1" in text
    assert "python3 -m afritech.ci.cognitive_salience_validator" in text
    assert "This guard validates salience containment." in text
    assert "It must not validate replay truth or\ndefine legitimacy." in text
    assert "Governed attention.\nTransparent priority.\nNo salience-driven truth." in text
