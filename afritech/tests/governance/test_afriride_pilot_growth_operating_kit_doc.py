from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/AfriRide_Pilot_Growth_Operating_Kit.md"
TEMPLATE = ROOT / "docs/operations/AfriRide_Pilot_Daily_Metrics_Template.csv"


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_growth_kit_has_field_execution_boundary() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "STATUS: FIELD EXECUTION KIT" in text
    assert "CLASSIFICATION: DRIVER AND FIRST-USER ACQUISITION SURFACE" in text
    assert "not runtime authority" in lowered
    assert "not introduce new architecture" in text
    assert "new pillars" in text
    assert "new validation program" in text


def test_growth_kit_prioritizes_daily_real_world_outcomes() -> None:
    text = read_doc()

    for outcome in (
        "new driver conversation",
        "new driver onboarded",
        "new invited user",
        "new completed ride",
        "new replay-backed lesson",
        "If none of those happened, the day stayed in system mode.",
    ):
        assert outcome in text


def test_growth_kit_defines_driver_script_and_onboarding() -> None:
    text = read_doc()

    for script_part in (
        "We are inviting 10-50 drivers for the controlled pilot.",
        "What makes ride platforms unfair for you today?",
        "What would make you trust a new ride system?",
        "every trip has a replay record",
        "complete test rides",
    ):
        assert script_part in text

    for checklist_item in (
        "identity record captured",
        "vehicle record captured",
        "driver accept flow tested",
        "fair pricing explanation completed",
        "replay receipt shown",
        "driver complaint channel confirmed",
    ):
        assert checklist_item in text


def test_growth_kit_defines_first_100_users_and_first_50_rides() -> None:
    text = read_doc()

    for target in (
        "airport transfer riders",
        "commuters in the pilot corridor",
        "students with repeat routes",
        "healthcare or shift workers",
        "friends and family referrals inside the service zone",
    ):
        assert target in text

    for success in (
        "50+ real rides",
        "10+ active drivers",
        "100+ invited users",
        "zero unexplained pricing anomalies",
        "all completed rides replay-backed",
    ):
        assert success in text


def test_growth_kit_defines_support_and_weekly_decision_rules() -> None:
    text = read_doc()

    for support_step in (
        "find the trip record",
        "run or inspect the replay",
        "explain pricing, dispatch, cancellation, or failure in plain language",
        "record whether the explanation was accepted",
    ):
        assert support_step in text

    for decision in ("go: continue pilot as scoped", "pause: stop live rides", "narrow: reduce zone"):
        assert decision in text


def test_growth_kit_blocks_system_mode_work() -> None:
    text = read_doc()
    before_boundary = text.split("Blocked:", maxsplit=1)[0]

    for blocked in (
        "new ecosystem expansion",
        "new pillar work",
        "abstract validator work",
        "multi-city launch work",
        "architecture polishing unrelated to rides",
    ):
        assert blocked in text
        assert blocked not in before_boundary


def test_daily_metrics_template_has_required_columns() -> None:
    rows = list(csv.DictReader(TEMPLATE.open(newline="", encoding="utf-8")))
    assert len(rows) == 1

    expected = (
        "date",
        "city",
        "drivers_contacted",
        "drivers_onboarded",
        "drivers_active",
        "users_invited",
        "users_activated",
        "rides_requested",
        "rides_completed",
        "rides_failed",
        "booking_time_median_seconds",
        "pickup_reliability_rate",
        "ride_success_rate",
        "pricing_anomaly_count",
        "replay_mismatch_count",
        "dispatch_unexplained_count",
        "dispute_count",
        "refund_case_count",
        "driver_complaint_count",
        "user_complaint_count",
        "replay_explained_incident_count",
        "top_driver_complaint",
        "top_user_complaint",
        "operator_decision",
    )

    assert tuple(rows[0].keys()) == expected
    assert rows[0]["operator_decision"] == "go|pause|narrow"
