from __future__ import annotations

import pytest

from tests.public_pilot._helpers import PUBLIC_PILOT_EXIT_REPORT_PATH, read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_release_guard]


def test_public_pilot_exit_criteria_documented() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_EXIT_CRITERIA.md")
    for phrase in (
        "pilot geography is enforced",
        "transaction limits are enforced",
        "monitoring is live",
        "incident response is tested",
        "rollback is verified",
        "support is staffed",
        "reconciliation passes",
        "PRR",
    ):
        assert phrase.lower() in text.lower()


def test_public_pilot_exit_report_stays_not_ready() -> None:
    text = PUBLIC_PILOT_EXIT_REPORT_PATH.read_text(encoding="utf-8")
    assert "status: NOT_READY_FOR_PRR" in text
    assert "next_stage: PRODUCTION_READINESS_REVIEW" in text
