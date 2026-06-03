"""Validate the AfriRide controlled pilot certification contract and artifact."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from afritech.ci.afriride_controlled_pilot_evidence_bundle_validator import (
    validate_bundle,
)
from afritech.ci.afriride_controlled_pilot_execution_receipt_validator import (
    validate_receipt,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_CERTIFICATION.md"

REQUIRED_TOP_LEVEL_FIELDS = (
    "certificate_id",
    "generated_at",
    "evidence_origin",
    "execution_receipt",
    "evidence_bundle",
    "verification",
    "scope",
    "classification",
    "constraints",
)
EXECUTION_RECEIPT_FIELDS = ("receipt_id", "status")
EVIDENCE_BUNDLE_FIELDS = ("bundle_id", "validated")
VERIFICATION_FIELDS = ("validators_passed", "replay_consistent", "identity_integrity")
SCOPE_FIELDS = ("locations", "scenarios")
CONSTRAINT_FIELDS = ("not_production_ready", "not_scalable", "not_market_ready")


class AfriRideControlledPilotCertificationValidationError(RuntimeError):
    """Raised when controlled pilot certification is invalid."""


@dataclass(frozen=True)
class AfriRideControlledPilotCertificationReport:
    schema: str
    status: str
    classification: str
    required_scenarios: int
    production_readiness_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.controlled_pilot_certification.v1"
            and self.status == "controlled_pilot_certification_contract"
            and self.classification == "certification_layer"
            and self.required_scenarios == 16
            and self.production_readiness_claimed is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideControlledPilotCertificationReport:
    if not path.exists():
        raise AfriRideControlledPilotCertificationValidationError(
            "controlled pilot certification contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: CONTROLLED PILOT CERTIFICATION CONTRACT")
    _require(text, "CLASSIFICATION: CERTIFICATION LAYER")
    _require(text, "without implying production readiness")
    _require(text, "MUST NOT CLAIM")
    _require(text, "System is NOT proven in uncontrolled environments")

    payload = _load_payload(text)
    _require_equal(payload["required_top_level_fields"], REQUIRED_TOP_LEVEL_FIELDS, "top-level fields")
    _require_equal(payload["execution_receipt_fields"], EXECUTION_RECEIPT_FIELDS, "receipt fields")
    _require_equal(payload["evidence_bundle_fields"], EVIDENCE_BUNDLE_FIELDS, "bundle fields")
    _require_equal(payload["verification_fields"], VERIFICATION_FIELDS, "verification fields")
    _require_equal(payload["scope_fields"], SCOPE_FIELDS, "scope fields")
    _require_equal(payload["constraint_fields"], CONSTRAINT_FIELDS, "constraint fields")
    if payload["scale_readiness_claimed"] is not False or payload["market_readiness_claimed"] is not False:
        raise AfriRideControlledPilotCertificationValidationError(
            "certification claims forbidden readiness"
        )
    if payload["required_locations"] != 3 or payload["required_scenarios"] != 16:
        raise AfriRideControlledPilotCertificationValidationError(
            "certification scope mismatch"
        )

    report = AfriRideControlledPilotCertificationReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        required_scenarios=payload["required_scenarios"],
        production_readiness_claimed=payload["production_readiness_claimed"],
    )
    if not report.verified:
        raise AfriRideControlledPilotCertificationValidationError(
            "certification report is not verified"
        )
    return report


def validate_certificate(certificate_path: Path, receipt_path: Path, bundle_root: Path) -> None:
    receipt_report = validate_receipt(receipt_path, bundle_root)
    bundle_report = validate_bundle(bundle_root)
    certificate = _load_json(certificate_path)
    receipt = _load_json(receipt_path)
    manifest = _load_json(bundle_root / "bundle_manifest.json")
    _require_fields(certificate, REQUIRED_TOP_LEVEL_FIELDS, "certificate")
    _require_fields(certificate["execution_receipt"], EXECUTION_RECEIPT_FIELDS, "execution receipt")
    _require_fields(certificate["evidence_bundle"], EVIDENCE_BUNDLE_FIELDS, "evidence bundle")
    _require_fields(certificate["verification"], VERIFICATION_FIELDS, "verification")
    _require_fields(certificate["scope"], SCOPE_FIELDS, "scope")
    _require_fields(certificate["constraints"], CONSTRAINT_FIELDS, "constraints")

    if certificate["evidence_origin"] != manifest["evidence_origin"]:
        raise AfriRideControlledPilotCertificationValidationError(
            "certificate evidence origin mismatch"
        )
    if certificate["evidence_origin"] != receipt["evidence_origin"]:
        raise AfriRideControlledPilotCertificationValidationError(
            "certificate receipt origin mismatch"
        )
    if certificate["evidence_origin"] != "field_observed":
        raise AfriRideControlledPilotCertificationValidationError(
            "non-field evidence cannot be certified"
        )
    if certificate["execution_receipt"]["receipt_id"] != receipt_report.receipt_id:
        raise AfriRideControlledPilotCertificationValidationError(
            "certificate receipt identity mismatch"
        )
    if certificate["execution_receipt"]["status"] != "VALID":
        raise AfriRideControlledPilotCertificationValidationError(
            "execution receipt is not certified valid"
        )
    if certificate["evidence_bundle"]["bundle_id"] != bundle_report.bundle_id:
        raise AfriRideControlledPilotCertificationValidationError(
            "certificate bundle identity mismatch"
        )
    if certificate["evidence_bundle"]["validated"] is not True:
        raise AfriRideControlledPilotCertificationValidationError(
            "evidence bundle is not certified validated"
        )
    for field in VERIFICATION_FIELDS:
        if certificate["verification"][field] is not True:
            raise AfriRideControlledPilotCertificationValidationError(
                f"verification flag false: {field}"
            )
    if certificate["scope"] != {"locations": 3, "scenarios": 16}:
        raise AfriRideControlledPilotCertificationValidationError(
            "certificate scope mismatch"
        )
    if certificate["classification"] != "CONTROLLED_PILOT_CERTIFIED":
        raise AfriRideControlledPilotCertificationValidationError(
            "certificate classification mismatch"
        )
    for field in CONSTRAINT_FIELDS:
        if certificate["constraints"][field] is not True:
            raise AfriRideControlledPilotCertificationValidationError(
                f"constraint flag missing: {field}"
            )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(controlled_pilot_certification:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRideControlledPilotCertificationValidationError(
            "missing controlled_pilot_certification yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("controlled_pilot_certification") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideControlledPilotCertificationValidationError(
            "invalid controlled_pilot_certification yaml block"
        )
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_fields(payload: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if field not in payload:
            raise AfriRideControlledPilotCertificationValidationError(
                f"missing {label} field: {field}"
            )


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideControlledPilotCertificationValidationError(f"missing phrase: {phrase}")


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideControlledPilotCertificationValidationError(f"{label} mismatch")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        report = validate_contract()
        if args:
            if len(args) != 3:
                raise AfriRideControlledPilotCertificationValidationError(
                    "usage: validator <certificate_path> <receipt_path> <bundle_root>"
                )
            validate_certificate(Path(args[0]), Path(args[1]), Path(args[2]))
            print("CONTROLLED PILOT CERTIFICATE VALID")
        else:
            print("AfriRide controlled pilot certification validation PASSED")
            print(f"schema={report.schema}")
            print(f"status={report.status}")
            print(f"classification={report.classification}")
            print(f"required_scenarios={report.required_scenarios}")
            print(f"verified={report.verified}")
    except (AfriRideControlledPilotCertificationValidationError, RuntimeError) as exc:
        print(f"CONTROLLED PILOT CERTIFICATE REJECTED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
