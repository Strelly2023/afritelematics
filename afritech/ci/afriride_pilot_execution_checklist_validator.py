"""Validate the AfriRide pilot execution checklist contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_PILOT_EXECUTION_CHECKLIST.md"

PHASES = (
    "control_init",
    "pre_run_hard_gate",
    "execution_strict_order",
    "live_incident_logging",
    "evidence_generation",
    "replay_verification",
    "execution_receipt",
    "certification",
    "go_no_go_decision",
    "final_output",
)
CONTROL_INIT_CHECKS = (
    "wave6_execution_checkpoint_passed",
    "all_validators_pass",
    "no_active_system_errors",
    "pilot_session_declared",
    "system_state_locked",
)
FROZEN_CONFIGURATION = ("pricing", "driver_pool", "matching_parameters")
DISABLED_FEATURES = ("experimental_flags", "non_deterministic_features")
PRE_RUN_CHECKS = (
    "api_responding",
    "queue_active",
    "worker_pool_stable",
    "event_log_writable",
    "replay_engine_running",
    "proof_system_active",
    "riders_whitelisted",
    "drivers_whitelisted",
    "ids_verified_no_duplicates",
    "gps_working",
    "network_confirmed",
    "device_registered",
    "all_16_scenarios_loaded",
    "location_mapping_correct",
)
SCENARIO_ORDER = {
    "melbourne": ("A1", "A2", "A3", "A4", "A5"),
    "bujumbura_uvira": ("C1", "C2", "C3", "D1", "D2"),
    "kinshasa": ("E1", "E2", "E3", "F1", "F2", "F3"),
    "global": ("G1", "G2", "G3"),
}
IMMEDIATE_STOP_CONDITIONS = ("replay_mismatch", "identity_drift", "missing_event")
EVIDENCE_OUTPUTS = (
    "participant_registry.json",
    "device_registry.json",
    "scenario_receipts",
    "replay_receipts",
    "incident_logs",
    "summary",
    "manifest",
)
FINAL_DELIVERABLES = (
    "evidence_bundle",
    "execution_receipt",
    "certification_artifact",
    "go_no_go_decision",
)


class AfriRidePilotExecutionChecklistValidationError(RuntimeError):
    """Raised when the live pilot execution checklist is invalid."""


@dataclass(frozen=True)
class AfriRidePilotExecutionChecklistReport:
    schema: str
    status: str
    classification: str
    live_pilot_ready_to_run: bool
    pilot_executed_claimed: bool
    no_step_skipping_allowed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.pilot_execution_checklist.v1"
            and self.status == "pilot_execution_checklist_contract"
            and self.classification == "operator_live_checklist"
            and self.live_pilot_ready_to_run is True
            and self.pilot_executed_claimed is False
            and self.no_step_skipping_allowed is True
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRidePilotExecutionChecklistReport:
    if not path.exists():
        raise AfriRidePilotExecutionChecklistValidationError(
            "pilot execution checklist contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: PILOT EXECUTION CHECKLIST CONTRACT")
    _require(text, "CLASSIFICATION: OPERATOR LIVE CHECKLIST")
    _require(text, "Do NOT skip steps")
    _require(text, "ABORT BEFORE START")
    _require(text, "NO silent failures allowed")
    _require(text, "You are NOT validating success")
    _require(text, "You are validating truth")
    _require(text, "Pilot Executed: NOT CLAIMED")

    payload = _load_payload(text)
    _require_equal(payload["phases"], PHASES, "phases")
    _require_equal(payload["control_init_checks"], CONTROL_INIT_CHECKS, "control init checks")
    _require_equal(payload["frozen_configuration"], FROZEN_CONFIGURATION, "frozen config")
    _require_equal(payload["disabled_features"], DISABLED_FEATURES, "disabled features")
    _require_equal(payload["pre_run_checks"], PRE_RUN_CHECKS, "pre-run checks")
    _validate_scenario_order(payload["scenario_order"])
    _require_equal(payload["immediate_stop_conditions"], IMMEDIATE_STOP_CONDITIONS, "stop conditions")
    _require_equal(payload["evidence_outputs"], EVIDENCE_OUTPUTS, "evidence outputs")
    _require_equal(payload["final_deliverables"], FINAL_DELIVERABLES, "final deliverables")
    if payload["operator_law"] != "validate_truth_not_success":
        raise AfriRidePilotExecutionChecklistValidationError("operator law mismatch")

    report = AfriRidePilotExecutionChecklistReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        live_pilot_ready_to_run=payload["live_pilot_ready_to_run"],
        pilot_executed_claimed=payload["pilot_executed_claimed"],
        no_step_skipping_allowed=payload["no_step_skipping_allowed"],
    )
    if not report.verified:
        raise AfriRidePilotExecutionChecklistValidationError(
            "pilot execution checklist report is not verified"
        )
    return report


def _validate_scenario_order(order: dict[str, list[str]]) -> None:
    for location, scenarios in SCENARIO_ORDER.items():
        if order.get(location) != list(scenarios):
            raise AfriRidePilotExecutionChecklistValidationError(
                f"scenario order mismatch: {location}"
            )
    if sum(len(scenarios) for scenarios in order.values()) != 19:
        raise AfriRidePilotExecutionChecklistValidationError(
            "scenario order must contain 19 checks"
        )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(pilot_execution_checklist:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRidePilotExecutionChecklistValidationError(
            "missing pilot_execution_checklist yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("pilot_execution_checklist") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRidePilotExecutionChecklistValidationError(
            "invalid pilot_execution_checklist yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRidePilotExecutionChecklistValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRidePilotExecutionChecklistValidationError(f"{label} mismatch")


def main() -> int:
    try:
        report = validate_contract()
    except AfriRidePilotExecutionChecklistValidationError as exc:
        print(f"PILOT EXECUTION CHECKLIST REJECTED: {exc}")
        return 1
    print("AfriRide pilot execution checklist validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"live_pilot_ready_to_run={report.live_pilot_ready_to_run}")
    print(f"pilot_executed_claimed={report.pilot_executed_claimed}")
    print(f"no_step_skipping_allowed={report.no_step_skipping_allowed}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
