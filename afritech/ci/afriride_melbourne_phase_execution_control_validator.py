"""Validate the AfriRide Melbourne phase execution control contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_MELBOURNE_PHASE_EXECUTION_CONTROL.md"

SCENARIOS = ("A1", "A2", "A3", "A4", "A5")
SCENARIO_OBJECTIVES = {
    "A1": "deterministic_ride_lifecycle",
    "A2": "deterministic_reassignment_under_rejection",
    "A3": "cancellation_halts_matching",
    "A4": "deterministic_timeout_under_delay",
    "A5": "payment_failure_state_isolation",
}
REQUIRED_SEQUENCES = {
    "A1": ("request", "match", "accept", "start", "route", "end", "payment_event"),
    "A2": ("driver_1_reject", "driver_2_reject", "driver_3_accept"),
    "A3": ("request_event", "matching_started_event", "cancel_event"),
    "A4": ("driver_1_timeout", "driver_2_accept"),
    "A5": (
        "request",
        "match",
        "accept",
        "start",
        "end",
        "payment_attempt",
        "payment_failed",
    ),
}
HARD_STOPS = (
    "replay_mismatch",
    "identity_drift",
    "missing_event",
    "duplicate_assignment",
    "accept_conflict",
    "post_cancel_assignment",
    "timeout_race",
    "payment_state_corrupts_trip_state",
)
EVIDENCE_REQUIRED = (
    "request_event",
    "match_event",
    "accept_event",
    "start_event",
    "route_events",
    "end_event",
    "assignment_events",
    "reject_events",
    "cancel_event",
    "timeout_event",
    "payment_attempt_event",
    "payment_failed_event",
    "execution_hash",
    "replay_hash",
)
FORBIDDEN_OPERATOR_ACTIONS = (
    "fix_data_during_execution",
    "ignore_anomalies",
    "force_completion",
    "manually_declare_success",
    "retry_payment_during_a5",
    "override_replay_mismatch",
)


class AfriRideMelbournePhaseExecutionControlValidationError(RuntimeError):
    """Raised when Melbourne phase execution control is invalid."""


@dataclass(frozen=True)
class AfriRideMelbournePhaseExecutionControlReport:
    schema: str
    status: str
    classification: str
    location: str
    phase_ready_to_run: bool
    phase_passed_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.melbourne_phase_execution_control.v1"
            and self.status == "melbourne_phase_execution_control_contract"
            and self.classification == "location_baseline_execution_control"
            and self.location == "Melbourne"
            and self.phase_ready_to_run is True
            and self.phase_passed_claimed is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideMelbournePhaseExecutionControlReport:
    if not path.exists():
        raise AfriRideMelbournePhaseExecutionControlValidationError(
            "Melbourne phase execution control contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: MELBOURNE PHASE EXECUTION CONTROL CONTRACT")
    _require(text, "CLASSIFICATION: LOCATION BASELINE EXECUTION CONTROL")
    _require(text, "A1 -> A2 -> A3 -> A4 -> A5")
    _require(text, "does not claim that Melbourne execution has passed")
    _require(text, "The operator preserves evidence, stops on invalidity, and lets replay decide truth")
    _require(text, "Melbourne Phase Passed: NOT CLAIMED")

    payload = _load_payload(text)
    _require_equal(payload["scenarios"], SCENARIOS, "scenarios")
    if payload["scenario_objectives"] != SCENARIO_OBJECTIVES:
        raise AfriRideMelbournePhaseExecutionControlValidationError(
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
    if payload["operator_law"] != "preserve_evidence_stop_on_invalidity_replay_decides_truth":
        raise AfriRideMelbournePhaseExecutionControlValidationError(
            "operator law mismatch"
        )

    report = AfriRideMelbournePhaseExecutionControlReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        location=payload["location"],
        phase_ready_to_run=payload["phase_ready_to_run"],
        phase_passed_claimed=payload["phase_passed_claimed"],
    )
    if not report.verified:
        raise AfriRideMelbournePhaseExecutionControlValidationError(
            "Melbourne phase execution control report is not verified"
        )
    return report


def _validate_required_sequences(sequences: dict[str, list[str]]) -> None:
    for scenario, expected in REQUIRED_SEQUENCES.items():
        if sequences.get(scenario) != list(expected):
            raise AfriRideMelbournePhaseExecutionControlValidationError(
                f"required sequence mismatch: {scenario}"
            )


def _validate_completion_rule(rule: dict[str, Any]) -> None:
    expected = {
        "all_scenarios_pass": True,
        "all_hashes_match": True,
        "identity_integrity": True,
        "event_integrity": True,
    }
    if rule != expected:
        raise AfriRideMelbournePhaseExecutionControlValidationError(
            "completion rule mismatch"
        )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(melbourne_phase_execution_control:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideMelbournePhaseExecutionControlValidationError(
            "missing melbourne_phase_execution_control yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("melbourne_phase_execution_control") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideMelbournePhaseExecutionControlValidationError(
            "invalid melbourne_phase_execution_control yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideMelbournePhaseExecutionControlValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideMelbournePhaseExecutionControlValidationError(f"{label} mismatch")


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideMelbournePhaseExecutionControlValidationError as exc:
        print(f"MELBOURNE PHASE EXECUTION CONTROL REJECTED: {exc}")
        return 1
    print("AfriRide Melbourne phase execution control validation PASSED")
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
