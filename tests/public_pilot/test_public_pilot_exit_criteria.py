from __future__ import annotations

import pytest

from tests.public_pilot._helpers import PUBLIC_PILOT_EXIT_REPORT_PATH, read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_release_guard]


def test_public_pilot_exit_criteria_documented() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_EXIT_CRITERIA.md")
    for phrase in (
        "invitation-based public pilot",
        "approved real users",
        "real trusted devices",
        "pilot geography",
        "transaction limits",
        "monitoring",
        "incident response",
        "rollback",
        "support",
        "reconciliation",
        "READY_FOR_PRR",
    ):
        assert phrase.lower() in text.lower()


def test_public_pilot_exit_report_stays_ready_for_prr() -> None:
    text = PUBLIC_PILOT_EXIT_REPORT_PATH.read_text(encoding="utf-8")
    assert "status: READY_FOR_PRR" in text
    assert "next_stage: PRODUCTION_READINESS_REVIEW" in text
