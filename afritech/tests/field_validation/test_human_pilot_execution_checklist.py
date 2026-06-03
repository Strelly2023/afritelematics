from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "afritech/docs/operations/melbourne_pilot_execution_checklist.md"


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_human_pilot_execution_checklist_maps_to_day_one_runbook():
    text = read_doc()

    assert "Day-One Human Execution Script" in text
    for minute in ("| 0 |", "| 15 |", "| 30 |", "| 45 |", "| 75 |", "| 105 |", "| 135 |", "| 165 |", "| 195 |", "| 225 |", "| 240 |"):
        assert minute in text

    for evidence in (
        "device_registration_snapshot",
        "preflight_validator_receipt",
        "dry_run_trace_receipt",
        "offline_trip_trace",
        "delayed_sync_trace",
        "gps_drift_trace",
        "duplicate_events_trace",
        "dispute_resolution_trace",
        "proof_dashboard_snapshot",
        "pilot_controller_closeout",
    ):
        assert evidence in text


def test_human_pilot_execution_checklist_preserves_authority_boundary():
    text = read_doc()
    lowered = text.lower()

    assert "may not define truth" in lowered
    assert "certify pilot completion" in lowered
    assert "authorize production readiness" in lowered
    assert "replay validators" in lowered
    assert "ci validators" in lowered


def test_human_pilot_execution_checklist_blocks_pre_evidence_claims():
    text = read_doc()

    assert "not_submitted" in text
    for forbidden in (
        "pilot completed",
        "production ready",
        "public launch ready",
        "regulatory approved",
        "market validated",
    ):
        assert forbidden in text


def test_human_pilot_execution_checklist_lists_operator_validators():
    text = read_doc()

    for command in (
        "python3 -m afritech.ci.afriride_live_pilot_protocol_validator",
        "python3 -m afritech.ci.afriride_day_one_runbook_validator",
        "python3 -m afritech.ci.afriride_post_pilot_analysis_validator",
        "python3 -m afritech.ci.afriride_stakeholder_evidence_report_validator",
    ):
        assert command in text
