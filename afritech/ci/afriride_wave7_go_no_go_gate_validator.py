"""Validate the AfriRide Wave 7 Go/No-Go gate contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_WAVE7_GO_NO_GO_GATE.md"

NO_GO_CONDITIONS = (
    "replay_mismatch",
    "missing_scenario",
    "missing_evidence",
    "identity_inconsistency",
    "validator_failure",
    "non_field_observed_evidence",
)
NO_GO_ACTIONS = ("block_progression", "isolate_issue", "rerun_affected_scenarios")
PILOT_COMPLETION_REQUIREMENTS = (
    "execution_receipt_valid",
    "evidence_bundle_valid",
    "certification_generated",
    "go_gate_passed",
)


class AfriRideWave7GoNoGoGateValidationError(RuntimeError):
    """Raised when the Wave 7 Go/No-Go gate contract is invalid."""


@dataclass(frozen=True)
class AfriRideWave7GoNoGoGateReport:
    schema: str
    status: str
    classification: str
    controlled_pilot_ready_to_run: bool
    controlled_pilot_completion_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.wave7_go_no_go_gate.v1"
            and self.status == "wave7_go_no_go_gate_contract"
            and self.classification == "transition_gate"
            and self.controlled_pilot_ready_to_run is True
            and self.controlled_pilot_completion_claimed is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideWave7GoNoGoGateReport:
    if not path.exists():
        raise AfriRideWave7GoNoGoGateValidationError("Wave 7 Go/No-Go gate missing")

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: WAVE7 GO NO-GO GATE CONTRACT")
    _require(text, "CLASSIFICATION: TRANSITION GATE")
    _require(text, "prevents premature transition")
    _require(text, "Controlled Pilot Completion: NOT YET ACHIEVED")
    _require(text, "Pilot is COMPLETE IF")

    payload = _load_payload(text)
    conditions = payload["go_conditions"]
    expected_conditions = {
        "replay_success_rate": "100%",
        "identity_drift": 0,
        "event_integrity": "100%",
        "scenarios_executed": 16,
        "locations_covered": 3,
        "evidence_bundle_complete": True,
        "validators_passed": True,
        "execution_receipt_valid": True,
        "certification_generated": True,
        "evidence_origin": "field_observed",
    }
    if conditions != expected_conditions:
        raise AfriRideWave7GoNoGoGateValidationError("Go conditions mismatch")
    _require_equal(payload["no_go_conditions"], NO_GO_CONDITIONS, "No-Go conditions")
    _require_equal(payload["no_go_actions"], NO_GO_ACTIONS, "No-Go actions")
    _require_equal(
        payload["pilot_completion_requirements"],
        PILOT_COMPLETION_REQUIREMENTS,
        "pilot completion requirements",
    )

    report = AfriRideWave7GoNoGoGateReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        controlled_pilot_ready_to_run=payload["controlled_pilot_ready_to_run"],
        controlled_pilot_completion_claimed=payload[
            "controlled_pilot_completion_claimed"
        ],
    )
    if not report.verified:
        raise AfriRideWave7GoNoGoGateValidationError(
            "Wave 7 Go/No-Go gate report is not verified"
        )
    return report


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(wave7_go_no_go_gate:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRideWave7GoNoGoGateValidationError(
            "missing wave7_go_no_go_gate yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("wave7_go_no_go_gate") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideWave7GoNoGoGateValidationError(
            "invalid wave7_go_no_go_gate yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideWave7GoNoGoGateValidationError(f"missing phrase: {phrase}")


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideWave7GoNoGoGateValidationError(f"{label} mismatch")


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideWave7GoNoGoGateValidationError as exc:
        print(f"WAVE7 GO/NO-GO GATE REJECTED: {exc}")
        return 1
    print("AfriRide Wave 7 Go/No-Go gate validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"controlled_pilot_ready_to_run={report.controlled_pilot_ready_to_run}")
    print(f"controlled_pilot_completion_claimed={report.controlled_pilot_completion_claimed}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
