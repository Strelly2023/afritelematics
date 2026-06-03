"""Validate the AfriRide controlled pilot evidence automation contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_EVIDENCE_AUTOMATION.md"

REQUIRED_PIPELINE = (
    "event_log",
    "execution_trace_extractor",
    "replay_engine",
    "proof_generator",
    "evidence_builder",
    "bundle_assembler",
    "bundle_validator",
    "admissible_evidence_bundle",
)
REQUIRED_COMPONENTS = (
    "trace_extractor",
    "scenario_mapper",
    "replay_validator_engine",
    "evidence_builder",
    "bundle_assembler",
    "bundle_validator_trigger",
)
GENERATED_ARTIFACTS = (
    "participant_registry.json",
    "device_registry.json",
    "scenario_execution_receipts",
    "incident_records",
    "replay_verification_receipts",
    "pilot_completion_summary.json",
    "bundle_manifest.json",
)


class AfriRideControlledPilotEvidenceAutomationValidationError(RuntimeError):
    """Raised when the evidence automation contract is invalid."""


@dataclass(frozen=True)
class AfriRideControlledPilotEvidenceAutomationReport:
    schema: str
    status: str
    classification: str
    scenarios_required: int
    manual_evidence_construction_allowed: bool
    replay_verification_required: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.controlled_pilot_evidence_automation.v1"
            and self.status == "controlled_pilot_evidence_automation_contract"
            and self.classification == "system_automation_layer"
            and self.scenarios_required == 16
            and self.manual_evidence_construction_allowed is False
            and self.replay_verification_required is True
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideControlledPilotEvidenceAutomationReport:
    if not path.exists():
        raise AfriRideControlledPilotEvidenceAutomationValidationError(
            "evidence automation contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: CONTROLLED PILOT EVIDENCE AUTOMATION CONTRACT")
    _require(text, "CLASSIFICATION: SYSTEM AUTOMATION LAYER")
    _require(text, "Evidence MUST be generated from system data")
    _require(text, "Evidence MUST NOT be manually constructed")
    _require(text, "skipping replay verification")

    payload = _load_payload(text)
    _require_equal(payload["required_pipeline"], REQUIRED_PIPELINE, "pipeline")
    _require_equal(payload["required_components"], REQUIRED_COMPONENTS, "components")
    _require_equal(payload["generated_artifacts"], GENERATED_ARTIFACTS, "generated artifacts")
    if payload["partial_bundle_creation_allowed"] is not False:
        raise AfriRideControlledPilotEvidenceAutomationValidationError(
            "partial bundle creation is allowed"
        )
    if payload["output_authority"] != "evidence_bundle_validator":
        raise AfriRideControlledPilotEvidenceAutomationValidationError(
            "automation output authority mismatch"
        )

    report = AfriRideControlledPilotEvidenceAutomationReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        scenarios_required=payload["scenarios_required"],
        manual_evidence_construction_allowed=payload[
            "manual_evidence_construction_allowed"
        ],
        replay_verification_required=payload["replay_verification_required"],
    )
    if not report.verified:
        raise AfriRideControlledPilotEvidenceAutomationValidationError(
            "evidence automation report is not verified"
        )
    return report


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(controlled_pilot_evidence_automation:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideControlledPilotEvidenceAutomationValidationError(
            "missing controlled_pilot_evidence_automation yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("controlled_pilot_evidence_automation") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideControlledPilotEvidenceAutomationValidationError(
            "invalid controlled_pilot_evidence_automation yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideControlledPilotEvidenceAutomationValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideControlledPilotEvidenceAutomationValidationError(
            f"{label} mismatch"
        )


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideControlledPilotEvidenceAutomationValidationError as exc:
        print(f"EVIDENCE AUTOMATION REJECTED: {exc}")
        return 1
    print("AfriRide controlled pilot evidence automation validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"scenarios_required={report.scenarios_required}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
