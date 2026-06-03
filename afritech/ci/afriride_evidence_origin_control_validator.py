"""Validate AfriRide evidence origin control and bundle provenance."""

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
    validate_bundle,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_EVIDENCE_ORIGIN_CONTROL.md"

ORIGIN_LAW = (
    "structure_and_replay_are_not_enough",
    "origin_authenticates_admissibility",
    "field_observed_required_for_progression",
)


class AfriRideEvidenceOriginControlValidationError(RuntimeError):
    """Raised when evidence origin control is invalid."""


@dataclass(frozen=True)
class AfriRideEvidenceOriginControlReport:
    schema: str
    status: str
    classification: str
    certification_required_origin: str
    wave7_required_origin: str

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.evidence_origin_control.v1"
            and self.status == "evidence_origin_control_contract"
            and self.classification == "provenance_enforcement_layer"
            and self.certification_required_origin == "field_observed"
            and self.wave7_required_origin == "field_observed"
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideEvidenceOriginControlReport:
    if not path.exists():
        raise AfriRideEvidenceOriginControlValidationError(
            "evidence origin control contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: EVIDENCE ORIGIN CONTROL CONTRACT")
    _require(text, "CLASSIFICATION: PROVENANCE ENFORCEMENT LAYER")
    _require(text, "Only field_observed evidence is admissible")
    _require(text, "never admissible for certification")

    payload = _load_payload(text)
    _require_equal(payload["allowed_origins"], EVIDENCE_ORIGINS, "allowed origins")
    _require_equal(payload["origin_law"], ORIGIN_LAW, "origin law")
    if payload["certification_rejects_non_field_observed"] is not True:
        raise AfriRideEvidenceOriginControlValidationError(
            "certification does not reject non-field evidence"
        )
    if payload["go_no_go_rejects_non_field_observed"] is not True:
        raise AfriRideEvidenceOriginControlValidationError(
            "Go/No-Go does not reject non-field evidence"
        )
    if payload["synthetic_certification_allowed"] is not False:
        raise AfriRideEvidenceOriginControlValidationError(
            "synthetic certification is allowed"
        )

    report = AfriRideEvidenceOriginControlReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        certification_required_origin=payload["certification_required_origin"],
        wave7_required_origin=payload["wave7_required_origin"],
    )
    if not report.verified:
        raise AfriRideEvidenceOriginControlValidationError(
            "evidence origin control report is not verified"
        )
    return report


def validate_bundle_origin(
    bundle_root: Path,
    *,
    require_field_observed: bool,
) -> str:
    validate_bundle(bundle_root)
    metadata = _load_json(bundle_root / "bundle_metadata.json")
    manifest = _load_json(bundle_root / "bundle_manifest.json")
    origin = metadata.get("evidence_origin")
    if origin not in EVIDENCE_ORIGINS:
        raise AfriRideEvidenceOriginControlValidationError(
            "invalid evidence origin"
        )
    if manifest.get("evidence_origin") != origin:
        raise AfriRideEvidenceOriginControlValidationError(
            "manifest evidence origin mismatch"
        )
    if require_field_observed and origin != "field_observed":
        raise AfriRideEvidenceOriginControlValidationError(
            f"REJECTED: evidence_origin={origin} is not admissible for certification"
        )
    return origin


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(evidence_origin_control:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRideEvidenceOriginControlValidationError(
            "missing evidence_origin_control yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("evidence_origin_control") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideEvidenceOriginControlValidationError(
            "invalid evidence_origin_control yaml block"
        )
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideEvidenceOriginControlValidationError(f"missing phrase: {phrase}")


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideEvidenceOriginControlValidationError(f"{label} mismatch")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        report = validate_contract()
        if args:
            require_field = "--require-field-observed" in args
            bundle_arg = next((arg for arg in args if not arg.startswith("--")), None)
            if bundle_arg is None:
                raise AfriRideEvidenceOriginControlValidationError(
                    "usage: validator <bundle_root> [--require-field-observed]"
                )
            origin = validate_bundle_origin(
                Path(bundle_arg),
                require_field_observed=require_field,
            )
            print(f"EVIDENCE ORIGIN VALID: {origin}")
        else:
            print("AfriRide evidence origin control validation PASSED")
            print(f"schema={report.schema}")
            print(f"status={report.status}")
            print(f"classification={report.classification}")
            print(f"certification_required_origin={report.certification_required_origin}")
            print(f"wave7_required_origin={report.wave7_required_origin}")
            print(f"verified={report.verified}")
    except (AfriRideEvidenceOriginControlValidationError, RuntimeError) as exc:
        print(f"EVIDENCE ORIGIN REJECTED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
