"""Validate the AfriRide Kinshasa phase execution control contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_KINSHASA_PHASE_EXECUTION_CONTROL.md"

SCENARIOS = ("E1", "E2", "E3", "F1", "F2", "F3")
SCENARIO_OBJECTIVES = {
    "E1": "deterministic_isolation_under_concurrency",
    "E2": "deterministic_duplicate_accept_arbitration",
    "E3": "behavioral_route_deviation_preservation",
    "F1": "lifecycle_invariant_enforcement",
    "F2": "deterministic_rate_control_under_spam",
    "F3": "availability_state_determinism_under_toggle_abuse",
}
REQUIRED_SEQUENCES = {
    "E1": ("concurrent_requests", "partition_assignments", "isolated_matching", "independent_completion"),
    "E2": ("single_request", "candidate_driver_list", "simultaneous_accept_attempts", "deterministic_winner", "loser_rejected"),
    "E3": ("normal_trip_start", "route_deviation", "actual_route_preserved", "end"),
    "F1": ("request", "match", "accept", "invalid_complete_attempt", "violation_recorded"),
    "F2": ("rapid_request_burst", "deterministic_rate_control", "accept_reject_pattern_recorded"),
    "F3": ("online", "offline", "online", "offline", "online", "deterministic_matching_outcome"),
}
HARD_STOPS = (
    "race_condition",
    "conflicting_assignments",
    "non_deterministic_outcome",
    "replay_mismatch",
    "hidden_behavior",
    "dual_acceptance",
    "route_rewrite",
    "invalid_lifecycle_completion",
    "random_rate_control",
    "missing_status_transition",
    "timing_based_selection_bias",
)
EVIDENCE_REQUIRED = (
    "request_events",
    "partition_assignments",
    "match_events",
    "accept_events",
    "reject_events",
    "route_events",
    "deviation_points",
    "invalid_complete_attempt_event",
    "violation_event",
    "rate_limit_decisions",
    "driver_status_events",
    "match_decisions",
    "execution_hash",
    "replay_hash",
)
FORBIDDEN_OPERATOR_ACTIONS = (
    "restrict_behaviors_artificially",
    "guide_users_to_ideal_paths",
    "ignore_adversarial_cases",
    "fix_outcomes_manually",
    "force_winner_manually",
    "filter_state_changes",
)


class AfriRideKinshasaPhaseExecutionControlValidationError(RuntimeError):
    """Raised when Kinshasa phase execution control is invalid."""


@dataclass(frozen=True)
class AfriRideKinshasaPhaseExecutionControlReport:
    schema: str
    status: str
    classification: str
    location: str
    phase_ready_to_run: bool
    phase_passed_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.kinshasa_phase_execution_control.v1"
            and self.status == "kinshasa_phase_execution_control_contract"
            and self.classification == "high_density_adversarial_execution_control"
            and self.location == "Kinshasa"
            and self.phase_ready_to_run is True
            and self.phase_passed_claimed is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideKinshasaPhaseExecutionControlReport:
    if not path.exists():
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            "Kinshasa phase execution control contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: KINSHASA PHASE EXECUTION CONTROL CONTRACT")
    _require(text, "CLASSIFICATION: HIGH DENSITY ADVERSARIAL EXECUTION CONTROL")
    _require(text, "E1 -> E2 -> E3 -> F1 -> F2 -> F3")
    _require(text, "User behavior MAY be unpredictable")
    _require(text, "System output MUST remain deterministic")
    _require(text, "Kinshasa Phase Passed: NOT CLAIMED")

    payload = _load_payload(text)
    _require_equal(payload["scenarios"], SCENARIOS, "scenarios")
    if payload["scenario_objectives"] != SCENARIO_OBJECTIVES:
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            "scenario objectives mismatch"
        )
    _validate_required_sequences(payload["required_sequences"])
    _require_equal(payload["hard_stops"], HARD_STOPS, "hard stops")
    _require_equal(payload["evidence_required"], EVIDENCE_REQUIRED, "evidence")
    _validate_completion_rule(payload["completion_rule"])
    _require_equal(
        payload["forbidden_operator_actions"],
        FORBIDDEN_OPERATOR_ACTIONS,
        "forbidden operator actions",
    )
    if payload["operator_law"] != "system_correct_despite_uncontrolled_users":
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            "operator law mismatch"
        )

    report = AfriRideKinshasaPhaseExecutionControlReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        location=payload["location"],
        phase_ready_to_run=payload["phase_ready_to_run"],
        phase_passed_claimed=payload["phase_passed_claimed"],
    )
    if not report.verified:
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            "Kinshasa phase execution control report is not verified"
        )
    return report


def _validate_required_sequences(sequences: dict[str, list[str]]) -> None:
    for scenario, expected in REQUIRED_SEQUENCES.items():
        if sequences.get(scenario) != list(expected):
            raise AfriRideKinshasaPhaseExecutionControlValidationError(
                f"required sequence mismatch: {scenario}"
            )


def _validate_completion_rule(rule: dict[str, Any]) -> None:
    expected = {
        "all_scenarios_pass": True,
        "replay_consistency": "100%",
        "determinism_preserved": True,
        "no_race_conditions": True,
    }
    if rule != expected:
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            "completion rule mismatch"
        )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(kinshasa_phase_execution_control:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            "missing kinshasa_phase_execution_control yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("kinshasa_phase_execution_control") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            "invalid kinshasa_phase_execution_control yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideKinshasaPhaseExecutionControlValidationError(
            f"{label} mismatch"
        )


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideKinshasaPhaseExecutionControlValidationError as exc:
        print(f"KINSHASA PHASE EXECUTION CONTROL REJECTED: {exc}")
        return 1
    print("AfriRide Kinshasa phase execution control validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"location={report.location}")
    print(f"phase_ready_to_run={report.phase_ready_to_run}")
    print(f"phase_passed_claimed={report.phase_passed_claimed}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
