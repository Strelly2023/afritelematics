from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave2_Cognitive_Scale_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 2 CONTROL ARTIFACT",
    "CLASSIFICATION: COGNITIVE SCALE GOVERNANCE POLICY",
    "ROLE: KEEP GOVERNED COGNITION HUMAN-USABLE AS EXPLANATIONS, NARRATIVES, AND LINEAGE SURFACES GROW",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

RISK_SURFACES = (
    "Lineage Explosion",
    "Narrative Density",
    "Diagnostic Branching",
    "Role Overload",
    "AI Explanation Sprawl",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_cognitive_scale_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "governed cognition -> too much governed cognition -> human overload" in text
    assert "Governed cognition exists to make replay-valid evidence usable." in text


def test_cognitive_scale_policy_preserves_authority_stack() -> None:
    text = read_doc()

    for phrase in (
        "Constitution -> legitimacy",
        "Replay -> truth validation",
        "Validators -> governance enforcement",
        "Explanation Schema -> safe explanation units",
        "Composition Schema -> safe narrative aggregation",
        "Cognitive Scale Policy -> bounded human comprehension",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Cognitive scale governance constrains presentation and navigation." in text
    assert "It does not\nvalidate truth." in text


def test_cognitive_scale_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in RISK_SURFACES:
        assert risk_surface in text

    for containment in (
        "lineage compression",
        "narrative summaries",
        "one primary recommended next check",
        "role-scoped cognition",
        "source explanation IDs",
    ):
        assert containment in text


def test_cognitive_scale_policy_defines_budgets() -> None:
    text = read_doc()

    for budget in (
        "View Budget",
        "Narrative Budget",
        "Diagnostic Budget",
        "Role Budget",
    ):
        assert budget in text

    for limit in (
        "one primary health signal",
        "five top-level facts",
        "three primary actions",
        "twenty source explanation records",
        "three nesting levels",
        "one primary next check",
    ):
        assert limit in text


def test_cognitive_scale_policy_requires_progressive_disclosure_and_ordering() -> None:
    text = read_doc()

    for layer in (
        "Layer 1: health or state",
        "Layer 2: cause",
        "Layer 3: affected artifact",
        "Layer 4: source evidence",
        "Layer 5: raw record or replay reference",
    ):
        assert layer in text

    for ordering_source in (
        "declared sequence",
        "declared timestamp",
        "canonical id",
        "severity derived from validator or replay result",
        "explicit role priority",
    ):
        assert ordering_source in text


def test_cognitive_scale_policy_requires_reversible_compression_and_role_parity() -> None:
    text = read_doc()

    assert "Lineage may be compressed only if the compression remains reversible." in text
    assert "Compression must preserve source traceability." in text

    for role_rule in (
        "change health classification",
        "change replay result",
        "change validator severity",
        "hide hard failures",
        "create role-specific legitimacy",
    ):
        assert role_rule in text

    assert "No role may receive a different truth model." in text


def test_cognitive_scale_policy_contains_ai_boundaries_and_warning_rules() -> None:
    text = read_doc()

    for ai_rule in (
        "AI may:",
        "AI must not:",
        "synthesize replay truth",
        "override validator severity",
        "invent source relationships",
        "AI output must always remain advisory and source-bound.",
    ):
        assert ai_rule in text

    for warning_field in (
        "exceeded budget name",
        "actual count",
        "allowed count",
        "omitted detail count",
        "drill-down path",
    ):
        assert warning_field in text


def test_cognitive_scale_policy_defines_future_budget_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/cognitive_complexity_budget.yaml" in text
    assert "schema: afritech.cognitive_complexity_budget.v1" in text
    assert "python3 -m afritech.ci.cognitive_complexity_validator" in text
    assert "This guard validates cognitive scale containment." in text
    assert "It must not validate replay\ntruth or define legitimacy." in text
    assert "Bounded cognition.\nPreserved evidence.\nNo hidden meaning." in text
