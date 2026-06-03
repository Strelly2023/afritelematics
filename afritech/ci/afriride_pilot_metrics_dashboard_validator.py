"""Validate the AfriRide pilot metrics dashboard contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_PILOT_METRICS_DASHBOARD.md"

REQUIRED_ARCHITECTURE = (
    "event_log",
    "replay_engine",
    "proof_layer",
    "live_dashboard",
    "ci_dashboard",
    "go_no_go",
)
LIVE_SECTIONS = (
    "trip_lifecycle_panel",
    "scenario_execution_tracker",
    "location_panels",
    "event_pipeline_health",
    "real_time_failure_feed",
    "actor_panels",
)
CI_PANELS = (
    "constitutional_status_panel",
    "replay_integrity_panel",
    "identity_integrity_panel",
    "deterministic_execution_panel",
    "evidence_bundle_status",
    "execution_receipt_status",
    "go_no_go_panel",
    "validator_pipeline_status",
)
CRITICAL_ALERTS = (
    "replay_mismatch",
    "identity_drift",
    "determinism_violation",
)
PRIMARY_INPUTS = (
    "event_log",
    "replay_engine",
    "proof_layer",
    "ci_validators",
    "evidence_bundle",
    "execution_receipt",
)
FORBIDDEN_DASHBOARD_ACTIONS = (
    "alter_execution",
    "modify_events",
    "override_replay_results",
    "influence_ci_decisions",
)
EXECUTION_CHECKPOINT_FLOW = (
    "run_pilot",
    "event_log_generated",
    "evidence_ingestion",
    "evidence_bundle",
    "bundle_validation",
    "execution_receipt",
    "receipt_validation",
    "certification",
    "go_no_go_decision",
)


class AfriRidePilotMetricsDashboardValidationError(RuntimeError):
    """Raised when the pilot metrics dashboard contract is invalid."""


@dataclass(frozen=True)
class AfriRidePilotMetricsDashboardReport:
    schema: str
    status: str
    classification: str
    live_defines_truth: bool
    ci_defines_admissibility: bool
    replay_defines_truth: bool
    pilot_completion_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.pilot_metrics_dashboard.v1"
            and self.status == "pilot_metrics_dashboard_contract"
            and self.classification == "live_ci_admissibility_surface"
            and self.live_defines_truth is False
            and self.ci_defines_admissibility is True
            and self.replay_defines_truth is True
            and self.pilot_completion_claimed is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRidePilotMetricsDashboardReport:
    if not path.exists():
        raise AfriRidePilotMetricsDashboardValidationError(
            "pilot metrics dashboard contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: PILOT METRICS DASHBOARD CONTRACT")
    _require(text, "CLASSIFICATION: LIVE + CI ADMISSIBILITY SURFACE")
    _require(text, "LIVE DASHBOARD -> Operational Reality")
    _require(text, "CI DASHBOARD   -> Constitutional Truth")
    _require(text, "Live dashboard may show success")
    _require(text, "CI dashboard decides if it is real success")
    _require(text, "Replay defines truth")
    _require(text, "CI defines admissibility")
    _require(text, "Pilot Completion: NOT YET ACHIEVED")

    payload = _load_payload(text)
    _require_equal(payload["required_architecture"], REQUIRED_ARCHITECTURE, "architecture")
    _require_equal(payload["live_sections"], LIVE_SECTIONS, "live sections")
    _require_equal(payload["ci_panels"], CI_PANELS, "CI panels")
    _require_equal(payload["critical_alerts"], CRITICAL_ALERTS, "critical alerts")
    _require_equal(payload["primary_inputs"], PRIMARY_INPUTS, "primary inputs")
    _require_equal(
        payload["forbidden_dashboard_actions"],
        FORBIDDEN_DASHBOARD_ACTIONS,
        "forbidden dashboard actions",
    )
    _require_equal(
        payload["execution_checkpoint_flow"],
        EXECUTION_CHECKPOINT_FLOW,
        "execution checkpoint flow",
    )
    _validate_metrics(payload)

    report = AfriRidePilotMetricsDashboardReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        live_defines_truth=payload["live_defines_truth"],
        ci_defines_admissibility=payload["ci_defines_admissibility"],
        replay_defines_truth=payload["replay_defines_truth"],
        pilot_completion_claimed=payload["pilot_completion_claimed"],
    )
    if not report.verified:
        raise AfriRidePilotMetricsDashboardValidationError(
            "pilot metrics dashboard report is not verified"
        )
    return report


def _validate_metrics(payload: dict[str, Any]) -> None:
    if payload["tier1_metrics"] != {
        "replay_success_rate": "100%",
        "identity_drift": 0,
        "execution_divergence": 0,
        "event_corruption": 0,
    }:
        raise AfriRidePilotMetricsDashboardValidationError(
            "Tier 1 metrics mismatch"
        )
    if payload["tier2_metrics"] != {
        "trip_completion_rate_minimum": "95%",
        "driver_acceptance_rate_minimum": "70%",
        "matching_latency_stable": True,
    }:
        raise AfriRidePilotMetricsDashboardValidationError(
            "Tier 2 metrics mismatch"
        )
    if payload["critical_alert_action"] != "hard_stop_pilot":
        raise AfriRidePilotMetricsDashboardValidationError(
            "critical alert action must hard stop pilot"
        )
    if payload["pilot_execution_ready_to_run"] is not True:
        raise AfriRidePilotMetricsDashboardValidationError(
            "pilot execution is not marked ready to run"
        )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(pilot_metrics_dashboard:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRidePilotMetricsDashboardValidationError(
            "missing pilot_metrics_dashboard yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("pilot_metrics_dashboard") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRidePilotMetricsDashboardValidationError(
            "invalid pilot_metrics_dashboard yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRidePilotMetricsDashboardValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRidePilotMetricsDashboardValidationError(f"{label} mismatch")


def main() -> int:
    try:
        report = validate_contract()
    except AfriRidePilotMetricsDashboardValidationError as exc:
        print(f"PILOT METRICS DASHBOARD REJECTED: {exc}")
        return 1
    print("AfriRide pilot metrics dashboard validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"live_defines_truth={report.live_defines_truth}")
    print(f"ci_defines_admissibility={report.ci_defines_admissibility}")
    print(f"replay_defines_truth={report.replay_defines_truth}")
    print(f"pilot_completion_claimed={report.pilot_completion_claimed}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
