"""Validate AfriRide one-city pilot dominance strategy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRATEGY_DOC = ROOT / "docs/roadmap/AfriRide_Pilot_Dominance_Strategy.md"

EXECUTION_PILLARS = (
    "Focus",
    "Simplification",
    "Real-World Deployment",
    "Strategic Dominance Loops",
)

CONTROLLED_PILOT_GATES = (
    "city_count: 1",
    "drivers: 10-50",
    "users: 100-300",
    "replay consistency",
    "zero pricing anomalies",
    "dispatch determinism",
    "booking time",
    "ride success rate",
    "disputes",
    "refund cases",
    "driver complaints",
)

DOMINANCE_LOOPS = (
    "Trust Loop",
    "Driver Loyalty Loop",
    "Governance Advantage Loop",
)

ROADMAP_STAGES = (
    "Stage 1: 0-3 Months",
    "Stage 2: 3-6 Months",
    "Stage 3: 6-12 Months",
    "Stage 4: 12+ Months",
)

FORBIDDEN_EXTERNAL_LEADS = (
    "GA Elite",
    "18 pillars",
    "constitutional layers",
    "complete ecosystem",
    "autonomous civilization platform",
)


class AfriRidePilotDominanceValidationError(RuntimeError):
    """Raised when the AfriRide strategy loses product focus."""


@dataclass(frozen=True)
class AfriRidePilotDominanceReport:
    battlefield: str
    product_message: str
    positioning_line: str
    driver_range: str
    user_range: str
    execution_pillars: tuple[str, ...]
    dominance_loops: tuple[str, ...]
    roadmap_stages: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return (
            self.battlefield == "AfriRide"
            and self.driver_range == "10-50"
            and self.user_range == "100-300"
            and self.execution_pillars == EXECUTION_PILLARS
            and self.dominance_loops == DOMINANCE_LOOPS
            and self.roadmap_stages == ROADMAP_STAGES
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afriride.pilot_dominance_strategy.v1",
            "battlefield": self.battlefield,
            "product_message": self.product_message,
            "positioning_line": self.positioning_line,
            "driver_range": self.driver_range,
            "user_range": self.user_range,
            "execution_pillars": self.execution_pillars,
            "dominance_loops": self.dominance_loops,
            "roadmap_stages": self.roadmap_stages,
            "verified": self.verified,
        }


def validate(path: Path = STRATEGY_DOC) -> AfriRidePilotDominanceReport:
    if not path.exists():
        raise AfriRidePilotDominanceValidationError("pilot dominance strategy missing")

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: BOUNDED PRODUCT DOMINANCE STRATEGY")
    _require(text, "CLASSIFICATION: AFRIRIDE ONE-CITY MARKET PROOF SURFACE")
    _require(text, "GOVERNANCE MODE: INTERNAL CONSTITUTION, EXTERNAL PRODUCT TRUST")
    _require(text, "build the best ride system in one city")
    _require(text, "AfriRide is the only ride system where every trip is provable, fair, and cannot be manipulated.")
    _require(text, "Uber guesses. We prove.")

    for phrase in EXECUTION_PILLARS:
        _require(text, phrase)
    for phrase in CONTROLLED_PILOT_GATES:
        _require(text, phrase)
    for phrase in DOMINANCE_LOOPS:
        _require(text, phrase)
    for phrase in ROADMAP_STAGES:
        _require(text, phrase)
    for phrase in FORBIDDEN_EXTERNAL_LEADS:
        _require(text, phrase)

    _validate_forbidden_language_boundary(text)

    report = AfriRidePilotDominanceReport(
        battlefield="AfriRide",
        product_message=(
            "AfriRide is the only ride system where every trip is provable, "
            "fair, and cannot be manipulated."
        ),
        positioning_line="Uber guesses. We prove.",
        driver_range="10-50",
        user_range="100-300",
        execution_pillars=EXECUTION_PILLARS,
        dominance_loops=DOMINANCE_LOOPS,
        roadmap_stages=ROADMAP_STAGES,
    )
    if not report.verified:
        raise AfriRidePilotDominanceValidationError(
            "pilot dominance strategy is not verified"
        )
    return report


def _validate_forbidden_language_boundary(text: str) -> None:
    marker = "External language must not lead with:"
    if marker not in text:
        raise AfriRidePilotDominanceValidationError(
            "missing external language boundary"
        )
    before_boundary = text.split(marker, maxsplit=1)[0]
    for phrase in FORBIDDEN_EXTERNAL_LEADS:
        if phrase in before_boundary:
            raise AfriRidePilotDominanceValidationError(
                f"external strategy leads with internal phrase: {phrase}"
            )


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRidePilotDominanceValidationError(f"missing phrase: {phrase}")


def format_summary(report: AfriRidePilotDominanceReport) -> str:
    return "\n".join(
        (
            "AfriRide pilot dominance validation PASSED",
            f"battlefield={report.battlefield}",
            f"product_message={report.product_message}",
            f"positioning_line={report.positioning_line}",
            f"drivers={report.driver_range} users={report.user_range}",
            f"dominance_loops={','.join(report.dominance_loops)}",
            f"verified={report.verified}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriRidePilotDominanceValidationError as exc:
        print(f"AfriRide pilot dominance validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
