from __future__ import annotations

import pytest

from afriride.field_validation.stakeholder_evidence_report import (
    AUDIENCES,
    REPORT_BOUNDARY,
    REQUIRED_SECTIONS,
    REPRODUCTION_COMMANDS,
    StakeholderEvidenceReportInstance,
    StakeholderEvidenceReportError,
    StakeholderEvidenceReportTemplate,
    build_initial_stakeholder_evidence_report,
    build_stakeholder_evidence_report_template,
    write_initial_stakeholder_evidence_report,
    write_stakeholder_evidence_report_template,
)
from afritech.ci.afriride_stakeholder_evidence_report_validator import validate


def test_stakeholder_evidence_report_preserves_boundary_and_audience():
    payload = build_stakeholder_evidence_report_template().canonical_dict()

    assert payload["authority_boundary"] == REPORT_BOUNDARY
    assert tuple(payload["audiences"]) == AUDIENCES
    assert "investor" in payload["audiences"]
    assert "auditor" in payload["audiences"]
    assert "production_ready" in payload["non_claims"]


def test_stakeholder_evidence_report_has_required_sections():
    payload = build_stakeholder_evidence_report_template().canonical_dict()

    assert tuple(payload["required_sections"]) == REQUIRED_SECTIONS
    for section in REQUIRED_SECTIONS:
        assert section in payload["sections"]


def test_stakeholder_evidence_report_includes_reproduction_commands():
    payload = build_stakeholder_evidence_report_template().canonical_dict()
    commands = tuple(payload["sections"]["reproduction_instructions"]["commands"])

    assert commands == REPRODUCTION_COMMANDS
    assert "python3 -m afritech.ci.afriride_post_pilot_analysis_validator" in commands


def test_stakeholder_evidence_report_validator_accepts_template():
    report = validate()

    assert report.verified is True
    assert len(report.report_template_hash) == 64
    assert len(report.initial_report_hash) == 64
    assert len(report.analysis_hash) == 64


def test_stakeholder_evidence_report_is_reproducible(tmp_path):
    output = tmp_path / "stakeholder_evidence_report_template.json"
    written = write_stakeholder_evidence_report_template(output)
    rebuilt = build_stakeholder_evidence_report_template()

    assert written.report_template_hash == rebuilt.report_template_hash


def test_stakeholder_evidence_report_rejects_missing_audience():
    valid = build_stakeholder_evidence_report_template()

    with pytest.raises(StakeholderEvidenceReportError):
        StakeholderEvidenceReportTemplate(
            analysis_hash=valid.analysis_hash,
            runbook_hash=valid.runbook_hash,
            audiences=("investor",),
        )


def test_stakeholder_evidence_report_rejects_missing_command():
    valid = build_stakeholder_evidence_report_template()

    with pytest.raises(StakeholderEvidenceReportError):
        StakeholderEvidenceReportTemplate(
            analysis_hash=valid.analysis_hash,
            runbook_hash=valid.runbook_hash,
            reproduction_commands=REPRODUCTION_COMMANDS[:-1],
        )


def test_initial_stakeholder_report_is_not_submitted_and_hash_linked():
    template = build_stakeholder_evidence_report_template()
    report = build_initial_stakeholder_evidence_report()
    payload = report.canonical_dict()

    assert payload["template_hash"] == template.report_template_hash
    assert payload["analysis_hash"] == template.analysis_hash
    assert payload["evidence_status"] == "not_submitted"
    assert payload["evidence_hashes"] == []
    assert "No real pilot evidence" in payload["summary"]


def test_initial_stakeholder_report_is_reproducible(tmp_path):
    output = tmp_path / "stakeholder_evidence_report_initial.json"
    written = write_initial_stakeholder_evidence_report(output)
    rebuilt = build_initial_stakeholder_evidence_report()

    assert written.report_hash == rebuilt.report_hash


def test_initial_stakeholder_report_rejects_evidence_before_submission():
    valid = build_initial_stakeholder_evidence_report()

    with pytest.raises(StakeholderEvidenceReportError):
        StakeholderEvidenceReportInstance(
            analysis_hash=valid.analysis_hash,
            template_hash=valid.template_hash,
            evidence_hashes=("0" * 64,),
            evidence_status="not_submitted",
        )


def test_stakeholder_report_rejects_forbidden_summary_claim():
    valid = build_initial_stakeholder_evidence_report()

    with pytest.raises(StakeholderEvidenceReportError):
        StakeholderEvidenceReportInstance(
            analysis_hash=valid.analysis_hash,
            template_hash=valid.template_hash,
            summary="AfriRide is production ready.",
        )
