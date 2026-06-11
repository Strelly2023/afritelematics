from __future__ import annotations

import json

from afritech.reporting import pilot_evidence_report_cli


def records_payload():
    return [
        {
            "traceId": "0123456789abcdef0123456789abcdef",
            "driverId": "driver-demo-001",
            "evidenceType": "driver_shift_started",
            "status": 200,
            "durationMs": 41,
            "structuredError": None,
            "timestamp": "2026-06-07T12:00:00+00:00",
        },
        {
            "traceId": "fedcba9876543210fedcba9876543210",
            "driverId": "driver-demo-001",
            "evidenceType": "gps_accuracy_event",
            "status": 0,
            "durationMs": 8000,
            "structuredError": {
                "type": "timeout",
                "severity": "warning",
                "endpoint": "/pilot/evidence",
                "durationMs": 8000,
                "message": "evidence_api_timeout",
                "traceId": "fedcba9876543210fedcba9876543210",
            },
            "timestamp": "2026-06-07T12:00:08+00:00",
        },
    ]


def write_records(tmp_path):
    input_path = tmp_path / "records.json"
    input_path.write_text(json.dumps(records_payload()), encoding="utf-8")
    return input_path


def test_cli_generates_json_report_and_validates(tmp_path):
    input_path = write_records(tmp_path)
    output_path = tmp_path / "pilot_report.json"

    status = pilot_evidence_report_cli.main(
        [
            "--input",
            str(input_path),
            "--format",
            "json",
            "--output",
            str(output_path),
            "--pilot-run-id",
            "pilot-run-cli-001",
            "--validate",
        ]
    )

    assert status == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["classification"] == "REVIEWABLE_PILOT_EVIDENCE"
    assert payload["production_proof"] is False
    assert payload["authority_source"] == "observability_only"
    assert payload["pilot_run_id"] == "pilot-run-cli-001"
    assert payload["entries"][1]["structuredError"]["type"] == "timeout"


def test_cli_generates_markdown_report(tmp_path):
    input_path = write_records(tmp_path)
    output_path = tmp_path / "pilot_report.md"

    status = pilot_evidence_report_cli.main(
        [
            "--input",
            str(input_path),
            "--format",
            "markdown",
            "--output",
            str(output_path),
            "--validate",
        ]
    )

    assert status == 0
    markdown = output_path.read_text(encoding="utf-8")
    assert "classification: REVIEWABLE_PILOT_EVIDENCE" in markdown
    assert "production_proof: false" in markdown
    assert "authority_source: observability_only" in markdown
    assert "traceId:" in markdown
    assert "structuredError:" in markdown


def test_cli_writes_json_to_stdout_when_output_omitted(tmp_path, capsys):
    input_path = write_records(tmp_path)

    status = pilot_evidence_report_cli.main(
        [
            "--input",
            str(input_path),
            "--format",
            "json",
            "--validate",
        ]
    )

    assert status == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["classification"] == "REVIEWABLE_PILOT_EVIDENCE"
    assert payload["production_proof"] is False


def test_cli_accepts_records_object_input(tmp_path):
    input_path = tmp_path / "records.json"
    input_path.write_text(json.dumps({"records": records_payload()}), encoding="utf-8")
    output_path = tmp_path / "pilot_report.json"

    status = pilot_evidence_report_cli.main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--validate",
        ]
    )

    assert status == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload["entries"]) == 2


def test_cli_accepts_jsonl_input(tmp_path):
    input_path = tmp_path / "pilot_observability_records.jsonl"
    input_path.write_text(
        "\n".join(json.dumps(record) for record in records_payload()) + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "pilot_report.md"

    status = pilot_evidence_report_cli.main(
        [
            "--input",
            str(input_path),
            "--format",
            "markdown",
            "--output",
            str(output_path),
            "--pilot-run-id",
            "controlled-session-001",
            "--validate",
        ]
    )

    assert status == 0
    markdown = output_path.read_text(encoding="utf-8")
    assert "pilot_run_id: controlled-session-001" in markdown
    assert "traceId:" in markdown
    assert "structuredError:" in markdown
    assert "production_proof: false" in markdown


def test_cli_fails_closed_for_invalid_input_shape(tmp_path, capsys):
    input_path = tmp_path / "records.json"
    input_path.write_text(json.dumps({"not_records": []}), encoding="utf-8")
    output_path = tmp_path / "pilot_report.json"

    status = pilot_evidence_report_cli.main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--validate",
        ]
    )

    assert status == 1
    assert not output_path.exists()
    captured = capsys.readouterr()
    assert "pilot evidence report failed" in captured.err
