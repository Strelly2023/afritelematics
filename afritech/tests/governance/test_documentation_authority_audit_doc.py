from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "docs/README.md"
AUDIT = ROOT / "docs/reviews/AFRITECH_DOCUMENTATION_AUTHORITY_AUDIT.md"


def test_docs_readme_defines_fast_entry_and_canonical_hierarchy() -> None:
    text = README.read_text(encoding="utf-8")

    for item in (
        "DOCUMENTATION ROOT INDEX",
        "CANONICAL_DOCUMENTATION_NAVIGATION_SURFACE",
        "Fast Entry",
        "AFRITECH_UNIFIED_ARCHITECTURE.md",
        "AFRITECH_CONSTITUTION_V1.md",
        "Canonical Hierarchy",
        "constitution governs",
        "architecture explains",
        "replay proves",
    ):
        assert item in text


def test_documentation_authority_audit_captures_overlap_and_consolidation_rules() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    for item in (
        "DOCUMENTATION AUTHORITY AUDIT",
        "Canonical Surface Proliferation",
        "Split Documentation Centers",
        "Duplicate And Parallel Narratives",
        "One Navigation Root",
        "Constitution Beats Commentary",
        "Commercial Docs Package, Not Govern",
        "documentation authority compression",
    ):
        assert item in text


def test_documentation_authority_audit_preserves_non_claims() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    for item in (
        "that all duplicates have already been removed",
        "that every older canonical-seeming document is obsolete",
        "that the repo has finished documentation consolidation",
    ):
        assert item in text
