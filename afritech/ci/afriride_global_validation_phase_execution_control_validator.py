"""Validate the AfriRide global validation phase execution control contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_GLOBAL_VALIDATION_PHASE_EXECUTION_CONTROL.md"

REGIONS = ("Melbourne", "Bujumbura_Uvira", "Kinshasa")
SCENARIOS = ("G1", "G2", "G3")
SCENARIO_OBJECTIVES = {
    "G1": "global_replay_integrity",
    "G2": "global_identity_invariance",
    "G3": "global_event_completeness",
}
COVERED_SCENARIOS = (
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "C1",
    "C2",
    "C3",
    "D1",
    "D2",
    "E1",
    "E2",
    "E3",
    "F1",
    "F2",
    "F3",
)
REQUIRED_SEQUENCES = {
    "G1": (
        "aggregate_all_scenario_outputs",
        "run_replay_for_each_scenario",
        "compare_execution_hash_to_replay_hash",
        "compute_replay_success_rate",
    ),
    "G2": (
        "aggregate_all_identities",
        "validate_trip_id_integrity",
        "validate_driver_id_integrity",
        "validate_rider_id_integrity",
        "compare_execution_identity_to_replay_identity",
    ),
    "G3": (
        "aggregate_all_scenario_traces",
        "validate_expected_lifecycle_per_scenario",
        "compare_execution_event_set_to_replay_event_set",
        "compute_event_completeness",
    ),
}
HARD_STOPS = (
    "replay_mismatch",
    "identity_drift",
    "missing_event",
    "cross_region_inconsistency",
    "identity_collision",
    "incomplete_lifecycle",
    "replay_event_set_mismatch",
)
POST_VALIDATION_AUTHORIZED_STEPS = (
    "evidence_bundle_generation",
    "execution_receipt_creation",
    "pilot_certification",
    "go_no_go_decision",
)
FORBIDDEN_OPERATOR_ACTIONS = (
    "validate_regions_in_isolation_only",
    "ignore_cross_region_anomalies",
    "manually_reconcile_inconsistencies",
    "assume_prior_phases_guarantee_success",
    "accept_near_success",
    "reconstruct_missing_data",
)


class AfriRideGlobalValidationPhaseExecutionControlValidationError(RuntimeError):
    """Raised when global validation phase execution control is invalid."""


@dataclass(frozen=True)
class AfriRideGlobalValidationPhaseExecutionControlReport:
    schema: str
    status: str
    classification: str
    phase_ready_to_run: bool
    phase_passed_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.global_validation_phase_execution_control.v1"
            and self.status == "global_validation_phase_execution_control_contract"
            and self.classification == "system_wide_truth_validation_control"
            and self.phase_ready_to_run is True
            and self.phase_passed_claimed is False
        )


def validate_contract(
    path: Path = CONTRACT_DOC,
) -> AfriRideGlobalValidationPhaseExecutionControlReport:
    if not path.exists():
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            "global validation phase execution control contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: GLOBAL VALIDATION PHASE EXECUTION CONTROL CONTRACT")
    _require(text, "CLASSIFICATION: SYSTEM WIDE TRUTH VALIDATION CONTROL")
    _require(text, "G1 -> G2 -> G3")
    _require(text, "Truth MUST remain consistent across ALL regions for ALL scenarios")
    _require(text, "Global Validation Passed: NOT CLAIMED")
    _require(text, "all regions together form one consistent truth system")

    payload = _load_payload(text)
    _require_equal(payload["regions"], REGIONS, "regions")
    _require_equal(payload["scenarios"], SCENARIOS, "scenarios")
    if payload["scenario_objectives"] != SCENARIO_OBJECTIVES:
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            "scenario objectives mismatch"
        )
    _require_equal(payload["covered_scenarios"], COVERED_SCENARIOS, "covered scenarios")
    _validate_required_sequences(payload["required_sequences"])
    _require_equal(payload["hard_stops"], HARD_STOPS, "hard stops")
    _validate_completion_rule(payload["completion_rule"])
    _require_equal(
        payload["post_validation_authorized_steps"],
        POST_VALIDATION_AUTHORIZED_STEPS,
        "post-validation steps",
    )
    _require_equal(
        payload["forbidden_operator_actions"],
        FORBIDDEN_OPERATOR_ACTIONS,
        "forbidden operator actions",
    )
    if payload["operator_law"] != "all_regions_form_one_consistent_truth_system":
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            "operator law mismatch"
        )

    report = AfriRideGlobalValidationPhaseExecutionControlReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        phase_ready_to_run=payload["phase_ready_to_run"],
        phase_passed_claimed=payload["phase_passed_claimed"],
    )
    if not report.verified:
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            "global validation phase execution control report is not verified"
        )
    return report


def _validate_required_sequences(sequences: dict[str, list[str]]) -> None:
    for scenario, expected in REQUIRED_SEQUENCES.items():
        if sequences.get(scenario) != list(expected):
            raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
                f"required sequence mismatch: {scenario}"
            )


def _validate_completion_rule(rule: dict[str, Any]) -> None:
    expected = {
        "all_global_scenarios_pass": True,
        "replay_success_rate": "100%",
        "identity_drift": 0,
        "event_completeness": "100%",
        "no_cross_region_inconsistencies": True,
    }
    if rule != expected:
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            "completion rule mismatch"
        )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(global_validation_phase_execution_control:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            "missing global_validation_phase_execution_control yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("global_validation_phase_execution_control") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            "invalid global_validation_phase_execution_control yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideGlobalValidationPhaseExecutionControlValidationError(
            f"{label} mismatch"
        )


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideGlobalValidationPhaseExecutionControlValidationError as exc:
        print(f"GLOBAL VALIDATION PHASE EXECUTION CONTROL REJECTED: {exc}")
        return 1
    print("AfriRide global validation phase execution control validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"phase_ready_to_run={report.phase_ready_to_run}")
    print(f"phase_passed_claimed={report.phase_passed_claimed}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
