from __future__ import annotations

import json

from afritech.reporting.pilot_evidence_report import build_pilot_evidence_run_report
from afritech.reporting.pilot_evidence_trend_cli import main


def report_payload(
    pilot_run_id: str,
    *,
    durations: tuple[int, ...],
    statuses: tuple[int, ...],
    structured_errors: tuple[dict[str, object] | None, ...] | None = None,
) -> dict:
    structured_errors = structured_errors or tuple(None for _ in durations)
    records = []
    for index, duration in enumerate(durations):
        records.append(
            {
                "traceId": f"{index + 1:032x}",
                "driverId": f"driver-demo-00{(index % 2) + 1}",
                "evidenceType": "driver_location_event",
                "status": statuses[index],
                "durationMs": duration,
                "structuredError": structured_errors[index],
                "timestamp": f"2026-06-07T12:00:{index:02d}+00:00",
            }
        )
    return build_pilot_evidence_run_report(pilot_run_id, records).canonical_dict()


def write_report(path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_trend_cli_writes_review_only_json(tmp_path):
    session_001 = tmp_path / "session001.json"
    session_002 = tmp_path / "session002.json"
    output = tmp_path / "pilot_trend.json"

    write_report(
        session_001,
        report_payload("controlled-session-001", durations=(20, 30), statuses=(200, 200)),
    )
    write_report(
        session_002,
        report_payload(
            "controlled-session-002",
            durations=(25, 35, 45),
            statuses=(200, 200, 0),
            structured_errors=(
                None,
                None,
                {"type": "timeout", "severity": "warning"},
            ),
        ),
    )

    exit_code = main(
        [
            "--input",
            str(session_001),
            str(session_002),
            "--output",
            str(output),
            "--validate",
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["classification"] == "REVIEWABLE_PILOT_EVIDENCE_TREND"
    assert payload["production_proof"] is False
    assert payload["authority_source"] == "observability_only"
    assert payload["sessions_compared"] == [
        "controlled-session-001",
        "controlled-session-002",
    ]
    assert payload["observation_growth"][1]["delta_from_previous"] == 1
    assert payload["new_error_types"][1]["new_error_types"] == ["timeout"]


def test_trend_cli_writes_to_stdout_when_no_output(tmp_path, capsys):
    session_001 = tmp_path / "session001.json"
    write_report(
        session_001,
        report_payload("controlled-session-001", durations=(20,), statuses=(200,)),
    )

    exit_code = main(["--input", str(session_001), "--validate"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["classification"] == "REVIEWABLE_PILOT_EVIDENCE_TREND"
    assert payload["production_proof"] is False


def test_trend_cli_fails_closed_for_production_proof_input(tmp_path, capsys):
    session_001 = tmp_path / "session001.json"
    payload = report_payload("controlled-session-001", durations=(20,), statuses=(200,))
    payload["production_proof"] = True
    write_report(session_001, payload)

    exit_code = main(["--input", str(session_001), "--validate"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pilot evidence trend failed" in captured.err
    assert captured.out == ""


def test_trend_cli_fails_for_non_object_input(tmp_path, capsys):
    session_001 = tmp_path / "session001.json"
    session_001.write_text("[]", encoding="utf-8")

    exit_code = main(["--input", str(session_001), "--validate"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "must contain one generated report JSON object" in captured.err
