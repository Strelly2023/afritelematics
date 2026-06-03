from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave2_Cross_Surface_Cognition_Consistency_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 2 CONTROL ARTIFACT",
    "CLASSIFICATION: CROSS-SURFACE COGNITION CONSISTENCY POLICY",
    "ROLE: PREVENT CLI, DASHBOARDS, AI COPILOTS, REPORTS, INCIDENT SYSTEMS, AND REPLAY EXPLORERS FROM PRODUCING DIVERGENT OPERATIONAL REALITIES",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

RISK_SURFACES = (
    "Explanation Parity",
    "Salience Parity",
    "Narrative Equivalence",
    "AI Copilot Consistency",
    "Deterministic Ordering",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_cross_surface_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "each surface is safe -> surfaces disagree -> operators receive different realities" in text
    assert "Surface variation may improve usability." in text
    assert "It must not fragment operational\ntruth perception." in text


def test_cross_surface_policy_preserves_authority_stack() -> None:
    text = read_doc()

    for phrase in (
        "Constitution -> legitimacy",
        "Replay -> truth validation",
        "Validators -> governance enforcement",
        "Explanation Schema -> safe explanation units",
        "Composition Schema -> safe narrative aggregation",
        "Cognitive Complexity Budget -> bounded cognition",
        "Salience Policy -> bounded attention semantics",
        "Cross-Surface Consistency Policy -> operational reality coherence",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Cross-surface consistency governs parity between presentations." in text
    assert "It does not\nvalidate truth." in text


def test_cross_surface_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in RISK_SURFACES:
        assert risk_surface in text

    for containment in (
        "same explanation identifiers",
        "same salience source",
        "same composition source ids",
        "same explanation schema",
        "shared ordering keys",
    ):
        assert containment in text


def test_cross_surface_policy_defines_allowed_and_forbidden_surface_differences() -> None:
    text = read_doc()

    for allowed in (
        "visual layout",
        "density",
        "role-specific depth",
        "progressive disclosure level",
        "export format",
        "accessibility mode",
        "interaction affordances",
    ):
        assert allowed in text

    for forbidden in (
        "replay result",
        "validator outcome",
        "hard failure visibility",
        "source evidence reference",
        "explanation identifier",
        "composition source ids",
        "salience source",
        "legitimacy implication",
        "authority disclaimer",
    ):
        assert forbidden in text


def test_cross_surface_policy_contains_role_equivalence_and_transparency() -> None:
    text = read_doc()

    for required in (
        "same underlying evidence",
        "same status semantics",
        "same replay result",
        "same validator severity",
        "same authority boundary",
    ):
        assert required in text

    for transparency_field in (
        "surface id",
        "surface type",
        "source schemas used",
        "source evidence references",
        "salience policy reference",
        "cognitive budget reference",
        "role scope",
        "presentation differences",
        "authority disclaimer",
    ):
        assert transparency_field in text


def test_cross_surface_policy_names_drift_patterns_and_consistency_checks() -> None:
    text = read_doc()

    for drift in (
        "inconsistent health labels",
        "conflicting urgency labels",
        "mismatched explanation ids",
        "incompatible source references",
        "divergent AI recommendations",
        "dashboard-only truth",
        "CLI-only truth",
        "incident report-only causality",
    ):
        assert drift in text

    for check in (
        "same explanation ids",
        "same composition ids",
        "same status values",
        "same salience levels",
        "same source references",
        "same hard failure visibility",
        "same replay and validator references",
    ):
        assert check in text


def test_cross_surface_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/cross_surface_cognition_policy.yaml" in text
    assert "schema: afritech.cross_surface_cognition_policy.v1" in text
    assert "python3 -m afritech.ci.cross_surface_cognition_validator" in text
    assert "This guard validates cross-surface cognition consistency." in text
    assert "It must not validate\nreplay truth or define legitimacy." in text
    assert "Presentation may vary.\nEvidence must match.\nOperational reality must not fork." in text
