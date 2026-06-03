"""Validate the AfriRide controlled pilot evidence bundle contract and artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from afritech.ci.afriride_controlled_pilot_scenario_matrix_validator import (
    REQUIRED_SCENARIOS,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_EVIDENCE_BUNDLE.md"

REQUIRED_LOCATIONS = ("Melbourne", "Bujumbura_Uvira", "Kinshasa")
LOCATION_TO_MATRIX_KEY = {
    "Melbourne": "melbourne",
    "Bujumbura_Uvira": "bujumbura_uvira",
    "Kinshasa": "kinshasa",
}
SCENARIO_IDS = {
    location: tuple(scenario.split("_", maxsplit=1)[0] for scenario in REQUIRED_SCENARIOS[key])
    for location, key in LOCATION_TO_MATRIX_KEY.items()
}
ALL_SCENARIO_IDS = tuple(
    scenario_id for location in REQUIRED_LOCATIONS for scenario_id in SCENARIO_IDS[location]
)

REQUIRED_FILES = (
    "bundle_metadata.json",
    "participant_registry.json",
    "device_registry.json",
    "pilot_completion_summary.json",
    "bundle_manifest.json",
)
EVIDENCE_ORIGINS = ("synthetic", "runtime_generated", "field_observed")
REQUIRED_DIRECTORIES = (
    "scenario_execution_receipts",
    "incident_records",
    "replay_verification_receipts",
)
SCENARIO_RECEIPT_FIELDS = (
    "scenario_id",
    "location",
    "trip_id",
    "participants",
    "execution_hash",
    "timestamp",
    "status",
)
INCIDENT_RECORD_FIELDS = (
    "scenario_id",
    "location",
    "incident_type",
    "event_id",
    "execution_hash",
    "replay_hash",
    "resolution",
    "status",
)
REPLAY_RECEIPT_FIELDS = (
    "scenario_id",
    "execution_hash",
    "replay_hash",
    "match",
    "validator_status",
)
COMPLETION_SUMMARY_FIELDS = (
    "locations",
    "scenarios_total",
    "scenarios_executed",
    "pass_count",
    "fail_count",
    "isolated_count",
    "replay_success_rate",
    "identity_integrity",
    "event_integrity",
    "final_status",
)
MANIFEST_FIELDS = (
    "bundle_id",
    "generated_at",
    "evidence_origin",
    "locations_covered",
    "total_scenarios",
    "receipts_count",
    "incident_count",
    "replay_verified",
    "hash",
)
INVALIDATION_CONDITIONS = (
    "missing_scenario_receipt",
    "replay_mismatch",
    "identity_inconsistency",
    "missing_incident_record",
    "manifest_hash_invalid",
    "unregistered_participant_used",
)
EVIDENCE_LAW = (
    "scenario_execution",
    "event_log",
    "replay_verification",
    "evidence_bundle",
)
FORBIDDEN_CLAIMS = (
    "production readiness achieved",
    "real-world scalability proven",
    "adversarial resilience proven",
    "market readiness proven",
)


class AfriRideControlledPilotEvidenceBundleValidationError(RuntimeError):
    """Raised when the controlled pilot evidence bundle is not admissible."""


@dataclass(frozen=True)
class AfriRideControlledPilotEvidenceBundleContractReport:
    schema: str
    status: str
    classification: str
    artifact_type: str
    scenarios_total: int
    truth_authority: str
    production_readiness_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.controlled_pilot_evidence_bundle.v1"
            and self.status == "controlled_pilot_evidence_bundle_contract"
            and self.classification == "proof_bound_evidence_package"
            and self.artifact_type == "proof_bound_evidence_package"
            and self.scenarios_total == 16
            and self.truth_authority == "replay_receipts"
            and self.production_readiness_claimed is False
        )


@dataclass(frozen=True)
class AfriRideControlledPilotEvidenceBundleReport:
    bundle_id: str
    locations_covered: int
    total_scenarios: int
    receipts_count: int
    incident_count: int
    replay_verified: bool
    final_status: str

    @property
    def verified(self) -> bool:
        return (
            self.locations_covered == 3
            and self.total_scenarios == 16
            and self.receipts_count == 16
            and self.replay_verified is True
            and self.final_status == "ADMISSIBLE"
        )


def validate_contract(
    path: Path = CONTRACT_DOC,
) -> AfriRideControlledPilotEvidenceBundleContractReport:
    if not path.exists():
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "evidence bundle contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: CONTROLLED PILOT EVIDENCE BUNDLE CONTRACT")
    _require(text, "CLASSIFICATION: PROOF-BOUND EVIDENCE PACKAGE")
    _require(text, "Pilot is NOT admissible")
    _require(text, "execution_hash == replay_hash")
    _require(text, "Bundle is rejected if any")
    _require(text, "forms a complete, consistent, and hash-bound system")

    lowered = text.lower()
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in lowered:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"forbidden claim: {phrase}"
            )

    payload = _load_contract_payload(text)
    _require_equal(payload["required_files"], REQUIRED_FILES, "required files")
    _require_equal(payload["required_directories"], REQUIRED_DIRECTORIES, "required directories")
    _require_equal(payload["required_locations"], REQUIRED_LOCATIONS, "required locations")
    _require_equal(payload["scenario_receipt_fields"], SCENARIO_RECEIPT_FIELDS, "scenario receipt fields")
    _require_equal(payload["incident_record_fields"], INCIDENT_RECORD_FIELDS, "incident fields")
    _require_equal(payload["replay_receipt_fields"], REPLAY_RECEIPT_FIELDS, "replay fields")
    _require_equal(payload["completion_summary_fields"], COMPLETION_SUMMARY_FIELDS, "summary fields")
    _require_equal(payload["manifest_fields"], MANIFEST_FIELDS, "manifest fields")
    _require_equal(payload["invalidation_conditions"], INVALIDATION_CONDITIONS, "invalidation conditions")
    _require_equal(payload["evidence_law"], EVIDENCE_LAW, "evidence law")

    if payload["production_readiness_claimed"] is not False:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "evidence bundle contract claims production readiness"
        )
    for claim_key in (
        "scalability_claimed",
        "adversarial_resilience_claimed",
        "market_readiness_claimed",
    ):
        if payload[claim_key] is not False:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"evidence bundle contract claims {claim_key}"
            )

    report = AfriRideControlledPilotEvidenceBundleContractReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        artifact_type=payload["artifact_type"],
        scenarios_total=payload["scenarios_total"],
        truth_authority=payload["truth_authority"],
        production_readiness_claimed=payload["production_readiness_claimed"],
    )
    if not report.verified:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "evidence bundle contract report is not verified"
        )
    return report


def validate_bundle(bundle_root: Path) -> AfriRideControlledPilotEvidenceBundleReport:
    if not bundle_root.exists() or not bundle_root.is_dir():
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "evidence bundle directory missing"
        )

    for rel_path in REQUIRED_FILES:
        if not (bundle_root / rel_path).is_file():
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"missing required file: {rel_path}"
            )
    for rel_path in REQUIRED_DIRECTORIES:
        if not (bundle_root / rel_path).is_dir():
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"missing required directory: {rel_path}"
            )

    participant_registry = _load_json(bundle_root / "participant_registry.json")
    device_registry = _load_json(bundle_root / "device_registry.json")
    metadata = _load_json(bundle_root / "bundle_metadata.json")
    summary = _load_json(bundle_root / "pilot_completion_summary.json")
    manifest = _load_json(bundle_root / "bundle_manifest.json")

    _validate_evidence_origin(metadata, manifest)
    _validate_participant_registry(participant_registry)
    _validate_device_registry(device_registry, participant_registry)
    registered_riders = {rider["rider_id"] for rider in participant_registry["riders"]}
    registered_drivers = {driver["driver_id"] for driver in participant_registry["drivers"]}

    receipts = _load_scenario_receipts(bundle_root, registered_riders, registered_drivers)
    replay_receipts = _load_replay_receipts(bundle_root)
    incidents = _load_incident_records(bundle_root)

    _validate_replay_consistency(receipts, replay_receipts)
    _validate_incident_accountability(receipts, incidents)
    _validate_summary(summary, receipts, incidents)
    _validate_manifest(manifest, bundle_root, receipts, incidents)

    report = AfriRideControlledPilotEvidenceBundleReport(
        bundle_id=manifest["bundle_id"],
        locations_covered=manifest["locations_covered"],
        total_scenarios=manifest["total_scenarios"],
        receipts_count=manifest["receipts_count"],
        incident_count=manifest["incident_count"],
        replay_verified=manifest["replay_verified"],
        final_status=summary["final_status"],
    )
    if not report.verified:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "evidence bundle report is not verified"
        )
    return report


def compute_bundle_hash(bundle_root: Path) -> str:
    chunks: list[bytes] = []
    for path in sorted(bundle_root.rglob("*.json")):
        rel_path = path.relative_to(bundle_root).as_posix()
        payload = _load_json(path)
        if rel_path == "bundle_manifest.json":
            payload = dict(payload)
            payload["hash"] = ""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        chunks.append(rel_path.encode("utf-8") + b"\0" + canonical.encode("utf-8"))
    return hashlib.sha256(b"\n".join(chunks)).hexdigest()


def _load_scenario_receipts(
    bundle_root: Path,
    registered_riders: set[str],
    registered_drivers: set[str],
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for location in REQUIRED_LOCATIONS:
        location_dir = bundle_root / "scenario_execution_receipts" / location
        if not location_dir.is_dir():
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"missing location receipts: {location}"
            )
        for scenario_id in SCENARIO_IDS[location]:
            receipt_path = location_dir / scenario_id / "receipt.json"
            if not receipt_path.is_file():
                raise AfriRideControlledPilotEvidenceBundleValidationError(
                    f"missing scenario receipt: {location}/{scenario_id}"
                )
            receipt = _load_json(receipt_path)
            _require_fields(receipt, SCENARIO_RECEIPT_FIELDS, f"receipt {scenario_id}")
            if receipt["scenario_id"] != scenario_id or receipt["location"] != location:
                raise AfriRideControlledPilotEvidenceBundleValidationError(
                    f"receipt identity mismatch: {location}/{scenario_id}"
                )
            participants = receipt["participants"]
            if participants.get("rider") not in registered_riders:
                raise AfriRideControlledPilotEvidenceBundleValidationError(
                    f"unregistered rider used: {scenario_id}"
                )
            if participants.get("driver") not in registered_drivers:
                raise AfriRideControlledPilotEvidenceBundleValidationError(
                    f"unregistered driver used: {scenario_id}"
                )
            if receipt["status"] not in {"PASS", "FAIL", "ISOLATED"}:
                raise AfriRideControlledPilotEvidenceBundleValidationError(
                    f"invalid receipt status: {scenario_id}"
                )
            receipts[scenario_id] = receipt
    return receipts


def _load_replay_receipts(bundle_root: Path) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    replay_root = bundle_root / "replay_verification_receipts"
    for scenario_id in ALL_SCENARIO_IDS:
        path = replay_root / f"{scenario_id}.json"
        if not path.is_file():
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"missing replay receipt: {scenario_id}"
            )
        receipt = _load_json(path)
        _require_fields(receipt, REPLAY_RECEIPT_FIELDS, f"replay {scenario_id}")
        if receipt["scenario_id"] != scenario_id:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"replay receipt scenario mismatch: {scenario_id}"
            )
        if receipt["match"] is not True or receipt["validator_status"] != "PASS":
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"replay receipt not verified: {scenario_id}"
            )
        receipts[scenario_id] = receipt
    return receipts


def _load_incident_records(bundle_root: Path) -> list[dict[str, Any]]:
    incidents: list[dict[str, Any]] = []
    for path in sorted((bundle_root / "incident_records").glob("*.json")):
        incident = _load_json(path)
        _require_fields(incident, INCIDENT_RECORD_FIELDS, f"incident {path.name}")
        if incident["status"] != "RECORDED":
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"incident not recorded: {path.name}"
            )
        incidents.append(incident)
    return incidents


def _validate_replay_consistency(
    receipts: dict[str, dict[str, Any]],
    replay_receipts: dict[str, dict[str, Any]],
) -> None:
    for scenario_id, receipt in receipts.items():
        replay = replay_receipts[scenario_id]
        if receipt["execution_hash"] != replay["execution_hash"]:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"execution hash mismatch between receipt and replay: {scenario_id}"
            )
        if replay["execution_hash"] != replay["replay_hash"]:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"replay mismatch: {scenario_id}"
            )


def _validate_incident_accountability(
    receipts: dict[str, dict[str, Any]],
    incidents: list[dict[str, Any]],
) -> None:
    incident_scenarios = {incident["scenario_id"] for incident in incidents}
    for scenario_id, receipt in receipts.items():
        if receipt["status"] in {"FAIL", "ISOLATED"} and scenario_id not in incident_scenarios:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"missing incident record: {scenario_id}"
            )


def _validate_summary(
    summary: dict[str, Any],
    receipts: dict[str, dict[str, Any]],
    incidents: list[dict[str, Any]],
) -> None:
    _require_fields(summary, COMPLETION_SUMMARY_FIELDS, "completion summary")
    if summary["locations"] != list(REQUIRED_LOCATIONS):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "summary location coverage mismatch"
        )
    if summary["scenarios_total"] != 16 or summary["scenarios_executed"] != len(receipts):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "summary scenario counts mismatch"
        )
    pass_count = sum(1 for receipt in receipts.values() if receipt["status"] == "PASS")
    fail_count = sum(1 for receipt in receipts.values() if receipt["status"] == "FAIL")
    isolated_count = sum(1 for receipt in receipts.values() if receipt["status"] == "ISOLATED")
    if (
        summary["pass_count"] != pass_count
        or summary["fail_count"] != fail_count
        or summary["isolated_count"] != isolated_count
    ):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "summary outcome counts mismatch"
        )
    if summary["fail_count"] + summary["isolated_count"] != len(incidents):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "summary incident count mismatch"
        )
    if (
        summary["replay_success_rate"] != "100%"
        or summary["identity_integrity"] is not True
        or summary["event_integrity"] is not True
        or summary["final_status"] != "ADMISSIBLE"
    ):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "summary does not declare admissible replay integrity"
        )


def _validate_manifest(
    manifest: dict[str, Any],
    bundle_root: Path,
    receipts: dict[str, dict[str, Any]],
    incidents: list[dict[str, Any]],
) -> None:
    _require_fields(manifest, MANIFEST_FIELDS, "bundle manifest")
    if (
        manifest["locations_covered"] != 3
        or manifest["total_scenarios"] != 16
        or manifest["receipts_count"] != len(receipts)
        or manifest["incident_count"] != len(incidents)
        or manifest["replay_verified"] is not True
    ):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "manifest counts mismatch"
        )
    if manifest["hash"] != compute_bundle_hash(bundle_root):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "manifest hash invalid"
        )


def _validate_evidence_origin(metadata: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_fields(metadata, ("bundle_id", "evidence_origin"), "bundle metadata")
    if metadata["evidence_origin"] not in EVIDENCE_ORIGINS:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "invalid evidence origin"
        )
    if manifest.get("evidence_origin") != metadata["evidence_origin"]:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "evidence origin mismatch"
        )
    if manifest.get("bundle_id") != metadata["bundle_id"]:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "bundle metadata identity mismatch"
        )


def _validate_participant_registry(registry: dict[str, Any]) -> None:
    if not isinstance(registry.get("riders"), list) or not isinstance(
        registry.get("drivers"), list
    ):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "participant registry missing riders/drivers"
        )
    for rider in registry["riders"]:
        _require_fields(rider, ("rider_id", "location"), "rider")
    for driver in registry["drivers"]:
        _require_fields(driver, ("driver_id", "vehicle", "location"), "driver")


def _validate_device_registry(
    registry: dict[str, Any],
    participants: dict[str, Any],
) -> None:
    if not isinstance(registry.get("devices"), list):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "device registry missing devices"
        )
    participant_ids = {
        item["rider_id"] for item in participants["riders"]
    } | {item["driver_id"] for item in participants["drivers"]}
    for device in registry["devices"]:
        _require_fields(
            device,
            ("device_id", "user_id", "type", "gps_enabled", "network_type"),
            "device",
        )
        if device["user_id"] not in participant_ids:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"device references unregistered user: {device['device_id']}"
            )
        if device["type"] not in {"driver", "rider"} or device["gps_enabled"] is not True:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"invalid device binding: {device['device_id']}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            f"invalid JSON: {path}"
        ) from exc
    if not isinstance(data, dict):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            f"JSON must be object: {path}"
        )
    return data


def _require_fields(payload: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if field not in payload:
            raise AfriRideControlledPilotEvidenceBundleValidationError(
                f"missing {label} field: {field}"
            )


def _load_contract_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(controlled_pilot_evidence_bundle:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "missing controlled_pilot_evidence_bundle yaml block"
        )
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict) or not isinstance(
        data.get("controlled_pilot_evidence_bundle"), dict
    ):
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            "invalid controlled_pilot_evidence_bundle yaml block"
        )
    return data["controlled_pilot_evidence_bundle"]


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideControlledPilotEvidenceBundleValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideControlledPilotEvidenceBundleValidationError(f"{label} mismatch")


def format_contract_summary(
    report: AfriRideControlledPilotEvidenceBundleContractReport,
) -> str:
    return "\n".join(
        (
            "AfriRide controlled pilot evidence bundle contract validation PASSED",
            f"schema={report.schema}",
            f"status={report.status}",
            f"classification={report.classification}",
            f"artifact_type={report.artifact_type}",
            f"scenarios_total={report.scenarios_total}",
            f"truth_authority={report.truth_authority}",
            f"production_readiness_claimed={report.production_readiness_claimed}",
            f"verified={report.verified}",
        )
    )


def format_bundle_summary(report: AfriRideControlledPilotEvidenceBundleReport) -> str:
    return "\n".join(
        (
            "EVIDENCE BUNDLE VALID",
            f"bundle_id={report.bundle_id}",
            f"locations_covered={report.locations_covered}",
            f"total_scenarios={report.total_scenarios}",
            f"receipts_count={report.receipts_count}",
            f"incident_count={report.incident_count}",
            f"replay_verified={report.replay_verified}",
            f"final_status={report.final_status}",
            f"verified={report.verified}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        contract = validate_contract()
        if args:
            bundle = validate_bundle(Path(args[0]))
            print(format_bundle_summary(bundle))
        else:
            print(format_contract_summary(contract))
    except AfriRideControlledPilotEvidenceBundleValidationError as exc:
        print(f"EVIDENCE BUNDLE REJECTED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
