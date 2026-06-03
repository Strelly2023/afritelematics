"""Validate the AfriRide controlled pilot scenario matrix."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DOC = ROOT / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_SCENARIO_MATRIX.md"

REQUIRED_LOCATIONS = ("melbourne", "bujumbura_uvira", "kinshasa")

REQUIRED_SCENARIOS = {
    "melbourne": (
        "A1_normal_ride_completion",
        "A2_driver_reject_cascade",
        "A3_rider_cancels_during_matching",
        "A4_network_delay_before_accept",
        "A5_payment_failure_card_declined",
    ),
    "bujumbura_uvira": (
        "C1_trip_crossing_border",
        "C2_driver_loses_network_mid_trip",
        "C3_delayed_event_submission",
        "D1_gps_drift_wrong_location",
        "D2_cash_payment_dispute",
    ),
    "kinshasa": (
        "E1_multiple_simultaneous_requests",
        "E2_duplicate_accept_attempt",
        "E3_route_deviation_by_driver",
        "F1_fake_trip_completion",
        "F2_rider_ghost_request_spam",
        "F3_manual_driver_status_toggle_abuse",
    ),
}

SCENARIO_STRUCTURE = (
    "scenario_type",
    "trigger",
    "expected_system_behavior",
    "replay_condition",
    "pass_fail_criteria",
)

GLOBAL_SCENARIOS = (
    "G1_replay_integrity",
    "G2_identity_invariance",
    "G3_event_completeness",
)

PASS_GATE = (
    "replay_stable",
    "deterministic_output_preserved",
    "proof_generated",
    "no_invariant_violation",
)

FAIL_GATE = (
    "replay_mismatch",
    "identity_drift",
    "hidden_state_mutation",
    "non_deterministic_behavior",
)

FORBIDDEN_CLAIMS = (
    "production launch ready",
    "real-world operational success certified",
    "global rollout approved",
)


class AfriRideControlledPilotScenarioMatrixValidationError(RuntimeError):
    """Raised when the scenario matrix is not admissible."""


@dataclass(frozen=True)
class AfriRideControlledPilotScenarioMatrixReport:
    schema: str
    status: str
    classification: str
    location_count: int
    scenario_count: int
    truth_authority: str
    production_launch_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.controlled_pilot_scenario_matrix.v1"
            and self.status == "controlled_pilot_scenario_matrix"
            and self.classification
            == "deterministic_failure_and_real_world_case_contract"
            and self.location_count == 3
            and self.scenario_count == 16
            and self.truth_authority == "replay_only"
            and self.production_launch_claimed is False
        )


def validate(path: Path = SCENARIO_DOC) -> AfriRideControlledPilotScenarioMatrixReport:
    if not path.exists():
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "controlled pilot scenario matrix missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: CONTROLLED PILOT SCENARIO MATRIX")
    _require(text, "CLASSIFICATION: DETERMINISTIC FAILURE AND REAL-WORLD CASE CONTRACT")
    _require(text, "It is not a production launch plan")
    _require(text, "System validity = survives ALL three environments")
    _require(text, "A pilot system is considered valid ONLY IF")

    lowered = text.lower()
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in lowered:
            raise AfriRideControlledPilotScenarioMatrixValidationError(
                f"forbidden claim: {phrase}"
            )

    payload = _load_matrix_payload(text)

    if payload["truth_authority"] != "replay_only":
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "truth authority must remain replay_only"
        )
    if payload["production_launch_claimed"] is not False:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "scenario matrix claims production launch"
        )
    if payload["operational_success_claimed"] is not False:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "scenario matrix claims operational success"
        )
    _require_equal(payload["scenario_structure"], SCENARIO_STRUCTURE, "scenario structure")
    _require_equal(payload["pass_gate"], PASS_GATE, "pass gate")
    _require_equal(payload["fail_gate"], FAIL_GATE, "fail gate")

    locations = payload["locations"]
    if tuple(locations.keys()) != REQUIRED_LOCATIONS:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "location coverage mismatch"
        )

    scenario_count = 0
    for location in REQUIRED_LOCATIONS:
        scenarios = locations[location]["scenarios"]
        if tuple(scenarios.keys()) != REQUIRED_SCENARIOS[location]:
            raise AfriRideControlledPilotScenarioMatrixValidationError(
                f"scenario coverage mismatch: {location}"
            )
        scenario_count += len(scenarios)
        for scenario_name, scenario in scenarios.items():
            _validate_scenario(location, scenario_name, scenario)

    if tuple(payload["global_scenarios"].keys()) != GLOBAL_SCENARIOS:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "global scenario coverage mismatch"
        )

    technical = payload["technical_metrics"]
    if technical != {
        "replay_success_rate": "100%",
        "event_integrity": "100%",
        "identity_drift": "0",
        "execution_divergence": "0",
    }:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "technical metrics contract mismatch"
        )

    failures = payload["failure_metrics"]["all_failures"]
    if failures != ["logged", "replayable", "isolated"]:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "failure metrics contract mismatch"
        )

    report = AfriRideControlledPilotScenarioMatrixReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        location_count=len(locations),
        scenario_count=scenario_count,
        truth_authority=payload["truth_authority"],
        production_launch_claimed=payload["production_launch_claimed"],
    )
    if not report.verified:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "scenario matrix report is not verified"
        )
    return report


def _validate_scenario(location: str, scenario_name: str, scenario: dict[str, Any]) -> None:
    for key in SCENARIO_STRUCTURE:
        if key not in scenario:
            raise AfriRideControlledPilotScenarioMatrixValidationError(
                f"missing {key}: {location}.{scenario_name}"
            )
    if not scenario["trigger"]:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            f"missing trigger: {location}.{scenario_name}"
        )
    if not scenario["expected_system_behavior"]:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            f"missing expected behavior: {location}.{scenario_name}"
        )
    criteria = scenario["pass_fail_criteria"]
    if not isinstance(criteria, dict) or not criteria.get("pass") or not criteria.get("fail"):
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            f"invalid pass/fail criteria: {location}.{scenario_name}"
        )


def _load_matrix_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(controlled_pilot_scenario_matrix:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "missing controlled_pilot_scenario_matrix yaml block"
        )
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict) or not isinstance(
        data.get("controlled_pilot_scenario_matrix"), dict
    ):
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            "invalid controlled_pilot_scenario_matrix yaml block"
        )
    return data["controlled_pilot_scenario_matrix"]


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideControlledPilotScenarioMatrixValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideControlledPilotScenarioMatrixValidationError(f"{label} mismatch")


def format_summary(report: AfriRideControlledPilotScenarioMatrixReport) -> str:
    return "\n".join(
        (
            "AfriRide controlled pilot scenario matrix validation PASSED",
            f"schema={report.schema}",
            f"status={report.status}",
            f"classification={report.classification}",
            f"locations={report.location_count}",
            f"scenarios={report.scenario_count}",
            f"truth_authority={report.truth_authority}",
            f"production_launch_claimed={report.production_launch_claimed}",
            f"verified={report.verified}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriRideControlledPilotScenarioMatrixValidationError as exc:
        print(f"AfriRide controlled pilot scenario matrix validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
