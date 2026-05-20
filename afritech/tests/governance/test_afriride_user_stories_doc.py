from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/requirements/AfriRide_User_Stories_and_Epics.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL REQUIREMENTS",
    "CLASSIFICATION: ISOLATED OPERATIONAL REQUIREMENTS SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

STATUS_LINES = (
    "[Implemented] -> backed by tested system behavior in the current bounded implementation surface",
    "[In Development] -> partially implemented, not yet fully validated",
    "[Planned] -> product direction, not yet implemented",
    "[Exploratory] -> conceptual, no execution commitment",
)

EPICS = (
    "Epic 1 - Ride Request and Intent Capture",
    "Epic 2 - Ride Lifecycle Management",
    "Epic 3 - Driver Matching",
    "Epic 4 - Pricing and Fare Calculation",
    "Epic 5 - API and System Interaction",
    "Epic 6 - Safety and Trust Layer",
    "Epic 7 - Replay and Traceability",
    "Epic 8 - Future Experience Layer",
)

IMPLEMENTED_STORIES = (
    "Create Ride Request",
    "Validate Ride Inputs",
    "Assign Unique Ride Identity",
    "Transition Ride States",
    "Prevent Invalid Transitions",
    "Complete Ride Execution",
    "Calculate Fare",
    "Submit Ride Request via API",
    "Track Ride Status",
    "Generate Execution Trace",
    "Validate Replay Consistency",
    "Link Execution to Proof",
)

IN_DEVELOPMENT_STORIES = (
    "Assign Driver to Ride",
    "Ensure Deterministic Matching",
    "Enforce API Compliance",
)

PLANNED_STORIES = (
    "Handle No Available Driver",
    "Display Upfront Pricing",
    "Support Pricing Categories",
    "Ensure Idempotent Requests",
    "Enable PIN Verification",
    "Share Ride Information",
    "Schedule Rides",
    "Multi-stop Trips",
)

EXPLORATORY_STORIES = (
    "Fare Splitting",
    "Membership - AfriRide One",
)

FORBIDDEN_INFLATION = (
    "global production readiness achieved",
    "unrestricted distributed systems readiness achieved",
    "universal validator completeness achieved",
    "current proof-certified marketplace",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def story_window(text: str, story: str) -> str:
    start = text.index(f"### {story}")
    next_story = text.find("\n### ", start + 1)
    next_epic = text.find("\n## ", start + 1)
    candidates = [pos for pos in (next_story, next_epic) if pos != -1]
    end = min(candidates) if candidates else len(text)
    return text[start:end]


def test_user_stories_doc_has_claim_disciplined_header() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    for line in STATUS_LINES:
        assert line in text

    assert "does not define constitutional truth" in text
    assert "does not expand the AfriTech proof surface" in text
    assert "does not claim global deployment readiness" in text
    assert "does not modify the constitutional enforcement contract" in text


def test_user_stories_doc_contains_expected_epics() -> None:
    text = read_doc()

    for epic in EPICS:
        assert f"## {epic}" in text


def test_user_stories_doc_classifies_implemented_stories() -> None:
    text = read_doc()

    for story in IMPLEMENTED_STORIES:
        window = story_window(text, story)
        assert "Status: [Implemented]" in window


def test_user_stories_doc_classifies_non_implemented_stories() -> None:
    text = read_doc()

    for story in IN_DEVELOPMENT_STORIES:
        assert "Status: [In Development]" in story_window(text, story)

    for story in PLANNED_STORIES:
        assert "Status: [Planned]" in story_window(text, story)

    for story in EXPLORATORY_STORIES:
        assert "Status: [Exploratory]" in story_window(text, story)


def test_user_stories_doc_isolates_future_experience_layer() -> None:
    text = read_doc()
    future = text[text.index("## Epic 8 - Future Experience Layer") :]

    assert "without treating planned product features as current proof truth" in future
    assert "Status: [Planned]" in future
    assert "Status: [Exploratory]" in future
    assert "not part of the current proof surface" in text


def test_user_stories_doc_avoids_readiness_inflation() -> None:
    text = read_doc().lower()

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in text

    assert "do not imply global production readiness" in text
    assert "unrestricted distributed systems readiness" in text
    assert "universal validator completeness" in text


def test_user_stories_doc_preserves_final_product_constraint() -> None:
    text = read_doc()

    assert "AfriRide user behavior is defined and constrained" in text
    assert "by constitutionally admissible execution" in text
    assert "not informal feature expectations" in text
