from __future__ import annotations

import pytest

from tests.controlled_pilot._helpers import read_text


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_release_guard]


def test_controlled_pilot_exit_criteria_are_documented() -> None:
    doc = read_text("docs/pilot/CONTROLLED_PILOT_EXIT_CRITERIA.md")
    for marker in [
        "Access control passes",
        "NovaRide",
        "NovaPay",
        "NovaID",
        "Cash procedure",
        "Monitoring and support",
        "Incident response",
        "APK distribution",
        "No payment-safety violation",
        "General availability remains false",
    ]:
        assert marker in doc

