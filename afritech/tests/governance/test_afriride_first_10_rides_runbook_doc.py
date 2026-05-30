from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/AfriRide_First_10_Rides_Runbook.md"
DASHBOARD = ROOT / "docs/operations/AfriRide_Pilot_KPI_Dashboard_Template.csv"


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_first_10_runbook_has_day_one_boundary() -> None:
    text = read_doc()
    lowered = text.lower()
    normalized = " ".join(text.split())

    assert "STATUS: DAY-ONE FIELD RUNBOOK" in text
    assert "CLASSIFICATION: FIRST REAL RIDES EXECUTION SURFACE" in text
    assert "not runtime authority" in lowered
    assert "not create new architecture" in text
    assert "new validators" in text
    assert "complete rides, capture proof, and learn from reality" in normalized


def test_first_10_runbook_defines_success_and_roles() -> None:
    text = read_doc()

    for success in (
        "drivers understand the flow",
        "users understand the promise",
        "rides complete or fail with trace",
        "pricing is explainable",
        "dispatch is explainable",
        "replay evidence exists",
        "one blocker is chosen for the next day",
    ):
        assert success in text

    for role in (
        "pilot lead",
        "driver coordinator",
        "user coordinator",
        "support operator",
        "replay operator",
    ):
        assert role in text


def test_first_10_runbook_defines_pre_ride_and_execution_checklists() -> None:
    text = read_doc()

    for setup in (
        "confirm service zone",
        "confirm driver roster",
        "confirm first user list",
        "confirm support phone or chat",
        "open daily metrics template",
        "open incident log",
    ):
        assert setup in text

    for ride_step in (
        "record ride_id",
        "record driver_id",
        "record user_id",
        "show or confirm price before trip",
        "assign driver",
        "confirm driver accepted",
        "attach replay receipt",
        "ask driver: did this feel fair?",
        "ask user: did this feel reliable?",
    ):
        assert ride_step in text


def test_first_10_runbook_defines_ride_sequence_and_coverage() -> None:
    text = read_doc()

    for ride in (
        "Ride 1: internal operator ride",
        "Ride 4: first invited user ride",
        "Ride 8: support-observed ride",
        "Ride 10: trust review ride",
    ):
        assert ride in text

    for coverage in (
        "at least 3 drivers",
        "at least 3 users",
        "at least 2 repeat corridor rides",
        "at least 1 support-observed ride",
        "10 replay receipt checks",
        "10 price explanation checks",
    ):
        assert coverage in text


def test_first_10_runbook_defines_plain_language_checks_and_stop_rules() -> None:
    text = read_doc()

    for question in (
        "Did the price feel fair?",
        "Did the pickup assignment make sense?",
        "Would you accept another ride?",
        "Was booking clear?",
        "Would you use this again?",
    ):
        assert question in text

    for stop_rule in (
        "driver identity is uncertain",
        "user consent is missing",
        "price cannot be explained",
        "dispatch cannot be explained",
        "replay receipt is missing",
        "support issue has no trace",
        "operator changes truth manually",
    ):
        assert stop_rule in text


def test_first_10_runbook_defines_end_of_day_decision() -> None:
    text = read_doc()

    for review in (
        "count completed rides",
        "count failed rides",
        "count replay-backed rides",
        "count pricing anomalies",
        "choose one blocker",
        "choose tomorrow's first action",
    ):
        assert review in text

    for decision in (
        "go: run the next rides",
        "pause: stop until blocker is fixed",
        "narrow: reduce zone, drivers, or users",
    ):
        assert decision in text


def test_kpi_dashboard_template_has_weekly_columns_and_targets() -> None:
    rows = list(csv.DictReader(DASHBOARD.open(newline="", encoding="utf-8")))
    assert rows

    expected_columns = (
        "metric",
        "day_1",
        "day_2",
        "day_3",
        "day_4",
        "day_5",
        "day_6",
        "day_7",
        "target",
        "operator_note",
    )
    assert tuple(rows[0].keys()) == expected_columns

    by_metric = {row["metric"]: row for row in rows}
    for metric in (
        "drivers_contacted",
        "drivers_onboarded",
        "drivers_active",
        "users_invited",
        "users_activated",
        "rides_requested",
        "rides_completed",
        "ride_success_rate",
        "booking_time_median_seconds",
        "pickup_reliability_rate",
        "pricing_anomaly_count",
        "replay_mismatch_count",
        "dispatch_unexplained_count",
        "operator_decision",
    ):
        assert metric in by_metric

    assert by_metric["rides_completed"]["target"] == "10_first_target"
    assert by_metric["pricing_anomaly_count"]["target"] == "0"
    assert by_metric["replay_mismatch_count"]["target"] == "0"
    assert by_metric["operator_decision"]["target"] == "go_pause_or_narrow"
