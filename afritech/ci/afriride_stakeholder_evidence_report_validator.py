"""Validate the AfriRide stakeholder evidence report template."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.stakeholder_evidence_report import (
    AUDIENCES,
    EVIDENCE_STATUS_VALUES,
    REPORT_BOUNDARY,
    REQUIRED_SECTIONS,
    REPRODUCTION_COMMANDS,
    StakeholderEvidenceReportError,
    build_initial_stakeholder_evidence_report,
    build_stakeholder_evidence_report_template,
)
from afriride.field_validation.post_pilot_analysis import NON_CLAIMS


class AfriRideStakeholderEvidenceReportValidationError(RuntimeError):
    """Raised when stakeholder reporting exceeds evidence boundaries."""


@dataclass(frozen=True)
class AfriRideStakeholderEvidenceReportValidationReport:
    report_template_hash: str
    initial_report_hash: str
    analysis_hash: str

    @property
    def verified(self) -> bool:
        return (
            len(self.report_template_hash) == 64
            and len(self.initial_report_hash) == 64
            and len(self.analysis_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "analysis_hash": self.analysis_hash,
            "initial_report_hash": self.initial_report_hash,
            "report_template_hash": self.report_template_hash,
            "schema": "afriride.stakeholder_evidence_report_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> AfriRideStakeholderEvidenceReportValidationReport:
    try:
        template = build_stakeholder_evidence_report_template()
    except StakeholderEvidenceReportError as exc:
        raise AfriRideStakeholderEvidenceReportValidationError(str(exc)) from exc

    payload = template.canonical_dict()
    _validate_payload(payload)
    instance_payload = build_initial_stakeholder_evidence_report().canonical_dict()
    _validate_instance_payload(instance_payload)
    report = AfriRideStakeholderEvidenceReportValidationReport(
        analysis_hash=str(payload["analysis_hash"]),
        initial_report_hash=str(instance_payload["report_hash"]),
        report_template_hash=str(payload["report_template_hash"]),
    )
    if not report.verified:
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder evidence report template not verified"
        )
    return report


def validate_report_file(
    path: Path = Path(
        "reports/afriride_live_pilot_protocol_v1/stakeholder_evidence_report_template.json"
    ),
) -> None:
    if not path.exists():
        raise AfriRideStakeholderEvidenceReportValidationError(
            "missing stakeholder evidence report template"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = build_stakeholder_evidence_report_template().canonical_dict()
    if payload.get("report_template_hash") != expected.get("report_template_hash"):
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder evidence report template hash mismatch"
        )
    _validate_payload(payload)


def validate_initial_report_file(
    path: Path = Path(
        "reports/afriride_live_pilot_protocol_v1/stakeholder_evidence_report_initial.json"
    ),
) -> None:
    if not path.exists():
        raise AfriRideStakeholderEvidenceReportValidationError(
            "missing initial stakeholder evidence report"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = build_initial_stakeholder_evidence_report().canonical_dict()
    if payload.get("report_hash") != expected.get("report_hash"):
        raise AfriRideStakeholderEvidenceReportValidationError(
            "initial stakeholder evidence report hash mismatch"
        )
    _validate_instance_payload(payload)


def _validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("authority_boundary") != REPORT_BOUNDARY:
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder report authority boundary mismatch"
        )
    if tuple(payload.get("audiences", ())) != AUDIENCES:
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder audiences mismatch"
        )
    if tuple(payload.get("required_sections", ())) != REQUIRED_SECTIONS:
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder report sections incomplete"
        )
    if set(NON_CLAIMS).difference(tuple(payload.get("non_claims", ()))): 
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder non-claims incomplete"
        )

    sections = payload.get("sections")
    if not isinstance(sections, dict):
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder sections missing"
        )
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            raise AfriRideStakeholderEvidenceReportValidationError(
                f"stakeholder section missing: {section}"
            )

    commands = tuple(sections["reproduction_instructions"].get("commands", ()))
    if commands != REPRODUCTION_COMMANDS:
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder reproduction commands incomplete"
        )
    evidence_values = tuple(sections["evidence_status"].get("allowed_values", ()))
    for required in ("not_submitted", "accepted", "deferred", "rejected"):
        if required not in evidence_values:
            raise AfriRideStakeholderEvidenceReportValidationError(
                f"stakeholder evidence status missing: {required}"
            )

    forbidden_terms = ("production readiness achieved", "public launch approved")
    serialized = json.dumps(payload, sort_keys=True).lower()
    for term in forbidden_terms:
        if term in serialized:
            raise AfriRideStakeholderEvidenceReportValidationError(
                f"stakeholder report contains forbidden claim: {term}"
            )


def _validate_instance_payload(payload: dict[str, Any]) -> None:
    if payload.get("authority_boundary") != REPORT_BOUNDARY:
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder report instance authority boundary mismatch"
        )
    if payload.get("evidence_status") not in EVIDENCE_STATUS_VALUES:
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder report instance status invalid"
        )
    if payload.get("evidence_status") == "not_submitted" and payload.get("evidence_hashes"):
        raise AfriRideStakeholderEvidenceReportValidationError(
            "not-submitted stakeholder report cannot include evidence hashes"
        )
    if set(NON_CLAIMS).difference(tuple(payload.get("non_claims", ()))): 
        raise AfriRideStakeholderEvidenceReportValidationError(
            "stakeholder report instance non-claims incomplete"
        )
    serialized = json.dumps(payload, sort_keys=True).lower()
    for term in ("production ready", "public launch ready", "regulatory approved"):
        if term in serialized:
            raise AfriRideStakeholderEvidenceReportValidationError(
                f"stakeholder report instance contains forbidden claim: {term}"
            )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = validate()
    except AfriRideStakeholderEvidenceReportValidationError as exc:
        print(f"AfriRide stakeholder evidence report validation FAILED: {exc}")
        return 1

    print(
        "AfriRide stakeholder evidence report validation PASSED: "
        f"report_template_hash={report.report_template_hash} "
        f"initial_report_hash={report.initial_report_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
