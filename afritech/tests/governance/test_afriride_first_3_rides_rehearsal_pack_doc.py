from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/AfriRide_First_3_Rides_Rehearsal_Pack.md"
CARDS = ROOT / "docs/operations/AfriRide_First_Ride_Response_Cards.csv"


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_rehearsal_pack_has_pre_live_boundary() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "STATUS: PRE-LIVE REHEARSAL PACK" in text
    assert "CLASSIFICATION: DRIVER CONVERSATION AND FIRST-RIDE SIMULATION SURFACE" in text
    assert "not runtime authority" in lowered
    assert "not add architecture" in text
    assert "new validators" in text
    assert "move into the first real rides faster" in text


def test_rehearsal_pack_defines_day_one_outcome() -> None:
    text = read_doc()

    for outcome in (
        "5 driver conversations",
        "3 qualified driver leads",
        "1 ready driver",
        "1 ready rider",
        "1 completed rehearsal ride",
        "1 replay-backed lesson",
    ):
        assert outcome in text


def test_rehearsal_pack_contains_word_for_word_driver_script() -> None:
    text = read_doc()

    for phrase in (
        "We are not asking you to switch platforms today.",
        "fair ride system where pricing is clear",
        "Can I ask you four quick questions",
        "What makes ride platforms unfair for you today?",
        "If a trip is questioned, we do not guess.",
        "Would you be willing to do one controlled test ride this week?",
        "what should a fair ride system never do to drivers?",
    ):
        assert phrase in text


def test_rehearsal_pack_defines_first_3_rides() -> None:
    text = read_doc()

    for ride in (
        "Ride 1 - Operator Rehearsal",
        "Ride 2 - Driver Training Ride",
        "Ride 3 - First Invited User Rehearsal",
    ):
        assert ride in text

    for pass_condition in (
        "ride completes with replay receipt and pricing explanation",
        "driver can complete the ride and explain why replay proof matters",
        "user can say whether the ride felt fair, reliable, and understandable",
    ):
        assert pass_condition in text


def test_rehearsal_pack_defines_problem_scenarios_and_replay_habit() -> None:
    text = read_doc()

    for scenario in (
        "driver asks about pay fairness",
        "driver worries about hidden pricing",
        "driver does not understand replay",
        "user asks why price is different",
        "pickup is delayed",
        "driver cancels",
        "user cancels",
        "payment record is unclear",
        "support issue has no trace",
        "replay receipt is missing",
    ):
        assert scenario in text

    for habit in (
        "find trip record",
        "inspect replay receipt",
        "explain price",
        "explain dispatch",
        "record driver reaction",
        "record user reaction",
        "choose one lesson",
    ):
        assert habit in text


def test_rehearsal_pack_defines_referral_and_decision_rules() -> None:
    text = read_doc()

    assert "Only ask after a driver or user has a good experience." in text
    assert "Do not ask for broad promotion before the first 10 rides are complete." in text

    for decision in (
        "go: run first live ride",
        "pause: fix one blocker before live ride",
        "narrow: reduce route, driver set, or user set",
    ):
        assert decision in text

    for basis in (
        "driver readiness",
        "user clarity",
        "pricing explainability",
        "dispatch explainability",
        "replay receipt availability",
        "support traceability",
    ):
        assert basis in text


def test_response_cards_cover_first_ride_scenarios() -> None:
    rows = list(csv.DictReader(CARDS.open(newline="", encoding="utf-8")))
    assert len(rows) == 10
    assert tuple(rows[0].keys()) == (
        "scenario",
        "operator_response",
        "required_evidence",
        "stop_if",
    )

    by_scenario = {row["scenario"]: row for row in rows}
    for scenario in (
        "driver asks about pay fairness",
        "driver worries about hidden pricing",
        "driver does not understand replay",
        "user asks why price is different",
        "pickup is delayed",
        "driver cancels",
        "user cancels",
        "payment record is unclear",
        "support issue has no trace",
        "replay receipt is missing",
    ):
        assert scenario in by_scenario
        assert by_scenario[scenario]["operator_response"]
        assert by_scenario[scenario]["required_evidence"]
        assert by_scenario[scenario]["stop_if"]

    assert by_scenario["replay receipt is missing"]["stop_if"] == (
        "next ride would start without replay proof"
    )
