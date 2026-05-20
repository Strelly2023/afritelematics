from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/architecture/AfriRide_UI_UX_Design_Documentation.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL DESIGN SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL DESIGN SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay admissibility",
    "execution legality",
    "identity ontology",
    "core invariants",
)

UX_PRINCIPLES = (
    "Predictable Interaction",
    "Minimal Cognitive Load",
    "Operational Transparency",
    "Safety and Continuity",
)

INFO_ARCHITECTURE = (
    "Rider Application Structure",
    "Driver Application Structure",
    "Admin Dashboard Structure",
)

WIREFRAMES = (
    "Rider Home Screen",
    "Ride Matching Screen",
    "Active Ride Screen",
    "Driver Ride Request Screen",
    "Ride Completion Screen",
)

PROTOTYPE_FLOWS = (
    "Rider Booking Flow",
    "Driver Acceptance Flow",
    "Cancellation Flow",
    "Scheduled Ride Flow",
)

TOKEN_GROUPS = (
    "Color Tokens",
    "Typography Tokens",
    "Spacing Tokens",
    "Border Radius Tokens",
    "Shadow Tokens",
)

COMPONENTS = (
    "Primary Button",
    "Ride Status Card",
    "Map Container",
    "Notification Banner",
)

OPERATIONAL_FORBIDDEN = (
    "mutate replay truth",
    "bypass lifecycle legality",
    "override deterministic execution",
    "introduce undeclared runtime behavior",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_ui_ux_doc_has_operational_design_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in text
    for surface in NON_REDEFINED_SURFACES:
        assert surface in text


def test_ui_ux_doc_declares_design_vision_and_principles() -> None:
    text = read_doc()

    for item in ("clarity", "speed", "safety", "predictability", "operational continuity"):
        assert item in text

    for principle in UX_PRINCIPLES:
        assert principle in text

    assert "without exposing constitutional complexity" in text
    assert "replay-safe lifecycle visibility" in text


def test_ui_ux_doc_defines_information_architecture_and_wireframes() -> None:
    text = read_doc()

    for section in INFO_ARCHITECTURE:
        assert section in text

    for wireframe in WIREFRAMES:
        assert wireframe in text

    for screen_item in (
        "Request Ride",
        "Searching for Drivers",
        "Share ETA",
        "Accept",
        "Reject",
        "Download Receipt",
    ):
        assert screen_item in text


def test_ui_ux_doc_defines_prototype_flows() -> None:
    text = read_doc()

    for flow in PROTOTYPE_FLOWS:
        assert flow in text

    for step in (
        "View fare estimate",
        "Driver assigned",
        "Accept ride",
        "Confirm cancellation",
        "Driver matching near activation",
    ):
        assert step in text


def test_ui_ux_doc_defines_design_tokens() -> None:
    text = read_doc()

    for token_group in TOKEN_GROUPS:
        assert token_group in text

    for token in (
        "color.primary",
        "color.success",
        "font.family.primary",
        "font.size.md",
        "spacing.md",
        "radius.md",
        "shadow.md",
    ):
        assert token in text


def test_ui_ux_doc_defines_components_accessibility_and_responsiveness() -> None:
    text = read_doc()

    for component in COMPONENTS:
        assert component in text

    for requirement in (
        "keyboard navigation",
        "screen readers",
        "high contrast readability",
        "touch accessibility",
        "responsive scaling",
        "mobile-first layouts",
        "tablet responsiveness",
        "desktop dashboards",
        "adaptive navigation",
    ):
        assert requirement in text


def test_ui_ux_doc_preserves_non_authoritative_runtime_boundary() -> None:
    text = read_doc()

    assert "Maps remain observational only and must not mutate runtime truth." in text
    assert "observational" in text
    assert "non-authoritative" in text
    assert "runtime-isolated" in text

    for forbidden in OPERATIONAL_FORBIDDEN:
        assert forbidden in text

    assert "bounded operational interaction surface" in text
    assert "under AfriTech constitutional admissibility enforcement" in text
