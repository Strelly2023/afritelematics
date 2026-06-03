"""Validate the AfriRide controlled pilot execution receipt contract and artifact."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from afritech.ci.afriride_controlled_pilot_evidence_bundle_validator import (
    EVIDENCE_ORIGINS,
    REQUIRED_LOCATIONS,
    compute_bundle_hash,
    validate_bundle,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_EXECUTION_RECEIPT.md"

REQUIRED_TOP_LEVEL_FIELDS = (
    "receipt_id",
    "generated_at",
    "evidence_origin",
    "pilot_scope",
    "evidence_bundle",
    "execution_summary",
    "replay_verification",
    "integrity_checks",
    "incident_accountability",
    "final_status",
    "constraints_acknowledged",
)
PILOT_SCOPE_FIELDS = ("locations", "total_scenarios")
EVIDENCE_BUNDLE_FIELDS = ("bundle_id", "bundle_hash", "manifest_hash", "verified")
EXECUTION_SUMMARY_FIELDS = (
    "scenarios_executed",
    "pass_count",
    "fail_count",
    "isolated_count",
)
REPLAY_VERIFICATION_FIELDS = ("replay_success_rate", "all_hashes_match")
INTEGRITY_CHECK_FIELDS = (
    "identity_integrity",
    "event_integrity",
    "participant_registry_valid",
    "device_registry_valid",
)
INCIDENT_ACCOUNTABILITY_FIELDS = ("total_incidents", "all_recorded")
CONSTRAINT_FIELDS = ("not_production_ready", "not_scalable", "not_market_ready")
INVALIDATION_CONDITIONS = (
    "missing_or_mismatched_bundle_hash",
    "replay_success_less_than_100",
    "scenario_count_less_than_16",
    "location_missing",
    "integrity_flag_false",
    "incident_missing",
    "constraint_flags_missing",
)
RECEIPT_LAW = (
    "evidence_bundle_complete",
    "replay_verification_passes",
    "integrity_constraints_hold",
    "no_prohibited_claims_introduced",
)
FORBIDDEN_CLAIMS = (
    "production readiness achieved",
    "scale proven",
    "commercial viability proven",
    "market readiness achieved",
)


class AfriRideControlledPilotExecutionReceiptValidationError(RuntimeError):
    """Raised when the controlled pilot execution receipt is inadmissible."""


@dataclass(frozen=True)
class AfriRideControlledPilotExecutionReceiptContractReport:
    schema: str
    status: str
    classification: str
    artifact_type: str
    total_scenarios: int
    truth_authority: str
    introduces_new_truth: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.controlled_pilot_execution_receipt.v1"
            and self.status == "controlled_pilot_execution_receipt_contract"
            and self.classification == "proof_anchor"
            and self.artifact_type == "proof_anchor"
            and self.total_scenarios == 16
            and self.truth_authority == "evidence_bundle_and_replay_receipts"
            and self.introduces_new_truth is False
        )


@dataclass(frozen=True)
class AfriRideControlledPilotExecutionReceiptReport:
    receipt_id: str
    bundle_id: str
    bundle_hash: str
    scenarios_executed: int
    replay_success_rate: str
    total_incidents: int
    final_status: str

    @property
    def verified(self) -> bool:
        return (
            bool(self.receipt_id)
            and bool(self.bundle_id)
            and bool(self.bundle_hash)
            and self.scenarios_executed == 16
            and self.replay_success_rate == "100%"
            and self.final_status == "ADMISSIBLE"
        )


def validate_contract(
    path: Path = CONTRACT_DOC,
) -> AfriRideControlledPilotExecutionReceiptContractReport:
    if not path.exists():
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: CONTROLLED PILOT EXECUTION RECEIPT CONTRACT")
    _require(text, "CLASSIFICATION: PROOF ANCHOR")
    _require(text, "Pilot execution is NOT admissible")
    _require(text, "Execution Receipt = Proof Compression Layer")
    _require(text, "receipt.evidence_bundle.bundle_hash == evidence_bundle.manifest.hash")
    _require(text, "An Execution Receipt is admissible IF AND ONLY IF")

    lowered = text.lower()
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in lowered:
            raise AfriRideControlledPilotExecutionReceiptValidationError(
                f"forbidden claim: {phrase}"
            )

    payload = _load_contract_payload(text)
    _require_equal(payload["required_locations"], REQUIRED_LOCATIONS, "required locations")
    _require_equal(payload["required_top_level_fields"], REQUIRED_TOP_LEVEL_FIELDS, "top-level fields")
    _require_equal(payload["pilot_scope_fields"], PILOT_SCOPE_FIELDS, "pilot scope fields")
    _require_equal(payload["evidence_bundle_fields"], EVIDENCE_BUNDLE_FIELDS, "bundle fields")
    _require_equal(payload["execution_summary_fields"], EXECUTION_SUMMARY_FIELDS, "summary fields")
    _require_equal(payload["replay_verification_fields"], REPLAY_VERIFICATION_FIELDS, "replay fields")
    _require_equal(payload["integrity_check_fields"], INTEGRITY_CHECK_FIELDS, "integrity fields")
    _require_equal(payload["incident_accountability_fields"], INCIDENT_ACCOUNTABILITY_FIELDS, "incident fields")
    _require_equal(payload["constraint_fields"], CONSTRAINT_FIELDS, "constraint fields")
    _require_equal(payload["invalidation_conditions"], INVALIDATION_CONDITIONS, "invalidation conditions")
    _require_equal(payload["receipt_law"], RECEIPT_LAW, "receipt law")

    if payload["generated_only_after_real_pilot_execution"] is not True:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt contract is not bound to real pilot execution"
        )
    if payload["introduces_new_truth"] is not False:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt contract introduces new truth"
        )
    for claim_key in (
        "production_readiness_claimed",
        "scalability_claimed",
        "market_readiness_claimed",
    ):
        if payload[claim_key] is not False:
            raise AfriRideControlledPilotExecutionReceiptValidationError(
                f"execution receipt contract claims {claim_key}"
            )

    report = AfriRideControlledPilotExecutionReceiptContractReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        artifact_type=payload["artifact_type"],
        total_scenarios=payload["total_scenarios"],
        truth_authority=payload["truth_authority"],
        introduces_new_truth=payload["introduces_new_truth"],
    )
    if not report.verified:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt contract report is not verified"
        )
    return report


def validate_receipt(
    receipt_path: Path,
    bundle_root: Path,
) -> AfriRideControlledPilotExecutionReceiptReport:
    if not receipt_path.is_file():
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt missing"
        )

    bundle_report = validate_bundle(bundle_root)
    receipt = _load_json(receipt_path)
    manifest = _load_json(bundle_root / "bundle_manifest.json")
    summary = _load_json(bundle_root / "pilot_completion_summary.json")
    computed_hash = compute_bundle_hash(bundle_root)

    _require_fields(receipt, REQUIRED_TOP_LEVEL_FIELDS, "execution receipt")
    _validate_evidence_origin(receipt, manifest)
    _validate_pilot_scope(receipt["pilot_scope"])
    _validate_evidence_bundle(receipt["evidence_bundle"], manifest, bundle_report, computed_hash)
    _validate_execution_summary(receipt["execution_summary"], summary)
    _validate_replay_verification(receipt["replay_verification"])
    _validate_integrity_checks(receipt["integrity_checks"], summary)
    _validate_incident_accountability(
        receipt["incident_accountability"],
        manifest["incident_count"],
    )
    _validate_constraints(receipt["constraints_acknowledged"])

    if receipt["final_status"] != "ADMISSIBLE":
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt final status is not admissible"
        )

    report = AfriRideControlledPilotExecutionReceiptReport(
        receipt_id=receipt["receipt_id"],
        bundle_id=receipt["evidence_bundle"]["bundle_id"],
        bundle_hash=receipt["evidence_bundle"]["bundle_hash"],
        scenarios_executed=receipt["execution_summary"]["scenarios_executed"],
        replay_success_rate=receipt["replay_verification"]["replay_success_rate"],
        total_incidents=receipt["incident_accountability"]["total_incidents"],
        final_status=receipt["final_status"],
    )
    if not report.verified:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt report is not verified"
        )
    return report


def _validate_pilot_scope(scope: dict[str, Any]) -> None:
    _require_fields(scope, PILOT_SCOPE_FIELDS, "pilot scope")
    if scope["locations"] != list(REQUIRED_LOCATIONS):
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt location coverage mismatch"
        )
    if scope["total_scenarios"] != 16:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt scenario count less than 16"
        )


def _validate_evidence_origin(receipt: dict[str, Any], manifest: dict[str, Any]) -> None:
    if receipt["evidence_origin"] not in EVIDENCE_ORIGINS:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "invalid evidence origin"
        )
    if receipt["evidence_origin"] != manifest["evidence_origin"]:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "receipt evidence origin mismatch"
        )


def _validate_evidence_bundle(
    payload: dict[str, Any],
    manifest: dict[str, Any],
    bundle_report: object,
    computed_hash: str,
) -> None:
    _require_fields(payload, EVIDENCE_BUNDLE_FIELDS, "evidence bundle")
    if payload["verified"] is not True:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt evidence bundle is not verified"
        )
    if payload["bundle_id"] != manifest["bundle_id"]:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt bundle identity mismatch"
        )
    if manifest["hash"] != computed_hash:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "evidence bundle manifest hash invalid"
        )
    if payload["bundle_hash"] != manifest["hash"] or payload["manifest_hash"] != manifest["hash"]:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "missing or mismatched bundle hash"
        )
    if not getattr(bundle_report, "verified", False):
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "evidence bundle report is not verified"
        )


def _validate_execution_summary(payload: dict[str, Any], summary: dict[str, Any]) -> None:
    _require_fields(payload, EXECUTION_SUMMARY_FIELDS, "execution summary")
    for field in EXECUTION_SUMMARY_FIELDS:
        if payload[field] != summary[field]:
            raise AfriRideControlledPilotExecutionReceiptValidationError(
                f"execution receipt summary mismatch: {field}"
            )
    if payload["scenarios_executed"] != 16:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "execution receipt scenario count less than 16"
        )


def _validate_replay_verification(payload: dict[str, Any]) -> None:
    _require_fields(payload, REPLAY_VERIFICATION_FIELDS, "replay verification")
    if payload["replay_success_rate"] != "100%" or payload["all_hashes_match"] is not True:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "replay success less than 100%"
        )


def _validate_integrity_checks(payload: dict[str, Any], summary: dict[str, Any]) -> None:
    _require_fields(payload, INTEGRITY_CHECK_FIELDS, "integrity checks")
    if payload["identity_integrity"] != summary["identity_integrity"]:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "identity integrity does not match evidence bundle"
        )
    if payload["event_integrity"] != summary["event_integrity"]:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "event integrity does not match evidence bundle"
        )
    for field in INTEGRITY_CHECK_FIELDS:
        if payload[field] is not True:
            raise AfriRideControlledPilotExecutionReceiptValidationError(
                f"integrity flag false: {field}"
            )


def _validate_incident_accountability(payload: dict[str, Any], incident_count: int) -> None:
    _require_fields(payload, INCIDENT_ACCOUNTABILITY_FIELDS, "incident accountability")
    if payload["total_incidents"] != incident_count:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "incident accountability count mismatch"
        )
    if incident_count > 0 and payload["all_recorded"] is not True:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "incident missing"
        )
    if payload["all_recorded"] is not True:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "incident accountability not recorded"
        )


def _validate_constraints(payload: dict[str, Any]) -> None:
    _require_fields(payload, CONSTRAINT_FIELDS, "constraints")
    for field in CONSTRAINT_FIELDS:
        if payload[field] is not True:
            raise AfriRideControlledPilotExecutionReceiptValidationError(
                f"constraint flags missing: {field}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            f"invalid JSON: {path}"
        ) from exc
    if not isinstance(data, dict):
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            f"JSON must be object: {path}"
        )
    return data


def _require_fields(payload: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if field not in payload:
            raise AfriRideControlledPilotExecutionReceiptValidationError(
                f"missing {label} field: {field}"
            )


def _load_contract_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(controlled_pilot_execution_receipt:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "missing controlled_pilot_execution_receipt yaml block"
        )
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict) or not isinstance(
        data.get("controlled_pilot_execution_receipt"), dict
    ):
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            "invalid controlled_pilot_execution_receipt yaml block"
        )
    return data["controlled_pilot_execution_receipt"]


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideControlledPilotExecutionReceiptValidationError(
            f"{label} mismatch"
        )


def format_contract_summary(
    report: AfriRideControlledPilotExecutionReceiptContractReport,
) -> str:
    return "\n".join(
        (
            "AfriRide controlled pilot execution receipt contract validation PASSED",
            f"schema={report.schema}",
            f"status={report.status}",
            f"classification={report.classification}",
            f"artifact_type={report.artifact_type}",
            f"total_scenarios={report.total_scenarios}",
            f"truth_authority={report.truth_authority}",
            f"introduces_new_truth={report.introduces_new_truth}",
            f"verified={report.verified}",
        )
    )


def format_receipt_summary(report: AfriRideControlledPilotExecutionReceiptReport) -> str:
    return "\n".join(
        (
            "EXECUTION RECEIPT VALID",
            f"receipt_id={report.receipt_id}",
            f"bundle_id={report.bundle_id}",
            f"bundle_hash={report.bundle_hash}",
            f"scenarios_executed={report.scenarios_executed}",
            f"replay_success_rate={report.replay_success_rate}",
            f"total_incidents={report.total_incidents}",
            f"final_status={report.final_status}",
            f"verified={report.verified}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        contract = validate_contract()
        if args:
            if len(args) != 2:
                raise AfriRideControlledPilotExecutionReceiptValidationError(
                    "usage: validator <receipt_path> <evidence_bundle_root>"
                )
            report = validate_receipt(Path(args[0]), Path(args[1]))
            print(format_receipt_summary(report))
        else:
            print(format_contract_summary(contract))
    except (
        AfriRideControlledPilotExecutionReceiptValidationError,
        RuntimeError,
    ) as exc:
        print(f"RECEIPT REJECTED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
