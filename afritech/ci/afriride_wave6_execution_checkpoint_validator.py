"""Validate the AfriRide Wave 6 execution checkpoint contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_WAVE6_EXECUTION_CHECKPOINT.md"

EXECUTION_FLOW = ("run_pilot", "evidence", "receipt", "certification", "go_no_go")
LOCATIONS = ("Melbourne", "Bujumbura_Uvira", "Kinshasa")
PHASES = {
    "melbourne": ("A1", "A2", "A3", "A4", "A5"),
    "bujumbura_uvira": ("C1", "C2", "C3", "D1", "D2"),
    "kinshasa": ("E1", "E2", "E3", "F1", "F2", "F3"),
    "global": ("G1", "G2", "G3"),
}
RUNTIME_HARD_STOPS = ("replay_mismatch", "identity_drift", "event_missing")
GENERATED_EVIDENCE_ARTIFACTS = (
    "participant_registry.json",
    "device_registry.json",
    "scenario_execution_receipts",
    "replay_verification_receipts",
    "incident_records",
    "pilot_completion_summary.json",
    "bundle_manifest.json",
)
REQUIRED_VALIDATORS = (
    "afriride_controlled_pilot_evidence_bundle_validator",
    "afriride_controlled_pilot_execution_receipt_validator",
    "afriride_controlled_pilot_certification_validator",
    "afriride_wave7_go_no_go_gate_validator",
)
NO_GO_CONDITIONS = (
    "replay_mismatch",
    "missing_scenario",
    "missing_evidence",
    "validator_failure",
    "identity_inconsistency",
)
NO_GO_ACTIONS = (
    "stop_progression",
    "isolate_failure",
    "fix_system",
    "rerun_affected_scenarios",
)
TRUTH_CHAIN = (
    "execution",
    "event",
    "replay",
    "evidence",
    "receipt",
    "certification",
    "decision",
)


class AfriRideWave6ExecutionCheckpointValidationError(RuntimeError):
    """Raised when the Wave 6 execution checkpoint contract is invalid."""


@dataclass(frozen=True)
class AfriRideWave6ExecutionCheckpointReport:
    schema: str
    status: str
    classification: str
    execution_ready_to_run: bool
    pilot_completion_claimed: bool
    production_readiness_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.wave6_execution_checkpoint.v1"
            and self.status == "wave6_execution_checkpoint_contract"
            and self.classification == "operator_grade_execution_sequence"
            and self.execution_ready_to_run is True
            and self.pilot_completion_claimed is False
            and self.production_readiness_claimed is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideWave6ExecutionCheckpointReport:
    if not path.exists():
        raise AfriRideWave6ExecutionCheckpointValidationError(
            "Wave 6 execution checkpoint contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: WAVE6 EXECUTION CHECKPOINT CONTRACT")
    _require(text, "CLASSIFICATION: OPERATOR-GRADE EXECUTION SEQUENCE")
    _require(text, "Run Pilot -> Evidence -> Receipt -> Certification -> GO / NO-GO")
    _require(text, "Receipt MUST NOT be manually created")
    _require(text, "Controlled Pilot Completion: NOT YET ACHIEVED")
    _require(text, "NOT production ready")

    payload = _load_payload(text)
    _require_equal(payload["execution_flow"], EXECUTION_FLOW, "execution flow")
    _require_equal(payload["locations"], LOCATIONS, "locations")
    _validate_phases(payload["phases"])
    _require_equal(payload["runtime_hard_stops"], RUNTIME_HARD_STOPS, "runtime hard stops")
    _require_equal(
        payload["generated_evidence_artifacts"],
        GENERATED_EVIDENCE_ARTIFACTS,
        "generated evidence artifacts",
    )
    _require_equal(payload["required_validators"], REQUIRED_VALIDATORS, "validators")
    _validate_go_conditions(payload["go_conditions"])
    _require_equal(payload["no_go_conditions"], NO_GO_CONDITIONS, "No-Go conditions")
    _require_equal(payload["no_go_actions"], NO_GO_ACTIONS, "No-Go actions")
    _require_equal(payload["truth_chain"], TRUTH_CHAIN, "truth chain")
    if payload["global_scale_claimed"] is not False:
        raise AfriRideWave6ExecutionCheckpointValidationError(
            "checkpoint claims global scale"
        )
    if payload["adversarial_completion_claimed"] is not False:
        raise AfriRideWave6ExecutionCheckpointValidationError(
            "checkpoint claims adversarial completion"
        )

    report = AfriRideWave6ExecutionCheckpointReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        execution_ready_to_run=payload["execution_ready_to_run"],
        pilot_completion_claimed=payload["pilot_completion_claimed"],
        production_readiness_claimed=payload["production_readiness_claimed"],
    )
    if not report.verified:
        raise AfriRideWave6ExecutionCheckpointValidationError(
            "Wave 6 execution checkpoint report is not verified"
        )
    return report


def _validate_phases(phases: dict[str, list[str]]) -> None:
    for phase, scenarios in PHASES.items():
        if phases.get(phase) != list(scenarios):
            raise AfriRideWave6ExecutionCheckpointValidationError(
                f"phase mismatch: {phase}"
            )
    total = sum(len(scenarios) for scenarios in phases.values())
    if total != 19:
        raise AfriRideWave6ExecutionCheckpointValidationError(
            "execution checkpoint must include 19 ordered scenario checks"
        )


def _validate_go_conditions(conditions: dict[str, Any]) -> None:
    expected = {
        "replay_success": "100%",
        "identity_drift": 0,
        "scenarios_executed": 16,
        "locations_covered": 3,
        "evidence_bundle_valid": True,
        "execution_receipt_valid": True,
        "certification_generated": True,
    }
    if conditions != expected:
        raise AfriRideWave6ExecutionCheckpointValidationError(
            "Go conditions mismatch"
        )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(wave6_execution_checkpoint:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRideWave6ExecutionCheckpointValidationError(
            "missing wave6_execution_checkpoint yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("wave6_execution_checkpoint") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideWave6ExecutionCheckpointValidationError(
            "invalid wave6_execution_checkpoint yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideWave6ExecutionCheckpointValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideWave6ExecutionCheckpointValidationError(f"{label} mismatch")


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideWave6ExecutionCheckpointValidationError as exc:
        print(f"WAVE6 EXECUTION CHECKPOINT REJECTED: {exc}")
        return 1
    print("AfriRide Wave 6 execution checkpoint validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"execution_ready_to_run={report.execution_ready_to_run}")
    print(f"pilot_completion_claimed={report.pilot_completion_claimed}")
    print(f"production_readiness_claimed={report.production_readiness_claimed}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
