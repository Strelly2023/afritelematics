"""Validate AfriRide Week 1-4 launch execution plan."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCH_PLAN = ROOT / "docs/operations/AfriRide_Week_1_4_Launch_Execution_Plan.md"

WEEKS = (
    "Week 1 - Pilot Readiness",
    "Week 2 - Driver Onboarding",
    "Week 3 - First User Rides",
    "Week 4 - Trust Review and Expansion Decision",
)

MINIMUM_PRODUCT = (
    "rider request flow",
    "driver accept flow",
    "dispatch assignment API",
    "trip status lifecycle",
    "pricing preview",
    "payment mock or manual settlement record",
    "support issue capture",
    "replay receipt per trip",
    "operator dashboard for pilot health",
)

REALITY_METRICS = (
    "rides_completed",
    "drivers_active",
    "users_invited",
    "users_activated",
    "booking_time",
    "ride_success_rate",
    "pickup_reliability",
    "replay_consistency",
    "pricing_anomaly_count",
    "dispatch_predictability",
    "dispute_count",
    "refund_case_count",
    "driver_complaint_count",
    "user_complaint_count",
    "replay_explained_incident_count",
)

STOP_RULES = (
    "replay mismatch",
    "unexplained pricing anomaly",
    "manual truth override attempted",
    "driver identity ambiguity",
    "support incident without trace",
    "payment record cannot be reconstructed",
    "pilot scope escape",
)

BLOCKED_WORK = (
    "new ecosystem pillar expansion",
    "multi-city launch",
    "general platform pitch expansion",
    "abstract validator expansion without pilot evidence",
    "large refactor unrelated to rides",
)


class AfriRideWeek14LaunchValidationError(RuntimeError):
    """Raised when the launch plan drifts away from real pilot execution."""


@dataclass(frozen=True)
class AfriRideWeek14LaunchReport:
    city_count: int
    driver_target: str
    user_target: str
    weeks: tuple[str, ...]
    minimum_product: tuple[str, ...]
    metrics: tuple[str, ...]
    stop_rules: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return (
            self.city_count == 1
            and self.driver_target == "10-50 active drivers"
            and self.user_target == "100-300 invited users"
            and self.weeks == WEEKS
            and self.minimum_product == MINIMUM_PRODUCT
            and self.metrics == REALITY_METRICS
            and self.stop_rules == STOP_RULES
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afriride.week_1_4_launch_execution_plan.v1",
            "city_count": self.city_count,
            "driver_target": self.driver_target,
            "user_target": self.user_target,
            "weeks": self.weeks,
            "minimum_product": self.minimum_product,
            "metrics": self.metrics,
            "stop_rules": self.stop_rules,
            "verified": self.verified,
        }


def validate(path: Path = LAUNCH_PLAN) -> AfriRideWeek14LaunchReport:
    if not path.exists():
        raise AfriRideWeek14LaunchValidationError("Week 1-4 launch plan missing")

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: REAL-WORLD EXECUTION PLAN")
    _require(text, "CLASSIFICATION: ONE-CITY LAUNCH OPERATING SURFACE")
    _require(text, "GOVERNANCE MODE: SHIP THIN, MEASURE REALITY, PRESERVE REPLAY PROOF")
    _require(text, "people use it")
    _require(text, "rides happen")
    _require(text, "drivers earn")
    _require(text, "the system proves fairness")
    _require(text, "city_count: 1")
    _require(text, "driver_target: 10-50 active drivers")
    _require(text, "user_target: 100-300 invited users")

    for phrase in WEEKS:
        _require(text, phrase)
    for phrase in MINIMUM_PRODUCT:
        _require(text, phrase)
    for phrase in REALITY_METRICS:
        _require(text, phrase)
    for phrase in STOP_RULES:
        _require(text, phrase)
    for phrase in BLOCKED_WORK:
        _require(text, phrase)

    _validate_anti_system_mode_boundary(text)

    report = AfriRideWeek14LaunchReport(
        city_count=1,
        driver_target="10-50 active drivers",
        user_target="100-300 invited users",
        weeks=WEEKS,
        minimum_product=MINIMUM_PRODUCT,
        metrics=REALITY_METRICS,
        stop_rules=STOP_RULES,
    )
    if not report.verified:
        raise AfriRideWeek14LaunchValidationError("Week 1-4 launch plan not verified")
    return report


def _validate_anti_system_mode_boundary(text: str) -> None:
    marker = "Blocked work:"
    if marker not in text:
        raise AfriRideWeek14LaunchValidationError("missing blocked work boundary")
    before_boundary = text.split(marker, maxsplit=1)[0]
    for phrase in BLOCKED_WORK:
        if phrase in before_boundary:
            raise AfriRideWeek14LaunchValidationError(
                f"blocked work appears before boundary: {phrase}"
            )


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideWeek14LaunchValidationError(f"missing phrase: {phrase}")


def format_summary(report: AfriRideWeek14LaunchReport) -> str:
    return "\n".join(
        (
            "AfriRide Week 1-4 launch validation PASSED",
            f"city_count={report.city_count}",
            f"driver_target={report.driver_target}",
            f"user_target={report.user_target}",
            f"weeks={len(report.weeks)}",
            f"minimum_product_items={len(report.minimum_product)}",
            f"metrics={len(report.metrics)}",
            f"stop_rules={len(report.stop_rules)}",
            f"verified={report.verified}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriRideWeek14LaunchValidationError as exc:
        print(f"AfriRide Week 1-4 launch validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
