from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave2_Canonical_Explanation_Composition_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 2 CONTROL ARTIFACT",
    "CLASSIFICATION: CANONICAL EXPLANATION COMPOSITION POLICY",
    "ROLE: PREVENT SAFE EXPLANATION RECORDS FROM COMBINING INTO UNSAFE SYNTHETIC MEANING",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

ALLOWED_COMPOSITION_TYPES = (
    "Timelines",
    "Lineage Grouping",
    "Replay Trace Aggregation",
    "Validator Clustering",
    "Diagnostic Sequencing",
)

FORBIDDEN_COMPOSITION_BEHAVIORS = (
    "Synthetic Legitimacy",
    "Synthetic Replay Truth",
    "Inferred Causality",
    "Semantic Interpolation",
    "Narrative Truth Generation",
    "Speculative Operational Conclusions",
    "AI Semantic Synthesis",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_composition_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "safe explanation records -> unsafe synthetic narrative" in text
    assert "Narratives explain replay-valid evidence. Narratives do not create truth." in text


def test_composition_policy_preserves_authority_stack() -> None:
    text = read_doc()

    for phrase in (
        "Constitution -> legitimacy",
        "Replay -> truth validation",
        "Validators -> governance enforcement",
        "Canonical Explanation Schema -> safe explanation units",
        "Composition Policy -> safe explanation aggregation",
        "Views / AI / Replay Explorer -> governed narrative projections",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Composition is an organization layer. It is not a validation layer." in text


def test_composition_policy_declares_allowed_and_forbidden_composition_forms() -> None:
    text = read_doc()

    for composition_type in ALLOWED_COMPOSITION_TYPES:
        assert composition_type in text

    for forbidden_behavior in FORBIDDEN_COMPOSITION_BEHAVIORS:
        assert forbidden_behavior in text


def test_composition_policy_preserves_source_integrity_and_evidence_boundary() -> None:
    text = read_doc()

    for source_integrity in (
        "source explanation IDs",
        "source authority references",
        "transformation steps",
        "omitted detail indicators",
        "replay authority references",
        "validator references",
    ):
        assert source_integrity in text

    assert "Composition cannot strengthen evidence authority." in text
    assert "They remain organized projections of existing proof." in text
    assert "It is not itself replay evidence." in text


def test_composition_policy_contains_ai_restrictions_and_transparency() -> None:
    text = read_doc()

    for ai_rule in (
        "AI may:",
        "AI must not:",
        "infer legitimacy",
        "synthesize operational truth",
        "override replay outcomes",
        "advisory status",
    ):
        assert ai_rule in text

    for transparency_field in (
        "composition id",
        "composition type",
        "source explanation ids",
        "source evidence references",
        "authority disclaimer",
    ):
        assert transparency_field in text


def test_composition_policy_defines_complexity_budget_and_future_schema() -> None:
    text = read_doc()

    for budget_item in (
        "twenty source explanation records",
        "three nesting levels",
        "five cross-reference groups",
        "one primary narrative summary",
        "one recommended investigation path",
    ):
        assert budget_item in text

    for schema_field in (
        "composition_record:",
        "source_explanation_ids",
        "transformation_steps",
        "omitted_detail_count",
        "advisory: boolean",
        "authority_disclaimer",
    ):
        assert schema_field in text


def test_composition_policy_defines_future_ga_guard_without_authority_inflation() -> None:
    text = read_doc()

    assert "python3 -m afritech.ci.canonical_explanation_composition_validator" in text
    assert "This guard validates composition containment." in text
    assert "It must not validate replay truth\nor define legitimacy." in text
    assert "Safe units.\nSafe aggregation.\nNo synthetic truth." in text
