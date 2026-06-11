from __future__ import annotations

import pytest

from afritech.reporting.pilot_evidence_report import build_pilot_evidence_run_report
from afritech.reporting.pilot_evidence_trend import (
    PilotEvidenceTrendComparisonError,
    compare_pilot_evidence_reports,
)


def report_payload(
    pilot_run_id: str,
    *,
    durations: tuple[int, ...],
    success_statuses: tuple[int, ...],
    driver_ids: tuple[str, ...],
    evidence_types: tuple[str, ...],
    structured_errors: tuple[dict[str, object] | None, ...] | None = None,
) -> dict:
    structured_errors = structured_errors or tuple(None for _ in durations)
    records = []
    for index, duration in enumerate(durations):
        records.append(
            {
                "traceId": f"{index + 1:032x}",
                "driverId": driver_ids[index % len(driver_ids)],
                "evidenceType": evidence_types[index % len(evidence_types)],
                "status": success_statuses[index],
                "durationMs": duration,
                "structuredError": structured_errors[index],
                "timestamp": f"2026-06-07T12:00:{index:02d}+00:00",
            }
        )
    return build_pilot_evidence_run_report(pilot_run_id, records).canonical_dict()


def sample_reports():
    return [
        report_payload(
            "controlled-session-001",
            durations=(20, 30),
            success_statuses=(200, 200),
            driver_ids=("driver-demo-001",),
            evidence_types=("driver_shift_started", "gps_accuracy_event"),
        ),
        report_payload(
            "controlled-session-002",
            durations=(25, 35, 45),
            success_statuses=(200, 200, 0),
            driver_ids=("driver-demo-001", "driver-demo-002"),
            evidence_types=("driver_shift_started", "gps_accuracy_event", "network_latency_event"),
            structured_errors=(
                None,
                None,
                {
                    "type": "timeout",
                    "severity": "warning",
                    "endpoint": "/pilot/evidence",
                },
            ),
        ),
    ]


def test_trend_comparison_outputs_review_only_contract():
    comparison = compare_pilot_evidence_reports(sample_reports()).canonical_dict()

    assert comparison["classification"] == "REVIEWABLE_PILOT_EVIDENCE_TREND"
    assert comparison["production_proof"] is False
    assert comparison["authority_source"] == "observability_only"
    assert comparison["sessions_compared"] == [
        "controlled-session-001",
        "controlled-session-002",
    ]


def test_trend_comparison_computes_growth_and_changes():
    comparison = compare_pilot_evidence_reports(sample_reports()).canonical_dict()

    assert comparison["observation_growth"][0]["value"] == 2
    assert comparison["observation_growth"][0]["delta_from_previous"] is None
    assert comparison["observation_growth"][1]["value"] == 3
    assert comparison["observation_growth"][1]["delta_from_previous"] == 1
    assert comparison["success_rate_changes"][0]["value"] == 1.0
    assert comparison["success_rate_changes"][1]["value"] == 0.6667
    assert comparison["latency_changes"]["average_duration_ms"][1]["delta_from_previous"] == 10
    assert comparison["latency_changes"]["max_duration_ms"][1]["delta_from_previous"] == 15
    assert comparison["new_error_types"][0]["new_error_types"] == []
    assert comparison["new_error_types"][1]["new_error_types"] == ["timeout"]
    assert comparison["driver_participation_changes"][1]["delta_from_previous"] == 1


def test_wrong_classification_fails_closed():
    reports = sample_reports()
    reports[0]["classification"] = "PRODUCTION_READY"

    with pytest.raises(PilotEvidenceTrendComparisonError):
        compare_pilot_evidence_reports(reports)


def test_production_proof_true_fails_closed():
    reports = sample_reports()
    reports[0]["production_proof"] = True

    with pytest.raises(PilotEvidenceTrendComparisonError):
        compare_pilot_evidence_reports(reports)


def test_wrong_authority_source_fails_closed():
    reports = sample_reports()
    reports[0]["authority_source"] = "report_authority"

    with pytest.raises(PilotEvidenceTrendComparisonError):
        compare_pilot_evidence_reports(reports)


def test_missing_summary_metrics_fails_closed():
    reports = sample_reports()
    del reports[0]["summary"]

    with pytest.raises(PilotEvidenceTrendComparisonError):
        compare_pilot_evidence_reports(reports)


def test_missing_pilot_run_id_fails_closed():
    reports = sample_reports()
    reports[0]["pilot_run_id"] = ""

    with pytest.raises(PilotEvidenceTrendComparisonError):
        compare_pilot_evidence_reports(reports)


def test_missing_required_summary_metric_fails_closed():
    reports = sample_reports()
    del reports[0]["summary"]["unique_trace_count"]

    with pytest.raises(PilotEvidenceTrendComparisonError):
        compare_pilot_evidence_reports(reports)

