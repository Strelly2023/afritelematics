"""Validate the AfriRide controlled pilot runbook contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

from afritech.ci.afriride_controlled_pilot_scenario_matrix_validator import (
    GLOBAL_SCENARIOS,
    REQUIRED_SCENARIOS,
)


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_DOC = ROOT / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_RUNBOOK.md"

SCENARIO_ORDER = {
    "melbourne": ("A1", "A2", "A3", "A4", "A5"),
    "bujumbura_uvira": ("C1", "C2", "C3", "D1", "D2"),
    "kinshasa": ("E1", "E2", "E3", "F1", "F2", "F3"),
    "global_validation": ("G1", "G2", "G3"),
}

SYSTEM_READINESS = (
    "api_reachable",
    "queue_ingestion_active",
    "worker_pool_operational",
    "event_log_writable",
    "replay_engine_active",
    "proof_generator_active",
)

VALIDATORS = (
    "afriride_controlled_pilot_layer_validator",
    "afriride_controlled_pilot_scenario_matrix_validator",
    "constitutional_pipeline",
    "app_surface_validator",
)

PARTICIPANTS = (
    "riders_whitelisted",
    "drivers_whitelisted",
    "devices_tested",
    "identity_consistency_validated",
)

ENVIRONMENT = (
    "location_boundaries_configured",
    "time_window_set",
    "scenario_set_loaded",
)

INCIDENT_FIELDS = (
    "scenario_id",
    "location",
    "timestamp",
    "event_id",
    "failure_type",
    "description",
    "execution_hash",
    "replay_hash",
    "status",
)

MANDATORY_EVIDENCE = (
    "event_log_entries",
    "execution_trace",
    "replay_output",
    "proof_receipt",
    "ui_confirmation_optional",
)

ABORT_CONDITIONS = (
    "replay_mismatch_detected",
    "identity_drift_detected",
    "event_missing_in_lifecycle",
    "non_deterministic_output_observed",
    "validator_failure_during_run",
)

FINAL_PASS_CRITERIA = (
    "all_scenarios_pass_or_isolated_safely",
    "replay_success_100_percent",
    "identity_drift_zero",
    "no_invariant_violations",
)

INVALIDATION_CONDITIONS = (
    "replay_mismatch",
    "identity_mutation",
    "hidden_execution_path",
    "missing_event_transition",
)

OPERATOR_RULES = (
    "follow_execution_order_strictly",
    "do_not_skip_scenarios",
    "do_not_modify_system_behavior",
    "do_not_override_outcomes",
)

FORBIDDEN_CLAIMS = (
    "production launch ready",
    "pilot completion achieved",
    "execution evidence complete",
)


class AfriRideControlledPilotRunbookValidationError(RuntimeError):
    """Raised when the controlled pilot runbook is not admissible."""


@dataclass(frozen=True)
class AfriRideControlledPilotRunbookReport:
    schema: str
    status: str
    classification: str
    artifact_type: str
    scenario_count: int
    production_launch_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.controlled_pilot_runbook.v1"
            and self.status == "controlled_pilot_runbook_contract"
            and self.classification == "executable_pilot_contract"
            and self.artifact_type == "execution_contract"
            and self.scenario_count == 19
            and self.production_launch_claimed is False
        )


def validate(path: Path = RUNBOOK_DOC) -> AfriRideControlledPilotRunbookReport:
    if not path.exists():
        raise AfriRideControlledPilotRunbookValidationError(
            "controlled pilot runbook missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: CONTROLLED PILOT RUNBOOK CONTRACT")
    _require(text, "CLASSIFICATION: EXECUTABLE PILOT CONTRACT")
    _require(text, "ABORT RUN (hard stop)")
    _require(text, "NO incident = no admissibility")
    _require(text, "Execution Hash == Replay Hash")
    _require(text, "Event -> Execution -> Replay -> Proof")

    lowered = text.lower()
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in lowered:
            raise AfriRideControlledPilotRunbookValidationError(
                f"forbidden claim: {phrase}"
            )

    payload = _load_runbook_payload(text)

    if payload["production_launch_claimed"] is not False:
        raise AfriRideControlledPilotRunbookValidationError(
            "runbook claims production launch"
        )
    if payload["simulation_only_claimed"] is not False:
        raise AfriRideControlledPilotRunbookValidationError(
            "runbook collapses controlled execution into simulation"
        )
    if payload["pipeline"] != "constitutional":
        raise AfriRideControlledPilotRunbookValidationError(
            "runbook must require constitutional pipeline"
        )

    scenario_count = _validate_scenario_order(payload["scenario_order"])
    checklist = payload["pre_run_checklist"]
    _require_equal(checklist["system_readiness"], SYSTEM_READINESS, "system readiness")
    _require_equal(checklist["validators"], VALIDATORS, "validator checklist")
    _require_equal(checklist["participants"], PARTICIPANTS, "participant checklist")
    _require_equal(checklist["environment"], ENVIRONMENT, "environment checklist")
    _require_equal(payload["incident_required_fields"], INCIDENT_FIELDS, "incident fields")
    _require_equal(payload["incident_status_values"], ("PASS", "FAIL", "ISOLATED"), "incident statuses")
    _require_equal(payload["mandatory_evidence"], MANDATORY_EVIDENCE, "mandatory evidence")
    if payload["evidence_storage_path"] != "/storage/pilot_runs/{location}/{scenario_id}/":
        raise AfriRideControlledPilotRunbookValidationError(
            "evidence storage path mismatch"
        )
    _require_equal(payload["evidence_properties"], ("immutable", "timestamped", "hash_bound"), "evidence properties")
    _require_equal(
        payload["replay_verification_steps"],
        ("extract_execution_trace", "run_replay_engine", "compare_outputs", "store_result"),
        "replay verification steps",
    )
    _require_equal(payload["abort_conditions"], ABORT_CONDITIONS, "abort conditions")
    _require_equal(
        payload["abort_actions"],
        ("stop_entire_pilot", "isolate_failing_scenario", "record_incident"),
        "abort actions",
    )
    _require_equal(
        payload["post_run_report_fields"],
        (
            "location",
            "scenarios_executed",
            "pass_count",
            "fail_count",
            "isolated_events",
            "replay_success_rate",
            "identity_integrity",
            "event_integrity",
            "final_status",
        ),
        "post-run report fields",
    )
    _require_equal(
        payload["required_attachments"],
        ("incident_logs", "replay_reports", "proof_receipts"),
        "required attachments",
    )
    _require_equal(payload["final_pass_criteria"], FINAL_PASS_CRITERIA, "pass criteria")
    _require_equal(
        payload["invalidation_conditions"],
        INVALIDATION_CONDITIONS,
        "invalidation conditions",
    )
    _require_equal(payload["operator_rules"], OPERATOR_RULES, "operator rules")

    report = AfriRideControlledPilotRunbookReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        artifact_type=payload["artifact_type"],
        scenario_count=scenario_count,
        production_launch_claimed=payload["production_launch_claimed"],
    )
    if not report.verified:
        raise AfriRideControlledPilotRunbookValidationError(
            "controlled pilot runbook report is not verified"
        )
    return report


def _validate_scenario_order(order: dict[str, list[str]]) -> int:
    if tuple(order.keys()) != tuple(SCENARIO_ORDER.keys()):
        raise AfriRideControlledPilotRunbookValidationError(
            "scenario order phase mismatch"
        )
    for phase, expected in SCENARIO_ORDER.items():
        if order[phase] != list(expected):
            raise AfriRideControlledPilotRunbookValidationError(
                f"scenario order mismatch: {phase}"
            )

    matrix_prefixes = {
        location: tuple(item.split("_", maxsplit=1)[0] for item in scenarios)
        for location, scenarios in REQUIRED_SCENARIOS.items()
    }
    matrix_prefixes["global_validation"] = tuple(
        item.split("_", maxsplit=1)[0] for item in GLOBAL_SCENARIOS
    )
    for phase, expected in matrix_prefixes.items():
        if tuple(order[phase]) != expected:
            raise AfriRideControlledPilotRunbookValidationError(
                f"runbook does not match scenario matrix: {phase}"
            )

    return sum(len(items) for items in order.values())


def _load_runbook_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(controlled_pilot_runbook:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRideControlledPilotRunbookValidationError(
            "missing controlled_pilot_runbook yaml block"
        )
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict) or not isinstance(
        data.get("controlled_pilot_runbook"), dict
    ):
        raise AfriRideControlledPilotRunbookValidationError(
            "invalid controlled_pilot_runbook yaml block"
        )
    return data["controlled_pilot_runbook"]


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideControlledPilotRunbookValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideControlledPilotRunbookValidationError(f"{label} mismatch")


def format_summary(report: AfriRideControlledPilotRunbookReport) -> str:
    return "\n".join(
        (
            "AfriRide controlled pilot runbook validation PASSED",
            f"schema={report.schema}",
            f"status={report.status}",
            f"classification={report.classification}",
            f"artifact_type={report.artifact_type}",
            f"scenarios={report.scenario_count}",
            f"production_launch_claimed={report.production_launch_claimed}",
            f"verified={report.verified}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriRideControlledPilotRunbookValidationError as exc:
        print(f"AfriRide controlled pilot runbook validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
