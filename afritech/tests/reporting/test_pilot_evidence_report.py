from __future__ import annotations

import json

from afritech.reporting.pilot_evidence_report import (
    AUTHORITY_SOURCE,
    REPORT_CLASSIFICATION,
    REQUIRED_REVIEW_FIELDS,
    build_pilot_evidence_run_report,
    render_pilot_evidence_run_report_json,
    render_pilot_evidence_run_report_markdown,
)


PILOT_RUN_ID = "pilot-run-observability-001"
TRACE_ID = "0123456789abcdef0123456789abcdef"
STRUCTURED_ERROR = {
    "type": "timeout",
    "severity": "warning",
    "endpoint": "/pilot/evidence",
    "durationMs": 8000,
    "message": "evidence_api_timeout",
    "traceId": TRACE_ID,
}


def sample_records():
    return [
        {
            "event": "pilot_evidence_request",
            "traceId": TRACE_ID,
            "driverId": "driver-demo-001",
            "evidenceType": "driver_shift_started",
            "status": 200,
            "durationMs": 123,
            "structuredError": None,
            "timestamp": "2026-06-07T12:00:00+00:00",
        },
        {
            "event": "pilot_evidence_request",
            "traceId": "fedcba9876543210fedcba9876543210",
            "driverId": "driver-demo-001",
            "evidenceType": "gps_accuracy_event",
            "status": 0,
            "durationMs": 8000,
            "structuredError": STRUCTURED_ERROR,
            "timestamp": "2026-06-07T12:00:08+00:00",
        },
    ]


def test_json_report_includes_required_review_fields():
    payload = json.loads(
        render_pilot_evidence_run_report_json(PILOT_RUN_ID, sample_records())
    )

    assert payload["classification"] == REPORT_CLASSIFICATION
    assert payload["production_proof"] is False
    assert payload["authority_source"] == AUTHORITY_SOURCE
    assert payload["pilot_run_id"] == PILOT_RUN_ID
    assert payload["required_review_fields"] == list(REQUIRED_REVIEW_FIELDS)

    for entry in payload["entries"]:
        assert set(REQUIRED_REVIEW_FIELDS).issubset(entry)
        assert entry["pilot_run_id"] == PILOT_RUN_ID


def test_json_report_includes_summary_metrics():
    payload = json.loads(
        render_pilot_evidence_run_report_json(PILOT_RUN_ID, sample_records())
    )
    summary = payload["summary"]

    assert summary["total_observations"] == 2
    assert summary["success_count"] == 1
    assert summary["failure_count"] == 1
    assert summary["success_rate"] == 0.5
    assert summary["average_duration_ms"] == 4061.5
    assert summary["max_duration_ms"] == 8000
    assert summary["evidence_types_seen"] == [
        "driver_shift_started",
        "gps_accuracy_event",
    ]
    assert summary["unique_driver_count"] == 1
    assert summary["unique_trace_count"] == 2
    assert payload["production_proof"] is False
    assert payload["authority_source"] == "observability_only"


def test_markdown_report_includes_same_review_fields():
    markdown = render_pilot_evidence_run_report_markdown(
        PILOT_RUN_ID,
        sample_records(),
    )

    assert f"classification: {REPORT_CLASSIFICATION}" in markdown
    assert "production_proof: false" in markdown
    assert f"authority_source: {AUTHORITY_SOURCE}" in markdown
    for field in REQUIRED_REVIEW_FIELDS:
        assert f"{field}:" in markdown


def test_markdown_report_includes_summary_metrics():
    markdown = render_pilot_evidence_run_report_markdown(
        PILOT_RUN_ID,
        sample_records(),
    )

    assert "## Summary Metrics" in markdown
    for field in (
        "total_observations",
        "success_count",
        "failure_count",
        "success_rate",
        "average_duration_ms",
        "max_duration_ms",
        "evidence_types_seen",
        "unique_driver_count",
        "unique_trace_count",
    ):
        assert f"{field}:" in markdown
    assert "production_proof: false" in markdown
    assert "authority_source: observability_only" in markdown


def test_structured_errors_are_preserved():
    report = build_pilot_evidence_run_report(PILOT_RUN_ID, sample_records())
    payload = report.canonical_dict()

    errored = payload["entries"][1]
    assert errored["structuredError"] == STRUCTURED_ERROR
    assert errored["structuredError"]["type"] == "timeout"
    assert errored["structuredError"]["traceId"] == TRACE_ID


def test_trace_ids_are_reviewable_without_becoming_authority():
    payload = build_pilot_evidence_run_report(
        PILOT_RUN_ID,
        sample_records(),
    ).canonical_dict()

    assert payload["entries"][0]["traceId"] == TRACE_ID
    assert payload["authority_source"] == "observability_only"
    assert payload["classification"] == "REVIEWABLE_PILOT_EVIDENCE"
    assert "traceId" in payload["required_review_fields"]


def test_observability_metadata_does_not_become_authority():
    payload = build_pilot_evidence_run_report(
        PILOT_RUN_ID,
        sample_records(),
    ).canonical_dict()

    assert payload["production_proof"] is False
    assert payload["authority_source"] == "observability_only"
    assert "production_ready" not in json.dumps(payload).lower()
    assert "certified" not in json.dumps(payload).lower()
