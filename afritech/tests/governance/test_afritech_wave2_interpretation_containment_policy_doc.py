from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave2_Interpretation_Containment_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 2 CONTROL ARTIFACT",
    "CLASSIFICATION: INTERPRETATION CONTAINMENT POLICY",
    "ROLE: PREVENT EXPLANATION SURFACES FROM ACCUMULATING AUTHORITY OR COMPLEXITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY OR REPLAY TRUTH",
)

ALLOWED_VIEW_TYPES = (
    "Status Views",
    "Lineage Views",
    "Diagnostic Views",
    "Summary Views",
    "Guided Views",
)

FORBIDDEN_PATTERNS = (
    "Dashboard-As-Truth",
    "Hidden Semantic Inference",
    "Failure Softening",
    "Summary Without Drill-Down",
    "View-Specific Truth",
    "Auto-Repair From Interpretation",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_interpretation_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "Views may simplify." in text
    assert "Views must not reinterpret, override, or create legitimacy." in text
    assert "Interpretation exists to reduce human cognitive load." in text


def test_interpretation_policy_preserves_authority_stack() -> None:
    text = read_doc()

    for phrase in (
        "Constitution -> legitimacy",
        "Replay -> truth validation",
        "Validators -> governance enforcement",
        "Status / observability -> explanation",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "All interpretation surfaces are subordinate" in text


def test_interpretation_policy_declares_allowed_views_and_forbidden_patterns() -> None:
    text = read_doc()

    for view_type in ALLOWED_VIEW_TYPES:
        assert view_type in text

    for pattern in FORBIDDEN_PATTERNS:
        assert pattern in text


def test_interpretation_policy_requires_layering_and_progressive_disclosure() -> None:
    text = read_doc()

    for layer in (
        "Layer 1: state",
        "Layer 2: cause",
        "Layer 3: affected artifact",
        "Layer 4: source evidence",
        "Layer 5: recommended next action",
    ):
        assert layer in text

    assert "summary view" in text
    assert "evidence view" in text
    assert "no summary may block access to source artifacts" in text


def test_interpretation_policy_contains_complexity_budget_and_parity_rules() -> None:
    text = read_doc()

    for budget_item in (
        "one primary health signal",
        "five top-level metric cards",
        "two lineage views",
        "one failure table",
        "one evidence drill-down panel",
    ):
        assert budget_item in text

    for parity_rule in (
        "same source data",
        "same health classification",
        "same failure identifiers",
        "same affected artifact identifiers",
        "same authority disclaimer",
    ):
        assert parity_rule in text


def test_interpretation_policy_defines_future_ga_guard_without_authority_inflation() -> None:
    text = read_doc()

    assert "python3 -m afritech.ci.interpretation_containment_validator" in text
    assert "This guard validates interpretation containment." in text
    assert "It must not validate replay truth or define legitimacy." in text
    assert "Many views.\nOne governed explanation model.\nZero new authority." in text
