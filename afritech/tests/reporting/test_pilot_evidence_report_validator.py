from __future__ import annotations

import pytest

from afritech.reporting.pilot_evidence_report import (
    build_pilot_evidence_run_report,
)
from afritech.reporting.pilot_evidence_report_validator import (
    PilotEvidenceReportValidationError,
    validate_pilot_evidence_report,
)


def valid_report_payload():
    return build_pilot_evidence_run_report(
        "pilot-run-validator-001",
        [
            {
                "traceId": "0123456789abcdef0123456789abcdef",
                "driverId": "driver-demo-001",
                "evidenceType": "driver_shift_started",
                "status": 200,
                "durationMs": 42,
                "structuredError": None,
                "timestamp": "2026-06-07T12:00:00+00:00",
            }
        ],
    ).canonical_dict()


def test_valid_report_passes():
    result = validate_pilot_evidence_report(valid_report_payload())

    assert result.valid is True
    assert result.classification == "REVIEWABLE_PILOT_EVIDENCE"
    assert result.production_proof is False
    assert result.authority_source == "observability_only"
    assert result.entry_count == 1


def test_wrong_classification_fails():
    payload = valid_report_payload()
    payload["classification"] = "PRODUCTION_READY"

    with pytest.raises(PilotEvidenceReportValidationError):
        validate_pilot_evidence_report(payload)


def test_production_proof_true_fails():
    payload = valid_report_payload()
    payload["production_proof"] = True

    with pytest.raises(PilotEvidenceReportValidationError):
        validate_pilot_evidence_report(payload)


def test_wrong_authority_source_fails():
    payload = valid_report_payload()
    payload["authority_source"] = "trace_authority"

    with pytest.raises(PilotEvidenceReportValidationError):
        validate_pilot_evidence_report(payload)


def test_missing_trace_id_fails():
    payload = valid_report_payload()
    payload["entries"][0]["traceId"] = ""

    with pytest.raises(PilotEvidenceReportValidationError):
        validate_pilot_evidence_report(payload)


def test_missing_structured_error_key_fails():
    payload = valid_report_payload()
    del payload["entries"][0]["structuredError"]

    with pytest.raises(PilotEvidenceReportValidationError):
        validate_pilot_evidence_report(payload)


def test_missing_required_field_fails():
    payload = valid_report_payload()
    del payload["entries"][0]["durationMs"]

    with pytest.raises(PilotEvidenceReportValidationError):
        validate_pilot_evidence_report(payload)

