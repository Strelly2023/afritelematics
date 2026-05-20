from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/website/AfriRide_Landing_Page_Copy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WEBSITE POSITIONING",
    "CLASSIFICATION: ISOLATED PUBLIC COMMUNICATION SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

CURRENT_FOUNDATION_ITEMS = (
    "deterministic runtime systems",
    "replay-safe coordination logic",
    "governance enforcement mechanisms",
    "operational continuity validation",
    "proof-bound system execution",
    "bounded AfriRide continuity proof behavior",
)

PLANNED_EXPERIENCE_ITEMS = (
    "upfront pricing visibility",
    "scheduled ride booking",
    "multi-stop routing",
    "guest ride coordination",
    "fare splitting",
    "ride comparison",
    "calendar-based trip planning",
    "AfriRide One",
    "live trip sharing",
    "Ride Check",
    "PIN-based ride verification",
    "lost item support",
    "AfriRideS / Comfort",
    "AfriRide Go",
    "AfriRideL",
    "AfriRide Animal",
)

BOUNDARY_ITEMS = (
    "globally deployed",
    "mass-market operational",
    "fully feature-complete",
)

FORBIDDEN_INFLATION = (
    "global deployment readiness achieved",
    "currently deployed ride marketplace",
    "mass-market operational today",
    "fully feature-complete today",
    "proven global scale",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def test_landing_page_has_isolated_public_status() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not define proof truth" in text
    assert "does not claim global deployment readiness" in text
    assert "Public communication must preserve or isolate all claims." in text


def test_landing_page_separates_foundation_from_planned_experience() -> None:
    text = read_doc()
    foundation = section(text, "## Current System Foundation", "## Rider Experience")
    experience = section(text, "## Rider Experience", "## Transparent Capability Model")

    assert "Status: [Implemented / In Development]" in foundation
    for item in CURRENT_FOUNDATION_ITEMS:
        assert item in foundation

    assert "Status: [Planned / Exploratory]" in experience
    for item in PLANNED_EXPERIENCE_ITEMS:
        assert item in experience
        assert item not in foundation


def test_landing_page_contains_transparent_capability_model() -> None:
    text = read_doc()
    model = section(text, "## Transparent Capability Model", "## Powered by AfriTech")

    assert "What exists today:" in model
    assert "What is being built:" in model
    assert "We do not present planned features as existing capabilities." in model


def test_landing_page_contains_honest_boundaries() -> None:
    text = read_doc()
    boundaries = section(text, "## Honest System Boundaries", "## The Vision")

    assert "AfriRide is not yet:" in boundaries
    for item in BOUNDARY_ITEMS:
        assert item in boundaries

    assert "AfriRide is currently:" in boundaries
    assert "architecturally validated" in boundaries
    assert "experimentally demonstrated" in boundaries
    assert "constitutionally enforced" in boundaries


def test_landing_page_preserves_proof_boundary() -> None:
    text = read_doc()

    assert "does not modify `afritech.demo.proof`" in text
    assert "does not expand proof scope beyond the bounded AfriRide domain" in text
    assert "does not claim global deployment readiness" in text
    assert "AfriRide does not allow reality and description to diverge" in text

    lowered = text.lower()
    for claim in FORBIDDEN_INFLATION:
        assert claim not in lowered
