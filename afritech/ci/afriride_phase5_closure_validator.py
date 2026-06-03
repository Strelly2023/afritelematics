"""Validate AfriRide Phase 5 closure and Wave 6 handoff boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

from afritech.ci import (
    afriride_ga_elive_workflow_validator,
    afriride_phase5_readiness_certificate_validator,
)


ROOT = Path(__file__).resolve().parents[2]
PHASE5_DOC = ROOT / "docs/proof/AFRIRIDE_PHASE5_CLOSURE.md"
WAVE6_DOC = ROOT / "docs/proof/AFRIRIDE_WAVE6_CONTROLLED_PILOT_READINESS_CONTRACT.md"

EVIDENCE_CHAIN = (
    "implementation_evidence",
    "integration_evidence",
    "adversarial_rejection_evidence",
    "signed_ledger_validation",
    "identity_bound_signature_validation",
    "portable_receipt_export",
    "driver_proof_visibility",
    "rider_proof_visibility",
    "live_local_rider_driver_e2e",
    "ga_elive_workflow_contract",
    "phase5_readiness_certificate",
    "mandatory_ga_ci_enforcement",
)

WAVE6_EXIT_EVIDENCE = (
    "pilot_readiness_contract",
    "pilot_readiness_validator",
    "pilot_readiness_certificate",
    "field_run_evidence_receipts",
    "pilot_incident_ledger",
    "pilot_participant_onboarding_proof",
    "pilot_device_registration_proof",
    "pilot_completion_report",
)

TRANSFERRED_GAPS = (
    "real_pilot_participants",
    "real_devices_in_the_field",
    "network_instability_handling",
    "operational_support_procedures",
    "multi_day_pilot_execution",
    "external_audit_visibility",
    "pilot_incident_management",
    "production_deployment_evidence",
)


class AfriRidePhase5ClosureValidationError(RuntimeError):
    """Raised when closure or handoff claims become inadmissible."""


@dataclass(frozen=True)
class AfriRidePhase5ClosureReport:
    phase5_status: str
    phase5_classification: str
    wave6_status: str
    evidence_count: int
    transferred_gap_count: int
    truth_authority: str

    @property
    def verified(self) -> bool:
        return (
            self.phase5_status == "closed"
            and self.phase5_classification == "ga_plus_plus_plus_plus_phase5_readiness_certified"
            and self.wave6_status == "planned"
            and self.evidence_count == len(EVIDENCE_CHAIN)
            and self.transferred_gap_count == len(TRANSFERRED_GAPS)
            and self.truth_authority == "replay_only"
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "evidence_count": self.evidence_count,
            "phase5_classification": self.phase5_classification,
            "phase5_status": self.phase5_status,
            "schema": "afriride.phase5_closure_validation_report.v1",
            "transferred_gap_count": self.transferred_gap_count,
            "truth_authority": self.truth_authority,
            "verified": self.verified,
            "wave6_status": self.wave6_status,
        }


def validate() -> AfriRidePhase5ClosureReport:
    phase5 = _load_payload(PHASE5_DOC, "phase5_closure")
    wave6 = _load_payload(WAVE6_DOC, "wave6_controlled_pilot_readiness")

    _validate_phase5(phase5)
    _validate_wave6(wave6)

    if not afriride_ga_elive_workflow_validator.validate().verified:
        raise AfriRidePhase5ClosureValidationError("GA eLive gate is not verified")
    if not afriride_phase5_readiness_certificate_validator.validate().verified:
        raise AfriRidePhase5ClosureValidationError("Phase 5 certificate gate is not verified")

    report = AfriRidePhase5ClosureReport(
        evidence_count=len(phase5["evidence_chain"]),
        phase5_classification=phase5["classification"],
        phase5_status=phase5["status"],
        transferred_gap_count=len(phase5["remaining_gaps_transferred_to_wave6"]),
        truth_authority=phase5["truth_authority"],
        wave6_status=wave6["status"],
    )
    if not report.verified:
        raise AfriRidePhase5ClosureValidationError("Phase 5 closure report not verified")
    return report


def _validate_phase5(payload: dict[str, Any]) -> None:
    expected = {
        "schema": "afriride.phase5_closure.v1",
        "status": "closed",
        "phase_scope": "system_integration_and_evidence",
        "next_wave": "afriride_wave6_controlled_pilot_readiness",
        "truth_authority": "replay_only",
        "receipts": "derived_evidence",
        "replay": "truth_authority",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise AfriRidePhase5ClosureValidationError(f"Phase 5 {key} mismatch")
    for key in ("controlled_pilot_ready", "write_enabled", "mutation_authority"):
        if payload.get(key) is not False:
            raise AfriRidePhase5ClosureValidationError(f"Phase 5 {key} must be false")
    if tuple(payload.get("evidence_chain", ())) != EVIDENCE_CHAIN:
        raise AfriRidePhase5ClosureValidationError("Phase 5 evidence chain mismatch")
    if tuple(payload.get("remaining_gaps_transferred_to_wave6", ())) != TRANSFERRED_GAPS:
        raise AfriRidePhase5ClosureValidationError("Phase 5 transferred gaps mismatch")


def _validate_wave6(payload: dict[str, Any]) -> None:
    expected = {
        "schema": "afriride.wave6_controlled_pilot_readiness.v1",
        "status": "planned",
        "classification": "controlled_pilot_readiness_contract",
        "predecessor": "afriride.phase5_closure.v1",
        "authority": "readiness_contract_only",
        "truth_authority": "replay_only",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise AfriRidePhase5ClosureValidationError(f"Wave 6 {key} mismatch")
    for key in ("controlled_pilot_ready", "write_enabled", "mutation_authority"):
        if payload.get(key) is not False:
            raise AfriRidePhase5ClosureValidationError(f"Wave 6 {key} must be false")
    if tuple(payload.get("required_exit_evidence", ())) != WAVE6_EXIT_EVIDENCE:
        raise AfriRidePhase5ClosureValidationError("Wave 6 exit evidence mismatch")
    if tuple(payload.get("operational_surfaces_to_prove", ())) != TRANSFERRED_GAPS:
        raise AfriRidePhase5ClosureValidationError("Wave 6 operational surfaces mismatch")
    if "controlled_pilot_ready" not in tuple(payload.get("non_claims", ())):
        raise AfriRidePhase5ClosureValidationError("Wave 6 non-claims must include controlled_pilot_ready")


def _load_payload(path: Path, key: str) -> dict[str, Any]:
    if not path.exists():
        raise AfriRidePhase5ClosureValidationError(f"missing document: {path}")
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"```yaml\n({key}:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRidePhase5ClosureValidationError(f"missing yaml block: {key}")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict) or not isinstance(data.get(key), dict):
        raise AfriRidePhase5ClosureValidationError(f"invalid yaml block: {key}")
    return data[key]


def format_summary(report: AfriRidePhase5ClosureReport) -> str:
    return "\n".join(
        (
            "AfriRide Phase 5 closure validation PASSED",
            f"phase5_status={report.phase5_status}",
            f"phase5_classification={report.phase5_classification}",
            f"wave6_status={report.wave6_status}",
            f"evidence_count={report.evidence_count}",
            f"transferred_gap_count={report.transferred_gap_count}",
            f"truth_authority={report.truth_authority}",
            f"verified={report.verified}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriRidePhase5ClosureValidationError as exc:
        print(f"AfriRide Phase 5 closure validation FAILED: {exc}")
        return 1
    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
