"""Stakeholder evidence report template for AfriRide pilot evidence.

The template communicates analysis results. It is not proof authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.post_pilot_analysis import (
    ALLOWED_PASS_CLAIM as ANALYSIS_ALLOWED_PASS_CLAIM,
    ANALYSIS_BOUNDARY,
    NON_CLAIMS as ANALYSIS_NON_CLAIMS,
    REQUIRED_ANALYSIS_GATES,
    build_post_pilot_analysis_protocol,
)


REPORT_BOUNDARY = (
    "Stakeholder evidence reports communicate validated evidence status only. "
    "They do not define truth, certify compliance, authorize launch, or replace "
    "replay and CI validators."
)

AUDIENCES = ("investor", "partner", "auditor")

REQUIRED_SECTIONS = (
    "executive_boundary",
    "hash_lineage",
    "evidence_status",
    "analysis_gate_summary",
    "reproduction_instructions",
    "non_claims",
    "required_next_evidence",
)

REPRODUCTION_COMMANDS = (
    "python3 -m afritech.ci.afriride_field_validator",
    "python3 -m afritech.ci.afriride_field_observability_validator",
    "python3 -m afritech.ci.afriride_live_pilot_protocol_validator",
    "python3 -m afritech.ci.afriride_day_one_runbook_validator",
    "python3 -m afritech.ci.afriride_post_pilot_analysis_validator",
)


class StakeholderEvidenceReportError(ValueError):
    """Raised when stakeholder reporting exceeds evidence authority."""


EVIDENCE_STATUS_VALUES = ("not_submitted", "accepted", "deferred", "rejected")


@dataclass(frozen=True)
class StakeholderEvidenceReportTemplate:
    analysis_hash: str
    runbook_hash: str
    audiences: tuple[str, ...] = AUDIENCES
    authority_boundary: str = REPORT_BOUNDARY
    required_sections: tuple[str, ...] = REQUIRED_SECTIONS
    reproduction_commands: tuple[str, ...] = REPRODUCTION_COMMANDS
    non_claims: tuple[str, ...] = ANALYSIS_NON_CLAIMS

    def __post_init__(self) -> None:
        if self.authority_boundary != REPORT_BOUNDARY:
            raise StakeholderEvidenceReportError("stakeholder report boundary mismatch")
        if self.audiences != AUDIENCES:
            raise StakeholderEvidenceReportError("stakeholder report audiences mismatch")
        if self.required_sections != REQUIRED_SECTIONS:
            raise StakeholderEvidenceReportError("stakeholder report sections incomplete")
        if self.reproduction_commands != REPRODUCTION_COMMANDS:
            raise StakeholderEvidenceReportError(
                "stakeholder report reproduction commands incomplete"
            )
        if set(ANALYSIS_NON_CLAIMS).difference(self.non_claims):
            raise StakeholderEvidenceReportError("stakeholder report non-claims incomplete")
        if len(self.analysis_hash) != 64 or len(self.runbook_hash) != 64:
            raise StakeholderEvidenceReportError(
                "stakeholder report requires analysis and runbook hashes"
            )

    @property
    def report_template_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "analysis_boundary": ANALYSIS_BOUNDARY,
            "analysis_hash": self.analysis_hash,
            "audiences": list(self.audiences),
            "authority_boundary": self.authority_boundary,
            "hash_lineage": {
                "post_pilot_analysis_hash": self.analysis_hash,
                "runbook_hash": self.runbook_hash,
            },
            "non_claims": list(self.non_claims),
            "required_sections": list(self.required_sections),
            "schema": "afriride.stakeholder_evidence_report_template.v1",
            "sections": _sections(),
        }
        if include_hash:
            payload["report_template_hash"] = self.report_template_hash
        return payload


def build_stakeholder_evidence_report_template() -> StakeholderEvidenceReportTemplate:
    analysis = build_post_pilot_analysis_protocol()
    return StakeholderEvidenceReportTemplate(
        analysis_hash=analysis.analysis_hash,
        runbook_hash=analysis.runbook_hash,
    )


def write_stakeholder_evidence_report_template(
    output_path: str | Path = "reports/afriride_live_pilot_protocol_v1/stakeholder_evidence_report_template.json",
) -> StakeholderEvidenceReportTemplate:
    template = build_stakeholder_evidence_report_template()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(template.canonical_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return template


@dataclass(frozen=True)
class StakeholderEvidenceReportInstance:
    template_hash: str
    analysis_hash: str
    evidence_status: str = "not_submitted"
    evidence_hashes: tuple[str, ...] = ()
    summary: str = "No real pilot evidence has been submitted for stakeholder review."
    authority_boundary: str = REPORT_BOUNDARY
    non_claims: tuple[str, ...] = ANALYSIS_NON_CLAIMS

    def __post_init__(self) -> None:
        if self.authority_boundary != REPORT_BOUNDARY:
            raise StakeholderEvidenceReportError("stakeholder report instance boundary mismatch")
        if self.evidence_status not in EVIDENCE_STATUS_VALUES:
            raise StakeholderEvidenceReportError("stakeholder evidence status is invalid")
        if set(ANALYSIS_NON_CLAIMS).difference(self.non_claims):
            raise StakeholderEvidenceReportError("stakeholder report instance non-claims incomplete")
        if len(self.template_hash) != 64 or len(self.analysis_hash) != 64:
            raise StakeholderEvidenceReportError(
                "stakeholder report instance requires template and analysis hashes"
            )
        if self.evidence_status == "not_submitted" and self.evidence_hashes:
            raise StakeholderEvidenceReportError(
                "not_submitted stakeholder report cannot include evidence hashes"
            )
        if self.evidence_status != "not_submitted" and not self.evidence_hashes:
            raise StakeholderEvidenceReportError(
                "submitted stakeholder report requires evidence hashes"
            )
        lowered_summary = self.summary.lower()
        for forbidden in (
            "production ready",
            "public launch ready",
            "regulatory approved",
            "market validated",
        ):
            if forbidden in lowered_summary:
                raise StakeholderEvidenceReportError(
                    f"stakeholder report instance contains forbidden claim: {forbidden}"
                )

    @property
    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "analysis_hash": self.analysis_hash,
            "authority_boundary": self.authority_boundary,
            "evidence_hashes": list(self.evidence_hashes),
            "evidence_status": self.evidence_status,
            "non_claims": list(self.non_claims),
            "schema": "afriride.stakeholder_evidence_report_instance.v1",
            "summary": self.summary,
            "template_hash": self.template_hash,
        }
        if include_hash:
            payload["report_hash"] = self.report_hash
        return payload


def build_initial_stakeholder_evidence_report() -> StakeholderEvidenceReportInstance:
    template = build_stakeholder_evidence_report_template()
    return StakeholderEvidenceReportInstance(
        analysis_hash=template.analysis_hash,
        template_hash=template.report_template_hash,
    )


def write_initial_stakeholder_evidence_report(
    output_path: str | Path = "reports/afriride_live_pilot_protocol_v1/stakeholder_evidence_report_initial.json",
) -> StakeholderEvidenceReportInstance:
    report = build_initial_stakeholder_evidence_report()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.canonical_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def _sections() -> dict[str, object]:
    return {
        "analysis_gate_summary": {
            "source": "post_pilot_analysis_protocol",
            "required_gates": list(REQUIRED_ANALYSIS_GATES),
            "valid_status_values": ("accepted", "deferred", "rejected"),
        },
        "evidence_status": {
            "allowed_values": ("not_submitted", "accepted", "deferred", "rejected"),
            "default": "not_submitted",
            "rule": "no success language is allowed until post-pilot analysis accepts evidence",
        },
        "executive_boundary": {
            "allowed_pass_claim": ANALYSIS_ALLOWED_PASS_CLAIM,
            "must_include": REPORT_BOUNDARY,
        },
        "hash_lineage": {
            "must_include": (
                "live_pilot_protocol_hash",
                "day_one_runbook_hash",
                "post_pilot_analysis_hash",
                "report_template_hash",
            ),
        },
        "non_claims": {
            "must_include": list(ANALYSIS_NON_CLAIMS),
        },
        "reproduction_instructions": {
            "commands": list(REPRODUCTION_COMMANDS),
            "rule": "stakeholder readers must be able to reproduce validator status locally",
        },
        "required_next_evidence": {
            "if_deferred": "list missing trace, dashboard, or replay artifacts",
            "if_rejected": "list invariant that failed and preserve failure evidence",
            "if_accepted": "state only bounded evidence acceptance, not readiness expansion",
        },
    }


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
