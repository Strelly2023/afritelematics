from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_unified_architecture_has_bounded_classification_and_non_claims() -> None:
    text = read_doc()
    lowered = text.lower()

    for item in (
        "Status: AFRITECH UNIFIED ARCHITECTURE",
        "Classification: BOUNDED SYSTEM INTEGRATION ARCHITECTURE SURFACE",
        "Architecture explains.",
        "Governance constrains.",
        "Replay proves.",
        "It does not permit this claim:",
    ):
        assert item in text

    for forbidden in (
        "all layers are production-proven",
        "the architecture itself proves truth",
        "the ecosystem is already globally deployed",
        "ai is sovereign over runtime",
        "external trust surfaces replace replay",
    ):
        assert forbidden in lowered


def test_unified_architecture_covers_all_major_system_layers() -> None:
    text = read_doc()

    for item in (
        "Trust Explorer",
        "Operator Web UI",
        "Rider App",
        "Driver App",
        "AfriRide API",
        "Event Gateway",
        "TRACE LAYER",
        "Replay Engine",
        "Evidence Engine",
        "Receipt Engine",
        "Crypto Layer",
        "AFRIPower",
        "AfriProgramming",
        "AfriCPPT",
        "AFrTPPS",
        "ADR",
        "INVARIANT",
        "RULE",
        "GUARD",
        "CI",
    ):
        assert item in text


def test_unified_architecture_defines_the_closed_loop_and_authority_boundary() -> None:
    text = read_doc()

    for item in (
        "REAL-WORLD ACTION",
        "-> EXECUTION",
        "-> TRACE",
        "-> REPLAY",
        "-> EVIDENCE",
        "-> RECEIPT",
        "-> INSIGHT",
        "-> PROPOSAL",
        "-> GOVERNED EVOLUTION",
        "-> EXTERNAL VERIFICATION",
        "-> REAL-WORLD EXECUTION PERFORMANCE",
        "UI does not define truth",
        "API does not define truth",
        "AI does not define truth",
        "replay defines admissible truth",
    ):
        assert item in text


def test_unified_architecture_preserves_platform_network_and_people_process_bridge() -> None:
    text = read_doc()

    for item in (
        "shared mobile client",
        "external verification apis",
        "multi-party validation",
        "onboarding models",
        "pilot execution playbooks",
        "performance measurement (kpis)",
        "technology",
        "processes",
        "people",
        "skills",
    ):
        assert item in text.lower()
