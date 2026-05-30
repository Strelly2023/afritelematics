from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/operations/AfriRide_Week_1_4_Launch_Execution_Plan.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_week_1_4_plan_has_real_world_execution_boundary() -> None:
    text = read_doc()
    lowered = text.lower()
    normalized = " ".join(lowered.split())

    assert "STATUS: REAL-WORLD EXECUTION PLAN" in text
    assert "CLASSIFICATION: ONE-CITY LAUNCH OPERATING SURFACE" in text
    assert "not runtime authority" in lowered
    assert "or evidence that a real city pilot has succeeded" in normalized
    assert "staying in system mode" in text


def test_week_1_4_plan_declares_new_success_metric() -> None:
    text = read_doc()

    for outcome in (
        "people use it",
        "rides happen",
        "drivers earn",
        "the system proves fairness",
    ):
        assert outcome in text

    for scope in (
        "city_count: 1",
        "driver_target: 10-50 active drivers",
        "user_target: 100-300 invited users",
    ):
        assert scope in text


def test_week_1_4_plan_defines_thin_product_layer() -> None:
    text = read_doc()

    for minimum in (
        "rider request flow",
        "driver accept flow",
        "dispatch assignment API",
        "trip status lifecycle",
        "pricing preview",
        "payment mock or manual settlement record",
        "support issue capture",
        "replay receipt per trip",
        "operator dashboard for pilot health",
    ):
        assert minimum in text

    for deferred in (
        "advanced marketplace optimization",
        "multi-region deployment",
        "full payment provider integration",
    ):
        assert deferred in text


def test_week_1_4_plan_defines_weekly_execution_gates() -> None:
    text = read_doc()

    for week in (
        "Week 1 - Pilot Readiness",
        "Week 2 - Driver Onboarding",
        "Week 3 - First User Rides",
        "Week 4 - Trust Review and Expansion Decision",
    ):
        assert week in text

    for gate in (
        "operators can request, assign, accept, complete, and replay a controlled test ride",
        "at least 10 drivers can complete test rides with replay receipts and no pricing anomaly",
        "first live user rides complete with replay consistency and zero pricing anomalies",
        "continue only if trust signals are explainable and replay proof remains intact",
    ):
        assert gate in text


def test_week_1_4_plan_defines_reality_metrics_and_stop_rules() -> None:
    text = read_doc()

    for metric in (
        "rides_completed",
        "drivers_active",
        "users_invited",
        "users_activated",
        "booking_time",
        "ride_success_rate",
        "replay_consistency",
        "pricing_anomaly_count",
        "driver_complaint_count",
        "user_complaint_count",
    ):
        assert metric in text

    for stop_rule in (
        "replay mismatch",
        "unexplained pricing anomaly",
        "manual truth override attempted",
        "support incident without trace",
        "payment record cannot be reconstructed",
        "pilot scope escape",
    ):
        assert stop_rule in text


def test_week_1_4_plan_blocks_system_mode_work() -> None:
    text = read_doc()
    before_boundary = text.split("Blocked work:", maxsplit=1)[0]

    for blocked in (
        "new ecosystem pillar expansion",
        "multi-city launch",
        "general platform pitch expansion",
        "abstract validator expansion without pilot evidence",
        "large refactor unrelated to rides",
    ):
        assert blocked in text
        assert blocked not in before_boundary

    for allowed in (
        "fix ride blockers",
        "fix driver blockers",
        "fix user blockers",
        "improve replay evidence",
        "improve support response",
        "improve pilot instrumentation",
    ):
        assert allowed in text
