from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/AfriRide_First_3_Live_Rides_Execution_Packet.md"
LOG = ROOT / "docs/operations/AfriRide_First_3_Live_Rides_Log_Template.csv"


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_live_packet_has_live_execution_boundary() -> None:
    text = read_doc()
    lowered = " ".join(text.lower().split())

    assert "STATUS: LIVE FIELD EXECUTION PACKET" in text
    assert "CLASSIFICATION: FIRST REAL RIDES OPERATING SURFACE" in text
    assert "not runtime authority" in lowered
    assert "not create new architecture" in text
    assert "new validators" in text
    assert "another rehearsal loop" in text


def test_live_packet_forces_one_rehearsal_then_live() -> None:
    text = read_doc()
    lowered = " ".join(text.lower().split())

    for rule in (
        "Run one rehearsal.",
        "Then run live ride 1.",
        "Do not rehearse endlessly.",
    ):
        assert rule in text
    assert "pause only long enough to fix that single blocker" in lowered


def test_live_packet_defines_live_ride_objectives_and_roles() -> None:
    text = read_doc()

    for objective in (
        "Can a real driver complete the flow?",
        "Can a real rider understand the promise?",
        "Can pricing be explained plainly?",
        "Can dispatch be explained plainly?",
        "Can replay reconstruct what happened?",
        "Can support handle confusion without guessing?",
    ):
        assert objective in text

    for role in (
        "pilot lead",
        "driver coordinator",
        "rider coordinator",
        "support operator",
        "replay operator",
    ):
        assert role in text


def test_live_packet_defines_three_live_rides() -> None:
    text = read_doc()

    for ride in (
        "Live Ride 1 - Controlled Real Ride",
        "Live Ride 2 - Repeatability Check",
        "Live Ride 3 - Confidence Check",
    ):
        assert ride in text

    for pass_condition in (
        "ride completes or fails with trace, replay, and plain-language explanation",
        "ride 2 produces no new unexplained pricing, dispatch, or replay issue",
        "team can explain all three rides without guessing",
    ):
        assert pass_condition in text


def test_live_packet_handles_rider_confusion_and_failed_rides() -> None:
    text = read_doc()

    for handling in (
        "Thanks for saying that.",
        "Let me check the trip record",
        "identify the ride",
        "inspect the trip record",
        "record whether the rider accepted the explanation",
        "Do not:",
        "guess",
        "change the truth manually",
    ):
        assert handling in text

    for issue_class in (
        "driver confusion",
        "rider confusion",
        "pricing explanation issue",
        "dispatch explanation issue",
        "pickup timing issue",
        "payment record issue",
        "support trace issue",
        "replay proof issue",
    ):
        assert issue_class in text


def test_live_packet_defines_go_forward_gate_and_referral_boundary() -> None:
    text = read_doc()

    for gate in (
        "at least 2 of 3 rides completed or failed with full trace",
        "0 unexplained pricing issues",
        "0 unexplained dispatch issues",
        "0 replay proof gaps",
        "driver feedback captured for every ride",
        "rider feedback captured for every ride",
        "operator decision recorded",
    ):
        assert gate in text

    assert "Ask for referrals only if the experience was good and explainable." in text
    assert "Do not ask for public promotion before the first 10 rides are complete." in text


def test_first_3_live_rides_log_template_has_required_rows() -> None:
    rows = list(csv.DictReader(LOG.open(newline="", encoding="utf-8")))
    assert len(rows) == 3
    assert tuple(rows[0].keys()) == (
        "ride_number",
        "ride_id",
        "driver_id",
        "rider_id",
        "route_type",
        "status",
        "price_explained",
        "dispatch_explained",
        "replay_receipt_checked",
        "driver_fairness_response",
        "rider_reliability_response",
        "confusion_point",
        "issue_class",
        "operator_decision",
        "next_action",
    )

    assert [row["ride_number"] for row in rows] == ["1", "2", "3"]
    assert rows[0]["next_action"] == "run_ride_2"
    assert rows[1]["next_action"] == "run_ride_3"
    assert rows[2]["next_action"] == "review_first_3"
