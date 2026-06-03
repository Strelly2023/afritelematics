from __future__ import annotations

import pytest

from afriride.field_validation.day_one_runbook import (
    EVIDENCE_CHECKPOINTS,
    NON_CLAIMS,
    RUNBOOK_BOUNDARY,
    DayOneRunbook,
    DayOneRunbookError,
    RunbookStep,
    build_day_one_runbook,
    write_day_one_runbook,
)
from afriride.field_validation.live_pilot_protocol import REQUIRED_SCENARIOS
from afritech.ci.afriride_day_one_runbook_validator import validate


def test_day_one_runbook_is_minute_ordered_and_bounded():
    payload = build_day_one_runbook().canonical_dict()
    minutes = tuple(step["minute"] for step in payload["steps"])

    assert payload["authority_boundary"] == RUNBOOK_BOUNDARY
    assert minutes == tuple(sorted(minutes))
    assert minutes[0] == 0
    assert minutes[-1] == 240
    assert payload["required_scenarios"] == list(REQUIRED_SCENARIOS)


def test_day_one_runbook_covers_all_evidence_checkpoints():
    payload = build_day_one_runbook().canonical_dict()
    emitted = {
        evidence
        for step in payload["steps"]
        for evidence in step["evidence"]
    }

    assert tuple(payload["required_evidence_checkpoints"]) == EVIDENCE_CHECKPOINTS
    assert set(EVIDENCE_CHECKPOINTS).issubset(emitted)
    assert "offline_trip_trace" in emitted
    assert "proof_dashboard_snapshot" in emitted


def test_day_one_runbook_preserves_non_claim_boundary():
    payload = build_day_one_runbook().canonical_dict()

    assert tuple(payload["non_claims"]) == NON_CLAIMS
    assert payload["allowed_claim"].startswith("AfriRide has a governed first-day")
    assert "pilot_completed" in payload["non_claims"]
    assert "production_ready" in payload["non_claims"]


def test_day_one_runbook_validator_accepts_runbook():
    report = validate()

    assert report.verified is True
    assert len(report.runbook_hash) == 64
    assert len(report.protocol_hash) == 64


def test_day_one_runbook_report_is_reproducible(tmp_path):
    output = tmp_path / "day_one_runbook.json"
    written = write_day_one_runbook(output)
    rebuilt = build_day_one_runbook()

    assert written.runbook_hash == rebuilt.runbook_hash


def test_day_one_runbook_rejects_unordered_steps():
    valid = build_day_one_runbook()
    unordered = (valid.steps[1], valid.steps[0], *valid.steps[2:])

    with pytest.raises(DayOneRunbookError):
        DayOneRunbook(protocol_hash=valid.protocol_hash, steps=unordered)


def test_day_one_runbook_rejects_missing_stop_check():
    with pytest.raises(DayOneRunbookError):
        RunbookStep(
            minute=0,
            owner="pilot_controller",
            action="Open pilot window.",
            evidence=("pilot_controller_closeout",),
            stop_check="",
        )
