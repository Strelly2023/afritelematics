from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/requirements/AfriRide_Rider_Features_and_Experience.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL REQUIREMENTS",
    "CLASSIFICATION: ISOLATED OPERATIONAL REQUIREMENTS SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

RIDER_CAPABILITIES = (
    "Upfront Pricing",
    "Scheduled Rides",
    "Multiple Destinations",
    "Guest Rider Booking",
    "Fare Split",
    "Calendar Sync",
    "AfriRide One",
    "Share My ETA",
    "Ride Check",
    "PIN Verification",
    "Lost Item Support",
    "AfriRideS / Comfort",
    "AfriRide Go",
    "AfriRideL",
    "AfriRide Animal",
    "Fare Estimation & Ride Comparison",
)

EXPLORATORY_FEATURES = (
    "Calendar Sync",
    "AfriRide One",
    "Ride Check",
)

PLANNED_FEATURES = tuple(
    feature for feature in RIDER_CAPABILITIES if feature not in EXPLORATORY_FEATURES
)

CURRENT_FOCUS_ALLOWED = (
    "Deterministic execution infrastructure",
    "Replay-safe operational coordination",
    "Governance enforcement through validators and CI gates",
    "Continuity scenario validation",
    "Proof-bound operational claims",
    "Constitutional runtime integration",
    "Bounded AfriRide continuity proof behavior",
)

FORBIDDEN_PROOF_CLAIMS = (
    "currently proven rider marketplace",
    "currently implemented consumer ride marketplace",
    "proof-certified rider marketplace",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def test_rider_features_doc_has_operational_requirements_status() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "[Implemented] -> Validator-backed and executed in the system" in text
    assert "[In Development] -> Partially implemented, not yet fully validated" in text
    assert "[Planned] -> Defined product direction, not yet implemented" in text
    assert "[Exploratory] -> Conceptual, no execution commitment" in text
    assert "This statement is operational positioning, not proof truth." in text
    assert "does not" in text
    assert "modify the constitutional enforcement contract" in text


def test_planned_rider_features_are_present_but_not_current_focus() -> None:
    text = read_doc()
    planned_details = section(
        text,
        "## Rider Experience Capabilities",
        "## Constitutional Infrastructure Layer",
    )
    current = section(
        text,
        "### Current Active Focus - [Implemented / In Development]",
        "## Rider Experience Capabilities",
    )

    for feature in RIDER_CAPABILITIES:
        assert feature in planned_details
        assert feature not in current

    for item in CURRENT_FOCUS_ALLOWED:
        assert item in current


def test_rider_features_doc_does_not_claim_proof_readiness() -> None:
    text = read_doc().lower()

    for phrase in FORBIDDEN_PROOF_CLAIMS:
        assert phrase not in text

    assert "global deployment readiness" in text
    assert "unrestricted distributed systems readiness" in text
    assert "does not" in text
    assert "not current proof claims" in text


def test_rider_features_doc_keeps_future_language_for_planned_capabilities() -> None:
    text = read_doc()
    planned = section(
        text,
        "## Rider Experience Capabilities",
        "## Constitutional Infrastructure Layer",
    )

    future_markers = (
        "planned",
        "expected",
        "intended",
        "future",
        "may",
        "would",
    )
    for feature in RIDER_CAPABILITIES:
        feature_index = planned.index(feature)
        window = planned[feature_index : feature_index + 700].lower()
        assert any(marker in window for marker in future_markers), feature


def test_rider_features_doc_classifies_feature_statuses_explicitly() -> None:
    text = read_doc()

    for feature in RIDER_CAPABILITIES:
        feature_index = text.index(feature)
        window = text[feature_index : feature_index + 220]
        if feature in EXPLORATORY_FEATURES:
            assert "Status: [Exploratory]" in window
        elif feature == "Fare Estimation & Ride Comparison":
            assert "Status: [Planned]" in text[text.rindex(feature) : text.rindex(feature) + 220]
        else:
            assert "Status: [Planned]" in window


def test_rider_features_doc_states_boundary_model() -> None:
    text = read_doc()

    assert "Core Truth Layer - Sealed" in text
    assert "Product Experience Layer - Isolated" in text
    assert "This layer is immutable and non-negotiable." in text
    assert "This layer is evolvable but non-authoritative." in text
    assert "execution admissibility = claim admissibility" in text
