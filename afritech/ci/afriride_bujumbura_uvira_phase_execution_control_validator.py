"""Validate the AfriRide Bujumbura/Uvira phase execution control contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_BUJUMBURA_UVIRA_PHASE_EXECUTION_CONTROL.md"

SCENARIOS = ("C1", "C2", "C3", "D1", "D2")
SCENARIO_OBJECTIVES = {
    "C1": "cross_border_identity_continuity",
    "C2": "buffered_event_integrity_under_offline",
    "C3": "logical_ordering_over_arrival_time",
    "D1": "gps_anomaly_preservation",
    "D2": "conflicting_claims_preserved_neutrally",
}
REQUIRED_SEQUENCES = {
    "C1": ("request", "match", "accept", "start", "cross_border_location_events", "end"),
    "C2": ("request", "match", "start", "offline_buffered_events", "reconnect_flush_events", "end"),
    "C3": ("event_1_arrives", "event_3_arrives", "event_2_arrives_late", "logical_order_reconstructed"),
    "D1": ("normal_gps_event", "gps_anomaly_event", "anomaly_preserved", "end"),
    "D2": ("end", "rider_paid_claim", "driver_unpaid_claim", "dispute_recorded"),
}
HARD_STOPS = (
    "event_loss",
    "replay_mismatch",
    "identity_drift",
    "event_ordering_break",
    "state_depends_on_network_timing",
    "trip_split",
    "duplicate_events",
    "silent_gps_correction",
    "claim_overwrite",
    "silent_dispute_resolution",
)
EVIDENCE_REQUIRED = (
    "request_event",
    "match_event",
    "accept_event",
    "start_event",
    "cross_border_location_events",
    "buffered_events",
    "flush_events",
    "ingestion_timestamps",
    "logical_timestamps",
    "original_gps_events",
    "anomalous_jumps",
    "rider_payment_claim_event",
    "driver_payment_claim_event",
    "end_event",
    "execution_hash",
    "replay_hash",
)
FORBIDDEN_OPERATOR_ACTIONS = (
    "fix_missing_data_manually",
    "replay_data_manually",
    "stabilize_network_artificially",
    "ignore_late_events",
    "smooth_gps_manually",
    "resolve_disputes_manually",
)


class AfriRideBujumburaUviraPhaseExecutionControlValidationError(RuntimeError):
    """Raised when Bujumbura/Uvira phase execution control is invalid."""


@dataclass(frozen=True)
class AfriRideBujumburaUviraPhaseExecutionControlReport:
    schema: str
    status: str
    classification: str
    location: str
    phase_ready_to_run: bool
    phase_passed_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.bujumbura_uvira_phase_execution_control.v1"
            and self.status == "bujumbura_uvira_phase_execution_control_contract"
            and self.classification == "infrastructure_stress_execution_control"
            and self.location == "Bujumbura_Uvira"
            and self.phase_ready_to_run is True
            and self.phase_passed_claimed is False
        )


def validate_contract(
    path: Path = CONTRACT_DOC,
) -> AfriRideBujumburaUviraPhaseExecutionControlReport:
    if not path.exists():
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
            "Bujumbura/Uvira phase execution control contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: BUJUMBURA UVIRA PHASE EXECUTION CONTROL CONTRACT")
    _require(text, "CLASSIFICATION: INFRASTRUCTURE STRESS EXECUTION CONTROL")
    _require(text, "C1 -> C2 -> C3 -> D1 -> D2")
    _require(text, "Network conditions MAY vary")
    _require(text, "Execution outcome MUST NOT vary")
    _require(text, "Bujumbura/Uvira Phase Passed: NOT CLAIMED")

    payload = _load_payload(text)
    _require_equal(payload["scenarios"], SCENARIOS, "scenarios")
    if payload["scenario_objectives"] != SCENARIO_OBJECTIVES:
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
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
    if payload["operator_law"] != "system_immunity_to_infrastructure_failure":
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
            "operator law mismatch"
        )

    report = AfriRideBujumburaUviraPhaseExecutionControlReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        location=payload["location"],
        phase_ready_to_run=payload["phase_ready_to_run"],
        phase_passed_claimed=payload["phase_passed_claimed"],
    )
    if not report.verified:
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
            "Bujumbura/Uvira phase execution control report is not verified"
        )
    return report


def _validate_required_sequences(sequences: dict[str, list[str]]) -> None:
    for scenario, expected in REQUIRED_SEQUENCES.items():
        if sequences.get(scenario) != list(expected):
            raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
                f"required sequence mismatch: {scenario}"
            )


def _validate_completion_rule(rule: dict[str, Any]) -> None:
    expected = {
        "all_scenarios_pass": True,
        "replay_correctness": "100%",
        "event_integrity": "100%",
        "identity_drift": 0,
        "ordering_preserved": True,
    }
    if rule != expected:
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
            "completion rule mismatch"
        )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(bujumbura_uvira_phase_execution_control:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
            "missing bujumbura_uvira_phase_execution_control yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("bujumbura_uvira_phase_execution_control") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
            "invalid bujumbura_uvira_phase_execution_control yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideBujumburaUviraPhaseExecutionControlValidationError(
            f"{label} mismatch"
        )


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideBujumburaUviraPhaseExecutionControlValidationError as exc:
        print(f"BUJUMBURA UVIRA PHASE EXECUTION CONTROL REJECTED: {exc}")
        return 1
    print("AfriRide Bujumbura/Uvira phase execution control validation PASSED")
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
